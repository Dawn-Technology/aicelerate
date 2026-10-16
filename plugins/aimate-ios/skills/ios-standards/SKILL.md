---
name: ios-standards
description: Internal company iOS policy, loaded by other aimate-ios skills such as review-ios. Not for direct use; use review-ios for reviews.
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
| Which architecture applies, or MVVM + Coordinators checks | `references/architecture.md` |
| Project that imports `ComposableArchitecture` | `references/tca.md` |
| Secrets, Keychain, biometrics, logging, transport, deep links, web content, or other security-sensitive change | `references/security.md` |
| Apple API availability, deprecation, or documentation | `references/apple-docs.md` |
| Existing UIKit, SwiftUI, XCTest, or mixed codebase | `references/legacy-projects.md` |
| XCTest, XCUITest, or Swift Testing | `references/testing.md` |
| Xcode, simulator, device, or host capability | `references/tooling.md` |
| Accepted optional capability providers | `references/capability-providers.md` |

Do not infer missing company Swift style rules. The earlier Ray Wenderlich/Kodeco-derived standard still needs to be recovered and reviewed.
