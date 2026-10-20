---
name: code-review
description: Reusable review core for structured findings on supplied code or diffs. Invoked by review-pr and review-local; not for reviewing a PR/MR or local working tree directly, use those skills instead.
metadata:
  author: "Piotr Ramotowski <piotr.ramotowski@dawn.tech>"
  version: 2.1.0
  role: "reusable-review-core"
  dependencies: []
---

# Code Review Core Skill

## Purpose

Find what stands between a code change and safe, maintainable delivery, and say how to fix it:

- **Quality Assurance**: Check changed behavior against stated intent and existing contracts to find bugs, logic errors, and edge cases.
- **Maintainability**: Check that the change is readable, well decomposed, and consistent with the existing architecture, so the next change to this code stays cheap.
- **Security**: Detect security vulnerabilities and privacy risks, using the OWASP Top 10 where applicable.
- **Actionable Feedback**: Give enough reasoning and remediation guidance for a human or agent to evaluate and address each finding.

Report every finding that meets the [finding standard](#finding-standard), and nothing that does not.

This skill is read-only and framework-agnostic. It analyzes the supplied code, diff, patch, commit, snippet, or changed files and returns structured findings and report text to the caller. The calling skill owns every provider-specific action; see [Guardrails](#guardrails).

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

There are two output modes:

- **Machine mode** (`calling-skill` or `inline-comments`; the two behave identically): return the full structure below and show nothing in chat.
- **Chat mode** (`chat` or `report`; the two behave identically): show `report` to the user. Ask the user directly when a [question](#asking-for-missing-input) or the [size check](#size-check) is needed.

```yaml
chunking_required: optional boolean
confirm_scope: optional boolean
counted_lines: optional number
chunk_plan:
  - chunk: sequential number
    files: ordered list of file paths
    counted_lines: number of counted lines in this chunk
clarification_question: optional string
summary:
  submission: short description of reviewed input
  scope: reviewed files, snippets, or change set
  review_complete: boolean
  residual_gaps: optional review gaps, missing context, or tests not run
  cross_file_context: compact contract facts and unresolved cross-file concerns with source locations
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
report: formatted findings report
comment_bodies: provider-neutral comment text keyed by finding id
```

Field rules:

- `chunking_required`: true only when the change needs a [chunked review](#large-reviews) and the caller must run it chunk by chunk. `counted_lines` and `chunk_plan` are present when it is true and omitted otherwise.
- `confirm_scope`: true when the change exceeds 5,000 counted lines; omitted otherwise. The caller decides whether full scope is already authorized; see the [size check](#size-check).
- `clarification_question`: present only when the review cannot start without more input; see [Asking for missing input](#asking-for-missing-input).
- `summary.review_complete`: true only for a completed normal review or a completed integration of the agreed scope. It is false for preflight, clarification, and per-chunk results, and whenever coverage is incomplete.
- `summary.residual_gaps`: see [Residual gaps](#residual-gaps).
- `summary.cross_file_context`: required for per-chunk results, as a list that may be empty; omitted otherwise.
- `report`: always rendered in the [chat format](#finding-format-rules), in both modes.
- `comment_bodies`: always present in machine mode, as a map that may be empty; omitted in chat mode.
- `location.line`: never invent a precise line number. Use the best available location and state the limitation in `residual_gaps`.

**Early return.** A preflight response (`chunking_required: true`) and a clarification response (`clarification_question` present) are not reviews. Both set `review_complete: false`, return zero totals, empty `findings`, and an empty `comment_bodies` map in machine mode, and use `report` to explain why the review has not run. A preflight records the counted line total and why chunking was needed in `residual_gaps`. Callers act on `chunk_plan`, `confirm_scope`, and `clarification_question`, never by parsing `residual_gaps` or `report`.

## Workflow

Run Steps 1–6 in order. A chunk or integration pass changes some steps, as described in [Large reviews](#large-reviews).

### Step 1 — Understand the Request

1. Identify `submission.type` and the available code input.
2. Determine whether the review is diff-based, full-file-based, snippet-based, or mixed.
3. Establish the expected behavior and relevant constraints from the title, description, linked issues, user request, or existing feedback. Separate explicit requirements from assumptions; do not invent requirements where the request is silent.
4. Note all open and resolved prior feedback, so you do not repeat it and can check whether earlier requested changes were made.

#### Asking for missing input

If the input is too ambiguous or incomplete to review safely, ask for the missing scope or code. In chat mode, ask the user and end the response. In machine mode, return an early-return response with the question in `clarification_question`. The caller asks the user and invokes the core again with the answer.

If some context is missing but a useful review is still possible, continue and record the gap instead of asking. Asking for missing input is allowed at any size; it is separate from the [size check](#size-check).

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

If the project states no conventions, use common practice for the language as background only, and note the assumption.

### Step 3 — Inventory, Size, and Trace the Code

1. Build a file-change inventory. Use the `code_input.files` list when supplied; otherwise list each changed or reviewed file with its change type when known. **Every file in the requested scope must be reviewed**; never skip a file silently.
2. Order the review to build context progressively:
   - **High priority**: core business logic, security-sensitive code, public APIs, data models.
   - **Lower priority**: generated files, lock files, migration snapshots, test fixtures.
   - **Within each tier, sort files alphabetically by path**, so the order is always the same.
3. Count the change size as described in [Counting lines](#counting-lines). At 1,500 counted lines or fewer, review everything in one pass; do not propose chunking or ask about size. Above 1,500, follow [Large reviews](#large-reviews).
4. Do not evaluate diffs in isolation:
   - For logic changes, read the expanded surrounding context or the full file.
   - Trace dependencies by searching where modified functions, classes, routes, schemas, or variables are used.
   - Trace the affected normal, boundary, and failure paths across files against the expected behavior from Step 1 and the relevant existing contracts. Look for both unmet requirements and regressions.

### Step 4 — Analyze

Check the code in each [review area](#review-areas) and keep only what meets the [finding standard](#finding-standard).

### Step 5 — Build the Findings List

Build the canonical `findings` list using the Output Interface fields. This list is the only source for totals, report text, and comment bodies.

Order findings by severity (`security-violation`, `request-for-change`, `optional`), then file path, line when known, and id.

### Step 6 — Self-Check and Render

Check each finding before returning it, and rewrite or drop any that fails:

- It is backed by concrete evidence, and its location is actionable by the caller.
- Its severity follows the [shared standard](#severity), not an area-specific preference.
- It is new, not a repeat of existing feedback.
- The suggested fix fits the local codebase, or has a concrete reason to depart from its patterns.
- The body or suggestion gives the smallest safe direction, with focused verification guidance where needed.
- A maintainability finding names a concrete cost to a future change, not a principle citation dressed up as evidence.

Then recompute totals and render `report` and any required `comment_bodies` from the final findings, never separately. Set `summary.review_complete` by the field rules, and deliver by output mode.

## Finding Standard

These rules apply to every review area.

### What counts as a finding

- Identify concrete evidence from the diff, code, or nearby context, and the affected behavior, contract, or maintenance cost. Explain the consequence.
- Do not report taste, speculative improvements, inferred style preferences, or the mere absence of documentation or new tests. An `optional` finding still needs an identifiable benefit and a proportionate fix.
- Separate a demonstrated problem from an unresolved assumption. An unresolved assumption is a [residual gap](#residual-gaps), not a finding.
- Explain the smallest safe direction in the finding's `body` or `suggestion`. Include focused verification guidance when needed to evaluate the proposed fix. Keep the reasoning in review feedback; do not require a tutorial or extra source comments to teach the author.
- Report every distinct supported finding, with no cap per category. Write one finding per underlying cause, even when several areas or lenses flag the same spot, and merge findings only when they share a cause, never to fit a quota.

### Severity

- `security-violation`: a reachable or plausibly reachable vulnerability with a concrete attack path, or sensitive-data exposure.
- `request-for-change`: a demonstrated correctness failure, unsafe behavior, broken stated or existing contract, or concrete maintenance hazard that materially obstructs safe changes. Name the affected behavior, contract, or change and its consequence; reviewer discomfort alone is not enough.
- `optional`: an evidence-backed, non-blocking improvement with an identifiable benefit that a reasonable author could decline.

Category does not decide severity: maintainability, style, and documentation findings can require changes when their consequences meet this standard.

### Residual gaps

`summary.residual_gaps` holds what the review could not establish: missing context, tests not run, line numbers that could not be derived, and files left unreviewed. For each unverified concern, state what is unverified, the missing evidence, and how to check it.

An unverified security concern is a residual gap, never an `optional` finding: uncertainty is not a severity.

Always include the residual gaps in `report`, whether or not there are findings. Keep unverified concerns clearly apart from demonstrated defects, and never imply that a completed review proved the absence of security issues.

## Review Areas

### Syntax

Check for parse errors, invalid language constructs, broken imports, type mismatches visible from the code, malformed config, and obvious build-breaking changes.

### Logic

Check for incorrect conditions, missing error handling, boundary mistakes, invalid state transitions, broken assumptions, concurrency issues, data loss, and unhandled null/empty/error cases.

Assess regression protection for the affected behavior. Check existing tests before reporting a coverage gap, and name the specific changed behavior and failure risk left unprotected. Do not request new tests merely because behavior changed or no test file was added.

### Security

Check for injection flaws, exposed credentials, auth bypasses, authorization gaps, unsafe deserialization, path traversal, SSRF, XSS, CSRF, insecure randomness, sensitive logging, privacy risks, and OWASP Top 10 issues where applicable.

### Style and Maintainability

Maintainability is the cost of the *next* change. Judge whether a competent teammate who has never seen this code could read it, find the behavior they need to change, change it in one place, and be confident they broke nothing else. Every finding here must trace back to that cost.

Apply the lenses below to what the change actually touches, and skip the rest silently. They show where to look; they are not a checklist or rules to enforce for their own sake.

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

Rules specific to this area:

- Report the cost, not the principle. "This function mixes retry policy with request building, so changing the retry rules means re-testing serialization" lands; "violates SRP" does not. Name a principle only as shorthand after the concrete explanation.
- Point at the seam, not the redesign.
- Stay inside the submitted scope. Do not ask the author to refactor code they only touched incidentally, unless their change makes an existing problem materially worse.
- Thresholds are signals, not findings. Line counts, parameter counts, and nesting depth show where to look; the finding still has to be a real readability or change-cost problem in this code.

### Documentation and Scope

Check for stale documentation or comments that contradict behavior, changed public or operational contracts, missing translations for changed user-visible content, prior feedback that still applies, and mismatch between the submitted changes and stated intent.

For unclear implementation, prefer clearer names, focused functions, explicit types or data, and simpler control flow over explanatory comments. Do not request comments that compensate for confusing code or narrate behavior the code already expresses.

Report missing documentation only when you can identify an unmet public or operational contract, an explicit project requirement, or an important constraint that cannot reasonably be expressed in code. Name who relies on it and the concrete consequence of its absence. Keep concise rationale for such constraints; do not remove useful documentation merely because code should be self-explanatory.

## Large Reviews

A change above 1,500 counted lines is reviewed in chunks, then finished with one integration pass. Scope has three stages: the **requested** scope, the **agreed** scope after any narrowing (the effective plan), and the **reviewed** scope, meaning the code actually covered.

### Counting lines

Size the review by changed lines, not by file count. Review quality drops with the amount of changed code held at once; many files with small edits are an easy review, and splitting them apart hides cross-file bugs.

Count added plus deleted lines per file from the diff, or take them from `code_input.files` when the caller supplies them. With no diff, such as a folder or full-file review, count every line of the reviewed files. Leave lock files, generated files, vendored dependencies, minified bundles, and snapshot files out of the count; they are still reviewed.

### Building the chunk plan

1. Group files by the directory that holds them, keeping each file with its tests and with the changed files that directly call it where the diff shows that.
2. Give each group the priority of its highest-priority file (Step 3, item 2). Order groups by priority, then by directory path.
3. Pack the groups in order into chunks of at most 1,500 counted lines. Split a group only between files, never inside one; a single file over the limit is a chunk of its own. Files left out of the count go in the chunk of the group they belong to.

In chat mode, follow the [chunked review protocol](#chunked-review-protocol) yourself. In machine mode, do not ask about size or review any chunk: return the preflight response defined under Early return, and let the calling skill run the protocol.

### Size check

The only size question is a single one, asked before the first chunk and only above 5,000 counted lines: narrow the scope, or review every chunk. Skip it when the caller or user has explicitly authorized the full scope; a generic request to review the change does not count.

### Chunked Review Protocol

Use this shared protocol for every chunked review. Calling skills own execution, not analysis or aggregation.

1. If `confirm_scope` is true and the full scope is not explicitly authorized, present the preflight warning and plan, ask once whether to narrow the scope or review every chunk, and end the response. Otherwise start immediately. If the user narrows the scope, keep an effective plan for the selected files and record the excluded files as unreviewed.
2. Review each chunk in plan order. Pass its files and diff, keep the submission, repository baseline, source refs, existing feedback, and diff coordinates, and supply `chunk_context` with `phase: chunk`, the effective plan, and prior completed results. Retain each result, including its reviewed scope and `summary.cross_file_context`.
3. After every selected chunk is reviewed, invoke the core once with `phase: integrate`, the effective plan, all completed results, and the original file inventory and repository context. This is not another full review.
4. Use only an integrated result with `summary.review_complete: true` as the final result. Do not concatenate rendered reports or sum pre-integration totals. If a selected chunk fails, retain the completed results for resumption; do not integrate or publish the successful subset. Resume the missing work, or report the reviewed scope and gaps as incomplete. Do not publish findings, approve, request changes, or pass a self-review gate before integration finishes.

### Chunk pass

When `chunk_context.phase` is `chunk`, or the caller has otherwise already established chunking, run Steps 1–6 with these changes:

- **Step 3**: skip sizing. Review the files supplied for this chunk, using prior results as context, not proof, and trace adjacent dependencies when needed.
- **Step 5**: put compact, source-backed contract facts and unresolved cross-file concerns in `summary.cross_file_context`, or an empty list when there are none.
- **Step 6**: `summary.review_complete` stays false.

### Integration pass

When `chunk_context.phase` is `integrate`, run Steps 1–6 with these changes:

- **Step 3**: do not size or review every file again. Instead, check that the completed results cover every file in the effective plan. A failed or malformed chunk result does not establish coverage; count only code actually reviewed, not files merely assigned to a failed invocation.
  - If any chunk or file is missing, stop. Return `review_complete: false`, the reviewed scope, and the missing work in `residual_gaps`. Leave findings and comment bodies empty rather than publishing unreconciled candidates, and say in `report` that the review is incomplete, not clean.
  - Otherwise, record files excluded from the requested scope as residual gaps, and continue with the chunk summaries and the relevant code.
- **Step 4**: check the established contracts and unresolved cross-file concerns against the affected producers, consumers, and tests. Inspect only the seams needed to resolve them. Recheck conflicting prior conclusions against the code rather than carrying either one forward.
- **Step 5**: reconcile the completed results before rendering:
  - Merge findings with the same underlying cause, even if their ids or locations differ. Keep one representative location and id, with the evidence and smallest safe remediation needed for that cause.
  - Resolve contradictory claims and severities against the code. Drop invalidated findings, and remove resolved gaps only when evidence supports it; keep unresolved questions as residual gaps.
  - Combine the reviewed coverage and remaining gaps, then recompute totals from the final findings. Never add raw chunk totals or deduplicate by id alone.
- **Step 6**: render again from the reconciled list, so numbering, totals, and comment keys match it.

## Finding Format Rules

Derive `report` and `comment_bodies` from the same canonical findings. Keep the evidence, consequence, classification, and remediation the same in both.

Render each finding in `report` in this chat format:

`**Finding #N — <id> <severity>**`

`**<title>**`

`<body>`

`*Relevant lines: <file path and line reference>*`

`Suggested approach: <suggestion or concise remediation guidance>`

After the findings, include the [residual gaps](#residual-gaps). If there are no findings, say so explicitly, without hiding the gaps.

Each `comment_bodies` entry is the same rendered finding without the `Finding #N — <id> <severity>` prefix. Do not add a separate severity line or label; classification stays in the structured finding.

Style rules:

- Keep the tone direct and peer-to-peer.
- Do not use extra headings like `Observation:` or `Impact:`.
- Use the changed file's language in code suggestions.
- Keep summaries short and factual.
- Do not claim that tests, builds, or tools passed unless they were actually run.

## Guardrails

- Never modify repository files, merge, commit, approve, request changes, or post provider comments from this core skill.
- Do not use provider-specific API tools; return provider-neutral output to the caller.
- Respect caller constraints about scope, chunking, and output target.

To change this skill's rules, see [evals/README.md](evals/README.md).
