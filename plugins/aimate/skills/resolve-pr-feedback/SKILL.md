---
name: resolve-pr-feedback
description: Use when asked to resolve, address, fix, or reply to review feedback on a GitHub Pull Request or GitLab Merge Request, including review comments, unresolved threads, requested changes, or "apply the review comments" requests.
metadata:
  author: "Martin Roest <martin.roest@dawn.tech>"
  version: 1.0.0
  dependencies:
    - code-review
    - write-commit-message
---

# PR/MR Feedback Resolution Workflow Skill

## Purpose

Turn review feedback on an open PR/MR into verified code changes on the same branch:

- **Verification**: Confirm every comment against the real code before changing anything, and push back on feedback that does not hold.
- **Correctness**: Address what the reviewer meant, not what the comment literally says.
- **Safety**: Work in a dedicated worktree, gated by the project's own build, lint, and test commands.
- **Traceability**: Every thread ends in a visible outcome — on the PR/MR once the push lands, in the report when it cannot.
- **Autonomy**: Decide, act, and report the decisions. Never stop to ask for approval.

This workflow is **write-enabled but scoped**:

- Change code only inside the dedicated worktree, and only what the accepted feedback requires.
- Never fix unrelated issues you notice on the way. Report them instead.
- Never merge, never force-push, never rewrite pushed history.

Both **GitHub** (Pull Requests) and **GitLab** (Merge Requests) are supported; PR and MR are used interchangeably. This skill is remote-only — for local pre-commit review use [review-local](../review-local/SKILL.md).

Provider commands, GraphQL documents, and API payloads live in [`references/provider-operations.md`](./references/provider-operations.md). Read the section a step points to; do not improvise provider calls.

## Autonomy

Run end to end without a confirmation step. Review feedback is mostly clear-cut, the work lands on a branch that is already under review, and everything here is cheap to correct — a blocked agent costs more than a wrong call a reviewer fixes with one comment.

- Never ask which threads to address, whether the plan looks right, or whether to push. Decide from the defaults below.
- Never present a plan and wait for approval. Record the plan, execute it, report what was decided.
- Log every judgment call in the Step 11 report, each with its one-line undo.
- The user intervenes afterwards, not before: a wrong fix is one more commit, a wrong reply is one more reply.

Defaults for every judgment call this workflow can face:

| Situation | Default |
| --- | --- |
| Provider not named in the input | Take it from the `origin` remote |
| Scope not named | Every unresolved thread |
| `{fix_branch}` already exists | Use the next free `-2`, `-3` suffix; never delete the old one |
| No push access to the head branch | Do the work anyway and export patches in Step 9-B |
| Two threads contradict each other | Follow the one that preserves the PR/MR's stated purpose, and say so in both threads |
| A fix reaches beyond the flagged line | Fix the same defect where it provably occurs in files you already touch; anything wider becomes `out-of-scope` |
| A blocking self-review finding survives two passes | Revert that item, mark it `needs-clarification`, push the rest |
| The review is large enough to chunk | Process every chunk in order without pausing |

Three things end a run early: no authenticated route, a dependency that cannot be loaded, and a request that explicitly asked for a plan first ("show me what you'd change"). Cutting the work short — a gate that stays red, a push rejected twice — is itself a decision: take it, finish at Step 11, and report it. Never turn any of these into a question.

## Inputs Required

1. **PR/MR identifier**: a URL, `{owner, repo, pull_number}` for GitHub, or `{project_path, merge_request_iid}` for GitLab.
2. **Optional scope**: a subset of threads, reviewers, or files. Default is every unresolved thread.

## Dependencies

- [code-review](../code-review/SKILL.md) owns the self-review in Step 8, and its findings gate the push.
- [write-commit-message](../write-commit-message/SKILL.md) owns every commit message written in Step 6.

Everything else belongs to this skill: provider detection, thread retrieval, validation, worktree, edits, gates, push, replies, and resolutions.

### Mandatory Dependency Boundary

Delegating to both is a hard workflow boundary, not a recommendation.

