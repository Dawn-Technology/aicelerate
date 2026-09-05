# aimate

AI Automation Teamate.

AI Acceleration supporting SDLC — reusable skills for security auditing, repository workflows, project integration setup, and development planning.

## Compatibility Note

If you have the Superpowers plugin installed, be aware that it can sometimes interfere with skill workflows in this plugin. Superpowers includes generic skills that may trigger unexpectedly and conflict with the more specific workflow instructions used by `aimate`.

If a skill behaves inconsistently, invokes the wrong workflow, or appears to ignore its instructions, first check whether Superpowers was triggered in the workflow. If it was, disable or uninstall the Superpowers plugin and then rerun the skill.

## Skills

### `configure-mcp`

> Validate and configure project-specific GitLab, GitHub, Jira/Confluence, Figma, and Sentry integrations through a short wizard.

Detects working official CLIs and existing MCP connections before asking questions. GitLab always uses `glab`; GitHub and Jira store preferred and fallback routes in `AGENTS.md`. The wizard safely merges only the required servers into `.mcp.json` and uses client-specific server names so multiple clients can coexist in one workspace. Also registered as a named agent in Copilot CLI's agent picker (`agents/openai.yaml`).

**Trigger phrases:** "configure MCP", "set up GitLab for this project", "connect Jira", "install the Figma MCP"

---

### `asvs-audit`

> OWASP ASVS 5.0 Level 1 security audit with deterministic, evidence-based findings.

Conducts systematic security audits against all 70 OWASP ASVS 5.0 Level 1 requirements. Produces structured reports with evidence-backed PASS/FAIL/N/A classifications and severity-rated findings.

**Trigger phrases:** "security audit", "asvs audit", "vulnerability scan", "compliance review", "pentest"

---

### `review-pr`

> Review a GitLab Merge Request or GitHub Pull Request and provide findings, and post structured review comments with issue explanation plus code fixes.

Performs comprehensive code review — identifies bugs, logic errors, security issues, and style violations. Uses `code-review` for reusable analysis, then handles provider-specific GitHub/GitLab comments, approvals, and request-changes actions.

**Trigger phrases:** "review this MR", "review this merge request", "review the gitlab MR"

---

### `resolve-pr-feedback`

> Resolve review feedback on a GitLab Merge Request or GitHub Pull Request — validate each comment, fix what holds up, push, and close the threads.

The other half of the review loop. It reads every unresolved thread, verifies each one against the real code before changing anything, and gives every comment a verdict: accept, accept with a different fix, already addressed, reject, out of scope, or needs clarification. Work happens in an isolated git worktree, runs through the project's own build, lint, and test commands, and is self-reviewed with `code-review` before anything is pushed. Replies explain what happened per thread; only threads that were actually addressed get resolved.

Rejecting feedback is a first-class outcome — with evidence, not opinion. It never force-pushes, never rewrites branch history, and never approves its own work.

Like `write-commit-message`, it runs autonomously: it decides, acts, and reports every judgment call with its one-line undo, rather than pausing for approval. It stops for three things only — no authenticated route, a missing dependency, or a request that asked for a plan first.

**Trigger phrases:** "resolve the PR feedback", "address the review comments", "fix the MR comments", "apply the review feedback"

---

### `review-local`

> Review local code before committing for a user-defined scope such as files, folders, uncommitted changes, staged changes, commits, patches, or snippets.

Uses `code-review` for reusable analysis and returns structured findings without posting remote comments or changing the working tree.

**Trigger phrases:** "review my local changes", "review this folder before commit", "review staged changes"

---

### `code-review`

> Framework-agnostic reusable code review core for syntax, logic, security, style, documentation, and maintainability findings.

Provides the shared analysis workflow, input/output interfaces, severity classification, and feedback format used by `review-pr`, `review-local`, and the pre-push self-review in `resolve-pr-feedback`.

---

### `test-pr-guide`

> Produce a step-by-step manual testing guide for a branch or PR.

Analyzes the diff, identifies what changed, and writes a guide a real person can follow to verify the feature or fix works — including setup requirements, test scenarios, and expected outcomes. Supports GitLab MR URLs and local branches.

**Trigger phrases:** "how do I test this PR", "create a test plan", "write a QA checklist", "how do I test this MR"

