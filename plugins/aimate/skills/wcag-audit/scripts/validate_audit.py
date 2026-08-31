#!/usr/bin/env python3
"""Validate the canonical WCAG CSV and, optionally, a generated report."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path


EXPECTED_CRITERIA = [
    ("1.1.1", "Non-text Content", "A", "2.0"),
    ("1.2.1", "Audio-only and Video-only (Prerecorded)", "A", "2.0"),
    ("1.2.2", "Captions (Prerecorded)", "A", "2.0"),
    ("1.2.3", "Audio Description or Media Alternative (Prerecorded)", "A", "2.0"),
    ("1.2.4", "Captions (Live)", "AA", "2.0"),
    ("1.2.5", "Audio Description (Prerecorded)", "AA", "2.0"),
    ("1.3.1", "Info and Relationships", "A", "2.0"),
    ("1.3.2", "Meaningful Sequence", "A", "2.0"),
    ("1.3.3", "Sensory Characteristics", "A", "2.0"),
    ("1.3.4", "Orientation", "AA", "2.1"),
    ("1.3.5", "Identify Input Purpose", "AA", "2.1"),
    ("1.4.1", "Use of Color", "A", "2.0"),
    ("1.4.2", "Audio Control", "A", "2.0"),
    ("1.4.3", "Contrast (Minimum)", "AA", "2.0"),
    ("1.4.4", "Resize Text", "AA", "2.0"),
    ("1.4.5", "Images of Text", "AA", "2.0"),
    ("1.4.10", "Reflow", "AA", "2.1"),
    ("1.4.11", "Non-text Contrast", "AA", "2.1"),
    ("1.4.12", "Text Spacing", "AA", "2.1"),
    ("1.4.13", "Content on Hover or Focus", "AA", "2.1"),
    ("2.1.1", "Keyboard", "A", "2.0"),
    ("2.1.2", "No Keyboard Trap", "A", "2.0"),
    ("2.1.4", "Character Key Shortcuts", "A", "2.1"),
    ("2.2.1", "Timing Adjustable", "A", "2.0"),
    ("2.2.2", "Pause, Stop, Hide", "A", "2.0"),
    ("2.3.1", "Three Flashes or Below Threshold", "A", "2.0"),
    ("2.4.1", "Bypass Blocks", "A", "2.0"),
    ("2.4.2", "Page Titled", "A", "2.0"),
    ("2.4.3", "Focus Order", "A", "2.0"),
    ("2.4.4", "Link Purpose (In Context)", "A", "2.0"),
    ("2.4.5", "Multiple Ways", "AA", "2.0"),
    ("2.4.6", "Headings and Labels", "AA", "2.0"),
    ("2.4.7", "Focus Visible", "AA", "2.0"),
    ("2.4.11", "Focus Not Obscured (Minimum)", "AA", "2.2"),
    ("2.5.1", "Pointer Gestures", "A", "2.1"),
    ("2.5.2", "Pointer Cancellation", "A", "2.1"),
    ("2.5.3", "Label in Name", "A", "2.1"),
    ("2.5.4", "Motion Actuation", "A", "2.1"),
    ("2.5.7", "Dragging Movements", "AA", "2.2"),
    ("2.5.8", "Target Size (Minimum)", "AA", "2.2"),
    ("3.1.1", "Language of Page", "A", "2.0"),
    ("3.1.2", "Language of Parts", "AA", "2.0"),
    ("3.2.1", "On Focus", "A", "2.0"),
    ("3.2.2", "On Input", "A", "2.0"),
    ("3.2.3", "Consistent Navigation", "AA", "2.0"),
    ("3.2.4", "Consistent Identification", "AA", "2.0"),
    ("3.2.6", "Consistent Help", "A", "2.2"),
    ("3.3.1", "Error Identification", "A", "2.0"),
    ("3.3.2", "Labels or Instructions", "A", "2.0"),
    ("3.3.3", "Error Suggestion", "AA", "2.0"),
    ("3.3.4", "Error Prevention (Legal, Financial, Data)", "AA", "2.0"),
    ("3.3.7", "Redundant Entry", "A", "2.2"),
    ("3.3.8", "Accessible Authentication (Minimum)", "AA", "2.2"),
    ("4.1.2", "Name, Role, Value", "A", "2.0"),
    ("4.1.3", "Status Messages", "AA", "2.1"),
]
EXPECTED_IDS = [criterion[0] for criterion in EXPECTED_CRITERIA]
REQUIRED_COLUMNS = [
    "sc_id", "name", "level", "wcag_version", "static_analyzable", "check_hint"
]
VERDICT_TOKENS = ("✅ PASS", "⚪ N/A", "⚠️ NEEDS_REVIEW", "❌ FAIL")


def validate_csv(path: Path) -> list[str]:
    errors: list[str] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != REQUIRED_COLUMNS:
            errors.append(f"CSV columns {reader.fieldnames!r} != {REQUIRED_COLUMNS!r}")
        rows = list(reader)

    ids = [row.get("sc_id", "") for row in rows]
    criteria = [
        (row.get("sc_id"), row.get("name"), row.get("level"), row.get("wcag_version"))
        for row in rows
    ]
    if len(rows) != 55:
        errors.append(f"CSV row count {len(rows)} != 55")
    if ids != EXPECTED_IDS:
        errors.append("CSV IDs or order differ from the canonical WCAG 2.2 A/AA list")
    if criteria != EXPECTED_CRITERIA:
        errors.append("CSV names, levels, or introduced-version metadata differ from the canonical list")
    if len(set(ids)) != len(ids):
        errors.append("CSV contains duplicate success-criterion IDs")
    if "4.1.1" in ids:
        errors.append("Obsolete WCAG 2.2 criterion 4.1.1 must not be active")

    levels = Counter(row.get("level") for row in rows)
    if levels != Counter({"A": 31, "AA": 24}):
        errors.append(f"level counts {dict(levels)} != {{'A': 31, 'AA': 24}}")

    static_values = Counter(row.get("static_analyzable") for row in rows)
    for value in ("yes", "partial", "no"):
        if not static_values[value]:
            errors.append(f"CSV has no criteria classified static_analyzable={value}")

    for index, row in enumerate(rows, start=2):
        if row.get("wcag_version") not in {"2.0", "2.1", "2.2"}:
            errors.append(f"line {index}: invalid wcag_version")
        if row.get("static_analyzable") not in {"yes", "partial", "no"}:
            errors.append(f"line {index}: invalid static_analyzable")
        if any(not row.get(column, "").strip() for column in REQUIRED_COLUMNS):
            errors.append(f"line {index}: one or more required fields are empty")
    return errors


def validate_report(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    ledger_match = re.search(
        r"^## Conformance criteria ledger\s*$([\s\S]*?)^## ", text, re.MULTILINE
    )
    if not ledger_match:
        return ["report is missing a bounded Conformance criteria ledger section"]

    rows: list[tuple[str, str]] = []
    for line in ledger_match.group(1).splitlines():
        cells = [cell.strip() for cell in line.split("|")]
        if len(cells) >= 7 and re.fullmatch(r"\d+\.\d+\.\d+", cells[1]):
            rows.append((cells[1], cells[4]))

    ids = [item[0] for item in rows]
    if len(rows) != 55:
        errors.append(f"report ledger row count {len(rows)} != 55")
    if ids != EXPECTED_IDS:
        errors.append("report ledger IDs or order differ from the canonical checklist")
    if any(token not in VERDICT_TOKENS for _, token in rows):
        errors.append("report contains an invalid verdict token")
    if "{{" in text or "}}" in text:
        errors.append("report contains unfilled template placeholders")
    if "not a certification or WCAG conformance claim" not in text:
        errors.append("report is missing the required static-audit disclaimer")

    verdict_counts = Counter(verdict for _, verdict in rows)
    summary_labels = {
        "✅ PASS": "PASS",
        "⚪ N/A": "N/A",
        "⚠️ NEEDS_REVIEW": "NEEDS_REVIEW",
        "❌ FAIL": "FAIL",
    }
    for verdict, label in summary_labels.items():
        summary = re.search(rf"^\|\s*{re.escape(verdict)}\s*\|\s*(\d+)\s*\|$", text, re.MULTILINE)
        if not summary:
            errors.append(f"report summary is missing a numeric {label} count")
        elif int(summary.group(1)) != verdict_counts[verdict]:
            errors.append(
                f"report summary {label} count {summary.group(1)} != ledger count {verdict_counts[verdict]}"
            )

    for sc_id, verdict in rows:
        if verdict in {"⚠️ NEEDS_REVIEW", "❌ FAIL"}:
            heading = rf"^###\s+{re.escape(verdict)}\s+{re.escape(sc_id)}\s+—"
            if not re.search(heading, text, re.MULTILINE):
                errors.append(f"report is missing a detailed section for {verdict} {sc_id}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    errors = validate_csv(args.csv_path)
    if args.report:
        errors.extend(validate_report(args.report))
    if errors:
        print("validate_audit: FAIL", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print("validate_audit: OK (55 criteria; A=31; AA=24)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
