# UIKit to SwiftUI Conversion Guide

Read for every phase of `migrate-swiftui-ios`. It holds the strategy, the decision per screen, the UIKit-to-SwiftUI mapping, what must stay the same, and the estimation tables.

## Strategy

Convert incrementally, so the app builds and works after every batch:

1. **Pilot first**: one or two typical S or M leaf screens, with only the foundation they need (the styles and shared components they use). The pilot proves the approach in this project and measures real time and tokens before the larger estimate is trusted.
2. **Foundation next**: the remaining colors, fonts and text styles, spacing, images, and shared components (buttons, cells, empty and error states) that several screens use. Convert each shared component once and reuse it.
3. **Leaf screens next**: screens that push nothing further, then their parents. Each converted screen is a SwiftUI `View` hosted in a `UIHostingController` inside the existing navigation, so coordinators, segues that remain, and deep links keep working.
4. **Navigation and app lifecycle last, and only when approved**: replacing coordinators and `UINavigationController` with `NavigationStack`, and `AppDelegate`/`SceneDelegate` with a SwiftUI `App`, is a separate decision. Keep `UIApplicationDelegateAdaptor` for push notifications, background tasks, and SDK setup.

Keep the project's architecture (see `../../ios-standards/references/architecture.md`): an existing view model, presenter, or store drives the new view; do not introduce TCA, a new navigation library, or a new observation framework as part of the conversion. Introduce `@Observable` only when the deployment target is iOS 17 or later and the developer approves it; otherwise use `ObservableObject`.

## Base Classes

A base view controller with many subclasses (the inventory reports the count) is foundation work, not a screen. List what it gives every subclass, such as overlays (panic buttons, banners, warnings), keyboard handling, permission or session checks, and analytics. While navigation stays UIKit, a converted screen can stay inside the base class: host the SwiftUI view in a small subclass of it, so the shared behavior keeps working. Move a piece of shared behavior to SwiftUI (a view modifier or a container view) only when the developer approves it; until then, do not duplicate it in each converted screen. The base class itself is converted last, or never.

## Shared Presentation Helpers

Apps often present sheets, pickers, toasts, loaders, and alerts through `UIViewController` extensions (for example `presentSelectionSheet(...)`). A converted SwiftUI view cannot call them directly. Keep the helpers and give the view a closure or view model method that the hosting controller implements by calling the helper; convert a helper to SwiftUI only as its own foundation step.

## Deployment Target

| Minimum | What the conversion can use |
| --- | --- |
| iOS 13–14 | Basic SwiftUI only: no `NavigationStack`, limited lists, `@StateObject` from iOS 14. Recommend raising the minimum first with `raise-minimum-ios`; converting below iOS 15 costs more and leaves many wrappers. |
| iOS 15 | `AsyncImage`, `refreshable`, `searchable`, `task`, `FocusState`, swipe actions. Navigation stays in UIKit. |
| iOS 16 | `NavigationStack`, `Grid`, `Layout`, sheets with detents, `ViewThatFits`. |
| iOS 17 or later | `@Observable`, `ContentUnavailableView`, scroll position APIs, `onChange` with two values. |

Confirm availability with `../../ios-standards/references/apple-docs.md` when it decides a step.

## Decision per Screen

Classify every view controller and shared UIKit view as one of:

