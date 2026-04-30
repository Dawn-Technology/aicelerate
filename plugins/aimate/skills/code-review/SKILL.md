---
name: code-review
description: Use when reviewing code changes or code samples and you need structured findings about correctness, security, maintainability, style, or documentation across pull requests, merge requests, commits, patches, diffs, or snippets.
metadata:
  author: "Martin Roest <martin.roest@dawn.tech>"
  version: 1.0.0
  role: "reusable-review-core"
---

# Code Review Core Skill

## Purpose

This skill provides the reusable core for code review. It is framework-agnostic and can be applied to:

- Pull requests and merge requests
- Commits and commit ranges
- Patches and unified diffs
- Changed working trees
- Standalone code snippets or files

The primary goals are:

- **Quality Assurance**: Identify bugs, logic errors, broken assumptions, and edge cases.
- **Maintainability**: Ensure code is readable, modular, and consistent with surrounding conventions.
- **Security**: Detect common vulnerabilities and privacy risks. Validate against OWASP Top 10 where applicable.
- **Education**: Provide actionable, constructive feedback with enough context for the author to improve the code.

This skill is **read-first** and **non-invasive**:

- Do not modify repository files as part of the review.
- Analyze only the provided code submission and surrounding context.
- Produce findings in a structured, reusable format that wrapper skills can present or publish.

## Dependency Contract

Wrapper skills such as `review-pr` should invoke this skill after gathering submission-specific metadata and code input. This skill owns the review logic. Wrapper skills should own transport-specific work such as:

- Identifying the source system
- Fetching code or diff data
- Creating worktrees or other local context
- Posting comments, approvals, or change requests back to the platform

## Input Interface

Users do not need to provide a formal structure directly. This section defines the recommended internal handoff format for wrapper skills and other callers.

Provide the review input in three parts.

### 1. Code Input

Provide at least one of:

- `diff`
- `patch`
- `changed_files`
- `snippets`
- `commit_range`

Recommended handoff format:

```yaml
code_input:
  submission_type: pull-request | merge-request | commit | commit-range | patch | diff | snippet | working-tree
  diff: "<unified diff or provider diff text>"
  changed_files:
    - path: src/example.ts
      change_type: modified
      patch_excerpt: "<optional>"
  snippets:
    - path: src/example.ts
      language: typescript
      content: |
        export function example() {}
  worktree_path: .worktrees/pr-review-123
```

### 2. Context Parameters

Use as many of these fields as are available:

```yaml
context:
  title: "Add retry logic to webhook delivery"
  description: "Implements retries for transient failures"
  author: "example-user"
  source_ref: "feature/retries"
  target_ref: "main"
  provider: github | gitlab | local | manual
  baseline_conventions: "<repo conventions, framework, test strategy>"
  existing_feedback:
    open_threads: []
    resolved_threads: []
  assumptions:
    - "Repository follows ESLint defaults when not stated otherwise"
  constraints:
    report_only: true
    comment_ready: true
```

### 3. Requested Review Scope

If the caller does not provide scope, review all modules below.

