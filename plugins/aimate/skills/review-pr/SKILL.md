---
name: review-pr
description: Use when asked to review a GitHub Pull Request or GitLab Merge Request, including PR/MR URLs, identifiers, discussions, findings, inline comments, approvals, or request-changes actions.
metadata:
  author: "Martin Roest <martin.roest@dawn.tech>"
  version: 5.0.1
  dependencies:
    - code-review
---

# PR/MR Review Workflow Skill

## Purpose

The purpose of this skill is to provide constructive and comprehensive feedback on code changes. The primary goals are:

- **Quality Assurance**: Identify bugs, potential logic errors, and edge cases.
- **Maintainability**: Ensure code is readable, modular, and consistent with the existing architecture.
- **Security**: Detect common security vulnerabilities and privacy risks. Validate against OWASP Top 10 where applicable.
- **Education**: Provide explanations and context for suggested changes to help the author grow.

This workflow is **read-first** and **non-invasive**:

- Do not modify repository files.
- Collect PR/MR content and discussions for review.
- Post comments, update PR/MR only when explicitly requested.

This skill supports both **GitHub** (Pull Requests) and **GitLab** (Merge Requests). The terms PR and MR are used interchangeably throughout.

Acting on review feedback is the opposite direction and a separate workflow: [resolve-pr-feedback](../resolve-pr-feedback/SKILL.md) validates the threads on a PR/MR, applies the fixes in an isolated worktree, and replies per thread.

## Inputs Required

1. **PR/MR identifier**: Either a URL or `{repository_id, pull_request_number}` for GitHub, or `{project_path, merge_request_iid}` for GitLab.

## Dependency

This skill depends on the reusable [code-review](../code-review/SKILL.md) skill for framework-agnostic review analysis, finding classification, and feedback generation.

`review-pr` owns provider detection, PR/MR metadata retrieval, branch checkout, provider-specific diff retrieval, inline comment positioning, approvals, request-changes state, and cleanup.

`code-review` owns the core review logic: syntax, logic, security, style/maintainability, documentation/scope analysis, finding schema, severity classification, and provider-neutral report/comment text.

### Mandatory Dependency Boundary

`review-pr` MUST delegate the core analysis to `code-review`; this is a hard workflow boundary, not a recommendation.

- Invoke/load the [code-review](../code-review/SKILL.md) skill with the active platform's skill mechanism before analyzing or classifying findings.
- Do not substitute your own syntax, logic, security, maintainability, documentation, or scope review for `code-review`.
- Do not present findings, post comments, approve, or request changes unless the findings came from the `code-review` output interface.
- If `code-review` cannot be invoked or loaded in the current environment, stop and tell the user the required dependency is unavailable. Do not continue with a manual review.
- Having read `code-review` earlier, remembering its workflow, seeing an obvious issue, reviewing a small PR/MR, or being under time pressure does not satisfy this dependency.

---

## Workflow

Follow these steps in order. Do not skip a step.

### Step 0 — Detect Provider & Resolve Tool Route

Before proceeding:

1. **Detect provider** from the URL or user-provided input:
   - URL contains `github.com` → `provider = "github"`, use `{owner, repo, pull_number}` as identifiers.
   - URL contains `gitlab.com` or a self-hosted GitLab domain → `provider = "gitlab"`, use `{project_path, merge_request_iid}` as identifiers.
   - If ambiguous, ask the user.

2. **Resolve an authenticated route** for the detected provider:
   - Follow the project's `aimate:tool-routing` block in `AGENTS.md`: explicit request, preferred route, then configured fallback. Do not ask again when the fallback works. Without a block, default to authenticated `gh` and then GitHub MCP for GitHub; GitLab always uses `glab` and never GitLab MCP.
   - Validate CLI routes with `gh auth status --active --hostname <pr-host>` or `glab auth status --hostname <mr-host>`. Never use `--show-token`. Validate MCP with discovery and one harmless read-only metadata call only when needed.
   - Store the working route as `provider_route` and mention a fallback briefly in the final report. If neither route works, stop before creating a worktree and point to the relevant login command or Aimate's `configure-mcp` skill. Never ask for a token in chat.
   - Do not call tools from another provider or use a GitLab.com route for a self-hosted MR.

3. Verify terminal access is available (required for git worktree operations in Step 2).

4. Verify the [code-review](../code-review/SKILL.md) dependency can be invoked/loaded. If unavailable, stop and tell the user the required dependency is unavailable.

Store `provider` — it will gate all provider-specific sub-steps throughout the workflow.

---

