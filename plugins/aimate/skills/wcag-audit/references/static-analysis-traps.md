# Static Analysis Boundaries

Use these principles when source does not directly establish the rendered accessibility outcome.

## Reachability and content

- A template proves what it can render, not that a qualifying instance exists in production.
- A CMS/API field, external embed, translation, or menu value is unresolved when its actual value determines applicability or compliance.
- Registration in a component library, route map, CMS bundle, or schema proves reachability, not rendered use or content characteristics.
- A loop or reusable component is one source pattern unless inspected data naturally bounds its rendered instances.
- Project comments and component descriptions are leads, not proof of runtime content.
- Evidence combined into one finding must coexist in the same reachable template branch, caller, state, and runtime path. Similar markup in a mutually exclusive branch does not support the behavior being analyzed.

Do not fail media criteria merely because a reachable player lacks caption, transcript, or audio-description fields. First establish an actual or bounded source-controlled instance of the applicable media type. Otherwise use NEEDS_REVIEW and record the missing authoring capability as a risk.

## CSS and visual behavior

Before a CSS-based FAIL, trace selectors, specificity, source order, media queries, pseudo-classes, inheritance, custom properties, opacity, backgrounds, and state changes.

- `outline: none` is only a Focus Visible failure when the element is keyboard-focusable and no visible focused-state change survives the cascade.
- A focus style may be shared with hover or active. Compare focused with unfocused presentation; WCAG 2.4.7 does not require unique styling for each input mode.
- Keep focus criteria distinct: 2.4.7 requires a visible focus indicator, 2.4.11 concerns focus being obscured, and focus-indicator area is in 2.4.13 at Level AAA.
- Source-defined color pairs can prove a contrast failure only when foreground, actual adjacent background, opacity composition, state, and relevant text-size or component exceptions are resolved.
- Authored dimensions below a threshold are candidates, not automatic failures. For 2.5.8, center a 24 CSS pixel diameter circle on the bounding box of each undersized target. The spacing exception fails only if that circle intersects another target or the circle of another undersized target. A CSS `gap` below 24px is not by itself a failure. Resolve computed bounding boxes, neighboring targets, and all other exceptions; otherwise use NEEDS_REVIEW.
- Visual reordering declarations identify patterns requiring DOM/reading-sequence analysis. Their presence is not automatically a failure, and they cannot be reported as absent when source searches found them.

## Native semantics and ARIA

- Native HTML semantics remain authoritative unless source proves they are overridden.
- A wrapping `<label>` labels its descendant input; a native checkbox exposes checked state without `aria-checked` on a decorative wrapper.
- An icon-only control without visible text is not automatically a Label-in-Name candidate.
- A custom ARIA widget must satisfy its required owned roles, states, keyboard behavior, and state changes as a complete pattern.
- For responsive ARIA, trace initial markup, initial CSS state, initialization calls, event registrations, every mutation, breakpoints, and user transitions. Do not infer all states from one attribute or event handler.
- For 1.3.5, removing `autocomplete="off"` is not sufficient when the input collects a listed personal-data purpose. Supply a valid purpose token such as `autocomplete="email"` or another supported programmatic identification mechanism.

## Behavior and complete processes

- Search for behavior, not only component names: event handlers, form dispatch/submission, focus changes, pointer/down events, route transitions, hover/focus disclosure, and live-region updates.
- For status messages, trace the exact mutation target and the live region in the same rendered branch. A live region in another mutually exclusive branch does not cover the updated message.
- A content update is not automatically a change of context. Determine whether page, focus, viewport, or meaning changes; if runtime outcome is unavailable, use NEEDS_REVIEW.
- A click handler on a label descendant is not a Keyboard failure when the same native control remains keyboard operable and the handler does not block it.
- Authentication, error handling, repeated help, page discovery, and multi-step processes often cross the selected source boundary. Do not issue PASS or N/A when framework configuration or rendered process steps remain unresolved.

## External observations

Treat user-supplied reports, screenshots, scanner output, and live-site claims as external evidence. Record provenance, corroborate what source can establish, and never present unverified rendered behavior as independently proven by this static audit.
