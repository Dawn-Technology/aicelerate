# Static Analysis Traps

Read this before evaluating source-generated markup, CMS content, CSS-dependent behavior, or criteria with normative exceptions.

## Source availability is part of the verdict

- A template proves the shape it can render, not the values supplied by a CMS, API, translation catalog, media host, menu tree, or runtime state.
- If actual editorial or external content is unavailable, criteria concerning alternative quality, language, instructions, link purpose, heading descriptiveness, media, flashing, or images of text remain unresolved when that content could affect the result.
- Do not use a parallel, newer, story-only, or unused component as evidence for the traced production render path.
- For loops and CMS collections, report one affected **source pattern**. State the rendered instance count as `unknown` unless bounded production data, configuration, or rendered evidence proves it. Never turn an asserted live count into source evidence.
- Registration in a CMS bundle, route map, component registry, field configuration, or production template makes a component reachable; it does not prove an instance is currently rendered or that its content has a particular sensory/media characteristic.

## User-supplied and external observations

Treat user-supplied live-site findings, screenshots, scanner output, and prior reports as external evidence:

- preserve the provenance;
- independently corroborate what source can prove;
- do not call the observation source-proven or independently verified;
- do not use an external assertion to supply an exact count unless the artifact itself is in scope and inspectable;
- place useful non-verdict discrepancies in Supplemental observations, not in the detailed FAIL/NEEDS_REVIEW sequence.

## CSS and rendered geometry

Before a source-proven CSS FAIL, trace all relevant selectors, specificity, source order, media queries, pseudo-classes, inherited/global rules, custom-property definitions, box sizing, generated content, and state styles.

- `outline: none` is a definite Focus Visible failure only when no visible focused-state change survives the cascade. A shadow or border that is also present when unfocused is not itself a focus indicator. Conversely, a focus-specific change to opacity, color, background, border, shadow, filter, transform, or another visible property is a replacement candidate; compare it with the unfocused state before deciding the verdict.
- Build a complete suppression inventory for `outline:none`, `outline:0`, transparent outlines, removed shadows, and framework resets across every in-scope CSS source. Resolve each occurrence in a per-selector state table. A replacement counts only when it applies to the same focusable element and state and survives specificity, source order, media queries, and later overrides. A lower-specificity global `:focus-visible` rule does not repair a higher-specificity component `:focus { outline:none }` rule. A border or shadow already present in the unfocused state is not a replacement indicator.
- WCAG 2.4.7 requires a visible keyboard focus indicator; it does not require that focus look different from hover or active. Do not declare FAIL merely because those states share a style. Likewise, an outline reset on a root or container is not a 2.4.7 violation until source proves that element is itself keyboard focusable and operable.
- Resolve statically defined color tokens and compute definite foreground/background pairs. Dynamic themes, images, opacity composition, and unknown cascade states remain unresolved, but CSS custom properties are not automatically runtime-only.
- An authored width or height below 24 CSS pixels is only a **2.5.8 candidate**. Rule out the Spacing, Equivalent, Inline, User Agent Control, and Essential exceptions before FAIL. In particular, resolve gaps and neighboring target geometry; a 24px circle centered on an undersized target must intersect another target or another undersized-target circle for the spacing exception to fail.
- If geometry or an exception cannot be established from source, use NEEDS_REVIEW. Never state that no exception applies solely because the target itself is undersized.

## Heading hierarchy

A skipped heading rank is a strong review signal and should normally be fixed, but the skipped number alone is not automatic proof of WCAG 1.3.1 failure. Establish that the programmatic heading hierarchy misrepresents a relationship conveyed visually or structurally. If the intended relationship or rendered surrounding headings are unavailable, use NEEDS_REVIEW or record an advisory observation.

## Forms and autocomplete

Trace the component actually rendered. For inputs collecting information about the user, `type="email"` describes a broad data type but does not identify whose email address is requested. An authored `autocomplete="off"` does not provide the WCAG input-purpose taxonomy. When the field requests the current user's email and no other programmatic purpose metadata exists, this is source evidence for 1.3.5 FAIL.

## External media

An external or CMS-selected video affects more than captions and audio description. When the actual media is unavailable, consider all content-dependent criteria it may affect, including flashes, images of text, language, alternatives, and controls. Do not mark those criteria N/A merely because the template contains only an iframe or optional field.

Maintain one media inventory and classify each source pattern or rendered instance as prerecorded/live, audio-only/video-only/synchronized, source-controlled/external, and used/unused/unknown. A reusable player or CMS paragraph that lacks a captions field proves a product-code risk, but it does not by itself prove that an in-scope rendered page contains meaningful prerecorded synchronized media. Without bounded production content or rendered evidence, use NEEDS_REVIEW for the content-dependent criterion and put the missing authoring capability in the finding or Supplemental observations. Use FAIL only when a reachable rendered instance, bounded source-controlled media asset, fixture that is production content, or equivalent evidence proves the applicable media exists and violates the criterion.

