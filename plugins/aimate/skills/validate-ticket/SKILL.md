---
name: validate-ticket
description: "[DEPRECATED] Renamed to prepare-ticket. Use only when validate-ticket is named explicitly; otherwise use prepare-ticket."
metadata:
  author: "Martin Roest <martin.roest@dawn.tech>"
  version: 2.0.0
  dependencies:
    - prepare-ticket
---

> [!WARNING]
> `validate-ticket` is renamed to `prepare-ticket`. This name still works and hands over to `prepare-ticket`, but it will be removed in a future major release. Update any prompt, agent definition, or project instruction that names it.

# Validate Ticket (deprecated)

This skill only keeps the old name working. All behaviour lives in [`prepare-ticket`](../prepare-ticket/SKILL.md).

1. **Tell the user first**, before any other work: "`validate-ticket` is now `prepare-ticket`. Running `prepare-ticket` for you — please use the new name from now on." Say this every time the skill runs.
2. **Run `prepare-ticket`** with the same request and arguments — the ticket identifier or pasted text, any focus, and any standing directive about tracker writes. Follow it exactly as if the user had called it by name.
