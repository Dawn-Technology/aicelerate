# Aimate iOS V1 — Session Handoff

Date: 2026-10-15 (updated after the provider review session) · Branch: `feature/ai-mate-ios-v0` · Repo: `Dawn-Technology/aicelerate`

Handoff purpose: a fresh agent session (Claude Code, Codex, Copilot, OpenCode) can continue the `aimate-ios` work from this file plus the linked repo docs without re-interviewing the user.

## 1. Project Context

`aicelerate` is a Dawn Technology agent-plugin marketplace. It hosts the generic, company-wide `aimate` plugin (GitHub PR workflows, code review, SDLC skills). This work adds an **optional, separately installable plugin for the mobile iOS team** (`aimate-ios`), while other departments keep using only `aimate`, which stays generic and untouched. The Android team will build its own plugin; that is out of scope here.

Key repo conventions:

- Copilot-canonical manifests; Claude compatibility via symlink `plugins/aimate-ios/.claude-plugin/plugin.json -> ../plugin.json`.
- No build system, tests, or CI: **Markdown-as-runtime**. Skills are executed by reading them; validation is mechanical checks only.
- Skills use the portable Agent Skills `SKILL.md` format (YAML frontmatter), which all four target hosts read natively.
- `docs/superpowers/` is temporary working material; the user removes it manually when the work is done.

## 2. Approved Design Decisions (user-confirmed)

1. **Plugin separation**: iOS knowledge goes in `aimate-ios`; `aimate` remains generic.
2. **Native first, few installs**: capability resolution order is explicit user/project route → native host/Xcode → accepted optional provider → command-line route → static inspection with honest reporting. Do not add third-party tools that need installing unless they bring clear value. All external providers are optional. States: `available` / `fallback` / `unavailable` / `not-required`; verification: `simulator-verified` / `device-verified` / `device-not-run: <reason>`.
3. **Policy precedence** (highest → lowest): user instruction → `AGENTS.md`/ADR/local skills → Xcode project/deployment targets → strong repo evidence → company standard (`ios-standards`) → general Apple guidance. Deviations are always reported, never silently migrated.
4. **Architecture**: the skills never choose an architecture. New projects use the company template's choice (TCA by default, or MVVM + Coordinators), stated in `AGENTS.md` or clear from the code. Existing and legacy projects follow whatever they use (legacy can be any pattern). Migrations never incidental. *(Supersedes the spec's "no TCA/MVVM default"; the spec was intentionally not edited.)*
5. **Testing standard**: Swift Testing for new unit tests; existing XCTest suites continue; XCUITest for UI; naming `test_<subject>_<condition>_<expected behavior>()` or a `@Test("…")` display name with a lower-camel-case function; no raw-identifier names unless the project already uses them; AAA structure; minimal `async`/`throws`.
6. **Host support**: OpenCode, Claude Code, Codex, GitHub Copilot. GitHub/`gh` operations stay in generic `aimate`.
7. **V1 exclusions**: signing, provisioning, certificates, archives, TestFlight, App Store Connect, release automation, incidental migrations, mandatory snapshot tests, physical-device automation.
8. **Pilot-first**: `review-ios` (read-only) before any write-enabled skill.
9. **Do not commit** unless the user asks. The user cannot open a PR yet (missing repository rights).

### Provider decisions (2026-10-15 review)

| Provider | Decision |
| --- | --- |
| Xcode MCP (`xcrun mcpbridge`) | **First route** for build, test, diagnostics, previews, `DocumentationSearch`. Read-only skills never use its write tools. |
| `getsentry/MobileBuildMCP` | Kept, optional, second route (no Xcode open, simulator control). Disable telemetry with `MOBILEBUILDMCP_SENTRY_DISABLED=true` for client work. |
| `twostraws` `swiftui-pro` | Kept, optional (SwiftUI review). |
| `twostraws` `swift-testing-pro` | Kept, optional; company naming wins. |
| `dadederk` `ios-accessibility` | Kept, optional. |
| `NSHipster/sosumi.ai` | Kept, optional; last fallback for Apple docs and TCA docs. |
| Point-Free Way, `kwon2540/tca-agent-skills` | Dropped (no subscription); replaced by company `tca.md`. |
| `efremidze/swift-architecture-skill` | Dropped; replaced by company `architecture.md`. |
| Maestro, `mobile-next/mobile-mcp` | Dropped (third-party installs; device automation deferred). |
| `AvdLee/SwiftUI-Agent-Skill` | Dropped for now; reconsider at the `build-swiftui` evaluation. |
| `kimsungwhee/apple-docs-mcp` | Dropped; replaced by company `apple-docs.md`. |

## 3. Current State

- Commit `09da24c ai-mate-ios: WIP` contains the original plugin, spec, plan, README and marketplace changes.
- Uncommitted on top of it: the provider review changes below, plus this handoff (untracked).

