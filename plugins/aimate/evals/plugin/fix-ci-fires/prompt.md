---
description: A natural request to get a red PR green. fix-ci should fire, not a review or feedback skill.
expected_outcome: The fix-ci skill fires and the reply starts working through the PR's CI instead of reviewing it.
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

PR 214 on our repo has a red pipeline — eslint and the type check are both failing after the dependency bump. Can you get it back to green? Keep going until the checks pass.
