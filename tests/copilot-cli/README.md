# Copilot CLI smoke tests

Status: GO — the spike established that the Copilot CLI installs aimate and its skills load and fire.

```bash
tests/copilot-cli/run-tests.sh
```

Requires the `copilot` CLI on PATH, authenticated (`gh auth status` logged in), with aimate installed: `copilot plugin install ./plugins/aimate` from the repo root. Three tests run: a free deterministic check that all 20 skills are listed by `copilot skill list`, a headless prompt asking for the available aimate skills, and a commit-flow fire test asserting the produced commit follows the write-commit-message rules (subject plus body). Copilot's non-interactive output is plain text, so fire assertions are on observable effects (the git commit) rather than a structured trace; that makes them less precise than the Claude Code equivalents.

Note: direct local-path plugin installs print a deprecation warning (1.0.98); a future Copilot release will require marketplace installs. Copilot marketplaces have their own format, so when that lands the repo needs a Copilot-compatible marketplace entry — tracked as an open point.

## The spike (timebox: half a day)

1. Install the current GitHub Copilot CLI and record its version here.
2. Install aimate via the route the repo README documents for Copilot.
3. Run the CLI non-interactively (confirm the exact prompt flag against the installed release) and ask it to list available skills.
4. If skills load: ask one natural prompt per core skill and check whether the matching skill fires.

## Outcomes

Go: build `test-helpers.sh`, `test-skills-load.sh` and `test-skill-fires.sh` here, mirroring `tests/claude-code/`, and document which aimate capabilities are degraded on Copilot so those failures are expected-and-skipped rather than red.

No-go: record below what was tried, the versions, and what failed. Copilot coverage then falls back to the manual checklists in `tests/manual/`.

## Spike log

| Date | Copilot CLI version | aimate version | Outcome | Notes |
|------|--------------------:|---------------:|---------|-------|
| 2026-10-15 | 1.0.98 | 3.7.0 | GO | `copilot plugin install ./plugins/aimate` installed all 20 skills; `copilot skill list` shows them; a natural commit prompt produced a commit following the write-commit-message rules (subject + why-body, branch-key rule applied). Direct local installs are deprecated in favor of plugin@marketplace. |
