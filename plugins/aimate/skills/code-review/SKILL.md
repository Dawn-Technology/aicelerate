---
name: code-review
description: Reusable review core for structured findings on supplied code or diffs. Invoked by review-pr and review-local; not for reviewing a PR/MR or local working tree directly, use those skills instead.
metadata:
  author: "Piotr Ramotowski <piotr.ramotowski@dawn.tech>"
  version: 2.0.0
  role: "reusable-review-core"
  dependencies: []
---

# Code Review Core Skill

## Purpose

Provide constructive and comprehensive feedback on code changes. The primary goals are:

- **Quality Assurance**: Check changed behavior against stated intent and existing contracts to identify bugs, logic errors, and edge cases.
- **Maintainability**: Ensure the change is readable, well decomposed, and consistent with the existing architecture, so the next change to this code stays cheap. SOLID, clean code, and DRY/KISS/YAGNI are lenses for finding that cost, not rules to enforce for their own sake.
- **Security**: Detect common security vulnerabilities and privacy risks. Validate against OWASP Top 10 where applicable.
- **Actionable Feedback**: Provide enough reasoning and remediation guidance for a human or agent to evaluate and address each finding.

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
  files: optional changed file list with added / modified / deleted status and added / deleted line counts when known
  snippets: optional code snippets with language and path hints
  repository_path: optional local checkout path
  review_baseline: optional project conventions already gathered by caller
review_context:
  existing_feedback: optional prior comments, review threads, or known unresolved findings
  constraints: optional user or repository constraints
  focus_areas: optional requested focus such as security, performance, tests, docs
  output_target: chat | inline-comments | report | calling-skill
  chunk_context: # optional; present only for chunk execution or integration
    phase: chunk | integrate
    plan: effective chunk_plan for the agreed scope
    completed_results: ordered structured results from completed chunks
```

Minimum viable input:

- For diffs, commits, patches, PRs, and MRs: a diff plus enough repository context to inspect adjacent code.
- For snippets: the snippet text plus language or framework hints when available.
- For local scopes: the file/folder/change scope and the repository path.
- For chunk integration: the original file inventory and repository context, plus the effective plan and completed results in `chunk_context`. Full diffs need not be resent; inspect the relevant code when checking cross-file concerns.

## Output Interface

Return review output to the caller in this shape:

```yaml
chunking_required: optional boolean; true only when the change exceeds 1,500 counted lines and the caller must run the review chunk by chunk
confirm_scope: optional boolean; true only above 5,000 counted lines; confirm scope once before the first chunk unless full-scope review is already authorized
counted_lines: optional number; total counted lines, present when chunking_required is true
chunk_plan:
  - chunk: sequential number
    files: ordered list of file paths
    counted_lines: number of counted lines in this chunk
summary:
  submission: short description of reviewed input
  scope: reviewed files, snippets, or change set
  review_complete: boolean; false for preflight, per-chunk results, or incomplete coverage; true only for a completed normal review or integrated agreed scope
  residual_gaps: optional review gaps, missing context, or tests not run
  cross_file_context: compact contract facts and unresolved cross-file concerns with source locations; required for chunk results, omitted otherwise
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

`chunk_plan` and `counted_lines` are required when `chunking_required` is `true` and omitted otherwise; `confirm_scope` is omitted unless it is `true`. A chunking response is a preflight result, not a completed review: set `summary.review_complete: false` and return zero totals, empty `findings`, an explanatory `report`, and an empty `comment_bodies` map when the output target requires it. Record the counted line total and why chunking was needed in `summary.residual_gaps`; callers must use `chunk_plan` and `confirm_scope`, rather than parse `residual_gaps`, to drive chunk execution.

Do not invent precise line numbers when they cannot be derived. Use the best available location and state the limitation in `residual_gaps`.

## Workflow

Follow these steps in order. Do not skip a step.

### Step 1 — Normalize Review Context

1. Identify `submission.type` and the available code input.
2. Determine whether the review is diff-based, full-file-based, snippet-based, or mixed.
3. Establish the expected behavior and relevant constraints from the title, description, linked issues, user request, or existing feedback. Distinguish explicit requirements from assumptions; do not invent requirements where the request is silent.
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