| File | Purpose |
| --- | --- |
| `docs/superpowers/specs/2026-10-15-aimate-ios-design.md` | Original design (temporary; architecture and provider decisions above supersede it) |
| `docs/superpowers/plans/2026-10-15-aimate-ios-v1.md` | 6-task plan; Tasks 1–5 done, Task 6 pending (checkboxes not updated) |
| `plugins/aimate-ios/plugin.json` (+ Claude symlink) | Manifest v0.1.0 |
| `plugins/aimate-ios/README.md` | Install per host, Xcode MCP setup (`claude mcp add xcode -- xcrun mcpbridge`), MobileBuildMCP telemetry note |
| `plugins/aimate-ios/docs/capability-matrix.md` | Maintainer record: kept providers, company replacements, rejected providers with reasons |
| `plugins/aimate-ios/skills/ios-standards/SKILL.md` | Internal policy index |
| `…/ios-standards/references/architecture.md` | Template rule, pattern identification table, checks for every pattern, MVVM + Coordinators checks |
| `…/ios-standards/references/tca.md` | Resolve TCA version from `Package.resolved`; docs from local checkout → GitHub tag → Sosumi; TCA review checks |
| `…/ios-standards/references/apple-docs.md` | SDK/compiler → Xcode `DocumentationSearch` → Apple documentation JSON → Sosumi |
| `…/ios-standards/references/tooling.md` | Native-first order; build/test order; read-only Xcode MCP tool limits |
| `…/ios-standards/references/{precedence,legacy-projects,testing,capability-providers}.md` | Precedence, legacy rules, testing policy, optional providers |
| `plugins/aimate-ios/skills/review-ios/SKILL.md` | Read-only iOS specialist review; reads `tca.md` and `apple-docs.md` when relevant |
| `plugins/aimate-ios/skills/review-ios/evals/evals.json` | 4 eval prompts (SwiftUI MVVM, search concurrency, legacy UIKit MVVM, TCA search) |
| `plugins/aimate-ios/skills/review-ios/evals/results.md` | Results for evals 1–3; eval 4 not run yet |

### `review-ios` design

- Adds deterministic iOS coverage without replacing generic review.
- Five steps: baseline from project evidence → trace changed behavior → apply engaged modules → classify (`security-violation` / `request-for-change` / `optional`) → return output.
- **Async four-question contract**: who owns the task, what cancels it, what prevents an older result replacing a newer one, how cancellation is distinguished from failure/empty success.
- **Output contract**: strict subset of the generic `aimate` `code-review` shape (`plugins/aimate/skills/code-review/SKILL.md`).

## 4. Verified Facts From This Session

- Xcode 26.6 `xcrun mcpbridge` (server `xcode-tools`) exposes 21 tools, including `BuildProject`, `GetBuildLog`, `RunSomeTests`, `RunAllTests`, `GetTestList`, `RenderPreview`, `XcodeRefreshCodeIssuesInFile`, `DocumentationSearch` (params `query`, `frameworks`), and file-write tools (`XcodeWrite`, `XcodeUpdate`, `XcodeMV`, `XcodeRM`, `XcodeMakeDir`). `DocumentationSearch` returned article text for a test query; no structured availability.
- `https://developer.apple.com/tutorials/data/documentation/<framework>/<symbol>.json` returns `metadata.platforms` with `introducedAt`, `deprecatedAt`, `message` (checked on `NavigationStack` and `NavigationView`).
- TCA DocC articles exist as Markdown under `Sources/ComposableArchitecture/Documentation.docc/Articles/` (MIT); Swift Package Index serves per-version DocC JSON; Sosumi `external/` proxies it as Markdown with links intact.

## 5. Open Items

1. ~~How `review-ios` gets invoked~~ — decided: only manually or through an `aimate-ios` block in the project's `AGENTS.md` (snippet in the plugin README; ideally in the company template). Generic `aimate` must never call it (tech lead: keep `aimate` generic; a Delphi developer does not need iOS behavior). Standalone runs on large changes review file by file.
2. ~~`ios-standards` description~~ — decided: reworded as internal, "not for direct use".
3. ~~Run eval 4 (TCA)~~ — done; both runs met the expected outcome, the skill run added version-verified evidence (see `results.md`).
4. **`swift-style.md`**: blocked on the user recovering their modified Ray Wenderlich/Kodeco Swift-style rules. Do not write it from memory.
5. Evals were run manually; raw outputs not persisted.
6. Template repository: its `AGENTS.md` should state the architecture (change in the template, not this plugin).

## 6. Next Steps

1. User reviews the uncommitted changes; commit only when asked.
3. Later capabilities (plan Task 6), each with its own RED-GREEN evaluation before authoring: `implement-ios`, `test-ios` (Xcode MCP / MobileBuildMCP), `build-swiftui` (re-evaluate `AvdLee/SwiftUI-Agent-Skill` vs `swiftui-pro`). Physical-device automation only after simulator behavior is reliable.

## 7. Working Preferences

- Go through decisions one item at a time; do not edit files until the user says so.
- Prefer native Apple tooling and company-owned references over third-party installs.
- The user approves design-level decisions explicitly and may skip detailed review of docs.
- Never commit unasked.
