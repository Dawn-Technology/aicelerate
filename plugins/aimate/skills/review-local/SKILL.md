---
name: review-local
description: Use when reviewing local code before committing and the user wants findings for a file, folder, uncommitted changes, staged changes, commits, patches, or snippets without involving a pull request or merge request.
metadata:
  author: "Martin Roest <martin.roest@dawn.tech>"
  version: 1.0.0
  depends_on: "code-review"
---

# Local Code Review Workflow Skill

## Purpose

This skill is the local-review wrapper around the reusable [`code-review`](../code-review/SKILL.md) skill.

`review-local` owns:

- Clarifying the local review scope with the user
- Gathering the requested local code input
- Preparing the `code-review` input bundle with local context
- Presenting the findings back to the user

`code-review` owns:

- Core code review logic
- Review baseline establishment
- Diff and snippet analysis patterns
- Finding classification
- Comment-ready feedback generation

This skill is intended for pre-commit or local review workflows where the code is available in the workspace and no PR/MR platform interaction is needed.

## Inputs Required

The user must define the review scope. Valid examples include:

- A single file
- A folder or module
- Uncommitted changes
- Staged changes
- A specific commit
- A commit range
- A patch or diff
- A code snippet

If the scope is ambiguous, ask the user to narrow it before reviewing.

---

## Workflow

Follow these steps in order. Do not skip a step.

### Step 0 — Identify the Local Scope

Determine what the user wants reviewed.

Supported scope shapes:

- `file: path/to/file`
- `folder: path/to/folder`
- `uncommitted changes`
- `staged changes`
- `commit: <sha>`
- `commit-range: <base>..<head>`
- `patch: <patch text or patch file>`
- `snippet: <inline code>`

If the user has not specified enough detail, ask a concise follow-up question limited to the missing scope information.

---

### Step 1 — Gather the Local Review Input

Collect the smallest input that fully represents the requested scope.

Use these guidelines:

- **File**: read the file and, when useful, also gather nearby context from adjacent files or local diffs
- **Folder**: build a file inventory, prioritize the most relevant files first, and gather the changed or requested files
- **Uncommitted changes**: gather the current working-tree diff
- **Staged changes**: gather the staged diff
- **Commit**: gather the commit diff and changed file list
- **Commit range**: gather the range diff and changed file list
- **Patch**: use the provided patch text or patch file contents
- **Snippet**: use the provided snippet and explicitly note limited context

When git is available, prefer using diff-based inputs for change review:

- `git diff`
- `git diff --cached`
- `git show <sha>`
- `git diff <base>..<head>`

If the scope is broad or the diff is very large, warn the user and propose chunking the review into smaller batches.

---

### Step 2 — Prepare the `code-review` Input Bundle

Users do not need to provide this structure directly. `review-local` should gather the requested local scope and pass it to `code-review` using a recommended internal handoff format.

Recommended handoff format:

```yaml
code_input:
  submission_type: working-tree | commit | commit-range | patch | diff | snippet
  diff: "<local unified diff when applicable>"
  changed_files:
    - path: src/example.ts
      change_type: modified
  snippets:
    - path: src/example.ts
      language: typescript
      content: |
        export function example() {}
  worktree_path: .

context:
  title: "Local code review"
  description: "<user-requested local review scope>"
  author: "local-user"
  source_ref: "<optional local branch or commit>"
  target_ref: "<optional comparison base>"
  provider: local
  assumptions:
    - "<only when needed>"
  constraints:
    report_only: true
    comment_ready: true

review_scope:
  modules:
    - syntax
    - logic
    - security
    - style
    - documentation
  include_architecture: true
  include_scope_consistency: true
```

Populate only the fields that are relevant to the chosen scope.

---

### Step 3 — Invoke `code-review`

Activate the [`code-review`](../code-review/SKILL.md) skill and pass the Step 2 bundle as its review input.

`code-review` is responsible for:

- Establishing the review baseline from local project context
- Parsing and prioritizing the submission
- Tracing control flow and downstream impact
- Reviewing the submission through syntax, logic, security, style, and documentation modules
- Producing structured findings and comment-ready feedback

Do not duplicate that logic here unless the dependency is unavailable.

**Fallback if `code-review` is unavailable**: Continue using the same review standards and output contract defined by `code-review`, and note that the dependency could not be loaded.

---

### Step 4 — Present Findings to the User

Present the grouped findings report returned by `code-review`.

The report must include:

- The reviewed local scope
- Any notable assumptions or context limits
- Finding totals per severity
- Each finding formatted exactly using the `code-review` comment template, prefixed with a reference ID

If no validated findings are present, say so explicitly and mention any review limits, such as missing project context or generated files that were not deeply inspected.

This skill is report-only. Do not post comments anywhere or modify files as part of the review.

## Guardrails

- Respect the user-defined scope; do not silently expand it into unrelated areas
- Prefer diffs for change review and file contents for whole-file review
- If the scope is too large for a high-quality single pass, stop and ask to review in chunks
- Use the same severity model and comment format as `code-review`
