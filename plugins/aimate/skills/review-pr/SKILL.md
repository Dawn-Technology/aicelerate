---
name: review-pr
description: Review a GitHub or GitLab Pull/Merge Request and provide findings, and post structured review comments with issue explanation plus code fixes. Use this skill when asked to review a GitHub Pull Request or GitLab Merge Request.
metadata:
  author: "Martin Roest <martin.roest@dawn.tech>"
  version: 4.0.0
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

### Step 3 — Gather Codebase Context

With the branch checked out, use `runSubagent` (`Explore` agent) to analyze the project conventions relevant to the proposed changes. To avoid wasting time on large monorepos, direct the subagent specifically. Use a prompt similar to:

> "Explore the `.worktrees/pr-review-{pr_mr_number}` directory. Focus primarily on the modules and adjacent dependencies affected by the PR/MR diff, while briefly checking for global configs (e.g., framework config, `README`, linting configs, `.github/copilot-instructions.md`). Report: language, framework, architectural patterns, naming conventions, and test strategy relevant to the changed files."

Store the subagent's full response as your **review baseline** for code analysis.

**Fallback if conventions are unclear**: Infer standards from the detected language/framework:

- **PHP**: PSR-12, PSR-4 (autoloading).
- **Python**: PEP 8, type hints (PEP 484).
- **JavaScript/TypeScript**: ESLint, Google/Airbnb style guides.
- **Go**: `gofmt`, idiomatic Go patterns.
- If still unclear, note this assumption in the final report and apply general best practices (SOLID, DRY, KISS).

---

### Step 4 — Retrieve, Parse, and Trace the Diff

1. Retrieve the diffs between the source and target branches using the MCP tools for `provider`.
2. Build a file-change inventory: list each changed file with its change type (added / modified / deleted). **All changed files MUST be reviewed**; do not skip any files.
3. Prioritise the review order to build context progressively:
   - **High priority**: core business logic, security-sensitive code, public APIs, data models.
   - **Lower priority**: generated files, lock files, migration snapshots, test fixtures.
   - **Within each tier, sort files alphabetically by path** to guarantee a deterministic traversal order.
4. **Context Constraints (Large PRs/MRs)**: If the PR/MR contains more than 15 changed files or massive diffs, warn the user. Propose reviewing the changes in chunks of 5 files at a time to maintain high-quality analysis. Ask for confirmation before processing the chunks.
5. **Trace Control Logic and Impact**: Do not evaluate diffs in isolation.
   - For changes in logic, read the expanded surrounding context or the full file to grasp the complete execution path.
   - Actively trace dependencies by exploring where modified functions, classes, or variables are invoked across the codebase (e.g., using codebase search capabilities or the `Explore` subagent).
   - Evaluate cross-file execution paths to definitively determine the impact and identify potential downstream breakages.

---

### Step 5 — Analyze & Classify Findings

Evaluate the diff against these four lenses using your analytical capabilities:

1. **Security (OWASP Top 10)**: Injection flaws, exposed credentials, auth bypasses. Confirm patterns are reachable. (Severity: Security violation)
2. **Correctness & Logic**: Incorrect conditionals, missing error handling, off-by-one errors. (Verify control-flow boundaries). (Severity: Request for Change)
3. **Architecture & Maintainability**: SOLID violations, naming conventions against the baseline, breaking API contracts. (Severity: Request for Change or Optional)
4. **Scope & Consistency**: Unaddressed feedback from existing threads, missing translations, description alignment. (Severity: Request for Change)

**Finding Schema & Rules**:
Only report findings with tangible evidence (do not report without validation). To ensure strict adherence to the schema, organize your findings internally using the following schema. **CRITICAL: Do NOT print this JSON schema to the chat.** Use it purely as an internal data structure to ensure you have collected all required fields, then proceed to format the output as requested in Step 6.

```json
[
  {
    "id": "<file-path>:<new_line>:<rule-slug>",
    "file": "path/to/file.ext",
    "line": "<precise line number from diff>",
    "severity": "optional | request-for-change | security-violation",
    "category": "<one of the 4 lenses>",
    "title": "<short constructive label>",
    "observation": "<1-2 sentences>",
    "suggestion": "<code block or instruction>"
  }
]
```

