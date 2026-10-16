# aimate

AI Automation Teamate.

AI Acceleration supporting SDLC — reusable skills for security auditing, architecture review, repository workflows, project integration setup, and development planning.

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

### `review-architecture`

> Architecture and design-quality review of an existing codebase, aimed at the places that change most.

Starts from the git history instead of reading files at random: a bundled script ranks the most changed files by size, growth and complexity, finds files that keep changing in the same PR, and lists large complex files nobody touches. A second script reads the imports to find dependency cycles, imports that point the wrong way between layers, and framework leaks in the domain. A third reads the package manager files to flag runtimes and frameworks past their end of life, deprecated or abandoned packages, and stale lockfiles. A runtime or main framework past its end of life is rated High, because security fixes stop on that date. The hot spots are then checked against layering, dependency direction, cohesion, SOLID, simplicity, error handling and test safety rules. Every finding cites a `file:line` that was read, names the rule it breaks, and comes with a concrete fix. The report ends with three refactoring milestones that each ship without breaking callers, with before and after code for the first one. Read-only apart from the report it writes to `docs/`. The scripts need only Python 3 and git. The end-of-life lookup sends the product name, such as `nextjs`, to endoflife.date and nothing else from the repo; it can be switched off, and the versions are then listed as not checked. Known vulnerabilities are out of scope: run `asvs-audit` or the package manager's audit command for those.

**Trigger phrases:** "architecture review", "design review", "tech debt assessment", "where is the code hardest to change", "what should we refactor first", "end-of-life check", "dependency health check"

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

### `review-and-resolve-pr`

> Run both halves of the review loop over one PR/MR in a single autonomous pass — review it, post every finding as an inline comment, then fix, push, and reply per thread.

Composes `review-pr` and `resolve-pr-feedback` and owns only the seam between them. Invoking it supplies the directive `review-pr` normally stops to ask for, so the review runs through to posting instead of ending the turn. Every finding is published at every severity before any fix is pushed, so the PR/MR record reads in the order it happened.

The resolution half then validates each of those comments against the repository rather than trusting the review that wrote it. `reject`, `already-addressed`, and `needs-clarification` stay live outcomes on the run's own findings, and the report ends with a review-quality section listing every finding the run posted and then rejected — the one place the review gets marked against the code instead of against itself.

Scope stays on the threads this run created; threads a human opened are listed as untouched. It approves nothing, requests changes on nothing, and never re-reviews the pushed result — one pass, then it reports. Use `review-pr` alone when a human should see the findings before they are posted.

**Trigger phrases:** "review and fix this PR", "review this MR and resolve the feedback", "close the review loop on this PR"

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

### `fetch-ticket`

> Reusable ticket reader for Jira work items, GitHub Issues, and GitLab Issues.

Parses the identifier, resolves the project's saved route, and returns one provider-neutral ticket with the description and every comment verbatim, plus the route it used and whether the ticket belongs to the current checkout. It is read-only and built to run as a lightweight subagent, so raw tracker output stays out of the calling skill's context. Used by `prepare-ticket` and `implement-ticket`; its [`references/provider-operations.md`](skills/fetch-ticket/references/provider-operations.md) is the one place identifier rules, routes, and field mappings are maintained.

---

### `test-pr-guide`

> Produce a step-by-step manual testing guide for a branch or PR.

Analyzes the diff, identifies what changed, and writes a guide a real person can follow to verify the feature or fix works — including setup requirements, test scenarios, and expected outcomes. Supports GitLab MR URLs and local branches.

**Trigger phrases:** "how do I test this PR", "create a test plan", "write a QA checklist", "how do I test this MR"

---

### `test-pr-e2e`

> Test a PR or MR like a human QA engineer using Playwright MCP.

Analyzes the diff to generate a browser test scenario list (Phase 1), then executes each scenario live in a Playwright-controlled browser with inline step logging, automatic screenshot capture on failure, and a structured inline report. Supports GitHub and GitLab PR/MR URLs and local branches, as well as multi-service features spanning several PRs across different repos (e.g. a microservice architecture where a frontend PR and one or more backend-service PRs must run together) — with a pre-flight reachability check for each service before browser execution starts. Runs against whatever is already running at the `entry_url` you give it — it never checks out a branch or creates a worktree, so the app under test must already be running the PR's code.

