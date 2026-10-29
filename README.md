# aicelerate — AI Acceleration Repository

An agent plugin marketplace by Dawn Technology, containing the `aimate` plugin with reusable skills for support in our Assured Delivery Process.

## Start here

Skills respond to natural phrasing, and can always be invoked by name.

| You have | Start with |
|---|---|
| A ticket | `prepare-ticket` |
| A spec or epic | `split-spec` |
| An idea, nothing written | `write-prd` |
| A tiny change | `implement-ticket` |
| A vague request, no criteria | `prepare-ticket` (it asks the open questions, it won't invent criteria) |
| An open PR or MR | `review-pr` |

A "ticket" here is any work description: a Jira/GitHub/GitLab item by its key, or text you paste into the chat. With tracker routing configured, results are written back to the tracker; without it, you get them in the chat.

## The flow

```
             SPEC                       PLAN                BUILD              REVIEW
 ┌───────────┐   ┌────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
 │   idea    │──►│ spec/epic  │──►│    ticket    │──►│   worktree   │──►│    PR/MR     │
 │   PRD     │   │  tickets   │   │    brief     │   │   verified   │   │   reviewed   │
 └───────────┘   └────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
  write-prd       split-spec      prepare-ticket    implement-ticket     review-pr
                                  write-plan (opt.)                      resolve-pr-feedback
```

The loop itself is two steps: `prepare-ticket` makes the ticket buildable, `implement-ticket` builds it and opens the PR. Everything left of it produces tickets; everything right of it lives on the open PR.

| Step | What it does |
|---|---|
| `write-prd` | an idea becomes a PRD with user stories, epics/stories to Jira if you want |
| `split-spec` | a spec or epic becomes vertical tickets with a demo line each; small work comes back as one ticket |
| `prepare-ticket` | takes a tracker item by key or pasted text, traces every claim against the repository and rewrites it into an agent-ready brief: intent, goal, acceptance criteria, definition of done. Not ready? You get a verdict and the one question to resolve. |
| `write-plan` | optional: turns the brief into sized tasks, to discuss the approach, take into refinement, or estimate from |
| `implement-ticket` | builds the brief in an isolated worktree, runs the repo's own checks, reviews its own work and resolves those findings, then opens the PR or MR and reports every deviation from the ticket |

## On the PR

implement-ticket reviews its own work before the PR opens. These run on the open PR or MR, as often as needed:

- `review-pr` — a second look, findings as inline comments
- `resolve-pr-feedback` — turns review threads (from a colleague or an agent) into pushed fixes and per-thread replies
- `review-and-resolve-pr` — both in one autonomous pass

## Checks, at any point

- `asvs-audit` — OWASP ASVS security audit of the codebase
- `review-architecture` — where the codebase is hardest to change, with a refactoring roadmap
- `test-pr-e2e` — browser-test a PR with Playwright, like a QA engineer would
- `test-pr-guide` — a manual test guide for a PR, for a human tester
- `review-local` — findings on local changes before you commit

wcag-audit (accessibility) is in development.

## Support skills

- `estimate-size` / `estimate-time` — story points during refinement, hours on a plan
- `write-commit-message` — commits in the house style
- `write-readme` — the company-wide README layout
- `configure-mcp` — one-time setup per project: tracker routing, integrations

Internal, not for direct use: `fetch-ticket` (reads a tracker item and returns it provider-neutral) and `code-review` (the shared review core). The skills above invoke them where needed.

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

#### Add Aimate tool routing and Jira configuration

The `configure-mcp` wizard can add these marked blocks automatically. They keep preferred and fallback routes stable without asking each developer on every invocation; an explicit instruction still overrides them.

```markdown
<!-- aimate:tool-routing:start -->
## Aimate tool routing

| Capability | Preferred route | Fallback route |
| --- | --- | --- |
| GitHub repository operations | `gh` | `github-client` MCP |
| GitLab repository operations | `glab` | none |
| Jira operations | `acli` | `atlassian-client` MCP |

- An explicit instruction in the current request overrides this table.
- Use the configured fallback without asking when the preferred route is unavailable.
- Reconcile remote state before changing routes after an ambiguous write.
<!-- aimate:tool-routing:end -->

<!-- aimate:jira:start -->
## Jira

- Jira site: `https://client.atlassian.net`
- Default project key: `CLIENT`
- Confirm the project key before creating, updating, or transitioning issues.
<!-- aimate:jira:end -->
```

### Commit Messages

Commit messages come from the [`write-commit-message`](plugins/aimate/skills/write-commit-message/SKILL.md) skill. It ships with the plugin, so there is nothing to configure per project. The skill triggers on its own whenever a commit is being authored — when you ask ("commit this") and when an agent reaches `git commit` partway through a task. It reads the staged diff, picks up a Jira key from the branch name, drafts an imperative subject with a body explaining the observable problem and the approach taken, and commits.

It runs autonomously: no approval step, no "shall I proceed", no questions about what to stage. It commits and then reports the SHA and the message it wrote. If something needs changing, `git commit --amend` is the fix.

Skills that produce commits, such as `implement-ticket` and `resolve-pr-feedback`, delegate the message to this skill, so the same standard applies whether you commit by hand or through an automated workflow.

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

The full stage-by-stage workflow (tooling per stage, MCP remarks, where specs live) moved to the [aimate plugin README](plugins/aimate/README.md#spec-driven-development-workflow). The short version is the flow above: you rarely need the whole chain.

## Plugin

See the [aimate plugin README](plugins/aimate/README.md) for available skills and usage details.

---

## Testing and evals

The repository carries a tiered test suite for the plugin itself. Free, deterministic checks run in CI on every pull request and block merge: structural validation of manifests, skills and links ([tests/](tests/README.md)) and skill-routing checks over the descriptions ([tests/triggers/](tests/README.md)). Host smoke tests run aimate headlessly on Claude Code and the Copilot CLI, and token-spending behavioral evals grade workflow quality against fixed requirements ([evals/](evals/README.md)). When you change a skill, add its routing prompts in the same pull request; when a behavioral report flags your change, the report names the failed requirement and the one-case command to reproduce it locally.
