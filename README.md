# aicelerate — AI Acceleration Repository

An agent plugin marketplace by Dawn Technology, containing the `aimate` plugin with reusable skills for support in our Assured Delivery Process.

## Install

### Visual Studio Code

#### Via the marketplace (recommended)

1. Open your VS Code `settings.json` and add the marketplace:

   ```json
   "chat.plugins.marketplaces": [
       "Dawn-Technology/aicelerate"
   ]
   ```

2. Open the Extensions view (`⇧⌘X`) and search for `@agentPlugins`.

3. Find `aimate` and select **Install**.

#### Direct install from source

Run **Chat: Install Plugin From Source** from the Command Palette and enter:

```
https://github.com/Dawn-Technology/aicelerate
```

#### Update

Run **Extensions: Check for Extension Updates** from the Command Palette.

### GitHub Copilot CLI

#### Via the marketplace (recommended)

Register the marketplace once, then install by name:

```bash
copilot plugin marketplace add Dawn-Technology/aicelerate
copilot plugin install aimate@aicelerate
```

#### Direct install

```bash
copilot plugin install Dawn-Technology/aicelerate:plugins/aimate
```

#### Update

```bash
copilot plugin update aimate
```

## Requirements

### Visual Studio Code

- GitHub Dawn Technology organization account with Copilot seat enabled

- Visual Studio Code with the [GitHub Copilot](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot-chat) extension installed
  - Agent plugin support enabled (`chat.plugins.enabled: true` in settings)
- [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli) installed and authenticated

## Recommended external skills

The following skills are not part of this repository but are recommended for use alongside `aimate`.

### Grill Me ([mattpocock/skills — grill-me](https://github.com/mattpocock/skills/tree/main/skills/productivity/grill-me))

Interviews you relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree one question at a time. Use when you want to stress-test a plan or get grilled on a design.

```bash
npx skills add https://github.com/mattpocock/skills/tree/main/skills/productivity --skill grill-me
```

### ADR Writing ([vercel/ai — adr-skill](https://skills.sh/vercel/ai/adr-skill))

Helps agents write Architectural Decision Records (ADRs) as executable specifications — structured enough for a coding agent to implement without follow-up questions.

```bash
npx skills add https://github.com/vercel/ai --skill adr-skill
```

### Caveman ([mattpocock/skills — caveman](https://github.com/mattpocock/skills/tree/main/skills/productivity/caveman))

Ultra-compressed communication mode that cuts token usage ~75% by dropping filler, articles, and pleasantries while keeping full technical accuracy. Use when you want terse, token-efficient responses.

```bash
npx skills add https://github.com/mattpocock/skills/tree/main/skills/productivity --skill caveman
```

## Recommended MCP servers

The following MCP servers are not part of this repository but are recommended for use alongside `aimate`.

### Context7 ([upstash/context7](https://github.com/upstash/context7))

Fetches up-to-date, version-specific documentation and code examples directly from the source and places them in your prompt. Prevents hallucinated APIs and outdated code generation. Add `use context7` to any prompt to pull in current library docs on demand.

```bash
npx ctx7 setup
```

