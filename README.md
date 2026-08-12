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

### Claude Code Compatibility

The marketplace is also compatible with Claude Code. Register it, then install by name:

```bash
claude plugin marketplace add Dawn-Technology/aicelerate
claude plugin install aimate@aicelerate
```

> [!NOTE]
> Compatibility is provided by symlinks (`.claude-plugin/marketplace.json` and `plugins/aimate/.claude-plugin/plugin.json`) that point at the Copilot-canonical manifests. Git stores these as symlinks on macOS and Linux. On Windows they only check out as symlinks when `git config core.symlinks` is `true`; otherwise they become plain text stubs and Claude Code discovery will fail.

## Requirements

### Visual Studio Code

- GitHub Dawn Technology organization account with Copilot seat enabled

- Visual Studio Code with the [GitHub Copilot](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot-chat) extension installed
  - Agent plugin support enabled (`chat.plugins.enabled: true` in settings)
- [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli) installed and authenticated

## Recommended external skills

The following skills are not part of this repository but are recommended for use alongside `aimate`.

### Grilling ([mattpocock/skills — grilling](https://www.skills.sh/mattpocock/skills/grilling))

Interviews you relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree one question at a time. Use when you want to stress-test a plan or get grilled on a design.

```bash
npx skills add https://github.com/mattpocock/skills --skill grilling
```

### ADR Writing ([vercel/ai — adr-skill](https://skills.sh/vercel/ai/adr-skill))

Helps agents write Architectural Decision Records (ADRs) as executable specifications — structured enough for a coding agent to implement without follow-up questions.

```bash
npx skills add https://github.com/vercel/ai --skill adr-skill
```

### Caveman ([JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman))

Ultra-compressed communication mode that cuts token usage ~75% by dropping filler, articles, and pleasantries while keeping full technical accuracy. Use when you want terse, token-efficient responses.

```bash
npx skills add https://github.com/JuliusBrussee/caveman --skill caveman
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

#### Add Aimate tool preferences and Jira configuration

The `configure-mcp` wizard can add these marked blocks automatically. They keep the project route stable without asking each developer on every invocation; an explicit instruction still overrides them.

```markdown
<!-- aimate:tool-preferences:start -->
## Aimate tool preferences

- Repository operations: `auto`
- Jira operations: `auto`
- GitLab operations always use the official `glab` CLI.
- Do not ask for these preferences again while the selected route is available and authenticated.
- An explicit instruction in the current request overrides these project defaults.
<!-- aimate:tool-preferences:end -->

<!-- aimate:jira:start -->
## Jira

