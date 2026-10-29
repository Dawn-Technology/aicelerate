---
description: The phrasing write-plan's description explicitly claims ("break down a ticket") — the green twin of the decompose-routes-to-a-skill case.
expected_outcome: write-plan fires and produces an implementation plan with small, sized tasks.
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Break down this ticket into an implementation plan: "Add CSV export to the orders page — a button that downloads the current filtered list as CSV with the visible columns. Acceptance: export respects active filters, handles 10k rows, filename contains the date."
