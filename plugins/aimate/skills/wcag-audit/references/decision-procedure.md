# Criterion Decision Procedure

Apply this procedure to every CSV row in order. Evaluate the declared scope, not a convenient example.

## 1. Inventory applicability

Identify the feature governed by the criterion and enumerate candidate instances across all in-scope production sources. Record searched paths, file types, framework constructs, and search signals.

Separate source-controlled values from values supplied by a CMS, API, translation catalog, menu tree, or external media service. A template candidate is not fully evaluated when its accessibility outcome depends on unavailable content.

- If a bounded search proves the feature is absent, assign **⚪ N/A**.
- If absence cannot be established because markup is dynamic, external, sampled, or outside the selected scope, assign **⚠️ NEEDS_REVIEW**, not N/A.
- If present, continue.

N/A means the feature does not exist. It does not mean “not checked,” “not found by the first grep,” or “cannot be decided statically.”

An unfinished bounded source search is not a WCAG uncertainty and must not be converted to NEEDS_REVIEW. Finish classifying the source inventory. If resource limits prevent that, use partial-report mode: mark the row `CONFIRMED_FAIL` when a definite violation already proves FAIL, otherwise use `INCOMPLETE / ⏳ NOT_EVALUATED`.

Some criteria govern how existing UI behaves rather than the presence of a special widget. Treat the underlying UI as the candidate inventory:

- If focusable UI components exist, 2.1.2 and 3.2.1 are applicable. Absence of a trap or focus-triggered context change is favorable evidence, not evidence that the criterion is N/A.
- If controls whose setting or value can change exist (text fields, checkboxes, selects, toggles), 3.2.2 is applicable. Absence of an automatic context change can support PASS when coverage is exhaustive.
- If any function is operable by a single pointer, 2.5.2 is applicable. Native controls and `click` handlers are candidates that ordinarily satisfy up-event activation; they are not evidence of zero candidates.
- If hover or focus reveals authored content, including a submenu, 1.4.13 is applicable even when no component is named tooltip or popover.

Use N/A for these criteria only when a bounded inventory proves the underlying UI or behavior itself is absent.

For PASS, `candidate_count` is the number of governed source patterns or bounded instances, not the number of violations, event listeners, or suspicious grep matches. Record `raw_hits`, group equivalent occurrences by shared component/template/behavior, and explicitly classify exclusions. A PASS entry with `candidates=0` contradicts the aggregation procedure; use N/A when the governed feature is conclusively absent.

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
4. Evaluate normative exceptions and alternatives before calling an apparent violation a FAIL.
5. Classify the instance as proven valid, definite violation, or unresolved.

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
- raw search-hit count for inventories where deterministic scanning is used;
- total candidate count;
- evaluated, violating, and unresolved counts;
- up to 10 representative source locations;
- the reasoning that connects evidence to the criterion;
- remediation for FAIL or exact browser/AT verification for NEEDS_REVIEW.

For dynamic collections where an exact total cannot be determined, write `at least N` and mark unresolved coverage. Never invent a precise count.

For a reusable loop, include, or component, evaluate the shared source pattern once after checking its callers and relevant variants. Record, for example, `raw_hits=37; candidates=4 source patterns; excluded=33 decorative/native/duplicate-loop occurrences`. For unavailable production data, state `rendered instances=unknown`. Do not infer the rendered total from a user statement or an example menu.

Reconcile shared inventories before finalizing the ledger. Examples of contradictions that must be corrected include a video candidate under 1.2.2 but zero media candidates under 1.2.1 without evidence classifying the media, input controls under 3.3.2 but N/A under 3.2.2, or interactive keyboard controls under 2.1.1 but N/A under 2.1.2 or 3.2.1.

The following raw signals are candidates that require classification; they are not automatic failures:

- CSS grid areas, `order`, or reverse flex direction for 1.3.2;
- fixed minimum dimensions wider than the 320 CSS-pixel reflow viewport for 1.4.10;
- every `position: sticky` or `position: fixed` content surface for 2.4.11;
- authored dimensions below 24 CSS pixels on or around interactive selectors for 2.5.8, including all spacing/equivalent/inline/user-agent/essential exceptions;
- login, password-reset, or other authentication entry points for 3.3.8 even when the actual authentication implementation is delegated to framework/core code;
- contact cards, telephone/email links, help links, chat, FAQ, or automated assistance for 3.2.6;
- every custom role, ARIA state, and state mutation for 4.1.2, including responsive initialization.

For 2.5.3, first prove that the control has a visible label containing text or an image of text. An icon-only control with no visible text is not an applicable mismatch. For 4.1.2, distinguish whether a name is programmatically determinable from whether it describes purpose: the latter is ordinarily evaluated by 2.4.6. Do not fail 4.1.2 solely because a non-empty accessible name is generic, duplicated, or awkwardly translated.

Reconcile the scope boundary with verdicts as well. If the report declares CMS/editorial values unavailable, content-dependent criteria cannot PASS unless the scope explicitly excludes that content or a bounded source constraint proves the unavailable values cannot affect the criterion. This includes alternative quality, headings and relationships, sensory instructions, images of text, heading/label descriptiveness, link purpose, and language of parts.

## 6. Assign severity or review priority

Use [`severity-guidance.md`](./severity-guidance.md). Severity describes user impact, not WCAG level. NEEDS_REVIEW has a review priority rather than a confirmed defect severity.