### Step 1 — Fetch PR/MR Details

Retrieve all metadata needed for the review using the tools matching `provider` and `provider_route`. Prefer the provider CLI's high-level PR/MR commands and use its authenticated `api` subcommand for missing fields. MCP is supported only for GitHub; use only the matching project server.

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

Store `worktree_path = ".worktrees/pr-review-{pr_mr_number}"` for Steps 3–5 and cleanup in Step 8. **Read-only enforced** — do not modify files in the worktree.

---

### Step 3 — Prepare PR/MR Review Context

Keep the checked-out worktree read-only and prepare PR/MR-specific context for the `code-review` dependency:

- `repository_path = ".worktrees/pr-review-{pr_mr_number}"`
- PR/MR title, description, author, source branch, and target branch.
- Existing open and resolved review threads.
- Provider diff refs and SHA metadata needed for inline comments.

If you already have a useful codebase baseline from adjacent tools or exploration, store it as `review_baseline` and pass it to `code-review`. Otherwise, let `code-review` gather the baseline from `repository_path`.

---

### Step 4 — Retrieve Provider Diff

1. Retrieve the diffs between the source and target branches through `provider_route`. Use `gh pr diff`/`gh api`, GitHub MCP tools, or `glab mr diff`/`glab api`. Do not use raw `curl`.
2. Preserve provider-specific diff coordinates and SHA metadata for Step 7-A.
3. Build the provider changed-file inventory required by the `code-review` input interface, including each changed file and its change type when available.
4. Pass all retrieved diff content and file inventory to `code-review`; it owns generic review ordering, large-review chunking, and dependency tracing.

---

### Step 5 — Invoke Code Review Core

Invoke the [code-review](../code-review/SKILL.md) skill with this PR/MR-specific input wrapper before doing any review analysis:

