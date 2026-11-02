---
description: Precision check — asking whether a ticket is ready must not pull in implement-ticket.
expected_outcome: implement-ticket does not fire; the reply assesses readiness instead of building.
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Is ticket ABC-123 ready for development? Here is its current text: "Add a phone number field to the customer profile, shown on the detail page and editable in the edit form. Validation: digits, spaces and + only, max 20 characters. Acceptance: field persists, invalid input shows an error, existing customers unaffected."
