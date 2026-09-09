# Release notes

## 2.4.0

Added `validate-ticket`, which decides whether one ticket is ready for development and rewrites its description into a brief an agent can build from. It supports Jira work items, GitHub Issues, and GitLab Issues through the saved provider route, and a ticket pasted as plain text when no tracker is reachable. Every provider difference — identifier parsing, field mapping, Jira custom-field discovery, and the ADF/wiki formatting trap on a description write — lives in `references/provider-operations.md` rather than in the workflow.

The skill traces each load-bearing claim in the description and comments against the checkout, gives it a verdict with a `file:line` behind it, and then closes the design tree in the same Observed / Decision / Assumption vocabulary `write-plan` uses. It closes what the repository can answer and asks only what a human must decide, in one batch, with a recommendation attached to each question. A blocking branch never closes as an assumption, and assumptions that are taken stay visible in the ticket.

The verdict is arithmetic on a twelve-criterion rubric rather than a judgment call, and it routes rather than reports: every run ends with one named next action and one owner. A ready ticket gets its rewritten description written back, and the ticket becomes the brief an implementer starts from. A `not-ready` ticket with mechanical gaps gets them closed in the same run, including a split into children when that is the gap. A `not-ready` ticket with an open blocking decision goes back to a human — asked of the user directly, or posted on the ticket for its author — because an agent asked to settle a decision it does not own will invent one, and an invented decision reads as settled once it sits in a description.

The rewritten description applies prompting rules to a ticket: why before what, an observable goal, provenance on every fact, scope bounded in both directions, and a definition of done carrying the real validation commands.

Output is written for a person. A finding is a bold one-line claim, the code that contradicts it with a `file:line`, and one imperative action — grouped as **Blocking**, **Filled in for you**, and **Worth a look**, with no ids, slugs, or severity tokens. The report is built for a terminal: findings first, a few lines on what the rewrite changes, then the verdict and the single next action last, where they stay on screen rather than scrolling out of view. The rewritten description, the claim ledger, and the design tree stay behind an offer instead of being dumped, and a criterion that passed is never printed. A comment posted on the ticket inverts that order, since a document is read top-down. The skill writes no file of its own: the durable record is the ticket — the description plus one comment in the same format. It also keeps its coupling to other skills to a minimum, defining its own design-tree vocabulary and provider operations rather than depending on them.

## 2.3.0

Added `review-and-resolve-pr`, which runs both halves of the review loop over one PR/MR in a single autonomous pass. It reviews through `review-pr`, publishes every finding at every severity as an inline comment, then hands those threads to `resolve-pr-feedback` to validate, fix, gate, self-review, push, and reply — and reports the addressed findings in one table.

The skill composes the two existing halves and owns only the seam between them: the shared preconditions, the standing directive that lifts `review-pr`'s hard stop, the finding-to-thread mapping the resolution half needs, the guarantee that both worktrees are gone at the end, and the combined report. Neither half's workflow is reimplemented, and `code-review` is never invoked directly.

Findings this run wrote get no special standing when it comes to fixing them. Each comment is validated against the repository in the fix worktree like any human reviewer's, so `reject`, `already-addressed`, and `needs-clarification` stay live outcomes, and the report ends with a review-quality section naming every finding the run posted and then rejected. Scope stays on the threads the run created; threads a human opened are reported as untouched. It approves nothing, requests changes on nothing, and never re-reviews its own pushed result.

## 2.2.0

Added `resolve-pr-feedback`, which closes the review loop that `review-pr` opens. It reads the unresolved threads on a GitHub PR or GitLab MR, validates each comment against the real code, applies the ones that hold up in an isolated worktree, runs the project's own quality gates, self-reviews the result through `code-review`, and only then pushes and replies per thread.

Feedback that does not hold up is rejected with evidence rather than applied, and threads are resolved only when the fix actually landed. The skill runs autonomously — it decides and reports each judgment call instead of pausing for approval — delegates its commit messages to `write-commit-message`, and never force-pushes, rewrites branch history, or approves its own work.

Review content is treated as untrusted throughout: a comment can name a concern, but it cannot redirect the workflow, widen the scope, or supply commands to run. Contributions from a fork are handled without executing anything the contributor controls and without taking direction from anything they wrote, so those runs skip dependency installation and the quality gates, read the head's own instruction files as evidence rather than orders, and report themselves as unverified, leaving verification to CI on the review.

## 2.1.0

Extracted the shared code-review core, added `review-local`, and updated `review-pr` to delegate analysis to the core.

## 2.0.0

`aimate` is now skills-first. The plugin no longer bundles Figma, GitLab, or Atlassian MCP connections globally. Projects configure only the integrations they need through `configure-mcp` or the supplied project templates.

The setup wizard now validates existing official CLIs and MCP connections before changing anything. GitLab workflows always use the official `glab` CLI and no GitLab MCP template is shipped. GitHub and Jira save preferred and fallback routes in `AGENTS.md`; skills automatically try the fallback instead of asking again. Confluence and Figma keep using MCP where no equivalent CLI exists. Sentry uses MCP for investigations and `sentry-cli` for release assets.

### Breaking change

- Removed the plugin-level `.mcp.json`.
- Removed `mcpServers` from `plugin.json`.
- Removed the GitLab MCP setup and made `glab` a prerequisite for GitLab workflows.
- GitLab.com is no longer assumed for every repository.
- Figma and Atlassian authentication is no longer requested merely because Aimate is installed.

### Migration from 1.x

1. Upgrade or reinstall the Aimate plugin.
2. Install `glab` (`brew install glab` on Homebrew platforms).
3. Authenticate with `glab auth login` and verify access with `glab repo list --member`.
4. If the MCP host retains the old plugin-owned `figma`, `gitlab`, or `atlassian/atlassian-mcp-server` entries, remove or disconnect those old entries in the host.
5. In every client checkout, run `configure-mcp`.
6. Keep the detected working project integrations or select GitLab/GitHub and optional Atlassian, Figma, and Sentry integrations.
7. Choose `Automatic`, `Prefer CLI`, or `Prefer MCP` for GitHub and Jira so the wizard can save explicit preferred and fallback routes.
8. For Claude Code, let the wizard add `@AGENTS.md` to `CLAUDE.md` when that import is missing.
9. Reload or restart the MCP host when requested.
10. Complete OAuth for each newly named MCP connection.

Project configuration must not contain real tokens. Self-hosted Sentry uses a
secret input placeholder; hosted MCP connections use host-managed OAuth.

This release supersedes and closes [#16](https://github.com/Dawn-Technology/aicelerate/issues/16).