```yaml
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

## Output Interface

Return findings in a stable structure that wrapper skills can reformat or publish.

```json
{
  "summary": {
    "submission_type": "pull-request",
    "title": "Add retry logic to webhook delivery",
    "author": "example-user",
    "totals": {
      "security-violation": 0,
      "request-for-change": 2,
      "optional": 1
    }
  },
  "findings": [
    {
      "id": "src/example.ts:42:missing-error-guard",
      "file": "src/example.ts",
      "line": 42,
      "severity": "request-for-change",
      "category": "logic",
      "title": "Guard the retry loop against permanent failures",
      "observation": "The current loop retries every error, including validation failures that will never succeed. That can hide the real failure and delay recovery.",
      "suggestion": "Only retry transient errors and return immediately for permanent failures."
    }
  ]
}
```

`category` should use one of:

- `syntax`
- `logic`
- `security`
- `style`
- `documentation`
- `architecture`
- `scope-consistency`

## Workflow

Follow these steps in order. Do not skip a step.

### Step 1 — Validate Inputs

1. Confirm that at least one code input form is present.
2. Determine `submission_type`.
3. Note any missing context that materially weakens the review.
4. If only snippets are available, explicitly limit findings to what can be validated from the snippet alone.

### Step 2 — Establish Review Baseline

Build the standards you will review against.

1. If `baseline_conventions` are provided, use them.
2. If `worktree_path` is available, inspect nearby files and project-level configs relevant to the changed code.
3. If conventions remain unclear, infer by language/framework:
   - **PHP**: PSR-12, PSR-4
   - **Python**: PEP 8, type hints
   - **JavaScript/TypeScript**: project lint rules or established ecosystem conventions
   - **Go**: `gofmt`, idiomatic Go
4. Record assumptions so wrapper skills can disclose them if needed.

### Step 3 — Parse and Prioritize the Submission

1. Build a file-change inventory if one is not already provided.
2. Review all changed files; do not silently skip files.
3. Prioritize:
   - **High priority**: business logic, auth, security-sensitive flows, public APIs, data models
   - **Lower priority**: generated files, lock files, snapshots, fixtures
4. If the submission is very large, recommend chunking into smaller review batches before continuing.

### Step 4 — Trace Context Before Judging

Do not review diffs in isolation.

1. Read surrounding code where logic changes occur.
2. Trace call sites, dependencies, and downstream impacts when enough context is available.
3. Reconcile proposed changes with the stated intent in `title`, `description`, and prior feedback.
4. Avoid speculative findings that cannot be supported by the available evidence.

### Step 5 — Review by Module

Evaluate the submission through these modular lenses.

#### Syntax

- Invalid or fragile language constructs
- Type misuse
- Broken imports, signatures, or obvious compile/runtime hazards visible from the submission

#### Logic

- Incorrect conditionals
- Missing error handling
- Off-by-one issues
- State transitions that violate business rules
- Control-flow regressions

#### Security

- Injection flaws
- Authorization or authentication gaps
- Sensitive data exposure
- Unsafe deserialization, path handling, or command execution
- Reachability must be validated before reporting

#### Style

- Naming mismatches with local conventions
- Avoidable duplication
- Readability problems that materially increase maintenance risk
- Inconsistent patterns when surrounding code clearly establishes a standard

#### Documentation

- Missing doc updates for behavior changes
- Stale comments
- Missing migration or configuration notes
- Missing tests or examples when the change introduces a new contract

#### Optional extended modules

- **Architecture**: contract breakage, SOLID violations, coupling, boundary erosion
- **Scope consistency**: unaddressed review feedback, missing translations, mismatch between description and code

### Step 6 — Classify Findings

Only report findings with tangible evidence.

Use this internal schema:

```json
[
  {
    "id": "<file-path>:<line>:<rule-slug>",
    "file": "path/to/file.ext",
    "line": "<precise line number>",
    "severity": "optional | request-for-change | security-violation",
    "category": "syntax | logic | security | style | documentation | architecture | scope-consistency",
    "title": "<short constructive label>",
    "observation": "<1-2 sentences>",
    "suggestion": "<code block or instruction>"
  }
]
```

Severity rules:

- `security-violation`: reachable security or privacy issue
- `request-for-change`: correctness, logic, contract, or maintainability problem that should block approval
- `optional`: worthwhile improvement that should not block approval on its own

### Step 7 — Format the Review Output

Present results in two layers:

1. **Structured output** using the output interface above
2. **Human-facing findings** using the comment template below

If no validated findings are present, say so explicitly and mention any review limits such as missing context or unreviewed generated files.

## Comment Template

Keep finding descriptions simple, conversational, and direct. Do not use structural headers like "Observation" or "Impact". Use the following flow for every finding:

1. **Title**: Short constructive topic
2. **Observation & Impact**: Explain what you noticed and why it matters in 1-2 sentences
3. **Context**: Relevant file path and exact line references in italics
4. **Suggested approach**: A polite, actionable recommendation, ideally with a suggested code block or concise instructions

Example:

````text
**Avoid repeated magic string**

I noticed that `"pending"` is hardcoded in multiple places. If the status name changes, missing a spot would cause inconsistent behavior.

*Relevant lines: `src/Service/OrderService.php` around line 42 and `src/Handler/CheckoutHandler.php` around line 17*

Could we extract it to a constant? Something like:

```php
const STATUS_PENDING = 'pending';

if ($order->getStatus() === self::STATUS_PENDING) {
    // handle pending state
}
```
````

Use the same language as the changed file in suggestion blocks.

## Guardrails

- Never invent missing evidence.
- Never report an issue you cannot tie to the provided code or available context.
- Do not let style-only comments drown out correctness or security issues.
- Keep wrapper compatibility stable by preserving `severity`, `id`, and comment-ready finding structure.
