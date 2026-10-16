# Policy Precedence

Apply rules in this order:

1. Explicit instruction in the current request.
2. Project instructions, accepted ADRs, and project-local skills.
3. Xcode project/workspace, package, deployment-target, and toolchain constraints.
4. Strong evidence from the repository's established design.
5. Company iOS policy.
6. General Apple-platform guidance.

Project instructions are every instruction file the repository keeps for agents: `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, and `.github/instructions/*.instructions.md`. Teams may use any of them; they rank together. When they contradict each other, report the contradiction and follow the more specific one.

An older local convention does not automatically beat a current explicit decision. Resolve contradictions by evidence and scope.

When company policy is not followed, report:

- the policy;
- the project instruction or evidence that outranks it;
- the choice made for this task;
- a safe incremental alignment when one directly serves the request.

Do not turn an unrelated feature or review into a migration proposal. Raise a separate recommendation only when the existing design causes a concrete correctness, safety, testing, or change-cost problem.
