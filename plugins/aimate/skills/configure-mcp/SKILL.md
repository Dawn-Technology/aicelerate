---
name: configure-mcp
description: Validate and configure project- or client-specific GitHub, GitLab, Jira/Confluence, Figma, Sentry, and Playwright tooling through a short interactive wizard, choosing CLI or MCP where both support the capability. Use when a user asks to install, set up, configure, repair, change, or onboard Aimate integrations or save project tool routing.
metadata:
  author: "Janne de Vos <janne.de.vos@dawn.tech>"
  version: 1.0.0
---

# Configure Aimate integrations

`agents/openai.yaml` registers this skill as a named custom agent in Copilot CLI's agent picker (`display_name`, `short_description`, `default_prompt`), so a user can launch the wizard directly instead of relying on trigger phrases.

Configure only the integrations the current project needs. Prefer an already working official CLI for overlapping developer workflows, and add an MCP connection only when selected or required by the capability. Never add MCP servers globally.

Before preflight or asking questions, read [`references/mcp-catalog.md`](references/mcp-catalog.md) completely. Treat it as the source of truth for selected implementations, versions, recognition rules, authentication, templates, and wizard questions. Do not invent another CLI or MCP implementation when the catalog has one. If a setup appears stale or unavailable, verify the official source and propose a catalog/template update before configuring the project.

## Tool routing

Use this matrix to select tooling. A dash means Aimate does not support that route for the capability.

| Capability | CLI | MCP | Default |
| --- | --- | --- | --- |
| Local branches, commits, fetch, checkout, and push | `git` | — | CLI |
| GitLab MRs, reviews, issues, and pipelines | `glab` | — | CLI |
| GitHub PRs, reviews, issues, and Actions | `gh` | GitHub MCP | CLI |
| Jira issues, JQL, comments, and transitions | `acli` | Atlassian MCP | CLI |
| Confluence search, pages, and comments | — | Atlassian MCP | MCP |
| Figma design context and canvas operations | — | Figma MCP | MCP, only when selected |
| Sentry issue, event, trace, and performance investigation | — | Sentry MCP | MCP, only when selected |
| Sentry releases, source maps, and debug symbols | `sentry-cli` | — | CLI |
| Running/generating Playwright tests, viewing traces and reports | `playwright` | — | CLI |
| Live, agent-driven browser navigation, interaction, and inspection | — | Playwright MCP | MCP, only when selected |

Resolve a route in this order:

1. Follow an explicit instruction in the current request when the matrix supports it.
2. Reuse the preferred route from the project's `aimate:tool-routing` block when it works.
3. Use the configured fallback when the preferred route is unavailable or unauthenticated.
4. Without project routing, use the default and then the other supported route from the matrix.

Never ask again while the resolved route works. Use the configured fallback automatically and report it briefly. Never fall back to a route shown as unsupported. After an ambiguous remote write failure, reconcile remote state before retrying or changing routes.

## Preflight

Validate the current project before asking configuration questions. Keep this phase read-only.

1. Find the project root from Git when available; otherwise use the current workspace root.
2. Inspect `AGENTS.md` for an existing `aimate:tool-routing` block. Treat its primary and fallback values as project policy. Recognize the older `aimate:tool-preferences` block and offer to migrate it without losing valid choices.
3. Detect the relevant CLIs from the catalog. For each detected executable:
   - Read its version without installing or upgrading anything.
   - Run only the catalog's non-secret authentication/status check. Never use flags that display a token.
   - Compare the authenticated host with `git remote get-url origin` where applicable.
4. Locate project-level MCP configuration supported by the active host, including `.mcp.json`. Do not inspect or modify global user configuration.
5. If a config exists:
   - Parse it and report malformed JSON before continuing.
   - Inventory every server name, transport, command, URL, input reference, and any duplicate or conflicting names.
   - Recognize GitHub, Atlassian, Figma, and Sentry by URL, command/package, and server name; do not rely on the name alone.
   - Recognize an existing GitLab MCP as obsolete. Report it and offer to remove it explicitly; never replace or recreate it.
   - Check that referenced input IDs exist, without requesting or printing their secret values.
   - For stdio servers, verify that the executable exists. Do not install packages or start a server merely to test it.
6. Inspect `git remote get-url origin` and compare its provider and host with every configured repository route. Flag a GitHub/GitLab mismatch and detect self-hosted GitLab URLs.
7. Use MCP server/tool discovery from the active host when available. Match discovered tools to each configured integration and make one harmless read-only call only when authentication or connectivity still needs confirmation. Never create, update, comment on, or delete remote data during validation.
8. Derive a short client slug from the directory name and existing server names.

Classify each CLI and MCP route separately:

- **Working**: discovered by the host and a harmless read-only operation succeeds.
- **Configured, unverified**: structurally valid, but the host cannot discover it or no safe connectivity check is available. Use only for MCP routes.
- **Needs authentication**: discovered, but its read-only check reports missing or expired authentication.
- **Broken**: malformed, missing executable/input, unreachable after a safe check, or incompatible with the repository host.
- **Not configured**: no matching project server exists. Use **Not installed** for a missing CLI executable.

Present a compact preflight summary before the wizard. Never call a server **Working** based only on valid JSON or a reachable public URL. If the host must reload before discovery, say so and classify it as **Configured, unverified**.

If configuration is malformed, stop before editing it and offer to repair it without discarding any recoverable entries. If every selected capability already has a **Working** route and its preference is saved, report that no changes are needed and finish.

## Wizard

Use the preflight results and the question matrix in `references/mcp-catalog.md` to avoid redundant questions and preserve working servers. Ask as few questions as possible. Use the host's structured user-input tool when available.

