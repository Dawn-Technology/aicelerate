---
name: split-spec
description: Use when asked to break down, split, cut or carve a spec, feature, epic or any larger piece of work into tickets — including "break this work down into tickets", "split this spec", "turn this into tickets", "maak hier tickets van" or "knip deze spec op" — and the input is bigger than one ticket. Produces vertical, independently deliverable tickets a developer can pick up without the spec. Applies even when the spec is pasted inline in the chat. Not for turning a single ticket into an implementation plan (use write-plan) and not for checking one ticket's readiness (use prepare-ticket).
metadata:
  author: "Tim Dinh <tim.dinh@dawn.tech>"
---

# Split a spec into tickets

Turn a spec, feature description or epic into tickets that each deliver demonstrable behavior and stand on their own. The test of a good split: a fresh session, given only one ticket and the repository, can finish it — and when it is finished, there is something to show.

## Before cutting

Read the spec, then ground it: explore the parts of the codebase the work touches. A split made without reading the code produces tickets that fight the architecture.

**Size gate — always first.** If the whole change fits one ticket (one focused session: roughly one concern, a handful of files), produce exactly one ticket and say the work needs no split. Splitting small work is a failure, not thoroughness.

## Cutting rules

- **Vertical slices only.** Every ticket delivers behavior that can be demonstrated: something a user, caller or operator can see work. A ticket that only touches one layer — only the database, only an API, only UI — is wrong unless physically unavoidable, and then the deviation is named in the ticket.
- **First ticket is the thinnest end-to-end slice** (tracer bullet): one valid path from entry to effect, however narrow. Later tickets widen it.
- **Preparatory refactor first** when existing behavior must keep working through the change: ticket 1 reshapes without behavior change, and says so.
- **Wide refactors** (the same change in many places) split as expand, migrate in batches, contract — never one ticket per place.

## Output format

The approval list is a plain numbered list of titles with demo lines. Every full ticket after approval starts with its own heading, exactly `### Ticket <n>: <title>` — one heading per ticket, nothing else at that heading level between tickets. Tools and reviewers count tickets by these headings, so a ticket without one does not exist.

## Each ticket must carry

1. **Title** — imperative, concrete.
2. **Demo line** — one sentence: "Demo: …what can be shown when this is done."
3. **Description** — all context the ticket needs, inline. Never a pointer like "see chapter 4 of the spec"; a fresh session gets only this text and the repo.
4. **Acceptance criteria that fail today** — checkable statements that are false on the current code and become true when the ticket is done. Prefer criteria a command can verify.
5. **Blockers as links** — a dependency on another ticket is an explicit reference ("Blocked by: #2"), created as a real tracker link when tracker routing is configured. Never prose like "after the previous work is done".

## Workflow

1. Apply the size gate.
2. Cut the slices and present a **numbered list first** — titles and demo lines only — for approval, before writing full tickets. In an unattended run where nobody can approve, say so and continue with the full tickets.
3. Write the full tickets. When tracker routing is configured (see configure-mcp), offer to create them with real blocker links; otherwise output them as markdown.

## Bad input

- **Spec already cut per layer** ("phase 1 database, phase 2 backend, phase 3 frontend"): cut vertically anyway and name the deviation from what was asked, with the reason.
- **Too big to split honestly** (a dozen-plus features, "V1 of the portal"): do not produce forty tickets. Propose scoping: ask which features define the first demonstrable version, and split only that.
- **Too vague to split** (no criteria, contradictions): list the open questions. Never invent acceptance criteria as if the requester wrote them.
