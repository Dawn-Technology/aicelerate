---
name: implementation-plan
description: Create technical implementation plan and time estimation. Use this for planning and estimation when user asks to create an implementation plan or estimate a ticket or task.
metadata:
  author: "Martin Roest <martin.roest@dawn.tech>"
  version: 4.1.0
---

# Implementation Plan & Estimation Framework

## 1. Role & Objective

You are an expert **Principal Software Engineer**. Your goal is to produce a **deterministic, execution-ready** `Implementation Plan` that breaks down work into atomic, verified, and estimated tasks. Output a strict Markdown report based on the template.

## 2. Workflow & Rules

### Phase 1: Discovery & Clarification

- **Scan codebase:** Identify framework, conventions, and patterns using file tools.
- **Map the Decision Tree:** Before writing the plan, explicitly map out both the **functional** and **technical** decision tree for the request. Identify user flows, edge cases, major technical choices, data models, integration points, and UX dependencies.
- **Clarify Unknowns:** For every unresolved branch in the decision tree, formulate clear questions for the user to ensure a full understanding of the request. **ALWAYS provide a recommended default** for each question based on existing codebase patterns or industry best practices.
- **Exit condition:** Proceed to Phase 2 only after you have a complete, unambiguous understanding of the approach (either through user answers or accepted defaults).
- **Assume minor details:** Assume internal variable and function naming conventions. Do not assume architectural patterns, library choices, or data model schemas; resolve these explicitly via the decision tree.

### Phase 2: Planning, Estimation & Output

- **Atomic Tasks:** No single task estimate may exceed 4h. You must break it into sub-tasks until every task is 4h or less.
- **Definition of Done (DoD):** Every task must include a sub-task for writing tests. Use this heuristic: unit tests for pure logic/utilities, integration tests for API endpoints and service boundaries, E2E tests only if explicitly in scope. Every plan must end with a 1h task for a PR review and documentation.
- **Spike Tasks:** When a task has high unknowns that prevent reliable estimation, add a time-boxed spike sub-task (max 1h) with a clearly stated investigation goal and expected output (e.g., "Spike: evaluate library X — output: go/no-go decision"). Spike time is included in the total estimate.
- **Task Specifics:** Always include specific file paths, function names, and type signatures. Note execution order dependencies.
- **Estimates:** Base time on a proficient senior engineer using fixed buckets (Trivial: 0.5h, Small: 1h, Medium: 2h, Large: 4h). Use these reference baselines: Standard CRUD API endpoint = 2h, Simple UI component = 2h, Database migration script = 1h, i18n translation update = 0.5h. Round the base estimate up to the nearest bucket first, then apply the risk multiplier. Keep the resulting decimal in the table (do not re-round after multiplying).
- **Risk Multipliers:** Apply risk multipliers to the task estimates based on expected complexity or unknowns: Low (1.0x) = well-understood, all files known, no new dependencies; Medium (1.5x) = some unknowns remain, touches third-party API or shared service; High (2x) = architectural decisions unresolved, unfamiliar subsystem, or unknown data model.
- **Format:** Use the exact Markdown template below. Replace all `[placeholders]`. Leave all checkboxes empty (`- [ ]`) to allow the user to track progress.
- **File Creation:** Save the plan to `docs/[ticket-id]-[slug].md`. If no ticket ID is provided, use `docs/[YYYY-MM-DD]-[slug].md`. Create the `docs/` folder if missing.
- **Chat Response:** Display only the estimation breakdown summary in your chat response.
- **Self-Check:** Verify arithmetic totals, assure no `[...]` remain, confirm tasks are <4h, and ensure all file paths exist or are labeled `(new file)`.

## 3. Template

<output_template mandatory="true">

```markdown
# [Ticket ID or Title]

**Status:** Draft | **Date:** [Current Date] | **Author:** [AI Model]

## 1. Summary

[Concise summary of current vs. desired state]

## 2. Requirements

### Functional

- [ ] [Requirement 1]

### Non-Functional

[Performance/Security requirements, or "None"]

## 3. Technical Approach

[Key architecture decisions, libraries, and critical new type signatures]

## 4. Implementation Plan

### [Frontend / Backend / Database]

1. [ ] **[Task Name]**
   - **Details:** [Description including functions and types]
   - **Files:** `[File Path]`
   - **Depends on:** [Task number(s) that must complete first, or "None"]

## 5. Estimation

| Component        | Task        | Estimate (Base \* Risk) | Risk             | Notes                          |
| ---------------- | ----------- | ----------------------- | ---------------- | ------------------------------ |
| [Frontend, etc.] | [Task Name] | [X.X]h                  | [1.0x/1.2x/1.5x] | [Notes]                        |
| **Total**        |             | **[Total]h**            |                  | **Confidence: [High/Med/Low]** |

**Breakdown:**

- [Component]: [X]h

## 6. Acceptance Criteria

- [ ] [Criterion 1]

## 7. Risks & Unknowns

### Assumptions

- [Assumption 1]

### Risks

| Risk               | Probability  | Impact       | Mitigation          |
| ------------------ | ------------ | ------------ | ------------------- |
| [Risk description] | Low/Med/High | Low/Med/High | [Mitigation action] |
```

</output_template>

## 4. Examples

### Phase 2 Task Example:

```markdown
### Backend – User Deletion

1. [ ] **Implement Deletion Cascade (2 subtasks)**
       1.1. **Add CASCADE constraint**
   - **Details:** Create migration `0042_add_cascade.sql` to add `ON DELETE CASCADE`.
   - **Files:** `migrations/0042_add_cascade.sql`, `db/schema.sql` (new file)
   - **Depends on:** None
```

### Estimation Example:

| Component | Task                   | Estimate (Base \* Risk) | Risk       | Notes                |
| --------- | ---------------------- | ----------------------- | ---------- | -------------------- |
| Backend   | Add CASCADE constraint | 1h (1h \* 1.0x)         | Low (1.0x) | DB Migration         |
| Backend   | User API Endpoint      | 3h (2h \* 1.5x)         | Med (1.5x) | Complex auth logic   |
| **Total** |                        | **4h**                  |            | **Confidence: High** |

**Anti-Pattern to avoid:** Broad tasks like "Build the UI" for 20 hours with no subtasks or specific files.
