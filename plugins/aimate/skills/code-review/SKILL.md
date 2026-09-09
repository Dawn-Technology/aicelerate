---
name: code-review
description: Reusable review core for structured findings on supplied code or diffs. Invoked by review-pr and review-local; not for reviewing a PR/MR or local working tree directly, use those skills instead.
metadata:
  author: "Piotr Ramotowski <piotr.ramotowski@dawn.tech>"
  version: 1.1.0
  role: "reusable-review-core"
  dependencies: []
---

# Code Review Core Skill

## Purpose

Provide constructive and comprehensive feedback on code changes. The primary goals are:

- **Quality Assurance**: Identify bugs, potential logic errors, and edge cases.
- **Maintainability**: Ensure the change is readable, well decomposed, and consistent with the existing architecture, so the next change to this code stays cheap. SOLID, clean code, and DRY/KISS/YAGNI are lenses for finding that cost, not rules to enforce for their own sake.
- **Security**: Detect common security vulnerabilities and privacy risks. Validate against OWASP Top 10 where applicable.
- **Education**: Provide explanations and context for suggested changes to help the author grow.

This skill is **read-first**, **framework-agnostic**, and **non-invasive**:

- Do not modify repository files.
- Analyze the supplied code, diff, patch, commit, snippet, or changed files.
- Return structured findings and formatted review text to the caller.
- Leave provider-specific actions, posting comments, approvals, commits, or state changes to the calling skill.

## Input Interface

The calling skill or user request must provide as much of this context as is available:

```yaml
submission:
  type: pull-request | merge-request | commit | patch | diff | snippet | local-scope
  title: optional short title
  description: optional intent, linked issues, or acceptance criteria
  author: optional author
  source_ref: optional branch, commit, file path, or snippet label
  target_ref: optional base branch, previous commit, or comparison target
code_input:
  diff: optional unified diff or provider diff
  files: optional changed file list with added / modified / deleted status
  snippets: optional code snippets with language and path hints
  repository_path: optional local checkout path
  review_baseline: optional project conventions already gathered by caller
review_context:
  existing_feedback: optional prior comments, review threads, or known unresolved findings
  constraints: optional user or repository constraints
  focus_areas: optional requested focus such as security, performance, tests, docs
  output_target: chat | inline-comments | report | calling-skill
```

Minimum viable input:

- For diffs, commits, patches, PRs, and MRs: a diff plus enough repository context to inspect adjacent code.
- For snippets: the snippet text plus language or framework hints when available.
- For local scopes: the file/folder/change scope and the repository path.

## Output Interface

Return review output to the caller in this shape:

```yaml
chunking_required: optional boolean; true only when review is deferred pending caller or user confirmation
chunk_plan:
  - chunk: sequential number
    files: ordered list of up to 5 file paths
summary:
  submission: short description of reviewed input
  scope: reviewed files, snippets, or change set
  residual_gaps: optional review gaps, missing context, or tests not run
totals:
  security-violation: number
  request-for-change: number
  optional: number
findings:
  - id: path/to/file:123:rule-slug
    severity: security-violation | request-for-change | optional
    category: syntax | logic | security | style | documentation | maintainability | scope-consistency
    title: short constructive label
    body: 1-2 sentences describing the issue and why it matters
    location:
      file: path/to/file
      line: precise line number or diff coordinate when available
      line_type: added | deleted | context | unknown
    suggestion: optional code block or concise remediation guidance
report: formatted chat-ready findings report
comment_bodies: provider-neutral comment text keyed by finding id; always present when output_target is calling-skill or inline-comments, omitted otherwise
```

`chunk_plan` is required when `chunking_required` is `true` and omitted otherwise. A chunking response is a preflight result, not a completed review: return zero totals, empty `findings`, an explanatory `report`, and an empty `comment_bodies` map when the output target requires it. Record why chunking was proposed in `summary.residual_gaps`; callers must use `chunk_plan`, rather than parse `residual_gaps`, to drive chunk execution.

Do not invent precise line numbers when they cannot be derived. Use the best available location and state the limitation in `residual_gaps`.

## Workflow

Follow these steps in order. Do not skip a step.

### Step 1 — Normalize Review Context

1. Identify `submission.type` and the available code input.
2. Determine whether the review is diff-based, full-file-based, snippet-based, or mixed.
3. Record the stated intent from the title, description, linked issues, user request, or existing feedback.
4. Note all open and resolved prior feedback to avoid duplicate findings and to verify whether previously requested changes have been addressed.

If the input is too ambiguous to review safely, ask the caller or user for the missing scope. If some context is missing but a useful review is still possible, continue and record the gap.

### Step 2 — Gather Codebase Context

Use the provided `review_baseline` when available. Otherwise, inspect the repository or supplied files enough to understand the project conventions relevant to the reviewed code:

