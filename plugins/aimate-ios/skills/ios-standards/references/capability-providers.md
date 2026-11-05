# Optional Capability Providers

These providers are optional. Detect them through the active host's skill and tool inventory. If several overlap, use the provider selected in the project instructions; otherwise prefer the first accepted provider relevant to the task and report the route used. Builds, tests, simulator interaction, and debugging use Xcode's own tools; see `tooling.md`.

| Capability | Exact skill/tool identifier | Source | Selection |
| --- | --- | --- | --- |
| SwiftUI review | `swiftui-pro` | `twostraws/SwiftUI-Agent-Skill` | Optional depth for the SwiftUI module |
| Swift Testing | `swift-testing-pro` | `twostraws/Swift-Testing-Agent-Skill` | Framework detail; company naming in `testing.md` wins |
| Accessibility | `ios-accessibility` | `dadederk/iOS-Accessibility-Agent-Skill` | Advisory depth; manual assistive-technology checks remain necessary |
| Apple and DocC documentation | `sosumi.ai` | `NSHipster/sosumi.ai` | Last fallback in `apple-docs.md` and `tca.md`; no installation needed |

Do not install a provider during a review. Absence selects the standalone fallback and is not an error. Never allow an external provider's assumed deployment target, Swift version, architecture, or workflow to override project evidence.

Licenses, source links, and adoption reasoning are recorded in the plugin's `docs/capability-matrix.md` for maintainers.
