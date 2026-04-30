---
name: review-pr
description: Review a GitHub or GitLab Pull/Merge Request and provide findings, and post structured review comments with issue explanation plus code fixes. Use this skill when asked to review a GitHub Pull Request or GitLab Merge Request.
metadata:
  author: "Martin Roest <martin.roest@dawn.tech>"
  version: 4.2.1
  depends_on: "code-review"
---

# PR/MR Review Workflow Skill

## Purpose

This skill is the PR/MR-specific wrapper around the reusable [`code-review`](../code-review/SKILL.md) skill.

`review-pr` owns:

- Provider detection
- PR/MR metadata retrieval
- Diff and discussion retrieval
- Temporary worktree setup and cleanup
- Posting comments, approvals, or change requests back to GitHub or GitLab

`code-review` owns:

- Core code review logic
- Review baseline establishment
- Diff and snippet analysis patterns
- Finding classification
- Comment-ready feedback generation

The primary goals are:

- **Quality Assurance**: Identify bugs, potential logic errors, and edge cases.
- **Maintainability**: Ensure code is readable, modular, and consistent with the existing architecture.
- **Security**: Detect common security vulnerabilities and privacy risks. Validate against OWASP Top 10 where applicable.
- **Education**: Provide explanations and context for suggested changes to help the author grow.

This workflow is **read-first** and **non-invasive**:

- Do not modify repository files.
- Analyze PR/MR content and discussions.
- Post comments, update PR/MR only when explicitly requested.

This skill supports both **GitHub** (Pull Requests) and **GitLab** (Merge Requests). The terms PR and MR are used interchangeably throughout.

## Inputs Required

1. **PR/MR identifier**: Either a URL or `{repository_id, pull_request_number}` for GitHub, or `{project_path, merge_request_iid}` for GitLab.

---

## Workflow

Follow these steps in order. Do not skip a step.

### Step 0 — Verify Capabilities & Detect Provider

Before proceeding:

1. **Detect provider** from the URL or user-provided input:
   - URL contains `github.com` → `provider = "github"`, use `{owner, repo, pull_number}` as identifiers.
   - URL contains `gitlab.com` or a self-hosted GitLab domain → `provider = "gitlab"`, use `{project_path, merge_request_iid}` as identifiers.
   - If ambiguous, ask the user.

2. **Verify the required MCP capabilities** for the detected provider:
   - **GitHub**: Requires GitHub MCP tools (reading PRs, discussions, diffs, posting reviews). If missing, stop and ask the user to install the GitHub MCP server.
   - **GitLab**: Requires GitLab MCP tools (reading MRs, discussions, diffs, posting notes). If missing, stop and ask the user to install the GitLab MCP server.

3. Verify terminal access is available (required for git worktree operations in Step 2).

Store `provider` — it will gate all provider-specific sub-steps throughout the workflow.

---

### Step 1 — Fetch PR/MR Details

Retrieve all metadata needed for the review using the tools matching `provider`.

**GitHub**:

- Fetch the PR details (title, description, source/target branches, author, labels, milestone, `base_sha`, `head_sha`).
- Fetch existing PR review threads and comments.
- Note: GitHub uses `base_sha` and `head_sha` for inline comment positioning in Step 7-A.

**GitLab**:

- Fetch the MR details (title, description, source/target branches, author, labels, milestone, `base_sha`, `start_sha`, `head_sha`).
- Fetch existing MR discussions and review threads.
- Note: GitLab requires `base_sha`, `start_sha`, and `head_sha` in the diff position object in Step 7-A.

For **both providers**:

- Note all open and resolved threads to avoid duplicate feedback and to verify whether previously requested changes have been addressed.
- Note the description for stated intent, linked issues, and breaking-change flags.

---

### Step 2 — Checkout PR/MR Branch

Use `run_in_terminal` to create an isolated worktree — even if the source branch is already checked out locally. **The purpose of this isolated worktree is to understand the full codebase, trace control logic across files, and evaluate the true architectural impact of the proposed changes.**

```bash
git fetch origin {source_branch}
git worktree add .worktrees/pr-review-{pr_mr_number} {source_branch}
```

Store `worktree_path = ".worktrees/pr-review-{pr_mr_number}"` for Steps 3–5. **Read-only enforced** — do not modify files in the worktree.

---

### Step 3 — Gather Codebase Context & Prepare the `code-review` Input Bundle

1. Use `runSubagent` (`Explore` agent) to analyze the project conventions in `worktree_path`. Focus primarily on the modules and adjacent dependencies affected by the PR/MR diff, while briefly checking project-level configuration such as framework config, `README`, linting config, and repository instructions.
2. Retrieve the diffs between the source and target branches using the MCP tools for `provider`.
3. Build a file-change inventory: list each changed file with its change type (added / modified / deleted). **All changed files MUST be reviewed**; do not skip files silently.
4. Collect the review context:
   - PR/MR title, description, source branch, target branch, author
   - Existing open and resolved review threads
   - `provider`
   - `worktree_path`
   - `baseline_conventions` from the `Explore` agent output
