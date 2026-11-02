---
type: llm
---

PASS if the reply cuts the work into tickets where the first ticket delivers one demonstrable end-to-end slice (for example: one valid row imported from upload through stored contact), and no ticket covers only a single layer such as "parsing only", "storage only" or "endpoint only".

FAIL if the tickets mirror the layers (parser ticket, storage ticket, API ticket), if any ticket cannot be demonstrated on its own, or if the reply is a single implementation plan rather than independent tickets.
