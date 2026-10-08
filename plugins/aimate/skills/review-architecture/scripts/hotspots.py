#!/usr/bin/env python3
"""Find architectural hot spots from git history.

Reports, for the recent history of a repository:
  - the files with the highest hot spot score (changes x complexity), with
    current size, growth over the window, and a decision-point count;
  - large, complex files that rarely change, which churn cannot see;
  - churn rolled up per module (directory);
  - pairs of files that are usually changed together (temporal coupling);
  - what the script left out, so a wrongly excluded folder is visible.

A "change" is one entry on the first-parent history: a merged PR (the merge
commit's full diff against the target branch), a squash-merged PR, or a direct
commit. This counts a merged PR once, however many WIP commits it had. On a
linear history that came from rebase merges, every commit counts as a change;
the output warns when the history looks like that. Branch syncs and release
merges, and bulk changes such as formatter runs, are left out of the counts.

Renames are followed, so a file that was moved keeps its history.

The window is anchored on the date of HEAD, not today, so a repository that
went quiet a year ago still gets a meaningful window.

Without git history (not a git repository, or no commits yet) the script ranks
files by size and complexity alone.

Standard library only. The complexity number is a count of decision keywords
per file (comments and string contents left out). Compare files within one
language, not across languages. When `lizard` is installed it adds the most
complex function per file.
"""

import argparse
import functools
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
    "erb", "haml", "cshtml", "razor", "jsp", "phtml", "hbs", "astro",
    "proto", "graphql", "gql", "prisma", "gradle",
}
# API contract files are architecture hot spots even though they are not code.
API_CONTRACT = re.compile(r"(^|/)(openapi|swagger|asyncapi)[^/]*\.(ya?ml|json)$", re.IGNORECASE)

# Directory names (lower case, matched ignoring case) that are third-party or
# build output wherever they appear.
SAFE_EXCLUDED_DIRS = {
    "node_modules", "vendor", "bower_components", ".next", ".nuxt", "coverage",
    "__pycache__", ".venv", "venv", ".git", "third_party", "thirdparty",
    "migrations", "pods", "carthage", ".gradle", ".terraform", ".idea", ".tox",
    ".mypy_cache", ".pytest_cache", "site-packages",
}
# Names that are usually build output or schema migrations but can also be a
# real domain folder (a `target` module in a marketing tool, `external`
# adapters, a data `migration` feature). Excluded by default, reported in the
# output, and overridable with --keep-dir.
AMBIGUOUS_EXCLUDED_DIRS = {
    "dist", "build", "out", "target", "gen", "generated", "external", "contrib",
    "obj", "migrate", "migration",
}
EXCLUDED_FILES = re.compile(
    r"(\.min\.(js|css)$|\.bundle\.js$|\.map$|\.pb\.go$|_pb2\.py$|\.g\.dart$|"
    r"\.designer\.cs$|\.generated\.\w+$|\.snap$)"
)
# A directory name is a test folder when it matches this whole. Most names match
# ignoring case (`tests/`, `Tests/`, `MyApp.Tests/`); `spec` and `specs` only in
# lower case, so a `Domain/Spec/` folder (the Specification pattern) is kept.
TEST_DIR_NAME = re.compile(
    r"(?i:tests?|__tests__|__mocks__|testing|e2e|cypress|fixtures?|"
    r"[^/]*\.tests?|androidtest|testfixtures)|specs?"
)
# File names are case sensitive so `FooTest.php` matches and `Latest.py` does not.
TEST_FILE = re.compile(
    r"((\.|_)(test|spec)s?\.\w+$|(^|/)test_[^/]+$|Tests?\.\w+$)"
)
_DECISION = (r"(?<!\bend )\b(if|elif|elsif|elseif|for|foreach|while|case|catch|except"
             r"|rescue|when|unless|until|guard)\b|&&|\|\||\?\?|\band\b|\bor\b")
DECISION_POINTS = re.compile(_DECISION)
# Keywords are upper case in much SQL and capitalised in Visual Basic. Elsewhere
# ignoring case would count prose ("For example", "Or") in templates.
DECISION_POINTS_CI = re.compile(_DECISION, re.IGNORECASE)
CASE_INSENSITIVE_EXTS = {"sql", "vb", "ps1"}
# `match` only as a statement or `x match {`, never `str.match(...)`.
MATCH_STATEMENT = re.compile(
    r"^(?:(?:let\s+(?:mut\s+)?)?[\w.:<>]+\s*=\s*|return\s+)?match\b(?!\s*\.)|\bmatch\s*\{")
# Languages where `#` starts a comment, and where `//` does not.
HASH_COMMENT_EXTS = {"py", "rb", "pl", "pm", "sh", "bash", "ps1", "r", "jl", "ex",
                     "exs", "tf", "php", "cr"}
