---
name: write-plan
description: Create an implementation plan with sized tasks from a prepared ticket, for planning and estimation. Use when the user asks to create an implementation plan, break down a ticket into tasks, or size the work. Input is the brief that prepare-ticket produces, or an equivalent ticket with acceptance criteria; this skill does not do its own discovery. Optional in the build loop.
metadata:
  author: "Martin Roest <martin.roest@dawn.tech>"
  version: 2.0.0
---

# Plan tasks

Turn a prepared ticket into an implementation plan with sized tasks. The plan serves planning and estimation; estimate-time attaches hours to it. The build loop does not require a plan, and nobody types the code by hand anymore, so the plan is a reference, not a contract.

## Size gate, always first

If the whole request fits one small, focused change (roughly one concern, a handful of files, a single session) do not produce a plan document. Say the work needs no plan and return a single task with its acceptance criteria.

## Input

The input is a prepared ticket: the agent-ready brief from prepare-ticket, or any ticket that already carries intent, acceptance criteria and a definition of done. The decisions in that brief are the plan's decisions.

- Do not reopen them, do not hunt for gaps, do not build a design tree. That work is prepare-ticket's job and it has been done.
- Light code exploration is fine when the brief references code you need to see to cut sensible tasks. Exploration grounds the tasks; it never reopens decisions.
- Input not prepared (no criteria, open contradictions)? Say that prepare-ticket would normally come first, state your assumptions explicitly at the top, and deliver the plan on those assumptions.

## Always deliver

Deliver the plan in this same response. Questions may accompany it under **Open questions**, with the assumption you proceeded on next to each, but they never replace the plan. When the codebase is unreachable, say so once at the top, label file paths as placeholders, and plan against your stated stack assumption.

## The plan

Break the work into tasks that are small, independently executable, and in dependency order. Per task:

1. **Title**, imperative and concrete.
2. **What and where**: the files, components or seams it touches, named as concretely as the codebase allows.
3. **Size**: S, M or L relative to the other tasks (estimate-size conventions when the project has them).
4. **Done when**: one checkable statement.

Close the plan with the task list as a short numbered overview, so estimate-time and a reader can take it in at a glance.