- Language and framework.
- Architectural patterns and boundaries.
- Naming and style conventions.
- Error handling and validation patterns.
- Test strategy relevant to the changed files.
- Security-sensitive areas such as authentication, authorization, input parsing, secrets, or data access.

When using an exploration subagent, direct it specifically:

> "Explore the repository path or supplied files. Focus primarily on the modules and adjacent dependencies affected by the review scope, while briefly checking for global configs such as framework config, README, linting configs, and repository instructions. Report: language, framework, architectural patterns, naming conventions, and test strategy relevant to the changed files."

Fallback if conventions are unclear:

- **PHP**: PSR-12, PSR-4.
- **Python**: PEP 8, type hints where the project uses them.
- **JavaScript/TypeScript**: project ESLint/Prettier config first, otherwise common idioms.
- **Go**: `gofmt` and idiomatic Go patterns.
- If still unclear, note the assumption and apply general best practices such as SOLID, DRY, and KISS.

### Step 3 — Retrieve, Parse, and Trace the Reviewed Code

1. Build a file-change inventory: if a `files` list is provided in `code_input`, use it directly. Otherwise, list each changed or reviewed file with its change type when known. **All files in the requested scope MUST be reviewed**; do not skip files silently.
2. Prioritize the review order to build context progressively:
   - **High priority**: core business logic, security-sensitive code, public APIs, data models.
   - **Lower priority**: generated files, lock files, migration snapshots, test fixtures.
   - **Within each tier, sort files alphabetically by path** to guarantee deterministic traversal order.
3. For large reviews with more than 15 changed files or massive diffs, warn the caller or user. Propose reviewing the changes in chunks of 5 files at a time to maintain high-quality analysis, unless the caller has already established chunking. When `output_target` is `chat` or `report`, ask the user for confirmation before processing each chunk. When `output_target` is `calling-skill` or `inline-comments`, do not prompt the user directly — instead return the preflight response defined in the Output Interface with `chunking_required: true` and a deterministic `chunk_plan`, and let the calling skill handle user confirmation.
4. Do not evaluate diffs in isolation:
   - For logic changes, read the expanded surrounding context or the full file.
   - Trace dependencies by searching where modified functions, classes, routes, schemas, or variables are invoked.
   - Evaluate cross-file execution paths to determine downstream impact.

### Step 4 — Analyze by Review Module

Only report findings backed by concrete evidence from the diff, code, or nearby context.

#### Syntax Module

Check for parse errors, invalid language constructs, broken imports, type mismatches visible from the code, malformed config, and obvious build-breaking changes.

Use severity:

- `request-for-change` for build-breaking or runtime-breaking syntax problems.
- `optional` only for low-risk cleanup that does not block execution.

#### Logic Module

Check for incorrect conditions, missing error handling, boundary mistakes, invalid state transitions, broken assumptions, concurrency issues, data loss, and unhandled null/empty/error cases.

Use severity:

- `request-for-change` for reachable correctness problems.
- `optional` for defensive improvements when no concrete failure is demonstrated.

#### Security Module

Check for injection flaws, exposed credentials, auth bypasses, authorization gaps, unsafe deserialization, path traversal, SSRF, XSS, CSRF, insecure randomness, sensitive logging, privacy risks, and OWASP Top 10 issues where applicable.

Use severity:

- `security-violation` only for reachable or plausibly reachable security issues.
- `request-for-change` for security-relevant hardening that blocks safe release but is not an immediate violation.
- Avoid speculative security findings without a clear attack path.

#### Style and Maintainability Module

Maintainability is the cost of the *next* change. Judge whether a competent teammate who has never seen this code could read it, find the behavior they need to change, change it in one place, and be confident they broke nothing else. Every finding in this module must trace back to that cost.

Apply the lenses below to what the change actually engages, and skip the rest silently. They are prompts for where to look, not a checklist to walk.

- **Decomposition and cohesion**: Does each function or method do one identifiable job, at one level of abstraction? Look for long bodies, deep nesting, long parameter lists, flag parameters that hide two behaviors in one function, and mixed concerns such as I/O, business rules, and formatting in the same block. Name the seam the code is missing rather than prescribing a rewrite.
- **SOLID, applied with judgment**:
  - *Single responsibility*: does this unit have more than one reason to change, so unrelated work keeps landing in the same place?
  - *Open/closed*: does adding the next variant mean editing a growing `switch`/`if` chain that enumerates known types?
  - *Liskov*: do subtypes and implementations honor the contract they stand in for, without strengthened preconditions, `not supported` throws, or quietly different semantics?
  - *Interface segregation*: are callers forced to depend on, implement, or mock members they never use?
  - *Dependency inversion*: does policy or domain logic reach directly for a concrete detail such as the clock, filesystem, HTTP client, ORM, or a global singleton, in a way that hard-wires it and blocks testing?