Use these as fallback context, not mandatory standards, if conventions are unclear:

- **PHP**: PSR-12, PSR-4.
- **Python**: PEP 8, type hints where the project uses them.
- **JavaScript/TypeScript**: project ESLint/Prettier config first, otherwise common idioms.
- **Go**: `gofmt` and idiomatic Go patterns.
- If still unclear, note the assumption and use idiomatic language practices as context. Do not report an inferred style preference as a defect; SOLID, DRY, and KISS remain lenses for finding concrete costs.

### Step 3 — Retrieve, Parse, and Trace the Reviewed Code

For `chunk_context.phase: integrate`, verify that the completed results cover every file in the effective plan. If any chunk or file is missing, stop and return a partial structured result with `summary.review_complete: false`, the actual reviewed scope, and missing work in `residual_gaps`. Leave findings and comment bodies empty rather than publishing unreconciled candidates, and explain that the review is incomplete, not clean. Otherwise preserve any files excluded from the original scope as residual gaps and use the chunk summaries and relevant code for the cross-file checks in Step 4, rather than sizing or reviewing every file again.

For a normal or per-chunk review:

1. Build a file-change inventory: if a `files` list is provided in `code_input`, use it directly. Otherwise, list each changed or reviewed file with its change type when known. **All files in the requested scope MUST be reviewed**; do not skip files silently.
2. Prioritize the review order to build context progressively:
   - **High priority**: core business logic, security-sensitive code, public APIs, data models.
   - **Lower priority**: generated files, lock files, migration snapshots, test fixtures.
   - **Within each tier, sort files alphabetically by path** to guarantee deterministic traversal order.
