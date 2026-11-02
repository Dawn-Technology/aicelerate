# Manual checklist — aimate in GitHub Copilot (desktop)

Copilot desktop has no headless mode, so this checklist is walked through by hand before each release. Update the header after every walkthrough.

Last verified: never | Copilot desktop: — | aimate: —

| # | Step | Expected | OK? | Notes |
|---|------|----------|-----|-------|
| 1 | Install aimate via the route documented in the repo README | Install completes without errors | | |
| 2 | Ask: "What aimate skills do you have?" | Core skills listed (fetch-ticket, prepare-ticket, write-plan, implement-ticket, review-pr, write-commit-message) | | |
| 3 | Open a project, ask: "Write the commit message for my staged changes" | write-commit-message behavior: message follows the Dawn rules | | |
| 4 | Ask: "Check whether ticket ABC-123 is ready to be picked up" | prepare-ticket behavior: readiness assessment against the rubric | | |
| 5 | Note any skill that references a capability the host lacks | Behavior degrades with a clear message, no silent failure | | |

A failed step gets a note with the exact prompt used and what happened instead, and becomes an issue on Dawn-Technology/aicelerate.
