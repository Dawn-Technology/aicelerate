# Acceptance Criteria Format

This file defines the single canonical format for acceptance criteria across the `aimate` plugin. It is the shared contract between the skills that produce a spec (`write-prd`), the skill that turns a spec into test stubs (`spec-to-tests`), and the skill that reviews a change against a spec (`review-pr`). Any automated delivery pipeline that consumes a Dawn spec reads the same format.

There is one definition, and it lives here. Skills reference this file rather than restating the grammar. If the format changes, it changes here and every reader is updated in the same step.

## Why a fixed format

An acceptance criterion is the join between a requirement, its tests, and its review. When criteria are free prose, a human has to judge whether code matches intent. When they follow a fixed, addressable grammar, that judgement becomes a checkable result: a tool can extract each criterion, find the test that covers it, and report whether the change satisfies it. The format below is designed to be parsed without guessing.

## Design goals

- **Machine-parseable.** The block sits under a fixed heading and is wrapped in stable sentinel comments, so a parser can extract the exact region regardless of what surrounds it.
- **Individually addressable.** Each criterion carries a stable id (`AC-1`, `AC-2`, …). The id is the join key across the spec, the tests, and the review findings.
- **Behaviour-oriented.** Each criterion states a condition and an expected outcome. Given/When/Then is the default. It describes behaviour, never test code.
- **Framework-agnostic.** The criteria say nothing about a test framework. Mapping to a framework happens later, in `spec-to-tests`.

## The block

Every spec ends with one acceptance-criteria block in exactly this shape:

```markdown
## Acceptance Criteria

<!-- acceptance-criteria:start format=gwt/v1 -->

### AC-1: Password reset link is emailed
- **Given** a registered user with a valid email
- **When** a password reset is requested
- **Then** a reset link valid for 60 minutes is sent to that email

### AC-2: Expired reset links are rejected
- **Given** an expired reset link
- **When** the user opens it
- **Then** the request is rejected
- **And** no password change occurs

<!-- acceptance-criteria:end -->
```

## Grammar

Read the rules as the contract a parser relies on.

1. **Section heading.** The block is introduced by the exact line `## Acceptance Criteria`.
2. **Sentinels.** The criteria are wrapped in `<!-- acceptance-criteria:start format=gwt/v1 -->` and `<!-- acceptance-criteria:end -->`. A consumer extracts the text between these two comments. The `format=gwt/v1` marker versions the grammar; bump it only when the grammar itself changes.
3. **Criterion header.** Each criterion begins with `### AC-<n>: <title>`, where `<n>` is a positive integer and `<title>` is a short human label. The `AC-<n>` token is the id.
4. **Criterion body.** Bulleted lines with bolded keywords:
   - `**Given**` — zero or more preconditions. Use `**And**` for each additional precondition.
   - `**When**` — the action. Use `**And**` for a compound action.
   - `**Then**` — one or more expected outcomes. Use `**And**` for each additional outcome.
   - A `**When**` and at least one `**Then**` are required. `**Given**` is optional.
5. **Shorthand.** Where Given/When/Then is overkill, a single `- **When** <condition>, **then** <outcome>` line is acceptable. Keep one style within a single spec — do not mix full and shorthand criteria in the same block.

## Id rules

- Ids are stable and never reused. Once `AC-3` names a criterion, it names that criterion for the life of the spec.
- Never renumber to close a gap. If a criterion is dropped, retire its id rather than shifting the others.
- New criteria take the next unused integer.
- The id is the join key. Tests reference it, review findings reference it, and any pipeline correlates spec, tests, and results through it.

## Quality bar

Each criterion must be checkable: a concrete condition and an observable outcome. If a criterion cannot be written as a condition and an outcome — for example "the page should feel fast" — that is a signal the requirement is still vague. Sharpen the requirement rather than writing a fuzzy criterion.

Keep criteria small. One criterion asserts one behaviour. Split a criterion that hides several independent outcomes so each can be tested and reviewed on its own.

## Readers of this file

- [`write-prd`](../skills/write-prd/SKILL.md) writes this block into every PRD.
- [`spec-to-tests`](../skills/spec-to-tests/SKILL.md) reads the block and generates one or more test stubs per criterion, each tagged with the criterion id.
- [`review-pr`](../skills/review-pr/SKILL.md) reads the block and reports, per id, whether the change and its tests satisfy the criterion.
