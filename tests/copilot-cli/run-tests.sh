#!/usr/bin/env bash
# Copilot CLI smoke tests for the aimate plugin. See README.md for setup.
set -euo pipefail

PASS=0; FAIL=0
ok()   { echo "  PASS: $1"; PASS=$((PASS + 1)); }
bad()  { echo "  FAIL: $1"; FAIL=$((FAIL + 1)); }

if ! command -v copilot >/dev/null 2>&1; then
  echo "SKIP: 'copilot' CLI not found on PATH." >&2
  exit 3
fi

echo "=== Test: aimate skills listed by copilot skill list (free, deterministic) ==="
listing=$(copilot skill list 2>&1 || true)
for skill in fetch-ticket prepare-ticket write-plan implement-ticket review-pr write-commit-message; do
  if grep -q "^  $skill " <<<"$listing"; then ok "skill listed: $skill"; else bad "skill listed: $skill"; fi
done

echo "=== Test: headless session sees aimate skills ==="
output=$(timeout 300 copilot -p "List every skill available to you that comes from the aimate plugin. Reply with just the skill names." 2>&1 || true)
for skill in prepare-ticket write-plan write-commit-message; do
  if grep -qi "$skill" <<<"$output"; then ok "skill visible headless: $skill"; else bad "skill visible headless: $skill"; fi
done

echo "=== Test: commit flow fires write-commit-message (asserts on the produced commit) ==="
dir=$(mktemp -d)
(
  cd "$dir"
  git init -q && echo "# demo" > README.md && git add -A
  git -c user.email=t@t -c user.name=t commit -qm init
  echo "extra line" >> README.md && git add -A
)
timeout 300 copilot -p "I've staged my changes in $dir — write the commit message for them and commit." --allow-all-tools >/dev/null 2>&1 || true
subject=$(git -C "$dir" log -1 --format=%s)
body=$(git -C "$dir" log -1 --format=%b)
if [ "$subject" != "init" ]; then ok "a commit was made"; else bad "a commit was made"; fi
if [ -n "$body" ]; then ok "commit has a body (why-paragraph per the skill's rules)"; else bad "commit has a body"; fi
if [ "${#subject}" -le 72 ] && [[ "$subject" != *:* ]]; then ok "subject within 72 chars, no Conventional-Commits prefix"; else bad "subject style"; fi

echo
echo "Passed: $PASS, failed: $FAIL"
[ "$FAIL" -eq 0 ]
