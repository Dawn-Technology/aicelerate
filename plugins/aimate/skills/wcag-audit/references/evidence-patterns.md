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
- **FAIL:** for a `yes` or `partial` criterion, cite at least one definite violating location, link the normative requirement, explain the failed condition and applicability, and resolve relevant exceptions. List no more than 10 representative locations.
- **NEEDS_REVIEW:** identify the source evidence that creates applicability and the exact rendered-content, browser, process, or assistive-technology check required.

## FAIL proof record

Keep this compact in working notes and use it to fill the finding's existing fields. It is not a second report or an exhaustive inventory.

1. **Established case:** the specific entry point/caller, selected branch/configuration, and relevant input value or invariant, with source locations. Distinguish "can render if an editor supplies X" from a source-established violating case. A field schema permitting bad content is an authoring risk, not evidence that bad content exists. An unconditional defect in a traced implementation can be reported for that implementation without claiming live deployment.
2. **Failed requirement:** the normative SC condition and why this case violates it. Include relevant exceptions and equivalent mechanisms. Missing a preferred technique alone does not prove failure.
3. **Disproof checked:** the strongest plausible mitigation or alternative explanation, the source inspected to check it, and the result. Read the complete semantic component, not only the suspicious lines; surrounding labels, headings, alternate controls, ancestor semantics, and branch selection can change the conclusion. Three checks are mandatory here:
   - **Enumerate your own absence claims.** A disproof that asserts "this only ever appears in X" or "no ancestor supplies it" is an absence claim and needs the same enumeration any other absence claim needs. Search the whole implementation boundary, including shells, wrappers, and parent templates, before writing it.
   - **Test the criterion's permitted alternatives.** Many criteria are satisfied by more than one mechanism — bypass blocks by landmarks or headings, keyboard access by an equivalent control, link purpose by programmatic context. Show the alternatives were checked and why each fails, or the FAIL is not established.
   - **Resolve computed values.** When the finding turns on an accessible name, state, or color that source supplies through a variable, caller argument, child content, or token, resolve it to its defining source. An asserted value such as `aria-label="{{ logo_alt }}"` meaning "ZE&GG Logo" is unproven until the caller is opened; unresolved values give NEEDS_REVIEW, not FAIL.
4. **Outcome:** confirmed instance plus sufficient remediation, or the exact missing evidence. Missing inspectable source work stays pending; a genuinely unavailable content/configuration/runtime fact produces NEEDS_REVIEW unless another instance proves FAIL.

Do not accept an assertion such as "real reachable outcome", "no exception", or "reviewed" as a substitute for these facts. The reviewer supplies their own disproof check; they do not simply copy the collector's.

Within each instance, source locations must form one coherent behavior trace. Do not borrow a live region, keyboard alternative, or style from a mutually exclusive branch. A criterion may group several independently proven instances in different components or variants; they need not coexist on one page. Remediation must satisfy the named criterion, not merely remove a suspicious attribute.

Exact totals are useful only when naturally bounded by inspected source. Otherwise write `at least N` or describe affected source patterns. Never derive a rendered-instance total from raw search hits, template loops, optional components, or unavailable CMS data.

## Citation provenance

Every citation must come from source opened in this run: each `path:line` appears in returned worker evidence or in a file the author read. Do not supply a plausible file name for a claim you did not verify. A reach, rollout, bundle, route, or configuration claim needs its controlling line quoted; without it, scope the finding to the implementation actually traced.

Line numbers are evidence, not decoration. Never carry one over from a summary, a previous report, or memory — re-derive it by matching the quoted content in the file at write time. A citation pointing at the wrong line is a defect even when the claimed code exists elsewhere in the file, because it shows the citation was never reopened.

Absence and coverage claims state how they were established — `enumerated <file set>: <count> files; inspected <count>` — rather than a bare count or a search-derived total.

## External evidence

Prefix observations not independently established by the static audit:

- `EXTERNALLY_REPORTED - ...`
- `SOURCE_CORROBORATED - ...`
- `NOT_INDEPENDENTLY_VERIFIED - ...`

Do not include secrets, PII, full user content, or unrelated source excerpts. Preserve source syntax exactly, including template expressions such as `{{ title }}`.
