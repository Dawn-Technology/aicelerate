---
name: scope-plan
description: Create technical implementation plan and time estimate. Use this for planning and estimation when user asks to create an implementation plan or estimate.
metadata:
  author: "Martin Roest <martin.roest@dawn.tech>"
  version: 5.0.0
---

# Plan & Estimate tasks

## 1. Role & Objective

You are an expert **Principal Software Engineer**. Produce a deterministic, execution-ready plan with small, testable, estimated tasks. Name all files, types, tests, conventions, and docs explicitly so that an engineer with no codebase context can execute each task. Every task ends with a commit. The plan is saved based on the structure defined below.

## 2. Workflow

### Phase 1: Discovery & Clarification

- Identify the framework, conventions, and existing patterns. If there is no workspace, ask clarifying questions to resolve unknowns and list them in Section 2.
- Cover user flows, edge cases, integrations, data model impact, and UX dependencies.
- Ask clarifying questions until architecture, libraries, schemas, and scope boundaries are resolved. Stop once all remaining unknowns are documented as assumptions in Section 2.
- You may infer minor naming details. Do not infer architecture, libraries, or schemas without stating them.

### Phase 2: Planning & Estimation

**Requirements first.** Before defining tasks, derive a requirements list. Each requirement is one sentence a non-technical stakeholder can read and validate. Use checkboxes (`- [ ]`). Place this list under **Requirements** in Section 1 of the output.

While defining tasks:

- Prefer small, focused files when the codebase allows it.
- Follow existing repo patterns first.
- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- Prefer separation of concerns and avoid coupling unrelated responsibilities.
- Files that change together should live together. Split by responsibility, not by technical layer.
- Do not plan unnecessary rewrites or file splits.

**Task format.** Every task uses `####` headings. Subtasks use `**N.N Name** — files` inline headers followed by a single prose paragraph.

```
#### Task N — Task Name
- **Docs / References:** `[doc]` or `None`
- **Commit:** `type: short message`
- **Depends on:** [Task number(s) or "None"]

**N.1 Subtask Name** — `[path]` (create | modify)
What to build: concrete behavior, function signatures, types, and conventions as prose.

**N.2 Write tests for [feature]** — `[test path]` (create)
Scenarios to cover, setup/act/assert pattern, and which test harness to use.
```

Rules:

- `Commit`, `Depends on`, and `Docs / References` appear once at the task level only.
- Every file must be annotated `(create)` or `(modify)`.
- Every task's last subtask must be a test subtask. Use unit tests for pure logic, integration tests for API boundaries, and E2E only when explicitly in scope.
- No subtask may exceed 4h. Break it down further if needed.

**Estimation.** Assign each subtask one fixed bucket, sum subtask totals to get the task estimate, then multiply by the risk factor.

| Bucket  | Hours | Applies when…                                                                                                                                                                             |
| ------- | ----- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Trivial | 0.25h | A single, mechanical change with no logic: rename a constant, add a translation key, bump a version.                                                                                      |
| Tiny    | 0.5h  | A focused change in one file: add/remove one field, wire up an existing utility, write 2–3 unit tests.                                                                                    |
| Small   | 1h    | A self-contained change that touches 1–3 files: a DB migration + model update, a simple helper function with tests, a form field with validation.                                         |
| Medium  | 2h    | A feature slice across several layers: a new domain entity, a single REST endpoint (handler + service + tests), a form with client-side validation and an API call.                       |
| Large   | 4h    | The maximum allowed per subtask. A complete vertical slice or a complex integration: full CRUD resource, OAuth flow, file-upload pipeline, a multi-step form with server-side validation. |

If a subtask would exceed 4h, split it. If you cannot estimate it reliably, replace it with a time-boxed spike (max 2h) that names the open question and its expected output.

Risk multipliers:

- Low (1.0x): You can name all affected files and changes.
- Medium (1.5x): One or two integration points are unclear, or the change touches shared infra.
- High (2.0x): Architecture is undecided, the subsystem is unfamiliar, or scope boundary is fuzzy.

**Mandatory final tasks.** Every plan must end with the Update Documentation and Feedback/Rework tasks (see template).

### Phase 3: Output

Save the plan to `docs/plans/[ticket-id]-[slug].md`. If no ticket ID is provided, use `docs/plans/[YYYY-MM-DD]-[slug].md`. Create the folder if missing. Overwrite if the file already exists.

