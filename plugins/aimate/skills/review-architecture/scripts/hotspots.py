#!/usr/bin/env python3
"""Find architectural hot spots from git history.

Reports, for the recent history of a repository:
  - the most frequently changed source files, with current size, growth over
    the window, and an approximate cyclomatic complexity;
  - churn rolled up per module (directory);
  - pairs of files that are usually changed together (temporal coupling).

A "change" is one entry on the first-parent history: a merged PR (the merge
commit's full diff against the target branch), a squash-merged PR, or a direct
commit. This counts a PR once, however many WIP commits it had.

The window is anchored on the date of HEAD, not today, so a repository that
went quiet a year ago still gets a meaningful window.

Standard library only. Uses `lizard` for complexity when it is installed and a
keyword count otherwise; the output says which one ran.
"""

import argparse
import json
import math
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from itertools import combinations

SOURCE_EXTENSIONS = {
    "py", "js", "jsx", "ts", "tsx", "mjs", "cjs", "vue", "svelte",
    "java", "kt", "kts", "scala", "groovy", "go", "rs", "rb", "php",
    "cs", "fs", "vb", "swift", "m", "mm", "c", "h", "cc", "cpp", "hpp", "cxx",
    "dart", "ex", "exs", "erl", "clj", "cljs", "lua", "pl", "pm", "r", "jl",
    "hs", "ml", "elm", "sol", "sql", "sh", "bash", "ps1", "tf",
    "twig", "blade", "module", "inc", "theme", "install",
}

EXCLUDED_DIRS = re.compile(
    r"(^|/)(node_modules|vendor|bower_components|dist|build|out|target|\.next|"
    r"\.nuxt|coverage|__pycache__|\.venv|venv|generated|gen|migrations|"
    r"Migrations|\.git|third_party|thirdparty|external|contrib)(/|$)"
)
EXCLUDED_FILES = re.compile(
    r"(\.min\.(js|css)$|\.bundle\.js$|\.map$|\.pb\.go$|_pb2\.py$|\.g\.dart$|"
    r"\.designer\.cs$|\.generated\.\w+$|\.snap$)"
)
TEST_PATH = re.compile(
    r"((^|/)(tests?|__tests__|spec|specs|testing|e2e|cypress|fixtures?)/|"
    r"(\.|_)(test|spec)s?\.\w+$|(^|/)test_[^/]+$|Tests?\.\w+$)"
)
DECISION_POINTS = re.compile(
    r"\b(if|elif|elseif|for|foreach|while|case|catch|except|when|unless|until)\b"
    r"|&&|\|\||\?\?|\band\b|\bor\b"
)


