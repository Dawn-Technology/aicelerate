#!/usr/bin/env bash
# Held-out acceptance for d03 — never shown to the agent.
# Run with cwd = the agent's workdir.
#
# The ticket is deliberately vague, so these checks are interpretation-agnostic:
# 1. the repo's own suite passes in the workdir;
# 2. the agent's tests genuinely cover NEW behavior: copied onto the pristine
#    fixture, the test suite must FAIL (criteria fail first — requirement R3).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRISTINE="$SCRIPT_DIR/../../fixtures/php-app"

php tests/run.php

tmp="$(mktemp -d)"
cp -r "$PRISTINE/." "$tmp/"
rm -rf "$tmp/tests"
cp -r tests "$tmp/tests"
if (cd "$tmp" && php tests/run.php >/dev/null 2>&1); then
  echo "FAIL: the agent's tests pass on the untouched fixture — no new behavior is actually tested" >&2
  exit 1
fi
echo "held-out d03 ok: suite passes on the work, agent's tests fail on baseline"
