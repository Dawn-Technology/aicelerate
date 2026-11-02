#!/usr/bin/env bash
# Verifies core aimate skills fire on natural developer prompts.
#
# Routing is stochastic: each prompt gets up to RUNS attempts and passes on
# any fire. This proves a skill *can* fire (loading and routing), not that it
# fires reliably; the per-prompt fire rate is printed for trend watching.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"
require_claude

RUNS="${RUNS:-3}"

echo "=== Test: aimate skills fire on natural prompts (up to $RUNS runs each) ==="

# skill|natural prompt a Dawn developer would type, never naming the skill
cases=(
  "write-commit-message|I've staged my changes, write the commit message for them"
  "write-plan|Break this ticket down into an implementation plan: add CSV export to the orders page"
  "prepare-ticket|Check whether ticket ABC-123 is ready to be picked up by a developer"
  "review-pr|Review pull request 42 on this repo before it gets merged"
)

project="$(create_test_project)"
cd "$project"

for entry in "${cases[@]}"; do
  skill="${entry%%|*}"
  prompt="${entry#*|}"
  fires=0
  for ((i = 1; i <= RUNS; i++)); do
    trace=$(run_claude_json "$prompt" 180)
    if skill_fired "$trace" "$skill"; then fires=$((fires + 1)); break; fi
  done
  if [ "$fires" -gt 0 ]; then
    echo "  PASS: $skill fired (attempt $i of $RUNS)"; PASS_COUNT=$((PASS_COUNT + 1))
  else
    echo "  FAIL: $skill never fired in $RUNS runs (prompt: $prompt)"; FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
done

summary