- Invoke/load each with the active platform's skill mechanism at the step that needs it.
- Do not substitute your own self-review or your own commit message, and do not add an approval step that `write-commit-message` does not have.
- If either cannot be invoked or loaded, stop and say which one. Do not push.
- Having read them earlier, or facing a small change, does not satisfy this boundary.

---

## Workflow

Follow these steps in order. Do not skip a step.

Notation: `{n}` is the PR/MR number, `{src}` the source branch, `{wt}` the worktree `.worktrees/pr-fix-{n}`, and `{fix_branch}` the temporary branch `aimate/pr-fix-{n}`.

Once Step 2 creates the worktree, every exit path finishes at Step 11 — a declined plan, a failing gate, an abandoned run. The worktree is never left behind silently.

### Step 0 — Detect Provider, Resolve Route, Confirm Write Access

1. **Detect provider** from the URL or the user's input:
   - `github.com` → `provider = "github"`, identifiers `{owner, repo, pull_number}`.
   - `gitlab.com` or a self-hosted GitLab domain → `provider = "gitlab"`, identifiers `{project_path, merge_request_iid}`.
   - If the input names no host, take the provider from the `origin` remote.

2. **Resolve an authenticated route**:
   - Follow the project's `aimate:tool-routing` block in `AGENTS.md`: explicit request, preferred route, then configured fallback. Do not ask again when the fallback works. Without a block, default to `gh` and then GitHub MCP for GitHub; GitLab always uses `glab` and never GitLab MCP.
   - Validate with `gh auth status --active --hostname <host>` or `glab auth status --hostname <host>`. Never use `--show-token`. Validate MCP with discovery plus one read-only metadata call.
   - Store it as `provider_route`. If neither route works, stop before creating a worktree and point at the login command or Aimate's `configure-mcp` skill. Never ask for a token in chat.

3. **Confirm write access.** This workflow pushes commits and resolves threads, so read-only access fails late with the work already done. Check the viewer's push permission on the repository that owns the head branch — see [write access checks](./references/provider-operations.md#write-access-checks). If you cannot push there, note it and carry on — Step 9-B exports the work as patches instead.

4. Verify terminal access, needed for the worktree in Step 2, and that both dependencies can be loaded.

---

### Step 1 — Fetch PR/MR Details and Feedback

Use the tools matching `provider` and `provider_route`. Prefer the CLI's high-level PR/MR commands, and its authenticated `api` subcommand for missing fields. MCP is GitHub-only; use only the matching project server. Commands are in [fetching threads](./references/provider-operations.md#fetching-threads).

Collect:

- Metadata: title, description, author, source and target branch, head repository, draft state, labels, linked issues.
- Every review thread: thread/discussion id, comment ids, author, body, file, line and side, resolved state, full reply chain.
- Top-level comments and review states, including any request-changes review.
- Suggested changes as text. Do not apply them through the provider's commit-suggestion API — Step 6 implements them as ordinary edits so they pass the same gates.
- The commits already on the branch, so you can tell whether a comment was addressed after it was written.

Build the working set:

- Default scope: every unresolved thread, plus any resolved thread whose latest reply asks for something new.
- Keep bot comments, marked as such. They get the same validation and no special deference.
- Group threads describing the same problem into one item, keeping every thread id, so one fix can close several threads.

If the working set is empty, say so and stop. No worktree is needed.

---

### Step 2 — Create the Isolated Worktree

```bash
git fetch origin {src}
git worktree add {wt} -b {fix_branch} origin/{src}
```