Or configure the MCP server manually using `https://mcp.context7.com/mcp` in your MCP client. See [context7.com/docs](https://context7.com/docs) for client-specific setup instructions.

## Project Initialisation

Before starting work in a new project, spend a few minutes setting up two things: an `AGENTS.md` file at the repo root, and optionally a project-specific coder agent. These are one-time tasks that pay off across every subsequent AI interaction.

### AGENTS.md / copilot-instructions.md

Copilot reads project context from two files:

- **`AGENTS.md`** — picked up by the Copilot CLI and the coding agent. Place it at the repo root.
- **`.github/copilot-instructions.md`** — picked up by Copilot in VS Code and on GitHub.com.

**`AGENTS.md` alone is sufficient.** Run the following command to auto-generate it from your codebase, then adjust where needed:

```bash
copilot init
```

For the full reference on placement and format, see the [GitHub Copilot CLI documentation](https://docs.github.com/copilot/how-tos/copilot-cli).

#### Keep it brief — it is always loaded

`AGENTS.md` is injected into every session, so every line costs tokens on every interaction. Only include rules that **always apply** regardless of the task — stack, commands, hard constraints. Keep language direct and skip prose.

For task-specific or context-specific guidance, use skills or agents instead. That way rules are only loaded when relevant.

#### Add a Jira configuration block

Copilot won't infer Jira context from your codebase. Add this block manually so every agent and skill that touches Jira targets the right project and sprint without prompting:

```markdown
## JIRA (<Project> Project)

- Assume "ticket" or "JIRA" refers to the <Project> project.
- Server: `#atlassian/atlassian-mcp-server`. URL: `https://<org>.atlassian.net/browse/<Project>`
- Requirements: Always include clear acceptance criteria and relevant file paths. Add ticket to backlog unless specified different.
- Allowed types: Taak, Story, Bug, Subtaak, Epic.
```

### Commit Message Instructions

The repo ships a [`commit-message.instructions.md`](commit-message.instructions.md) file that defines a strict [Conventional Commits](https://www.conventionalcommits.org/) format with impact analysis and footer metadata. It is used in three ways:

- **VS Code** — Copilot uses it automatically when generating commit messages via the Source Control panel.
- **Copilot CLI agents** — Agents reference it when crafting commits, so the same standard applies whether you commit manually or via an automated skill.
- **Skills and prompts** — Any skill that produces commits (e.g. `create-gitlab-mr`) can reference it explicitly to ensure consistent output.

#### VS Code setup

Add the following to your project's `.vscode/settings.json` (or user `settings.json` to apply globally):

```json
"github.copilot.chat.commitMessageGeneration.instructions": [
    { "file": "commit-message.instructions.md" }
]
```

With this in place, the **Generate Commit Message** button in the Source Control panel will follow the Conventional Commits format defined in the file.

#### Copilot CLI and agents

The file is automatically picked up by the Copilot CLI when it is present at the repo root. No extra configuration is required — agents will apply the commit conventions whenever they stage and commit changes.

### Tone of Voice

The repo ships a [`tone-of-voice.instructions.md`](tone-of-voice.instructions.md) that defines the voice for content Copilot produces on your behalf. It is most valuable when generating output that gets shared externally — documentation, PRDs, ADRs, architectural design specs, and similar artefacts where consistent, professional tone matters. Storing it once means every piece of generated content follows the same standard without repeating yourself.

#### Store it in Copilot memory (recommended)

Copilot memory is user-scoped and persists across all sessions and repositories. Storing your tone preferences there means you never have to repeat them.

Start a session with memory enabled, then ask Copilot to read and remember the file:

```bash
copilot --enable-memory
```

Once in the session, run:

```
Read tone-of-voice.instructions.md and store my tone of voice preferences in your memory.
```

Copilot will extract the preferences and save them as user-scoped memories. They will be active in every future session without any further configuration.

#### VS Code setup

To apply the tone in VS Code, reference the file in your user `settings.json` (not the project settings, so it applies globally):

```json
"github.copilot.chat.codeGeneration.instructions": [
    { "file": "tone-of-voice.instructions.md" }
]
```

---

### Coder Agent (optional)

Because `aimate` intentionally does not bundle a coding agent, each team is expected to configure their own. A custom coder agent combines your project's `AGENTS.md` context, the `aimate` skills, and any project-specific skills into a single, ready-to-invoke agent.

Create a `.github/agents/` directory (or the equivalent for your Copilot client) and define an agent that:

- Include coding specific guidelines and best practices
- Rules for addding automatic testing
- Adhere to coding rules like PHPStan or other tooling
- Instructions for running scripts/quality tools locally

This is where teams add project-specific skills — e.g. a deployment agent, a migration helper, or domain-specific code generators — on top of the shared `aimate` foundation.

---

## Spec-Driven Development Workflow

`aimate` and its recommended external skills are designed to support a **spec-driven development** workflow: start with a well-defined specification, align on architecture, plan the work, then hand it off to a coding agent of your choosing.

The plugin intentionally does **not** include a pre-configured coding agent. Projects vary significantly in language, tooling, and conventions. It is expected that each team brings their own coding agent and project-specific skills on top of this shared foundation.

The stages below describe the recommended workflow and which skills and MCP servers to use at each step.

The three MCP servers bundled with `aimate` (Figma, GitLab, Atlassian) are available throughout the workflow. Skills that depend on an MCP server call it automatically — you do not need to invoke the MCP directly. See the [aimate plugin README](plugins/aimate/README.md#mcp-servers) for setup details. The only manual step required is generating a GitLab Personal Access Token the first time a GitLab skill is used.

---

### Stage 1 — Explore & Challenge

Before writing a line of spec, stress-test the problem statement and approach. Pull in existing Jira context documentation to ground the conversation.

| Tool | Source | Purpose |
|---|---|---|
| `grill-me` | [External](#grill-me-mattpocodeskills--grill-me) | Relentlessly interview yourself on the problem, constraints, and assumptions until shared understanding is reached |
| Atlassian MCP | aimate (bundled) | Read existing Jira tickets for background context before defining scope |

---

### Stage 2 — Specify

Translate the problem into a structured Product Requirements Document with user stories. Reference designs from Figma and link back to the originating Jira issues. And or create JIRA ticket based on the PRD.

| Tool | Source | Purpose |
|---|---|---|
| `write-prd` | aimate | Interview-driven PRD creation with codebase exploration and component sketching |
| Figma MCP | aimate (bundled) | Inspect designs, read component specs, and pull design context directly into the PRD |
| Atlassian MCP | aimate (bundled) | Read linked Jira issues for acceptance criteria and link the finished PRD back to the ticket |

---

### Stage 3 — Decide Architecture

Document key architectural decisions as ADRs — structured enough for a coding agent to implement without follow-up questions.

| Tool | Source | Purpose |
|---|---|---|
| `grill-me` | [External](#grill-me-mattpocodeskills--grill-me) | Stress-test architectural options before committing |
| `adr-writing` | [External](#adr-writing-vercelai--adr-skill) | Write Architectural Decision Records in MADR format |

---

### Stage 4 — Plan

Break down the spec into an atomic, dependency-mapped implementation plan with effort estimates. Sync the outcome back to Jira. And use estimation for planning and sales.

| Tool | Source | Purpose |
|---|---|---|
| `scope-plan` | aimate | Generate execution-ready implementation plan and time estimate |
| Atlassian MCP | aimate (bundled) | Update Jira tickets with estimates and move issues into the sprint |

---

### Stage 5 — Implement

Hand off the result of the scope-plan or spec to your team's coding agent. This stage is intentionally left to each project team — choose the coding agent, model, and project-specific skills that fit your stack.

| Tool | Source | Purpose |
|---|---|---|
| Context7 MCP | [Recommended MCP](#context7-upstashcontext7) | Pull in up-to-date, version-specific library docs to prevent hallucinated APIs |
| Figma MCP | aimate (bundled) | Reference component specs and design tokens when generating UI code |
| GitLab MCP / Github MCP | aimate (bundled) | Create pull requests for changed code |

---

### Stage 6 — Review

Review the resulting code changes for correctness, quality, and security. The GitLab MCP / Github MCP is used automatically by `review-pr` to fetch the diff and post inline review comments.

| Tool | Source | Purpose |
|---|---|---|
| `review-pr` | aimate | Comprehensive MR/PR review with inline comments and code fix suggestions — uses GitLab MCP to post directly on the MR |
| `asvs-audit` | aimate | OWASP ASVS 5.0 Level 1 security audit with evidence-backed findings |
| GitLab MCP / Github | aimate (bundled) | Fetch MR diff, read existing comments, and post structured review comments |

---

### Stage 7 — Test & Ship

Produce a manual test guide and open the merge request. The GitLab MCP handles branch creation, push, and MR opening.

| Tool | Source | Purpose |
|---|---|---|
| `test-pr-guide` | aimate | Step-by-step manual testing guide for a branch or MR |
| `create-gitlab-mr` | aimate | Commit, push, and open a GitLab MR in one step — uses GitLab MCP under the hood |
| GitLab MCP | aimate (bundled) | Create the remote branch, push commits, and open the MR with description and labels |

---

## Plugin

See the [aimate plugin README](plugins/aimate/README.md) for available skills and usage details.
