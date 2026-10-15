#!/usr/bin/env bash
# Shared helpers for headless Claude Code smoke tests.
# Source this file; do not execute it.

set -euo pipefail

CLAUDE_TIMEOUT="${CLAUDE_TIMEOUT:-300}"
VERBOSE="${VERBOSE:-0}"

PASS_COUNT=0
FAIL_COUNT=0

require_claude() {
  if ! command -v claude >/dev/null 2>&1; then
    echo "SKIP: 'claude' CLI not found on PATH." >&2
    echo "Install Claude Code and make sure 'claude --version' works, then re-run." >&2
    exit 3
  fi
}

# run_claude "prompt" [timeout] — plain text reply on stdout.
run_claude() {
  local prompt="$1" t="${2:-$CLAUDE_TIMEOUT}"
  timeout "$t" claude -p "$prompt" --output-format text 2>&1 || true
}

# run_claude_json "prompt" [timeout] — full stream-json trace on stdout,
# used to assert on structured tool invocations instead of reply prose.
run_claude_json() {
  local prompt="$1" t="${2:-$CLAUDE_TIMEOUT}"
  timeout "$t" claude -p "$prompt" --output-format stream-json --verbose 2>&1 || true
}

# skill_fired trace skill-name — did the trace invoke the Skill tool with this skill?
skill_fired() {
  local trace="$1" skill="$2"
  grep -q '"name"[[:space:]]*:[[:space:]]*"Skill"' <<<"$trace" \
    && grep -q "$skill" <<<"$trace"
}

assert_contains() {
  local output="$1" pattern="$2" name="$3"
  if grep -qi -- "$pattern" <<<"$output"; then
    echo "  PASS: $name"; PASS_COUNT=$((PASS_COUNT + 1))
  else
    echo "  FAIL: $name (expected to find: $pattern)"; FAIL_COUNT=$((FAIL_COUNT + 1))
    [ "$VERBOSE" = "1" ] && printf '--- output ---\n%s\n--------------\n' "$output"
  fi
}

assert_not_contains() {
  local output="$1" pattern="$2" name="$3"
  if grep -qi -- "$pattern" <<<"$output"; then
    echo "  FAIL: $name (must not contain: $pattern)"; FAIL_COUNT=$((FAIL_COUNT + 1))
    [ "$VERBOSE" = "1" ] && printf '--- output ---\n%s\n--------------\n' "$output"
  else
    echo "  PASS: $name"; PASS_COUNT=$((PASS_COUNT + 1))
  fi
}

create_test_project() {
  local dir
  dir="$(mktemp -d)"
  (cd "$dir" && git init -q && echo "# test project" > README.md && git add . && git -c user.email=test@test -c user.name=test commit -qm init)
  echo "$dir"
}

summary() {
  echo
  echo "Passed: $PASS_COUNT, failed: $FAIL_COUNT"
  [ "$FAIL_COUNT" -eq 0 ]
}