```yaml
submission:
  type: pull-request   # or merge-request, based on detected provider
  title: "{pr_mr_title}"
  description: "{pr_mr_description}"
  author: "{author}"
  source_ref: "{source_branch}"
  target_ref: "{target_branch}"
code_input:
  diff: "{provider_diff}"
  files: "{changed_file_inventory}"
  repository_path: ".worktrees/pr-review-{pr_mr_number}"
  review_baseline: "{review_baseline}"
review_context:
  existing_feedback: "{open_and_resolved_threads}"
  constraints: "Review every changed file. Do not modify files. Preserve provider diff coordinates for inline comments."
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

The `code-review` dependency MUST:

- Apply its full review workflow to all changed files.
- Return provider-neutral findings, report text, and comment bodies using its output interface.

Store the returned output as `code_review_result`. `code_review_result` is the only valid source for:

- Findings shown in Step 6.
- Comment bodies posted in Step 7-A.
- Request-changes summaries in Step 7-C.

If `code_review_result.chunking_required` is `true`, do not continue to the normal Step 6 report:

1. Present the warning from `code_review_result.report` and the structured `code_review_result.chunk_plan`.
2. Ask the user to confirm processing the first chunk, then end the response without further tool calls.
3. After confirmation, invoke `code-review` for only that chunk and state in `review_context.constraints` that chunking has already been established. Preserve the original file order, diff coordinates, repository context, and existing feedback.
4. Present that chunk's report, identify its position in the plan, and ask for confirmation before processing the next chunk. Do not post comments, approve, or request changes until all confirmed chunks have been reviewed and their results retained.
5. After the final chunk, combine the chunk results without reclassifying or rewriting them: sum totals, concatenate findings and `comment_bodies`, order findings by severity then file path, combine residual gaps, and retain each rendered finding block verbatim in the aggregate `report`. Store the aggregate as `code_review_result`, then continue to Step 6.

If the user declines or stops chunking, proceed to Step 8 only after they explicitly choose report-only/stop; report that the review is incomplete and list the unreviewed chunks.

Before moving to Step 6, perform this invariant check:

```text
Did I invoke/load code-review for this PR/MR, and are all findings/report/comment bodies copied from code_review_result?
```

If the answer is not yes, go back and invoke `code-review`. Do not continue by analyzing the PR/MR yourself.

---

### Step 6 — Review & Present Findings to the User

Present the findings returned by `code-review` to the user **before taking any action**.

The report must include:

- PR/MR title, source → target branch, author.
- Findings totals per severity.
- Findings ordered by severity, then file path.

Render each finding using the canonical chat format defined by [code-review](../code-review/SKILL.md#step-6--rubber-duck-and-render). Copy each rendered finding verbatim from `code_review_result.report`; do not recreate or alter its prefix or content.

If there are no findings, state that explicitly and mention any residual testing or review gaps.

**HARD STOP**: End the response immediately after presenting the findings and asking the user how they would like to proceed. Provide options naturally: discussing/refining findings, posting comments, approving the PR/MR, or requesting changes. Do NOT call any tools after presenting the report in that same response, and do NOT proceed until the user issues a clear directive in a later turn.

---

### Step 7 — Execute Chosen Action (Only When Confirmed)

Based on the user's instructions from Step 6, take the appropriate action. All sub-steps below branch on `provider` and use the already resolved `provider_route`. Do not ask for the preference again.

#### 7-A: Post Comments

Post all approved findings as visible inline comments on the PR/MR.

Use the `comment_bodies` map returned by `code-review` in Step 5 as the body for each inline comment, matched by finding `id`. Do not re-generate comment text.

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

- **CLI route:** Use authenticated `gh api` to create one pending review containing the approved inline comments, then submit it. Use `gh pr review` for approve/request-changes when it supports the requested action. Never use raw `curl`.
- **MCP route:** Start a pending review using the matching GitHub add-comment-to-pending-review tool for each finding.
  - Provide `owner`, `repo`, `pull_number`, `commit_id` (use `head_sha`), `path`, `line`, and `body`.
  - For multi-line findings, use `start_line` and `line` to span the range.
- Ensure the chosen `line` or range still belongs to the PR diff. If the exact target is not commentable on GitHub, move to the nearest stable diff line or fall back to a top-level PR comment.
- After all MCP comments are added, submit the pending review with event `COMMENT` and an empty or summary body.
- **Fallback**: If inline positioning fails, use `gh pr comment` on CLI or the GitHub top-level issue-comment tool on MCP, indicating the target file and line.

**GitLab**:

- Use `glab mr note create <mr> --file <path> --line <line> -m <body>` for added or modified lines.
- Use `--line <start>:<end>` for a supported multi-line range and `--old-line <line>` for a removed line.
- Use authenticated `glab api` only when the high-level command cannot represent a required position. For that fallback, provide `base_sha`, `start_sha`, and `head_sha` and map old/new paths and lines correctly. Never use raw `curl`.
- After any ambiguous failure, fetch current MR discussions before retrying and submit only missing comments.
- **Fallback**: If inline positioning fails, create a general MR note with `glab mr note create` and include the target file and line in the body.

#### 7-B: Approve

If the user requests approval, confirm there are no unresolved security violations first. If there are, explicitly confirm the user wants to proceed despite the risks.

**GitHub**: Submit an approving review through `gh pr review --approve` or the matching MCP review tool with event `APPROVE`.

**GitLab**: Approve the MR through `glab mr approve`.

#### 7-C: Request Changes

Formally mark the PR/MR as requiring changes.

**GitHub**: Submit a review through `gh pr review --request-changes` or the matching MCP review tool with event `REQUEST_CHANGES` and a summary covering the key findings.

**GitLab**: Proceed in two distinct steps. Execute these GraphQL operations through authenticated `glab api graphql`.

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

If the user wants no action taken, proceed to Step 8 — Cleanup. If they want to refine, discuss the findings, update them, and repeat Step 6.

---

### Step 8 — Clean Up

Prerequisite: Step 8 must never run in the same response as Step 6. Execute it only after Step 7 is complete, or after the user explicitly says to stop at reporting only.

This step is always executed, regardless of which option was chosen in Step 6.

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

Use the canonical formats defined by [code-review](../code-review/SKILL.md#finding-format-rules). Do not maintain a separate finding template in this skill.

Differences by destination:

- In chat, copy the rendered finding blocks verbatim from `code_review_result.report`.
- In posted comments, use the corresponding entries from `code_review_result.comment_bodies` verbatim.

Style rules:

- See [code-review](../code-review/SKILL.md) Finding Format Rules for tone, heading, and language conventions.
- State exactly what was posted, including comment or note IDs when available.
- If a fallback path was used, explain why in one sentence.

## Guardrails

- Never merge, alter code, or use API tools from the wrong provider.
- Do not use raw `curl` for provider API interactions. Use `gh`, `glab`, or the matching MCP route. Use `git` only for local repository/worktree operations.
- After an ambiguous remote write failure, reconcile published reviews/comments through the same route before retrying. Never silently switch routes and duplicate a mutation.
- Keep findings tied to concrete diff evidence from the branch worktree.
- If the workflow is interrupted (user cancels, agent crashes), manually run `git worktree prune` to clean orphaned entries and recover disk space.
