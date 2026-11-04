# Capability Matrix

External providers are optional. Selection prefers native Apple tooling, then company-owned references, then third-party providers only when they add clear value without extra installation burden. Verify versions and licenses again before organization-wide installation. Runtime selection rules are copied into `skills/ios-standards/references/capability-providers.md` so a skills-only installation remains self-contained.

| Capability | Preferred provider | Decision | License / source | Standalone fallback |
| --- | --- | --- | --- | --- |
| Xcode build, tests, diagnostics, previews, documentation search | Xcode MCP (`xcrun mcpbridge`, Xcode 27 or later) | Only build and test provider: the project lead wants the team to work through Xcode itself; native and nothing to install | Apple, bundled with Xcode | `xcodebuild`/`simctl`, then static inspection |
| TCA guidance | Company [`tca.md`](../skills/ios-standards/references/tca.md) reading the TCA DocC articles at the resolved version | Own; Point-Free Way subscription not adopted | TCA documentation is MIT ([`pointfreeco/swift-composable-architecture`](https://github.com/pointfreeco/swift-composable-architecture)) | Local checkout, GitHub at the resolved tag, then Sosumi |
| Architecture checks | Company [`architecture.md`](../skills/ios-standards/references/architecture.md) | Own; TCA and MVVM + Coordinators are company standards, legacy patterns are followed | Company | Checks for every pattern |
| Apple documentation | Company [`apple-docs.md`](../skills/ios-standards/references/apple-docs.md); [`NSHipster/sosumi.ai`](https://github.com/NSHipster/sosumi.ai) as last fallback | Own the lookup order; adopt Sosumi because it needs no installation | Apple; Sosumi is MIT | Installed SDK declarations and compiler diagnostics |
| SwiftUI review | [`twostraws/SwiftUI-Agent-Skill`](https://github.com/twostraws/SwiftUI-Agent-Skill) | Compose as optional depth; text-only | MIT | `review-ios` SwiftUI module |
| Swift Testing | [`twostraws/Swift-Testing-Agent-Skill`](https://github.com/twostraws/Swift-Testing-Agent-Skill) | Compose as optional depth; company naming wins over its raw-identifier style | MIT | Company testing reference plus compiler/project evidence |
| Accessibility | [`dadederk/iOS-Accessibility-Agent-Skill`](https://github.com/dadederk/iOS-Accessibility-Agent-Skill) | Compose as optional depth; covers SwiftUI and UIKit; manual assistive-technology checks remain necessary | MIT | `review-ios` accessibility module |
| Security review | Company [`security.md`](../skills/ios-standards/references/security.md) | Own the checks and severities | Company, with Apple documentation as sources | `review-ios` Security module |
| UI automation (tests) | XCUITest through Xcode MCP | Company standard | Apple | Static inspection |
| Driving the app on a simulator | Xcode 27 device interaction, used directly by the developer's agent | `drive-ios` removed: Xcode 27 covers tapping through the app, logs, and debugging, and the chapter lead prefers it | Apple, bundled with Xcode | — |
| Physical-device interaction | None in V1 | Deferred until simulator automation is reliable | — | `device-not-run` with reason |
| GitHub operations | Generic `aimate` through `gh` | Reuse; do not duplicate in this plugin | Existing aimate behavior | Report manual remote action when no route works |

## Rejected

| Provider | Reason |
| --- | --- |
| [Point-Free Way](https://www.pointfree.co/the-way) | Requires a commercial subscription; replaced by `tca.md` |
| [`kwon2540/tca-agent-skills`](https://github.com/kwon2540/tca-agent-skills) | Unversioned third-party copy of TCA guidance; replaced by `tca.md` |
| [`efremidze/swift-architecture-skill`](https://github.com/efremidze/swift-architecture-skill) | Competes with company architecture policy and produces migration plans; replaced by `architecture.md` |
| [Maestro](https://github.com/mobile-dev-inc/Maestro) | Third-party framework to install; conflicts with the XCUITest standard |
| [`getsentry/MobileBuildMCP`](https://github.com/getsentry/MobileBuildMCP) | Third-party install with its own build cache (tens of gigabytes per project) that fails on private SSH packages; the project lead wants the team to use Xcode itself, and Xcode 27 MCP covers builds, tests, simulator interaction, and debugging |
| [`mobile-next/mobile-mcp`](https://github.com/mobile-next/mobile-mcp) | Third-party install; overlaps Xcode MCP device interaction; device automation is deferred |
| [`AvdLee/SwiftUI-Agent-Skill`](https://github.com/AvdLee/SwiftUI-Agent-Skill) | Implementation-focused; reconsider at the `build-swiftui` evaluation |
| [`kimsungwhee/apple-docs-mcp`](https://github.com/kimsungwhee/apple-docs-mcp) | Third-party install; replaced by Xcode `DocumentationSearch`, Apple documentation JSON, and Sosumi |
| [`dpearson2699/swift-ios-skills`](https://github.com/dpearson2699/swift-ios-skills) (`swift-security`) | PolyForm Perimeter 1.0.0 (non-OSI, noncompete clause), although its `SKILL.md` frontmatter says MIT; replaced by `security.md`. Do not copy its content |
| `xclaude-plugin` | Abandoned; its maintainer points to newer alternatives |
| Appium | Not a default unless a project already standardizes on it |

Do not adopt non-OSI or restrictive skill licenses without Legal approval. Do not fork external skills merely to adjust company policy; compose a small local reference instead.

## Project Record

Projects should record selected optional providers in `AGENTS.md`, including a pinned version or revision where upstream changes can break behavior. Re-evaluate a provider when it fails or when a relevant Xcode, Swift, SDK, or package version changes.