The HTML `controls` attribute proves only that playback controls are requested. It does not prove the media file contains audio, that it is synchronized media, that it is prerecorded, or that it is meaningful. A file-field type or `.mp4` MIME declaration likewise does not establish those properties; inspect the bounded asset or rendered production content.

## Hover- and focus-triggered content

Do not search only for component names such as `tooltip` or `popover`. Inventory CSS and script triggers including `:hover`, `:focus`, `:focus-within`, mouseenter/leave, focus/blur, disclosure state classes, dropdowns, submenus, title attributes, and portals. Trace the content that becomes visible and evaluate dismissible, hoverable, and persistent behavior. A submenu revealed by hover or focus is an applicable 1.4.13 candidate.

## Dynamic ARIA states

An authored `aria-hidden`, `aria-expanded`, `aria-selected`, `aria-pressed`, or similar initial value is not evaluated in isolation. Build a state matrix covering initial DOM, initial CSS visibility, initialization code, each user transition, responsive breakpoints, and the no-JavaScript fallback. Search every mutation of the attribute and confirm whether initialization is actually invoked. If CSS makes a desktop navigation visible while its initial `aria-hidden="true"` remains unchanged until a resize event, that precise initial desktop state can support FAIL; do not claim the attribute is never changed or that all viewport states fail.

Merely mentioning `initial`, `breakpoint`, or `resize` is not a completed trace. For each responsive state handler, record its source location, the initial DOM value, the CSS state at each breakpoint, every event registration, and a direct initialization invocation (or its absence). A handler that is only registered for future `resize` events does not correct the initial page state.

ARIA widget roles must be validated as a complete owned structure. For example, a `role="listbox"` must expose valid option descendants/ownership and state semantics; native checkboxes wrapped in labels do not become ARIA options merely because their container is named a listbox.

## Native semantics and duplicate interaction surfaces

- An empty `<span>` without a role, accessible-name attribute, or text normally contributes no accessible object/name. Missing `aria-hidden="true"` on that span alone is not a 1.1.1 failure. Evaluate the accessible name of the containing functional control and whether decorative generated graphics are exposed.
- `alt|default('')` or another empty-alt fallback is a risk, not a definite failure, until a source-controlled informative caller omits the alternative or rendered/CMS evidence proves an informative image receives an empty alternative.
- A `<label>` that wraps an `<input>` establishes implicit label association. Custom visual spans, SVGs, or visually-hidden CSS do not invalidate it unless the native input is removed from the accessibility tree or the interaction bypass changes the exposed name/state.
- A native checkbox exposes its checked state automatically. Do not add or require `aria-checked` on a non-semantic visual wrapper. Require ARIA state only when a custom element assumes a checkbox/switch/option role.
- A click handler on a label descendant may be redundant or fragile, but it is not a Keyboard failure if the same checkbox/function remains keyboard operable and the handler does not block that path.

## Consistency and help

When parallel layouts or design systems exist, compare every in-scope variant and trace their route/process mapping before PASS for 3.2.3 or 3.2.4. Shared components in one variant do not prove consistency across variants.

For 3.2.6, a help mechanism means human contact details, a human contact mechanism, a self-help option, or a fully automated contact mechanism. A newsletter subscription is not a help mechanism merely because it appears in the footer.

Search components, templates, route variants, and configuration for contact/help mechanisms. A reusable contact card or contact paragraph is an applicability candidate even when CMS placement is unavailable. If route composition or repeated placement cannot be established from the selected source boundary, use NEEDS_REVIEW rather than N/A.

## Authentication boundaries

A login or password-recovery page establishes an authentication candidate even when framework/core code renders the form. Do not assign 3.3.8 N/A merely because source contains no CAPTCHA, puzzle, or cognitive-function test. Inspect the reachable authentication process and alternatives; when the implementation or configured modules are outside scope, use NEEDS_REVIEW and identify the exact delegated boundary.

## Label quality versus programmatic name

- SC 2.5.3 applies only when a component has a visible label containing text or an image of text. An icon-only button with an invisible `aria-label` has no visible-label mismatch to test under this criterion.
- SC 2.4.6 evaluates whether provided headings and labels describe topic or purpose.
- SC 4.1.2 evaluates whether name, role, value, states, and changes are programmatically available. A non-empty accessible name that is generic or duplicated may fail 2.4.6, but that quality problem alone does not make the name non-programmatically-determinable for 4.1.2.

## Automatic form behavior

For 3.2.2, changing a checkbox, select, or text field and then programmatically dispatching a change, clicking submit, or navigating is an automatic-behavior candidate even when a developer describes it as “expected filtering.” Trace the actual result. A content update is not automatically a change of context: establish a new page/window, focus or viewport move, or content change that changes the page's meaning or significantly rearranges it. Require advance warning only when that context-change threshold is met. If AJAX/full-page behavior is outside source visibility, use NEEDS_REVIEW rather than presume either PASS or FAIL. Reuse the same dynamic-update inventory for 4.1.3.
