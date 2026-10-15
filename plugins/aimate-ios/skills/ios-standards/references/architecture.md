# Architecture Selection

Select for qualities, not labels. Prefer the smallest design that provides:

- clear state ownership and mutation;
- explicit side effects and dependencies;
- testable business behavior;
- predictable navigation and lifecycle behavior;
- structured concurrency and cancellation;
- cohesive units with boundaries proportionate to the feature.

## Existing Code

Follow the established architecture when it can support the change safely. Correct local violations in that architecture; do not introduce TCA into MVVM, MVVM into TCA, or SwiftUI into UIKit merely because a specialist knows it better.

Recommend a migration separately only with evidence that the current design blocks safe changes or testing.

## New or Isolated Code

- Use native SwiftUI state for small local presentation state.
- Use MVVM when a presentation model provides a clear test seam without unnecessary ceremony.
- Consider TCA for complex shared state, effects, navigation, cancellation, or deterministic state-machine testing, especially where the project already uses TCA.
- Preserve UIKit or mixed architecture where platform requirements or repository boundaries call for it.

Before applying version-sensitive TCA guidance, inspect the resolved package version and prefer the accepted official Point-Free skill when available.
