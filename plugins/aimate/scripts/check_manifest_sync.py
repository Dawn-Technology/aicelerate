#!/usr/bin/env python3
"""Fail if a Claude Code .claude-plugin manifest drifts from its canonical source.

Claude Code discovers the marketplace and plugin via the .claude-plugin/*.json
files. They must mirror the Copilot-canonical manifests exactly (by parsed JSON).
They are committed as real files (not symlinks) so Windows checkouts work, which
means nothing stops them drifting apart — this check does.
"""
import json
import sys
from pathlib import Path

# (canonical source, Claude Code mirror), relative to repo root.
PAIRS = [
    ("marketplace.json", ".claude-plugin/marketplace.json"),
    ("plugins/aimate/plugin.json", "plugins/aimate/.claude-plugin/plugin.json"),
]


def load(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    root = Path(__file__).resolve().parents[3]
    failures = []
    for canonical_rel, mirror_rel in PAIRS:
        canonical, mirror = root / canonical_rel, root / mirror_rel
        if not mirror.exists():
            failures.append(f"{mirror_rel}: missing")
            continue
        try:
            if load(canonical) != load(mirror):
                failures.append(
                    f"{mirror_rel}: out of sync with {canonical_rel} "
                    f"(copy {canonical_rel} onto {mirror_rel})"
                )
            else:
                print(f"OK: {mirror_rel} mirrors {canonical_rel}")
        except json.JSONDecodeError as exc:
            failures.append(f"{mirror_rel} or {canonical_rel}: invalid JSON ({exc})")

    if failures:
        print("\nMANIFEST SYNC FAILED:", file=sys.stderr)
        for line in failures:
            print(f"  - {line}", file=sys.stderr)
        return 1
    print("\nAll manifests in sync.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
