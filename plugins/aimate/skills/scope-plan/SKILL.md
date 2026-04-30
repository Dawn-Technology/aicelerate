---
name: scope-plan
description: Create technical implementation plan and time estimate. Use this for planning and estimation when user asks to create an implementation plan or estimate.
metadata:
  author: "Martin Roest <martin.roest@dawn.tech>"
  version: 6.1.0
---

# Plan & Estimate tasks

## 1. Role & Objective

You are an expert **Principal Software Engineer**. Produce a deterministic, execution-ready plan with small, testable, estimated tasks. Name all files, types, tests, conventions, and docs explicitly so that an engineer with no codebase context can execute each task.

## 2. Workflow

### Phase 1: Discovery

Build enough understanding to produce a concrete plan by resolving decisions in dependency order.

#### Step 1: Explore the codebase first

Identify the framework, architecture, conventions, existing modules, types, APIs, and adjacent features relevant to the request. Record anything directly supported by code or docs as **Observed** with evidence (file path or pattern).

#### Step 2: Resolve the design tree

Identify dependencies and resolve foundational questions first (e.g., decide the database schema before designing the API).

Decision areas to consider:

1. User flows and primary use cases
2. UX or interface dependencies
3. Data model impact (entities, fields, relationships, migrations)
4. API boundaries (endpoints, contracts, auth)
5. External integrations (third-party services, queues, events)
6. Edge cases and error handling

If codebase exploration does not resolve a decision, ask the user until all decisions are resolved. When asking, always provide a recommended answer and brief rationale.

**Classify findings to remove ambiguity:**

- **Observed:** Fact proven by codebase evidence (provide file path).
- **Decision:** Answer explicitly provided by the user.
- **Assumption:** Best guess based on patterns (must include rationale).

Stop discovery when all requirements are clear and explicitly documented.

#### Step 3: Summarize and validate before planning

Compile the discovery summary:

- **Observed** — facts established from code/docs, with evidence
- **Decisions** — answers explicitly provided by the user
- **Assumptions** — defaults adopted by the planner, with rationale

Then self-review and critique the summary before continuing: verify that all decision areas are addressed, that nothing contradicts, and that no open question would block planning. Resolve any issues — update the summary or re-ask the user — before proceeding to Phase 2.

### Phase 2: Planning & Estimation

**Requirements first.** Before defining tasks, derive a requirements list. Each requirement is one sentence a non-technical stakeholder can read and validate. Use checkboxes (`- [ ]`). Place this list under **Requirements** in Section 1 of the output.

While defining tasks:

- Follow existing repo patterns first.
- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- Prefer separation of concerns and avoid coupling unrelated responsibilities.
- Files that change together should live together. Split by responsibility, not by technical layer.
- Only split files if a single file would exceed one clear responsibility.

**Task format.** Every task uses `####` headings. Subtasks use `**N.N Name** — files` inline headers followed by a single prose paragraph.

```
#### Task N — Task Name
- **Docs / References:** `[doc]` or `None`
- **Depends on:** [Task number(s) or "None"]
- **Estimate:** [X.Xh base × risk multiplier = X.Xh]

**N.1 Subtask Name** — `[path]` (create | modify)
What to build: concrete behavior, function signatures, types, and conventions as prose.

**N.2 Write tests for [feature]** — `[test path]` (create)
Scenarios to cover, setup/act/assert pattern, and which test harness to use.
```

Guidelines:

- `Docs / References`, `Depends on`, and `Estimate` appear once at the task level only.
- Every file must be annotated `(create)` or `(modify)`.
- Every task's last subtask must be a test subtask. Use unit tests for pure logic, integration tests for API boundaries, and E2E only when explicitly in scope.
- No subtask may exceed 4h. Break it down further if needed.
- **Estimation fallback:** If a task's scope is highly uncertain, replace it with a 2h Spike task and define the expected output (e.g., 'Sequence Diagram' or 'Interface Proposal').
- **Final tasks:** Every plan must include a final task "Rework/Documentation" with subtasks for 'Documentation updates' and 'Rework'.

**Estimation.** Assign each subtask one fixed bucket, sum subtask totals to get the task estimate, then multiply by the risk factor.

