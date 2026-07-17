# aimate

AI Automation Teamate.

AI Acceleration supporting SDLC — reusable skills for security auditing, GitLab workflow automation, and development planning.

## Compatibility Note

If you have the Superpowers plugin installed, be aware that it can sometimes interfere with skill workflows in this plugin. Superpowers includes generic skills that may trigger unexpectedly and conflict with the more specific workflow instructions used by `aimate`.

If a skill behaves inconsistently, invokes the wrong workflow, or appears to ignore its instructions, first check whether Superpowers was triggered in the workflow. If it was, disable or uninstall the Superpowers plugin and then rerun the skill.

## Acceptance Criteria Contract

`aimate` specs carry acceptance criteria in a single machine-readable format. Every PRD ends with an `## Acceptance Criteria` block where each criterion has a stable id (`AC-1`, `AC-2`, …) and states a condition and an expected outcome in Given/When/Then — structured data rather than prose buried in a user story.

The id is the join key. `write-prd` writes the block, `spec-to-tests` turns each criterion into a test stub tagged with its id, and `review-pr` reports per id whether the change and its tests satisfy the criterion. The loop from spec to executable check holds because all three skills read and write one format, defined once in [`shared/acceptance-criteria.md`](shared/acceptance-criteria.md). An automated delivery pipeline reads the same block to get an objective definition of done.

## Skills

### `asvs-audit`

> OWASP ASVS 5.0 Level 1 security audit with deterministic, evidence-based findings.

Conducts systematic security audits against all 70 OWASP ASVS 5.0 Level 1 requirements. Produces structured reports with evidence-backed PASS/FAIL/N/A classifications and severity-rated findings.

**Trigger phrases:** "security audit", "asvs audit", "vulnerability scan", "compliance review", "pentest"

---

### `review-pr`

> Review a GitLab Merge Request or GitHub Pull Request and provide findings, and post structured review comments with issue explanation plus code fixes.

Performs comprehensive code review — identifies bugs, logic errors, security issues, and style violations. Posts structured inline comments with code fix suggestions directly on the MR. Also runs an acceptance-criteria verification pass: it locates the linked spec and reports, per `AC-<n>`, whether the diff and its tests satisfy each criterion.

**Trigger phrases:** "review this MR", "review this merge request", "review the gitlab MR"

---

### `test-pr-guide`

> Produce a step-by-step manual testing guide for a branch or PR.

Analyzes the diff, identifies what changed, and writes a guide a real person can follow to verify the feature or fix works — including setup requirements, test scenarios, and expected outcomes. Supports GitLab MR URLs and local branches.

**Trigger phrases:** "how do I test this PR", "create a test plan", "write a QA checklist", "how do I test this MR"

---

### `create-gitlab-mr`

> Creates a new feature branch from current git changes, commits them, pushes to the remote, and opens a GitLab Merge Request using the GitLab MCP server.

Automates the full workflow from local changes to a published GitLab MR: creates a branch, stages and commits changes, pushes, and opens the MR — all in one step.

**Trigger phrases:** "create a gitlab MR", "open a merge request", "push and create MR"

---

### `scope-plan`

> Create technical implementation plan and time estimate.

Produces a deterministic, execution-ready implementation plan with atomic tasks, effort estimates, and dependency mapping. Suitable for sprint planning, ticket estimation, or pre-development alignment.

**Trigger phrases:** "create an implementation plan", "estimate this ticket", "plan this task"

---

### `write-prd`

> Create a PRD and user stories through user interview, codebase exploration, and component design.

Guides you through building a complete Product Requirements Document by interviewing you about the problem, exploring the codebase, sketching major components, and writing the final PRD as a Markdown file. Every PRD ends with a machine-readable `## Acceptance Criteria` block (stable `AC-<n>` ids) in the shared canonical format, derived from the interview and confirmed with you.

**Trigger phrases:** "write a PRD", "create a product requirements document", "write user stories", "plan a new feature"

---

### `spec-to-tests`

> Turn the acceptance-criteria block of a PRD into failing test stubs in the repository's own test framework.

Reads the `## Acceptance Criteria` block from a spec, detects the project's test framework (PHPUnit, Jest/Vitest, pytest, Go `testing`, and similar), and scaffolds one or more stubs per criterion. Each stub is tagged with its criterion id and encodes Given/When/Then as arrange/act/assert with a failing or pending assertion — a starting point to fill in, never a fabricated passing test.

**Trigger phrases:** "generate tests from spec", "spec to tests", "scaffold tests from the prd"

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