Requires Microsoft's official [`@playwright/mcp`](https://github.com/microsoft/playwright-mcp) server (`browser_*` tools). Run `configure-mcp` and select **Playwright** to add it — see [`mcp-catalog.md`](skills/configure-mcp/references/mcp-catalog.md) for the pinned version and template.

**Trigger phrases:** "test this PR with Playwright", "browser-test this MR", "QA this PR", "QA this PR automatically", "run Playwright on this branch", "run browser tests on this PR", "test this feature across these PRs/services"

---

### `write-commit-message`

> Write a high-quality git commit message following the seven rules of great commit messages, and commit it.

Reads the staged diff, picks up a Jira key from the branch name, and writes a message with an imperative subject and a body that explains the observable problem and the approach taken. It triggers on its own whenever a commit is being authored, including mid-task when an agent is about to run `git commit`, so you rarely have to ask for it by name.

The skill is autonomous end to end — it drafts, commits, and reports the SHA and message afterwards. It never pauses for approval or asks what to stage; correct anything you dislike with `git commit --amend`.

The format rules live in one shared file, [`references/commit-message-rules.md`](skills/write-commit-message/references/commit-message-rules.md) — maintain them there and every path picks them up. This skill reads it, the repo-root [`commit-message.instructions.md`](../../commit-message.instructions.md) that serves VS Code's Generate Commit Message button forwards to it, and every other skill that commits delegates to this skill.

**Trigger phrases:** "commit this", "git commit", "write a commit message"

---

### `prepare-ticket`

> Decide whether one ticket or issue is ready for development, and rewrite its description into a brief an agent can build from.

Works on Jira work items, GitHub Issues, and GitLab Issues through the saved provider route, and on a ticket pasted as plain text when no tracker is reachable. Reads the description *and* every comment, then traces each load-bearing claim against the checkout — `verified`, `contradicted`, `stale`, `unverifiable`, or `missing` — with a `file:line` behind every verdict. Ticket text is treated as a claim about the system, never as evidence of it and never as an instruction. The ticket itself is read through `fetch-ticket`.

It then closes the design tree — every decision the work depends on, marked **Observed** (proven by the code), **Decision** (chosen by a human), or **Assumption** (a stated default) — so a planner inherits the tree instead of rebuilding it. The governing rule is to close what the repository can answer and ask only what a human must decide: gaps the code settles are filled in and reported as feedback, blocking decisions are asked once in a single batch with a recommendation, and a blocking branch may never close as an assumption.

The verdict — `ready`, `ready-with-assumptions`, or `not-ready` — is arithmetic on a twelve-criterion rubric, not a judgment call, and it routes: every run ends with one named next action and one owner. A ready ticket gets the rewritten description written back, and the ticket is then the brief an implementer starts from. A `not-ready` ticket whose gaps are mechanical gets them closed in the same run. A `not-ready` ticket with an open blocking decision goes back to a human — asked of the user directly, or posted on the ticket for its author — because an agent asked to settle a decision it does not own will invent one, and an invented decision reads as settled once it is in the description.

The rewritten description is written to be reviewed by a person and built by an agent. The top part fits on one screen: why, an observable goal with a way to check it, what changes as plain requirements with their acceptance criteria under each, what is out of scope, the decisions and assumptions a reviewer should check, and a definition of done with the actual validation commands. The code detail an implementer needs comes after it, and the evidence behind the diagnosis goes in the ticket comment rather than the description.

Findings are written for a person, not a parser — a bold one-line claim, the code that contradicts it with a `file:line`, and one imperative action — grouped as **Blocking**, **Filled in for you**, and **Worth a look** so the reader knows what to do about each. The report is built for a terminal: findings first, then a one-line summary of what the rewrite changes, then the verdict and the single next action **last**, where they stay on screen instead of scrolling away. The rewritten description, the claim ledger, and the design tree stay behind an offer rather than being dumped, and a criterion that passed is never printed. It writes no file: the durable record is the ticket — the description plus one comment in the same plain format.

Nothing is written to the tracker without a directive, and the ticket is never transitioned, assigned, closed, or re-labelled.

