#!/usr/bin/env python3
"""Assemble and check an ASVS report from verified Markdown verdicts."""

import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import re

SKILL = Path(__file__).resolve().parent.parent
STATUS_ICONS = {"PASS": "✅", "FAIL": "❌", "N/A": "⚪", "NEEDS_REVIEW": "⚠️"}
SEVERITY_ICONS = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}
REVIEW_REASONS = {"deployment", "external-docs", "external-system", "tool-failure"}
BLOCKS = ["finding", "review", "verification", "evidence", "rejected"]
COMPONENT_FIELDS = [
    "component", "component_path", "language", "framework", "database",
    "auth_method", "key_libraries",
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_verdicts(text):
    sections = re.findall(
        r"(?ms)^## (#\d+|other-findings)\n(.*?)(?=^## (?:#\d+|other-findings)\n|\Z)",
        text,
    )
    expected = [f"#{n}" for n in range(1, 71)] + ["other-findings"]
    require([label for label, _ in sections] == expected,
            "Verdicts must contain #1 through #70, then other-findings, exactly once")
    verdicts = []
    for label, body in sections:
        end = f"<!-- end {label} -->"
        require(body.rstrip().endswith(end), f"{label}: unfinished section")
        body = body.rstrip()[:-len(end)]
        parts = re.split(r"(?m)^<!-- (finding|review|verification|evidence|rejected) -->\n?", body)
        require(parts[1::2] == BLOCKS, f"{label}: missing, duplicate or reordered block markers")
        verdict = dict(zip(parts[1::2], (p.strip() for p in parts[2::2])))
        prefix = r"Status: (PASS|FAIL|N/A|NEEDS_REVIEW)\. " if label != "other-findings" else ""
        header = re.fullmatch(
            prefix + r"Candidates: (\d+) checked, (\d+) rejected\.", parts[0].strip(),
        )
        require(header is not None, f"{label}: invalid status or candidate counts")
        values = header.groups()
        verdict["status"] = values[0] if prefix else None
        checked, rejected = map(int, values[-2:])
        require(checked >= rejected, f"{label}: more rejected candidates than checked")
        rejected_lines = [line for line in verdict["rejected"].splitlines() if line.strip()]
        require(len(rejected_lines) == rejected and all(line.startswith("- ") for line in rejected_lines),
                f"{label}: rejected lines do not match the candidate count")
        verdict.update(checked=checked, rejected_count=rejected)
        verdicts.append(verdict)
    return verdicts


def table_cells(row, count, label):
    require(len(row.splitlines()) == 1, f"{label}: expected one table row")
    cells = re.split(r"(?<!\\)\|", row.strip())
    require(len(cells) == count + 2 and not cells[0] and not cells[-1],
            f"{label}: malformed table row")
    cells = [cell.strip() for cell in cells[1:-1]]
    require(all(cells), f"{label}: empty table cell")
    return cells


def severity(block, label):
    matches = re.findall(
        r"(?m)^- \*\*Severity\*\*: (\S+) (Critical|High|Medium|Low)\s*$", block,
    )
    require(len(matches) == 1, f"{label}: expected one severity")
    icon, level = matches[0]
    require(icon == SEVERITY_ICONS[level], f"{label}: severity icon does not match")
    return level


def validate_items(verdicts, requirements):
    owners = {}
    levels = {}
    for n, (verdict, requirement) in enumerate(zip(verdicts, requirements), 1):
        req_id = requirement["req_id"]
        label = f"#{n} {req_id}"
        row = table_cells(verdict["verification"], 5, label)
        require(row[0] == label, f"{label}: verification row has the wrong item or requirement ID")
        status = verdict["status"]
        require(row[3] == f"{STATUS_ICONS[status]} {status}", f"{label}: status mismatch")
        require(verdict["evidence"].startswith(f"### {label}: {status}\n"),
                f"{label}: missing or mismatched evidence heading")
        require(re.search(r"(?m)^- Searched: .+", verdict["evidence"]),
                f"{label}: evidence must record searches")
        if status == "NEEDS_REVIEW":
            review = table_cells(verdict["review"], 4, label)
            require(review[0] == label and review[1].strip("`") in REVIEW_REASONS,
                    f"{label}: invalid needs-review row or reason")
        else:
            require(not verdict["review"], f"{label}: unexpected needs-review row")
        if status == "FAIL":
            reference = re.fullmatch(r"See finding #(\d+)\.", verdict["finding"])
            if reference:
                owners[n] = int(reference[1])
                require(verdict["checked"] == verdict["rejected_count"] == 0,
                        f"{label}: shared findings must not count candidates twice")
            else:
                require(re.match(rf"### #{n} {re.escape(req_id)}(?:\s|:)", verdict["finding"]),
                        f"{label}: missing finding")
                owners[n] = n
                levels[n] = severity(verdict["finding"], label)
        else:
            require(not verdict["finding"], f"{label}: only FAIL items may have findings")
            require(verdict["checked"] == verdict["rejected_count"],
                    f"{label}: non-FAIL items cannot retain candidate failures")
    for n, owner in owners.items():
        require(owner in levels, f"#{n}: finding reference must name a detailed FAIL finding")
        require(re.search(rf"See finding #{owner}(?!\d)", verdicts[n - 1]["verification"]),
                f"#{n}: verification row must refer to finding #{owner}")
    return owners, levels


def other_findings(verdict):
    require(not verdict["review"] and not verdict["verification"],
            "other-findings: review and verification blocks must be empty")
    require(verdict["evidence"].startswith("### Other-findings checklist\n")
            and re.search(r"(?m)^- Searched: .+", verdict["evidence"]),
            "other-findings: missing checklist searches")
    if not verdict["finding"]:
        require(verdict["checked"] == verdict["rejected_count"],
                "other-findings: unchecked candidate failures remain")
        return [], []
    blocks = re.split(r"(?m)(?=^### O(?:\d+)?:)", verdict["finding"])
    require(not blocks[0].strip(), "other-findings: headings must use '### O: Title'")
    entries = []
    for block in blocks[1:]:
        level = severity(block, "other-findings")
        location = re.search(r"(?m)^  \| `([^`]+)` \|", block)
        require(location is not None, "other-findings: missing location table")
        entries.append((list(SEVERITY_ICONS).index(level), location[1], level, block.strip()))
    entries.sort(key=lambda entry: (entry[0], entry[1]))
    return [
        re.sub(r"^### O(?:\d+)?:", f"### O{n}:", entry[3], count=1)
        for n, entry in enumerate(entries, 1)
    ], [entry[2] for entry in entries]


def assemble(metadata, text):
    with (SKILL / "assets/OWASP_Application_Security_Verification_Standard_5.0.0_L1_en.csv").open(
        encoding="utf-8", newline="",
    ) as source:
        requirements = list(csv.DictReader(source))
    require(len(requirements) == 70, "ASVS CSV must contain exactly 70 requirements")
    verdicts = read_verdicts(text)
    items, other = verdicts[:70], verdicts[70]
    owners, levels = validate_items(items, requirements)
    other_blocks, other_levels = other_findings(other)
    counts = Counter(v["status"] for v in items)
    fail_levels = Counter(levels[owners[n]] for n in owners)
    other_counts = Counter(other_levels)
    applicable = 70 - counts["N/A"]
    require(applicable > 0, "Compliance score requires at least one applicable item")
    computed = {
        "count_total": 70,
        "count_fail": counts["FAIL"], "count_pass": counts["PASS"],
        "count_needs_review": counts["NEEDS_REVIEW"], "count_na": counts["N/A"],
        "compliance_score": f'{counts["PASS"] / applicable * 100:.1f}',
        "compliance_score_max": f'{(counts["PASS"] + counts["NEEDS_REVIEW"]) / applicable * 100:.1f}',
        "count_other": len(other_blocks),
        "count_candidates": sum(v["checked"] for v in verdicts),
        "count_rejected": sum(v["rejected_count"] for v in verdicts),
        "findings": "\n\n---\n\n".join(items[n - 1]["finding"] for n in levels) or "None found.",
        "other_findings": "\n\n---\n\n".join(other_blocks) or "None found.",
        "needs_review": (
            "| Item | Reason | Question to answer | Searched |\n|---|---|---|---|\n"
            + "\n".join(v["review"] for v in items if v["review"])
        ) if counts["NEEDS_REVIEW"] else "None.",
        "verification": (
            "| Item | Chapter / Section | Requirement | Status | Evidence |\n"
            "|:---|:---|:---|:---|:---|\n"
            + "\n".join(v["verification"] for v in items)
        ),
        "evidence": "\n\n".join(v["evidence"] for v in verdicts),
        "rejected": "\n".join(v["rejected"] for v in verdicts if v["rejected"]) or "None.",
    }
    for level in SEVERITY_ICONS:
        computed[f"fail_{level.lower()}"] = fail_levels[level]
        computed[f"other_{level.lower()}"] = other_counts[level]
    require(isinstance(metadata, dict), "Report metadata must be a JSON object")
    components = metadata.get("components")
    require(isinstance(components, list) and components, "Metadata must include components")
    component_rows = []
    for component in components:
        require(isinstance(component, dict), "Each component must be a JSON object")
        cells = []
        for field in COMPONENT_FIELDS:
            value = component.get(field)
            require(isinstance(value, str) and value.strip(), f"Component is missing {field}")
            cells.append(value.replace("|", "\\|").replace("\n", "<br>"))
        component_rows.append("| " + " | ".join(cells) + " |")
    computed["component_rows"] = "\n".join(component_rows)

    template = (SKILL / "references/REPORT-TEMPLATE.md").read_text(encoding="utf-8")
    template = re.sub(r"<!--.*?-->", "", template, flags=re.S)
    for heading, field in [
        ("Findings", "findings"), ("Other findings", "other_findings"),
        ("Needs review", "needs_review"), ("Verification summary", "verification"),
        ("Evidence appendix", "evidence"), ("Checked and rejected", "rejected"),
    ]:
        template, replaced = re.subn(
            rf"(?ms)(^## {re.escape(heading)}\n).*?(?=^## |\Z)",
            lambda match: match[1] + "\n{{ " + field + " }}\n\n", template,
        )
        require(replaced == 1, f"Template must contain one '{heading}' section")
    template, replaced = re.subn(
        r"(?m)^\| \{\{ component \}\}.*$", "{{ component_rows }}", template,
    )
    require(replaced == 1, "Template must contain one component row")
    values = {**metadata, **computed}

    def substitute(match):
        field = match[1]
        value = values.get(field)
        require(isinstance(value, (str, int) if field in computed else str) and str(value).strip(),
                f"Missing or invalid report field: {field}")
        return str(value)

    return re.sub(r"\{\{\s*(\w+)\s*\}\}", substitute, template).strip() + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--verdicts", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        metadata = json.loads(args.metadata.read_text(encoding="utf-8-sig"))
        report = assemble(metadata, args.verdicts.read_text(encoding="utf-8-sig"))
        args.output.write_bytes(report.encode("utf-8"))
    except (OSError, ValueError) as error:
        parser.exit(1, f"Report assembly failed: {error}\n")
    print(f"Checked all 70 items and wrote {args.output}")


if __name__ == "__main__":
    main()
