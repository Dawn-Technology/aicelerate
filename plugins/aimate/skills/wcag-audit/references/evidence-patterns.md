# Evidence Patterns

Evidence must be specific, sanitized, and traceable. Prefer a source location plus the relevant element, selector, component, state, or attribute.

## Canonical forms

| Type | Format | Example |
|---|---|---|
| Source element | `<path>:<line> <element/component> <relevant attribute or state>` | `src/Nav.jsx:42 <button aria-label="Close">` |
| Selector or style | `<path>:<line> <selector> <relevant declaration>` | `styles/base.css:118 .menu:focus { outline: none; }` |
| Framework behavior | `framework:<name>:<behavior> at <path>:<line>` | `framework:HTML:button keyboard semantics at src/Nav.jsx:42` |
| Missing mechanism | `missing:<requirement>; searched <bounded source>` | `missing:label for one input; searched src/forms/` |
| N/A | `N/A - <governed feature absent>; searched <bounded source/signals>` | `N/A - no synchronized media; searched src/, templates/ for video/audio/player components` |
| Needs review | `NEEDS_REVIEW - <specific boundary>; verify <exact steps>` | `NEEDS_REVIEW - computed contrast depends on the rendered background; inspect .btn-primary in every theme/state` |

## Verdict evidence

- **PASS:** cite positive implementation evidence and state what bounded patterns or components it covers. Do not claim whole-repository coverage from one example.
- **N/A:** identify the governed feature and the bounded search that proves it absent.
- **FAIL:** cite at least one definite violating location and explain applicability and relevant exceptions. List no more than 10 representative locations.
- **NEEDS_REVIEW:** identify the source evidence that creates applicability and the exact rendered-content, browser, process, or assistive-technology check required.

Exact totals are useful only when naturally bounded by inspected source. Otherwise write `at least N` or describe affected source patterns. Never derive a rendered-instance total from raw search hits, template loops, optional components, or unavailable CMS data.

## External evidence

Prefix observations not independently established by the static audit:

- `EXTERNALLY_REPORTED - ...`
- `SOURCE_CORROBORATED - ...`
- `NOT_INDEPENDENTLY_VERIFIED - ...`

Do not include secrets, PII, full user content, or unrelated source excerpts. Preserve source syntax exactly, including template expressions such as `{{ title }}`.