- **Clean code signals**: intention-revealing names, comments that explain *why* instead of restating *what*, dead or commented-out code, leftover debug output, magic numbers and strings that deserve a name, primitive obsession where a domain type already exists, and error handling that swallows or loses context.
- **Duplication and coupling**: distinguish duplicated *knowledge*, one rule that must change in lockstep in several places, from code that merely looks alike. De-duplicating coincidental similarity introduces worse coupling than it removes. Also watch for a change that reaches across an architectural boundary the codebase otherwise respects.
- **Complexity budget**: abstraction, indirection, configuration, or generality added for a requirement that does not exist yet. Speculative flexibility is a maintainability cost, not a virtue.
- **Consistency with the codebase**: established project patterns outrank textbook purity. Introducing a second way to do something the codebase already does one way is itself the finding. Conversely, do not fault code for following a convention you would have chosen differently.

Reporting bar for this module:

- Report the cost, not the principle. "This function mixes retry policy with request building, so changing the retry rules means re-testing serialization" lands; "violates SRP" does not. Name a principle only as shorthand after the concrete explanation.
- Point at the seam, not the redesign. Suggest the smallest change that removes the cost.
- Stay inside the submitted scope. Do not ask the author to refactor code they only touched incidentally, unless their change makes an existing problem materially worse.
- Thresholds are signals, not findings. Line counts, parameter counts, and nesting depth tell you where to look; the finding still has to be a real readability or change-cost problem in this code.
- One finding per underlying cause, even when several lenses flag the same spot.

Use severity:

- `request-for-change` when the change breaks a contract or public API, entrenches a pattern the codebase will have to unpick later, makes behavior genuinely hard to follow, or is likely to cause a future defect.
- `optional` for improvements a reasonable author could decline: naming, local restructuring, cosmetic consistency, and principle-based preferences where the current code still reads and behaves correctly.
- No finding at all when the only complaint is taste.

#### Documentation and Scope Module

Check missing or stale docs, comments that contradict behavior, missing tests for behavior changes, missing translations, unaddressed prior feedback, and mismatch between the submitted changes and stated intent.

Use severity:

- `request-for-change` when missing documentation, tests, or scope alignment blocks confident review.
- `optional` for helpful but non-blocking documentation improvements.

### Step 5 — Classify Findings

For each finding, capture these fields internally:

- `id`: stable identifier such as `path/to/file:123:rule-slug`
- `severity`: `security-violation`, `request-for-change`, or `optional`
- `category`: `syntax`, `logic`, `security`, `style`, `documentation`, `maintainability`, or `scope-consistency`
- `title`: short constructive label
- `body`: 1-2 sentences describing the issue and why it matters
- `location`: file path and line reference from the diff or reviewed code
- `suggestion`: optional code block or concise remediation guidance

Order findings by severity, then file path.

### Step 6 — Rubber-Duck and Render

Before returning findings, critique them:

- Is each finding backed by concrete evidence?
- Is the location actionable by the caller?
- Is the severity justified?
- Is the finding new, or does it duplicate existing feedback?
- Is the suggested fix compatible with the local codebase patterns?
- For maintainability findings: does the body name a concrete cost to a future change, or is it a principle citation dressed up as evidence? Rewrite or drop the latter.

Then deliver output based on `output_target`:

- **`calling-skill`**: Return the structured output interface (summary, totals, findings, report, comment_bodies) to the calling skill. Do not render to chat.
- **`inline-comments`**: Return `comment_bodies` keyed by finding id; omit the chat render.
- **`chat`** or **`report`**: Render the report to the user in the format below.

If there are findings, use this chat format:

`**Finding #N — <id> <severity>**`

`**<title>**`

`<body>`

`*Relevant lines: <file path and line reference>*`

`Suggested approach: <suggestion or concise remediation guidance>`

If there are no findings, state that explicitly and mention any residual testing or review gaps.

## Finding Format Rules

Use the same finding content for chat and provider-neutral comment bodies.

Differences by destination:

- In chat, include the `Finding #N — <id> <severity>` prefix.
- In posted comments, omit the prefix and keep the rest unchanged.

Style rules:

- Keep the tone direct and peer-to-peer.
- Do not use extra headings like `Observation:` or `Impact:`.
- Use the changed file's language in code suggestions.
- Keep summaries short and factual.
- Do not claim that tests, builds, or tools passed unless they were actually run.

## Guardrails

- Never merge, alter code, commit, approve, request changes, or post provider comments from this core skill.
- Keep findings tied to concrete evidence from the supplied code and available context.
- Do not use provider-specific API tools from this skill; return provider-neutral output to the caller.
- Respect caller constraints about scope, chunking, and output target.
