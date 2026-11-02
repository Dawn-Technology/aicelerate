---
description: Precision check — a review request about a commit must not pull in write-commit-message.
expected_outcome: No commit-message skill fires; the reply reviews the change instead of drafting a message.
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Review my last commit for bugs. Here is what it changed:

```diff
diff --git a/src/export.php b/src/export.php
--- a/src/export.php
+++ b/src/export.php
@@ -18,7 +18,7 @@ class CsvExporter
-                $order->orderedAt->format('m/d/Y'),
+                $order->orderedAt->format('d/m/Y'),
```
