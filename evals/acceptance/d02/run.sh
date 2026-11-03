#!/usr/bin/env bash
# Held-out acceptance for d02 — never shown to the agent.
# Run with cwd = the agent's workdir.
set -euo pipefail

# 1. The repo's own suite must pass.
php tests/run.php

# 2. Held-out checks on the ticket's criteria.
php -r '
spl_autoload_register(function ($class) {
    $p = getcwd() . "/src/" . str_replace("\\", "/", substr($class, 4)) . ".php";
    if (str_starts_with($class, "App\\") && file_exists($p)) require $p;
});
function fail($m) { fwrite(STDERR, "$m\n"); exit(1); }
$u = new App\Auth\User(9, "zoe", App\Auth\User::ROLE_ADMIN);
foreach (["deactivate", "reactivate", "isActive"] as $m)
    if (!method_exists($u, $m)) fail("missing method $m");
if (!$u->isActive()) fail("new user should be active");
if (!$u->canEdit() || !$u->canAdministrate()) fail("active admin lost rights");
$u->deactivate();
if ($u->isActive()) fail("deactivate did not stick");
if ($u->canEdit()) fail("deactivated user can still edit");
if ($u->canAdministrate()) fail("deactivated user can still administrate");
$u->reactivate();
if (!$u->isActive() || !$u->canEdit() || !$u->canAdministrate()) fail("reactivate did not restore rights");
$r = new App\Auth\User(10, "rea", App\Auth\User::ROLE_READER);
if ($r->canEdit()) fail("reader gained edit rights");
echo "held-out d02 ok\n";
'
