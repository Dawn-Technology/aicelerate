#!/usr/bin/env python3
"""Validate the canonical WCAG CSV and, optionally, a generated report."""

from __future__ import annotations

import argparse
import csv
import json
import math
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
DETAIL_VERDICTS = ("⚠️ NEEDS_REVIEW", "❌ FAIL")
SKILL_VERSION = "1.6.0"
PARTIAL_VERDICT = "⏳ NOT_EVALUATED"
SEVERITY_LABELS = ("Critical", "Serious", "Moderate", "Minor")
SEVERITY_RANK = {label: rank for rank, label in enumerate(reversed(SEVERITY_LABELS))}
FAIL_SEVERITY_BASELINES = {
    "1.1.1": "Serious",
    "1.2.2": "Serious",
    "1.4.3": "Serious",
    "2.1.1": "Serious",
    "2.4.7": "Serious",
    "3.3.2": "Serious",
}
EXCLUDED_PATH_PARTS = {
    ".git", ".svn", ".hg", "node_modules", "vendor", "dist", "build",
    "out", "target", ".next", "coverage", ".nyc_output", "__pycache__",
    ".pytest_cache", "tests", "test", "spec", "__tests__",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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


def source_roots(target: Path, scopes: list[Path] | None = None) -> list[Path]:
    """Resolve explicit audit roots or fall back to conventional custom-code roots."""
    if scopes:
        return scopes
    drupal_custom_roots = [
        candidate for candidate in (
            target / "web" / "themes" / "custom",
            target / "web" / "modules" / "custom",
        )
        if candidate.is_dir()
    ]
    return drupal_custom_roots or [target]


def focus_suppression_count(target: Path, scopes: list[Path] | None = None) -> int:
    """Count authored CSS/preprocessor focus-suppression candidates."""
    authored_extensions = {".scss", ".sass", ".less"}
    search_roots = source_roots(target, scopes)
    files = [
        candidate for root in search_roots for candidate in root.rglob("*")
        if candidate.is_file()
        and candidate.suffix.lower() in authored_extensions
        and not EXCLUDED_PATH_PARTS.intersection(candidate.parts)
        and not re.search(r"(?:\.test|\.spec|\.stories)\.", candidate.name)
    ]
    if not files:
        files = [
            candidate for root in search_roots for candidate in root.rglob("*.css")
            if candidate.is_file()
            and not EXCLUDED_PATH_PARTS.intersection(candidate.parts)
            and not candidate.name.endswith((".min.css", ".bundle.css"))
        ]

    pattern = re.compile(r"\boutline\s*:\s*(?:none|0(?=\s*(?:[;}!]|$)))", re.IGNORECASE)
    count = 0
    for candidate in files:
        try:
            count += len(pattern.findall(candidate.read_text(encoding="utf-8", errors="ignore")))
        except OSError:
            continue
    return count


def markup_control_count(target: Path, scopes: list[Path] | None = None) -> int:
    """Count raw authored form-control candidates before applicability filtering."""
    search_roots = source_roots(target, scopes)
    extensions = {".html", ".twig", ".jsx", ".tsx", ".vue", ".php"}
    pattern = re.compile(r"<(?:input|select|textarea)\b", re.IGNORECASE)
    count = 0
    for root in search_roots:
        for candidate in root.rglob("*"):
            if (
                not candidate.is_file()
                or candidate.suffix.lower() not in extensions
                or EXCLUDED_PATH_PARTS.intersection(candidate.parts)
                or re.search(r"(?:\.test|\.spec|\.stories)\.", candidate.name)
            ):
                continue
            try:
                count += len(pattern.findall(candidate.read_text(encoding="utf-8", errors="ignore")))
            except OSError:
                continue
    return count


def authored_markup_count(
    target: Path,
    pattern: re.Pattern[str],
    path_fragment: str | None = None,
    scopes: list[Path] | None = None,
) -> int:
    """Count raw authored markup candidates in production source roots."""
    search_roots = source_roots(target, scopes)
    extensions = {".html", ".twig", ".jsx", ".tsx", ".vue", ".php"}
    count = 0
    for root in search_roots:
        for candidate in root.rglob("*"):
            if (
                not candidate.is_file()
                or candidate.suffix.lower() not in extensions
                or EXCLUDED_PATH_PARTS.intersection(candidate.parts)
                or re.search(r"(?:\.test|\.spec|\.stories)\.", candidate.name)
                or (path_fragment is not None and path_fragment not in candidate.as_posix())
            ):
                continue
            try:
                count += len(pattern.findall(candidate.read_text(encoding="utf-8", errors="ignore")))
            except OSError:
                continue
    return count


def authored_source_files(
    target: Path, extensions: set[str], scopes: list[Path] | None = None
) -> list[Path]:
    """Return bounded production source files using the audit's standard roots."""
    search_roots = source_roots(target, scopes)
    return [
        candidate for root in search_roots for candidate in root.rglob("*")
        if candidate.is_file()
        and candidate.suffix.lower() in extensions
        and not EXCLUDED_PATH_PARTS.intersection(candidate.parts)
        and not re.search(r"(?:\.test|\.spec|\.stories)\.", candidate.name)
        and not candidate.name.endswith((".min.js", ".bundle.js", ".min.css", ".bundle.css"))
        and not (candidate.suffix.lower() == ".css" and candidate.with_suffix(".scss").is_file())
    ]


def source_signal_locations(
    target: Path,
    extensions: set[str],
    pattern: re.Pattern[str],
    scopes: list[Path] | None = None,
) -> list[str]:
    """Return one location per raw source signal for inventory reconciliation."""
    locations: list[str] = []
    for candidate in authored_source_files(target, extensions, scopes):
        try:
            source = candidate.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for match in pattern.finditer(source):
            locations.append(f"{candidate}:{source.count(chr(10), 0, match.start()) + 1}")
    return locations


def report_candidate_count(row: dict[str, str], detail: str) -> int | None:
    """Read candidate count from the ledger first, then its detailed section."""
    ledger_count = candidate_count(row.get("evidence", ""))
    return ledger_count if ledger_count is not None else candidate_count(detail)


def uninvoked_resize_aria_handlers(target: Path, scopes: list[Path] | None = None) -> list[str]:
    """Find ARIA resize handlers registered for future events but never initialized."""
    locations: list[str] = []
    declaration = re.compile(r"\bconst\s+(\w*[Rr]esize\w*)\s*=\s*(?:\([^)]*\)|\w+)\s*=>")
    for candidate in authored_source_files(target, {".js", ".ts"}, scopes):
        try:
            source = candidate.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "aria-hidden" not in source or not re.search(r"addEventListener\(\s*['\"]resize['\"]", source):
            continue
        for match in declaration.finditer(source):
            name = match.group(1)
            if not re.search(
                rf"addEventListener\(\s*['\"]resize['\"]\s*,\s*{re.escape(name)}\b",
                source,
            ):
                continue
            # A reference passed to addEventListener is not an initialization call.
            if not re.search(rf"\b{re.escape(name)}\s*\(\s*\)\s*;", source):
                line = source.count("\n", 0, match.start()) + 1
                locations.append(f"{candidate}:{line}")
    return locations


def responsive_aria_initial_mismatch_locations(
    target: Path, scopes: list[Path] | None = None
) -> list[str]:
    """Find component-local initial ARIA states contradicted by responsive CSS."""
    mismatches: list[str] = []
    for location in uninvoked_resize_aria_handlers(target, scopes):
        js_path = Path(location.rsplit(":", 1)[0])
        component_root = js_path.parent
        markup = "\n".join(
            candidate.read_text(encoding="utf-8", errors="ignore")
            for candidate in component_root.rglob("*.twig")
        )
        styles = "\n".join(
            candidate.read_text(encoding="utf-8", errors="ignore")
            for extension in ("*.css", "*.scss", "*.sass", "*.less")
            for candidate in component_root.rglob(extension)
        )
        script = js_path.read_text(encoding="utf-8", errors="ignore")
        if (
            re.search(r"aria-hidden\s*=\s*[\"']true[\"']", markup, re.IGNORECASE)
            and re.search(r"(?:@media|breakpoint)[\s\S]{0,1200}display\s*:\s*(?:flex|block)", styles, re.IGNORECASE)
            and re.search(r"setAttribute\(\s*[\"']aria-hidden[\"']\s*,\s*[\"']false[\"']", script)
        ):
            mismatches.append(location)
    return mismatches


def undersized_interactive_style_locations(
    target: Path, scopes: list[Path] | None = None
) -> list[str]:
    """Find raw sub-24px dimensions in style blocks whose selector looks interactive."""
    locations: list[str] = []
    selector_hint = re.compile(
        r"(?:button|toggle|trigger|control|link|search|menu|nav|tab|checkbox|radio)",
        re.IGNORECASE,
    )
    dimension = re.compile(r"\b(?:width|height)\s*:\s*(?:[1-9]|1\d|2[0-3])(?:\.\d+)?px\b", re.IGNORECASE)
    for candidate in authored_source_files(
        target, {".css", ".scss", ".sass", ".less"}, scopes
    ):
        try:
            source = candidate.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        lines = source.splitlines()
        for index, line in enumerate(lines):
            if not dimension.search(line):
                continue
            context = "\n".join(lines[max(0, index - 14):index + 1])
            if selector_hint.search(context):
                locations.append(f"{candidate}:{index + 1}")
    return locations


def _hex_color(value: str, tokens: dict[str, str]) -> str | None:
    value = value.strip().lower()
    variable = re.fullmatch(r"var\(\s*(--[\w-]+)\s*\)", value)
    if variable:
        return _hex_color(tokens.get(variable.group(1), ""), tokens)
    if value == "white":
        return "ffffff"
    if value == "black":
        return "000000"
    match = re.fullmatch(r"#([0-9a-f]{3}|[0-9a-f]{6})", value)
    if not match:
        return None
    color = match.group(1)
    return "".join(character * 2 for character in color) if len(color) == 3 else color


def _relative_luminance(color: str) -> float:
    channels = [int(color[index:index + 2], 16) / 255 for index in (0, 2, 4)]
    linear = [
        channel / 12.92 if channel <= 0.04045
        else math.pow((channel + 0.055) / 1.055, 2.4)
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def definite_low_text_contrast_locations(
    target: Path, scopes: list[Path] | None = None
) -> list[str]:
    """Find authored text-like style blocks with a resolved contrast below 3:1."""
    files = authored_source_files(target, {".css", ".scss", ".sass", ".less"}, scopes)
    tokens: dict[str, str] = {}
    for candidate in files:
        source = candidate.read_text(encoding="utf-8", errors="ignore")
        for match in re.finditer(
            r"(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{3,6}|white|black|var\(\s*--[\w-]+\s*\))",
            source,
        ):
            tokens[match.group(1)] = match.group(2)

    locations: list[str] = []
    text_selector = re.compile(r"(?:badge|button|label|title|text|link|tag|teaser)", re.IGNORECASE)
    block_pattern = re.compile(r"([^{}]{0,300})\{([^{}]*)\}")
    value_pattern = r"(#[0-9a-fA-F]{3,6}|white|black|var\(\s*--[\w-]+\s*\))"
    for candidate in files:
        source = candidate.read_text(encoding="utf-8", errors="ignore")
        for match in block_pattern.finditer(source):
            body = match.group(2)
            foreground = re.search(rf"(?<![-\w])color\s*:\s*{value_pattern}", body, re.IGNORECASE)
            background = re.search(
                rf"background(?:-color)?\s*:\s*{value_pattern}", body, re.IGNORECASE
            )
            if not foreground or not background:
                continue
            context = source[max(0, match.start() - 500):match.start()] + match.group(1)
            if not text_selector.search(context) or re.search(r"::?(?:before|after)", match.group(1)):
                continue
            foreground_hex = _hex_color(foreground.group(1), tokens)
            background_hex = _hex_color(background.group(1), tokens)
            if not foreground_hex or not background_hex:
                continue
            first = _relative_luminance(foreground_hex)
            second = _relative_luminance(background_hex)
            ratio = (max(first, second) + 0.05) / (min(first, second) + 0.05)
            if ratio < 3:
                line = source.count("\n", 0, match.start()) + 1
                locations.append(
                    f"{candidate}:{line} ({foreground_hex} on {background_hex}, {ratio:.2f}:1)"
                )
    return locations


def suspicious_focus_suppressions(target: Path, scopes: list[Path] | None = None) -> list[str]:
    """Find focus blocks that remove outline without a local visible replacement."""
    search_roots = source_roots(target, scopes)
    block_pattern = re.compile(r"([^{}]*(?:focus|focus-visible)[^{}]*)\{([^{}]*)\}", re.IGNORECASE)
    suppression = re.compile(r"\boutline\s*:\s*(?:none|0)(?:\s*!important)?\s*;?", re.IGNORECASE)
    replacement = re.compile(
        r"\b(?:box-shadow|border(?:-color)?|background(?:-color)?|text-decoration)\s*:"
        r"|\boutline\s*:\s*(?!none\b|0(?:\D|$))",
        re.IGNORECASE,
    )
    files = [
        candidate for root in search_roots for candidate in root.rglob("*")
        if candidate.is_file()
        and candidate.suffix.lower() in {".scss", ".sass", ".less"}
        and not EXCLUDED_PATH_PARTS.intersection(candidate.parts)
        and not re.search(r"(?:\.test|\.spec|\.stories)\.", candidate.name)
    ]
    if not files:
        files = [
            candidate for root in search_roots for candidate in root.rglob("*.css")
            if candidate.is_file()
            and not EXCLUDED_PATH_PARTS.intersection(candidate.parts)
            and not candidate.name.endswith((".min.css", ".bundle.css"))
        ]

    suspicious: list[str] = []
    for candidate in files:
        try:
            source = candidate.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for match in block_pattern.finditer(source):
            body = match.group(2)
            if suppression.search(body) and not replacement.search(suppression.sub("", body)):
                line = source.count("\n", 0, match.start()) + 1
                suspicious.append(f"{candidate}:{line}")
    return suspicious


def candidate_count(evidence: str) -> int | None:
    match = re.search(r"\bcandidates=(?:at least\s+)?(\d+)", evidence)
    return int(match.group(1)) if match else None


def raw_hit_count(evidence: str) -> int | None:
    match = re.search(r"\braw_hits=(\d+)", evidence)
    return int(match.group(1)) if match else None


def validate_model_provenance(text: str) -> list[str]:
    """Require two explicitly identified, distinct evaluator models."""
    errors: list[str] = []
    author_match = re.search(
        r"^\*\*Initial draft author:\*\*\s*(.+)$", text, re.MULTILINE
    )
    review_match = re.search(
        r"^\*\*Independent review:\*\*\s*(.+)$", text, re.MULTILINE
    )

    unavailable = re.compile(r"\b(?:unavailable|not available|none|not performed|unknown)\b", re.IGNORECASE)

    def identifier(value: str | None) -> str | None:
        if value is None or "[[" in value or unavailable.search(value):
            return None
        parenthetical = re.findall(r"\(([^()]*)\)", value)
        candidate = parenthetical[-1] if parenthetical else value
        normalized = re.sub(r"[^a-z0-9]+", " ", candidate.lower()).strip()
        return normalized or None

    author_id = identifier(author_match.group(1) if author_match else None)
    review_id = identifier(review_match.group(1) if review_match else None)
    if author_id is None:
        errors.append("initial draft author must identify its evaluator model")
    if review_id is None:
        errors.append("independent review must identify a second evaluator model")
    if author_id is not None and review_id is not None and author_id == review_id:
        errors.append("initial draft and independent review must use distinct model identifiers")
    return errors


def build_source_inventory(target: Path, scopes: list[Path] | None = None) -> dict[str, object]:
    """Build deterministic raw inventories before evaluator classification."""
    style_extensions = {".css", ".scss", ".sass", ".less"}
    markup_extensions = {".html", ".twig", ".jsx", ".tsx", ".vue", ".php"}
    signals: dict[str, list[str]] = {
        "focus_suppressions": source_signal_locations(
            target,
            style_extensions,
            re.compile(r"\boutline\s*:\s*(?:none|0(?=\s*(?:[;}!]|$)))", re.IGNORECASE),
            scopes,
        ),
        "sticky_fixed": source_signal_locations(
            target, style_extensions, re.compile(r"\bposition\s*:\s*(?:sticky|fixed)\b", re.IGNORECASE), scopes
        ),
        "visual_order": source_signal_locations(
            target,
            style_extensions,
            re.compile(r"\b(?:grid-template-areas|grid-area|order)\s*:|flex-direction\s*:\s*(?:row|column)-reverse", re.IGNORECASE),
            scopes,
        ),
        "animations": source_signal_locations(
            target, style_extensions, re.compile(r"@keyframes\b|\banimation(?:-name)?\s*:", re.IGNORECASE), scopes
        ),
        "auth_entry_points": source_signal_locations(
            target,
            markup_extensions,
            re.compile(r"(?:user[-_/ ]login|user[-_/ ]password|password[-_/ ]reset|\bauthentication\b)", re.IGNORECASE),
            scopes,
        ),
        "help_contact": source_signal_locations(
            target,
            markup_extensions,
            re.compile(r"(?:mailto:|tel:|contact[-_ ]card|contact[-_ ]mechanism|help[-_ ](?:link|center|centre)|\bchat(?:bot)?\b|faq[-_ ])", re.IGNORECASE),
            scopes,
        ),
        "uninvoked_resize_aria_handlers": uninvoked_resize_aria_handlers(target, scopes),
        "responsive_aria_initial_mismatches": responsive_aria_initial_mismatch_locations(target, scopes),
        "definite_low_text_contrast": definite_low_text_contrast_locations(target, scopes),
        "undersized_interactive_styles": undersized_interactive_style_locations(target, scopes),
    }
    interactive = authored_markup_count(
        target, re.compile(r"<(?:a|button|input|select|textarea)\b", re.IGNORECASE), scopes=scopes
    )
    controls = markup_control_count(target, scopes)
    aria_widgets = authored_markup_count(
        target,
        re.compile(
            r"<(?:a|button|input|select|textarea)\b|\brole\s*=\s*[\"']|\baria-(?:expanded|hidden|selected|pressed|checked|controls|haspopup)\s*=",
            re.IGNORECASE,
        ),
        scopes=scopes,
    )
    return {
        "target": str(target),
        "scopes": [str(scope) for scope in source_roots(target, scopes)],
        "counts": {
            "interactive_markup": interactive,
            "form_controls": controls,
            "aria_widget_signals": aria_widgets,
            **{name: len(locations) for name, locations in signals.items()},
        },
        "locations": signals,
    }


def validate_partial_report(
    path: Path,
    criteria_rows: list[dict[str, str]],
    target: Path | None,
    scopes: list[Path] | None = None,
) -> list[str]:
    """Validate an interim progress artifact without pretending unfinished rows have verdicts."""
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    errors.extend(validate_model_provenance(text))
    if not path.name.endswith("-PARTIAL.md"):
        errors.append("partial report filename must end with -PARTIAL.md")
    if not re.search(r"^# .*\[PARTIAL\]\s*$", text, re.MULTILINE):
        errors.append("partial report title must end with [PARTIAL]")
    if not re.search(rf"^\*\*Skill version:\*\*\s*{re.escape(SKILL_VERSION)}\s*$", text, re.MULTILINE):
        errors.append(f"partial report was not generated with current skill version {SKILL_VERSION}")
    if "not a completed WCAG audit" not in text:
        errors.append("partial report is missing the required interim-artifact disclaimer")
    if re.search(r"\[\[[a-z][a-z0-9_]*\]\]", text):
        errors.append("partial report contains unfilled template placeholders")

    ledger_match = re.search(
        r"^## Progress ledger\s*$([\s\S]*?)^## ", text, re.MULTILINE
    )
    if not ledger_match:
        return errors + ["partial report is missing a bounded Progress ledger section"]

    rows: list[dict[str, str]] = []
    for line in ledger_match.group(1).splitlines():
        cells = [cell.strip() for cell in line.split("|")]
        if len(cells) >= 8 and re.fullmatch(r"\d+\.\d+\.\d+", cells[1]):
            rows.append({
                "sc_id": cells[1],
                "name": cells[2],
                "level": cells[3],
                "progress": cells[4],
                "verdict": cells[5],
                "evidence": " | ".join(cells[6:-1]).strip(),
            })

    expected = [(item[0], item[1], item[2]) for item in EXPECTED_CRITERIA]
    actual = [(row["sc_id"], row["name"], row["level"]) for row in rows]
    if len(rows) != 55:
        errors.append(f"partial progress-ledger row count {len(rows)} != 55")
    if actual != expected:
        errors.append("partial progress ledger IDs, names, levels, or order differ from the canonical checklist")

    static_by_id = {row["sc_id"]: row["static_analyzable"] for row in criteria_rows}
    valid_progress = {"COMPLETE", "CONFIRMED_FAIL", "INCOMPLETE"}
    for row in rows:
        progress = row["progress"]
        verdict = row["verdict"]
        if progress not in valid_progress:
            errors.append(f"partial row {row['sc_id']} has invalid progress state {progress!r}")
        elif progress == "INCOMPLETE" and verdict != PARTIAL_VERDICT:
            errors.append(f"partial row {row['sc_id']} must use {PARTIAL_VERDICT} when INCOMPLETE")
        elif progress == "CONFIRMED_FAIL" and verdict != "❌ FAIL":
            errors.append(f"partial row {row['sc_id']} must use ❌ FAIL when CONFIRMED_FAIL")
        elif progress == "CONFIRMED_FAIL" and not re.search(
            r"\bat least\s+\d+\b", row["evidence"], re.IGNORECASE
        ):
            errors.append(f"partial CONFIRMED_FAIL row {row['sc_id']} must state an at-least violation count")
        elif progress == "COMPLETE" and verdict not in VERDICT_TOKENS:
            errors.append(f"partial COMPLETE row {row['sc_id']} has invalid verdict")
        if progress == "COMPLETE" and static_by_id.get(row["sc_id"]) == "no" and verdict == "✅ PASS":
            errors.append(f"partial report gives forbidden static PASS for {row['sc_id']}")
        if progress == "COMPLETE" and verdict == "✅ PASS":
            if any(token not in row["evidence"] for token in ("Coverage:", "candidates=", "evaluated=", "unresolved=0")):
                errors.append(f"partial COMPLETE PASS {row['sc_id']} lacks bounded coverage")
        if progress == "COMPLETE" and verdict == "⚪ N/A":
            if any(token not in row["evidence"] for token in ("N/A -", "Coverage:", "searched", "candidates=0", "evaluated=0", "unresolved=0")):
                errors.append(f"partial COMPLETE N/A {row['sc_id']} lacks bounded negative evidence")
        if progress == "INCOMPLETE" and not row["evidence"].strip():
            errors.append(f"partial INCOMPLETE row {row['sc_id']} lacks a remaining-work statement")

    progress_counts = Counter(row["progress"] for row in rows)
    for progress in ("COMPLETE", "CONFIRMED_FAIL", "INCOMPLETE"):
        match = re.search(rf"^\|\s*{progress}\s*\|\s*(\d+)\s*\|$", text, re.MULTILINE)
        if not match:
            errors.append(f"partial progress summary is missing {progress}")
        elif int(match.group(1)) != progress_counts[progress]:
            errors.append(
                f"partial progress summary {progress} count {match.group(1)} != ledger count {progress_counts[progress]}"
            )

    completed = [row for row in rows if row["progress"] == "COMPLETE"]
    completed_verdicts = Counter(row["verdict"] for row in completed)
    labels = {"✅ PASS": "PASS", "⚪ N/A": "N/A", "⚠️ NEEDS_REVIEW": "NEEDS_REVIEW", "❌ FAIL": "FAIL"}
    for verdict, label in labels.items():
        match = re.search(rf"^\|\s*{re.escape(verdict)}\s*\|\s*(\d+)\s*\|$", text, re.MULTILINE)
        if not match:
            errors.append(f"partial completed-verdict summary is missing {label}")
        elif int(match.group(1)) != completed_verdicts[verdict]:
            errors.append(
                f"partial completed-verdict summary {label} count {match.group(1)} != ledger count {completed_verdicts[verdict]}"
            )

    detail_match = re.search(
        r"^## Completed findings and required review\s*$([\s\S]*?)^## ", text, re.MULTILINE
    )
    expected_details = [
        (row["verdict"], row["sc_id"], row["name"])
        for row in rows
        if row["progress"] == "CONFIRMED_FAIL"
        or (row["progress"] == "COMPLETE" and row["verdict"] in DETAIL_VERDICTS)
    ]
    actual_details: list[tuple[str, str, str]] = []
    detail_text = detail_match.group(1) if detail_match else ""
    for line in detail_text.splitlines():
        match = re.fullmatch(r"### (⚠️ NEEDS_REVIEW|❌ FAIL) (\d+\.\d+\.\d+) — (.+)", line)
        if match:
            actual_details.append((match.group(1), match.group(2), match.group(3)))
    if actual_details != expected_details:
        errors.append("partial detailed sections must match COMPLETE review/fail and CONFIRMED_FAIL rows in order")

    required_fields = (
        "**WCAG level:**", "**Severity / review priority:**", "**Affected or unresolved instances:**",
        "**Coverage:**", "**Representative evidence:**", "**Impact or uncertainty:**",
        "**Remediation or exact manual verification:**",
    )
    for _, sc_id, _ in expected_details:
        match = re.search(
            rf"^### (?:⚠️ NEEDS_REVIEW|❌ FAIL) {re.escape(sc_id)} —[^\n]*\n([\s\S]*?)(?=^### |^## )",
            text,
            re.MULTILINE,
        )
        detail = match.group(1) if match else ""
        for field in required_fields:
            if field not in detail:
                errors.append(f"partial detailed finding {sc_id} is missing mandatory field {field}")
        severity_match = re.search(
            r"^[-*] \*\*Severity / review priority:\*\*\s*(\S+)",
            detail,
            re.MULTILINE,
        )
        if severity_match and severity_match.group(1) not in SEVERITY_LABELS:
            errors.append(
                f"partial detailed finding {sc_id} uses invalid severity/review priority "
                f"{severity_match.group(1)!r}; use one of {', '.join(SEVERITY_LABELS)}"
            )

    if target is not None and not target.is_dir():
        errors.append(f"target repository is not an accessible directory: {target}")
    for scope in scopes or []:
        if not scope.is_dir():
            errors.append(f"audit scope is not an accessible directory: {scope}")
    return errors


def validate_report(
    path: Path,
    criteria_rows: list[dict[str, str]],
    target: Path | None = None,
    scopes: list[Path] | None = None,
) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    if re.search(r"^# .*\[PARTIAL\]", text, re.MULTILINE | re.IGNORECASE):
        return validate_partial_report(path, criteria_rows, target, scopes)
    errors.extend(validate_model_provenance(text))
    ledger_match = re.search(
        r"^## Conformance criteria ledger\s*$([\s\S]*?)^## ", text, re.MULTILINE
    )
    if not ledger_match:
        return ["report is missing a bounded Conformance criteria ledger section"]

    rows: list[dict[str, str]] = []
    for line in ledger_match.group(1).splitlines():
        cells = [cell.strip() for cell in line.split("|")]
        if len(cells) >= 7 and re.fullmatch(r"\d+\.\d+\.\d+", cells[1]):
            rows.append({
                "sc_id": cells[1],
                "name": cells[2],
                "level": cells[3],
                "verdict": cells[4],
                "evidence": " | ".join(cells[5:-1]).strip(),
            })

    ids = [row["sc_id"] for row in rows]
    if len(rows) != 55:
        errors.append(f"report ledger row count {len(rows)} != 55")
    if ids != EXPECTED_IDS:
        errors.append("report ledger IDs or order differ from the canonical checklist")
    if any(row["verdict"] not in VERDICT_TOKENS for row in rows):
        errors.append("report contains an invalid verdict token")
    report_criteria = [(row["sc_id"], row["name"], row["level"]) for row in rows]
    expected_report_criteria = [criterion[:3] for criterion in EXPECTED_CRITERIA]
    if report_criteria != expected_report_criteria:
        errors.append("report ledger names or levels differ from the canonical checklist")

    if re.search(r"\[\[[a-z][a-z0-9_]*\]\]", text):
        errors.append("report contains unfilled template placeholders")
    if "not a certification or WCAG conformance claim" not in text:
        errors.append("report is missing the required static-audit disclaimer")
    if not re.search(rf"^\*\*Skill version:\*\*\s*{re.escape(SKILL_VERSION)}\s*$", text, re.MULTILINE):
        errors.append(f"report was not generated with current skill version {SKILL_VERSION}")

    partial_report = bool(re.search(r"^# .*\[PARTIAL\]", text, re.MULTILINE | re.IGNORECASE))
    incomplete_source_phrases = re.compile(
        r"\b(?:sampled(?: only| paths?| files?| evidence| scripts?| behaviors?)?"
        r"|spot[- ]checked|not performed|not completed|out of scope for this pass"
        r"|not fully inventoried|full inventory not completed|full .*? audit .*? not completed)\b",
        re.IGNORECASE,
    )
    incomplete_matches = sorted({match.group(0) for match in incomplete_source_phrases.finditer(text)})
    if incomplete_matches and not partial_report:
        errors.append(
            "normal report admits unfinished bounded source analysis "
            f"({', '.join(incomplete_matches[:5])}); finish the inventory or publish [PARTIAL]"
        )

    static_by_id = {
        row["sc_id"]: row["static_analyzable"]
        for row in criteria_rows
        if row.get("sc_id")
    }
    for row in rows:
        sc_id = row["sc_id"]
        verdict = row["verdict"]
        evidence = row["evidence"]
        if static_by_id.get(sc_id) == "no" and verdict == "✅ PASS":
            errors.append(f"report gives forbidden static PASS for static_analyzable=no criterion {sc_id}")
        if verdict == "✅ PASS":
            required = ("Coverage:", "candidates=", "evaluated=", "unresolved=0")
            if any(token not in evidence for token in required):
                errors.append(f"PASS {sc_id} lacks the complete bounded coverage manifest")
            if "sampled" in evidence.lower():
                errors.append(f"PASS {sc_id} relies on sampling rather than exhaustive coverage")
            count = candidate_count(evidence)
            if count == 0:
                errors.append(f"PASS {sc_id} has candidates=0; absent governed features require N/A")
        if verdict == "⚪ N/A":
            required = (
                "N/A -", "Coverage:", "searched", "candidates=0",
                "evaluated=0", "unresolved=0",
            )
            if any(token not in evidence for token in required):
                errors.append(f"N/A {sc_id} lacks bounded negative evidence")

    verdict_counts = Counter(row["verdict"] for row in rows)
    rows_by_id = {row["sc_id"]: row for row in rows}

    def detail_for(sc_id: str) -> str:
        match = re.search(
            rf"^### (?:⚠️ NEEDS_REVIEW|❌ FAIL) {re.escape(sc_id)} —[^\n]*\n([\s\S]*?)(?=^### |^## )",
            text,
            re.MULTILINE,
        )
        return match.group(1) if match else ""

    limitations_match = re.search(
        r"^\*\*Source limitations:\*\*\s*(.+)$", text, re.MULTILINE
    )
    limitations = limitations_match.group(1) if limitations_match else ""
    unavailable_content = bool(re.search(
        r"(?:rendered|CMS|editorial|translated).*?(?:not available|unavailable|cannot be verified)",
        limitations,
        re.IGNORECASE,
    ))
    if unavailable_content:
        for sc_id in ("1.3.1", "1.3.3", "1.4.5", "2.4.4", "2.4.6", "3.1.2"):
            if rows_by_id.get(sc_id, {}).get("verdict") in {"✅ PASS", "⚪ N/A"}:
                errors.append(
                    f"{sc_id} cannot PASS/N/A while the declared CMS/editorial content boundary remains unresolved"
                )

    non_text_detail = detail_for("1.1.1")
    if rows_by_id.get("1.1.1", {}).get("verdict") == "❌ FAIL":
        if re.search(
            r"empty|<span[^>]*>[\s\S]{0,200}(?:no|without) aria-hidden|icon span has no",
            non_text_detail,
            re.IGNORECASE,
        ):
            errors.append("1.1.1 treats missing aria-hidden on an empty non-semantic span as a violation")
        if "default('')" in non_text_detail and not re.search(
            r"(?:source-controlled informative caller|rendered informative instance|<img[^>]+alt=[\"']{2})",
            non_text_detail,
            re.IGNORECASE,
        ):
            errors.append("1.1.1 uses an empty-alt fallback without proving an informative affected instance")

    # Applicability consistency: these criteria govern existing controls and
    # interactions, not merely the presence of a specially named widget.
    if rows_by_id.get("2.1.1", {}).get("verdict") != "⚪ N/A":
        for sc_id in ("2.1.2", "3.2.1"):
            if rows_by_id.get(sc_id, {}).get("verdict") == "⚪ N/A":
                errors.append(
                    f"{sc_id} cannot be N/A when 2.1.1 establishes in-scope keyboard/focusable UI"
                )
    if (
        rows_by_id.get("3.3.2", {}).get("verdict") != "⚪ N/A"
        and rows_by_id.get("3.2.2", {}).get("verdict") == "⚪ N/A"
    ):
        errors.append("3.2.2 cannot be N/A when 3.3.2 establishes in-scope input controls")

    pointer_row = rows_by_id.get("2.5.2", {})
    if pointer_row.get("verdict") == "⚪ N/A" and re.search(
        r"\b(?:click|native control|native form)\b", pointer_row.get("evidence", ""), re.IGNORECASE
    ):
        errors.append("2.5.2 N/A evidence identifies pointer-operated click/native candidates")

    hover_row = rows_by_id.get("1.4.13", {})
    if hover_row.get("verdict") == "⚪ N/A":
        hover_evidence = hover_row.get("evidence", "").lower()
        if "hover" not in hover_evidence or "focus" not in hover_evidence:
            errors.append("1.4.13 N/A must show bounded searches for both hover- and focus-triggered content")
        if not re.search(r"\b(?:dropdown|submenu|disclosure|menu)\b", hover_evidence):
            errors.append("1.4.13 N/A must include dropdown/submenu/disclosure applicability signals")
    if hover_row.get("verdict") == "❌ FAIL" and not re.search(
        r"\b(?:obscur(?:e|es|ing)|replac(?:e|es|ing))\b", detail_for("1.4.13"), re.IGNORECASE
    ):
        errors.append("1.4.13 FAIL does not resolve the dismissible exception for content that obscures/replaces content")

    input_row = rows_by_id.get("3.2.2", {})
    if input_row.get("verdict") == "✅ PASS" and re.search(
        r"(?:auto.?submit|programmatic(?:ally)? (?:submit|click)|\.click\(\)|dispatchEvent|change submission)",
        input_row.get("evidence", "") + "\n" + text,
        re.IGNORECASE,
    ) and rows_by_id.get("4.1.3", {}).get("verdict") == "⚠️ NEEDS_REVIEW":
        errors.append("3.2.2 PASS conflicts with unresolved automatic/AJAX form-update behavior under 4.1.3")

    media_related = ("1.2.2", "1.2.3", "1.2.4", "1.2.5")
    media_present = any(
        rows_by_id.get(sc_id, {}).get("verdict") != "⚪ N/A" for sc_id in media_related
    )
    media_only_row = rows_by_id.get("1.2.1", {})
    if media_present and media_only_row.get("verdict") == "⚪ N/A" and not re.search(
        r"\b(?:classified|synchronized|contains audio|audio track)\b",
        media_only_row.get("evidence", ""),
        re.IGNORECASE,
    ):
        errors.append("1.2.1 N/A conflicts with a related media candidate that was not explicitly classified")
    if media_only_row.get("verdict") == "⚪ N/A" and "controls" in media_only_row.get("evidence", "").lower():
        errors.append("1.2.1 uses the HTML controls attribute as media-content classification evidence")

    captions_row = rows_by_id.get("1.2.2", {})
    if captions_row.get("verdict") == "❌ FAIL":
        captions_detail = detail_for("1.2.2")
        if not re.search(
            r"\b(?:rendered instance|published instance|production content|source-controlled media|reachable route)\b",
            captions_row.get("evidence", "") + "\n" + captions_detail,
            re.IGNORECASE,
        ):
            errors.append(
                "1.2.2 FAIL must prove applicable rendered/production media, not only a player template"
            )
        if unavailable_content and not re.search(
            r"(?:^|[\s`/])[^\s`]+\.(?:mp4|webm|mov|m4v|mp3|wav|ogg)(?:[\s`]|$)",
            captions_detail,
            re.IGNORECASE,
        ):
            errors.append(
                "1.2.2 FAIL contradicts the unavailable rendered-content boundary without a bounded media asset"
            )

    non_text_row = rows_by_id.get("1.1.1", {})
    images_of_text_row = rows_by_id.get("1.4.5", {})
    if (
        images_of_text_row.get("verdict") in {"⚪ N/A", "✅ PASS"}
        and re.search(
            r"\b(?:CMS|editorial|content-dependent|unresolved)\b",
            non_text_row.get("evidence", ""),
            re.IGNORECASE,
        )
    ):
        errors.append("1.4.5 cannot be PASS/N/A while 1.1.1 records unresolved CMS/editorial image content")

    keyboard_detail = detail_for("2.1.1")
    if rows_by_id.get("2.1.1", {}).get("verdict") == "❌ FAIL" and re.search(
        r"(?:remains|already).*?(?:keyboard-accessible|reachable and operable)|duplicates? an? .*accessible control",
        keyboard_detail,
        re.IGNORECASE,
    ):
        errors.append("2.1.1 FAIL admits the same function remains keyboard operable")

    labels_detail = detail_for("3.3.2")
    if rows_by_id.get("3.3.2", {}).get("verdict") == "❌ FAIL" and re.search(
        r"acceptable in principle|rel(?:y|ies) solely on the <label> wrapper|risks? obscuring",
        labels_detail,
        re.IGNORECASE,
    ):
        errors.append("3.3.2 FAIL treats valid implicit wrapping-label semantics as an uncertain risk")

    aria_detail = detail_for("4.1.2")
    if rows_by_id.get("4.1.2", {}).get("verdict") == "❌ FAIL" and re.search(
        r"native (?:input|checkbox)[\s\S]{0,300}(?:visual wrapper|aria-checked)",
        aria_detail,
        re.IGNORECASE,
    ):
        errors.append("4.1.2 incorrectly requires aria-checked on a non-semantic wrapper around a native checkbox")
    if rows_by_id.get("4.1.2", {}).get("verdict") == "❌ FAIL" and re.search(
        r"programmatically determinable[\s\S]{0,240}(?:does not (?:correctly )?identify|generic|duplicated|non-descriptive)"
        r"|(?:generic|duplicated|non-descriptive)[\s\S]{0,240}programmatically determinable",
        aria_detail,
        re.IGNORECASE,
    ):
        errors.append(
            "4.1.2 uses accessible-name descriptiveness/uniqueness as a Name, Role, Value failure; "
            "score name quality under 2.4.6 unless the name is not programmatically determinable"
        )

    label_in_name_detail = detail_for("2.5.3")
    if re.search(
        r"(?:confirmed mismatch|violation)[\s\S]{0,400}visible text is absent"
        r"|visible text is absent[\s\S]{0,400}(?:confirmed mismatch|violation)",
        rows_by_id.get("2.5.3", {}).get("evidence", "") + "\n" + label_in_name_detail,
        re.IGNORECASE,
    ):
        errors.append("2.5.3 treats an icon-only control with no visible text label as a label/name mismatch")

    help_row = rows_by_id.get("3.2.6", {})
    if help_row.get("verdict") == "✅ PASS" and "newsletter" in help_row.get("evidence", "").lower() and not re.search(
        r"human contact|contact details|self-help|automated contact",
        help_row.get("evidence", ""),
        re.IGNORECASE,
    ):
        errors.append("3.2.6 treats a newsletter as a help mechanism without evidence of normative help")

    if "parallel" in text.lower() and "design-system" in text.lower():
        for sc_id in ("3.2.3", "3.2.4"):
            row = rows_by_id.get(sc_id, {})
            if row.get("verdict") == "✅ PASS" and not re.search(
                r"route mapping|legacy.*zv2|zv2.*legacy|both design",
                row.get("evidence", ""),
                re.IGNORECASE,
            ):
                errors.append(f"{sc_id} PASS does not reconcile the declared parallel design systems")

    if target is not None:
        if not target.is_dir():
            errors.append(f"target repository is not an accessible directory: {target}")
        else:
            for scope in scopes or []:
                if not scope.is_dir():
                    errors.append(f"audit scope is not an accessible directory: {scope}")

            source_suppressions = focus_suppression_count(target, scopes)
            focus_evidence = rows_by_id.get("2.4.7", {}).get("evidence", "")
            stated_match = re.search(r"\braw_hits=(\d+)", focus_evidence)
            if not stated_match:
                focus_detail = re.search(
                    r"^### (?:⚠️ NEEDS_REVIEW|❌ FAIL) 2\.4\.7 —[^\n]*\n([\s\S]*?)(?=^### |^## )",
                    text,
                    re.MULTILINE,
                )
                if focus_detail:
                    stated_match = re.search(r"\braw_hits=(\d+)", focus_detail.group(1))
            if source_suppressions and (
                not stated_match or int(stated_match.group(1)) < source_suppressions
            ):
                stated = stated_match.group(1) if stated_match else "missing"
                errors.append(
                    "2.4.7 focus-suppression inventory is incomplete: "
                    f"report raw_hits={stated}, authored source occurrences={source_suppressions}"
                )

            suspicious_focus = suspicious_focus_suppressions(target, scopes)
            focus_detail_text = detail_for("2.4.7")
            if suspicious_focus and re.search(r"violations=0|every .*paired", focus_detail_text, re.IGNORECASE):
                errors.append(
                    "2.4.7 claims every suppression has a replacement, but focus blocks without a local "
                    f"replacement remain (for example {suspicious_focus[0]})"
                )

            source_controls = markup_control_count(target, scopes)
            labels_row = rows_by_id.get("3.3.2", {})
            labels_match = re.search(r"\braw_hits=(\d+)", labels_row.get("evidence", ""))
            if labels_row.get("verdict") == "✅ PASS" and source_controls and (
                not labels_match or int(labels_match.group(1)) < source_controls
            ):
                stated = labels_match.group(1) if labels_match else "missing"
                errors.append(
                    "3.3.2 control inventory is incomplete: "
                    f"report raw_hits={stated}, raw authored control occurrences={source_controls}; "
                    "inventory and explicitly rule out hidden/non-user controls before PASS"
                )

            interactive_count = authored_markup_count(
                target,
                re.compile(r"<(?:a|button|input|select|textarea)\b", re.IGNORECASE),
                scopes=scopes,
            )
            for sc_id in ("2.1.1", "2.5.2", "2.5.3", "3.2.1"):
                row = rows_by_id.get(sc_id, {})
                stated = raw_hit_count(row.get("evidence", "") + "\n" + detail_for(sc_id))
                if row.get("verdict") == "✅ PASS" and interactive_count and (
                    stated is None or stated < interactive_count
                ):
                    errors.append(
                        f"{sc_id} PASS inventory is incomplete: report raw_hits={stated or 'missing'}, "
                        f"raw authored interactive occurrences={interactive_count}"
                    )

            aria_widget_count = authored_markup_count(
                target,
                re.compile(
                    r"<(?:a|button|input|select|textarea)\b|\brole\s*=\s*[\"']|\baria-(?:expanded|hidden|selected|pressed|checked|controls|haspopup)\s*=",
                    re.IGNORECASE,
                ),
                scopes=scopes,
            )
            aria_row = rows_by_id.get("4.1.2", {})
            aria_stated = raw_hit_count(aria_row.get("evidence", "") + "\n" + detail_for("4.1.2"))
            if aria_row.get("verdict") != "⚪ N/A" and aria_widget_count and (
                aria_stated is None or aria_stated < aria_widget_count
            ):
                errors.append(
                    "4.1.2 widget/state inventory is incomplete: "
                    f"report raw_hits={aria_stated or 'missing'}, raw authored occurrences={aria_widget_count}"
                )

            responsive_mismatches = responsive_aria_initial_mismatch_locations(target, scopes)
            if responsive_mismatches and aria_row.get("verdict") != "❌ FAIL":
                errors.append(
                    "4.1.2 must FAIL for a source-proven responsive initial ARIA/CSS mismatch "
                    f"(for example {responsive_mismatches[0]})"
                )

            if aria_row.get("verdict") != "❌ FAIL" and re.search(
                r"role=[\"']listbox[\"'][\s\S]{0,500}without[\s\S]{0,120}role=[\"']option[\"']",
                detail_for("4.1.2"),
                re.IGNORECASE,
            ):
                errors.append(
                    "4.1.2 describes a non-select listbox without required option semantics but does not assign FAIL"
                )

            low_contrast = definite_low_text_contrast_locations(target, scopes)
            if low_contrast and rows_by_id.get("1.4.3", {}).get("verdict") != "❌ FAIL":
                errors.append(
                    "1.4.3 must resolve source-defined text/background pairs below 3:1; the large-text "
                    f"exception cannot repair them (for example {low_contrast[0]})"
                )

            animation_locations = source_signal_locations(
                target,
                {".css", ".scss", ".sass", ".less"},
                re.compile(r"@keyframes\b|\banimation(?:-name)?\s*:", re.IGNORECASE),
                scopes,
            )
            if animation_locations and rows_by_id.get("2.2.2", {}).get("verdict") == "⚪ N/A":
                errors.append(
                    "2.2.2 cannot be N/A until authored animation candidates are classified for duration, "
                    f"information, and pause/stop/hide applicability (for example {animation_locations[0]})"
                )

            for sc_id in ("3.2.2", "3.3.1", "3.3.2", "3.3.3"):
                row = rows_by_id.get(sc_id, {})
                stated = raw_hit_count(row.get("evidence", "") + "\n" + detail_for(sc_id))
                if row.get("verdict") == "✅ PASS" and source_controls and (
                    stated is None or stated < source_controls
                ):
                    errors.append(
                        f"{sc_id} PASS form inventory is incomplete: report raw_hits={stated or 'missing'}, "
                        f"raw authored form-control occurrences={source_controls}"
                    )

            heading_label_count = authored_markup_count(
                target,
                re.compile(r"<(?:h[1-6]|label)\b", re.IGNORECASE),
                scopes=scopes,
            )
            headings_row = rows_by_id.get("2.4.6", {})
            headings_stated = raw_hit_count(headings_row.get("evidence", "") + "\n" + detail_for("2.4.6"))
            if headings_row.get("verdict") == "✅ PASS" and heading_label_count and (
                headings_stated is None or headings_stated < heading_label_count
            ):
                errors.append(
                    "2.4.6 PASS inventory is incomplete: "
                    f"report raw_hits={headings_stated or 'missing'}, "
                    f"raw authored heading/label occurrences={heading_label_count}"
                )

            layout_patterns = {
                "2.4.1": re.compile(r"href=[\"']#main-content[\"']", re.IGNORECASE),
                "2.4.2": re.compile(r"<title\b", re.IGNORECASE),
                "3.1.1": re.compile(r"<html(?:\s|\{)", re.IGNORECASE),
            }
            for sc_id, pattern in layout_patterns.items():
                row = rows_by_id.get(sc_id, {})
                raw_count = authored_markup_count(
                    target, pattern, "templates/layout", scopes=scopes
                )
                stated = candidate_count(row.get("evidence", ""))
                if row.get("verdict") == "✅ PASS" and raw_count and (
                    stated is None or stated < raw_count
                ):
                    errors.append(
                        f"{sc_id} PASS misses layout variants: report candidates={stated or 'missing'}, "
                        f"authored occurrences={raw_count}"
                    )

            if aria_row.get("verdict") != "⚪ N/A":
                has_aria_mutation = any(
                    "aria-hidden" in candidate.read_text(encoding="utf-8", errors="ignore")
                    for candidate in authored_source_files(target, {".js"}, scopes)
                )
                aria_detail = detail_for("4.1.2")
                if has_aria_mutation and not re.search(
                    r"\b(?:initial desktop|initial viewport|initial DOM|breakpoint|resize)\b",
                    aria_row.get("evidence", "") + "\n" + aria_detail,
                    re.IGNORECASE,
                ):
                    errors.append(
                        "4.1.2 must inventory aria-hidden JavaScript mutations and reconcile exact initial/breakpoint states"
                    )

                uninitialized = uninvoked_resize_aria_handlers(target, scopes)
                aria_combined = aria_row.get("evidence", "") + "\n" + aria_detail
                if uninitialized and not re.search(
                    r"(?:not|never) invoked|only registered|initiali[sz]ation (?:call )?(?:is )?absent",
                    aria_combined,
                    re.IGNORECASE,
                ):
                    errors.append(
                        "4.1.2 misses ARIA resize handlers that are registered but not invoked during "
                        f"initialization (for example {uninitialized[0]})"
                    )

            reorder_locations = source_signal_locations(
                target,
                {".css", ".scss", ".sass", ".less"},
                re.compile(r"\b(?:grid-template-areas|grid-area|order)\s*:|flex-direction\s*:\s*(?:row|column)-reverse", re.IGNORECASE),
                scopes,
            )
            sequence_row = rows_by_id.get("1.3.2", {})
            if sequence_row.get("verdict") == "⚪ N/A" and reorder_locations:
                errors.append(
                    "1.3.2 N/A misses authored visual-order candidates such as CSS grid areas/order "
                    f"(for example {reorder_locations[0]})"
                )

            wide_min_locations = source_signal_locations(
                target,
                {".css", ".scss", ".sass", ".less"},
                re.compile(
                    r"\bmin-width\s*:\s*(?:(?:3[2-9]\d|[4-9]\d{2}|\d{4,})px|(?:2[1-9]|[3-9]\d|\d{3,})rem)\b",
                    re.IGNORECASE,
                ),
                scopes,
            )
            reflow_row = rows_by_id.get("1.4.10", {})
            reflow_combined = reflow_row.get("evidence", "") + "\n" + detail_for("1.4.10")
            if wide_min_locations and re.search(
                r"no (?:definite )?`?min-width`? (?:beyond|over)|candidates=0", reflow_combined, re.IGNORECASE
            ):
                errors.append(
                    "1.4.10 source inventory contradicts its negative min-width claim "
                    f"(for example {wide_min_locations[0]})"
                )

            sticky_locations = source_signal_locations(
                target,
                {".css", ".scss", ".sass", ".less"},
                re.compile(r"\bposition\s*:\s*(?:sticky|fixed)\b", re.IGNORECASE),
                scopes,
            )
            obscured_row = rows_by_id.get("2.4.11", {})
            obscured_stated = raw_hit_count(obscured_row.get("evidence", "") + "\n" + detail_for("2.4.11"))
            if sticky_locations and obscured_row.get("verdict") != "⚪ N/A" and (
                obscured_stated is None or obscured_stated < len(sticky_locations)
            ):
                errors.append(
                    "2.4.11 sticky/fixed inventory is incomplete: "
                    f"report raw_hits={obscured_stated or 'missing'}, authored occurrences={len(sticky_locations)}"
                )

            undersized_locations = undersized_interactive_style_locations(target, scopes)
            target_size_row = rows_by_id.get("2.5.8", {})
            target_size_combined = target_size_row.get("evidence", "") + "\n" + detail_for("2.5.8")
            if undersized_locations and re.search(
                r"no authored (?:control|target).*?(?:below|sub-?)24|candidates=0",
                target_size_combined,
                re.IGNORECASE,
            ):
                errors.append(
                    "2.5.8 source inventory contradicts its claim that no authored sub-24px candidate exists; "
                    f"classify the candidate and normative exceptions (for example {undersized_locations[0]})"
                )

            auth_locations = source_signal_locations(
                target,
                {".html", ".twig", ".jsx", ".tsx", ".vue", ".php"},
                re.compile(r"(?:user[-_/ ]login|user[-_/ ]password|password[-_/ ]reset|\bauthentication\b)", re.IGNORECASE),
                scopes,
            )
            if auth_locations and rows_by_id.get("3.3.8", {}).get("verdict") == "⚪ N/A":
                errors.append(
                    "3.3.8 cannot be N/A when authentication/login/password-recovery entry points exist; "
                    f"inspect the delegated process (for example {auth_locations[0]})"
                )

            help_locations = source_signal_locations(
                target,
                {".html", ".twig", ".jsx", ".tsx", ".vue", ".php"},
                re.compile(r"(?:mailto:|tel:|contact[-_ ]card|contact[-_ ]mechanism|help[-_ ](?:link|center|centre)|\bchat(?:bot)?\b|faq[-_ ])", re.IGNORECASE),
                scopes,
            )
            if help_locations and rows_by_id.get("3.2.6", {}).get("verdict") == "⚪ N/A":
                errors.append(
                    "3.2.6 cannot be N/A until authored help/contact candidates are classified across page variants "
                    f"(for example {help_locations[0]})"
                )

            listbox_count = authored_markup_count(
                target,
                re.compile(r"\brole\s*=\s*[\"']listbox[\"']", re.IGNORECASE),
                scopes=scopes,
            )
            option_count = authored_markup_count(
                target,
                re.compile(r"\brole\s*=\s*[\"']option[\"']", re.IGNORECASE),
                scopes=scopes,
            )
            if listbox_count > option_count and not re.search(
                r"\blistbox\b[\s\S]{0,240}\boption\b|\boption\b[\s\S]{0,240}\blistbox\b",
                aria_row.get("evidence", "") + "\n" + aria_detail,
                re.IGNORECASE,
            ):
                errors.append(
                    "4.1.2 does not reconcile authored listbox structures with their required option semantics"
                )
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

    summary_values = set(verdict_counts.values())
    for match in re.finditer(r"\b(\d+)\s+of\s+55\s+criteria\b", text, re.IGNORECASE):
        stated = int(match.group(1))
        if stated not in summary_values:
            errors.append(
                f"report prose states {stated} of 55 criteria, which matches no ledger verdict count"
            )

    severity_counts: dict[str, int] = {}
    for severity in ("Critical", "Serious", "Moderate", "Minor"):
        match = re.search(rf"^\|\s*{severity}\s*\|\s*(\d+)\s*\|$", text, re.MULTILINE)
        if not match:
            errors.append(f"report severity summary is missing numeric {severity} count")
        else:
            severity_counts[severity] = int(match.group(1))
    if severity_counts and sum(severity_counts.values()) != verdict_counts["❌ FAIL"]:
        errors.append("report severity counts do not sum to the FAIL ledger count")

    detail_match = re.search(
        r"^## Detailed findings and required review\s*$([\s\S]*?)^## (?:Supplemental observations|Regulatory context)\s*$",
        text,
        re.MULTILINE,
    )
    if not detail_match:
        errors.append("report is missing a bounded detailed findings section")
        return errors

    expected_details = [
        (row["verdict"], row["sc_id"], row["name"])
        for row in rows
        if row["verdict"] in DETAIL_VERDICTS
    ]
    actual_details: list[tuple[str, str, str]] = []
    for line in detail_match.group(1).splitlines():
        if not line.startswith("### "):
            continue
        exact = re.fullmatch(
            r"### (⚠️ NEEDS_REVIEW|❌ FAIL) (\d+\.\d+\.\d+) — (.+)", line
        )
        if not exact:
            errors.append(f"unexpected or malformed verdict heading in detailed section: {line}")
            continue
        actual_details.append((exact.group(1), exact.group(2), exact.group(3)))

    if actual_details != expected_details:
        errors.append("detailed sections must match FAIL/NEEDS_REVIEW ledger rows exactly once and in CSV order")
    required_detail_fields = (
        "**WCAG level:**",
        "**Severity / review priority:**",
        "**Affected or unresolved instances:**",
        "**Coverage:**",
        "**Representative evidence:**",
        "**Impact or uncertainty:**",
        "**Remediation or exact manual verification:**",
    )
    for _, sc_id, _ in expected_details:
        detail = detail_for(sc_id)
        for field in required_detail_fields:
            if field not in detail:
                errors.append(f"detailed finding {sc_id} is missing mandatory field {field}")
        severity_match = re.search(
            r"^[-*] \*\*Severity / review priority:\*\*\s*(\S+)",
            detail,
            re.MULTILINE,
        )
        if severity_match:
            severity = severity_match.group(1)
            if severity not in SEVERITY_LABELS:
                errors.append(
                    f"detailed finding {sc_id} uses invalid severity/review priority "
                    f"{severity!r}; use one of {', '.join(SEVERITY_LABELS)}"
                )
            baseline = FAIL_SEVERITY_BASELINES.get(sc_id)
            row = next((item for item in rows if item["sc_id"] == sc_id), None)
            if (
                row is not None
                and row["verdict"] == "❌ FAIL"
                and baseline is not None
                and severity in SEVERITY_RANK
                and SEVERITY_RANK[severity] < SEVERITY_RANK[baseline]
                and not re.search(r"\breasonable (?:accessible )?workaround\b", detail, re.IGNORECASE)
            ):
                errors.append(
                    f"FAIL {sc_id} severity {severity} is below the {baseline} baseline without "
                    "evidence of a reasonable accessible workaround"
                )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--target", type=Path)
    parser.add_argument(
        "--inventory",
        action="store_true",
        help="print deterministic source inventory JSON before evaluation (requires --target)",
    )
    parser.add_argument(
        "--scope",
        action="append",
        type=Path,
        help="exact in-scope source root; repeat for disjoint roots (requires --target)",
    )
    args = parser.parse_args()

    errors = validate_csv(args.csv_path)
    scopes = args.scope
    if scopes and args.target:
        scopes = [
            scope if scope.is_absolute() else args.target / scope
            for scope in scopes
        ]
    if scopes and not args.target:
        errors.append("--scope requires --target")
    if args.inventory and not args.target:
        errors.append("--inventory requires --target")
    if args.inventory and args.report:
        errors.append("--inventory cannot be combined with --report")
    if args.inventory and args.target and not args.target.is_dir():
        errors.append(f"target repository is not an accessible directory: {args.target}")
    if args.inventory:
        for scope in scopes or []:
            if not scope.is_dir():
                errors.append(f"audit scope is not an accessible directory: {scope}")
    if args.report:
        errors.extend(
            validate_report(args.report, read_csv(args.csv_path), args.target, scopes)
        )
    elif args.target and not args.inventory:
        errors.append("--target requires --report")
    if errors:
        print("validate_audit: FAIL", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    if args.inventory:
        print(json.dumps(build_source_inventory(args.target, scopes), indent=2))
        return 0
    print("validate_audit: OK (55 criteria; A=31; AA=24)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
