# Aimate integration catalog

Last verified: 2026-08-12

This file is the source of truth for the implementations, versions, authentication, recognition rules, and questions used by `configure-mcp`. Use the [tool-routing matrix](../SKILL.md#tool-routing) for CLI/MCP selection. Re-check the linked official source before changing a version, endpoint, package, or authentication method.

`figma connect` is deliberately outside the Figma design route: it publishes Code Connect mappings and does not replace the Figma MCP.

## Question flow

Skip any question already answered reliably by the request, Git remote, or a **Working** preflight result. Never ask for passwords or token values.

### Q1 — Repository provider

Ask as one mutually exclusive question:

> Which repository provider should this project connect to?

- **GitLab** — Use the official `glab` CLI for projects and merge requests.
- **GitHub** — Configure GitHub repositories and pull requests.
- **None** — Do not configure a repository integration.

Recommend the provider detected from `origin`. If an existing working CLI or MCP route matches it, preserve it and skip Q1.

### Q1a — GitLab hosting

Ask only after GitLab is selected and the remote host does not answer it:

> Where is this GitLab project hosted?

- **GitLab.com** — Authenticate `glab` against `gitlab.com`.
- **Self-hosted** — Ask for the GitLab hostname next.

For self-hosted GitLab ask:

> What is the hostname of the GitLab instance?

Use the hostname with `glab auth status --hostname <host>` and `glab auth login --hostname <host>`. Do not ask the user for an API URL or token.

### Q2 — Additional integrations

Ask as one multi-select question:

> Which additional integrations does this project need?

- **Atlassian** — Add Jira/Confluence access.
- **Figma** — Add design access.
- **Sentry** — Add error, issue, trace, and performance diagnostics.
- **Playwright** — Add local browser automation and inspection for an agent session.
- **None** — Add none; this option is exclusive.

Allow any combination of Atlassian, Figma, Sentry, and Playwright. Clearly show already configured integrations and default to retaining them. If the host has no multi-select UI, ask for a comma-separated selection in one question instead of four yes/no questions.

Playwright has no authentication step and no CLI/MCP route choice: selecting it always adds the Playwright MCP server. Detect the Playwright CLI separately during preflight; it does not depend on this selection.

### Q2a — Shared route preference

Ask once only when GitHub or Jira is selected, both routes could satisfy the selected capability, and no valid project preference exists:

> How should Aimate choose when both an official CLI and MCP can perform the action?

- **Automatic** — Reuse a working saved route; otherwise prefer the capability default.
- **Prefer CLI** — Prefer `gh` or `acli`; use MCP for capabilities without a CLI equivalent.
- **Prefer MCP** — Prefer the matching MCP; keep local Git and CLI-only release/build operations on CLI.

GitLab always uses `glab`, regardless of this preference. Translate the answer into explicit preferred and fallback routes in the marked `AGENTS.md` block when the user agrees. Do not ask separate GitHub/Jira preference questions.

### Q2b — Atlassian capabilities

Ask only when Atlassian is selected and existing project guidance does not answer it:

> Which Atlassian capabilities does this project need?

- **Jira only** — Use `acli` or Atlassian MCP according to the route preference.
- **Jira and Confluence** — Jira follows the preference; Confluence uses Atlassian MCP.
- **Confluence only** — Use Atlassian MCP.

Do not install Atlassian MCP for Jira-only when authenticated `acli` is the resolved route.

### Q2c — Sentry hosting

Ask only after Sentry is selected and existing configuration does not answer it:

> Where is this Sentry project hosted?

- **Sentry Cloud** — Use the official hosted MCP with OAuth.
- **Self-hosted** — Ask for the HTTPS Sentry hostname next.

For self-hosted Sentry ask:

> What is the HTTPS hostname of the Sentry installation?

Accept a hostname such as `sentry.example.com`, not an API token. Strip a supplied `https://` prefix when rendering the `--host` argument and confirm the normalized hostname.

### Q3 — Client identity

Ask once only when a reliable slug cannot be derived:

> What short client or project name should be used to distinguish these MCP connections?

Show the proposed lowercase slug. Reuse it for every selected server. Never ask for a separate name per integration.

### Q4 — Project guidance

Ask when a route preference is selected:

> Should I save these preferred and fallback routes in `AGENTS.md` so Aimate skills do not ask again?

When Jira is selected, combine that with:

> Should I also add project-specific Jira guidance to `AGENTS.md`?

- **Yes** — Ask for Jira site URL and default project key only when unknown.
- **No** — Configure the selected routes without changing `AGENTS.md`.

### Q5 — Confirmation

Summarize preserved, added, and repaired integrations:

> Apply this project-level integration configuration?

Do not list removals unless the user explicitly requested them.

## Supported setups

### Local Git

- **Selected implementation:** Git's `git` executable.
- **Version policy:** Use the project's installed Git; do not install or upgrade it from the wizard.
- **Capabilities:** Local repository inspection, branch/worktree management, commits, fetch, checkout, and push.
- **Safe validation:** `git --version`, `git rev-parse --show-toplevel`, `git remote get-url origin`, and `git status --short`.
- **Boundary:** Provider CLIs or MCP handle PR/MR metadata, discussions, approvals, and inline review APIs.
- **Official source:** https://git-scm.com/docs/git

### GitHub CLI

- **Selected implementation:** GitHub's official `gh` CLI.
- **Version policy:** Use a maintained installed version that provides `gh pr`, `gh api`, and `gh auth status`; do not auto-install or auto-upgrade it.
- **Capabilities:** GitHub PR metadata/diffs/reviews, issues, Actions, and authenticated REST/GraphQL through `gh api`.
- **Authentication:** Host-specific CLI authentication. Never use `--show-token` during validation.
- **Safe validation:** Verify `gh` exists, run `gh --version`, then `gh auth status --active --hostname <origin-host>`.
- **Repair action:** Ask the user to run `gh auth login --hostname <origin-host>`; never request a token in chat.
- **Official source:** https://cli.github.com/manual/

### GitLab CLI

- **Selected implementation:** GitLab's official `glab` CLI.
- **Required route:** Use `glab` for all GitLab operations. Do not configure or fall back to GitLab MCP.
- **Version policy:** Use a maintained installed version that provides `glab mr`, `glab api`, and `glab auth status`; do not auto-install or auto-upgrade it.
- **Capabilities:** GitLab MR metadata/diffs/reviews, issues, pipelines, and authenticated REST/GraphQL through `glab api` for operations without a high-level command.
- **Install:** On macOS or Homebrew-enabled Linux use `brew install glab`. For other platforms, follow the official installation options.
- **Authentication:** Host-specific CLI authentication. Never use `--show-token` during validation.
- **Safe validation:** Verify `glab` exists, run `glab --version`, then `glab auth status --hostname <origin-host>`. After login, run `glab repo list --member` as a read-only access check.
- **Repair action:** Ask the user to run `glab auth login --hostname <origin-host>`; never request a token in chat.
- **Official sources:** https://docs.gitlab.com/cli/, https://docs.gitlab.com/cli/auth/login/, and https://docs.gitlab.com/cli/repo/list/

### Atlassian CLI for Jira Cloud

- **Selected implementation:** Atlassian's official `acli` CLI.
- **Minimum tested release line:** `1.3.15-stable`, which includes the current OAuth permission update. Newer stable versions are allowed.
- **Capabilities:** Jira Cloud work-item search/view/create/edit/comment/transition/assignment and related project/sprint commands.
- **Not covered:** Confluence and Jira/Confluence Data Center.
- **Safe validation:** Verify `acli` exists, run `acli --version`, then `acli jira auth status`. Do not switch accounts during preflight.
- **Repair action:** Ask the user to run `acli jira auth login` or `acli jira auth switch`; site-admin re-authorization may be required after the 1.3.15 OAuth scope update.
- **Official sources:** https://developer.atlassian.com/cloud/acli/reference/commands/ and https://developer.atlassian.com/cloud/acli/changelog/

### Sentry CLI

- **Selected implementation:** Sentry's official `sentry-cli`.
- **Version policy:** Use a maintained installed version; do not auto-install or auto-upgrade it.
- **Capabilities:** Releases, source maps, debug symbols, and build/release automation. Do not treat it as equivalent to Sentry MCP for agent-led investigation.
- **Safe validation:** Verify `sentry-cli` exists and run `sentry-cli --version`. Run `sentry-cli info` only when Sentry CLI operations are actually selected and it will not expose credentials.
- **Official source:** https://github.com/getsentry/sentry-cli

### Playwright CLI

- **Selected implementation:** Playwright's official `playwright` CLI.
- **Version policy:** Use a maintained installed version that provides `playwright test`, `playwright codegen`, and `playwright show-report`; do not auto-install or auto-upgrade it. Detected release line at last verification: `1.62.x`.
- **Capabilities:** Running and generating end-to-end tests, opening trace/report viewers, and installing browser binaries on explicit user request.
- **Authentication:** None.
- **Safe validation:** Verify `playwright` (or the project's local `npx playwright`) exists and run `playwright --version`. Do not run `playwright install` or execute a test suite during preflight.
- **Official source:** https://playwright.dev/docs/test-cli

### Playwright MCP

- **Selected implementation:** Playwright's official `@playwright/mcp` stdio package.
- **Pinned package version:** `0.0.79`. Use `@playwright/mcp@0.0.79`; do not use `latest` or an unpinned package.
- **Transport:** stdio through `npx`.
- **Authentication:** None; it launches a local or configured browser session directly.
- **Capabilities:** Live, agent-driven browser navigation, interaction, and accessibility-tree snapshots during a session. Not a replacement for the Playwright CLI's test running or codegen.
- **Template:** `playwright.mcp.json`
- **Recognize by:** Package `@playwright/mcp`, or discovered navigate/click/snapshot browser tools.
- **Safe validation:** Verify `npx`, discover tools, then read the current page/tab state only; never navigate to an unrequested URL or submit a form during validation.
- **Official source:** https://github.com/microsoft/playwright-mcp

### GitHub Cloud

- **Selected implementation:** GitHub's official hosted MCP server.
- **Version policy:** Hosted service; no client-side version pin.
- **Transport:** Streamable HTTP.
- **Endpoint:** `https://api.githubcopilot.com/mcp/`
- **Authentication:** Host-managed GitHub OAuth. Do not request a PAT by default.
- **Template:** `github-cloud.mcp.json`
- **Recognize by:** Exact `api.githubcopilot.com/mcp` URL or discovered GitHub repository/issue/pull-request tools.
- **Safe validation:** Discover tools, then read authenticated user/context or repository metadata without mutations.
- **Not covered:** GitHub Enterprise Server and Enterprise Cloud with data residency require different setups. Explain this and verify the official GitHub documentation before adding them.
- **Official source:** https://github.com/github/github-mcp-server

### Atlassian Cloud

- **Selected implementation:** Atlassian's official hosted Rovo MCP server.
- **Version policy:** Hosted service; no client-side version pin.
- **Transport:** Streamable HTTP.
- **Endpoint:** `https://mcp.atlassian.com/v1/mcp/authv2`
- **Authentication:** Host-managed OAuth 2.1. Do not request Atlassian passwords or tokens.
- **Template:** `atlassian-cloud.mcp.json`
- **Recognize by:** `mcp.atlassian.com` URL or discovered Jira/Confluence tools.
- **Safe validation:** Discover tools, then list accessible sites/resources or read one known issue only when a project key is already available.
- **Migration:** Treat `/v1/sse` as obsolete and `/v1/mcp` as an older setup; offer migration to `/v1/mcp/authv2` without deleting credentials.
- **Not covered:** Jira/Confluence Data Center is not this cloud service. Stop and verify a suitable implementation when detected.
- **Official source:** https://support.atlassian.com/atlassian-rovo-mcp-server/docs/getting-started-with-the-atlassian-remote-mcp-server/

### Figma

- **Selected implementation:** Figma's official remote MCP server, recommended over the desktop server.
- **Version policy:** Hosted service; no client-side version pin.
- **Transport:** Streamable HTTP.
- **Endpoint:** `https://mcp.figma.com/mcp`
- **Authentication:** Host-managed Figma OAuth. Do not request a token.
- **Template:** `figma.mcp.json`
- **Recognize by:** Exact `mcp.figma.com/mcp` URL or discovered Figma file/design-context tools.
- **Safe validation:** Discover tools, then read authenticated user/context or inspect a file only when the user already supplied a file URL/key.
- **Official source:** https://developers.figma.com/docs/figma-mcp-server/remote-server-installation/

### Sentry Cloud

- **Selected implementation:** Sentry's official hosted MCP server.
- **Version policy:** Hosted service; no client-side version pin.
- **Transport:** Streamable HTTP.
- **Endpoint:** `https://mcp.sentry.dev/mcp`
- **Authentication:** Host-managed Sentry OAuth. Do not request an access token by default.
- **Template:** `sentry-cloud.mcp.json`
- **Recognize by:** Exact `mcp.sentry.dev/mcp` URL or discovered Sentry issue/event/trace tools.
- **Safe validation:** Discover tools, then list accessible organizations or projects. Do not mutate issue state.
- **Scope option:** Prefer a client-specific server name. Organization/project path scoping may be added when the user explicitly requests tighter access.
- **Official source:** https://github.com/getsentry/sentry-mcp

### Sentry self-hosted

- **Selected implementation:** Sentry's official `@sentry/mcp-server` stdio package.
- **Pinned package version:** `0.37.0`. Use `@sentry/mcp-server@0.37.0`; do not use `latest` or an unpinned package.
- **Transport:** stdio through `npx`.
- **Host:** Normalized hostname supplied through `--host=<hostname>`.
- **Authentication:** Client-specific secret input placeholder passed through `--access-token`; never store the real token.
- **Compatibility:** Disable Seer because it may not be available self-hosted.
- **Template:** `sentry-self-hosted.mcp.json`
- **Recognize by:** Package `@sentry/mcp-server`, a `--host` argument, or discovered Sentry tools.
- **Safe validation:** Verify `npx`, discover tools, then list accessible organizations or projects.
- **Official source:** https://github.com/getsentry/sentry-mcp

## Maintenance rule

When an official hosted endpoint, minimum CLI release, or pinned package is older than 90 days since `Last verified`, verify it before generating a new configuration when internet access is available. Update this catalog and the matching template together. Never change only one of them.
