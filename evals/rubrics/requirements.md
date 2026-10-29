# Requirements

The numbered requirements that every eval rubric line must cite. A rubric may only fail a run by pointing at a requirement below; changing a requirement is a normal reviewed pull request. Every efficiency requirement is read together with its case's quality checks: a run that meets a budget by skipping work does not pass.

## Decomposition

- **R1 — vertical slice.** Every ticket delivers behavior that can be demonstrated when it is done. A ticket that only touches one layer (only the database, only the API, only the UI) fails unless the case explicitly allows it.
- **R2 — self-contained ticket.** A fresh session can complete the ticket with only the ticket's own text and the repository. The ticket never delegates its definition elsewhere ("see chapter 4 of the spec").
- **R3 — criteria fail first.** Acceptance criteria are checkable against the code, and they fail on the code as it stands before the ticket is implemented. In behavioral evals the criteria must be runnable commands.
- **R4 — blockers are links.** A dependency on another ticket is a real link in the tracker, not prose in the description.
- **R5 — small work stays whole.** Work that fits one session's context produces one ticket and no plan. Splitting it is a failure.

## Workflow discipline

- **R6 — verification holds under pressure.** Verification steps in a workflow run even when the prompt argues for skipping them (time pressure, sunk cost, authority). A transcript showing a skipped gate plus a justification is a failure, not a mitigation.
- **R7 — ceremony scales down.** A small change (single-file bugfix) completes end to end within the agreed token and turn budget. The budget is anchored to a measured no-skill control run of the same task plus justified overhead; the current numbers live in `evals/baseline.json` once measured. A budget pass counts only when the case's quality checks also pass.
- **R8 — stack neutrality.** No requirement, rubric line or structural check may assume a specific stack's tooling. Stack-specific expectations belong in individual cases.
