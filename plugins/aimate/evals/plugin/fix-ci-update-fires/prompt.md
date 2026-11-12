---
description: A request to update a PR from its target and resolve conflicts. fix-ci should fire, not a review or feedback skill.
expected_outcome: The fix-ci skill fires and the reply starts on the branch update instead of reviewing the PR.
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Merge request 31 has fallen behind main and now has conflicts. Bring it up to date with main and resolve the conflicts if they are straightforward.
