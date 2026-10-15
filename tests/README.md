# Tests

Automated checks for the aicelerate marketplace and the aimate plugin. The suite is tiered by cost: structural checks are free and deterministic and run in CI on every pull request; host smoke tests call a real agent CLI and run on demand or on release branches.

## Layout

```
tests/
  structural/     deterministic validation of manifests, skills and links (CI, blocking)
  claude-code/    headless smoke tests against the Claude Code CLI
  copilot-cli/    headless smoke tests against the GitHub Copilot CLI
  manual/         checklists for hosts without a headless mode
```

## Structural validation

```bash
node tests/structural/validate-plugin.mjs
```

Validates, with no dependencies and no network:

- `marketplace.json` parses and every plugin `source` path exists.
- `plugins/aimate/plugin.json` parses, and its `version` matches both the marketplace entry and the newest `## x.y.z` heading in `RELEASE_NOTES.md`.
- Every directory under `plugins/aimate/skills/` contains a `SKILL.md` whose frontmatter has `name` and `description`, with `name` equal to the directory name.
- Every relative markdown link in a `SKILL.md` or its `references/` resolves to an existing file. Bare `…` targets are treated as placeholders in example content and skipped.
- No `SKILL.md` exceeds the line budget (500 lines, set at the top of the script).

Exit code 0 means all checks passed; any violation prints one line per finding and exits 1. A failure here means the plugin is broken as shipped — fix the finding, don't loosen the check.

## Claude Code smoke tests

```bash
tests/claude-code/run-tests.sh                    # all tests
tests/claude-code/run-tests.sh --test test-skills-load.sh
tests/claude-code/run-tests.sh --verbose --timeout 600
```

Requires the `claude` CLI on PATH with the aimate plugin installed; without it the tests skip with exit code 0 and a clear message. Two tests run:

- `test-skills-load.sh` asks a headless session to list aimate skills and asserts the core skill names appear.
- `test-skill-fires.sh` sends one natural developer prompt per core skill and asserts from the `stream-json` trace that the matching skill was invoked. Routing is stochastic, so each prompt gets up to `RUNS` attempts (default 3) and passes on any fire; this proves a skill can fire, not that it fires reliably.

In CI these run as a manually dispatched job (see `.github/workflows/test.yml`): the runner installs the Claude Code CLI, installs aimate from the checkout so the pull request's version is what gets tested, and needs the `EVAL_ANTHROPIC_API_KEY` repository secret.

## Copilot

The Copilot CLI is covered by a go/no-go spike before any automation is built — see `tests/copilot-cli/README.md`. Copilot desktop and Copilot in VS Code have no headless mode and are covered by the release checklists in `tests/manual/`, each carrying a "last verified" header that release PRs update.
