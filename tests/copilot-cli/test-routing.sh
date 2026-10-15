#!/usr/bin/env bash
# Copilot routing evals: do aimate skills fire when they should, on Copilot?
#
# Copilot is the primary host for Dawn's developers, so firing is measured here,
# not assumed from Claude Code results. The prompts are shared with the Claude
# Code plugin-eval cases (plugins/aimate/evals/plugin/*/prompt.md) so both hosts
# are measured on identical phrasings. Each run pins --session-id and the fire
# verdict comes from the structured "skill.invoked" events in that session's
# ~/.copilot/session-state/<id>/events.jsonl — not from reply text.
#
# Spends Copilot quota; run on demand. RUNS=N repeats each prompt (default 1).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CASES_DIR="$REPO_ROOT/plugins/aimate/evals/plugin"
RUNS="${RUNS:-1}"

if ! command -v copilot >/dev/null 2>&1; then
  echo "SKIP: 'copilot' CLI not found on PATH." >&2
  exit 3
fi

# case-directory | skill name pattern | fire or quiet
CASES=(
  "decompose-routes-to-a-skill|write-plan\|prepare-ticket\|write-prd|fire"
  "commit-message-fires|write-commit-message|fire"
  "commit-message-stays-quiet-on-review|write-commit-message|quiet"
  "prepare-ticket-fires|prepare-ticket\|validate-ticket|fire"
  "implement-stays-quiet-on-readiness|implement-ticket|quiet"
  "plan-fires-on-break-down-ticket|write-plan|fire"
)

strip_frontmatter() { awk 'c==2 {print} /^---$/ {c++}' "$1"; }

new_uuid() { python3 -c "import uuid; print(uuid.uuid4())"; }

PASS=0; FAIL=0
for entry in "${CASES[@]}"; do
  IFS='|' read -r dir pattern mode <<<"${entry}"
  prompt="$(strip_frontmatter "$CASES_DIR/$dir/prompt.md")"
  fires=0
  for ((i = 1; i <= RUNS; i++)); do
    sid="$(new_uuid)"
    work="$(mktemp -d)"
    (cd "$work" && git init -q && echo "# project" > README.md && git add -A && git -c user.email=t@t -c user.name=t commit -qm init)
    timeout 300 copilot -p "$prompt" --session-id "$sid" --allow-all-tools -s -C "$work" >/dev/null 2>&1 || true
    events="$HOME/.copilot/session-state/$sid/events.jsonl"
    if [ -f "$events" ] && grep '"skill.invoked"' "$events" | grep -Eq "\"skillName\":\"($pattern)\""; then
      fires=$((fires + 1))
    fi
  done
  if [ "$mode" = "fire" ]; then
    if [ "$fires" -gt 0 ]; then echo "  PASS: $dir fired ($fires/$RUNS)"; PASS=$((PASS + 1)); else echo "  FAIL: $dir never fired in $RUNS run(s)"; FAIL=$((FAIL + 1)); fi
  else
    if [ "$fires" -eq 0 ]; then echo "  PASS: $dir stayed quiet"; PASS=$((PASS + 1)); else echo "  FAIL: $dir fired $fires/$RUNS time(s), must stay quiet"; FAIL=$((FAIL + 1)); fi
  fi
done

echo
echo "Passed: $PASS, failed: $FAIL (fire verdicts from session events, not reply text)"
[ "$FAIL" -eq 0 ]
