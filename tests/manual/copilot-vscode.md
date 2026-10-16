# Manual checklist — aimate in GitHub Copilot (VS Code)

Copilot in VS Code has no headless mode, so this checklist is walked through by hand before each release. Update the header after every walkthrough.

Last verified: never | VS Code: — | Copilot Chat: — | aimate: —

| # | Step | Expected | OK? | Notes |
|---|------|----------|-----|-------|
| 1 | Add `"chat.plugins.marketplaces": ["Dawn-Technology/aicelerate"]` to settings.json | Setting accepted, no errors | | |
| 2 | Extensions view → search `@agentPlugins` | aimate appears | | |
| 3 | Install aimate, reload | Install completes without errors | | |
| 4 | In Copilot Chat, ask: "What aimate skills do you have?" | Core skills listed (fetch-ticket, prepare-ticket, write-plan, implement-ticket, review-pr, write-commit-message) | | |
| 5 | In a repo with staged changes, ask: "Write the commit message for my staged changes" | write-commit-message behavior: message follows the Dawn rules (no Conventional Commits prefix, why/how paragraphs) | | |
| 6 | Ask: "Break down this ticket into a plan: add CSV export to the orders page" | write-plan behavior: plan with small, sized tasks | | |
| 7 | Run Extensions: Check for Extension Updates after a release | New aimate version is offered | | |

A failed step gets a note with the exact prompt used and what happened instead, and becomes an issue on Dawn-Technology/aicelerate.