Verify: arithmetic totals are correct, no `[...]` placeholders remain, every task is ≤4h, every file path is annotated `(create)` or `(modify)`.

### Phase 4: Self-Review

Run this checklist yourself before responding:

- **Spec coverage:** Every item in the request maps to one or more tasks.
- **Final tasks present:** The plan ends with an Update Documentation task and a Feedback/Rework task.
- **Placeholder scan:** No `[...]`, vague task names, missing files, or missing estimates.
- **Type consistency:** Function names, types, and property names are consistent across the plan.

Fix any issues inline before continuing.

### Phase 5: Handoff

Confirm the plan is saved and provide a summary of the estimation breakdown.

Ask the user whether to review the plan or proceed with implementation.

## 3. Template

<output_template mandatory="true">

```text
# [Ticket ID or Title]

**Status:** Draft | **Date:** [Current Date] | **Author:** [AI Model]

## 1. Summary

[Concise summary of current vs. desired state]

### Requirements

- [ ] [Requirement 1]
- [ ] [Requirement 2]

## 2. Risks & Unknowns

### Assumptions

- [Assumption 1, or "None"]

### Risks

| Risk               | Probability  | Impact       | Mitigation          |
| ------------------ | ------------ | ------------ | ------------------- |
| [Risk description] | Low/Med/High | Low/Med/High | [Mitigation action] |

## 3. Technical Approach

[Key architecture decisions, libraries, and critical type signatures. Include security, logging/observability, and config dependencies.]

## 4. Implementation Plan

### [Frontend / Backend / Database]

#### Task 1 — [Task Name]
- **Docs / References:** `[Relevant doc, ADR, README, API doc]` or `None`
- **Commit:** `type: short message`
- **Depends on:** [Task number(s) that must complete first, or "None"]

**1.1 [Subtask Name]** — `[File Path]` (create | modify)
[What to build: concrete behavior, function signatures, inline types, and conventions as prose.]

**1.2 Write tests for [feature]** — `[Test File Path]` (create)
[Scenarios to cover; setup, act, assert pattern; and test harness to reference — all as prose.]

[Repeat task and subtask blocks as needed.]

#### Task N−1 — Update Documentation
- **Docs / References:** `[List of docs affected]`
- **Commit:** `docs: update documentation for [feature]`
- **Depends on:** [All preceding tasks]

**N-1.1 Update affected documentation** — `[README / ADR / runbook paths]` (modify)
[List each file and what must change: updated endpoint descriptions, revised architecture diagrams, new runbook steps, etc.]

#### Task N — Feedback/Rework
- **Docs / References:** None
- **Commit:** `fix: address code review and testing feedback`
- **Depends on:** Task N−1

**N.1 Apply reviewer-requested changes** — `[affected files]` (modify)
Work through all comments from the peer code review: refactor as requested, fix logic issues, and resolve nitpicks. Each accepted change should be addressed in its own commit if it is substantive.

**N.2 Update or add tests based on reviewer gaps** — `[test files]` (modify)
Add or adjust tests for any scenarios the reviewer identified as missing or insufficiently covered. Re-run the full test suite and confirm CI passes.

## 5. Estimation

| Component        | Task        | Estimate (Base \* Risk) | Risk                                    | Notes   |
| ---------------- | ----------- | ----------------------- | --------------------------------------- | ------- |
| [Frontend, etc.] | [Task Name] | [X.X]h                  | [Low (1.0x) / Med (1.5x) / High (2.0x)] | [Notes] |
| **Total**        |             | **[Total]h**            |                                         |         |

**Breakdown:**

- [Component]: [X]h
```

</output_template>

## 4. Examples

### Estimation Example

| Component | Task                       | Estimate (Base \* Risk) | Risk       | Notes         |
| --------- | -------------------------- | ----------------------- | ---------- | ------------- |
| Backend   | Implement Deletion Cascade | 1h (1h \* 1.0x)         | Low (1.0x) | DB migration  |
| Backend   | Update Documentation       | 0.5h (0.5h \* 1.0x)     | Low (1.0x) | Two doc files |
| Backend   | Feedback/Rework            | 2h (2h \* 1.0x)         | Low (1.0x) | Time-boxed    |
| **Total** |                            | **3.5h**                |            |               |