- Branch from the fetched remote head, never from a local copy that may be stale or checked out elsewhere.
- Working on `{fix_branch}` and pushing by refspec in Step 9 keeps the branch name from colliding with an existing checkout of `{src}`.
- If `{fix_branch}` already exists from an interrupted run, branch to the next free suffix (`{fix_branch}-2`, `-3`). Never delete or reuse the old one; report that it is still there.
- For a fork head, add the fork as a remote and branch from it instead — see [fork heads](./references/provider-operations.md#fork-heads).

Edit files only inside `{wt}`.

---

### Step 3 — Detect Quality Gates and Capture the Baseline

Take the commands from the first source that names them: repository instructions (`AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `README.md`), then task runners and manifests (`package.json`, `composer.json`, `Makefile`, `justfile`, `pyproject.toml`, `go.mod`, `Cargo.toml`), then CI definitions (`.github/workflows/`, `.gitlab-ci.yml`). Never invent a gate the project does not have.

Pick up to three that cover the changed area — a build or type check, a lint check, and the tests — preferring scoped commands over full-suite runs.

A fresh worktree has no installed dependencies. Install them from the project's lockfile (`npm ci`, `composer install`, `uv sync`, `go mod download`). Never add a dependency the project does not declare, and never touch global tooling.

Run the gates once before changing anything and record the result as `gate_baseline`. If a gate cannot run here — no dependencies, no network, no database — record that with the reason and continue. Never claim a gate passed when it did not run.

The baseline decides Step 7: a gate that was green becomes a hard pass condition, and a suite that was already red is not this work's failure.

---

### Step 4 — Validate Every Piece of Feedback

This is the core of the skill. Reviewers are often right, sometimes partly right, occasionally wrong. Applying feedback unchecked produces broken code and a false trail of resolved threads.

For each item, read the current state of the code in `{wt}` — not the diff quoted in the comment — trace the affected paths, and assign exactly one verdict:

| Verdict | Meaning | Code change | Thread in Step 10 |
| --- | --- | --- | --- |
| `accept` | Concern is real, proposed fix is right | Implement as asked | Reply, resolve |
| `accept-with-deviation` | Concern is real, proposed fix is wrong, incomplete, or harmful | Implement a better fix | Reply with the deviation, resolve |
| `already-addressed` | The code already satisfies the request | None | Reply with the commit or lines, resolve |
| `reject` | Concern does not hold: misreads the code, intended behaviour, or factually wrong | None | Reply with the evidence, leave open |
| `out-of-scope` | Concern is real but belongs to other work | None | Reply, offer a follow-up ticket, leave open |
| `needs-clarification` | Ambiguous; different readings lead to different code | None | Ask in the thread, leave open |
| `question` | Not a change request | None | Answer in the thread, leave open |

Rules:

- Every verdict needs concrete evidence: a `file:line` in `{wt}`, a commit SHA, a test name, or a traced call path. A verdict without evidence is not a verdict.
- Verify the claim independently. If the reviewer says a value can be null, find the path that makes it null; if you cannot, the verdict is `reject` or `needs-clarification`, never `accept`.
- `reject` is a legitimate outcome and must never be avoided out of politeness, but the bar is evidence, not opinion. A style preference from a reviewer with merge rights is `accept`.
- If a fix reaches further than the reviewer asked, fix the same defect where it provably occurs in the files you already touch, and record the reach. Anything wider than that is `out-of-scope`.
- If addressing a comment would break the stated purpose of the PR/MR, that is `needs-clarification`.
- When two threads conflict, follow the one that preserves the stated purpose of the PR/MR, and say so in both threads.

For each accepted item, sketch the change first: files touched, approach, risk, and whether it needs a test.

---

### Step 5 — Record the Plan and Proceed

Write the plan down before changing any file. It is the record the Step 11 report is built from, not an approval request:

- PR/MR title, `{src}` → target branch, and the size of the working set.
- One line per item: thread reference, reviewer, verdict, intended change, evidence.
- Grouped by verdict, `accept` and `accept-with-deviation` first.
- Every conflict, wider reach, and Autonomy default applied.
- The detected gates and `gate_baseline`, including any gate that could not run.

Then continue to Step 6 in the same turn. Do not ask whether to proceed.

One exception: when the request explicitly asked for a plan first, present the plan, stop there, and clean up in Step 11 on the next turn.

---

### Step 6 — Implement and Commit

Work through the accepted items one logical change at a time.

- Match the surrounding code: naming, structure, error handling, test patterns.
- Add or update tests when an item changes behaviour and the project has a suite for that area. If it does not, say so in the report.
- Update documentation, translations, and type definitions the change makes stale.
- Keep unrelated formatting out of the diff. If the project's formatter rewrites untouched lines, commit that separately.
- Stay inside the recorded plan. Anything you discover that the plan does not cover goes into the Step 11 report, not into the diff.
- Track which thread ids each edit resolves. Step 10 needs that mapping.

Commit each logical unit as you finish it — one commit per item, or one per group of items sharing a fix. That gives Step 8 a real diff and keeps each fix attributable to its thread. Invoke [write-commit-message](../write-commit-message/SKILL.md) for every message and use it verbatim; it runs autonomously, so add no approval step of your own.

Nothing is pushed yet, so amending or squashing `{fix_branch}` stays safe until Step 9.

If an accepted item proves unimplementable as planned — the fix breaks something else, or the reviewer's assumption fails once you write it — revert its partial edits, move it to `needs-clarification`, and report it. Do not improvise a solution the user has not seen.

---

### Step 7 — Run the Quality Gates

Run the Step 3 gates in `{wt}`.

- Every gate green in `gate_baseline` must be green now. That is a hard condition.
- A gate already red must be no redder: compare the failure lists, not the exit codes.
- On a new failure, fix it and re-run, at most twice. If it still fails, stop and go to Step 11 keeping `{wt}`, and report the failure with its exact output.
- Never weaken a test, a lint rule, or a type to make a gate pass, and never push a red branch.
- Record the final output for the Step 11 report. Never state that a gate passed unless you ran it here and saw it pass.

---

### Step 8 — Self-Review Before Pushing

Nothing leaves the machine before [code-review](../code-review/SKILL.md) has seen it.

```bash
git -C {wt} status --short          # must be empty; commit or discard whatever is left
git -C {wt} diff origin/{src}...HEAD
```

Invoke [code-review](../code-review/SKILL.md) with:

```yaml
submission:
  type: local-scope
  title: "Self-review of feedback resolution for {pr_mr_title}"
  description: "Changes resolving review feedback. Accepted items: {accepted_item_summaries}"
  author: "{git_config_user_name_if_available}"
  source_ref: "{fix_branch}"
  target_ref: "origin/{src}"
code_input:
  diff: "{self_review_diff}"
  files: "{changed_file_inventory}"
  repository_path: "{wt}"
review_context:
  existing_feedback: "{original_threads_with_verdicts}"
  constraints: "Self-review before pushing to an open PR/MR. Verify each change resolves its thread and introduces no regression. Do not re-report deviations the plan already accepted."
  focus_areas:
    - logic
    - security
    - syntax
    - maintainability
    - documentation
    - scope-consistency
  output_target: calling-skill
```

Store the result as `self_review_result`:

- Every `security-violation` and `request-for-change` finding blocks the push. Fix, re-run Step 7, and self-review again — at most twice. If a finding survives that, revert the item it belongs to, move that item to `needs-clarification`, and push the rest. Never push a change your own review still calls broken.
- `optional` findings do not block. List them in the report and leave them.
- If `chunking_required` is `true`, process every chunk in order and combine the results without reclassifying them, then apply this gate.

Then check what `code-review` cannot, because it reviews the code and not the mandate:

- Does each change actually resolve the thread it claims to, or only look like it does?
- Is anything in the diff outside the recorded plan?
- Are any secrets, debug statements, commented-out code, or stray `TODO` markers left behind?
- Does the diff still match the stated purpose of the PR/MR?

Invariant before Step 9:

```text
Did I invoke/load code-review on this diff, are all blocking findings fixed or waived by the user, and did every green baseline gate pass after the last edit?
```

If not, go back. Do not push.

---

### Step 9 — Push

#### 9-A: Push

Push once Step 8 clears. Do not ask first; the commit list, changed files, gate results, and self-review outcome go into the Step 11 report.

```bash
git -C {wt} push origin {fix_branch}:{src}
```

- Never force-push, and never rewrite history that is already on the remote.
- On a non-fast-forward rejection, someone pushed to `{src}` while you worked. Rebase `{fix_branch}` — still unpushed, so this is safe — onto the new remote head, re-run Steps 7 and 8, and retry once. If it is rejected again, stop pushing, keep `{wt}`, and report it — the branch moved twice while you worked, so a human should look.
- After an ambiguous failure, fetch and compare the remote head before retrying. A failed response can follow a successful push.

#### 9-B: When the Push Is Not Possible

A fork without maintainer edits, a protected branch, or read-only access. Do not discard the work — export it:

```bash
git -C {wt} format-patch origin/{src}..HEAD -o .worktrees/pr-fix-{n}-patches
```

Keep `{wt}`, skip Step 10 entirely — nothing landed, so no thread has an outcome to report on — and put the patch path, the `git am` command, and every verdict into the Step 11 report instead.

---

### Step 10 — Reply and Resolve Threads

Runs only after a successful push. Every thread in the working set gets a visible outcome; the Step 4 table says which get resolved and which stay open. Mechanics are in [replying and resolving](./references/provider-operations.md#replying-and-resolving).

Each reply states what was done, or why nothing was done, plus the evidence: the commit SHA carrying the fix, or `file:line`.

- Never resolve a thread whose fix did not land in the push.
- Leave `reject` and `out-of-scope` threads open unless the user explicitly says to close them. Deciding a reviewer is wrong is the reviewer's call to accept, not yours to close.
- Both providers restrict who may resolve. If a resolve is refused for permissions, leave the reply and report which threads still need a human.
- If a batch fails partway, re-fetch the threads and post only what is missing. A duplicate reply is noise the author cannot easily delete.
- Never approve a PR/MR you just changed. If a re-review is wanted, request one through the provider.

---

### Step 11 — Clean Up and Report

Runs on every path that created a worktree, and never in the same response as a plan-first preview.

```bash
git worktree remove {wt} --force
git branch -D {fix_branch}
git remote remove pr-head    # or mr-head, only if Step 2 added one
```

Keep `{wt}` only when the run stopped on a failing gate or left unpushed work the user still needs. Say so explicitly and give the commands above. If removal fails, tell the user to run `git worktree prune`.

Report:

- Every decision taken without asking — verdicts, conflicts resolved, reach beyond the flagged line, reverted items, defaults applied — each with its one-line undo.
- One line per thread: reference, verdict, outcome, resolved or left open.
- Commits pushed, with SHAs, and the branch they landed on.
- Gate results, including any gate that could not run and why.
- Self-review outcome, including `optional` findings left unaddressed.
- Anything deferred: out-of-scope items worth a ticket, threads awaiting a human, unrelated problems found but not fixed.
- Any fallback path used, in one sentence.

---

## Reply Format Rules

- Plain prose, one to four sentences, no headings.
- Lead with the outcome, then the evidence.
- Point at a commit SHA or `file:line`, never "fixed in the latest commit".
- Claim a test or build only when Step 7 actually ran it.
- Match the language of the thread, and do not thank, apologise, or editorialise.

```text
Fixed in a1b2c3d — the guard now runs before the cache write, so the null path in OrderService.php:88 can no longer reach it.
```

```text
Applied differently: clamping would hide the bad input instead of rejecting it, so validation moved up into CreateOrderRequest.php:34 and the handler stays strict.
```

```text
Left as is — `items` is guaranteed non-empty by the query on line 42, and the repository throws when it is not, so the extra check is unreachable.
```

## Guardrails

- Never stop for approval. Decide, act, and report — the three exceptions are listed under Autonomy.
- Never merge, close, reopen, approve, or retarget a PR/MR.
- Never force-push, and never rewrite history already on the remote.
- Never edit files outside `{wt}`, and never change code the recorded plan does not cover.
- Never weaken a test, lint rule, or type check to make a gate pass.
- Never resolve a thread that was not addressed, and never resolve a rejected thread without the user's say-so.
- Never use raw `curl` for provider APIs, tools from the wrong provider, or a GitLab.com route for a self-hosted MR. Use `gh`, `glab`, or the matching MCP route, and `git` for local, worktree, and push operations.
- After an ambiguous remote write failure, reconcile through the same route before retrying. Never switch routes mid-batch and duplicate a mutation.
- If the workflow is interrupted, run `git worktree prune` and delete any leftover `aimate/pr-fix-*` branch.
