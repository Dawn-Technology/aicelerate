#!/usr/bin/env bash
# Verifies the aimate skills are visible to a headless Claude Code session.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"
require_claude

echo "=== Test: aimate skills load ==="

output=$(run_claude "List every skill available to you that comes from the aimate plugin. Reply with just the skill names." 120)

for skill in fetch-ticket prepare-ticket write-plan implement-ticket review-pr write-commit-message; do
  assert_contains "$output" "$skill" "skill listed: $skill"
done

summary
