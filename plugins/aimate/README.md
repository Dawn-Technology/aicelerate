# aimate

AI Automation Teamate.

AI Acceleration supporting SDLC — reusable skills for security auditing, GitLab workflow automation, and development planning.

## Skills

### `asvs-audit`

> OWASP ASVS 5.0 Level 1 security audit with deterministic, evidence-based findings.

Conducts systematic security audits against all 70 OWASP ASVS 5.0 Level 1 requirements. Produces structured reports with evidence-backed PASS/FAIL/N/A classifications and severity-rated findings.

**Trigger phrases:** "security audit", "asvs audit", "vulnerability scan", "compliance review", "pentest"

---

### `gitlab-mr-review`

> Review a GitLab Merge Request and provide findings, and post structured review comments with issue explanation plus code fixes.

Performs comprehensive code review on GitLab MRs — identifies bugs, logic errors, security issues, and style violations. Posts structured inline comments with code fix suggestions directly on the MR.

**Trigger phrases:** "review this MR", "review this merge request", "review the gitlab MR"

---

### `create-gitlab-mr`

> Creates a new feature branch from current git changes, commits them, pushes to the remote, and opens a GitLab Merge Request using the GitLab MCP server.

Automates the full workflow from local changes to a published GitLab MR: creates a branch, stages and commits changes, pushes, and opens the MR — all in one step.

**Trigger phrases:** "create a gitlab MR", "open a merge request", "push and create MR"

---

### `implementation-plan`

> Create technical implementation plan and time estimation.

Produces a deterministic, execution-ready implementation plan with atomic tasks, effort estimates, and dependency mapping. Suitable for sprint planning, ticket estimation, or pre-development alignment.

**Trigger phrases:** "create an implementation plan", "estimate this ticket", "plan this task"

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

---

### Atlassian

Connects to the official [Atlassian MCP server](https://www.atlassian.com/platform/remote-mcp-server) over HTTP.

- **Transport:** HTTP (`https://mcp.atlassian.com/v1/mcp`)
- **Auth:** Atlassian OAuth — handled automatically in Copilot
- **Use cases:** Read and update Jira issues, search Confluence, manage sprints and worklogs

No additional configuration required.
