#!/usr/bin/env python3
"""Check WCAG report accounting and Markdown structure; never judge WCAG semantics."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path


SKILL_VERSION = "2.1.0"
VERDICTS = ("✅ PASS", "⚪ N/A", "⚠️ NEEDS_REVIEW", "❌ FAIL")
PRIORITIES = ("Critical", "Serious", "Moderate", "Minor")


def read_checklist(path: Path) -> tuple[list[tuple[str, str, str]], list[str]]:
    errors: list[str] = []
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    except OSError as exc:
        return [], [f"cannot read checklist: {exc}"]

    expected_columns = {
        "sc_id", "name", "level", "wcag_version", "static_analyzable", "check_hint"
    }
    if not rows or set(rows[0]) != expected_columns:
        errors.append("checklist columns are not canonical")
    criteria = [(row["sc_id"], row["name"], row["level"]) for row in rows]
    levels = Counter(level for _, _, level in criteria)
    if len(criteria) != 55 or len({sc_id for sc_id, _, _ in criteria}) != 55:
        errors.append("checklist must contain 55 unique criteria")
    if levels != Counter({"A": 31, "AA": 24}):
        errors.append("checklist must contain 31 Level A and 24 Level AA criteria")
    if any(sc_id == "4.1.1" for sc_id, _, _ in criteria):
        errors.append("obsolete criterion 4.1.1 must not be active")
    return criteria, errors


def section(text: str, heading: str) -> str | None:
    match = re.search(
        rf"^## {re.escape(heading)}\s*$([\s\S]*?)(?=^## |\Z)",
        text,
        re.MULTILINE,
    )
    return match.group(1) if match else None


def parse_ledger(text: str) -> list[tuple[str, str, str, str]]:
    body = section(text, "Conformance criteria ledger")
    if body is None:
        return []
    pattern = re.compile(
        r"^\|\s*(\d+\.\d+\.\d+)\s*\|\s*([^|]+?)\s*\|\s*(A|AA)\s*\|\s*"
        r"(✅ PASS|⚪ N/A|⚠️ NEEDS_REVIEW|❌ FAIL)\s*\|",
        re.MULTILINE,
    )
    return [tuple(match.groups()) for match in pattern.finditer(body)]


def parse_manual_review_ids(text: str) -> list[str]:
    body = section(text, "Manual verification plan")
    if body is None:
        return []
    priority = "|".join(PRIORITIES)
    return re.findall(
        rf"^\|\s*(\d+\.\d+\.\d+)\s*\|\s*(?:{priority})\s*\|",
        body,
        re.MULTILINE,
    )


def validate_report(text: str, criteria: list[tuple[str, str, str]]) -> list[str]:
    errors: list[str] = []
    if re.search(r"^# .*\[PARTIAL\]", text, re.MULTILINE):
        return ["check_report.py currently checks completed reports only"]
    if "[[" in text or "]]" in text:
        errors.append("report contains an unfilled template placeholder")
    if not re.search(
        rf"^\*\*Skill version:\*\*\s*{re.escape(SKILL_VERSION)}\s*$", text, re.MULTILINE
    ):
        errors.append(f"report must declare skill version {SKILL_VERSION}")
    if "not a certification or WCAG conformance claim" not in text:
        errors.append("report is missing the static-audit disclaimer")
    if not re.search(r"^\*\*Evaluator coverage:\*\* COMPLETE\b", text, re.MULTILINE):
        errors.append("completed report must declare Evaluator coverage: COMPLETE")

    model_values: list[str] = []
    for label in ("Initial draft author", "Independent review"):
        match = re.search(rf"^\*\*{label}:\*\*\s*(.+)$", text, re.MULTILINE)
        if not match:
            errors.append(f"report is missing {label}")
        else:
            model_values.append(re.sub(r"\s+", " ", match.group(1).strip().lower()))
    if len(model_values) == 2 and model_values[0] == model_values[1]:
        errors.append("initial and independent evaluators must be distinct")

    ledger = parse_ledger(text)
    actual_criteria = [(sc_id, name, level) for sc_id, name, level, _ in ledger]
    if actual_criteria != criteria:
        errors.append("ledger must contain the canonical 55 criteria in exact order")

    counts = Counter(verdict for _, _, _, verdict in ledger)
    for verdict in VERDICTS:
        match = re.search(
            rf"^\|\s*{re.escape(verdict)}\s*\|\s*(\d+)\s*\|\s*$",
            text,
            re.MULTILINE,
        )
        if not match:
            errors.append(f"summary is missing {verdict}")
        elif int(match.group(1)) != counts[verdict]:
            errors.append(
                f"summary count for {verdict} is {match.group(1)}, ledger count is {counts[verdict]}"
            )
    total = re.search(r"^\|\s*\*\*Total\*\*\s*\|\s*\*\*(\d+)\*\*\s*\|", text, re.MULTILINE)
    if not total or int(total.group(1)) != len(ledger) or len(ledger) != 55:
        errors.append("summary total and ledger must both equal 55")

    fail_ids = [sc_id for sc_id, _, _, verdict in ledger if verdict == "❌ FAIL"]
    confirmed = section(text, "Confirmed findings")
    finding_ids = re.findall(r"^### ❌ FAIL (\d+\.\d+\.\d+) —", confirmed or "", re.MULTILINE)
    if finding_ids != fail_ids:
        errors.append("Confirmed findings must contain exactly one section per FAIL in ledger order")

    review_ids = [sc_id for sc_id, _, _, verdict in ledger if verdict == "⚠️ NEEDS_REVIEW"]
    if parse_manual_review_ids(text) != review_ids:
        errors.append(
            "Manual verification plan must contain exactly one valid-priority row per NEEDS_REVIEW in ledger order"
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checklist", type=Path)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()

    criteria, errors = read_checklist(args.checklist)
    try:
        text = args.report.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"cannot read report: {exc}")
        text = ""
    if criteria and text:
        errors.extend(validate_report(text, criteria))

    if errors:
        print("check_report: FAIL", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print("check_report: OK (structure and accounting only; WCAG judgments not evaluated)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
