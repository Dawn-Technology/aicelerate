# Criterion Decision Procedure

Apply this procedure to every CSV row in order. Evaluate the declared scope, not a convenient example.

## 1. Inventory applicability

Identify the feature governed by the criterion and enumerate candidate instances across all in-scope production sources. Record searched paths, file types, framework constructs, and search signals.

- If a bounded search proves the feature is absent, assign **⚪ N/A**.
- If absence cannot be established because markup is dynamic, external, sampled, or outside the selected scope, assign **⚠️ NEEDS_REVIEW**, not N/A.
- If present, continue.

N/A means the feature does not exist. It does not mean “not checked,” “not found by the first grep,” or “cannot be decided statically.”

## 2. Apply the static-analysis ceiling

Interpret `static_analyzable` as follows:

| Value | Static FAIL | Static PASS | Rule |
|---|---:|---:|---|
| `yes` | Allowed | Allowed | A bounded source implementation can ordinarily decide the criterion. |
| `partial` | Allowed | Conditional | Analyze all visible source evidence. Any unresolved rendered state makes the aggregate verdict NEEDS_REVIEW. |
| `no` | Allowed | Prohibited | Conclusive source evidence may prove a violation, but absence of such evidence becomes NEEDS_REVIEW with a concrete runtime check. |

This flag never suppresses a definite violation. For example, `outline: none` with no replacement can support a focus-visible FAIL even though a browser is normally required to prove PASS.

## 3. Evaluate every candidate instance

For each candidate:

1. Check native HTML behavior or a documented framework/component default.
2. Search for wrappers, prop combinations, CSS, event handlers, or overrides that bypass that behavior.
3. Verify the relevant implementation and generated semantics as far as source permits.
4. Classify the instance as proven valid, definite violation, or unresolved.

A native control proves only itself. A `<button>` does not establish that every application control satisfies Keyboard or Name, Role, Value. A `<label for>` does not establish that every form input is labeled.

## 4. Aggregate one criterion verdict

Use this strict precedence:

1. One or more definite violations → **❌ FAIL**.
2. No definite violations, but one or more unresolved instances → **⚠️ NEEDS_REVIEW**.
3. Every applicable candidate has positive evidence and PASS is permitted by the static-analysis flag → **✅ PASS**.
4. No candidates after a bounded applicability search → **⚪ N/A**.

Do not average instances or lower FAIL to NEEDS_REVIEW because other instances pass.

## 5. Record evidence coverage

Every criterion ledger entry must include:

- searched paths and file types;
- search signals, including framework-specific equivalents;
- total candidate count;
- evaluated, violating, and unresolved counts;
- up to 10 representative source locations;
- the reasoning that connects evidence to the criterion;
- remediation for FAIL or exact browser/AT verification for NEEDS_REVIEW.

For dynamic collections where an exact total cannot be determined, write `at least N` and mark unresolved coverage. Never invent a precise count.

## 6. Assign severity or review priority

Use [`severity-guidance.md`](./severity-guidance.md). Severity describes user impact, not WCAG level. NEEDS_REVIEW has a review priority rather than a confirmed defect severity.

