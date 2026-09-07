# WCAG Static Audit Examples

These are illustrative cases, not repository evidence. Apply the decision procedure to the actual source; do not copy their conclusions without establishing their premises.

## FAIL with representative instances

```markdown
### ❌ FAIL 1.3.5 — Identify Input Purpose

- **WCAG level:** AA
- **Severity / review priority:** Moderate
- **Affected or unresolved instances:** 1 source implementation; live usage count unknown
- **Coverage:** The subscription form rendered by the source-controlled `/subscribe` route
- **Normative requirement:** [1.3.5 Identify Input Purpose](https://www.w3.org/TR/WCAG22/#identify-input-purpose) requires programmatic identification of listed personal-data purposes using supporting technology.
- **Applicability and exceptions:** The static label and submit handler establish that this field collects the subscriber's own email address. No applicable exception.
- **Counterevidence checked:** The reviewer traced the complete form and its initialization; there is no purpose token, equivalent metadata, or later attribute assignment. `type="email"` does not identify whose email is requested.
- **Representative evidence:**
  - `src/routes/subscribe.html:12 <label for="email">Your email address</label>`
  - `src/routes/subscribe.html:13 <input id="email" type="email" autocomplete="off">`
  - `src/forms/subscribe.js:8 submit handler uses this field for the subscriber; no input metadata mutation`
- **Impact or uncertainty:** Assistive tools lack a supported purpose identifier for this personal-data field. This is an implementation finding, not proof of live deployment.
- **Remediation or exact manual verification:** Set `autocomplete="email"` on the input.
```

## NEEDS_REVIEW manual-verification row

```markdown
| 2.4.11 | Serious | Source establishes sticky header and fixed mobile actions, but not rendered focus geometry. | At 320 CSS pixels and each breakpoint, keyboard through representative long pages and verify focused controls remain at least partially visible. |
```

## N/A with bounded negative evidence

```markdown
| 1.2.4 | Captions (Live) | AA | ⚪ N/A | N/A - no live synchronized media; searched production `src/`, `templates/`, and source-controlled content for live players, streams, video, caption tracks, and caption providers |
```

## PASS with bounded positive evidence

```markdown
| 3.1.1 | Language of Page | A | ✅ PASS | `src/layouts/Document.tsx:14 <html lang={locale}>`; the sole document renderer is used by every in-scope route, and invalid locale values fall back to `en` at `src/i18n/locale.ts:39` |
```

This PASS also requires source-controlled page content to match those locales. If CMS content can be in another language, the same `lang` implementation supports NEEDS_REVIEW, not whole-scope PASS.

## Work progress is not a verdict

- A worker inspects two of five form implementations and runs out of context: retain the evidence and assign the remaining three; do not call the row NEEDS_REVIEW or stop the audit automatically.
- All source-defined form patterns are checked, but actual CMS labels are unavailable: NEEDS_REVIEW with a content verification step is a completed static assessment.
- One reviewed personal-email field definitely lacks supported purpose metadata: 1.3.5 is FAIL even if the total number of affected rendered forms is unknown. Do not demand an exhaustive instance count before finalizing that row.
- Small CSS targets or `outline: none` identify manual checks for 2.5.8 or 2.4.7. Both are `no` rows: neither a plausible failure nor a plausible replacement style overrides their static NEEDS_REVIEW gate.

## Rejecting an unsupported finding

A linked image uses an editor-supplied alt value with an empty fallback. The schema permits empty values, but the content is unavailable. The reviewer cannot confirm an unnamed image link from that alone: report NEEDS_REVIEW for published alternatives and note optional validation as an authoring risk. Conversely, a traced source-controlled link containing a fixed empty-alt image and no other name is a different case that can support a source FAIL.

If one of two alleged link-purpose violations has a contextual heading that the collector overlooked, remove that instance and reassess its context. Do not retain it to preserve the original count, and do not turn the entire criterion into PASS if the second instance independently fails.
