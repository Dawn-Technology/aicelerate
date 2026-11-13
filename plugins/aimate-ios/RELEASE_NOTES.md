# Release notes

## 0.1.0 (2026-11-04)

First version of `aimate-ios`, an add-on to `aimate` for native iOS projects. Requires `aimate`: the review skills run `aimate`'s review skills with iOS depth added, and the audits use the output format of `aimate`'s `code-review`.

- `review-ios`: iOS layer on top of `aimate`'s `review-pr`, `review-local`, and `code-review`, adding iOS depth to the same review, covering SwiftUI, UIKit, concurrency, lifecycle, accessibility, TCA, MVVM + Coordinators, XCTest, XCUITest, Swift Testing, deployment targets, and Apple-platform API compatibility. Returns the generic `code-review` output shape.
- `test-ios`: builds and runs the tests affected by a change, or named tests, on a simulator through Xcode MCP or `xcodebuild`.
- `security-audit-ios`: read-only security audit of a whole iOS project against OWASP MASVS 2.1 and the MASTG iOS tests that can be checked from source, with a status per MASVS control, in the `review-ios` output shape.
- `accessibility-audit-ios`: validates a whole iOS app against WCAG 2.2 A and AA, interpreted for native screens, with a status per criterion in an untracked report in `docs/`; offers a thorough check that runs Apple's automated accessibility audit in XCUITest on a simulator.
- `fix-localization-ios`: scans localization, presents a fix plan, and fixes the approved items on a new branch; checks every approved item afterwards and reports why any is not fixed.
- `raise-minimum-ios`: raises the minimum iOS version and removes code that only existed for older versions, after a confirmed plan.
- `migrate-swiftui-ios` (alpha, use at your own risk): converts UIKit screens to SwiftUI after a plan with time and token estimates and agreement with the developer, in batches that build and test; reports the result and the tokens used.
- `review-architecture-ios`: iOS layer on top of `aimate`'s `review-architecture` (no fallback copy of its method), with Swift module-graph and platform-health scripts.
- `summarize-project-ios`: onboarding overview and assessment of an iOS project.
- `ios-standards`: shared company iOS policy that the other skills read.

Builds, tests, and diagnostics use Xcode's own tools (Xcode 27 or later), with `xcodebuild` as fallback.
