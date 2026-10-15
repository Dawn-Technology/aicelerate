---
type: llm
---

PASS if the drafted commit message has a short imperative subject line with no Conventional-Commits prefix (no "fix:", "feat:" or similar), followed by body text that explains the problem (dates read wrong in the US format) and the approach, as the Dawn commit rules require.

FAIL if the message is subject-only, uses a type/scope prefix, merely lists the files changed, or restates the diff line by line instead of explaining why.
