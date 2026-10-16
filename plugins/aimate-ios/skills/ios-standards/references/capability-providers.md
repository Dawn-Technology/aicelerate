# Optional Capability Providers

These providers are optional. Detect them through the active host's skill and tool inventory. If several overlap, use the provider selected in the project instructions; otherwise prefer the first accepted provider relevant to the task and report the route used. Native Xcode tools come first; see `tooling.md`.

| Capability | Exact skill/tool identifier | Source | Selection |
| --- | --- | --- | --- |
| Build/test without Xcode open; simulator control, UI automation, and LLDB debugging | `MobileBuildMCP` | `getsentry/MobileBuildMCP` | Second build/test route after Xcode MCP; the UI automation route for `drive-ios`, which needs `MOBILEBUILDMCP_ENABLED_WORKFLOWS` to include `ui-automation` (and `debugging` for crash backtraces); disable telemetry for client work with `MOBILEBUILDMCP_SENTRY_DISABLED=true` |
| SwiftUI review | `swiftui-pro` | `twostraws/SwiftUI-Agent-Skill` | Optional depth for the SwiftUI module |
| Swift Testing | `swift-testing-pro` | `twostraws/Swift-Testing-Agent-Skill` | Framework detail; company naming in `testing.md` wins |
| Accessibility | `ios-accessibility` | `dadederk/iOS-Accessibility-Agent-Skill` | Advisory depth; manual assistive-technology checks remain necessary |
| Apple and DocC documentation | `sosumi.ai` | `NSHipster/sosumi.ai` | Last fallback in `apple-docs.md` and `tca.md`; no installation needed |

Do not install a provider during a review. Absence selects the standalone fallback and is not an error. Never allow an external provider's assumed deployment target, Swift version, architecture, or workflow to override project evidence.

Licenses, source links, and adoption reasoning are recorded in the plugin's `docs/capability-matrix.md` for maintainers.
