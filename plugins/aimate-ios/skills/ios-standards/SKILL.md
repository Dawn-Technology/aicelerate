---
name: ios-standards
description: Use when another aimate-ios skill needs company policy for an existing or new native iOS project, especially architecture selection, legacy constraints, testing conventions, deployment targets, or tool capability resolution.
metadata:
  author: "Dawn Technology"
  version: 0.1.0
  role: "internal-policy-foundation"
---

# iOS Standards

This internal foundation contains only company-owned policy. Load the references relevant to the task; prefer accepted external specialists for detailed framework guidance.

## Reference Selection

| Need | Read |
| --- | --- |
| Conflicting rules or company-standard deviation | `references/precedence.md` |
| TCA, MVVM, native state, or pattern selection | `references/architecture.md` |
| Existing UIKit, SwiftUI, XCTest, or mixed codebase | `references/legacy-projects.md` |
| XCTest, XCUITest, or Swift Testing | `references/testing.md` |
| Xcode, simulator, device, or host capability | `references/tooling.md` |
| Accepted optional capability providers | `references/capability-providers.md` |

Do not infer missing company Swift style rules. The earlier Ray Wenderlich/Kodeco-derived standard still needs to be recovered and reviewed.