| Decision | When |
| --- | --- |
| `convert` | Standard content: forms, lists, details, settings, onboarding, simple collections. |
| `convert with wrapper` | Mostly standard, with one UIKit-only part wrapped in `UIViewRepresentable` or `UIViewControllerRepresentable`, such as a map with custom annotations, a camera, a mail composer, a document picker, or a rich text editor. |
| `keep UIKit` | Converting costs more than it gains, or SwiftUI cannot match the behavior at the deployment target: complex custom collection layouts, custom transitions, heavy drawing, text editing with TextKit, or performance-critical lists. Host it from SwiftUI with `UIViewControllerRepresentable` when its parent is converted. |
| `remove` | Dead or legacy screens that nothing presents any more (confirm with the developer; the inventory's "possibly unreferenced" is a hint, not proof). |
| `already SwiftUI` | A UIKit controller that only hosts a SwiftUI view (the inventory's "SwiftUI host"). No conversion; it disappears when its parent's navigation is converted. |

Name the reason for every decision other than `convert`.

## Mapping

| UIKit | SwiftUI |
| --- | --- |
| `UIViewController` with a view model | `View` with the view model as `@StateObject`/`@ObservedObject` (or `@State`/`@Bindable` with `@Observable`), hosted in `UIHostingController` while navigation stays UIKit |
| Storyboard scene or XIB | Code in the `View`; remove the scene and its `IBOutlet`/`IBAction` only when nothing else uses them |
| `UITableView`, `UICollectionView` with flow layout | `List` or `ScrollView` with `LazyVStack`/`LazyVGrid`; diffable data sources become `ForEach` over identifiable data |
| `UITableViewCell`, `UICollectionViewCell` | A row `View`; keep separators, insets, and selection behavior the design needs |
| Auto Layout, `UIStackView`, SnapKit | Stacks, `frame`, `padding`, `Spacer`, `Grid`, `ViewThatFits` |
| `UIRefreshControl` | `refreshable` (iOS 15) |
| `UISearchController` | `searchable` (iOS 15) |
| `UIAlertController` | `alert` and `confirmationDialog` |
| Present, push, dismiss | Coordinator or presenting controller keeps doing it through closures from the view; `sheet`, `fullScreenCover`, and `NavigationStack` only when navigation is converted |
| Delegates and target-action | Closures or view model methods |
| Combine bindings, KVO | `@Published` or `@Observable` properties observed by the view |
| RxSwift bindings | Keep the Rx view model and bridge it to an observable object; replacing Rx is a separate decision |
| Keyboard notifications | Built-in keyboard avoidance, `FocusState`, `scrollDismissesKeyboard` |
| `WKWebView`, `MKMapView` with UIKit-only features, `PDFView`, camera, composers, document pickers | `UIViewRepresentable` or `UIViewControllerRepresentable` wrapper (`Map` for simple maps on iOS 17) |
| Custom `draw(_:)`, `CAShapeLayer` | `Canvas`, `Shape`, or `Path`; keep as a wrapper when it is performance-critical |
| Child view controllers | Composed views; keep a UIKit child only when it is `keep UIKit` |

## Must Stay the Same

For every converted screen, keep and check:

- **Behavior**: data loading, error and empty states, pagination, pull to refresh, validation, and analytics events.
- **Accessibility identifiers** that UI tests use (`accessibilityIdentifier`), plus labels, traits, and Dynamic Type (see `../../ios-standards/references/accessibility.md`).
- **Localization**: the same keys and bundles, so no text falls back to the key (see `../../ios-standards/references/localization.md`). When the app switches language at runtime (for example Localize-Swift or a custom bundle), keep its lookup: a resolved `String` passed to `Text` is shown verbatim, so the view must observe the app's language-change notification and re-render, and must not switch to `LocalizedStringKey` lookups that ignore the in-app language.
- **Navigation entry points**: deep links, push notification routes, and state restoration that open the screen.
- **Look**: spacing, colors, fonts, and dark mode as close as the design requires; list the differences the developer must accept.

## Project Files

Adding and removing Swift files, storyboards, and XIBs changes the Xcode project unless its folders are synchronized groups (Xcode 16 and later). Before converting:

- With synchronized folders, add and remove files in the folder.
- With XcodeGen or Tuist, change the files and regenerate the project with the project's documented command.
- Otherwise, recommend that the developer converts the affected groups to folders in Xcode first ("Convert to Folder"), or approves minimal edits to `project.pbxproj`. Never rewrite the project file wholesale; build after each edit.

## Estimates

Estimate per screen from its complexity class (from `uikit_inventory.py`) and its decision, then add the foundation and navigation work. Show agent time in minutes or hours, tokens in millions, and developer time in hours, per screen and per batch. These are starting values; replace them with the measured pilot result (see the skill) and record the actual numbers in the report so the team can tune this table.

| Class | Screen (rules from `uikit_inventory.py`; minor and major flags are its weights 1 and 2) | Agent time | Tokens, all types | Output tokens | Developer review and testing |
| --- | --- | --- | --- | --- | --- |
| S | Up to 150 lines, in code, at most one minor flag | 5–15 min | 0.5–1.5 M | 10–25 k | 0.5–1 h |
| M | Up to 400 lines, or from a storyboard or XIB, or two minor flags | 15–30 min | 1.5–4 M | 25–60 k | 1–2 h |
| L | Up to 800 lines, or one major flag (map, camera, custom layout, Rx) | 30–60 min | 4–8 M | 60–120 k | 2–4 h |
| XL | More than 800 lines, or two or more major flags | 1–2 h | 8–16 M | 120–250 k | 4–8 h |

- `convert with wrapper`: 1.5 times the values of its class. `keep UIKit`: about 10% of its class, for hosting it from a converted parent. `remove`: a few minutes and a small fraction of an S each; count it with the batch that removes it.
- Foundation: one M per three to five shared components, where a shared component is a UIKit view or cell the inventory marks as shared (used by three or more files), plus styles. A base class with subclasses: one L to plan and wrap it, more only when its behavior moves to SwiftUI.
- Navigation conversion: one L per navigation flow. A flow is a coordinator that owns screen navigation (the inventory marks coordinators as `navigation` or `service`; service coordinators do not count) or a storyboard with segues that no coordinator drives. When an app has both, count each flow once. App lifecycle: one M.
- **MVC screens** (the inventory's `MVC`: no view model, presenter, or store): extracting the state and logic into a view model comes first, so estimate them one class higher (S becomes M, and so on; XL times 1.5).
- **Styles**: one S when the project already has SwiftUI colors, fonts, and spacing (for example from earlier SwiftUI screens), one M when they exist only for UIKit, plus one M for a design system of custom controls.
- **Containers** (the inventory's `container`, such as a tab bar controller): navigation work, one M each, only when navigation is converted; while navigation stays UIKit, they cost nothing.
- `already SwiftUI`: no cost. Round shared-component groups up (8 shared components at three to five per M is two to three M; use the range).
- Scan and plan (phases 1 to 3): about 2–6 M tokens for an app of 50–100 screens; report it separately from the conversion.
- Sum every column, including output tokens, per batch and in total.
- Tokens are dominated by cache reads, because every step re-reads the conversation. Report all four types (input, cache write, cache read, output); the team's price list decides the cost, not this skill.
- Give every total as a range, never a single number.
