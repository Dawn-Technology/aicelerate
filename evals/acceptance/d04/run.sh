#!/usr/bin/env bash
# Held-out acceptance for d04 — never shown to the agent.
# Run with cwd = the agent's workdir. Exercises only the agreed CLI contract.
set -euo pipefail

[ -f kitty.php ] || { echo "FAIL: kitty.php missing" >&2; exit 1; }

run() { php kitty.php "$@"; }

run add alice 12.50 >/dev/null
run add bob 7 >/dev/null
run add alice 10 >/dev/null

bal_alice="$(run balance alice | tr -d '[:space:]')"
bal_bob="$(run balance bob | tr -d '[:space:]')"
total="$(run total | tr -d '[:space:]')"

ok() { php -r "exit(abs((float)\"$1\" - $2) < 0.001 ? 0 : 1);"; }

ok "$bal_alice" 22.50 || { echo "FAIL: alice balance '$bal_alice', expected 22.50" >&2; exit 1; }
ok "$bal_bob" 7 || { echo "FAIL: bob balance '$bal_bob', expected 7" >&2; exit 1; }
ok "$total" 29.50 || { echo "FAIL: total '$total', expected 29.50" >&2; exit 1; }

echo "held-out d04 ok: contract holds (add, balance, total with persistence)"
