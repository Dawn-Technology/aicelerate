# WCAG Static Audit Examples

Use these examples only to clarify formatting. Apply the canonical decision procedure and actual repository evidence.

## FAIL with representative instances

```markdown
### ❌ FAIL 1.1.1 — Non-text Content

- **WCAG level:** A
- **Severity / review priority:** Serious
- **Affected or unresolved instances:** at least 3 source-proven violations
- **Coverage:** Product cards, account avatars, and authored chart components under `src/`; CMS-provided image content remains outside this finding count
- **Normative requirement:** [1.1.1 Non-text Content](https://www.w3.org/TR/WCAG22/#non-text-content) requires an equivalent text alternative for the informative content in these instances.
- **Applicability and exceptions:** The cited images convey information or act as controls; none is decorative, redundant with adjacent text, or covered by another 1.1.1 exception.
- **Representative evidence:**
  - `src/catalog/ProductCard.tsx:31 <img src={product.image}> missing alt`
  - `src/account/Avatar.tsx:18 <img alt="avatar"> alternative does not identify the user represented`
  - `src/charts/Revenue.tsx:54 <svg> has no accessible name or adjacent text alternative`
- **Impact or uncertainty:** Screen-reader users cannot obtain information conveyed by product, account, and chart imagery.
- **Remediation or exact manual verification:** Provide data-derived alternatives for informative images, empty alternatives for decorative images, and an equivalent textual summary for the chart.
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