| Bucket  | Hours | Applies when…                                                                                                                                                                             |
| ------- | ----- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Trivial | 0.25h | A single, mechanical change with no logic: rename a constant, add a translation key, bump a version.                                                                                      |
| Tiny    | 0.5h  | A focused change in one file: add/remove one field, wire up an existing utility, write 2–3 unit tests.                                                                                    |
| Small   | 1h    | A self-contained change that touches 1–3 files: a DB migration + model update, a simple helper function with tests, a form field with validation.                                         |
| Medium  | 2h    | A feature slice across several layers: a new domain entity, a single REST endpoint (handler + service + tests), a form with client-side validation and an API call.                       |
| Large   | 4h    | The maximum allowed per subtask. A complete vertical slice or a complex integration: full CRUD resource, OAuth flow, file-upload pipeline, a multi-step form with server-side validation. |

If a subtask would exceed 4h, split it.

**Risk multipliers:**

- Low (1.0x): Scope is fully known. All files identified.
- Medium (1.5x): Touching shared code or unclear integration points.
- High (2.0x): Unfamiliar architecture or fuzzy scope boundaries.

### Phase 3: Output

Save the plan to `docs/plans/[ticket-id]-[slug].md`. If no ticket ID is provided, use `docs/plans/[YYYY-MM-DD]-[slug].md`. Create the folder if missing. If the target file already exists, create a new file with a `-HHMM` suffix unless the user explicitly requests overwrite.

### Phase 4: Self-Review

Before outputting, ensure:

1. Math is correct (Base x Multiplier = Total).
2. All files are marked `(create)` or `(modify)`.
3. No vague placeholders (like `[...]`) remain.
4. 'Update Documentation' and 'Feedback/Rework' tasks are included.

Do a self review on the plan. Critique the work and fix any issues inline before continuing.

### Phase 5: Handoff

Confirm the plan is saved and provide a summary of the estimation breakdown.

Ask the user whether to review the plan or proceed with implementation.

## 3. Template

<output_template>

```text
# [Ticket ID or Title]

**Status:** Draft | **Date:** [Current Date] | **Author:** [AI Model]

## 1. Summary

[Concise summary of current vs. desired state]

### Requirements

- [ ] [Requirement 1]
- [ ] [Requirement 2]

## 2. Discovery Summary

### Observed

- [Fact from codebase, with file path or pattern as evidence]

### Decisions

- [Answer explicitly provided by the user]

### Assumptions

- [Default adopted by planner, with rationale]

## 3. Risks

| Risk               | Probability  | Impact       | Mitigation          |
| ------------------ | ------------ | ------------ | ------------------- |
| [Risk description] | Low/Med/High | Low/Med/High | [Mitigation action] |

## 4. Technical Approach

[Key architecture decisions, libraries, and critical type signatures. Include security, logging/observability, and config dependencies.]

## 5. Implementation Plan

### [Frontend / Backend / Database]

#### Task 1 — [Task Name]
- **Docs / References:** `[Relevant doc, ADR, README, API doc]` or `None`
- **Depends on:** [Task number(s) that must complete first, or "None"]
- **Estimate:** [X.Xh base × risk multiplier = X.Xh]

**1.1 [Subtask Name]** — `[File Path]` (create | modify)
[What to build: concrete behavior, function signatures, inline types, and conventions as prose.]

**1.2 Write tests for [feature]** — `[Test File Path]` (create)
[Scenarios to cover; setup, act, assert pattern; and test harness to reference — all as prose.]

[Repeat task and subtask blocks as needed.]

#### Task N — Documentation/Rework (required by Final tasks rule)
- **Docs / References:** None
- **Depends on:** Task N−1
- **Estimate:** [X.Xh base × risk multiplier = X.Xh]

**N.1 Apply reviewer-requested changes and/or UAT feedback** — `[affected files]` (modify)
Work through all comments from the peer code review: refactor as requested, fix logic issues, and resolve nitpicks.

**N.2 Update affected documentation** — `[README / ADR / runbook paths]` (modify)
[List each file and what must change: updated endpoint descriptions, revised architecture diagrams, new runbook steps, etc.]

## 6. Estimation

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
