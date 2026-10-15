# Evals

Behavioral (Tier 3) evaluation of the aimate plugin: a real agent runs a case's prompt against a fixture project, and the result is graded against fixed requirements. Every run spends real tokens — run on demand, never in CI. The free, deterministic checks live in `tests/` instead.

## Running

```bash
node evals/runner/run-eval.mjs all                       # every case, aimate pipeline
node evals/runner/run-eval.mjs 13-php-permissions-model  # one case
node evals/runner/run-eval.mjs all --pipeline vanilla    # control: no skill plugins
node evals/runner/run-eval.mjs all --pipeline addyosmani # comparison pipeline
node evals/runner/run-eval.mjs all --runs 3              # baseline-grade: report mean and spread
node evals/runner/run-eval.mjs all --dry-run             # print the plan only
```

The runner enables exactly one pipeline's plugin for the duration of a sweep (and re-enables aimate afterwards), so results are never contaminated by another plugin's routing. Generator and judge are different models by construction (defaults: sonnet generates, opus judges) and the report header records both plus the Claude Code version, because results shift across model and CLI versions.

Results land in `evals/results/<timestamp>/` (gitignored): one JSON per run with the full artifact, plus `report.md` with a score table, cost, wall-clock, which skills fired, and every failed check with its requirement id and a one-line repro command.

## Cases

One JSON file per case under `evals/cases/<group>/`:

```json
{
  "id": "13-php-permissions-model",
  "fixture": "php-app",
  "pipeline": "decompose",
  "prompt": "the exact user message, verbatim",
  "spec": ["the input spec, line by line"],
  "expect": [
    { "check": "between 3 and 8 tickets", "by": "structural", "type": "ticket_count", "min": 3, "max": 8 },
    { "check": "first ticket is a preparatory refactor", "by": "judge", "req": "R1" }
  ],
  "behavioral": true
}
```

Every expectation names its verifier. `structural` checks run as deterministic rules over the artifact (`ticket_count`, `single_ticket_or_none`, `demo_line_per_ticket`, `no_see_spec_reference`, `regex_present`, `regex_absent`). `judge` checks are graded by the judge model against `evals/rubrics/requirements.md`, citing the requirement id in `req`; the artifact is fenced as untrusted data. Cases define expected properties, never one right answer. The runner refuses a case missing `id`, `prompt`, `spec` or `expect`.

`evals/rubrics/requirements.md` holds the numbered requirements every judged check cites; changing a requirement is a normal reviewed pull request. `evals/fixtures/` holds the starter projects cases run against (each a small real app with passing tests). Rejected skill changes belong in `evals/REJECTED.md` so prior attempts stay visible.

## Reading results

Scores from agent runs are stochastic. Compare runs only at equal model and CLI versions, prefer three runs per case and read the spread before the mean, and treat a delta smaller than the observed spread as noise. A budget or efficiency result only counts when the same run's quality checks pass.
