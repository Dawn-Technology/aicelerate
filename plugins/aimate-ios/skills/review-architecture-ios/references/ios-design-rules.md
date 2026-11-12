# iOS Design Rules

iOS additions to the generic architecture rules. Cite findings by the generic rule names (`design-rules.md` of `aimate`'s `review-architecture`, or the condensed list in `SKILL.md`); this file says how those rules apply to iOS, which signals are iOS-specific, and when not to flag.

## Layer Mapping

Name the architecture from code with [`../../ios-standards/references/architecture.md`](../../ios-standards/references/architecture.md), then map:

| Generic layer | TCA | MVVM + Coordinators |
| --- | --- | --- |
| Domain | Model and pure-logic modules (no SwiftUI or UIKit) | Domain models and use cases |
| Application | Reducers (`*Feature`) orchestrating through `@Dependency` clients | View models and coordinators |
| Infrastructure | Live dependency clients, persistence (GRDB, SwiftData, Core Data), networking, SDK wrappers | Repositories, data stores, adapters, networking |
| UI | SwiftUI and UIKit views (`*View`) | Views and view controllers |

Layers in iOS projects are Swift package targets or Xcode targets, not folders. Use `scripts/swift_modules.py` for the graph: declared dependencies, imports, transitive dependency counts, and Xcode target links.

## Apple Frameworks

- `Foundation` is allowed everywhere.
- `SwiftUI`, `UIKit`, `AVKit`, and SDK view types in a domain module break Dependency Direction. A player or SDK view passed through a use case is common; flag it only when it blocks a change or test you can name.
- Reducers importing `SwiftUI` for TCA bindings and presentation, or `UIKit` for `openSettingsURLString`, follow the framework's idiom: do not flag.
- A generated API contract (OpenAPI types) used as the domain model is a recorded deviation only when project instructions or an ADR state that decision explicitly; a note on where generated files go is not a decision. Otherwise report it once as Medium under Dependency Direction, with the count of references outside the networking layer.

## iOS Signals

Severity follows the generic rules: High in a hot spot when it blocks safe change or testing, Medium for a clear violation outside the top hot spots, Low for local cleanup. The notes give exceptions.

| Signal | Rule to cite | Notes |
| --- | --- | --- |
| A low-level module (components, styling, utilities) depends on the composition root or on features; visible as a high transitive count with high fan-in | Dependency Direction | Name the import that creates the edge. |
| A target imports an internal module it does not declare | Module Encapsulation | Low unless it hides a layering break. |
| A hand-written `==` or `hash` on TCA `State` or `Action` that omits fields | Tested Where It Changes | `TestStore` compares with `==`, so assertions on the omitted fields always pass. High in a hot spot. |
| Side effects in a reducer or view model outside dependencies: `URLSession.shared`, `String(contentsOf:)`, `UserDefaults.standard`, `Date()`, `UUID()`, `FileManager.default`, database queries | Abstraction Decoupling | Untestable without the real system. |
| Feature flags or remote config read directly in views | Layer Isolation | Flags belong in state or the view model, so tests and snapshots can set them. |
| A parent reducer pattern-matches deep child actions instead of child delegate actions | Module Encapsulation | Every child change touches the parent. |
| Navigation or routing rules copied per tab or screen, and the copies differ | Single Source of Truth | Show both copies and the difference. |
| One root reducer, coordinator, or view model owns unrelated concerns (navigation, deep links, persistence, loading, alerts) | Single Reason to Change | Count the concerns and the lines. |
| Dependency injection that fails only at runtime (`fatalError("not registered")`) or depends on startup order | Abstraction Decoupling | Report once, with the count of crash-on-resolve entries. Low unless a crash on resolve has happened or a hot spot depends on startup order. |
| iOS and tvOS (or iPhone and iPad) code duplicated per feature where the logic, not only the layout, is copied | Single Source of Truth | Duplicated views for different platforms are expected. |
| Logic duplicated between Swift and shared Kotlin Multiplatform or server code | Single Source of Truth | Name both locations. |

## Cycles

SwiftPM rejects cycles between targets, so Acyclic Dependencies between package targets holds by construction; `swift_modules.py` still reports import cycles. Cycles between files inside one large target are not checked; say so in "Method and limits".

## Tests

Count TCA `TestStore` tests of a parent reducer and snapshot tests of a parent view as tests of the children they cover. "No tests by name" is not "no tests" until you have checked those.

## Platform

Replaces Supported Platform for apps. The deployment target is a floor, not a runtime: Apple publishes no end-of-life dates for iOS versions, and endoflife.date entries for iOS do not mean an app on that minimum is unsupported. Never report a support date for iOS, tvOS, or watchOS.

- Report deployment targets per Xcode target and package, from `scripts/ios_platform.py`.
- The cost of an old minimum is the availability and backport code it forces: the count of `#available`/`@available` checks, backport modules, and packages that exist only for older systems. Medium when that code sits in hot spots or many files; Low otherwise. An old minimum alone is never High.
- Platforms declared in packages or Xcode targets that cannot build or are not shipped: Low, or Medium when shared schemes or test plans still include them.
- Mixed Swift language modes or strict-concurrency settings between targets: Low, Medium when a hot spot sits on the less strict side.
- The `swift-tools-version` and project format against the local Xcode: report only a mismatch.

## Dependency Health

Replaces the package-manager checks for SwiftPM.

- Direct dependencies pinned to a branch or revision, or coming from a personal fork: Medium; Low when the code that uses them is not in a hot spot.
- `Package.resolved` files that disagree: Medium when one resolves outside the manifest's requirement, Low otherwise.
- Packages declared but not used by any target: Low.
- Vendored binary frameworks: note their version and update path; not a finding by themselves.
- SwiftPM has no deprecation flag: do not report "no deprecated packages" as a checked result.