---

### Step 6 — Present Findings to the User

Present the grouped findings report to the user **before taking any action**.

The report must include:

- PR/MR title, source → target branch, author.
- Finding totals per severity.
- Each finding formatted exactly using the **Comment Template** defined below, prefixed with a reference ID (e.g., `**Finding #1 — src/Auth.php:88:sql-injection**`).

**HARD STOP**: Pause here and ask the user how they would like to proceed. Provide options naturally: discussing/refining findings, posting comments, approving the PR/MR, or requesting changes. Do NOT proceed until the user issues a clear directive.

---

### Step 7 — Execute Chosen Action (Only When Confirmed)

Based on the user's instructions from Step 6, take the appropriate action. All sub-steps below branch on `provider`.

#### 7-A: Post Comments

Post all approved findings as visible inline comments on the PR/MR.

**GitHub**:

- Start a pending review using `mcp_github_add_comment_to_pending_review` for each finding.
  - Provide `owner`, `repo`, `pull_number`, `commit_id` (use `head_sha`), `path`, `line`, and `body`.
  - For multi-line findings, use `start_line` and `line` to span the range.
- After all comments are added, submit the review using `mcp_github_pull_request_review_write` with `event: "COMMENT"` and an empty or summary `body`.
- **Fallback**: If inline positioning fails (the line is not part of the diff), fall back to a top-level PR comment using `mcp_github_add_issue_comment`, indicating the target file and line.

**GitLab**:

- Create draft notes using `mcp_gitlab_create_draft_note` in a loop for each finding.
  - You MUST provide `base_sha`, `start_sha`, and `head_sha` in the `position` object.
  - **Position Mapping**: Added/modified lines → `new_line` + `new_path`. Deleted lines → `old_line` + `old_path`. Set `position_type: "text"`.
- After all draft notes are created, publish them in a single batch with `mcp_gitlab_bulk_publish_draft_notes`. The user expects published notes, not drafts.
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

If the user wants no action taken, proceed to Step 8 — Cleanup. If they want to refine, discuss the findings, update them, and repeat Step 6.

---

### Step 8 — Clean Up

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

## Comment Template

Keep finding descriptions simple, conversational, and direct. Do not use structural headers (like "Observation:" or "Impact:"). Use the following flow for every finding:

1. **Title**: Short constructive topic (e.g., `**Avoid repeated magic string**`).
2. **Observation & Impact**: Briefly explain what you noticed and why it matters in 1-2 sentences. Use a peer-to-peer tone (e.g., "I noticed", "Have we considered").
3. **Context**: Relevant file path and exact line references in italics.
4. **Suggested approach**: A polite, actionable recommendation, ideally with a suggested code block or concise instructions.

Do not invent alternative formats or omit any field. In the chat report, prefix with `**Finding #N — <id>**` (strip the prefix when posting to GitHub or GitLab).

**Example:**

````text
**Avoid repeated magic string**

I noticed that `"pending"` is hardcoded in multiple places. If the status name changes, missing a spot would cause inconsistent behavior.

*Relevant lines: `src/Service/OrderService.php` around line 42 and `src/Handler/CheckoutHandler.php` around line 17*

Could we extract it to a constant? Something like:

```php
// define once
const STATUS_PENDING = 'pending';

// use everywhere
if ($order->getStatus() === self::STATUS_PENDING) {
    // handle pending state
}
```

_Use the same language as the changed file in the suggestion block._
````

## Output Style for chat

- Keep summary concise.
- State exactly what was posted (comment/note IDs when available) and on which platform.
- If a fallback path was used, explain why in one sentence.

## Guardrails

- Never merge, alter code, or use API tools from the wrong provider (e.g., do not use GitLab MCP tools on a GitHub PR).
- Do not use raw `curl` or `git` CLI commands for provider API interactions; use MCP tools only.
- Keep findings tied to concrete diff evidence from the branch worktree.
- If the workflow is interrupted (user cancels, agent crashes), manually run `git worktree prune` to clean orphaned entries and recover disk space.
