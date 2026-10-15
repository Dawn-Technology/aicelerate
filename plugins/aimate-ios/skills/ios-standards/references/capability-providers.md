# Optional Capability Providers

These providers are optional. Detect them through the active host's skill and tool inventory. If several overlap, use the project-selected provider from `AGENTS.md`; otherwise prefer the first accepted provider relevant to the task and report the route used.

| Capability | Exact skill/tool identifier | Source | Selection |
| --- | --- | --- | --- |
| TCA | `ComposableArchitecture` | Point-Free Way | Prefer when installed; official and version-maintained |
| Open TCA fallback | `tca` | `kwon2540/tca-agent-skills` | Use only at a project-approved pinned revision |
| Architecture selection | `swift-architecture-skill` | `efremidze/swift-architecture-skill` | Compose for pattern selection, not as project policy |
| Xcode build/test | `MobileBuildMCP` | `getsentry/MobileBuildMCP` | Preferred executable provider |
| Simulator flows | `MobileBuildMCP`; `Maestro` | `getsentry/MobileBuildMCP`; `mobile-dev-inc/Maestro` | MobileBuildMCP first; Maestro only when the project checks in Maestro flows; avoid overlapping automation ownership |
| Physical device | `mobile-mcp` | `mobile-next/mobile-mcp` | Use only after device/privacy preflight |
| SwiftUI implementation | `swiftui-expert-skill` | `AvdLee/SwiftUI-Agent-Skill` | Preferred SwiftUI specialist |
| SwiftUI review | `swiftui-pro` | `twostraws/SwiftUI-Agent-Skill` | Use selectively; do not run equal-priority overlapping SwiftUI specialists |
| Swift Testing | `swift-testing-pro` | `twostraws/Swift-Testing-Agent-Skill` | Framework detail; company naming still applies |
| Accessibility | `ios-accessibility` | `dadederk/iOS-Accessibility-Agent-Skill` | Advisory depth; manual checks remain necessary |
| Apple documentation | `sosumi`; structured search tool `apple-docs-mcp` | `NSHipster/sosumi.ai`; `kimsungwhee/apple-docs-mcp` | Installed SDK/compiler evidence still outranks cached guidance |

Do not install a provider during a review. Absence selects the standalone fallback and is not an error. Never allow an external provider's assumed deployment target, Swift version, architecture, or workflow to override project evidence.

Licenses, source links, and adoption reasoning are recorded in the plugin's `docs/capability-matrix.md` for maintainers.
