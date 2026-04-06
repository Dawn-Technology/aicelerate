---
name: gitlab-mr-review
description: Review a GitLab Merge Request and provide findings, and post structured review comments with issue explanation plus code fixes. Use this skill when asked to review a Gitlab Merge request.
metadata:
  author: "Martin Roest <martin.roest@dawn.tech>"
  version: 3.6.1
---

# GitLab MR Review Workflow Skill

## Purpose

The purpose of this skill is to provide constructive and comprehensive feedback on code changes. The primary goals are:

- **Quality Assurance**: Identify bugs, potential logic errors, and edge cases.
- **Maintainability**: Ensure code is readable, modular, and consistent with the existing architecture.
- **Security**: Detect common security vulnerabilities and privacy risks. Validate against OWASP Top 10 where applicable.
- **Education**: Provide explanations and context for suggested changes to help the author grow.

This workflow is **read-first** and **non-invasive**:

- Do not modify repository files.
- Analyze MR content and discussions.
- Post comments, update MR only when explicitly requested.

## Inputs Required

1. **MR identifiers**: Either an MR URL or `{project_id, merge_request_iid}`

---

## Workflow

Follow these steps in order. Do not skip a step.

### Step 0 — Verify Capabilities

Before proceeding, verify you have GitLab integration capabilities available (reading MRs, reading discussions, fetching diffs, leaving review notes, executing GraphQL). You also require terminal access to checkout git worktrees.

- If GitLab capabilities are missing, stop immediately and ask the user to install the GitLab MCP server: https://github.com/zereight/gitlab-mcp/tree/main

---

### Step 1 — Fetch GitLab MR Details

Retrieve all MR metadata needed for the review.

1. Fetch the MR details using your GitLab capabilities.
   - Extract: title, description, source/target branches, author, labels, milestone, diff refs (`base_sha`, `start_sha`, `head_sha`).
   - **Note diff refs**: These are required in Step 7-A for inline comment positioning.
2. Fetch existing MR discussions and review threads.
   - Note all open and resolved threads to avoid posting duplicate feedback AND to systematically verify if the requested changes have been implemented in the latest code.
3. Note the MR description for stated intent, linked issues, and breaking-change flags.

---

### Step 2 — Checkout MR Branch

Use `run_in_terminal` to create an isolated worktree — even if the source branch is already checked out locally. **The purpose of this isolated worktree is to allow you to understand the full codebase, thoroughly trace control logic across files, and evaluate the true architectural impact of the proposed changes.**

```bash
git fetch origin {source_branch}
git worktree add .worktrees/mr-review-{merge_request_iid} {source_branch}
```

Store `worktree_path = ".worktrees/mr-review-{merge_request_iid}"` for Steps 3–5. **Read-only enforced** — do not modify files in the worktree.

---

### Step 3 — Gather Codebase Context

With the MR branch checked out, use `runSubagent` (`Explore` agent) to analyze the project conventions relevant to the proposed changes. To avoid wasting time on large monorepos, direct the subagent specifically. Use a prompt similar to:

> "Explore the `.worktrees/mr-review-{merge_request_iid}` directory. Focus primarily on the modules and adjacent dependencies affected by the MR diff, while briefly checking for global configs (e.g., framework config, `README`, linting configs, `.github/copilot-instructions.md`). Report: language, framework, architectural patterns, naming conventions, and test strategy relevant to the changed files."

Store the subagent's full response as your **review baseline** for code analysis.

**Fallback if conventions are unclear**: Infer standards from the detected language/framework:

- **PHP**: PSR-12, PSR-4 (autoloading).
- **Python**: PEP 8, type hints (PEP 484).
- **JavaScript/TypeScript**: ESLint, Google/Airbnb style guides.
- **Go**: `gofmt`, idiomatic Go patterns.
- If still unclear, note this assumption in the final report and apply general best practices (SOLID, DRY, KISS).

---

### Step 4 — Retrieve, Parse, and Trace the Diff

1. Retrieve the diffs between the source and target branches using your GitLab capabilities.
2. Build a file-change inventory: list each changed file with its change type (added / modified / deleted). **All changed files MUST be reviewed**; do not skip any files.
3. Prioritise the review order to build context progressively:
   - **High priority**: core business logic, security-sensitive code, public APIs, data models.
   - **Lower priority**: generated files, lock files, migration snapshots, test fixtures.
   - **Within each tier, sort files alphabetically by path** to guarantee a deterministic traversal order.
4. **Context Constraints (Large MRs)**: If the MR contains more than 15 changed files or massive diffs causing context limits, warn the user. Propose reviewing the changes in chunks of 5 files at a time to maintain high-quality analysis. Ask for confirmation before processing the chunks.
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