3. Size the review by changed lines, not by file count. Review quality drops with the amount of changed code held at once; many files with small edits are an easy review, and splitting them apart hides cross-file bugs. Count the added plus deleted lines per file from the diff, or take them from `code_input.files` when the caller supplies them. With no diff, such as a folder or full-file review, count every line of the reviewed files. Leave lock files, generated files, vendored dependencies, minified bundles, and snapshot files out of the count; they are still reviewed. Then apply the first rule that matches:
   - **`chunk_context.phase` is `chunk`, or the caller has already established chunking**: review the files supplied for this chunk, using prior results as context and tracing adjacent dependencies when needed.
   - **1,500 counted lines or fewer**: review everything in one pass. Do not propose chunking or ask for size confirmation.
   - **More than 1,500 counted lines**: review in chunks, built deterministically. Group files by the directory that holds them, keeping each file with its tests and with the changed files that directly call it where the diff shows that. Order the groups by the priority in item 2, then pack them in order into chunks of at most 1,500 counted lines. Split a group only between files, never inside one; a single file over the limit is a chunk of its own. Files left out of the count go in the chunk of the group they belong to.

   The only size-related confirmation is a single question before the first chunk, and only above 5,000 lines: offer to narrow the scope or review every chunk. This limit does not prohibit clarifying missing input or unsafe ambiguity. Explicit authorization to proceed without size confirmation satisfies it; a generic request to review the change does not. When `output_target` is `chat` or `report`, follow the [chunked review protocol](#chunked-review-protocol) yourself. When `output_target` is `calling-skill` or `inline-comments`, do not prompt for size confirmation or review a chunk: return the preflight response defined in the Output Interface and let the calling skill execute that protocol.
4. Do not evaluate diffs in isolation:
   - For logic changes, read the expanded surrounding context or the full file.
   - Trace dependencies by searching where modified functions, classes, routes, schemas, or variables are invoked.
   - Trace affected normal, boundary, and failure paths across files against the expected behavior from Step 1 and relevant existing contracts. Look for both unmet requirements and regressions.

#### Chunked Review Protocol

Use this shared protocol for every chunked review; calling skills own execution, not analysis or aggregation:

1. If `confirm_scope` is true and proceeding without size confirmation has not been explicitly authorized, present the preflight warning and plan, ask once whether to narrow the scope or review every chunk, and end the response. Otherwise start immediately. If narrowed, keep an effective plan for the selected files and record the excluded files as unreviewed.
2. Review each chunk in plan order. Pass its files and diff, preserve the submission, repository baseline, source refs, existing feedback, and diff coordinates, and supply `chunk_context` with `phase: chunk`, the effective plan, and prior completed results. Retain each result, including its actual reviewed scope and `summary.cross_file_context`. Previous conclusions are context, not proof.
3. After every selected chunk is reviewed, invoke the core once with `phase: integrate`, the effective plan, all completed results, and the original file inventory and repository context. The core checks cross-file seams in Step 4 and reconciles findings in Step 5; this is not another full review.
4. Use only an integrated result with `summary.review_complete: true` as the final result. Do not concatenate rendered reports or sum pre-integration totals. Do not publish findings, approve, request changes, or pass a self-review gate before integration finishes. If stopped early, report the actual reviewed scope and unreviewed files instead of claiming completion.

### Step 4 — Analyze by Review Module

For chunk integration, check the established contracts and unresolved cross-file concerns against the affected producers, consumers, and tests. Inspect only the seams needed to resolve them. Recheck conflicting prior conclusions against code rather than carrying either forward automatically.

All review modules use the same reporting bar:

- Identify concrete evidence from the diff, code, or nearby context and the affected behavior, contract, or maintenance cost. Explain the consequence.
- Do not report taste, speculative improvements, or the mere absence of documentation or new tests. Optional findings still need an identifiable benefit and a proportionate fix.
- Distinguish a demonstrated problem from an unresolved assumption. Record missing evidence in `summary.residual_gaps`, or seek clarification when needed, rather than presenting uncertainty as a defect.
- Explain the smallest safe direction in the finding's `body` or `suggestion`. Include focused verification guidance when needed to evaluate the proposed fix. Keep the reasoning in review feedback; do not require a tutorial or additional source comments to teach the author.

Use the same severity standard across modules:

- `security-violation` for reachable or plausibly reachable vulnerabilities with a concrete attack path or sensitive-data exposure.
- `request-for-change` for demonstrated correctness failures, unsafe behavior, broken stated or existing contracts, or concrete maintenance hazards that materially obstruct safe changes. Name the affected behavior, contract, or change and its consequence; reviewer discomfort alone is not enough.
- `optional` for evidence-backed, non-blocking improvements with an identifiable benefit that a reasonable author could decline.

#### Syntax Module

Check for parse errors, invalid language constructs, broken imports, type mismatches visible from the code, malformed config, and obvious build-breaking changes.

#### Logic Module

Check for incorrect conditions, missing error handling, boundary mistakes, invalid state transitions, broken assumptions, concurrency issues, data loss, and unhandled null/empty/error cases.

Assess regression protection for the affected behavior as part of quality assurance. Check existing tests before reporting a coverage gap, and identify the specific changed behavior and failure risk that remain unprotected. Do not request new tests merely because behavior changed or no test file was added.

#### Security Module

Check for injection flaws, exposed credentials, auth bypasses, authorization gaps, unsafe deserialization, path traversal, SSRF, XSS, CSRF, insecure randomness, sensitive logging, privacy risks, and OWASP Top 10 issues where applicable.

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
- **Consistency with the codebase**: prefer established patterns unless there is a concrete reason to depart. Report inconsistency only when it introduces a demonstrated cost or violates an explicit project requirement. A justified simplification is not a defect merely because it differs, and an existing convention does not excuse a demonstrated correctness or safety problem.

Reporting bar for this module:

- Report the cost, not the principle. "This function mixes retry policy with request building, so changing the retry rules means re-testing serialization" lands; "violates SRP" does not. Name a principle only as shorthand after the concrete explanation.
- Point at the seam, not the redesign. Suggest the smallest change that removes the cost.
- Stay inside the submitted scope. Do not ask the author to refactor code they only touched incidentally, unless their change makes an existing problem materially worse.
- Thresholds are signals, not findings. Line counts, parameter counts, and nesting depth tell you where to look; the finding still has to be a real readability or change-cost problem in this code.
- One finding per underlying cause, even when several lenses flag the same spot.

#### Documentation and Scope Module

Check stale documentation or comments that contradict behavior, changed public or operational contracts, missing translations for changed user-visible content, prior feedback that still applies, and mismatch between the submitted changes and stated intent.

For unclear implementation, prefer clearer names, focused functions, explicit types or data, and simpler control flow over explanatory comments. Do not request comments that compensate for confusing code or narrate behavior already expressed by the code.

Report missing documentation only when you can identify an unmet public or operational contract, an explicit project requirement, or an important constraint that cannot reasonably be expressed in code. Name who relies on it and the concrete consequence of its absence. Preserve concise rationale for such constraints; do not remove useful documentation merely because code should be self-explanatory.

### Step 5 — Classify Findings

Build the canonical `findings` list using the field definitions in the Output Interface and the shared reporting and severity standard. This list is the only source for totals, report text, and comment bodies.

For chunk integration, reconcile the completed results before rendering:

- Merge findings with the same underlying cause, even if their ids or locations differ. Keep a representative cause location and id, and retain the evidence and smallest safe remediation needed to address that cause.
- Resolve contradictory claims and severities against the code. Drop invalidated findings and remove resolved gaps only when supported by evidence; preserve unresolved questions as residual gaps.
- Combine actual reviewed coverage and remaining gaps, then recompute totals from the final findings. Never add raw chunk totals or deduplicate by id alone.

Order findings by severity (`security-violation`, `request-for-change`, `optional`), then file path, line when known, and id. For a chunk result, include compact, source-backed contract facts and unresolved cross-file concerns in `summary.cross_file_context`; use an empty list when there are none.

### Step 6 — Rubber-Duck and Render

Before returning findings, critique them:

- Is each finding backed by concrete evidence?
- Is the location actionable by the caller?
- Is the severity justified by the shared standard, rather than a module-specific preference?
- Is the finding new, or does it duplicate existing feedback?
- Does the suggested fix fit the local codebase, or have a concrete reason to depart from its patterns?
- Does the body or suggestion give the smallest safe direction, with focused verification guidance where needed?
- For maintainability findings: does the body name a concrete cost to a future change, or is it a principle citation dressed up as evidence? Rewrite or drop the latter.

After critique, recompute totals and render `report` and any required `comment_bodies` from the final findings, never independently. Set `summary.review_complete` to true only when the agreed scope has been reviewed and any required integration has finished; per-chunk results remain false. Re-render after integration so numbering, totals, and comment keys match the reconciled list. Then deliver output based on `output_target`:

- **`calling-skill`** or **`inline-comments`**: Return the complete structured output interface, including `summary`, `totals`, `findings`, `report`, and `comment_bodies` keyed by finding id. Suppress chat rendering, not metadata; preflight responses use the same interface.
- **`chat`** or **`report`**: Render the report to the user in the format below.

If there are findings, use this chat format:

`**Finding #N — <id> <severity>**`

`**<title>**`

`<body>`

`*Relevant lines: <file path and line reference>*`

`Suggested approach: <suggestion or concise remediation guidance>`

If there are no findings, state that explicitly and mention any residual testing or review gaps.

## Finding Format Rules

Derive chat and provider-neutral comment bodies from the same canonical findings. Preserve the evidence, consequence, classification, and remediation across destinations; presentation may differ as described below.

Differences by destination:

- In chat, include the `Finding #N — <id> <severity>` prefix.
- In posted comments, omit the prefix and keep the rest unchanged.

Style rules:

- Keep the tone direct and peer-to-peer.
- Do not use extra headings like `Observation:` or `Impact:`.
- Use the changed file's language in code suggestions.
- Keep summaries short and factual.
- Do not claim that tests, builds, or tools passed unless they were actually run.

## Evaluating Skill Changes

When changing review rules, compare the previous and proposed skill against [the fixed scenarios](evals/scenarios.json) in separate contexts. Supply the same scenario inputs and shared context to both; keep expected outcomes hidden until the reviews are complete. Compare missed problems, unsupported findings, remediation scope, and output-contract compliance, not finding counts alone. Record actual differences without claiming that a single comparison proves reliability. Run this comparison when maintaining the skill, not during ordinary code reviews.

## Guardrails

- Never merge, alter code, commit, approve, request changes, or post provider comments from this core skill.
- Keep findings tied to concrete evidence from the supplied code and available context.
- Do not use provider-specific API tools from this skill; return provider-neutral output to the caller.
- Respect caller constraints about scope, chunking, and output target.
