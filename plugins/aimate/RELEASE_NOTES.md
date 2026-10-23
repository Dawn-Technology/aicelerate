# Release notes

## 4.3.0

Added `write-test-scenarios` (1.0.0), which derives **manual** test scenarios from a Jira work item, GitHub Issue, or GitLab Issue, mapped per acceptance criterion — happy path, edge, negative, and regression — instead of from a diff. `test-pr-guide` verifies what was built; this verifies what was asked, so a criterion implemented wrongly has something to fail against. It needs no branch or code, so it fits test design at refinement or in parallel with implementation.

The skill wraps `fetch-ticket` and makes exactly one write of its own: a comment on the ticket, posted only after explicit confirmation. With a repository open and matching the ticket, it gathers light read-only context and saves to `docs/specs/<ticket-id>-<slug>.test.md`, then offers a link comment, pinned to the commit once the file is committed and pushed. Without one — including the common case of a Jira ticket, which carries no repository binding — it derives scenarios from the ticket alone, marks code-dependent assumptions as unverified, saves to a user-chosen local path, and offers the full scenarios as a comment instead. Acceptance criteria that are missing, ambiguous, or untestable are flagged rather than invented around.

`test-pr-guide` gains an explicit trigger boundary: it and `write-test-scenarios` both produce the same scenario taxonomy, but from a diff/branch/PR/MR versus a ticket respectively, and a bare "test plan" request with neither in context now prompts a disambiguating question instead of guessing.

## 4.2.0 (2026-10-20)

Code reviews are easier for an agent to follow, report every supported finding, and keep unverified concerns visible without turning them into findings. The review rules themselves are unchanged; each one is now stated once, in one place.

- **`code-review` (2.1.0)** is restructured so a normal review no longer reads past the large-review rules. The finding standard, severities, and residual gaps are each defined once, and chunk and integration passes are described as changes to the normal steps. The `report` field always uses the chat format, chunk groups have a defined order, and the eval guide moved to [evals/README.md](skills/code-review/evals/README.md).
- **`code-review` (2.1.0)** reports every distinct finding with no cap per category, and lets maintainability, style, and documentation findings require changes when their consequences justify it. An unverified security concern is a residual gap, never an `optional` finding, and residual gaps always appear in the report. Comment bodies carry no separate severity label.
- **`code-review` (2.1.0)** returns a new `clarification_question` when a review cannot start without more input. **`review-pr` (5.5.0)** and **`review-local` (1.3.0)** ask the user that question and run the review again; **`resolve-pr-feedback` (1.3.0)** fills the gap from the worktree or keeps the push blocked.
- A failed chunk no longer lets the successful chunks be integrated or published. **`review-pr` (5.5.0)** requires a complete review before any publication, approval, or request-changes action, and posts residual gaps in a labelled review summary rather than as inline findings.
- The [review scenarios](skills/code-review/evals/scenarios.json) grew to 14, adding uncapped maintainability findings, security uncertainty alongside a real defect, a failed chunk, and the clarification response.

### Migration from 4.1

