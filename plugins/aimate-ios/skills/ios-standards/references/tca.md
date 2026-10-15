# TCA

Read when the project imports `ComposableArchitecture`. TCA guidance is version-sensitive; use documentation for the resolved version rather than remembered APIs.

## Resolve the Version

Read the `swift-composable-architecture` pin from `Package.resolved` in the workspace or project `xcshareddata/swiftpm/` directory, or the package root. Record the version in the review baseline. If no pin exists, say so and label any `main` documentation as unpinned.

## Read the Documentation

Use the first source that works:

1. Local package checkout, which matches the resolved version and works offline: `~/Library/Developer/Xcode/DerivedData/<Project>-<hash>/SourcePackages/checkouts/swift-composable-architecture/Sources/ComposableArchitecture/Documentation.docc/`, or `.build/checkouts/` for a Swift package.
2. GitHub at the resolved tag: `https://raw.githubusercontent.com/pointfreeco/swift-composable-architecture/<version>/Sources/ComposableArchitecture/Documentation.docc/Articles/<Article>.md`.
3. Sosumi: `https://sosumi.ai/external/https://swiftpackageindex.com/pointfreeco/swift-composable-architecture/<version>/documentation/composablearchitecture/<page>`.

Relevant articles: `GettingStarted`, `DependencyManagement`, `SwiftConcurrency`, `TestingTCA`, `WhatIsNavigation`, `TreeBasedNavigation`, `StackBasedNavigation`, `SharingState`, `Bindings`, `Performance`, `FAQ`, and `MigrationGuides` for version-to-version changes.

When the project uses an older documented style than its pinned version supports, follow the project. Point to the migration guide separately only when the older style blocks the change.

## Review Checks

- Reducers stay pure: side effects are returned as `Effect`, not performed inline.
- Dependencies come through `@Dependency`, not singletons or directly constructed clients.
- Long-running or repeatable effects have a cancellation ID, are cancelled when their feature goes away, and cannot deliver an older response after a newer request.
- Errors thrown in `.run` effects are handled or deliberately reported, not silently ended.
- Child features compose through `Scope`, `ifLet`, `forEach`, or navigation reducers, not manually held stores.
- State observation matches the pattern the project uses for its version, such as `@ObservableState` with direct store access or `ViewStore` in older code.
- Navigation state is modelled in the reducer with `@Presents` or `StackState`, not owned by the view.
- Tests use `TestStore`, assert received actions and state changes, and control dependencies and clocks.
