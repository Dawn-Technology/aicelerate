# Rejected skill changes

Append-only ledger of skill and description changes rejected on eval evidence, so contributors can review prior attempts before proposing overlapping work. One concise row per rejected proposal; accepted changes are not recorded here.

| Date | Affected skill | Attempted change | Score (before → after) | PR and outcome |
|------|----------------|------------------|------------------------|----------------|
| 2026-10-15 | prepare-ticket (and all skills, on Copilot) | Description rewrite adding natural readiness phrasings and a pasted-inline clause, aiming to make Copilot's router fire the skill | Copilot fire rate 0/2 → 0/2 (0/10 cumulative across all Copilot routing attempts today); Claude Code routing unaffected (fired before and after) | Not a PR — attempted on feature/aimate-test-suite, measured by tests/copilot-cli/test-routing.sh. Verdict: description tuning does not reach Copilot's router; reliable aimate use on Copilot needs explicit invocation or instruction-file nudges (untested). Description kept (it is better prose and cost nothing), claim rejected. |