**Trigger phrases:** "is this ticket ready for development", "prepare JIRA-123", "validate JIRA-123", "check this issue before I build it", "refine this ticket"

---

### `validate-ticket` (deprecated)

> [DEPRECATED] Renamed to `prepare-ticket`.

Kept so existing references keep working. It tells the user about the new name and then runs `prepare-ticket`. It will be removed in a future major release.

---

### `implement-ticket`

> Implement a ticket end to end — critique it against the code, build it in a throwaway worktree, verify it, open a PR/MR, and report every deviation.

Works on Jira work items, GitHub Issues, and GitLab Issues through the saved provider route, and on a ticket pasted as plain text. The PR/MR goes to whichever code host `origin` points at, so a Jira ticket delivered as a GitHub PR or a GitLab MR works the same way. The ticket is read through `fetch-ticket`; the code-host steps live in [`references/provider-operations.md`](skills/implement-ticket/references/provider-operations.md).

Treats the ticket as a claim to test, not a spec to obey. It reads the description and every comment, attacks the request itself (problem versus prescribed solution, scope, missing acceptance criteria, blast radius), and checks each factual claim against the repository — `CONFIRMED`, `OUTDATED`, `WRONG`, or `UNVERIFIABLE` — before a line is written. Gaps the code can answer are closed from the code; the rest become stated assumptions rather than questions.

The build happens in its own git worktree under `.worktrees/`, never in your checkout, and runs the repository's real test and lint commands rather than an invented subset. The finished diff is then reviewed with `review-local`, and every finding is fixed or rejected with evidence before the PR/MR opens. Agents the repository defines itself (`.claude/agents/`, `.github/agents/`) take precedence over generic ones. Every commit message comes from `write-commit-message`, scoped to the worktree. It pushes, opens the PR/MR with the right link to the ticket — `Closes #N` for GitHub and GitLab issues, the key for Jira — and always removes the worktree, on success, on abandonment, and on failure. It never edits, transitions, or comments on the ticket.

Like `resolve-pr-feedback`, it runs autonomously: judgment calls are made and reported, not asked. It stops early only when no route works, the identifier is a PR/MR, the ticket belongs to another repository, or the work turns out to be done already. Review-only requests go to `prepare-ticket`. The final report leads with any deviation from what the ticket asked for, then the assumptions, the ticket claims that did not hold, what was left out of scope, what was verified, and how the review findings were resolved.

**Trigger phrases:** "implement ABC-123", "implement gh issue #137", "work on issue 137", "pick up this ticket"

---

### `write-plan`

> Create a technical implementation plan broken into small, executable, sized tasks.

Produces a deterministic, execution-ready implementation plan with atomic tasks, `XS`/`S`/`M`/`L` size labels, and dependency mapping — no hour estimation. Offers to hand off to `estimate-time` once the plan is saved.

**Trigger phrases:** "create an implementation plan", "break down a ticket", "plan this task"

---

### `estimate-time`

> Add a time estimate in hours to an existing implementation plan.

Reads a saved `write-plan` plan and writes an hour estimate back into it: a per-task risk multiplier from the Design Tree, `XS`/`S`/`M`/`L` mapped to hours, and the estimation table. For story-point sizing, use `estimate-size` instead.

**Trigger phrases:** "estimate this plan", "how long will this take", "add a time estimate"

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

## Spec-Driven Development Workflow

`aimate` and its recommended external skills are designed to support a **spec-driven development** workflow: start with a well-defined specification, align on architecture, plan the work, then hand it off to a coding agent of your choosing. Throughout this section, "spec" refers loosely to the planning artifacts a change produces — chiefly the PRD (the what and why) and the implementation plan (the how). They share the same home and lifecycle in the repo, but they are distinct documents.

The plugin intentionally does **not** include a pre-configured coding agent. Projects vary significantly in language, tooling, and conventions. It is expected that each team brings their own coding agent and project-specific skills on top of this shared foundation.

