---
name: review-local
description: Use when reviewing local code before committing and the user wants findings for a file, folder, uncommitted changes, staged changes, commits, patches, or snippets without involving a pull request or merge request.
metadata:
  author: "Martin Roest <martin.roest@dawn.tech>"
  version: 1.0.0
  dependencies:
    - code-review
---

# Local Code Review Workflow Skill

## Purpose

Review local code before committing without involving a pull request or merge request. This skill is read-first and non-invasive:

- Do not modify repository files.
- Do not commit, stage, push, or create branches.
- Review the scope requested by the user.
- Use the reusable [code-review](../code-review/SKILL.md) skill for analysis and finding generation.

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

### Step 2 — Prepare Code Review Core Input

Invoke the [code-review](../code-review/SKILL.md) skill with this local-review wrapper:

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

The code-review dependency MUST review every file or snippet in the requested scope, trace adjacent code when needed, classify findings, and return structured output to this skill.

### Step 3 — Present Findings

Present the findings returned by `code-review` to the user.

The report must include:

- Reviewed local scope.
- The `code-review` report, including finding totals, ordered findings, and residual review gaps. If `code-review` reports no findings, confirm the scope that was reviewed, state that no issues were found, and include any residual gaps from the `code-review` summary.

## Guardrails

- Keep the review read-only unless the user explicitly asks for edits in a later turn.
- Do not post remote comments, approve PRs/MRs, or request changes from this skill.
- Do not create branches, commits, pushes, or worktrees.
- Keep findings tied to concrete local code evidence.