5. If the PR/MR contains more than 15 changed files or massive diffs, warn the user and propose chunking into batches of 5 files before invoking `code-review`.
6. Pass the gathered data to `code-review` using a handoff format like this:

```yaml
code_input:
  submission_type: pull-request | merge-request
  diff: "<provider diff text>"
  changed_files:
    - path: src/example.ts
      change_type: modified
  worktree_path: .worktrees/pr-review-{pr_mr_number}

context:
  title: "<pr/mr title>"
  description: "<pr/mr description>"
  author: "<author>"
  source_ref: "<source branch>"
  target_ref: "<target branch>"
  provider: github | gitlab
  baseline_conventions: "<Explore agent summary>"
  existing_feedback:
    open_threads: "<open threads>"
    resolved_threads: "<resolved threads>"

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

If the `Explore` result is incomplete, let `code-review` infer conventions from the repository language/framework and disclose those assumptions in the findings report.

---

### Step 4 — Invoke `code-review`

Activate the [`code-review`](../code-review/SKILL.md) skill and pass the Step 3 bundle as its review input.

`code-review` is responsible for:

- Establishing the review baseline from `worktree_path` and `baseline_conventions`
- Parsing and prioritizing the diff
- Tracing control flow and downstream impact
- Reviewing the submission through syntax, logic, security, style, documentation, architecture, and scope-consistency lenses as applicable
- Producing structured findings and comment-ready feedback

Do not duplicate that logic here unless the dependency is unavailable.

**Fallback if `code-review` is unavailable**: Continue using the same review standards and output contract defined by `code-review`, and note that the dependency could not be loaded.

---

### Step 5 — Present Findings to the User

Do a rubber-duck review of the findings before sharing them, and drop any point that is not backed by concrete evidence.
Then present the grouped findings report returned by `code-review` **before taking any action**.

The report must include:

- PR/MR title, source → target branch, author
- Finding totals per severity
- Findings ordered by severity, then file path
- Each finding formatted exactly using the `code-review` comment template, prefixed with a reference ID (for example, `**Finding #1 — src/Auth.php:88:sql-injection**`)

Render each finding in this format:

`**Finding #N — <id>**`

`**<title>**`

`<body>`

`*Relevant lines: <file path and line reference>*`

`Suggested approach: <suggestion or concise remediation guidance>`

If there are no findings, state that explicitly and mention any residual testing or review gaps.

**HARD STOP**: End the response immediately after presenting the findings and asking the user how they would like to proceed. Provide options naturally: discussing/refining findings, posting comments, approving the PR/MR, or requesting changes. Do NOT call any tools after presenting the report in that same response, and do NOT proceed until the user issues a clear directive in a later turn.

---

### Step 6 — Execute Chosen Action (Only When Confirmed)

Based on the user's instructions from Step 5, take the appropriate action. All sub-steps below branch on `provider`.

#### 7-A: Post Comments

Post all approved findings as visible inline comments on the PR/MR.

Before calling any provider-specific comment API, normalize the target anchor for every finding:

- **Anchor to a stable diff line**: Use a line that is part of the reviewed diff hunk, not just the file on the branch.
- **Prefer non-blank anchors**: If the finding targets a blank line, whitespace-only line, or other unstable anchor, shift the inline comment to the nearest non-blank context line in the same hunk and mention the intended blank line in the comment body.
- **Map the line type correctly**: Added or modified lines should use the post-change line coordinates. Deleted lines should use the pre-change line coordinates. Unchanged context lines should carry both old and new line numbers when the provider API supports that form.
- **Use ranges only when the provider supports them cleanly**: For multi-line findings, prefer explicit start/end positions. If the platform cannot represent the range reliably, anchor to the most representative line and describe the span in the body.
- **Do not force invalid inline positions**: If you cannot derive a stable diff anchor after checking the hunk, fall back to a general review comment that names the file and target line.

If comment submission or publication fails after some comments may already have been created, treat the failure as a potential partial success:

- Reconcile remote state before retrying.
- Fetch the current published review comments/notes to identify what already landed.
- Fetch the remaining pending draft comments/notes, if the provider supports drafts.
- Retry only the comments that are still missing. Do not blindly resubmit the whole batch.

**GitHub**:

- Start a pending review using `mcp_github_add_comment_to_pending_review` for each finding.
  - Provide `owner`, `repo`, `pull_number`, `commit_id` (use `head_sha`), `path`, `line`, and `body`.
  - For multi-line findings, use `start_line` and `line` to span the range.
- Ensure the chosen `line` or range still belongs to the PR diff. If the exact target is not commentable on GitHub, move to the nearest stable diff line or fall back to a top-level PR comment.
- After all comments are added, submit the review using `mcp_github_pull_request_review_write` with `event: "COMMENT"` and an empty or summary `body`.
- **Fallback**: If inline positioning fails (the line is not part of the diff), fall back to a top-level PR comment using `mcp_github_add_issue_comment`, indicating the target file and line.

**GitLab**:

