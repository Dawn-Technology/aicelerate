# Criterion Decision Procedure

Apply this procedure when finalizing every CSV row in order. Source collection may be grouped by surface; reuse its evidence rather than searching anew for each criterion.

## 1. Establish applicability

Identify what the criterion governs and locate relevant production source patterns. Trace materially different callers, variants, and values supplied by a CMS, API, translation catalog, menu tree, framework, or external service.

- If the governed feature is conclusively absent, use **N/A**.
- If the feature is present, continue.
- If applicability depends on unavailable content or runtime state, use **NEEDS_REVIEW**.

Trace the particular caller, not merely a resolver's fallback capability. A rollout list with omitted bundles does not prove that a specific template is selected for those bundles. If actual deployment selection is unavailable, describe an unconditional source defect only within its proven implementation boundary; do not claim both variants are deployed or site-wide affected counts. A cross-page consistency FAIL requires evidence of the relevant page set, not just two alternative implementations.

N/A is not appropriate merely because no violation pattern was found. Criteria that constrain ordinary page behavior, such as orientation or focus behavior, generally remain applicable to the page; absence of a prohibited implementation can support PASS.

## 2. Apply the static-analysis boundary

Apply the CSV `static_analyzable` gate before classifying instances:

| Value | Static interpretation |
|---|---|
| `yes` | Source can ordinarily establish PASS or FAIL when the boundary is complete. |
| `partial` | Decide source-proven instances; use NEEDS_REVIEW when content, rendering, runtime, or an exception remains unresolved. |
| `no` | Once applicability is established, use NEEDS_REVIEW with a specific rendered/interactive check. Source risks inform that check; do not turn them into PASS or FAIL in this static-only mode. Conclusively absent governed features may still be N/A. |

This deliberately conservative boundary prevents visual or interactive hypotheses from becoming confirmed defects. The flag does not turn a suspicious pattern into a finding. For `yes` and `partial`, applicability and normative exceptions still have to be established.

## 3. Classify each relevant source pattern

For each materially distinct pattern:

1. Determine the final semantics or behavior visible from source.
2. Check native HTML or a verified framework default.
3. Trace overrides, CSS cascade, state changes, responsive variants, and relevant callers.
4. Resolve applicable WCAG exceptions and alternatives.
5. Classify it as proven valid, definite violation, or unresolved.

Do not equate search hits with governed instances. A reusable component can represent many rendered instances; a single source hit can also be irrelevant after inspection.

Do not equate zero search hits with absence either. Confirm the search method actually reaches the target root, then rest the absence claim on an enumeration of the governed files. Where the enumeration was not performed, the pattern is unresolved, not absent.

Before proposing FAIL, read the normative SC and relevant definitions, not just its CSV hint or a technique. Record a link to the requirement and explain the failed condition. Best practice, an ARIA authoring-pattern mismatch, or a missing preferred technique alone is not a WCAG violation. If normative text cannot be verified, keep the proposal unresolved and explain what must be checked.

Use the [FAIL proof record](./evidence-patterns.md#fail-proof-record) for candidate instances. Reject an unsupported instance, not necessarily the entire criterion: another independently proven instance can still establish FAIL.

## 4. Coordinator finalization

Workers provide reviewed evidence; the coordinator alone sets the aggregate verdict. Read the row's `static_analyzable` flag from the CSV, then use the first matching condition below. This ordering is deliberate: incomplete work is not runtime uncertainty, and a worker's candidate violation never overrides a `no` flag.

| First matching condition | Decision |
|---|---|
| Decisive evidence has not been independently reviewed, or a material challenge remains unresolved | Keep pending; follow up. Partial report if work cannot finish. |
| `yes`/`partial` and at least one reviewed, source-proven violation with applicability/alternatives/exceptions resolved | FAIL; further defect enumeration is optional. |
| Source work needed to settle a non-FAIL verdict remains unfinished | Keep pending; do not assign NEEDS_REVIEW. |
| The governed feature is conclusively absent across the declared boundary | N/A. |
| `no` and the governed feature is present or its applicability depends on external evidence | NEEDS_REVIEW with the exact check. Never PASS or FAIL. |
| `yes`/`partial` and a relevant content/configuration/runtime dependency remains unresolved | NEEDS_REVIEW with the exact check. |
| `yes`/`partial` and every applicable pattern is supported as valid across the boundary | PASS. |

If no condition can be justified, keep the row pending and identify the missing evidence. Review must cover the facts and boundaries needed for that decision; mere review of selected examples is insufficient for PASS/N/A.

One violation is enough for aggregate FAIL. An exact violation total is optional unless naturally bounded by source. Use `at least N` when additional rendered or data-driven instances may exist.

Apply this aggregation only after the static gate above. Separate assessment progress from verdict: uninspected source that could change PASS/N/A/NEEDS_REVIEW leaves the assessment pending. For FAIL, further defect enumeration cannot change the verdict and is not a completion requirement. For NEEDS_REVIEW, inspect distinct relevant source patterns for provable violations, but do not enumerate unknowable CMS values or attempt prohibited runtime tests. State both the inspected boundary and the precise external check.

For each non-FAIL row, reconcile its contributing surfaces before accepting the verdict: source-resolved, externally unresolved, or not yet inspected. PASS cannot coexist with an externally unresolved relevant surface, even if the dependency implementation is excluded from general searches. N/A cannot rely on a field label, package name, or absence of a local integration to exclude behavior that an allowed embed/content value could introduce.

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