- MR title, source → target branch, author.
- Finding totals per severity.
- Each finding formatted exactly using the **Comment Template** defined below, prefixed with a reference ID (e.g., `**Finding #1 — src/Auth.php:88:sql-injection**`).

**HARD STOP**: Pause here and ask the user how they would like to proceed. Provide options naturally: discussing/refining findings, posting comments, approving the MR or requesting changes. Do NOT proceed until the user issues a clear directive.

---

### Step 7 — Execute Chosen Action (Only When Confirmed)

Based on the user's instructions from Step 6, take the appropriate action:

#### 7-A: Post Comments

Post all approved findings as visible inline notes on the MR. First, create them using `create_draft_note` in a loop, and then IMMEDIATELY publish the batch using `bulk_publish_draft_notes`.

- You MUST provide `base_sha`, `start_sha`, and `head_sha` in the `position` object.
- **Position Mapping**: If commenting on an added/modified line, use `new_line` and `new_path`. For deleted lines, use `old_line` and `old_path`. Set `position_type: "text"`.
- **Publishing**: After all notes are successfully created, you MUST call `bulk_publish_draft_notes`. The user expects published notes, not drafts.
- **Fallback**: If inline positioning fails (e.g., "Line is out of bounds" error), catch the error gracefully and fall back to posting a general MR discussion note (using `create_merge_request_discussion_note`) that indicates the target file and line.

#### 7-B: Approve

If the user requests approval, approve the MR via the GitLab MCP. If there are security violations, confirm the user explicitly wants to approve despite the risks.

#### 7-C: Request Changes

If the user wishes to formally request changes, proceed in two distinct steps.

**Step 1 — Verify reviewer assignment (separate check)**

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

_Note: `mergeRequestRequestChanges` requires GitLab 17.10+ (added February 2026). On older instances it may not exist — inspect the `errors` array and inform the user if the mutation fails. Pass the full project path and MR IID as GraphQL variables._

#### 7-D/E: Refine or Report Only

If the user wants no action taken, proceed to step 8 - cleanup. If they want to refine, discuss the findings, update them, and repeat Step 6.

---

### Step 8 — Clean Up

This step is always executed, regardless of which option was chosen in Step 6.

1. **Remove the git worktree with verification**:

   ```bash
   git worktree remove .worktrees/mr-review-{merge_request_iid} --force
   ```

2. **Report back** to the user:
   - **For Report only (option 1)**: Confirm findings were presented; no actions taken.
   - **For Posted comments/approval/request-changes**: Published note IDs, approval state (if applicable), MR state change (if applicable) and include summary with key findings.
   - If any fallback path was used, explain why in one sentence.
   - If worktree cleanup failed, notify the user to run `git worktree prune` manually.

---

## Comment Template

Keep finding descriptions simple, conversational, and direct. Do not use structural headers (like "Observation:" or "Impact:"). Use the following flow for every finding:

1. **Title**: Short constructive topic (e.g., `**Avoid repeated magic string**`).
2. **Observation & Impact**: Briefly explain what you noticed and why it matters in 1-2 sentences. Use a peer-to-peer tone (e.g., "I noticed", "Have we considered").
3. **Context**: Relevant file path and exact line references in italics.
4. **Suggested approach**: A polite, actionable recommendation, ideally with a suggested code block or concise instructions.

Do not invent alternative formats or omit any field. In the chat report, prefix with `**Finding #N — <id>**` (strip the prefix when posting to GitLab).

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
- State exactly what was posted (thread IDs/note IDs when available).
- If a fallback path was used, explain why in one sentence.

## Guardrails

- Never merge, alter code, or use alternate providers (GitHub, Jira, etc.).
- Do not use raw `curl` or `git` CLI commands for GitLab API interactions; use MCP tools only.
- Keep findings tied to concrete diff evidence from the branch worktree.
- If the workflow is interrupted (user cancels, agent crashes), manually run `git worktree prune` to clean orphaned entries and recover disk space.

## Completion Checklist

- [ ] **Step 0**: Capabilities verified
- [ ] **Step 1**: MR metadata fetched (title, branches, diff refs, author), discussions loaded
- [ ] **Step 2**: Worktree created at `.worktrees/mr-review-{merge_request_iid}`
- [ ] **Step 3**: Codebase context gathered, conventions documented
- [ ] **Step 4**: Diff parsed, files prioritised, high/low priority files identified
- [ ] **Step 5**: Diff analyzed against the four lenses and compiled into structured findings
- [ ] **Step 6**: Report presented to user, action confirmed
- [ ] **Step 7**: Appropriate sub-procedure executed (7-A/B/C/D/E)
- [ ] **Step 8**: Worktree removed, summary reported to user
