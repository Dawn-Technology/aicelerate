#!/usr/bin/env python3
"""Check an accessibility audit report's Criteria table against accessibility.md.

Every WCAG criterion listed in accessibility.md must appear exactly once in the
report's `Criteria` table, with one status from: fail, pass, needs check, not
applicable. Criteria that are not in accessibility.md must not appear. Prints the
counts per status for the report's summary, and exits 1 when the table is wrong.

Usage: check_report.py --report docs/<project>-accessibility-audit-<date>.md [--reference PATH]
"""
import argparse
import os
import re
import sys
from collections import Counter

STATUSES = ("fail", "needs check", "pass", "not applicable")
ID_RE = re.compile(r"^\|\s*(\d+\.\d+\.\d+)\b")


def criteria_ids(path):
    ids = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            match = ID_RE.match(line)
            if match:
                ids.append(match.group(1))
    return ids


def report_rows(path):
    """Rows of the table under the first heading named Criteria: (id, cells)."""
    rows, inside = [], False
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if re.match(r"^#+\s*`?Criteria\b", line.strip()):
                inside = True
                continue
            if inside and re.match(r"^#+\s", line):
                break
            if inside:
                match = ID_RE.match(line)
                if match:
                    cells = [c.strip().strip("`*").lower() for c in line.strip().strip("|").split("|")]
                    rows.append((match.group(1), cells))
    return rows


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--report", required=True)
    parser.add_argument("--reference", default=os.path.join(here, "..", "..", "ios-standards", "references", "accessibility.md"))
    args = parser.parse_args()

    expected = criteria_ids(args.reference)
    rows = report_rows(args.report)
    problems = []
    if not rows:
        problems.append("no `Criteria` section with a table whose rows start with a criterion number")
    seen = Counter(i for i, _ in rows)
    statuses = Counter()
    for criterion, cells in rows:
        found = [s for s in STATUSES if s in cells]
        if len(found) != 1:
            problems.append(f"{criterion}: needs exactly one status cell ({', '.join(STATUSES)}), found {found or 'none'}")
        else:
            statuses[found[0]] += 1
    for criterion in expected:
        if seen[criterion] == 0:
            problems.append(f"{criterion}: missing")
        elif seen[criterion] > 1:
            problems.append(f"{criterion}: listed {seen[criterion]} times")
    for criterion in seen:
        if criterion not in expected:
            problems.append(f"{criterion}: not in accessibility.md; remove it (only criteria from the reference are audited)")

    print(f"Criteria in accessibility.md: {len(expected)}; rows in report: {len(rows)}")
    print("Counts: " + ", ".join(f"{s} {statuses[s]}" for s in STATUSES))
    if problems:
        print("Problems:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("OK: every criterion appears once with one status.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
