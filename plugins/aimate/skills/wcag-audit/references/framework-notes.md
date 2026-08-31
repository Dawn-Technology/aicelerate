# Framework Source Semantics

Use only the section matching the detected stack. Framework conventions provide instance evidence, not criterion-wide PASS.

## Plain HTML

- Native `button`, `a[href]`, `input`, `select`, `textarea`, `details/summary`, headings, lists, and landmarks provide baseline semantics when used according to specification.
- Inspect accessible names, disabled states, duplicate IDs, DOM order, CSS reordering, focus suppression, and scripted behavior that overrides native behavior.
- Trace includes, partials, and server-side layout composition before deciding scope coverage.

## React and JSX

- `htmlFor` maps to HTML `for`; `className` maps to `class`. Component names do not guarantee their rendered element.
- Trace wrapper components and polymorphic `as`, `component`, or slot props to the final host element.
- Inspect `onClick` on non-native elements, conditional ARIA, portals, route-change focus, dialog focus restoration, live regions, and CSS-in-JS states.
- A component-library claim is evidence only when the installed component, version, props, and local overrides are identified.

## Vue

- Trace component templates, slots, `v-bind`, conditional rendering, Teleport, and custom directives to rendered semantics.
- Inspect `@click` on non-native elements, dynamic ARIA, route transitions, focus management, and scoped/global style interactions.
- A component tag is not native evidence unless its rendered root and relevant states are known.

## Angular

- Inspect templates, property/attribute bindings, structural control flow, CDK overlays, router transitions, and custom ControlValueAccessor implementations.
- Distinguish `[attr.aria-*]` from DOM-property bindings and trace values that can become null or invalid.
- Angular Material/CDK defaults may support semantics and focus behavior, but verify version, configuration, and overrides per instance.

## Twig

- Trace template inheritance, includes, macros, blocks, conditions, and data-provided attributes to the final HTML shape.
- Treat escaped output as security behavior, not accessibility evidence. Inspect whether content variables provide meaningful names, labels, alternatives, and language.
- Search every caller of a macro before treating the macro's default markup as exhaustive coverage.

## Unknown or mixed stacks

Audit generic rendered-HTML semantics. Identify templates and component boundaries by imports, includes, naming, and output construction. If final semantics cannot be traced, classify affected instances as unresolved rather than assuming a framework default.

