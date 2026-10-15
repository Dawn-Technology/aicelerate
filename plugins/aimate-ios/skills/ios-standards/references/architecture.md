# Architecture

Follow the project's architecture. Never choose or switch one as a side effect of a change.

## Which Architecture Applies

| Situation | Architecture |
| --- | --- |
| New project | The company template's choice: TCA by default, or MVVM + Coordinators. `AGENTS.md` states it, or it is clear from the code. |
| Existing project | The architecture the project already uses, including legacy patterns. |
| Recorded deviation | What `AGENTS.md` or an accepted ADR records; report it as described in `precedence.md`. |

When `AGENTS.md` does not name the architecture, identify it from evidence:

| Pattern | Typical evidence |
| --- | --- |
| TCA | `import ComposableArchitecture`, `@Reducer`, `Store`, `TestStore` |
| MVVM | `ObservableObject` or `@Observable` view models bound by views |
| Coordinator | `Coordinator` types that own navigation |
| MVC | logic in `UIViewController` subclasses, no presentation model |
| VIPER / MVP | `Presenter`, `Interactor`, `Router`, or `Wireframe` types |
| Clean | `UseCase` and `Repository` layers |
| Reactive | Combine or RxSwift binding pipelines |
| Mixed | several of the above; record which areas use which |

Record the identified pattern, or the mix, in the review baseline. A type name is not proof; check how state, effects, and navigation actually flow.

## Checks for Every Pattern

- clear state ownership and mutation;
- explicit side effects and dependencies;
- testable business behavior;
- predictable navigation and lifecycle behavior;
- structured concurrency and cancellation;
- cohesive units with boundaries proportionate to the feature.

Fix violations locally, inside the existing pattern. Do not introduce TCA into MVVM, MVVM into TCA, or SwiftUI into UIKit because a specialist knows it better. Recommend a migration separately only with evidence that the current design blocks safe changes or testing.

## TCA

Read `tca.md` for version-specific documentation and checks.

## MVVM + Coordinators

- The view owns a view model it creates with `@StateObject`, or `@State` for an `@Observable` model; an injected view model uses `@ObservedObject` or a plain property.
- View models hold no UIKit or SwiftUI view types and do not push, present, or know about other screens.
- Async work started by a view model has an owner, is cancelled when its screen goes away, and cannot overwrite newer results with older ones.
- Coordinators own navigation: pushing, presenting, dismissing, deep links, and back navigation.
- Coordinators release child coordinators when their flow ends, without retain cycles between coordinator, child coordinator, and view controller.
- Dependencies are injected through initializers or the coordinator, not reached through singletons.

Plain SwiftUI state remains fine for small, view-local presentation state in either architecture.
