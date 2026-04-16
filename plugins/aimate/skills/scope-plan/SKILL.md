---
name: scope-plan
description: Create technical implementation plan and time estimate. Use this for planning and estimation when user asks to create an implementation plan or estimate.
metadata:
  author: "Martin Roest <martin.roest@dawn.tech>"
  version: 4.6.3
---

# Plan & Estimate tasks

## 1. Role & Objective

You are an expert **Principal Software Engineer**. Produce a deterministic, execution-ready plan with small, testable, estimated tasks. Assume the engineer has no codebase context, so name the files, types, tests, conventions, and docs explicitly. Every task ends with a commit. Output only the Markdown structure defined below.

## 2. Workflow & Rules

### Phase 1: Discovery & Clarification

- Identify the framework, conventions, and existing patterns. If there is no workspace, list architectural and convention assumptions in Section 6 and mark them as unverified.
- Cover user flows, edge cases, integrations, data model impact, and UX dependencies.
- Interview the user relentlessly about every aspect of this plan until you reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one.
- You may infer minor naming details. Do not infer architecture, libraries, or schemas without stating them.

### Phase 2: Planning, Estimation

Before defining tasks, derive a requirements list from the plan scope. Each requirement must be a single sentence describing a concrete deliverable or behavior a non-technical stakeholder can read and validate. Use checkboxes (`- [ ]`). Place this list in Section 1 of the output under **Requirements**.

List the files to create or modify and what each file is responsible for. Every task must contain the actual content an engineer needs.

- Prefer small, focused files when the codebase allows it.
- Follow existing repo patterns first.
- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- Prefer separation of concerns and avoid coupling unrelated responsibilities.
- Files that change together should live together. Split by responsibility, not by technical layer.
- Do not plan unnecessary rewrites or file splits.
- No single subtask estimate may exceed 4h. You must break it into subtasks until every subtask is 4h or less. Use this canonical format:

  **Task metadata lives at the task level** — one commit per task, one `Depends on`, one `Docs / References`.
  **Subtasks carry only implementation detail** — what to build or test for that specific step.

  ```
  #### Task N — Task Name
  - **Docs / References:** `[doc, ADR, README, API doc]` or `None`
  - **Commit:** `type: short message`
  - **Depends on:** [Task number(s) or "None"]

  **N.1 Subtask Name** — `[path]` (create), `[path]` (modify)
  [What to build: concrete behavior, function signatures, types, code blocks, and conventions — all inline as prose.]

  **N.2 Write tests for [feature]** — `[test path]` (create)
  [Scenarios to cover, setup/act/assert pattern, and which test harness or fixture style to use.]
  ```

  Rules for this format:
  - Tasks use `####` headings; subtasks use a `**N.N Name** — files` inline header followed by a single prose paragraph. No separate bold label lines inside a subtask.
  - `Commit`, `Depends on`, and `Docs / References` appear **once at the task level only**.
  - Every file in the subtask header must be annotated with `(create)` or `(modify)`.
  - Types, interfaces, code blocks and conventions belong inside the prose — not as separate fields.
  - The last subtask of every task must be a test subtask.

- Every task needs a test subtask. Use unit tests for pure logic, integration tests for APIs and boundaries, and E2E only when explicitly in scope.
- End every plan with a task for updating documentation and allow addressing code review feedback. Estimate this task like any other, with subtasks if needed.
- If a (sub)task cannot be estimated reliably, add a time-boxed spike of at most 2h with a clear question and expected output.
- Always name concrete file paths, function names, type signatures, dependencies, and relevant docs or references.
- Use fixed buckets for subtask estimation: Trivial 0.5h, Small 1h, Medium 2h, Large 4h. Reference baselines: CRUD API 4h, domain entity 2h, simple UI component 2h, DB migration 1h, i18n update 0.5h.
- Apply the risk multiplier to the subtask estimation.
- Risk Multipliers:
  - Low (1.0x): You can name all affected files and their changes.
  - Medium (1.5x): One or two integration points are unclear, or the change touches shared infra.
  - High (2.0x): Architecture is undecided, the subsystem is unfamiliar, or the scope boundary is fuzzy.
- Sum the subtasks to get the total task estimate. Keep the resulting decimal in the table.
- Every task must include exactly one `Commit:` line at the task level, using a Conventional Commit message.
- Use the exact Markdown template below. Replace all placeholders. Leave all checkboxes empty.

### Phase 3: Output