NO_SLASH_COMMENT_EXTS = {"py", "rb", "pl", "pm", "sh", "bash", "ps1", "r", "jl", "ex", "exs"}
RENAME_BRACE = re.compile(r"^(.*)\{(.*) => (.*)\}(.*)$")
PR_SUBJECT = re.compile(r"\((#|!)\d+\)\s*$|^Merge pull request|^Merge branch")
# Merges that carry a whole branch's worth of earlier changes: a long-lived
# branch merged into another (`Merge branch 'main' into develop`), or a release
# merge. They would count every file twice.
_LONG_LIVED = r"(?:main|master|develop|development|dev|trunk|staging|release[^'\s]*)"
AGGREGATE_MERGE = re.compile(
    r"^Merge (?:remote-tracking )?branch '(?:origin/|upstream/)?" + _LONG_LIVED + r"'"
    r"|^Merge pull request #\d+ from \S+/" + _LONG_LIVED + r"\s*$"
)
THIN_HISTORY = 30
# Below this many decision points a file is not "complex", however rarely it changes.
MIN_STABLE_COMPLEXITY = 10
# Words that name a layer or a file's job, not the feature it belongs to.
LAYER_WORDS = {
    "controller", "controllers", "service", "services", "repository", "repositories",
    "handler", "handlers", "command", "commands", "query", "queries", "model",
    "models", "entity", "entities", "request", "requests", "response", "responses",
    "resolver", "resolvers", "provider", "factory", "mapper", "store", "component",
    "components", "page", "pages", "view", "views", "test", "tests", "spec",
    "interface", "base", "abstract", "index", "module", "types", "type", "schema",
    "schemas", "hook", "hooks", "util", "utils", "helper", "helpers", "form",
    "forms", "policy", "event", "events", "listener", "listeners", "route",
    "routes", "config", "stories", "story", "styles", "style",
}