---

### `write-commit-message`

> Write a high-quality git commit message following the seven rules of great commit messages, and commit it.

Reads the staged diff, picks up a Jira key from the branch name, and writes a message with an imperative subject and a body that explains the observable problem and the approach taken. It triggers on its own whenever a commit is being authored, including mid-task when an agent is about to run `git commit`, so you rarely have to ask for it by name.

The skill is autonomous end to end — it drafts, commits, and reports the SHA and message afterwards. It never pauses for approval or asks what to stage; correct anything you dislike with `git commit --amend`.

The format rules live in one shared file, [`references/commit-message-rules.md`](skills/write-commit-message/references/commit-message-rules.md) — maintain them there and every path picks them up. This skill reads it, the repo-root [`commit-message.instructions.md`](../../commit-message.instructions.md) that serves VS Code's Generate Commit Message button forwards to it, and every other skill that commits delegates to this skill.

**Trigger phrases:** "commit this", "git commit", "write a commit message"

---

### `create-gitlab-mr`

> Creates a new feature branch from current git changes, commits it, pushes it, and opens a GitLab Merge Request through `glab`.

Automates the full workflow from local changes to a published GitLab MR: creates a branch, stages and commits changes, pushes, and opens the MR — all in one step. The commit message itself comes from `write-commit-message`.

**Trigger phrases:** "create a gitlab MR", "open a merge request", "push and create MR"

---

### `write-plan`

> Create a technical implementation plan broken into small, executable, sized tasks.

Produces a deterministic, execution-ready implementation plan with atomic tasks, `S`/`M`/`L` size labels, and dependency mapping — no hour estimation. Offers to hand off to `estimate-time` once the plan is saved.

**Trigger phrases:** "create an implementation plan", "break down a ticket", "plan this task"

---

### `estimate-time`

> Add a time estimate in hours to an existing implementation plan.

Reads a saved `write-plan` plan and writes an hour estimate back into it: a per-task risk multiplier from the Design Tree, `S`/`M`/`L` mapped to hours, and the estimation table. For story-point sizing, use `estimate-size` instead.

**Trigger phrases:** "estimate this plan", "how long will this take", "add a time estimate"

---

### `scope-plan` (deprecated)

> [DEPRECATED] Superseded by `write-plan` and `estimate-time`.

Kept for existing references only. Use `write-plan` for the plan and `estimate-time` for the hour estimate.

---

### `estimate-size`

> Estimate software tickets with a complete, configurable relative-sizing workflow.

Provides a complete built-in approach for projects without local estimation rules, while also supporting project-defined scales and exceptions or a one-off custom scale. It uses repository and historical context to calibrate estimates, explains the size drivers, and recommends splitting oversized work. It does not convert points to hours.

**Trigger phrases:** "size this story", "assign story points", "check this estimate", "estimate work item"

When a dedicated project-specific estimation skill applies, that skill takes precedence and this skill should not interfere. When a project has only local rules, this skill applies those rules over its built-in defaults.

**Using your own estimation rules.** Local rules are picked up from project context (contribution guides, team handbooks, estimation docs) or supplied directly in the prompt. Examples:

- Local policy from the repo: `Size NIO-123 using our estimation guidelines in docs/estimation.md`
- Partial override (your scale, built-in workflow): `Assign story points to this ticket — we only use 1, 2, 3, 5 and 8`
- Non-numeric team scale: `Size this story on our T-shirt scale (S/M/L/XL)`
- One-off custom scale, without making it project policy: `Just for this one: rate this ticket 1-10 on implementation risk`

---

### `write-prd`

> Create a PRD and user stories through user interview, codebase exploration, and component design.

Guides you through building a complete Product Requirements Document by interviewing you about the problem, exploring the codebase, sketching major components, and writing the final PRD as a Markdown file.

**Trigger phrases:** "write a PRD", "create a product requirements document", "write user stories", "plan a new feature"

---

### `write-readme`

> Generate a consistent, high-level README for any codebase or repository.

Explores the repository structure and produces a README following a
fixed section order — title, dev setup, overview, project structure,
database, configuration, testing, and CI/CD. Skips sections that don't
apply. One predictable layout across all company projects.

