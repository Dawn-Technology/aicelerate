# Copilot CLI smoke tests

Status: pending spike — not yet established whether the Copilot CLI loads aimate's skills at all. No test infrastructure is built until that question is answered.

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
| — | — | — | not yet run | requires a machine with the Copilot CLI installed |
