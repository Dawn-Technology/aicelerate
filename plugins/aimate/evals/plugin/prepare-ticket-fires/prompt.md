---
description: A natural readiness question with the ticket pasted inline. prepare-ticket should fire and deliver a verdict, not an implementation.
expected_outcome: The prepare-ticket skill fires; the reply challenges the ticket against what it can see and ends with a readiness verdict and a single next action.
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Is this ticket ready for a developer to pick up?

Ticket USER-91: "Customers keep complaining about the slow list page. Make it faster. Also the layout jumps around while loading. Priority: high."
