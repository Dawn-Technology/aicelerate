---
description: A natural commit-message request with the staged diff pasted inline. write-commit-message should fire and the message should follow the Dawn rules.
expected_outcome: The write-commit-message skill fires and the drafted message has a short subject without a Conventional-Commits prefix and a body explaining why and how.
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

I've staged my changes — write the commit message for them. Here is the staged diff:

```diff
diff --git a/src/export.php b/src/export.php
--- a/src/export.php
+++ b/src/export.php
@@ -18,7 +18,7 @@ class CsvExporter
-                $order->orderedAt->format('m/d/Y'),
+                $order->orderedAt->format('Y-m-d'),
diff --git a/tests/run.php b/tests/run.php
--- a/tests/run.php
+++ b/tests/run.php
@@ -26,7 +26,7 @@
-check(str_contains($csv, '03/09/2026'), 'export date format');
+check(str_contains($csv, '2026-03-09'), 'export date format');
```
