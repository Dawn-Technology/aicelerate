# aimate

AI Automation Teamate.

AI Acceleration supporting SDLC — reusable skills for security auditing, GitLab workflow automation, and development planning.

## Compatibility Note

If you have the Superpowers plugin installed, be aware that it can sometimes interfere with skill workflows in this plugin. Superpowers includes generic skills that may trigger unexpectedly and conflict with the more specific workflow instructions used by `aimate`.

If a skill behaves inconsistently, invokes the wrong workflow, or appears to ignore its instructions, first check whether Superpowers was triggered in the workflow. If it was, disable or uninstall the Superpowers plugin and then rerun the skill.

## Skills

### `asvs-audit`

> OWASP ASVS 5.0 Level 1 security audit with deterministic, evidence-based findings.

Conducts systematic security audits against all 70 OWASP ASVS 5.0 Level 1 requirements. Produces structured reports with evidence-backed PASS/FAIL/N/A classifications and severity-rated findings.

**Trigger phrases:** "security audit", "asvs audit", "vulnerability scan", "compliance review", "pentest"

---

### `review-pr`

> Review a GitLab Merge Request or GitHub Pull Request and provide findings, and post structured review comments with issue explanation plus code fixes.

Performs comprehensive code review — identifies bugs, logic errors, security issues, and style violations. Posts structured inline comments with code fix suggestions directly on the MR.

**Trigger phrases:** "review this MR", "review this merge request", "review the gitlab MR"

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

> Creates a new feature branch from current git changes, commits them, pushes to the remote, and opens a GitLab Merge Request using the GitLab MCP server.

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

Leest Jira-epics en -issues via de Atlassian MCP-server, scant de applicatiecode en workspace-documenten, genereert hypothesen over technische knelpunten als architect, en schrijft een compleet WBSO-concept weg als Markdown. Inclusief parapluproject-ondersteuning en drie ramingsstrategieën voor S&O-uren.

**Trigger phrases:** "maak een WBSO-aanvraag", "stel een S&O-aanvraag op", "help me met WBSO", "schrijf een WBSO-formulier"

---

## MCP Servers

This plugin bundles three MCP servers, configured in [.mcp.json](.mcp.json).

### Figma

Connects to the official [Figma MCP server](https://www.figma.com/blog/introducing-figma-ai-mcp/) over HTTP.

- **Transport:** HTTP (`https://mcp.figma.com/mcp`)
- **Auth:** Figma OAuth — handled automatically in Copilot
- **Use cases:** Read design context, inspect components, generate code from Figma designs

No additional configuration required.

---

### GitLab

Uses [`@zereight/mcp-gitlab`](https://github.com/zereight/gitlab-mcp) over stdio with a Personal Access Token.

- **Transport:** stdio (`npx -y @zereight/mcp-gitlab`)
- **Auth:** Personal Access Token — Copilot prompts for it on first use and stores it securely
- **Use cases:** Create and review MRs, post comments, manage branches, fetch diffs

**Setup:** Generate a GitLab PAT at **User Settings → Access Tokens** with the `api` scope. Copilot will prompt you for it when a GitLab skill is first invoked.

### Atlassian

Connects to the official [Atlassian MCP server](https://www.atlassian.com/platform/remote-mcp-server) over HTTP.

- **Transport:** HTTP (`https://mcp.atlassian.com/v1/mcp`)
- **Auth:** Atlassian OAuth — handled automatically in Copilot
- **Use cases:** Read and update Jira issues, search Confluence, manage sprints and worklogs

No additional configuration required.