- `confirm_scope` is now true whenever a change exceeds 5,000 counted lines. Custom callers decide whether full scope is already authorized before asking, as the [chunked review protocol](skills/code-review/SKILL.md#chunked-review-protocol) describes.
- Custom callers should handle `clarification_question`: ask the user, then invoke the review again with the answer.

## 4.1.0 (2026-10-20)

`prepare-ticket` (3.0.0) now aims to turn a ticket into an intent-driven specification: why the change matters, the intended outcome, acceptance criteria, and boundaries, while leaving implementation choices to the developer.

Improved design-tree handling follows answers into dependent decisions instead of stopping after one round of questions. Agreed decisions improve the specification, unresolved choices stay visible, and a final handoff challenge checks for materially different interpretations before declaring it ready.

## 4.0.0

Reviews now focus on whether a change delivers the requested behavior safely and keeps the next change manageable. Findings need evidence, a concrete consequence, and the smallest safe direction; unclear code should be improved rather than explained through more comments. Incomplete reviews can no longer look clean merely because their finding totals are zero.

- **`code-review` (2.0.0)** replaces the education goal with actionable feedback, applies one evidence and severity standard across review areas, and checks intended behavior and existing regression coverage. Necessary contract documentation and concise external rationale remain valid; style preferences, speculative abstractions, and missing new test files are not findings by themselves.
- **`code-review` (2.0.0)** also owns a shared chunked review protocol. Chunks pass along contract facts and unresolved cross-file concerns, then a final integration step verifies coverage, checks affected producers and consumers, reconciles conflicting claims, merges duplicate causes, and rebuilds totals and rendered output. The 1,500-line chunking and 5,000-line size-confirmation thresholds are unchanged.
- **`review-pr` (5.4.0)**, **`review-local` (1.2.0)**, **`resolve-pr-feedback` (1.2.0)**, and **`review-and-resolve-pr` (1.2.0)** use that protocol instead of concatenating chunk reports. Incomplete reviews cannot authorize publication or pass the pre-push self-review gate. Existing provider permissions and the autonomous loop's standing authorization remain unchanged.
- Added [11 fixed review scenarios](skills/code-review/evals/scenarios.json) for comparing skill revisions, including convention departures, necessary rationale, existing test coverage, duplicate cross-chunk findings, and incomplete review states. Comparisons are a skill-maintenance activity, not an additional step in every review.

### Breaking changes

- `inline-comments` now returns the complete structured review result, not a result containing only `comment_bodies`.
- `summary.review_complete` is required. It is false for preflight, per-chunk results, and incomplete coverage; only a completed normal review or an integrated agreed scope returns true.
- Chunked callers must pass `review_context.chunk_context` and run final integration before consuming the result as a completed review. Per-chunk results include `summary.cross_file_context` for the handoff.

### Migration from 3.x

1. Update the plugin as a whole so the core and its callers use the same contract. The bundled workflows reference sibling skills inside the plugin; copying one skill alone does not install its dependencies.
2. In custom inline callers, read comment text from the returned result's `comment_bodies` map and retain the rest of the result.
3. Replace custom chunk concatenation with the [shared chunked review protocol](skills/code-review/SKILL.md#chunked-review-protocol). Use the integrated findings, totals, report, and comment bodies rather than raw chunk output.
4. Require `summary.review_complete: true` before publication, approval, request-changes actions, or a successful self-review gate. Missing or false completion state is not a clean review.

## 3.7.0

Added `test-pr-e2e` (1.0.0), which tests a PR or MR like a human QA engineer using Microsoft's official `@playwright/mcp` server. Phase 1 delegates to `test-pr-guide` to turn the diff into an editable scenario list; Phase 2 runs each scenario live in a Playwright-controlled browser with inline step logging, failure screenshots, and a structured report. It supports a single PR/branch or a multi-service feature split across several repos, with a pre-flight reachability check per service.

The skill never checks out a branch or creates a worktree — it runs against whatever is already serving the PR's code at the `entry_url` given to it. Login is handled by asking for credentials once and reusing only the resulting browser session; credentials are never logged or stored. Console/network monitoring reuses the server's own tools, clean-state falls back to a `browser_evaluate` reset when `--caps=storage` isn't enabled, and password fields are excluded from DOM read-back checks.

Playwright MCP setup is delegated to `configure-mcp` and its pinned `@playwright/mcp@0.0.79` catalog entry rather than bundling a server directly, consistent with the plugin's 2.0.0 architecture. `test-pr-e2e` depends on `review-pr`, `test-pr-guide`, and `configure-mcp`.

## 3.6.0

`validate-ticket` is renamed to `prepare-ticket` (2.0.0). The skill does more than check a ticket: it rewrites the title and description into a brief an agent can build from, so "prepare" says what it does better. Its behaviour is unchanged.

- `validate-ticket` (2.0.0) stays as a deprecated wrapper so existing prompts, agent definitions, and project instructions keep working. It tells the user about the new name and then runs `prepare-ticket`. It will be removed in a future major release.
- `fetch-ticket` (1.0.1) and `implement-ticket` (1.2.1) now name `prepare-ticket`.

### Migration

Replace `validate-ticket` with `prepare-ticket` in any prompt, agent definition, or project instruction that names it.

## 3.5.0

`validate-ticket` (1.3.0) is shorter and gives each rule once, with its reason, instead of repeating it across steps and a closing list of prohibitions. The approval rule for tracker writes now lives in one place in Step 7, and the guardrails are replaced by a short final check. Rules are written as what to do rather than what to avoid.

- The design tree gains an eleventh area, **Security, performance, and cost**, so these are settled before a ticket is called ready rather than found during the build.
- The rewritten description cites code by path and symbol instead of line number, and names the evidence commit at the top of Context, so the brief stays usable after the code moves on. Findings, the report, and the comment keep `path:line`.
- Every description rule now says why it exists.
- Steps 4 and 5 are reordered: Step 4 closes the design tree without asking, and Step 5 scores the rubric first and then asks every human-only question in one batch. Before, the questions were asked before the rubric that finds half of them had been scored. With nobody there to answer, the questions stay open and the ticket is not ready.
- The description is reordered so a human can review it before an agent builds it. Everything above a horizontal rule fits on one screen and says what will be built: Why, Goal with a **How to check** line, What changes, Out of scope, Decisions and assumptions to check, and Definition of done. The code detail comes after the rule. Before, a long Context section sat between the goal and the requirements.
- The description has one list of behaviour. Each requirement is a plain heading under **What changes**, with its acceptance criteria directly under it, replacing the separate in-scope, requirements, and acceptance-criteria lists that drifted apart. Definition of done covers only how the work is checked and shipped. The rubric drops from thirteen criteria to twelve.
- Acceptance criteria are no longer the skill's to invent. Each outcome traces to a fact in the code, a human decision, or a visible default marked *(assumed)*. A new user-visible outcome nobody has decided becomes a blocking question.
- Context is replaced by **Implementation notes**: an optional suggested approach the implementer may set aside, where the code is, and the constraints to honour, one fact per line. Facts about the code no longer read as orders to edit it.
- Decisions and assumptions are a list of only what a human should check, not a table that also held facts from the code.
- Measurements, run identifiers, and the argument for the diagnosis go in the ticket comment instead of the description, which links to it.

## 3.4.0

Added `review-architecture` (1.2.0), a read-only review of how an existing codebase is designed. It starts from the git history rather than from random files. Three bundled scripts, which need only Python 3 and git, do the measuring so every run counts the same way:

- `hotspots.py` ranks the most changed files by size, growth and complexity, lists the files that keep changing in the same PR, and lists large, complex files nobody touches.
- `deps.py` reads the imports to find dependency cycles, imports that point the wrong way between layers, and framework leaks in the domain.
- `packages.py` reads the package manager files, Dockerfiles, compose files and CI workflows to find runtimes and frameworks past their end of life, deprecated or abandoned packages, and stale lockfiles.

The review checks the hot spots against layering, dependency direction, cohesion, SOLID, simplicity, error handling and test safety rules. It holds a codebase to the architecture it declares, so framework idiom is not reported as a flaw. Every finding cites a `file:line` that was read. A runtime or main framework past its end of life is rated High from the end-of-life date, because security fixes stop that day; components that end within six months, and databases or images that production is not shown to run on, are Medium, in a separate finding. The report goes to `docs/<project>-architecture-review-<date>.md` and ends with three refactoring milestones that each ship without breaking callers.

`packages.py` is the only script that uses the network. It sends one request per product to endoflife.date, with nothing from the repo but the product name. `--offline` skips it, and the versions are then listed as not checked. Known vulnerabilities are not checked; the report points to `asvs-audit` and the package manager's audit command.

## 3.3.0

`review-pr` (5.3.0) handles GitHub's restriction against self-review: `APPROVE` and `REQUEST_CHANGES` review events are rejected when submitted by the PR's own author. Step 1 now detects this and stores it as `is_self_review`, and a single GitHub Self-Review Fallback block (referenced by Steps 7-B and 7-C instead of being restated in each) offers a `COMMENT`-state review or a different reviewer/account, and reports in Step 8 that no formal approval/request-changes state was set.

## 3.2.0

`implement-ticket` (1.2.0) now reviews its own work before it opens the PR/MR. Stage 7 runs `review-local` on the finished diff, in its own subagent on the default model. Every finding, at every severity, must be resolved: fixed by default, or rejected only with `file:line` or command output showing it does not hold or is outside the change. The fixes are committed through `write-commit-message`, the repo's checks run again, and the fix commits are reviewed once more, up to three review passes. Anything still open after that is listed as unresolved. On a very large diff the reviewer reviews every chunk and does not stop to ask about scope. The closing report gains a Review line with the findings raised, fixed, rejected, and left open. `review-local` is now a dependency of `implement-ticket`.

## 3.1.0

The title of a ticket is now a write you approve by name. Before, `validate-ticket` could rewrite the title when you had only approved a new description.

- **`validate-ticket` (1.2.0)**: The report ends with one short yes/no question that names each write, such as "Post the 2 questions and rewrite the title and description?". An approval that names only the description leaves the title alone, and a standing directive covers only what it names. A `not-ready` ticket with open questions now gets the questions posted and the ticket rewritten with those questions visible in it, and the rewrite note goes in the same comment as the questions, so the ticket gets one comment. Jira edits pass `--yes`, because an agent's shell cannot answer the confirmation prompt.
- **`implement-ticket` (1.1.0)**: Rewritten to say what to do instead of what to avoid. PR/MR titles and bodies are written in plain English for a colleague new to the code, with the ticket link on the last line. The code-host route (which tool to use, how to check it, when to stop) now has its own section in `references/provider-operations.md`, separate from the tracker route in `fetch-ticket`.

## 3.0.0

Added `implement-ticket`, which takes a ticket from request to open PR/MR in one autonomous pass. It supports Jira work items, GitHub Issues, and GitLab Issues through the saved provider route, and a ticket pasted as plain text. The PR/MR goes to whichever code host `origin` points at, independent of where the ticket lives, so a Jira ticket delivered as a GitHub PR works the same way as a GitLab issue delivered as a GitLab MR.

The skill treats the ticket as a claim to test rather than a spec to obey. It critiques the request, classifies every factual claim against the repository, and closes the remaining gaps as stated assumptions instead of questions. The build runs in a throwaway worktree that is always removed, verification uses the repository's own commands, and agents the repository defines itself outrank generic ones. Every commit message is delegated to `write-commit-message`, scoped to that worktree. The PR/MR links the ticket — `Closes #N` for GitHub and GitLab issues, the key for Jira — and the skill never edits, transitions, or comments on the ticket. The closing report leads with any deviation from what the ticket asked for. Review-only requests are handed to `validate-ticket`.

Added `fetch-ticket`, a reusable, read-only ticket reader that `validate-ticket` and `implement-ticket` both call. It parses the identifier, resolves the saved route, and returns one provider-neutral ticket with the description and every comment verbatim, plus the route it used and whether the ticket belongs to the current checkout. It is built to run as a lightweight subagent, so raw tracker payloads stay out of the caller's context. Identifier parsing, route resolution, field mapping, and every read now live only in `fetch-ticket`'s `references/provider-operations.md`; each caller keeps only its own writes.

Changed skills:

- **`validate-ticket` (1.1.0)**: Reads the ticket through `fetch-ticket`, and its `references/provider-operations.md` now holds only the tracker writes. Claim tracing is delegated to a lightweight explore subagent, so file views and search hits stay out of the main session. A new Voice section governs every question, finding, and comment. Blocking questions now carry context, choice, options, recommendation, and later cost, and must be answerable without opening the code. The rubric gains a thirteenth criterion, **Title**: the title is the Goal as a one-line instruction in plain language, a replaced title is printed in full, and it is written back to the ticket together with the description. A `stale` load-bearing claim is now a blocker, like a `contradicted` one. Open blocking questions are asked once, in Step 4, and a `not-ready` ticket's next action is to post them on the ticket rather than ask again. The closing report runs only when an action was taken. The rubric, finding format rules, and description template moved into `references/readiness-rubric.md` and `references/description-template.md`.
- **`write-commit-message` (1.1.0)**: States that a delegating workflow should run it in an isolated subagent on the host's fast, lightweight model tier.
- **`resolve-pr-feedback` (1.1.0)**, **`review-and-resolve-pr` (1.1.0)**: Delegate each commit message to `write-commit-message` in an isolated subagent on the fast, lightweight model tier. In `resolve-pr-feedback`, that subagent is still scoped to the worktree and told the change is already staged and it must not stage anything itself. Both skip the one-time scope question on very large reviews and run every chunk.
- **`code-review` (1.2.0)**: Decides whether to split a review by the number of changed lines instead of the number of files. Many files with small edits are an easy review, and splitting them apart hides bugs that span files. A change of up to 1,500 lines, not counting lock files, generated code, vendored code, minified bundles, and snapshots, is now reviewed in one pass. A larger change is split into chunks of at most 1,500 lines that keep a directory's files and their tests together, instead of fixed batches of five files. Chunks run without asking for confirmation; the user is asked once, and only above 5,000 lines, whether to narrow the scope. The output gains `confirm_scope` and `counted_lines`, and `code_input.files` can carry per-file line counts.
- **`review-pr` (5.1.0)**, **`review-local` (1.1.0)**: Run every chunk in order without stopping to confirm each one, and ask only the one-time scope question `code-review` raises above 5,000 lines. `review-pr` passes per-file line counts from the provider to `code-review`.

### Breaking change

- Removed `create-gitlab-mr`. It committed whatever was in the working tree and opened an MR in one step, without validating the work or running the project's checks. `implement-ticket` now covers the ticket-to-MR path on GitLab and GitHub, `write-commit-message` covers committing, and `glab mr create` opens an MR from an existing branch.
- Removed `scope-plan`, deprecated since `write-plan` and `estimate-time` replaced it. Use `write-plan` for the implementation plan and `estimate-time` for the hour estimate.
- Removed `wbso-aanvraag`. Drafting a Dutch WBSO subsidy application is a finance and advisory task, not part of the delivery workflow this plugin supports, and the skill no longer belongs here.

### Migration from 2.x

Replace any prompt, agent definition, or project instruction that names a removed skill:

- `create-gitlab-mr` → `implement-ticket` when the work starts from a ticket, or commit through `write-commit-message` and run `glab mr create` yourself.
- `scope-plan` → `write-plan`, then `estimate-time` when an hour estimate is needed.
- `wbso-aanvraag` → no replacement in `aimate`. Keep a copy from the 2.x release if your team still uses it.

## 2.4.0

Added `validate-ticket`, which decides whether one ticket is ready for development and rewrites its description into a brief an agent can build from. It supports Jira work items, GitHub Issues, and GitLab Issues through the saved provider route, and a ticket pasted as plain text when no tracker is reachable. Every provider difference — identifier parsing, field mapping, Jira custom-field discovery, and the ADF/wiki formatting trap on a description write — lives in `references/provider-operations.md` rather than in the workflow.

The skill traces each load-bearing claim in the description and comments against the checkout, gives it a verdict with a `file:line` behind it, and then closes the design tree in the same Observed / Decision / Assumption vocabulary `write-plan` uses. It closes what the repository can answer and asks only what a human must decide, in one batch, with a recommendation attached to each question. A blocking branch never closes as an assumption, and assumptions that are taken stay visible in the ticket.

The verdict is arithmetic on a twelve-criterion rubric rather than a judgment call, and it routes rather than reports: every run ends with one named next action and one owner. A ready ticket gets its rewritten description written back, and the ticket becomes the brief an implementer starts from. A `not-ready` ticket with mechanical gaps gets them closed in the same run, including a split into children when that is the gap. A `not-ready` ticket with an open blocking decision goes back to a human — asked of the user directly, or posted on the ticket for its author — because an agent asked to settle a decision it does not own will invent one, and an invented decision reads as settled once it sits in a description.

The rewritten description applies prompting rules to a ticket: why before what, an observable goal, provenance on every fact, scope bounded in both directions, and a definition of done carrying the real validation commands.

Output is written for a person. A finding is a bold one-line claim, the code that contradicts it with a `file:line`, and one imperative action — grouped as **Blocking**, **Filled in for you**, and **Worth a look**, with no ids, slugs, or severity tokens. The report is built for a terminal: findings first, a few lines on what the rewrite changes, then the verdict and the single next action last, where they stay on screen rather than scrolling out of view. The rewritten description, the claim ledger, and the design tree stay behind an offer instead of being dumped, and a criterion that passed is never printed. A comment posted on the ticket inverts that order, since a document is read top-down. The skill writes no file of its own: the durable record is the ticket — the description plus one comment in the same format. It also keeps its coupling to other skills to a minimum, defining its own design-tree vocabulary and provider operations rather than depending on them.

## 2.3.0

Added `review-and-resolve-pr`, which runs both halves of the review loop over one PR/MR in a single autonomous pass. It reviews through `review-pr`, publishes every finding at every severity as an inline comment, then hands those threads to `resolve-pr-feedback` to validate, fix, gate, self-review, push, and reply — and reports the addressed findings in one table.

The skill composes the two existing halves and owns only the seam between them: the shared preconditions, the standing directive that lifts `review-pr`'s hard stop, the finding-to-thread mapping the resolution half needs, the guarantee that both worktrees are gone at the end, and the combined report. Neither half's workflow is reimplemented, and `code-review` is never invoked directly.

Findings this run wrote get no special standing when it comes to fixing them. Each comment is validated against the repository in the fix worktree like any human reviewer's, so `reject`, `already-addressed`, and `needs-clarification` stay live outcomes, and the report ends with a review-quality section naming every finding the run posted and then rejected. Scope stays on the threads the run created; threads a human opened are reported as untouched. It approves nothing, requests changes on nothing, and never re-reviews its own pushed result.

## 2.2.0

Added `resolve-pr-feedback`, which closes the review loop that `review-pr` opens. It reads the unresolved threads on a GitHub PR or GitLab MR, validates each comment against the real code, applies the ones that hold up in an isolated worktree, runs the project's own quality gates, self-reviews the result through `code-review`, and only then pushes and replies per thread.

Feedback that does not hold up is rejected with evidence rather than applied, and threads are resolved only when the fix actually landed. The skill runs autonomously — it decides and reports each judgment call instead of pausing for approval — delegates its commit messages to `write-commit-message`, and never force-pushes, rewrites branch history, or approves its own work.

Review content is treated as untrusted throughout: a comment can name a concern, but it cannot redirect the workflow, widen the scope, or supply commands to run. Contributions from a fork are handled without executing anything the contributor controls and without taking direction from anything they wrote, so those runs skip dependency installation and the quality gates, read the head's own instruction files as evidence rather than orders, and report themselves as unverified, leaving verification to CI on the review.

## 2.1.0

Extracted the shared code-review core, added `review-local`, and updated `review-pr` to delegate analysis to the core.

## 2.0.0

`aimate` is now skills-first. The plugin no longer bundles Figma, GitLab, or Atlassian MCP connections globally. Projects configure only the integrations they need through `configure-mcp` or the supplied project templates.

The setup wizard now validates existing official CLIs and MCP connections before changing anything. GitLab workflows always use the official `glab` CLI and no GitLab MCP template is shipped. GitHub and Jira save preferred and fallback routes in `AGENTS.md`; skills automatically try the fallback instead of asking again. Confluence and Figma keep using MCP where no equivalent CLI exists. Sentry uses MCP for investigations and `sentry-cli` for release assets.

### Breaking change

- Removed the plugin-level `.mcp.json`.
- Removed `mcpServers` from `plugin.json`.
- Removed the GitLab MCP setup and made `glab` a prerequisite for GitLab workflows.
- GitLab.com is no longer assumed for every repository.
- Figma and Atlassian authentication is no longer requested merely because Aimate is installed.

### Migration from 1.x

1. Upgrade or reinstall the Aimate plugin.
2. Install `glab` (`brew install glab` on Homebrew platforms).
3. Authenticate with `glab auth login` and verify access with `glab repo list --member`.
4. If the MCP host retains the old plugin-owned `figma`, `gitlab`, or `atlassian/atlassian-mcp-server` entries, remove or disconnect those old entries in the host.
5. In every client checkout, run `configure-mcp`.
6. Keep the detected working project integrations or select GitLab/GitHub and optional Atlassian, Figma, and Sentry integrations.
7. Choose `Automatic`, `Prefer CLI`, or `Prefer MCP` for GitHub and Jira so the wizard can save explicit preferred and fallback routes.
8. For Claude Code, let the wizard add `@AGENTS.md` to `CLAUDE.md` when that import is missing.
9. Reload or restart the MCP host when requested.
10. Complete OAuth for each newly named MCP connection.

Project configuration must not contain real tokens. Self-hosted Sentry uses a
secret input placeholder; hosted MCP connections use host-managed OAuth.

This release supersedes and closes [#16](https://github.com/Dawn-Technology/aicelerate/issues/16).
