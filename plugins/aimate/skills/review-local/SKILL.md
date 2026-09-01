---
name: review-local
description: Use when reviewing local code before committing and the user wants findings for a file, folder, uncommitted changes, staged changes, commits, patches, or snippets without involving a pull request or merge request.
metadata:
  author: "Piotr Ramotowski <piotr.ramotowski@dawn.tech>"
  version: 1.0.2
  dependencies:
    - code-review
---

# Local Code Review Workflow Skill

## Purpose

Review local code before committing without involving a pull request or merge request. This skill is read-first and non-invasive:

- Do not modify repository files.
- Do not commit, stage, push, or create branches.
- Resolve the scope requested by the user.
- Delegate analysis and finding generation to the reusable [code-review](../code-review/SKILL.md) skill.

## Dependency

This skill depends on the reusable [code-review](../code-review/SKILL.md) skill for framework-agnostic review analysis, finding classification, and feedback generation.

`review-local` owns local scope resolution, local diff/patch/snippet collection, repository context packaging, user-facing presentation, and read-only local-review guardrails.

`code-review` owns the core review logic: syntax, logic, security, style/maintainability, documentation/scope analysis, finding schema, severity classification, and provider-neutral report text.

### Mandatory Dependency Boundary

`review-local` MUST delegate the core analysis to `code-review`; this is a hard workflow boundary, not a recommendation.

- Invoke/load the [code-review](../code-review/SKILL.md) skill with the active platform's skill mechanism before analyzing or classifying findings.
- Do not substitute your own syntax, logic, security, maintainability, documentation, or scope review for `code-review`.
- Do not present findings unless the findings came from the `code-review` output interface.
- If `code-review` cannot be invoked or loaded in the current environment, stop and tell the user the required dependency is unavailable. Do not continue with a manual review.
- Having read `code-review` earlier, remembering its workflow, seeing an obvious issue, reviewing a small change, or being under time pressure does not satisfy this dependency.

## Inputs Required

The user must define the review scope. Supported scopes include:

- A folder, such as `src/Domain/Billing`.
- A file, such as `app/Http/Controllers/UserController.php`.
- Uncommitted changes.
- Staged changes.
- A commit or commit range.
- A patch or diff file.
- A code snippet pasted in chat.

If the scope is unclear, ask one concise clarification before reviewing.

## Workflow

Follow these steps in order.

### Step 1 — Resolve Local Scope

Determine the requested scope and collect the matching input without changing the working tree:

- **Uncommitted changes**: use `git diff`.
- **Staged changes**: use `git diff --staged`.
- **Commit**: use `git show --stat` and `git show`.
- **Commit range**: use `git diff <base>..<head>`.
- **Folder or file**: inspect the requested path and, when useful, compare with the current branch base or review the full file contents.
- **Patch/diff file**: read the provided patch or diff.
- **Snippet**: use the pasted code and any language/framework hints from the user.

Also collect repository context that helps the core review:

- `git status --short`
- nearby files or callers/callees for changed logic
- relevant project config, README, lint/test config, or repository instructions

Do not create worktrees or branches for local reviews.

### Step 2 — Invoke Code Review Core

Invoke the [code-review](../code-review/SKILL.md) skill with this local-review wrapper before doing any review analysis:

```yaml
submission:
  type: local-scope   # or commit, patch, diff, snippet — whichever matches the requested scope
  title: "Local review: {user_scope}"
  description: "{user_request}"
  author: "{git_config_user_name_if_available}"
  source_ref: "{scope_or_head_ref}"
  target_ref: "{base_ref_if_known}"
code_input:
  diff: "{local_diff_or_patch_when_available}"
  files: "{reviewed_file_inventory}"
  snippets: "{snippets_when_applicable}"
  repository_path: "{current_repository_path}"
review_context:
  existing_feedback: "{user_supplied_feedback_if_any}"
  constraints: "Local pre-commit review. Do not modify files. Do not commit, stage, push, create branches, or create worktrees."
  focus_areas:
    - syntax
    - logic
    - security
    - style
    - documentation
    - maintainability
    - scope-consistency
  output_target: calling-skill
```

The `code-review` dependency MUST review every file or snippet in the requested scope, trace adjacent code when needed, classify findings, and return structured output to this skill.

Store the returned output as `code_review_result`. `code_review_result` is the only valid source for findings shown in Step 3.

If `code_review_result.chunking_required` is `true`, do not continue to the normal Step 3 report:

1. Present the warning from `code_review_result.report` and the structured `code_review_result.chunk_plan`.
2. Ask the user to confirm processing the first chunk, then end the response without further tool calls.
3. After confirmation, invoke `code-review` for only that chunk and state in `review_context.constraints` that chunking has already been established. Preserve the original file order, local diff context, repository context, and existing feedback.
4. Present that chunk's report, identify its position in the plan, and ask for confirmation before processing the next chunk.
5. After the final chunk, combine the chunk results without reclassifying or rewriting them: sum totals, concatenate findings, order findings by severity then file path, combine residual gaps, and retain each rendered finding block verbatim in the aggregate `report`. Store the aggregate as `code_review_result`, then continue to Step 3.

If the user declines or stops chunking, state that the review is incomplete and list the unreviewed chunks.

Before moving to Step 3, perform this invariant check:

```text
Did I invoke/load code-review for this local review, and are all findings/report details copied from code_review_result?
```

If the answer is not yes, go back and invoke `code-review`. Do not continue by analyzing the local changes yourself.

### Step 3 — Present Findings

Present the findings returned by `code_review_result` to the user.

The report must include:

- Reviewed local scope.
- The `code-review` report, including finding totals, ordered findings, and residual review gaps. If `code-review` reports no findings, confirm the scope that was reviewed, state that no issues were found, and include any residual gaps from the `code-review` summary.

## Guardrails

- Keep the review read-only unless the user explicitly asks for edits in a later turn.
- Do not post remote comments, approve PRs/MRs, or request changes from this skill.
- Do not create branches, commits, pushes, or worktrees.
- Keep findings tied to concrete local code evidence.
