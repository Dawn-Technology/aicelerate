# Capability Matrix

External providers are optional. Selection prefers official ownership, suitable licensing, current maintenance, portable skill content, and low company maintenance. Verify versions and licenses again before organization-wide installation. Runtime selection rules are copied into `skills/ios-standards/references/capability-providers.md` so a skills-only installation remains self-contained.

| Capability | Preferred provider | Decision | License / source | Standalone fallback |
| --- | --- | --- | --- | --- |
| TCA guidance | [Point-Free Way](https://www.pointfree.co/the-way) | Adopt when the subscription and skill-content terms are acceptable; it is official and supports OpenCode, Claude Code, Codex, and Copilot | Commercial subscription; installer [`pointfreeco/pfw`](https://github.com/pointfreeco/pfw) is MIT | Qualities-first company policy plus current official TCA documentation |
| Open TCA guidance | [`kwon2540/tca-agent-skills`](https://github.com/kwon2540/tca-agent-skills) | Compose only after pinning and reviewing; current but has limited adoption history | MIT | Inspect the installed TCA version and use official documentation |
| Architecture selection | [`efremidze/swift-architecture-skill`](https://github.com/efremidze/swift-architecture-skill) | Compose; it supports selecting among TCA, MVVM, and simpler patterns | MIT | Company qualities-first architecture reference |
| Xcode build and tests | [`getsentry/MobileBuildMCP`](https://github.com/getsentry/MobileBuildMCP) | Adopt as the preferred optional executable provider | MIT | Host-native Xcode integration, approved local CLI, then static inspection |
| Simulator UI automation | MobileBuildMCP; optionally [Maestro](https://github.com/mobile-dev-inc/Maestro) for durable high-level flows | Adopt MobileBuildMCP; compose Maestro only where checked-in flows add value | MIT / Apache-2.0 | Existing XCUITest through available Xcode tooling |
| Physical-device interaction | [`mobile-next/mobile-mcp`](https://github.com/mobile-next/mobile-mcp) | Compose only for approved devices after trust, signing, and privacy preflight | Apache-2.0 | `device-not-run` with reason |
| SwiftUI implementation | [`AvdLee/SwiftUI-Agent-Skill`](https://github.com/AvdLee/SwiftUI-Agent-Skill) | Adopt as preferred optional SwiftUI specialist | MIT | Company project-precedence and visual-validation policy |
| SwiftUI review | [`twostraws/SwiftUI-Agent-Skill`](https://github.com/twostraws/SwiftUI-Agent-Skill) | Compose selectively; do not enable overlapping SwiftUI specialists at equal priority | MIT | `review-ios` deterministic checklist |
| Swift Testing | [`twostraws/Swift-Testing-Agent-Skill`](https://github.com/twostraws/Swift-Testing-Agent-Skill) | Adopt for Swift Testing; retain company naming and XCTest/XCUITest policy | MIT | Company testing reference plus compiler/project evidence |
| Accessibility | [`dadederk/iOS-Accessibility-Agent-Skill`](https://github.com/dadederk/iOS-Accessibility-Agent-Skill) | Adopt after organizational review; manual assistive-technology checks remain necessary | MIT | Company accessibility checks in specialist review |
| Apple documentation | [`NSHipster/sosumi.ai`](https://github.com/NSHipster/sosumi.ai); optionally [`apple-docs-mcp`](https://github.com/kimsungwhee/apple-docs-mcp) | Adopt Sosumi for portable retrieval; compose MCP for structured search | MIT | Installed SDK declarations, compiler diagnostics, and source inspection |
| GitHub operations | Generic `aimate` through `gh` | Reuse; do not duplicate in this plugin | Existing aimate behavior | Report manual remote action when no route works |

## Rejected as Defaults

- Do not adopt non-OSI or restrictive skill licenses without Legal approval.
- Do not use abandoned `xclaude-plugin`; its maintainer points to newer alternatives.
- Do not make Appium the default unless a project already standardizes on it.
- Do not fork external skills merely to adjust company policy; compose a small local reference instead.

## Project Record

Projects should record selected optional providers in `AGENTS.md`, including a pinned version or revision where upstream changes can break behavior. Re-evaluate a provider when it fails or when a relevant Xcode, Swift, SDK, or package version changes.
