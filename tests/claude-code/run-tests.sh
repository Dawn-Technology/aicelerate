#!/usr/bin/env bash
# Runs the Claude Code smoke tests.
#
# Usage:
#   ./run-tests.sh                 # all tests
#   ./run-tests.sh --test test-skills-load.sh
#   ./run-tests.sh --verbose --timeout 600
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ONLY=""
export VERBOSE="${VERBOSE:-0}" CLAUDE_TIMEOUT="${CLAUDE_TIMEOUT:-300}"

while [ $# -gt 0 ]; do
  case "$1" in
    --test) ONLY="$2"; shift 2 ;;
    --verbose) export VERBOSE=1; shift ;;
    --timeout) export CLAUDE_TIMEOUT="$2"; shift 2 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

tests=(test-skills-load.sh test-skill-fires.sh)
[ -n "$ONLY" ] && tests=("$ONLY")

failed=0
for t in "${tests[@]}"; do
  echo
  if bash "$SCRIPT_DIR/$t"; then
    echo "OK: $t"
  else
    code=$?
    if [ "$code" -eq 3 ]; then echo "SKIPPED: $t (claude CLI not available)"; else echo "FAILED: $t"; failed=1; fi
  fi
done

exit "$failed"
