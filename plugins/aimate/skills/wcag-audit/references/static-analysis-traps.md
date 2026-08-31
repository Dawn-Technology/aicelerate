# Static Analysis Traps

Read this before evaluating source-generated markup, CMS content, CSS-dependent behavior, or criteria with normative exceptions.

## Source availability is part of the verdict

- A template proves the shape it can render, not the values supplied by a CMS, API, translation catalog, media host, menu tree, or runtime state.
- If actual editorial or external content is unavailable, criteria concerning alternative quality, language, instructions, link purpose, heading descriptiveness, media, flashing, or images of text remain unresolved when that content could affect the result.
- Do not use a parallel, newer, story-only, or unused component as evidence for the traced production render path.
- For loops and CMS collections, report one affected **source pattern**. State the rendered instance count as `unknown` unless bounded production data, configuration, or rendered evidence proves it. Never turn an asserted live count into source evidence.

## User-supplied and external observations

Treat user-supplied live-site findings, screenshots, scanner output, and prior reports as external evidence:

- preserve the provenance;
- independently corroborate what source can prove;
- do not call the observation source-proven or independently verified;
- do not use an external assertion to supply an exact count unless the artifact itself is in scope and inspectable;
- place useful non-verdict discrepancies in Supplemental observations, not in the detailed FAIL/NEEDS_REVIEW sequence.

## CSS and rendered geometry

Before a source-proven CSS FAIL, trace all relevant selectors, specificity, source order, media queries, pseudo-classes, inherited/global rules, custom-property definitions, box sizing, generated content, and state styles.

- `outline: none` is a definite Focus Visible failure only when no visible focused-state change survives the cascade. A shadow or border that is also present when unfocused is not itself a focus indicator.
- Resolve statically defined color tokens and compute definite foreground/background pairs. Dynamic themes, images, opacity composition, and unknown cascade states remain unresolved, but CSS custom properties are not automatically runtime-only.
- An authored width or height below 24 CSS pixels is only a **2.5.8 candidate**. Rule out the Spacing, Equivalent, Inline, User Agent Control, and Essential exceptions before FAIL. In particular, resolve gaps and neighboring target geometry; a 24px circle centered on an undersized target must intersect another target or another undersized-target circle for the spacing exception to fail.
- If geometry or an exception cannot be established from source, use NEEDS_REVIEW. Never state that no exception applies solely because the target itself is undersized.

## Heading hierarchy

A skipped heading rank is a strong review signal and should normally be fixed, but the skipped number alone is not automatic proof of WCAG 1.3.1 failure. Establish that the programmatic heading hierarchy misrepresents a relationship conveyed visually or structurally. If the intended relationship or rendered surrounding headings are unavailable, use NEEDS_REVIEW or record an advisory observation.

## Forms and autocomplete

Trace the component actually rendered. For inputs collecting information about the user, `type="email"` describes a broad data type but does not identify whose email address is requested. An authored `autocomplete="off"` does not provide the WCAG input-purpose taxonomy. When the field requests the current user's email and no other programmatic purpose metadata exists, this is source evidence for 1.3.5 FAIL.

## External media

An external or CMS-selected video affects more than captions and audio description. When the actual media is unavailable, consider all content-dependent criteria it may affect, including flashes, images of text, language, alternatives, and controls. Do not mark those criteria N/A merely because the template contains only an iframe or optional field.

