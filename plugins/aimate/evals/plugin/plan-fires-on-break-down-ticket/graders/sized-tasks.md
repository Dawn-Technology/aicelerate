---
type: llm
---

PASS if the reply is an implementation plan broken into small, individually executable tasks, each with some size or effort indication, covering the export respecting filters, the 10k-row handling and the dated filename. The case provides no codebase, so placeholder file names are expected; disclosing that openly (for example "these file names are placeholders, point me at the repo to match them") is correct behavior and must never count against the plan — an agent that silently invents concrete file names is worse, not better.

FAIL if the reply is one undifferentiated task list without sizing, starts writing the implementation code itself, or ignores any of the three acceptance criteria.