def git(repo, *args, check=True):
    result = subprocess.run(
        ["git", "-c", "core.quotepath=false", "-C", repo, *args],
        capture_output=True, text=True, errors="replace",
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def exclusion(path, include_tests, extensions, keep_dirs):
    """Why a path is left out, or None when it is counted."""
    if path.startswith('"'):
        return "path git could not print (tab, newline or quote in name)"
    dirs = path.split("/")[:-1]
    for seg in dirs:
        low = seg.lower()
        if low in SAFE_EXCLUDED_DIRS:
            return f"directory `{seg}`"
        if low in AMBIGUOUS_EXCLUDED_DIRS and low not in keep_dirs:
            return f"directory `{seg}`"
    if EXCLUDED_FILES.search(path):
        return "generated or minified file"
    if not include_tests:
        for seg in dirs:
            if TEST_DIR_NAME.fullmatch(seg) and seg.lower() not in keep_dirs:
                return f"test directory `{seg}`"
        if TEST_FILE.search(path):
            return "test file"
    ext = path.rsplit(".", 1)[-1].lower() if "." in os.path.basename(path) else ""
    if extensions is not None and ext not in extensions and not API_CONTRACT.search(path):
        return "not a source extension"
    return None


def split_rename(path):
    """Return (old, new) for a numstat rename path, (None, path) otherwise."""
    m = RENAME_BRACE.match(path)
    if m:
        pre, a, b, post = m.groups()
        return (pre + a + post).replace("//", "/"), (pre + b + post).replace("//", "/")
    if " => " in path:
        old, new = path.split(" => ", 1)
        return old, new
    return None, path


def parse_numstat_log(text):
    """Yield (sha, date, parent_count, subject, {path: lines_changed}, renames)."""
    cur = None

    for line in text.splitlines():
        if line.startswith("@@"):
            if cur:
                yield cur
            sha, date, parents, subject = (line[2:].split("|", 3) + [""] * 4)[:4]
            cur = (sha, date, len(parents.split()), subject, {}, [])
        elif line.strip() and cur:
            parts = line.split("\t")
            if len(parts) != 3:
                continue
            added, deleted, path = parts
            churn = (int(added) if added.isdigit() else 0) + (
                int(deleted) if deleted.isdigit() else 0)
            old, new = split_rename(path)
            if old is not None:
                cur[5].append((old, new))
            cur[4][new] = cur[4].get(new, 0) + churn
    if cur:
        yield cur


def follow_renames(changes):
    """Credit a renamed file's older changes to its current name.

    `changes` is newest first. Returns the changes with canonical paths, and a
    map from current name to the oldest name seen in the window.
    """
    alias, origin, out = {}, {}, []
    for sha, date, parents, subject, files, renames in changes:
        for old, new in renames:
            current = alias.get(new, new)
            alias[old] = current
            origin[current] = old
        canon = {}
        for p, c in files.items():
            q = alias.get(p, p)
            canon[q] = canon.get(q, 0) + c
        out.append((sha, date, parents, subject, canon))
    return out, origin


def count_loc(text):
    return sum(1 for line in text.splitlines() if line.strip())


@functools.lru_cache(maxsize=None)
def _code_tokens(hash_comment, slash_comment):
    """Regex that finds what must not be counted: strings, comments, docstrings."""
    parts = [r'"""', r"'''", r'"(?:\\.|[^"\\])*"', r"'(?:\\.|[^'\\])*'",
             r"^\s*(?:--|#(?!\[))"]
    if slash_comment:
        parts += [r"/\*", r"(?:^|(?<=\s))//"]
    if hash_comment:
        parts.append(r"(?<=\s)#(?!\[)")
    return re.compile("|".join(parts))


def code_lines(text, ext=""):
    """Yield each line's code, without comments, docstrings and string contents."""
    tokens = _code_tokens(ext in HASH_COMMENT_EXTS, ext not in NO_SLASH_COMMENT_EXTS)
    open_mark = None  # the closing mark of a docstring or block comment we are inside
    for line in text.splitlines():
        out, pos = [], 0
        while True:
            if open_mark:
                end = line.find(open_mark, pos)
                if end < 0:
                    break
                pos, open_mark = end + len(open_mark), None
                continue
            m = tokens.search(line, pos)
            if not m:
                out.append(line[pos:])
                break
            out.append(line[pos:m.start()])
            tok = m.group()
            if tok in ('"""', "'''"):
                open_mark, pos = tok, m.end()
            elif tok == "/*":
                open_mark, pos = "*/", m.end()
            elif tok[0] in "\"'":
                out.append('""')
                pos = m.end()
            else:
                break  # a comment runs to the end of the line
        yield "".join(out).strip()


def decision_points(text, ext=""):
    total = 0
    pattern = DECISION_POINTS_CI if ext in CASE_INSENSITIVE_EXTS else DECISION_POINTS
    for code in code_lines(text, ext):
        if not code:
            continue
        total += len(pattern.findall(code))
        if MATCH_STATEMENT.search(code):
            total += 1
    return total


def lizard_detail(path, text):
    try:
        import lizard
        functions = lizard.analyze_file.analyze_source_code(path, text).function_list
    except Exception:
        return None
    if not functions:
        return None
    worst = max(functions, key=lambda f: f.cyclomatic_complexity)
    return {"function": worst.name, "ccn": worst.cyclomatic_complexity}


def file_ext(path):
    base = os.path.basename(path)
    return base.rsplit(".", 1)[-1].lower() if "." in base else ""


def measure(path, text, with_lizard=True):
    loc = count_loc(text)
    points = decision_points(text, file_ext(path))
    detail = lizard_detail(path, text) if with_lizard else None
    return {
        "loc": loc,
        "complexity": points,
        "complexity_per_100_loc": round(100 * points / loc, 1) if loc else None,
        "most_complex_function": detail["function"] if detail else None,
        "most_complex_function_ccn": detail["ccn"] if detail else None,
    }


BOT_AUTHOR = re.compile(r"\[bot\]|dependabot|renovate|github-actions", re.IGNORECASE)
# File names so common that a test with the same name says nothing; the folder must match too.
GENERIC_STEMS = {"index", "main", "utils", "util", "types", "helpers", "helper", "config",
                 "constants", "app", "mod", "init", "base"}


def distinct_authors(repo, since, path):
    """How many people changed a file in the window (a number only, bots left out)."""
    out = git(repo, "log", "--follow", f"--since={since}", "--format=%an%x09%ae", "HEAD",
              "--", path, check=False)
    people = set()
    for line in out.splitlines():
        name, _, email = line.partition("\t")
        if not BOT_AUTHOR.search(line):
            people.add((email or name).lower())
    return len(people)


def _key(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def source_key(path):
    return _key(os.path.basename(path).rsplit(".", 1)[0])


def test_key(path):
    """The name of the code a test file is about: OrderServiceTest.php -> orderservice."""
    stem = os.path.basename(path).rsplit(".", 1)[0]
    stem = re.sub(r"(?i)^test[_-]", "", stem)
    stem = re.sub(r"(?i)[._-]?(tests?|specs?)$", "", stem)
    stem = re.sub(r"(?<=[a-z])IT$", "", stem)
    return _key(stem)


class TestIndex:
    """Test files found by name, for any source file."""

    def __init__(self, tracked, exts, keep_dirs):
        self.by_key = defaultdict(list)
        self.sources = []
        self.test_files = 0
        for p in sorted(tracked):
            why = exclusion(p, False, exts, keep_dirs)  # --include-tests only affects churn
            if why is None:
                self.sources.append(p)
            elif why.startswith("test"):
                self.test_files += 1
                self.by_key[test_key(p)].append(p)

    def for_file(self, path):
        key = source_key(path)
        hits = self.by_key.get(key, [])
        if key in GENERIC_STEMS:
            folder = _key(os.path.basename(os.path.dirname(path)))
            hits = [t for t in hits if folder and folder in {_key(x) for x in t.split("/")[:-1]}]
        return hits


def name_tokens(path):
    """The words in a file's name that name a feature, not a layer or a job."""
    stem = os.path.basename(path).rsplit(".", 1)[0]
    stem = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", stem)
    words = {w.lower() for w in re.split(r"[^A-Za-z0-9]+", stem) if len(w) >= 4}
    return words - LAYER_WORDS


def stable_complex(repo, scope, scored_paths, freq, is_excluded, limit):
    """Large, complex files that rarely change.

    Churn alone cannot see them: they are untouched because they are finished,
    feared or dead. Picks the 300 biggest candidates by size (no file reads),
    then ranks those by complexity.
    """
    listing = git(repo, "ls-tree", "-r", "-l", "HEAD", *(["--", scope] if scope else []),
                  check=False)
    sized = []
    for line in listing.splitlines():
        head, _, path = line.partition("\t")
        fields = head.split()
        if len(fields) < 4 or not fields[3].isdigit() or int(fields[3]) > 1_000_000:
            continue
        if path in scored_paths or freq.get(path, 0) > 2 or is_excluded(path):
            continue
        sized.append((int(fields[3]), path))
    sized.sort(reverse=True)
    rows = []
    for _, path in sized[:300]:
        mm = measure(path, git(repo, "show", f"HEAD:{path}", check=False), with_lizard=False)
        rows.append({"path": path, "changes": freq.get(path, 0), **mm})
    rows = [r for r in rows if r["complexity"] >= MIN_STABLE_COMPLEXITY]
    rows.sort(key=lambda r: (-r["complexity"], -r["loc"], r["path"]))
    rows = rows[:limit]
    for r in rows:
        detail = lizard_detail(r["path"], git(repo, "show", f"HEAD:{r['path']}", check=False))
        r["most_complex_function"] = detail["function"] if detail else None
        r["most_complex_function_ccn"] = detail["ccn"] if detail else None
        r["last_changed"] = git(repo, "log", "-1", "--format=%cs", "HEAD", "--",
                                r["path"], check=False).strip() or None
    return rows


class ModuleMap:
    """Group files into modules.

    A module is `depth` folders deep, counted below the point where the tree
    starts to branch. A top-level folder that holds nothing but one child
    folder, again and again (`src/main/java/com/acme/`), is skipped through, so
    `billing` and `users` are compared as modules and not lumped together as
    `src/main`.
    """

    def __init__(self, paths, depth):
        self.depth = depth
        self.children = defaultdict(set)
        self.has_file = set()
        for p in paths:
            parts = p.split("/")
            for i in range(len(parts) - 1):
                self.children["/".join(parts[:i])].add(parts[i])
            self.has_file.add("/".join(parts[:-1]))
        self.cache = {}

    def base(self, top):
        if top not in self.cache:
            node = top
            while node not in self.has_file and len(self.children[node]) == 1:
                node = f"{node}/{next(iter(self.children[node]))}"
            self.cache[top] = node
        return self.cache[top]

    def of(self, path):
        dirs = path.split("/")[:-1]
        if not dirs:
            return "(root)"
        base = self.base(dirs[0])
        base_parts = base.split("/")
        below = dirs[len(base_parts):]
        return "/".join(base_parts + below[:self.depth])


def size_ranking(root, scope, args, keep_dirs, extensions, reason):
    """No history available: rank files by complexity and size."""
    base = os.path.join(root, scope) if scope else root
    rows = []
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d.lower() not in SAFE_EXCLUDED_DIRS
                       and not (d.lower() in AMBIGUOUS_EXCLUDED_DIRS
                                and d.lower() not in keep_dirs)]
        for name in filenames:
            rel = os.path.relpath(os.path.join(dirpath, name), root).replace(os.sep, "/")
            if exclusion(rel, args.include_tests, extensions, keep_dirs):
                continue
            try:
                with open(os.path.join(root, rel), encoding="utf-8", errors="replace") as fh:
                    text = fh.read(2_000_000)
            except OSError:
                continue
            m = measure(rel, text)
            m["path"] = rel
            rows.append(m)
    rows.sort(key=lambda r: (-r["complexity"], -r["loc"]))
    rows = rows[:args.top]
    meta = {"repo": root, "history": False, "reason": reason,
            "path_filter": scope or None}
    if args.json:
        print(json.dumps({"meta": meta, "files": rows}, indent=2))
        return 0
    print(f"# Size and complexity ranking for {os.path.basename(root)}\n")
    print(f"NOTE: no git history ({reason}). Files are ranked by decision points "
          f"and size only; nothing here says how often a file changes.\n")
    print("| # | File | LOC | Complexity | Per 100 LOC | Most complex function |")
    print("|---|---|---|---|---|---|")
    for i, r in enumerate(rows, 1):
        fn = (f"`{r['most_complex_function']}` ({r['most_complex_function_ccn']})"
              if r["most_complex_function"] else "n/a")
        print(f"| {i} | `{r['path']}` | {r['loc']} | {r['complexity']} | "
              f"{r['complexity_per_100_loc']} | {fn} |")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".",
                    help="repository path, or a folder inside one (default: .). "
                         "A folder inside a repository limits the review to it.")
    ap.add_argument("--path", default="",
                    help="limit to this subdirectory, relative to --repo")
    ap.add_argument("--months", type=int, default=12,
                    help="window length in months before HEAD's date (default 12)")
    ap.add_argument("--max-changes", type=int, default=2000,
                    help="cap on changes read from history (default 2000)")
    ap.add_argument("--top", type=int, default=15, help="hot spots to list (default 15)")
    ap.add_argument("--module-depth", type=int, default=2,
                    help="folders deep that make up a module (default 2), counted "
                         "below single-child folders such as src/main/java/com/acme. "
                         "Use 1 for coarser modules.")
    ap.add_argument("--coupling-max-files", type=int, default=40,
                    help="ignore changes touching more files than this when "
                         "measuring coupling; bulk renames and formatting runs "
                         "couple everything to everything (default 40)")
    ap.add_argument("--coupling-min-shared", type=int, default=3,
                    help="minimum shared changes for a coupled pair (default 3)")
    ap.add_argument("--bulk-files", type=int, default=200,
                    help="ignore changes touching more source files than this "
                         "everywhere, not only in coupling: formatter runs, mass "
                         "renames and vendor drops are not design signals "
                         "(default 200)")
    ap.add_argument("--stable-top", type=int, default=10,
                    help="large, complex, rarely changed files to list; 0 turns "
                         "the list off (default 10)")
    ap.add_argument("--include-tests", action="store_true",
                    help="count test files too")
    ap.add_argument("--all-files", action="store_true",
                    help="count every text file, not only source extensions")
    ap.add_argument("--ext", action="append", default=[], metavar="EXT[,EXT]",
                    help="also count files with these extensions (for example "
                         "html,graphql). Repeatable.")
    ap.add_argument("--keep-dir", action="append", default=[], metavar="NAME",
                    help="count a directory with this name even though it is on "
                         "the build-output list (dist, build, out, target, gen, "
                         "generated, external, contrib, obj, migrate, migration) "
                         "or looks like a test folder (spec, testing, fixtures). "
                         "Repeatable.")
    ap.add_argument("--no-history", action="store_true",
                    help="skip git history and rank files by size and complexity")
    ap.add_argument("--json", action="store_true", help="print JSON instead of markdown")
    args = ap.parse_args()

    keep_dirs = {d.lower() for d in args.keep_dir}
    extra_exts = {e.strip().lstrip(".").lower() for chunk in args.ext
                  for e in chunk.split(",") if e.strip()}
    extensions = None if args.all_files else SOURCE_EXTENSIONS | extra_exts
    start = os.path.abspath(args.repo)
    if not os.path.isdir(start):
        print(f"error: {start} is not a directory", file=sys.stderr)
        return 2

    try:
        if args.no_history:
            raise RuntimeError("history skipped with --no-history")
        repo = git(start, "rev-parse", "--show-toplevel").strip()
        prefix = git(start, "rev-parse", "--show-prefix").strip().rstrip("/")
    except (RuntimeError, FileNotFoundError) as exc:
        reason = str(exc) if args.no_history else "not a git repository"
        return size_ranking(start, args.path.strip("/"), args, keep_dirs, extensions, reason)
    scope = "/".join(x for x in (prefix, args.path.strip("/")) if x)

    if not git(repo, "rev-parse", "--verify", "-q", "HEAD", check=False).strip():
        return size_ranking(repo, scope, args, keep_dirs, extensions, "no commits yet")

    shallow = git(repo, "rev-parse", "--is-shallow-repository", check=False).strip() == "true"
    head = git(repo, "rev-parse", "--short", "HEAD").strip()
    branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD", check=False).strip()
    # Untracked files (such as a report written earlier) do not change HEAD's line numbers.
    dirty = bool(git(repo, "status", "--porcelain", "--untracked-files=no",
                     check=False).strip())
    head_date = git(repo, "log", "-1", "--format=%cI", "HEAD").strip()
    # The window ends at HEAD's commit date, not today.
    y, m, d = (int(x) for x in head_date[:10].split("-"))
    m -= args.months
    while m <= 0:
        m += 12
        y -= 1
    since = f"{y:04d}-{m:02d}-{min(d, 28):02d}"

    log_args = ["log", "--first-parent", "-m", "--numstat", "--find-renames",
                "--format=@@%H|%cs|%P|%s", f"--since={since}",
                f"-n{args.max_changes}", "HEAD"]
    if scope:
        log_args += ["--", scope]
    raw_changes = list(parse_numstat_log(git(repo, *log_args)))
    changes, origin = follow_renames(raw_changes)

    tracked = set(git(repo, "ls-files", *([scope] if scope else [])).splitlines())

    def select(exts):
        """Keep the files worth counting in each change.

        Returns the filtered changes, what was left out (reason -> file -> how
        many changes touched it), and how many whole changes were ignored as
        aggregate merges or bulk changes.
        """
        out, excluded = [], defaultdict(Counter)
        skipped = Counter()
        for sha, date, parents, subject, files in changes:
            if parents > 1 and AGGREGATE_MERGE.search(subject):
                skipped["aggregate_merges"] += 1
                out.append((sha, date, {}))
                continue
            kept = {}
            for p, c in files.items():
                if p not in tracked:
                    continue
                why = exclusion(p, args.include_tests, exts, keep_dirs)
                if why:
                    excluded[why][p] += 1
                else:
                    kept[p] = c
            if len(kept) > args.bulk_files:
                skipped["bulk_changes"] += 1
                kept = {}
            out.append((sha, date, kept))
        return out, excluded, skipped

    filtered, excluded, skipped = select(extensions)
    fallback_all_files = False
    if extensions and not skipped and not any(f for _, _, f in filtered):
        filtered, excluded, skipped = select(None)
        fallback_all_files = True
    active_exts = None if fallback_all_files else extensions

    modmap = ModuleMap([p for p in tracked if not exclusion(
        p, args.include_tests, active_exts, keep_dirs)], args.module_depth)

    freq, lines = Counter(), Counter()
    for _, _, files in filtered:
        for p, c in files.items():
            freq[p] += 1
            lines[p] += c

    # The tree just before the window opened, to measure growth. When the
    # window reaches back to the first commit, every file is new.
    window_start_sha, window_covers_root = None, False
    if raw_changes:
        oldest = raw_changes[-1][0]
        window_start_sha = git(repo, "rev-parse", "--verify", "-q", f"{oldest}^1",
                               check=False).strip() or None
        window_covers_root = window_start_sha is None and not shallow

    # Score the most-changed files, then rank the pool by score. A file with
    # fewer changes but far more complexity can outrank a trivial busy one.
    pool_size = max(args.top * 4, 40)
    scored = []
    for path, n in freq.most_common(pool_size):
        text = git(repo, "show", f"HEAD:{path}", check=False)
        mm = measure(path, text)
        before = 0 if window_covers_root else None
        if window_start_sha:
            old_path = origin.get(path, path)
            old = subprocess.run(
                ["git", "-C", repo, "show", f"{window_start_sha}:{old_path}"],
                capture_output=True, text=True, errors="replace")
            before = count_loc(old.stdout) if old.returncode == 0 else 0
        scored.append({
            "path": path,
            "changes": n,
            "lines_churned": lines[path],
            "loc": mm["loc"],
            "loc_at_window_start": before,
            "growth": None if before is None else mm["loc"] - before,
            "complexity": mm["complexity"],
            "complexity_per_100_loc": mm["complexity_per_100_loc"],
            "most_complex_function": mm["most_complex_function"],
            "most_complex_function_ccn": mm["most_complex_function_ccn"],
            "score": round(n * math.log2(2 + mm["complexity"]), 1),
        })
    scored.sort(key=lambda h: (-h["score"], -h["changes"], h["path"]))
    hotspots = scored[:args.top]
    tests = TestIndex(tracked, active_exts, keep_dirs)
    for h in hotspots:
        h["authors"] = distinct_authors(repo, since, h["path"])
        h["tests_by_name"] = tests.for_file(h["path"])[:3]

    stable = stable_complex(repo, scope, {h["path"] for h in hotspots}, freq,
                            lambda p: exclusion(p, args.include_tests, active_exts, keep_dirs),
                            args.stable_top) if args.stable_top > 0 else []

    modules = defaultdict(lambda: {"changes": 0, "files": set(), "lines_churned": 0})
    for sha, _, files in filtered:
        touched = {modmap.of(p) for p in files}
        for mod in touched:
            modules[mod]["changes"] += 1
        for p, c in files.items():
            mod = modules[modmap.of(p)]
            mod["files"].add(p)
            mod["lines_churned"] += c
    module_rows = sorted(
        ({"module": k, "changes": v["changes"], "files_touched": len(v["files"]),
          "lines_churned": v["lines_churned"]} for k, v in modules.items()),
        key=lambda r: -r["changes"])[:args.top]

    module_source_files, module_tested = Counter(), Counter()
    for src in tests.sources:
        mod = modmap.of(src)
        module_source_files[mod] += 1
        module_tested[mod] += bool(tests.for_file(src))
    for r in module_rows:
        r["source_files"] = module_source_files[r["module"]]
        r["files_with_test_by_name"] = module_tested[r["module"]]

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
            "cross_module": modmap.of(a) != modmap.of(b),
            "share_a_name": bool(name_tokens(a) & name_tokens(b)),
        })
    # Pairs in different modules whose names have nothing in common come first: in
    # a repo organised by layer, `OrderController` and `OrderRepository` are one
    # feature's slice, and always in different modules.
    coupling.sort(key=lambda r: (-(r["cross_module"] and not r["share_a_name"]),
                                 -r["cross_module"], -r["shared_changes"], -r["degree"]))

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

    merges = sum(1 for _, _, parents, _, _ in changes if parents > 1)
    pr_style = sum(1 for _, _, parents, subject, _ in changes
                   if parents > 1 or PR_SUBJECT.search(subject))
    linear_warning = (len(changes) >= 10 and merges == 0
                      and pr_style < len(changes) / 2)

    try:
        import lizard  # noqa: F401
        have_lizard = True
    except ImportError:
        have_lizard = False

    ranked_excluded = sorted(excluded.items(), key=lambda kv: -len(kv[1]))
    excluded_summary = {why: len(paths) for why, paths in ranked_excluded}
    excluded_top = {why: [p for p, _ in paths.most_common(2)] for why, paths in ranked_excluded}
    meta = {
        "repo": repo,
        "head": head,
        "branch": branch,
        "working_tree_dirty": dirty,
        "head_date": head_date[:10],
        "window_since": since,
        "oldest_change_read": raw_changes[-1][1] if raw_changes else None,
        "changes_read": len(changes),
        "changes_with_source_files": sum(1 for _, _, f in filtered if f),
        "hit_max_changes": len(changes) >= args.max_changes,
        "shallow_clone": shallow,
        "path_filter": scope or None,
        "merge_commits": merges,
        "pr_style_changes": pr_style,
        "history_looks_linear": linear_warning,
        "complexity_method": "decision keyword count per file"
        + (" + lizard per-function maximum" if have_lizard else ""),
        "file_filter": "all files (no source files matched)" if fallback_all_files
        else ("all files" if args.all_files else "source extensions"),
        "tests_included": args.include_tests,
        "kept_dirs": sorted(keep_dirs),
        "coupling_skipped_bulk_changes": skipped_bulk,
        "aggregate_merges_ignored": skipped["aggregate_merges"],
        "bulk_changes_ignored": skipped["bulk_changes"],
        "thin_history": sum(1 for _, _, f in filtered if f) < THIN_HISTORY,
        "excluded_files": excluded_summary,
        "excluded_top_files": excluded_top,
        "pool_size": pool_size,
        "source_files": len(tests.sources),
        "test_files": tests.test_files,
    }
    result = {"meta": meta, "hotspots": hotspots, "stable_complex": stable,
              "modules": module_rows, "coupling": coupling}

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    print(f"# Hot spots for {os.path.basename(repo)} @ {head}\n")
    print(f"Branch: {branch}. Window: {since} .. {meta['head_date']} (anchored on HEAD). "
          f"Changes read: {meta['changes_read']}; "
          f"with source files: {meta['changes_with_source_files']}. "
          f"A change is one PR or direct commit on the first-parent history.")
    if scope:
        print(f"Scope: `{scope}` only. Coupling to files outside it is not visible.")
    print(f"Complexity: {meta['complexity_method']}. "
          f"Score = changes x log2(2 + complexity), ranked over the {pool_size} "
          f"most-changed files. "
          f"Files: {meta['file_filter']}, tests {'included' if args.include_tests else 'excluded'}. "
          f"Modules: {args.module_depth} folders deep, below folders that only nest one child.")
    if dirty:
        print("WARNING: the working tree has uncommitted changes. This analysis reads "
              "HEAD; line numbers from files on disk may not match it.")
    if meta["hit_max_changes"]:
        print(f"WARNING: hit --max-changes; the oldest change read is "
              f"{meta['oldest_change_read']}, so the window is shorter than requested. "
              f"Re-run with --max-changes {args.max_changes * 2 + 1000}, or shorten --months.")
    if meta["thin_history"]:
        print(f"WARNING: thin history; only {meta['changes_with_source_files']} changes "
              f"touched source files (under {THIN_HISTORY}). Churn numbers are weak. "
              f"Widen --months (24, then 36).")
    if skipped["aggregate_merges"]:
        print(f"NOTE: {skipped['aggregate_merges']} aggregate merge(s) (a long-lived branch "
              f"merged into another, or a release merge) were left out of churn and "
              f"coupling, because their files were already counted in the original "
              f"changes. If this is a release branch, review the integration branch "
              f"(develop) for finer-grained history.")
    if skipped["bulk_changes"]:
        print(f"NOTE: {skipped['bulk_changes']} bulk change(s) (> {args.bulk_files} source "
              f"files each: formatter runs, mass renames) were left out of churn and "
              f"coupling. Change with --bulk-files.")
    if shallow:
        print("WARNING: shallow clone; history is truncated and churn is understated.")
    if linear_warning:
        print(f"WARNING: history is linear ({merges} merge commits, {pr_style} of "
              f"{len(changes)} changes carry a PR reference). If PRs were "
              f"rebase-merged, a PR with several commits counts as several changes, "
              f"which overstates churn and coupling. Squash merges look the same "
              f"but count correctly.")
    if fallback_all_files:
        print("NOTE: no files with source extensions changed; counted all files instead.")
    if excluded_summary:
        shown = "; ".join(
            f"{why}: {n} (most changed: {', '.join(f'`{p}`' for p in excluded_top[why])})"
            for why, n in list(excluded_summary.items())[:8])
        print(f"Left out (files changed in the window): {shown}. "
              f"Real code left out? Re-run with --keep-dir NAME (folders), "
              f"--ext EXT (file types) or --all-files.")
    print()

    print("## Hot spots (by score)\n")
    print(f"Tests: {tests.test_files} test files and {len(tests.sources)} source files in the "
          f"repo. \"Tests by name\" matches a test file to the code it is named after "
          f"(`OrderServiceTest` to `OrderService`); \"none\" still needs a search for the "
          f"file's main class in the test folders. Authors: people who changed the file in "
          f"the window, bots left out.\n")
    print("| # | File | Changes | Authors | Lines churned | LOC | Growth | Complexity | Per 100 LOC | Score | Tests by name |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for i, h in enumerate(hotspots, 1):
        growth = "n/a" if h["growth"] is None else (
            "new" if h["loc_at_window_start"] == 0 else f"{h['growth']:+d}")
        cx = str(h["complexity"])
        if h["most_complex_function"]:
            cx += f" (max {h['most_complex_function_ccn']} in `{h['most_complex_function']}`)"
        found = h["tests_by_name"]
        tcell = ", ".join(f"`{t}`" for t in found[:2]) + (" and more" if len(found) > 2 else "") \
            if found else "none"
        print(f"| {i} | `{h['path']}` | {h['changes']} | {h['authors']} | {h['lines_churned']} | "
              f"{h['loc']} | {growth} | {cx} | "
              f"{'n/a' if h['complexity_per_100_loc'] is None else h['complexity_per_100_loc']} | "
              f"{h['score']} | {tcell} |")

    if stable:
        print("\n## Large, complex, rarely changed\n")
        print("Files with at most 2 changes in the window, ranked by complexity. Each is "
              "finished, feared or dead; the hot spot score cannot tell which.\n")
        print("| # | File | Changes | LOC | Complexity | Per 100 LOC | Last changed |")
        print("|---|---|---|---|---|---|---|")
        for i, s in enumerate(stable, 1):
            cx = str(s["complexity"])
            if s["most_complex_function"]:
                cx += f" (max {s['most_complex_function_ccn']} in `{s['most_complex_function']}`)"
            print(f"| {i} | `{s['path']}` | {s['changes']} | {s['loc']} | {cx} | "
                  f"{s['complexity_per_100_loc']} | {s['last_changed'] or 'n/a'} |")

    print(f"\n## Most changed modules (depth {args.module_depth})\n")
    print("| Module | Changes | Files touched | Lines churned | Source files with a test by name |")
    print("|---|---|---|---|---|")
    for r in module_rows:
        n, m = r["files_with_test_by_name"], r["source_files"]
        share = f"{n} of {m} ({round(100 * n / m)}%)" if m else "n/a"
        print(f"| `{r['module']}` | {r['changes']} | {r['files_touched']} | "
              f"{r['lines_churned']} | {share} |")

    print("\n## Files changed together\n")
    print(f"Pairs sharing at least {args.coupling_min_shared} changes, where at least half "
          f"of the less-changed file's changes also touched the other. "
          f"{skipped_bulk} larger changes (> {args.coupling_max_files} files) ignored. "
          f"Cross-module pairs with unrelated names first; a pair that shares a name "
          f"is probably one feature's slice.\n")
    if not coupling:
        print("No coupled pairs above the thresholds.")
    else:
        print("| File A | File B | Shared changes | Degree | Cross-module | Share a name |")
        print("|---|---|---|---|---|---|")
        for c in coupling:
            print(f"| `{c['a']}` | `{c['b']}` | {c['shared_changes']} | {c['degree']} | "
                  f"{'yes' if c['cross_module'] else 'no'} | "
                  f"{'yes' if c['share_a_name'] else 'no'} |")
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
