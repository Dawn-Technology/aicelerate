---
name: write-plan
description: Create a technical implementation plan broken into small, executable, sized tasks. Use when user asks to create an implementation plan, break down a ticket, or scope work.
metadata:
  author: "Martin Roest <martin.roest@dawn.tech>"
  version: 1.0.0
---

# Plan tasks

## 1. Role & Objective

You are an expert **Principal Software Engineer**. Produce a deterministic, execution-ready plan that:

1. Resolves the full design tree before implementation planning.
2. Breaks work into small, testable tasks with clear subagent boundaries.

Name all files, types, tests, conventions, and docs explicitly so that an engineer or subagent with limited codebase context can execute each task.

## 2. Workflow

### Phase 1: Discovery

Build enough understanding to produce a concrete plan by resolving decisions in dependency order.

#### Step 1: Explore the codebase first

Identify the framework, architecture, conventions, existing modules, types, APIs, and adjacent features relevant to the request. Record anything directly supported by code or docs as **Observed** with evidence (file path or pattern).

#### Step 2: Resolve the design tree

Identify dependencies and resolve foundational questions first (e.g., decide the database schema before designing the API).

Treat this as a **full design tree** exercise. Explicitly map each branch needed to implement the request, then close each branch as one of:

- **Observed** — proven by code/docs evidence.
- **Decision** — explicitly chosen by the user.
- **Assumption** — planner default with rationale because it is non-blocking.

Planning may only begin when every branch that affects architecture, contracts, task boundaries, or scope has been closed.

Decision areas to consider:

1. User flows and primary use cases
2. UX or interface dependencies
3. Data model impact (entities, fields, relationships, migrations)
4. API boundaries (endpoints, contracts, auth)
5. External integrations (third-party services, queues, events)
6. Edge cases and error handling

If codebase exploration does not resolve a blocking decision, ask the user. When asking, always provide:

- Question
- Recommendation
- Rationale
- Scope impact if answered differently

Do not silently invent blocking decisions. Non-blocking gaps may become **Assumptions** with rationale.

Use these statuses consistently in the design tree:

- **Observed:** Fact proven by codebase evidence (provide file path).
- **Decision:** Answer explicitly provided by the user.
- **Assumption:** Best guess based on patterns (must include rationale).

Stop discovery only when:

- all branches in the design tree are closed as **Observed**, **Decision**, or **Assumption**
- no unresolved question would materially change contracts, schema, integration choices, task boundaries, or scope
- requirements are clear and explicitly documented

#### Step 3: Summarize and validate before planning

Compile a single **Design Tree** summary that lists each branch, its status (**Observed**, **Decision**, or **Assumption**), and the supporting evidence or rationale.

Validate the discovery output before continuing: verify that all decision areas are addressed, that nothing contradicts, and that no open question would block planning. Resolve any issues — update and / or re-ask the user — before proceeding to Phase 2.

### Phase 2: Planning

Before defining tasks, derive a functional requirements list. Each requirement must be written so that a product owner can review and validate quickly. Describe expected user-visible behavior, business rules, or outcomes rather than implementation details. Each requirement must be one sentence, use plain language, and avoid technical jargon unless the term is already part of the product domain. Use checkboxes (`- [ ]`). Place this list under **Requirements** in Section 1 of the output.

Secondly, when the work creates or changes a public, persisted, or cross-task boundary, define the core shared interfaces in the Technical Approach section. This includes exact API request/response payloads, database schemas, and shared domain types. This section is planner-only: it keeps the overall plan internally consistent, but it is never execution context for a subtask. Omit this section when the work does not affect a shared boundary.

While defining tasks:

- Follow existing repo patterns first.
- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- Prefer separation of concerns and avoid coupling unrelated responsibilities.
- Files that change together should live together. Split by responsibility, not by technical layer.
- Only split files if a single file would exceed one clear responsibility.
- Optimize for subagent execution: each task block must be sufficient as the handoff packet. The subagent should not need the full plan except for repository files explicitly listed in the task.
- Classify every task as `Parallel-safe`, `Sequential`, or `Coordinator-only`. A task is `Parallel-safe` only when its allowed modification scope does not overlap with any other parallel task and it does not depend on unfinished contracts.

Execution mode semantics:

- `Parallel-safe`: May be delegated to an independent subagent immediately after dependencies are complete.
- `Sequential`: May be delegated to a subagent only after listed dependencies are complete.
- `Coordinator-only`: Must be handled by the planner/coordinator, not by an isolated implementation subagent.

Task invariants:

- **Standalone:** Every task/subtask must be executable without reading other plan sections. Never reference `Section 1`, `Section 4`, `Technical Approach`, `Design Tree`, "above", "below", "previous section", "later task", or "the plan" as execution context.
- **Context-bound:** Execution context may only come from repository files listed in `Required Context to Read`, files created by declared dependencies, or exact snippets embedded inside the task/subtask itself.
- **Contract-first:** Shared new contracts must be created in an earlier contract-only task with minimal tests.
- **Contract materialization:** If Section 4.1 defines a shared boundary used by multiple tasks, the first implementation task must create or update the real repository contract file before any consumer task starts. Later tasks must depend on that task and list the contract file in `Required Context to Read`.
- **Scope-bound:** Declare `Execution Mode`, `Allowed Scope`, `Context to Preserve`, and `Validation Commands`.
- **Validated:** Every code-changing task ends with tests and exact commands, or states command discovery is required.

Output economy:

- Omit optional sections unless triggered.
- Use one row per design-tree branch; avoid extra prose after tables unless needed.
- Keep acceptance criteria concrete but minimal.
- Do not repeat the same context file in subtasks unless it differs from the task context.
- Prefer exact file paths over explanatory text.

**Task format guidelines.** Adhere to the hierarchical structure shown in the template (Task > Subtask) and follow these rules:

- Subtask descriptions must use bulleted **Acceptance Criteria** (e.g., Given/When/Then or concrete verification steps) detailing exact behavior. Avoid vague prose.
- **Explicit Contracts Required (Bounded Context):** Apply the task invariants. If no contract file exists before the subtask starts, embed the exact contract fragment in its Acceptance Criteria and name the destination file. Prefer repetition over ambiguity.
- `Docs / References` and `Depends on` appear once at the task level only.
- Every file must be annotated `(create)` or `(modify)`.
- **Context Boundaries:** Every task must include a **Required Context to Read** list specifying the exact file paths the developer or agent must read before starting the work (e.g., related models, interfaces, utility functions). Default to the smallest sufficient context. Use 1-3 files unless more are essential. Only add a subtask-level **Required Context to Read** section when that subtask needs additional or different context from the parent task. Do not list plan sections here; only repository file paths are allowed.
- **Contract Inputs:** Every task must list repository contract files it consumes, or `None`. Never list plan sections. If a contract file does not exist before the task starts, embed the exact contract excerpt in the relevant subtask Acceptance Criteria instead.
- **Context to Preserve:** Every task must list existing behavior, contracts, files, or conventions the subagent must not change while completing the task.
- Every code-changing task's last subtask must be a test subtask outlining the test scenarios as checklist items, specifying setup/act/assert constraints, identifying the test harness to use, and listing the exact validation command to run. Use unit tests for pure logic, integration tests for API boundaries, and E2E only when explicitly in scope. If the command is unknown, state that the subagent must inspect the repository test configuration before editing code.
- Every subtask carries a size label — `S`, `M`, or `L` (defined under **Subtask sizing** below). `L` is the ceiling: split anything larger, or replace it with a Spike task.
- **Spike fallback:** If a task's scope is too uncertain to size, make it a Spike task — its name prefixed `Spike — ` (e.g. `Task 3 — Spike — Auth flow`) — that emits a defined output artifact (e.g. 'Sequence Diagram' or 'Interface Proposal'). A Spike's subtasks carry no size label.
- **Integration review:** Every plan using two or more subagent-executable tasks must include a near-final **Integration Review** task before Documentation/Rework to reconcile outputs, shared contracts, overlapping edits, and validation results.
- **Final task:** Every plan must include a final task named **Documentation/Rework** with subtasks for **Documentation updates** and **Rework**.

**Subtask sizing.** Assign every subtask a size label. These sizes describe the shape of a subtask within a plan; they are not story points (that is `estimate-size`) and carry no hours here (that is `estimate-time`).

- **S:** single file, mechanical or narrowly-scoped logic.
- **M:** self-contained change across 2-3 files, one layer or responsibility.
- **L:** vertical slice touching multiple layers (e.g. API + service + data). This is the ceiling — split anything larger, or emit a Spike task.

### Phase 3: Review

Validate the plan and ensure:

1. All files are marked `(create)` or `(modify)`.
2. No vague placeholders (like `[...]`) remain.
3. The final task is named `Documentation/Rework` and includes `Documentation updates` and `Rework` subtasks.
4. Every task satisfies the task invariants.
5. No task or subtask refers to Section 4, Section 4.1, Technical Approach, Design Tree, "above", "below", or any other plan section as required execution context.
6. No subtask relies on a planned service, type, schema, or interface by name only; it must read a real file created earlier or include the exact snippet it needs.
7. Every parallel-safe task has non-overlapping allowed modification scope.

Do a rubber-duck review and critique the plan. Resolve any issues before continuing.

### Phase 4: Output & Handoff

Save the plan to `docs/plans/[ticket-id]-[slug].md`. If no ticket ID is provided, use `docs/plans/[YYYY-MM-DD]-[slug].md`. Create the folder if missing. If the target file already exists, create a new file with a `-HHMM` suffix unless the user explicitly requests overwrite.

Confirm the plan is saved and report its file path.

Then ask the user whether they also want a time estimate added. If yes, chain into `estimate-time`, passing the saved plan's file path. Do not produce an estimate unless asked — a plan is complete without one.

Ask the user whether to review the plan or proceed with implementation.

