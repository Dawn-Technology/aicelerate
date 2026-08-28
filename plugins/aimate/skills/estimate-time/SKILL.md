---
name: estimate-time
description: Add a time estimate in hours to an existing implementation plan. Use when the user asks to estimate a plan or task list, or asks how long the work will take.
metadata:
  author: "Martin Roest <martin.roest@dawn.tech>"
  version: 1.0.0
---

# Estimate Time

Add an hour-based time estimate to an existing implementation plan. This skill estimates time in hours; it does not size work in story points (that is `estimate-size`) and it does not plan or break down work (that is `write-plan`).

## Input

This skill requires the path to an existing plan file, normally one produced by `write-plan`. `write-plan` saves the plan before offering to estimate, so when chained it passes that path.

If invoked with no plan-file path, ask the user for one, or offer to run `write-plan` first. Do not estimate without a plan file — this skill reads the plan's structure; it does not re-run discovery.

## Workflow

### Step 1 — Read the plan

Read the plan file. Use its **Design Tree** and **Implementation Plan** sections as the sole input. Do not re-derive the design tree or re-plan the tasks.

### Step 2 — Derive a risk multiplier per task

For each task, determine which Design Tree branches its work rests on, then assign a risk multiplier:

- **Low (1.0×):** the task rests only on `Observed` and/or `Decision` branches — scope fully known.
- **Medium (1.5×):** the task rests on one or more `Assumption` branches that do NOT define a public, persisted, or cross-task contract, schema, or integration boundary.
- **High (2.0×):** the task rests on an `Assumption` branch that DOES define such a boundary, or on a Spike output, or the Design Tree does not cover the task's scope (do a quick codebase check; if still unclear, use High).

### Step 3 — Map sizes to hours and compute the base

Map each subtask's size label to a fixed hour bucket:

- **S = 1h**
- **M = 2h**
- **L = 4h**

Sum a task's subtask hours to get its base, then multiply by the task's risk multiplier to get the task total.

**Spike tasks** (identified by the `Spike — ` prefix in the task name; their subtasks carry no size label) take a fixed **2h base** before the risk multiplier is applied.

### Step 4 — Write the estimate back into the plan (idempotent)

Write the estimate into the same plan file — do not create a separate file.

- For each task, add a task-level line `- **Estimate:** [base × risk = total]` (e.g. `- **Estimate:** 4.0h × 1.5 = 6.0h`). If the line already exists, replace it rather than adding a second one.
- Add or replace the Section 6 Estimation table and its Breakdown:

  ```markdown
  ## 6. Estimation

  | Component | Task | Estimate (Base × Risk) | Risk | Notes |
  | --------- | ---- | ---------------------- | ---- | ----- |
  | [Component] | [Task Name] | [X.X]h | [Low (1.0x) / Med (1.5x) / High (2.0x)] | [Notes] |
  | **Total** |  | **[Total]h** |  |  |

  **Breakdown:**

  - [Component]: [X]h
  ```

  If a Section 6 block already exists, replace it in place — never append a second one.

### Step 5 — Review

Verify the math: for every task, `base × risk = total`, and the Section 6 Total equals the sum of the task totals. Correct any mismatch before reporting.

Report the total and the per-task breakdown, and confirm the estimate was written back into the plan file.