def git(repo, *args, check=True):
    result = subprocess.run(
        ["git", "-C", repo, *args],
        capture_output=True, text=True, errors="replace",
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def is_source(path, include_tests, extensions):
    if EXCLUDED_DIRS.search(path) or EXCLUDED_FILES.search(path):
        return False
    if not include_tests and TEST_PATH.search(path):
        return False
    ext = path.rsplit(".", 1)[-1].lower() if "." in os.path.basename(path) else ""
    return extensions is None or ext in extensions


def parse_numstat_log(text):
    """Yield (sha, date, {path: lines_changed}) per change."""
    sha, date, files = None, None, {}
    for line in text.splitlines():
        if line.startswith("@@"):
            if sha:
                yield sha, date, files
            sha, date = line[2:].split("|", 1)
            files = {}
        elif line.strip() and sha:
            parts = line.split("\t")
            if len(parts) != 3:
                continue
            added, deleted, path = parts
            churn = (int(added) if added.isdigit() else 0) + (
                int(deleted) if deleted.isdigit() else 0)
            files[path] = files.get(path, 0) + churn
    if sha:
        yield sha, date, files


def count_loc(text):
    return sum(1 for line in text.splitlines() if line.strip())


def complexity_keywords(text):
    total = 0
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(("//", "#", "*", "/*", "--")):
            continue
        total += len(DECISION_POINTS.findall(stripped))
    return {"total": total, "max_function": None, "method": "keyword-count"}


def complexity_lizard(path, text):
    try:
        import lizard  # noqa: F401
    except ImportError:
        return None
    try:
        info = lizard.analyze_file.analyze_source_code(path, text)
    except Exception:
        return None
    functions = info.function_list
    if not functions:
        return None
    return {
        "total": sum(f.cyclomatic_complexity for f in functions),
        "max_function": max(
            ((f.cyclomatic_complexity, f.name) for f in functions))[1],
        "max_function_ccn": max(f.cyclomatic_complexity for f in functions),
        "method": "lizard",
    }


def module_of(path, depth):
    parts = path.split("/")[:-1]
    return "/".join(parts[:depth]) if parts else "(root)"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".", help="repository path (default: .)")
    ap.add_argument("--path", default="", help="limit to this subdirectory")
    ap.add_argument("--months", type=int, default=12,
                    help="window length in months before HEAD's date (default 12)")
    ap.add_argument("--max-changes", type=int, default=2000,
                    help="cap on changes read from history (default 2000)")
    ap.add_argument("--top", type=int, default=15, help="hot spots to list (default 15)")
    ap.add_argument("--module-depth", type=int, default=2,
                    help="directory depth for module roll-up (default 2)")
    ap.add_argument("--coupling-max-files", type=int, default=40,
                    help="ignore changes touching more files than this when "
                         "measuring coupling; bulk renames and formatting runs "
                         "couple everything to everything (default 40)")
    ap.add_argument("--coupling-min-shared", type=int, default=3,
                    help="minimum shared changes for a coupled pair (default 3)")
    ap.add_argument("--include-tests", action="store_true",
                    help="count test files too")
    ap.add_argument("--all-files", action="store_true",
                    help="count every text file, not only source extensions")
    ap.add_argument("--json", action="store_true", help="print JSON instead of markdown")
    args = ap.parse_args()

    repo = os.path.abspath(args.repo)
    try:
        git(repo, "rev-parse", "--git-dir")
    except (RuntimeError, FileNotFoundError):
        print(f"error: {repo} is not a git repository", file=sys.stderr)
        return 2

    shallow = git(repo, "rev-parse", "--is-shallow-repository", check=False).strip() == "true"
    head = git(repo, "rev-parse", "--short", "HEAD").strip()
    head_date = git(repo, "log", "-1", "--format=%cI", "HEAD").strip()
    # The window ends at HEAD's commit date, not today.
    y, m, d = (int(x) for x in head_date[:10].split("-"))
    m -= args.months
    while m <= 0:
        m += 12
        y -= 1
    since = f"{y:04d}-{m:02d}-{min(d, 28):02d}"

    log_args = ["log", "--first-parent", "-m", "--numstat", "--no-renames",
                "--format=@@%H|%cs", f"--since={since}", f"-n{args.max_changes}", "HEAD"]
    if args.path:
        log_args += ["--", args.path]
    changes = list(parse_numstat_log(git(repo, *log_args)))

    tracked = set(git(repo, "ls-files", *( [args.path] if args.path else [] )).splitlines())

    def select(extensions):
        out = []
        for sha, date, files in changes:
            kept = {p: c for p, c in files.items()
                    if p in tracked and is_source(p, args.include_tests, extensions)}
            out.append((sha, date, kept))
        return out

    extensions = None if args.all_files else SOURCE_EXTENSIONS
    filtered = select(extensions)
    fallback_all_files = False
    if extensions and not any(f for _, _, f in filtered):
        filtered = select(None)
        fallback_all_files = True

    freq, lines = Counter(), Counter()
    for _, _, files in filtered:
        for p, c in files.items():
            freq[p] += 1
            lines[p] += c

    # The tree just before the window opened, to measure growth. When the
    # window reaches back to the first commit, every file is new.
    window_start_sha, window_covers_root = None, False
    if changes:
        oldest = changes[-1][0]
        window_start_sha = git(repo, "rev-parse", "--verify", "-q", f"{oldest}^1",
                               check=False).strip() or None
        window_covers_root = window_start_sha is None and not shallow

    have_lizard = True
    try:
        import lizard  # noqa: F401
    except ImportError:
        have_lizard = False

    hotspots = []
    for path, n in freq.most_common(args.top):
        text = git(repo, "show", f"HEAD:{path}", check=False)
        loc = count_loc(text)
        before = 0 if window_covers_root else None
        if window_start_sha:
            old = subprocess.run(["git", "-C", repo, "show", f"{window_start_sha}:{path}"],
                                 capture_output=True, text=True, errors="replace")
            before = count_loc(old.stdout) if old.returncode == 0 else 0
        if is_source(path, True, SOURCE_EXTENSIONS):
            cx = complexity_lizard(path, text) or complexity_keywords(text)
        else:
            cx = {"total": None, "method": "not source"}
        hotspots.append({
            "path": path,
            "changes": n,
            "lines_churned": lines[path],
            "loc": loc,
            "loc_at_window_start": before,
            "growth": None if before is None else loc - before,
            "complexity": cx["total"],
            "complexity_per_100_loc": round(100 * cx["total"] / loc, 1)
            if loc and cx["total"] is not None else None,
            "most_complex_function": cx.get("max_function"),
            "most_complex_function_ccn": cx.get("max_function_ccn"),
            "score": round(n * math.log2(2 + (cx["total"] or 0)), 1),
        })

    modules = defaultdict(lambda: {"changes": 0, "files": set(), "lines_churned": 0})
    for sha, _, files in filtered:
        touched = {module_of(p, args.module_depth) for p in files}
        for mod in touched:
            modules[mod]["changes"] += 1
        for p, c in files.items():
            mod = modules[module_of(p, args.module_depth)]
            mod["files"].add(p)
            mod["lines_churned"] += c
    module_rows = sorted(
        ({"module": k, "changes": v["changes"], "files_touched": len(v["files"]),
          "lines_churned": v["lines_churned"]} for k, v in modules.items()),
        key=lambda r: -r["changes"])[:args.top]

    pair_counts = Counter()
    skipped_bulk = 0
    for _, _, files in filtered:
        if len(files) > args.coupling_max_files:
            skipped_bulk += 1
            continue
        for a, b in combinations(sorted(files), 2):
            pair_counts[(a, b)] += 1
    coupling = []
    for (a, b), shared in pair_counts.items():
        if shared < args.coupling_min_shared:
            continue
        degree = shared / min(freq[a], freq[b])
        if degree < 0.5:
            continue
        coupling.append({
            "a": a, "b": b, "shared_changes": shared,
            "degree": round(degree, 2),
            "cross_module": module_of(a, args.module_depth) != module_of(b, args.module_depth),
        })
    coupling.sort(key=lambda r: (-r["cross_module"], -r["shared_changes"], -r["degree"]))

    # Per hot spot: how many files it moves with, and its strongest partners.
    partners = defaultdict(list)
    for c in coupling:
        partners[c["a"]].append((c["shared_changes"], c["b"]))
        partners[c["b"]].append((c["shared_changes"], c["a"]))
    for h in hotspots:
        ranked = sorted(partners.get(h["path"], []), reverse=True)
        h["coupled_files"] = len(ranked)
        h["top_partners"] = [{"path": f, "shared_changes": n} for n, f in ranked[:3]]

    coupling = coupling[: args.top * 2]

    meta = {
        "repo": repo,
        "head": head,
        "head_date": head_date[:10],
        "window_since": since,
        "changes_read": len(changes),
        "changes_with_source_files": sum(1 for _, _, f in filtered if f),
        "hit_max_changes": len(changes) >= args.max_changes,
        "shallow_clone": shallow,
        "path_filter": args.path or None,
        "complexity_method": "lizard" if have_lizard else "keyword-count",
        "file_filter": "all files (no source files matched)" if fallback_all_files
        else ("all files" if args.all_files else "source extensions"),
        "tests_included": args.include_tests,
        "coupling_skipped_bulk_changes": skipped_bulk,
    }
    result = {"meta": meta, "hotspots": hotspots, "modules": module_rows,
              "coupling": coupling}

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    print(f"# Hot spots for {os.path.basename(repo)} @ {head}\n")
    print(f"Window: {since} .. {meta['head_date']} (anchored on HEAD). "
          f"Changes read: {meta['changes_read']}"
          f"{' (hit --max-changes cap)' if meta['hit_max_changes'] else ''}; "
          f"with source files: {meta['changes_with_source_files']}. "
          f"A change is one PR or direct commit on the first-parent history.")
    print(f"Complexity: {meta['complexity_method']}"
          f"{' (approximate: decision keywords per file, not per function)' if not have_lizard else ''}. "
          f"Files: {meta['file_filter']}, tests {'included' if args.include_tests else 'excluded'}.")
    if shallow:
        print("WARNING: shallow clone; history is truncated and churn is understated.")
    if fallback_all_files:
        print("NOTE: no files with source extensions changed; counted all files instead.")
    print()

    print("## Most changed files\n")
    print("| # | File | Changes | Lines churned | LOC | Growth | Complexity | Per 100 LOC | Score |")
    print("|---|---|---|---|---|---|---|---|---|")
    for i, h in enumerate(hotspots, 1):
        growth = "n/a" if h["growth"] is None else (
            "new" if h["loc_at_window_start"] == 0 else f"{h['growth']:+d}")
        cx = "n/a" if h["complexity"] is None else str(h["complexity"])
        if h["most_complex_function"]:
            cx += f" (max {h['most_complex_function_ccn']} in `{h['most_complex_function']}`)"
        print(f"| {i} | `{h['path']}` | {h['changes']} | {h['lines_churned']} | {h['loc']} | "
              f"{growth} | {cx} | {'n/a' if h['complexity_per_100_loc'] is None else h['complexity_per_100_loc']} | {h['score']} |")

    print(f"\n## Most changed modules (depth {args.module_depth})\n")
    print("| Module | Changes | Files touched | Lines churned |")
    print("|---|---|---|---|")
    for r in module_rows:
        print(f"| `{r['module']}` | {r['changes']} | {r['files_touched']} | {r['lines_churned']} |")

    print("\n## Files changed together\n")
    print(f"Pairs sharing at least {args.coupling_min_shared} changes, where at least half "
          f"of the less-changed file's changes also touched the other. "
          f"{skipped_bulk} bulk changes (> {args.coupling_max_files} files) ignored. "
          f"Cross-module pairs first.\n")
    if not coupling:
        print("No coupled pairs above the thresholds.")
    else:
        print("| File A | File B | Shared changes | Degree | Cross-module |")
        print("|---|---|---|---|---|")
        for c in coupling:
            print(f"| `{c['a']}` | `{c['b']}` | {c['shared_changes']} | {c['degree']} | "
                  f"{'yes' if c['cross_module'] else 'no'} |")
    partnered = [h for h in hotspots if h["top_partners"]]
    if partnered:
        print("\n## What the hot spots change with\n")
        print("Coupled files per hot spot (same thresholds as above) and the three "
              "strongest partners. A hot spot coupled to many files across modules "
              "is a candidate for mixed responsibilities.\n")
        for h in partnered:
            tops = ", ".join(f"`{t['path']}` ({t['shared_changes']})" for t in h["top_partners"])
            print(f"- `{h['path']}`: {h['coupled_files']} coupled files; strongest: {tops}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