1. Ask one repository-provider question: **GitLab**, **GitHub**, or **none** only when the Git remote and working configuration do not already answer it. Do not ask separate GitLab and GitHub yes/no questions because they serve the same purpose.
   - When GitLab is selected, require `glab`. If it is missing, offer the official installation step for the platform but never install it without user confirmation. After installation, guide `glab auth login` and verify with `glab repo list --member`. Mention that a fine-grained personal access token (see `references/mcp-catalog.md`) is a narrower-scoped alternative to the default OAuth flow; offer it, but do not push it on a user who is fine with OAuth.
2. Ask one multi-select additional-integrations question for **Atlassian**, **Figma**, **Sentry**, and **Playwright**, with **none** as an exclusive option. Clearly mark integrations already configured and default to keeping them. If the host cannot render multi-select questions, ask for a comma-separated selection in one conversational question; do not ask four separate yes/no questions. Playwright has no authentication or route-preference question; selecting it always adds the Playwright MCP server.
3. Ask one shared route-preference question only when GitHub or Jira is selected, both routes could satisfy the selected capability, and no saved routing policy answers it: **Automatic**, **Prefer CLI**, or **Prefer MCP**. GitLab always uses `glab` and is not part of this question. Convert the answer into an explicit preferred route and fallback for each selected capability.
4. When Atlassian is selected, ask whether the project needs **Jira only**, **Confluence only**, or **Jira and Confluence**. Confluence always requires MCP; Jira can use `acli` or MCP.
5. Ask only for details required by the selected variants:
   - GitLab: derive the hostname from the Git remote. Ask **GitLab.com** or **self-hosted** only when no remote answers it.
   - Atlassian: ask for a recognizable client/server name. Authentication and site selection happen through Atlassian OAuth; never request a password.
   - Sentry: ask **Sentry Cloud** or **self-hosted**. For self-hosted, ask for the HTTPS host name.
   - GitHub, Figma, Sentry Cloud, and GitLab.com need no further URL question.
6. For each **Broken** or **Needs authentication** route, explain whether the next action is repair, authentication, or replacement. Do not replace a working route just because its name or version differs from the templates.
7. Derive the actual routes using the catalog. GitLab always uses `glab`; never add GitLab MCP. Do not add GitHub MCP when its selected CLI route is working. Do not add Atlassian MCP for Jira-only when the selected `acli` route is working. Figma design context, Confluence, Sentry investigation, and live browser automation require MCP. Playwright's CLI and MCP are complementary, not alternate routes for the same capability: detect the CLI independently of whether the MCP server is selected.
8. Show a concise summary of additions, repairs, preserved servers, saved preferences, and removals. Never remove an existing server unless the user explicitly requests it. Write after confirmation. If the user's initial request already specifies every choice, skip answered questions and confirmation.

If structured questions are unavailable, ask the same questions conversationally in one compact message.

## Apply configuration

Use the template selected by `references/mcp-catalog.md` from `assets/templates/`:

- `github-cloud.mcp.json`
- `atlassian-cloud.mcp.json`
- `figma.mcp.json`
- `sentry-cloud.mcp.json`
- `sentry-self-hosted.mcp.json`
- `playwright.mcp.json`
- `project.mcp.example.json` for the combined shape
- `agents-tool-routing.md` for saved project routes and fallback behavior
- `agents-jira.md` for optional Jira project guidance
- `claude-agents-import.md` when Claude Code needs to import `AGENTS.md`

Replace `client` in server names with the normalized client slug. Use lowercase letters, digits, and hyphens. This makes multiple client connections distinguishable in one workspace, for example `atlassian-acme` and `atlassian-contoso`.

Create or update `.mcp.json` in the project root:

- Preserve unrelated top-level keys, inputs, and servers.
- Merge into `mcpServers`; never overwrite the entire file.
- Stop and explain the conflict if a selected server name already exists with different settings. Let the user choose whether to replace it or use another name.
- Keep valid JSON with two-space indentation and a trailing newline.
- Never put a real token, password, or secret in the file. Retain `${input:...}` placeholders.
- Add an input only when its selected server uses it, and do not duplicate an input with the same `id`.

Offer to append the routing policy from `assets/templates/agents-tool-routing.md` to the project's `AGENTS.md`. Keep only selected capabilities, replace every placeholder with an explicit CLI, named MCP server, or `none`, and order supported alternatives according to the chosen preference. Preserve existing instructions and update the marked block instead of duplicating it. Explain that skills will try the configured fallback without asking again and that an explicit user instruction still overrides the table.

Claude Code reads `CLAUDE.md` instead of `AGENTS.md`. When Claude Code compatibility is requested or detected, inspect `CLAUDE.md`. If it does not already import `AGENTS.md`, offer to add the single `@AGENTS.md` line from `assets/templates/claude-agents-import.md`. Preserve all existing Claude-specific instructions and never replace or symlink an existing file.

When Jira is selected, offer to append the Jira guidance from `assets/templates/agents-jira.md` to the project's `AGENTS.md`. Replace the site and project placeholders, preserve existing instructions, and update the marked block instead of duplicating it.

## Verify and hand off

Repeat the preflight checks after writing. Reload/restart the MCP host when the host exposes a safe reload action; otherwise ask the user to reload and explain that runtime verification remains pending. Report:

- which named servers were added or already present;
- which CLIs were found and authenticated for the matching host;
- where the project configuration lives;
- which preferred and fallback routes were saved in `AGENTS.md`;
- each integration's final status using the preflight classifications;
- which connections still require host authentication or a token prompt;
- whether the MCP host must reload the project or restart before discovering new servers.

Do not claim a connection works merely because its JSON is valid. If MCP discovery tools are available, check that the configured names appear. Otherwise give the user the exact reload/authentication next step.
