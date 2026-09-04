# Criterion Decision Procedure

Apply this procedure to every CSV row in order and to the declared source boundary—not a convenient example.

## 1. Establish applicability

Identify what the criterion governs and locate relevant production source patterns. Trace materially different callers, variants, and values supplied by a CMS, API, translation catalog, menu tree, framework, or external service.

- If the governed feature is conclusively absent, use **N/A**.
- If the feature is present, continue.
- If applicability depends on unavailable content or runtime state, use **NEEDS_REVIEW**.

N/A is not appropriate merely because no violation pattern was found. Criteria that constrain ordinary page behavior, such as orientation or focus behavior, generally remain applicable to the page; absence of a prohibited implementation can support PASS.

## 2. Apply the static-analysis boundary

Use the CSV `static_analyzable` value as guidance:

| Value | Static interpretation |
|---|---|
| `yes` | Source can ordinarily establish PASS or FAIL when the boundary is complete. |
| `partial` | Decide source-proven instances; use NEEDS_REVIEW when content, rendering, runtime, or an exception remains unresolved. |
| `no` | Do not issue PASS from source alone. Use NEEDS_REVIEW unless source independently proves the complete failure condition without requiring rendered judgment. |

The flag does not turn a suspicious pattern into a finding. Applicability and normative exceptions still have to be established.

## 3. Classify each relevant source pattern

For each materially distinct pattern:

1. Determine the final semantics or behavior visible from source.
2. Check native HTML or a verified framework default.
3. Trace overrides, CSS cascade, state changes, responsive variants, and relevant callers.
4. Resolve applicable WCAG exceptions and alternatives.
5. Classify it as proven valid, definite violation, or unresolved.

Do not equate search hits with governed instances. A reusable component can represent many rendered instances; a single source hit can also be irrelevant after inspection.

## 4. Aggregate the criterion

Use strict precedence:

1. At least one definite violation → **FAIL**.
2. No definite violation and at least one unresolved applicable pattern → **NEEDS_REVIEW**.
3. Every applicable pattern proven valid and static PASS permitted → **PASS**.
4. Governed feature conclusively absent → **N/A**.

One violation is enough for aggregate FAIL. An exact violation total is optional unless naturally bounded by source. Use `at least N` when additional rendered or data-driven instances may exist.

## 5. Record evidence

Record:

- searched source boundary and relevant signals;
- applicability reasoning;
- the relevant normative exceptions and evidence resolving each one for a FAIL;
- concrete source locations or verified framework behavior;
- unresolved content/runtime/process boundary, if any;
- reasoning connecting the evidence to the normative requirement;
- remediation for FAIL or exact manual verification for NEEDS_REVIEW.

Reconcile shared evidence before reporting. A report cannot claim the same feature is absent under one criterion and present under another, claim PASS while acknowledging unresolved applicable instances, or call a representative review exhaustive.

## 6. Assign impact

Use [`severity-guidance.md`](./severity-guidance.md). Severity describes a confirmed FAIL's user impact; NEEDS_REVIEW uses review priority. WCAG A/AA level is reported separately.
