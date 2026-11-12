# Release notes

## 0.1.0 (2026-11-04)

First version of `aimate-ios`, an optional plugin next to `aimate` for native iOS projects.

- `review-ios`: iOS specialist pass next to the generic review, covering SwiftUI, UIKit, concurrency, lifecycle, accessibility, TCA, MVVM + Coordinators, XCTest, XCUITest, Swift Testing, deployment targets, and Apple-platform API compatibility. Returns the generic `code-review` output shape.
- `test-ios`: builds and runs the tests affected by a change, or named tests, on a simulator through Xcode MCP or `xcodebuild`.
- `security-audit-ios`: read-only security audit of a whole iOS project against OWASP MASVS 2.1 and the MASTG iOS tests that can be checked from source, with a status per MASVS control, in the `review-ios` output shape.
- `fix-localization-ios`: scans localization, presents a fix plan, and fixes the approved items on a new branch; checks every approved item afterwards and reports why any is not fixed.
- `raise-minimum-ios`: raises the minimum iOS version and removes code that only existed for older versions, after a confirmed plan.
- `review-architecture-ios`: iOS companion of `review-architecture`, with Swift module-graph and platform-health scripts.
- `summarize-project-ios`: onboarding overview and assessment of an iOS project.
- `ios-standards`: shared company iOS policy that the other skills read.

Builds, tests, and diagnostics use Xcode's own tools (Xcode 27 or later), with `xcodebuild` as fallback.