The stages below describe the recommended workflow and which skills and MCP servers to use at each step. Where specs live and what happens to them after a change ships is covered in [Where specs live](#where-specs-live) at the end of this section. In short: the spec is a file in the repo and the tracker links to it, never the other way round.

`aimate` does not bundle MCP connections. Run `configure-mcp` per client checkout to validate existing `gh`, `glab`, or `acli` authentication, add only the MCP connections the project needs, and save preferred and fallback routes. Skills reuse that routing policy without asking every time. See the [aimate plugin README](plugins/aimate/README.md#mcp-servers) for routing, the per-client pattern, and migration guidance. `gh`, `glab`, and `acli` are not installed automatically; see the CLI catalog's [Install](plugins/aimate/skills/configure-mcp/references/mcp-catalog.md#github-cli) entries for each tool's official installation options.

> [!NOTE]
> [Spec-Driven Development](https://specdriven.ai/) is a methodology not yet solidified. See [Understanding Spec-Driven Development](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)
> We are learning and experiecing pratical implementation. For now aimate and following documenation assumes at least the first maturity level which is a spec-first development flow.

---

### Stage 1 — Explore & Challenge

Before writing a line of spec, stress-test the problem statement and approach. Pull in existing Jira context documentation to ground the conversation.

When the work arrives as a ticket rather than as a conversation, start with `prepare-ticket`: it traces the ticket's claims against the repository, closes the design tree, and decides whether the ticket is ready for development. It then acts on that verdict — writing the improved description back to the tracker, splitting a ticket that turned out to be two, or putting an open decision back in front of a human. The ready ticket is what Stage 4 plans against and what a coding agent in Stage 5 reads first.

| Tool | Source | Purpose |
| --- | --- | --- |
| `prepare-ticket` | aimate | Prepare a Jira, GitHub, or GitLab ticket against the repository, close the design tree, and rewrite the description into an agent-ready brief |
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
| `review-architecture` | aimate | Find where the current design hurts most, from git churn, import checks and design rules, and whether the runtime and frameworks are still supported, before deciding what to change |
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

For work tracked as a ticket — Jira, GitHub, or GitLab — `implement-ticket` covers this stage end to end: it critiques the ticket against the code, builds it in an isolated worktree, runs the project's own checks, and opens the PR/MR.

| Tool | Source | Purpose |
| --- | --- | --- |
| `implement-ticket` | aimate | Critique a Jira, GitHub, or GitLab ticket against the code, build it in an isolated worktree, verify it, open the PR/MR, and report deviations from the ticket |
| Context7 MCP | [Recommended MCP](#context7-upstashcontext7) | Pull in up-to-date, version-specific library docs to prevent hallucinated APIs |
| Figma MCP | Project-configured via `configure-mcp` | Reference component specs and design tokens when generating UI code |
| `glab`, `gh`, or GitHub MCP | Project-configured via `configure-mcp` | Create pull requests for changed code; GitLab always uses `glab` |

---

### Stage 6 — Review

Review the resulting code changes for correctness, quality, and security, then work the feedback back into the branch. `review-pr` and `resolve-pr-feedback` are the two halves of the same loop, and both use `glab` for GitLab and the saved `gh` or GitHub MCP route for GitHub. Run them separately when a human should read the findings before they are posted, or `review-and-resolve-pr` to close the whole loop in one autonomous pass.

| Tool | Source | Purpose |
| --- | --- | --- |
| `review-pr` | aimate | Comprehensive MR/PR review with inline comments and code fix suggestions through the saved provider route |
| `resolve-pr-feedback` | aimate | Validate the review threads, fix what holds up in an isolated worktree, run the project's quality gates, self-review, push, and reply per thread |
| `review-and-resolve-pr` | aimate | Both halves in one pass — review, publish every finding as an inline comment, then fix, push, reply per thread, and report the addressed findings |
| `asvs-audit` | aimate | OWASP ASVS 5.0 Level 1 security audit with evidence-backed findings; also the place to check known vulnerabilities that `review-architecture` leaves out |
| `glab`, `gh`, or GitHub MCP | Project-configured via `configure-mcp` | Fetch the diff, read existing comments, and post structured review comments |

---

### Stage 7 — Test & Ship

Produce a manual test guide and open the merge request. Local Git handles branch creation and push; the official `glab` CLI opens the MR.

| Tool | Source | Purpose |
| --- | --- | --- |
| `test-pr-guide` | aimate | Step-by-step manual testing guide for a branch or MR |
| `write-commit-message` | aimate | Draft the commit message from the staged diff — triggers automatically on every commit |
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