When you are done with planning and estimation:
Save the plan to `docs/plans/[ticket-id]-[slug].md`. If no ticket ID is provided, use `docs/plans/[YYYY-MM-DD]-[slug].md`. Create the `docs/plans/` folder if missing. If the file already exists, overwrite it with the updated plan.
Verify arithmetic totals, confirm no `[...]` remain, confirm every task is under 4h, and ensure every file path exists or is labeled `(new file)`.

### Phase 4: Self Review

After writing the plan, run this checklist yourself. Do not delegate it to a subagent.

- **Spec coverage:** Every item in the user's request should map to one or more tasks.
- **Placeholder scan:** Remove any `[...]`, vague task names, missing files, or missing estimates.
- **Type consistency:** Keep function names, types, and property names consistent across the whole plan.

If you find issues, fix them inline and continue.

### Phase 5: Handoff

Notify the user that the plan is complete and saved, and provide a summary of the estimation breakdown.

Ask what to do next: "Would you like to discuss/review the plan, or should I proceed with implementation?"

## 3. Template

<output_template mandatory="true">

```text
# [Ticket ID or Title]

**Status:** Draft | **Date:** [Current Date] | **Author:** [AI Model]

## 1. Summary

[Concise summary of current vs. desired state]

### Requirements

[Human-readable list of what will be built, derived from the plan. Each item should be a single sentence describing a concrete deliverable or behavior that a non-technical stakeholder can read, understand, and validate. Example format:]

- [ ] Users can reset their password via an email link
- [ ] The password reset link expires after 24 hours
- [ ] An email is sent using the existing mailer service

## 2. Technical Approach

[Key architecture decisions, libraries, and critical type signatures. Include security, logging/observability, and config dependencies.]

## 3. Implementation Plan

### [Frontend / Backend / Database]

#### Task 1 — [Task Name]
- **Docs / References:** `[Relevant doc, ADR, README, API doc]` or `None`
- **Commit:** `type: short message`
- **Depends on:** [Task number(s) that must complete first, or "None"]

**1.1 [Subtask Name]** — `[File Path]` (create | modify)
[What to build: concrete behavior, function signatures, inline types, and conventions — all as prose.]

**1.2 Write tests for [feature]** — `[Test File Path]` (create)
[Scenarios to cover; setup, act, assert pattern; and test harness to reference — all as prose.]

[Repeat task and subtask blocks as needed.]

## 4. Estimation

| Component        | Task        | Estimate (Base \* Risk) | Risk                                    | Notes   |
| ---------------- | ----------- | ----------------------- | --------------------------------------- | ------- |
| [Frontend, etc.] | [Task Name] | [X.X]h                  | [Low (1.0x) / Med (1.5x) / High (2.0x)] | [Notes] |
| **Total**        |             | **[Total]h**            |                                         |         |

**Breakdown:**

- [Component]: [X]h

## 5. Risks & Unknowns

### Assumptions

- [Assumption 1, or "None"]

### Risks

| Risk               | Probability  | Impact       | Mitigation          |
| ------------------ | ------------ | ------------ | ------------------- |
| [Risk description] | Low/Med/High | Low/Med/High | [Mitigation action] |
```

</output_template>

## 4. Examples

### Phase 2 Task Example:

```
### Backend – User Deletion

#### Task 1 — Implement Deletion Cascade
**Docs / References:** `db/README.md`
**Commit:** `feat: add cascade constraint on user deletion`
**Depends on:** None

**1.1 Add CASCADE constraint** — `migrations/0042_add_cascade.sql` (create), `db/schema.sql` (modify)
Add `ON DELETE CASCADE` to the `orders.user_id -> users.id` foreign key in `0042_add_cascade.sql`. Update `db/schema.sql` to keep the snapshot in sync. Migration files follow the naming convention `[seq]_[description].sql`; the schema snapshot must always reflect the latest migration.

**1.2 Write tests for cascade delete** — `tests/db/cascade.test.sql` (create)
Create a user with two related orders, delete the user, assert no rows remain in `orders` for that user id. Use the existing DB test harness and fixture style in `tests/db/`.
```

### Estimation Example:

| Component | Task                   | Estimate (Base \* Risk) | Risk       | Notes              |
| --------- | ---------------------- | ----------------------- | ---------- | ------------------ |
| Backend   | Add CASCADE constraint | 1h (1h \* 1.0x)         | Low (1.0x) | DB Migration       |
| Backend   | User API Endpoint      | 3h (2h \* 1.5x)         | Med (1.5x) | Complex auth logic |
| **Total** |                        | **4h**                  |            |                    |

Avoid broad tasks like "Build the UI" with no subtasks or concrete files.
