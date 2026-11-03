#!/usr/bin/env bash
# Held-out acceptance for d01 — never shown to the agent.
# Run with cwd = the agent's workdir.
set -euo pipefail

# 1. The repo's own suite must pass (the agent must have updated the stale date test).
php tests/run.php

# 2. Held-out check: the export really produces ISO 8601 dates, day > 12 to catch swaps.
php -r '
spl_autoload_register(function ($class) {
    $p = getcwd() . "/src/" . str_replace("\\", "/", substr($class, 4)) . ".php";
    if (str_starts_with($class, "App\\") && file_exists($p)) require $p;
});
$o = new App\Orders\Order(1, "x", 1.0, new DateTimeImmutable("2026-03-25"));
$csv = (new App\Export\CsvExporter())->export([$o]);
if (!str_contains($csv, "2026-03-25")) { fwrite(STDERR, "expected 2026-03-25 in: $csv"); exit(1); }
if (str_contains($csv, "03/25/2026") || str_contains($csv, "25/03/2026")) { fwrite(STDERR, "old format still present"); exit(1); }
echo "held-out d01 ok\n";
'