**Trigger phrases:** "write a readme", "generate readme", "create readme",
"project is missing documentation"

---

### `wbso-aanvraag`

> Analyseer een project op WBSO-waardigheid en genereer de technische projectbeschrijving, S&O-uren schatting en Jira-labeladvies.

Leest Jira-epics en -issues via `acli` of Atlassian MCP, scant de applicatiecode en workspace-documenten, genereert hypothesen over technische knelpunten als architect, en schrijft een compleet WBSO-concept weg als Markdown. Inclusief parapluproject-ondersteuning en drie ramingsstrategieën voor S&O-uren.

**Trigger phrases:** "maak een WBSO-aanvraag", "stel een S&O-aanvraag op", "help me met WBSO", "schrijf een WBSO-formulier"

---

## MCP Servers

`aimate` is skills-first and does not bundle MCP servers. Configure only the integrations a project or client needs in that checkout's `.mcp.json` or equivalent host project configuration.

Run the `configure-mcp` skill to inspect existing project configuration, validate installed official CLIs and MCP connections, and configure GitLab or GitHub plus optional Atlassian, Figma, and Sentry integrations. It saves preferred and fallback routes in `AGENTS.md`, safely merges configuration, and uses client-specific MCP names such as `atlassian-acme`.

This avoids prompting every user to connect accounts they do not have and allows different client checkouts to use different GitLab instances or Atlassian sites.

### Per-client pattern

Keep the MCP configuration with the client checkout:

```text
clients/
├── acme/.mcp.json
└── contoso/.mcp.json
```

If two clients share one workspace, give each server a distinct name:

```json
{
  "mcpServers": {
    "atlassian-acme": {
      "type": "http",
      "url": "https://mcp.atlassian.com/v1/mcp/authv2"
    },
    "atlassian-contoso": {
      "type": "http",
      "url": "https://mcp.atlassian.com/v1/mcp/authv2"
    }
  }
}
```

Authenticate each named connection with the matching client site. Never commit real tokens or passwords.

### Manual templates

Copy-paste templates are available in [`skills/configure-mcp/assets/templates`](skills/configure-mcp/assets/templates):

- GitHub Cloud
- Atlassian Cloud
- Figma
- Sentry Cloud and self-hosted Sentry
- combined example project configuration
- `AGENTS.md` tool-routing block
- optional Jira guidance for `AGENTS.md`
- a minimal Claude Code import for `CLAUDE.md`

The capability routing, selected implementations, validation commands, wizard questions, and version policy are documented in [`mcp-catalog.md`](skills/configure-mcp/references/mcp-catalog.md).

### CLI and MCP routing

- Local Git operations always use `git`.
- GitLab repository operations always use the official `glab` CLI.
- GitHub repository operations use the saved `gh` or GitHub MCP route.
- Jira uses the saved `acli` or Atlassian MCP route; Confluence requires Atlassian MCP.
- Figma design context requires Figma MCP.
- Sentry investigations use Sentry MCP; releases, source maps, and debug symbols use `sentry-cli`.

An explicit instruction in the current request overrides the project routing. Skills automatically try its configured fallback and do not ask again while either route works. Claude Code projects can import the same policy from `CLAUDE.md` with `@AGENTS.md`.

### GitLab CLI prerequisite

Install and authenticate the official GitLab CLI before using GitLab skills:

```bash
brew install glab
glab auth login
glab repo list --member
```

For non-Homebrew platforms, use the official [`glab` installation options](https://gitlab.com/gitlab-org/cli/-/blob/HEAD/docs/installation_options.md). The final command is a read-only check that confirms the authenticated account can list its member projects.

## Upgrading to 2.0.0

Version 2.0.0 removes the globally bundled Figma, GitLab, and Atlassian MCP servers. Existing authenticated host connections are not copied automatically.

After upgrading:

1. Remove or disconnect any old plugin-owned Aimate MCP entries if your host retains them.
2. Open each client project and run `configure-mcp`.
3. Select only the integrations that project needs.
4. Reload the MCP host and complete authentication for the new client-specific server names.

See [`RELEASE_NOTES.md`](RELEASE_NOTES.md) for the full migration notes. This change supersedes and closes [#16](https://github.com/Dawn-Technology/aicelerate/issues/16).
