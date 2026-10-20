#!/usr/bin/env python3
"""Availability checks against new minimum OS versions (read-only).

Lists every #available, #unavailable, and @available in tracked Swift files and
classifies each against the minimums you pass:

- always-true: every platform it names is at or below the new minimum, so the
  check (or annotation) can go and only the available branch stays;
- always-false: an #unavailable check that can never be true any more;
- needed: at least one named platform is above its minimum;
- backport-candidate: an @available that marks code deprecated at or below the
  new minimum (typical for backport wrappers), so the wrapper can be replaced
  by the system API and removed;
- review: a form the script does not classify (obsoleted, unavailable,
  renamed, or a platform without a version), so read it yourself.

@available(*, ...) annotations do not concern OS versions and are skipped, as
are generated files (Generated, GeneratedSources, *.generated.swift).

A platform you do not pass keeps its current minimum, so a check that names it
stays "needed" unless that platform's version is also covered. The `*` wildcard
does not count as a platform.

Runs on Python 3.9, the version Xcode ships; run it with `xcrun python3`.

Usage: xcrun python3 availability.py --repo <path> --min iOS=18.0 [--min tvOS=17.0] [--json]
"""

import argparse
import json
import os
import re
import subprocess
import sys

if sys.version_info < (3, 9):
    sys.exit("Needs Python 3.9 or newer. Run it with Xcode's Python: xcrun python3 " + sys.argv[0])

SKIP_PARTS = {".build", "DerivedData", "checkouts", "Pods", "Carthage", "node_modules"}
CHECK_RE = re.compile(r"(#available|#unavailable|@available)\s*\(([^)]*)\)")
PLATFORM_RE = re.compile(r"\b(iOS|tvOS|watchOS|macOS|visionOS|macCatalyst|iOSApplicationExtension)\b\s*,?\s*(?:introduced:\s*)?(\d+(?:\.\d+){0,2})?")


def version(v):
    parts = [int(x) for x in v.split(".")]
    return tuple(parts + [0] * (3 - len(parts)))


def classify(kind, args, minimums):
    if kind == "@available" and args.strip().startswith("*"):
        return None, []
    if kind == "@available":
        dep = re.match(r"\s*(iOS|tvOS|watchOS|macOS|visionOS|macCatalyst)\b.*?\bdeprecated:\s*(\d+(?:\.\d+){0,2})", args)
        if dep:
            floor = minimums.get(dep.group(1))
            if floor is not None and version(dep.group(2)) <= floor:
                return "backport-candidate", []
            return "needed", []
        if re.search(r"\b(deprecated|obsoleted|unavailable|renamed|noasync)\b", args):
            return "review", []
    found = [(p, v) for p, v in PLATFORM_RE.findall(args)]
    if not found or any(not v for _, v in found):
        return "review", found
    covered = []
    for p, v in found:
        base = "iOS" if p == "iOSApplicationExtension" else p
        floor = minimums.get(base)
        covered.append(floor is not None and version(v) <= floor)
    if all(covered):
        return ("always-false" if kind == "#unavailable" else "always-true"), found
    return "needed", found


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--min", action="append", required=True, help="Platform=version, e.g. iOS=18.0")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    minimums = {}
    for m in args.min:
        p, _, v = m.partition("=")
        minimums[p] = version(v)
    repo = os.path.abspath(args.repo)
    out = subprocess.run(["git", "-C", repo, "ls-files", "*.swift"], capture_output=True, text=True, check=True).stdout
    files = [f for f in out.splitlines()
             if not (set(f.split("/")) & SKIP_PARTS)
             and not re.search(r"(^|/)(Generated|GeneratedSources)/|\.generated\.swift$", f)]

    rows = []
    for f in files:
        try:
            lines = open(os.path.join(repo, f), encoding="utf-8", errors="replace").read().splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines, 1):
            for m in CHECK_RE.finditer(line):
                verdict, platforms = classify(m.group(1), m.group(2), minimums)
                if verdict is None:
                    continue
                rows.append({"location": f"{f}:{i}", "kind": m.group(1), "args": m.group(2).strip(),
                             "verdict": verdict, "code": line.strip()[:140]})

    if args.json:
        json.dump(rows, sys.stdout, indent=2)
        return
    counts = {}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    print("Minimums:", ", ".join(f"{p} {'.'.join(map(str, v))}" for p, v in minimums.items()))
    print("Totals:", ", ".join(f"{k} {v}" for k, v in sorted(counts.items())) or "none")
    for verdict in ("always-true", "always-false", "backport-candidate", "review", "needed"):
        sel = [r for r in rows if r["verdict"] == verdict]
        if sel:
            print(f"\n{verdict} ({len(sel)}):")
            for r in sel:
                print(f"  {r['location']}  {r['kind']}({r['args']})")


if __name__ == "__main__":
    main()
