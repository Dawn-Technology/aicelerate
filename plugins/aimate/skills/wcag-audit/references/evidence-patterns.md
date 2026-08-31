# Evidence Patterns

Evidence must be specific, sanitized, and traceable. Prefer a source location plus the relevant element, selector, component, or attribute.

## Canonical forms

| Type | Format | Example |
|---|---|---|
| Source element | `<path>:<line> <element-or-component> <relevant attribute/state>` | `src/Nav.jsx:42 <button aria-label="Close">` |
| Selector or style | `<path>:<line> <selector> <relevant declaration>` | `styles/base.css:118 .menu:focus { outline: none; }` |
| Framework default | `framework:<name>:<feature> at <path>:<line>` | `framework:HTML:button-keyboard-semantics at src/Nav.jsx:42` |
| Missing requirement | `missing:<requirement>; searched <paths/signals>` | `missing:label for 3 inputs; searched src/forms/**/*.{tsx,css}` |
| N/A | `N/A - <feature absent>; Coverage: paths=<paths>; searched <signals>; candidates=0; evaluated=0; unresolved=0` | `N/A - no synchronized media; Coverage: paths=src/,templates/; searched video,audio,track; candidates=0; evaluated=0; unresolved=0` |
| Needs review | `NEEDS_REVIEW - <limitation>; verify <exact steps>` | `NEEDS_REVIEW - rendered contrast unresolved; verify .btn-primary in every theme and state with a contrast analyzer` |
| Monorepo | `[<component>] <canonical form>` | `[checkout] src/Payment.tsx:76 <div onClick> lacks keyboard handler` |

## Coverage manifest

PASS and N/A evidence must be accompanied by a compact coverage statement:

```text
Coverage: paths=src/**/*.tsx,styles/**/*.css; signals=button,onClick,onKeyDown,role;
candidates=34; evaluated=34; violations=0; unresolved=0
```

When coverage is incomplete:

```text
Coverage: paths=src/widgets/; candidates=at least 12; evaluated=10;
violations=0; unresolved=2 generated at runtime
```

The latter cannot yield PASS. N/A uses the same manifest with `candidates=0; evaluated=0; unresolved=0` and must state the searched signals.

## Representative-instance rule

For FAIL and NEEDS_REVIEW:

- preserve the total count;
- list at most 10 representative instances;
- choose examples across distinct components, patterns, routes, or root causes;
- state `Showing 10 of N instances` when capped;
- do not duplicate the same generated source location.

## Verdict examples

- `PASS: src/Nav.jsx:42 <button aria-label="Close">; coverage candidates=8 evaluated=8 unresolved=0`
- `FAIL: templates/card.twig:12 <img> missing alt; showing 1 of 6 instances`
- `N/A - no live synchronized media; Coverage: paths=src/,templates/,content/; searched=live players,streams,caption providers; candidates=0; evaluated=0; unresolved=0`
- `NEEDS_REVIEW - focus may be obscured by .sticky-header; verify keyboard focus at 320px width on /checkout steps 1-3`

Never include secrets, PII, full user content, or unrelated source excerpts.

Preserve source code exactly. Evidence containing template syntax such as `{{ title }}` is valid and must not be altered for report validation.

## External evidence provenance

Prefix evidence not produced by the static audit:

- `EXTERNALLY_REPORTED - <source supplied by user or prior tool>`
- `SOURCE_CORROBORATED - <what the inspected source independently establishes>`
- `NOT_INDEPENDENTLY_VERIFIED - <rendered behavior requiring runtime access>`

An externally reported rendered count is not a source candidate count.