- Create draft notes using `mcp_gitlab_create_draft_note` in a loop for each finding.
  - You MUST provide `base_sha`, `start_sha`, and `head_sha` in the `position` object.
  - **Position Mapping**: Added/modified lines → `new_line` + `new_path`. Deleted lines → `old_line` + `old_path`. Context lines → both `old_line` + `new_line`. Set `position_type: "text"`.
  - This non-blank anchor rule matters especially on GitLab: a draft note on a blank line may be accepted during creation and then silently disappear when drafts are published.
- After all draft notes are created, publish them in a single batch with `mcp_gitlab_bulk_publish_draft_notes`. The user expects published notes, not drafts.
- If `mcp_gitlab_bulk_publish_draft_notes` errors, do not immediately publish every draft individually. GitLab can partially complete the batch before returning an error.
  1. Fetch current MR notes to see which comments were already published.
  2. List remaining draft notes to identify what is still pending.
  3. Publish only the still-pending drafts individually.
- **Fallback**: If inline positioning fails (e.g., "Line is out of bounds"), fall back to a general MR discussion note using `mcp_gitlab_create_merge_request_discussion_note`, indicating the target file and line.

#### 7-B: Approve

If the user requests approval, confirm there are no unresolved security violations first. If there are, explicitly confirm the user wants to proceed despite the risks.

**GitHub**: Submit an approving review using `mcp_github_pull_request_review_write` with `event: "APPROVE"`.

**GitLab**: Approve the MR using `mcp_gitlab_approve_merge_request`.

#### 7-C: Request Changes

Formally mark the PR/MR as requiring changes.

**GitHub**: Submit a review using `mcp_github_pull_request_review_write` with `event: "REQUEST_CHANGES"` and a summary `body` covering the key findings.

**GitLab**: Proceed in two distinct steps.

**Step 1 — Verify reviewer assignment**

Query the MR to get the current user's username and the existing reviewers list:

```graphql
query getMRReviewers($projectPath: ID!, $iid: String!) {
  currentUser {
    username
  }
  project(fullPath: $projectPath) {
    mergeRequest(iid: $iid) {
      reviewers {
        nodes {
          username
        }
      }
    }
  }
}
```

If the current user is **not** in the reviewers list, add them using `APPEND` to preserve existing reviewers:

```graphql
mutation addSelfAsReviewer(
  $projectPath: ID!
  $iid: String!
  $username: String!
) {
  mergeRequestSetReviewers(
    input: {
      projectPath: $projectPath
      iid: $iid
      reviewerUsernames: [$username]
      operationMode: APPEND
    }
  ) {
    mergeRequest {
      id
    }
    errors
  }
}
```

**Step 2 — Request changes**

Once reviewer assignment is confirmed, submit the request-changes state:

```graphql
mutation requestChanges($projectPath: ID!, $iid: String!) {
  mergeRequestRequestChanges(input: { projectPath: $projectPath, iid: $iid }) {
    mergeRequest {
      id
    }
    errors
  }
}
```

_Note: `mergeRequestRequestChanges` requires GitLab 17.10+. On older instances the mutation may not exist — inspect the `errors` array and inform the user if it fails._

#### 7-D/E: Refine or Report Only

If the user wants no action taken, proceed to Step 7 — Cleanup. If they want to refine, discuss the findings, update them, and repeat Step 5.

---

### Step 7 — Clean Up

This step is always executed after Step 6, or immediately after Step 5 when the user chooses report-only.

1. **Remove the git worktree with verification**:

   ```bash
   git worktree remove .worktrees/pr-review-{pr_mr_number} --force
   ```

2. **Report back** to the user:
   - **For Report only**: Confirm findings were presented; no actions taken.
   - **For Posted comments/approval/request-changes**: Published comment/note IDs, approval state (if applicable), PR/MR state change (if applicable), and a summary of key findings.
   - If any fallback path was used, explain why in one sentence.
   - If worktree cleanup failed, notify the user to run `git worktree prune` manually.

---

## Finding Format Rules

Use the comment template defined in [`code-review`](../code-review/SKILL.md). Keep the same finding content for chat and posted review comments.

Differences by destination:

- In chat, include the `Finding #N — <id>` prefix.
- In posted comments, omit the prefix and keep the rest unchanged.

Style rules:

- Keep the tone direct and peer-to-peer.
- Do not use extra headings like `Observation:` or `Impact:`.
- Use the changed file's language in code suggestions.
- Keep summaries short and factual.
- State exactly what was posted, including comment or note IDs when available and the platform used.
- If a fallback path was used, explain why in one sentence.

## Guardrails

- Never merge, alter code, or use API tools from the wrong provider (e.g., do not use GitLab MCP tools on a GitHub PR).
- Do not use raw `curl` or `git` CLI commands for provider API interactions; use MCP tools only.
- Keep findings tied to concrete diff evidence from the branch worktree.
- If the workflow is interrupted (user cancels, agent crashes), manually run `git worktree prune` to clean orphaned entries and recover disk space.
