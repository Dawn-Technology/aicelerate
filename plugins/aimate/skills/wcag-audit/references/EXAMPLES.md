# WCAG Static Audit Examples

Use these examples only to clarify formatting. Apply the canonical decision procedure and actual repository evidence.

## FAIL with representative instances

```markdown
### ❌ FAIL 1.1.1 — Non-text Content

- **WCAG level:** A
- **Severity / review priority:** Serious
- **Affected or unresolved instances:** at least 3 source-proven violations
- **Coverage:** Product cards, account avatars, and authored chart components under `src/`; CMS-provided image content remains outside this finding count
- **Representative evidence:**
  - `src/catalog/ProductCard.tsx:31 <img src={product.image}> missing alt`
  - `src/account/Avatar.tsx:18 <img alt="avatar"> alternative does not identify the user represented`
  - `src/charts/Revenue.tsx:54 <svg> has no accessible name or adjacent text alternative`
- **Impact or uncertainty:** Screen-reader users cannot obtain information conveyed by product, account, and chart imagery.
- **Remediation or exact manual verification:** Provide data-derived alternatives for informative images, empty alternatives for decorative images, and an equivalent textual summary for the chart.
```

## NEEDS_REVIEW with an exact runtime check

```markdown
### ⚠️ NEEDS_REVIEW 2.4.11 — Focus Not Obscured (Minimum)

- **WCAG level:** AA
- **Severity / review priority:** Serious priority
- **Affected or unresolved instances:** 2 sticky layout patterns unresolved
- **Coverage:** Application-shell headers and mobile action regions under `src/layouts/` and `styles/`
- **Representative evidence:**
  - `src/layouts/AppShell.tsx:22 <Header className="sticky top-0">`
  - `styles/mobile.css:91 .bottom-actions { position: fixed; bottom: 0; }`
- **Impact or uncertainty:** Source establishes possible overlap but not focused-element geometry across viewport and content states.
- **Remediation or exact manual verification:** At 320 CSS pixels and each responsive breakpoint, keyboard through every control on representative long pages. Verify each focused control is at least partially visible with both sticky regions present, including validation-error and open-panel states.
```

## N/A with bounded negative evidence

```markdown
| 1.2.4 | Captions (Live) | AA | ⚪ N/A | N/A - no live synchronized media; searched production `src/`, `templates/`, and source-controlled content for live players, streams, video, caption tracks, and caption providers |
```

## PASS with bounded positive evidence

```markdown
| 3.1.1 | Language of Page | A | ✅ PASS | `src/layouts/Document.tsx:14 <html lang={locale}>`; the sole document renderer is used by every in-scope route, and invalid locale values fall back to `en` at `src/i18n/locale.ts:39` |
```