- Preferred route: `auto` (`acli` or the `atlassian-client` MCP server).
- Jira site: `https://client.atlassian.net`
- Default project key: `CLIENT`
- Confirm the project key before creating, updating, or transitioning issues.
<!-- aimate:jira:end -->
```

### Commit Messages

Commit messages come from the [`write-commit-message`](plugins/aimate/skills/write-commit-message/SKILL.md) skill. It ships with the plugin, so there is nothing to configure per project. The skill triggers on its own whenever a commit is being authored — when you ask ("commit this") and when an agent reaches `git commit` partway through a task. It reads the staged diff, picks up a Jira key from the branch name, drafts an imperative subject with a body explaining the observable problem and the approach taken, and commits.

It runs autonomously: no approval step, no "shall I proceed", no questions about what to stage. It commits and then reports the SHA and the message it wrote. If something needs changing, `git commit --amend` is the fix.

Skills that produce commits, such as `create-gitlab-mr`, delegate the message to this skill, so the same standard applies whether you commit by hand or through an automated workflow.

#### One shared rules file

The format itself — the seven rules, what belongs in each paragraph, the self-check, the worked examples — lives in a single maintained file: [`commit-message-rules.md`](plugins/aimate/skills/write-commit-message/references/commit-message-rules.md), inside the skill so it ships with the plugin. The skill reads it, and so does anything else that writes a commit message. Change the rules there and every path picks them up; nothing restates them.

#### VS Code's Generate Commit Message button

The button in the Source Control panel reads its instructions from a file and cannot invoke a skill, so it has its own entry point: [`commit-message.instructions.md`](commit-message.instructions.md). That file holds no rules of its own — it forwards to the shared rules, so the button and the skill produce the same message.

Point the setting at both files. The button's generation call has no tools and cannot open a linked file, so the rules have to be in the prompt next to the instructions that reference them:

```json
"github.copilot.chat.commitMessageGeneration.instructions": [
    { "file": "commit-message.instructions.md" },
    { "file": "plugins/aimate/skills/write-commit-message/references/commit-message-rules.md" }
]
```

Copilot chat and agent mode open the linked file themselves and need only the first entry.

In another project, copy both files in and adjust the second path. Committing from chat avoids the copy entirely — `write-commit-message` reads the rules from the installed plugin, so it never goes stale.

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

`aimate` and its recommended external skills are designed to support a **spec-driven development** workflow: start with a well-defined specification, align on architecture, plan the work, then hand it off to a coding agent of your choosing. Throughout this section, "spec" refers loosely to the planning artifacts a change produces — chiefly the PRD (the what and why) and the implementation plan (the how). They share the same home and lifecycle in the repo, but they are distinct documents.

The plugin intentionally does **not** include a pre-configured coding agent. Projects vary significantly in language, tooling, and conventions. It is expected that each team brings their own coding agent and project-specific skills on top of this shared foundation.

The stages below describe the recommended workflow and which skills and MCP servers to use at each step. Where specs live and what happens to them after a change ships is covered in [Where specs live](#where-specs-live) at the end of this section. In short: the spec is a file in the repo and the tracker links to it, never the other way round.

`aimate` does not bundle MCP connections. Run `configure-mcp` per client checkout to validate existing `gh`, `glab`, or `acli` authentication, add only the MCP connections the project needs, and save the project route preference. Skills reuse that preference without asking every time. See the [aimate plugin README](plugins/aimate/README.md#mcp-servers) for routing, the per-client pattern, and migration guidance.

> [!NOTE]
> [Spec-Driven Development](https://specdriven.ai/) is a methodology not yet solidified. See [Understanding Spec-Driven Development](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)
> We are learning and experiecing pratical implementation. For now aimate and following documenation assumes at least the first maturity level which is a spec-first development flow.

---

### Stage 1 — Explore & Challenge

Before writing a line of spec, stress-test the problem statement and approach. Pull in existing Jira context documentation to ground the conversation.

| Tool | Source | Purpose |
| --- | --- | --- |
| `grilling` | [External](#grilling-mattpocockskills--grilling) | Relentlessly interview yourself on the problem, constraints, and assumptions until shared understanding is reached |
| `estimate-size` | aimate | Size a backlog item in story points during refinement (points, not hours) |
| Atlassian MCP | aimate (bundled) | Read existing Jira tickets for background context before defining scope |
| Jira via `acli` or Atlassian MCP | Project-configured via `configure-mcp` | Read existing Jira tickets for background context before defining scope |

---

### Stage 2 — Specify

Translate the problem into a structured Product Requirements Document with user stories. Commit the PRD to the repo under `docs/specs/` and link the Jira ticket to that file — do not paste the PRD into the ticket. Reference designs from Figma and link back to the originating Jira issues. Optionally create a Jira ticket based on the PRD.

| Tool | Source | Purpose |
| --- | --- | --- |
| `write-prd` | aimate | Interview-driven PRD creation with codebase exploration and component sketching |
| Figma MCP | Project-configured via `configure-mcp` | Inspect designs, read component specs, and pull design context directly into the PRD |
| Jira via `acli` or Atlassian MCP | Project-configured via `configure-mcp` | Read linked Jira issues for acceptance criteria, and link the ticket to the committed PRD file |

---

### Stage 3 — Decide Architecture

Document key architectural decisions as ADRs — structured enough for a coding agent to implement without follow-up questions. Store ADRs in the repo alongside the spec; unlike PRDs and plans, ADRs are durable architectural records and are not retired.

| Tool | Source | Purpose |
| --- | --- | --- |
| `grilling` | [External](#grilling-mattpocockskills--grilling) | Stress-test architectural options before committing |
| `adr-writing` | [External](#adr-writing-vercelai--adr-skill) | Write Architectural Decision Records in MADR format |

---

### Stage 4 — Plan

Break down the spec into an atomic, dependency-mapped implementation plan with effort estimates. Commit the plan alongside the PRD in the repo, and sync the time estimate and status back to Jira. Use the estimate for planning and sales.

| Tool | Source | Purpose |
| --- | --- | --- |
| `write-plan` | aimate | Generate an execution-ready implementation plan with sized tasks |
| `estimate-time` | aimate | Add an hour estimate to the plan when a time forecast is needed |
| Atlassian MCP | aimate (bundled) | Update Jira tickets with estimates and move issues into the sprint |
| Jira via `acli` or Atlassian MCP | Project-configured via `configure-mcp` | Update Jira tickets with estimates and move issues into the sprint |

---

### Stage 5 — Implement

Hand off the result of write-plan (and estimate-time, if a time forecast is needed) or the spec to your team's coding agent. This stage is intentionally left to each project team — choose the coding agent, model, and project-specific skills that fit your stack.

| Tool | Source | Purpose |
| --- | --- | --- |
| Context7 MCP | [Recommended MCP](#context7-upstashcontext7) | Pull in up-to-date, version-specific library docs to prevent hallucinated APIs |
| Figma MCP | Project-configured via `configure-mcp` | Reference component specs and design tokens when generating UI code |
| `glab`, `gh`, or GitHub MCP | Project-configured via `configure-mcp` | Create pull requests for changed code; GitLab always uses `glab` |

---

### Stage 6 — Review

Review the resulting code changes for correctness, quality, and security. `review-pr` uses `glab` for GitLab and the saved `gh` or GitHub MCP route for GitHub.

| Tool | Source | Purpose |
| --- | --- | --- |
| `review-pr` | aimate | Comprehensive MR/PR review with inline comments and code fix suggestions through the saved provider route |
| `asvs-audit` | aimate | OWASP ASVS 5.0 Level 1 security audit with evidence-backed findings |
| `glab`, `gh`, or GitHub MCP | Project-configured via `configure-mcp` | Fetch the diff, read existing comments, and post structured review comments |

---

### Stage 7 — Test & Ship

Produce a manual test guide and open the merge request. Local Git handles branch creation and push; the official `glab` CLI opens the MR.

| Tool | Source | Purpose |
| --- | --- | --- |
| `test-pr-guide` | aimate | Step-by-step manual testing guide for a branch or MR |
| `write-commit-message` | aimate | Draft the commit message from the staged diff — triggers automatically on every commit |
| `create-gitlab-mr` | aimate | Commit, push, and open a GitLab MR in one step through `glab` |
| `glab` | Installed and authenticated locally | Open the MR with description and labels after local Git pushes the branch |

---

### Where specs live

The workflow above produces specs. This part covers where they are stored and what happens to them once a change ships. The rule that makes the whole thing work: **the spec is a file in the repo, and the tracker links to it — never the other way round.**

We work across Jira, GitLab issues, and GitHub depending on the client. The repo is the only thing every project has in common, so the repo is where the spec belongs. That keeps the rule the same everywhere and puts the spec next to the code it describes.

**In the repo:** the PRD and the plan, as markdown, under `docs/specs/<ticket-id>-<slug>.md` (or split into `.prd.md` and `.plan.md` when large). The ticket ID in the filename keeps the spec and the ticket traceable in both directions. They change in the same pull request as the code they drive, so a reviewer sees intent and implementation together.

**In the tracker:** status, assignee, sprint, estimate, and discussion, plus one link to the spec file pinned to a commit. Link rather than paste the requirements in, so nobody ends up reading a stale copy instead of the real spec.

#### A spec is not documentation, so the folder does not bloat

The common worry is that `docs/specs/` becomes a swamp of stale files. That happens when specs are treated as permanent documentation. They are not. A spec describes one change and stops being edited once that change ships. Documentation describes the system as it is now and lives forever. Keep the two apart, retire finished specs out of the active folder, and the working area stays lean.

- **One spec, one change.** A spec covers a single ticket. Once it merges you stop editing it; the next change gets its own file. Every spec has a natural end.
- **Keep the PRD small; keep the plan granular.** A PRD over roughly two pages is usually two tickets — if `write-prd` produces something sprawling, split the work rather than writing a monster. Plans are different: an atomic, dependency-mapped plan is legitimately long, so judge it by whether the tasks are small and the scope is still one ticket, not by page count. If a single spec covers so much that its plan balloons, that is a sign to split the ticket, not to trim the plan.
- **Retire when the ticket is closed.** While the ticket is open the spec stays in `docs/specs/`, because a feature is often hardened or hotfixed after merge and the spec is still the live reference then. When the ticket is closed, move the spec to `docs/specs/done/` in a small cleanup PR. The active folder stays lean and the spec is kept, not thrown away.
- **Do not curate `done/`.** It is a growing pile on purpose and nobody maintains it. It sits out of the active folder, so it does not clutter daily work, and it has a defined future use (see below).
- **ADRs are not retired.** ADRs live in the repo like specs, but they stay put when the ticket closes. An architectural decision stays true after the change ships, so it is a durable record, not a disposable spec.
- **Do not duplicate real docs.** If a fact is true beyond this one change, it belongs in a README or an architecture doc, and the spec links to it. Duplication is what "bloat" usually means.

#### Why we keep retired specs

While the change is being built, the spec is the truth about what we are building — what `write-plan` plans against and `estimate-time` estimates against, what `review-pr` checks, and what a second dev reads to understand what "done" means. That job ends when the ticket closes.

Once the code merges, the truth about what the system *does* moves to the code itself, because the code is the running, tested answer. So we take the spec out of the active folder; as a live document it would start to mislead the moment the next change touches that area. But the spec still holds one thing the code never will: the *why*, including the alternatives that were rejected. That record has value beyond the change, which is why we keep it in `done/` rather than delete it.

The real reason to preserve it is the delivery factory on our roadmap. An autonomous or semi-assisted delivery system needs intent and constraints at retrieval time, cheaply, without reconstructing them from a diff. A spec is the highest-quality "why" we ever capture about a change, written when it is true and tied to a commit, which makes the `done/` pile the natural corpus to seed the factory's memory layer later. Deleting specs today would destroy that corpus, and intent thrown away cannot be recovered. Git history technically keeps deleted files, but not as something you can point an ingestion job at; a `done/` folder is an enumerable dataset sitting ready.

Nothing here asks you to do factory work today. Keep writing and retiring specs as described. Once a repo is onboarded into the factory, retiring will mean ingest into the memory layer and then remove from `done/`, and this section will be updated to say so.

#### Quick checks before you merge

- Is there a spec file for this work in `docs/specs/`?
- Does the ticket link to it, rather than repeat it?
- Does the spec describe what the diff actually does?
- Is the PRD focused on this one change, not a permanent doc in disguise, and is the scope still a single ticket?

---

## Plugin

See the [aimate plugin README](plugins/aimate/README.md) for available skills and usage details.