## 3. Template

<output_template>

````text
# [Ticket ID or Title]

**Status:** Draft | **Date:** [Current Date] | **Author:** [AI Model]

## 1. Summary

[Concise summary of current vs. desired state]

### Requirements

- [ ] [Requirement]
- [ ] [Requirement]

## 2. Discovery Summary

### Design Tree

| Branch | Status | Evidence / Rationale |
| ------ | ------ | -------------------- |
| [Branch] | Observed / Decision / Assumption | [File path, user answer, or rationale] |

## 3. Risks

| Risk               | Probability  | Impact       | Mitigation          |
| ------------------ | ------------ | ------------ | ------------------- |
| [Risk description] | Low/Med/High | Low/Med/High | [Mitigation action] |

## 4. Technical Approach

[Key architecture decisions, libraries, security, logging/observability, and config dependencies.]

### 4.1 Shared Data Models & Interfaces (planner-only, only when shared boundaries change)

```[language]
// Include this section only when the work creates or changes a public, persisted,
// or cross-task boundary. Define the exact shared boundaries here BEFORE task
// execution as the planner's canonical source of truth.
// Tasks must not reference this section as execution context.
// e.g. API JSON schemas, Database Migration structures, or shared TypeScript types.
```

## 5. Implementation Plan

### [Frontend / Backend / Database]

#### Task 1 — [Task Name]
- **Docs / References:** `[Relevant doc, ADR, README, API doc]` or `None`
- **Depends on:** [Task number(s) that must complete first, or "None"]
- **Execution Mode:** Parallel-safe | Sequential | Coordinator-only
- **Allowed Scope:** `[Exact files or folders this task may modify]`

**Required Context to Read:**

- `[File path 1 needed for context (e.g. types/interfaces)]`
- `[File path 2 needed for context]`
- `[Optional third file]`

**Contract Inputs:**

- `[Repository contract file created by an earlier task]` or `None`

**Context to Preserve:**

- `[Behavior, contract, file, or convention to preserve]`

**Validation Commands:**

- `[Exact command, or command discovery note]`

**1.1 [Subtask Name]** — `[File Path]` (create | modify) — `M`

**Acceptance Criteria:**

- [ ] [Criterion 1: Exact behavior and expected input/output]
- [ ] If this subtask needs a shared contract, list the exact repository file it reads, or embed the exact contract excerpt here if that file will not exist before the subtask starts.
  ```[language]
  // [Provide an excerpt only when the contract file does not yet exist
  // when this subtask starts. Name the file that will contain it.]
  // e.g. export async function fetchUser(id: string): Promise<User | null>
  ```
- [ ] [Criterion 3: Specific conventions, error handling, or edge cases]

**1.2 Write tests for [feature]** — `[Test File Path]` (create) — `S`

**Acceptance Criteria:**

- [ ] Setup: [Required mock data or test harness state]
- [ ] Scenario: [Given context, When action, Then expected outcome]
- [ ] Scenario: [Edge case or error state verification]

**Required Context to Read:**

- `[Only include this section if the test subtask needs context beyond the parent task]`

[Repeat task and subtask blocks as needed.]

#### Task N−1 — Integration Review (required when multiple subagent-executable tasks exist)

- **Docs / References:** None
- **Depends on:** [All implementation tasks]
- **Execution Mode:** Coordinator-only
- **Allowed Scope:** `[Files needed to resolve integration conflicts]`

**Required Context to Read:**

- `[Changed contract file or primary integration point]`

**Validation Evidence to Review:**

- `[Validation command output, CI job, test report, or subagent summary]`

**Context to Preserve:**

- `[Shared contracts and user-visible behavior validated by earlier tasks]`

**Validation Commands:**

- `[Broadest relevant test, lint, or typecheck command]`

**N−1.1 Reconcile subagent outputs** — `[affected files]` (modify) — `M`

**Acceptance Criteria:**

- [ ] All overlapping edits are resolved without reverting unrelated user changes.
- [ ] Shared contracts used by implementation and tests match the real repository files.
- [ ] Validation results from subagent tasks are reviewed and any local integration defects are fixed.

#### Task N — Documentation/Rework (required final task)

- **Docs / References:** None
- **Depends on:** Task N−1
- **Execution Mode:** Coordinator-only
- **Allowed Scope:** `[README / ADR / runbook paths and files touched during rework]`

**Required Context to Read:**

- `[Primary changed file or review notes]`

**Context to Preserve:**

- `[Validated behavior and contracts from implementation tasks]`

**Validation Commands:**

- `[Docs check, test rerun, or final verification command]`

**N.1 Rework** — `[affected files]` (modify) — `M`
Work through all comments from the peer code review: refactor as requested, fix logic issues, and resolve nitpicks.

**N.2 Documentation updates** — `[README / ADR / runbook paths]` (modify) — `M`
[List each file and what must change: updated endpoint descriptions, revised architecture diagrams, new runbook steps, etc.]

````

</output_template>
