# Aimate iOS V1 — Session Handoff

Date: 2026-10-15, last updated 2026-10-16 (end of day: five skills, all RED-GREEN evaluated on KNMI, NPO Start, Thuisarts) · Branch: `feature/ai-mate-ios-v0` · Repo: `Dawn-Technology/aicelerate`

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
7. **V1 exclusions**: signing, provisioning, certificates, archives, TestFlight, App Store Connect, release automation, incidental migrations, mandatory snapshot tests, physical-device automation (reconfirmed 2026-10-16: no XCUITest/device step yet).
8. **Pilot-first**: all five skills are read-only on source; no write-enabled skill yet.
9. **Do not commit** unless the user asks. The user cannot open a PR yet (missing repository rights).
10. **Every skill is RED-GREEN evaluated** on the three real projects before it is considered done: baseline without the skill, write the skill from the observed gaps, rerun with it, record both in `evals/results.md`.
11. **Company references over third-party skills**: security and localization rules are company-owned text in `ios-standards/references/`, shared by the matching audit skill and the `review-ios` module.

### Provider decisions (2026-10-15 review)

| Provider | Decision |
| --- | --- |
| Xcode MCP (`xcrun mcpbridge`) | **First route** for build, test, diagnostics, previews, `DocumentationSearch`. Read-only skills never use its write tools. |
| `getsentry/MobileBuildMCP` | Kept, optional, second build/test route and the UI automation route for `drive-ios`. Disable telemetry with `MOBILEBUILDMCP_SENTRY_DISABLED=true`; the MCP server needs `MOBILEBUILDMCP_ENABLED_WORKFLOWS=simulator,ui-automation,debugging` (default registers only 24 tools without UI automation). |
| `dpearson2699/swift-ios-skills` (`swift-security`) | Rejected 2026-10-16: PolyForm Perimeter 1.0.0 (non-OSI, noncompete) although its frontmatter says MIT; replaced by company `security.md`. Do not copy its content. |
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

- Commits: `09da24c ai-mate-ios: WIP` (original plugin, spec, plan, README, marketplace) and `74d9574 ai-mate-ios: Added and update skills and references` (provider review and this handoff).
- **Everything from 2026-10-16 is uncommitted**: the real-project fixes to `review-ios` and the references, `security.md`, `localization.md`, the four new skills with their evals, README, capability docs, and this handoff. `claude plugin validate plugins/aimate-ios` passes.

### Skills

| Skill | What it does | Writes source | Evals |
| --- | --- | --- | --- |
| `review-ios` | Specialist review of a change; modules include Security and Localization; verifies with build and affected tests | no | evals 1–6 (5–6 security) |
| `test-ios` | Runs affected, named, plan, or full-suite tests on a simulator; builds instead when no test covers the change; reruns failures once to detect flaky tests | no | 3 real projects |
| `security-audit-ios` | Whole-project static security audit over every `security.md` area, per target, CI separate | no | 3 real projects |
| `drive-ios` | Operates the app on a simulator: `reproduce`, `validate`, `capture`; described steps always through the UI; stops when UI automation is unavailable | no | 3 real projects + eval 4 (not yet run) |
| `localization-audit-ios` | Whole-project static localization audit: supported languages, scripted inventory, exact key-to-bundle matching | no | 3 real projects |
| `ios-standards` | Internal references: precedence, architecture, tca, apple-docs, tooling, testing, legacy-projects, capability-providers, security, localization | — | — |

All audit and review skills return the `review-ios` YAML shape (section "6. Return Compatible Output").

### Files

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
| `…/ios-standards/references/tooling.md` | Native-first order; build/test order (Xcode MCP → MobileBuildMCP → `xcodebuild`/`simctl` → static); `XcodeListWindows` project check; MobileBuildMCP usage (`session_set_defaults` + `test_sim` with `-only-testing`) and storage note; DerivedData reuse; exact capability states |
| `…/ios-standards/references/{precedence,legacy-projects,testing,capability-providers}.md` | Precedence, legacy rules, testing policy, optional providers |
| `plugins/aimate-ios/skills/review-ios/SKILL.md` | iOS specialist review (no source edits); runs only manually or via project instructions |
| `…/ios-standards/references/security.md` | Company security checks and severities (secrets, Keychain, biometrics, client-only enforcement, app lock, logging, transport, crypto, deep links, web content, server-supplied content, analytics, debug features, data at rest, privacy manifests, dependencies and CI) |
| `…/ios-standards/references/localization.md` | Supported-language rules, severities, and checks (completeness, key-to-bundle matching, text outside localization, wrong-language values, plurals, formatting, Info.plist, extensions, hygiene) |
| `plugins/aimate-ios/skills/review-ios/evals/` | 6 eval prompts and results |
| `plugins/aimate-ios/skills/{test-ios,security-audit-ios,drive-ios,localization-audit-ios}/` | `SKILL.md` plus `evals/evals.json` and `evals/results.md` each |

### `review-ios` design

- Adds deterministic iOS coverage without replacing generic review.
- Always reads `precedence.md`, `architecture.md`, `tooling.md`; other references only when relevant. A failed read is retried, then named in `residual_gaps`.
- **Project instructions** = `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md` (rank 2 in `precedence.md`, equal weight; contradictions reported, more specific wins). Baseline checks all locations with a file listing, reads what exists, and reports disagreements with project files and the machine (paths, Xcode versions, simulators). "No project instructions; baseline inferred from project evidence" only when none exist.
- Project skills: `.agents/skills/`, `.claude/skills/`, `skills-lock.json` checked with a file listing; each reported as used or not, and why.
- `chat` output opens with `Baseline` and `Verification` sections, then findings with exact severity labels.
- Six steps: baseline → trace changed behavior → apply engaged modules → **verify** (build + affected tests by default, unless "static only"; names scheme, test plan, destination) → classify → return output.
- `residual_gaps` starts with the baseline and every build/test route with its exact state, for every output target including `chat`. A route not attempted is "not run", never `unavailable`.
- Framework-behavior claims cite docs or source at the resolved version, or are marked unverified.
- Problems outside the diff that the change does not introduce or make reachable are at most `optional`, with a follow-up ticket.
- **Async four-question contract**: who owns the task, what cancels it, what prevents an older result replacing a newer one, how cancellation is distinguished from failure/empty success.
- **Output contract**: strict subset of the generic `aimate` `code-review` shape (`plugins/aimate/skills/code-review/SKILL.md`).

## 4. Verified Facts From This Session

- Xcode 26.6 `xcrun mcpbridge` (server `xcode-tools`) exposes 21 tools, including `BuildProject`, `GetBuildLog`, `RunSomeTests`, `RunAllTests`, `GetTestList`, `RenderPreview`, `XcodeRefreshCodeIssuesInFile`, `DocumentationSearch` (params `query`, `frameworks`), and file-write tools (`XcodeWrite`, `XcodeUpdate`, `XcodeMV`, `XcodeRM`, `XcodeMakeDir`). `DocumentationSearch` returned article text for a test query; no structured availability.
- `https://developer.apple.com/tutorials/data/documentation/<framework>/<symbol>.json` returns `metadata.platforms` with `introducedAt`, `deprecatedAt`, `message` (checked on `NavigationStack` and `NavigationView`).
- TCA DocC articles exist as Markdown under `Sources/ComposableArchitecture/Documentation.docc/Articles/` (MIT); Swift Package Index serves per-version DocC JSON; Sosumi `external/` proxies it as Markdown with links intact.

### Real-project testing (KNMI, commit `8569aaeb`, no `AGENTS.md`, TCA 1.23.2, iOS 15)

Run headless with `claude -p … --plugin-dir plugins/aimate-ios --plugin-dir plugins/aimate`, read-only tool allowlists.

- Plain "Review commit …" does **not** load `review-ios` (as intended).
- `review-ios` states the missing `AGENTS.md`, infers the baseline (incl. mixed XCTest/Swift Testing), picks the TCA checkout via `git describe --tags`, and cited `PresentationReducer.swift` at 1.23.2 (depth varies per run; one run marked it unverified instead).
- **Xcode MCP route**: picked the KNMI window among two open projects; build succeeded; `RunSomeTests` returned "No result" (Xcode run destination left on default, not a simulator) → fell back to `xcodebuild`, tests passed.
- **MobileBuildMCP route** (2.7.1, telemetry off): `session_set_defaults` with app scheme `KNMI (iOS)` + simulator, `test_sim` with `-only-testing` → 6 passed. First run is a full build (~13 min); its own cache reached ~18 GB (purged).
- Xcode asks the user to allow each new agent connection; a session started before "Allow" sees 0 Xcode tools.
- MobileBuildMCP purge: `--delete` needs `--workspace-key` and `--confirm delete-mobilebuildmcp-storage`; `--classes all` keeps DerivedData.

### Real-project testing (NPO Start, commit `08fb03293c`, `AGENTS.md` present, MVVM-C, iOS 16.6)

- Follows the `AGENTS.md` `xcodebuild` route (scheme `NPO Start`, test plan `NPOStart-iOS-UnitTests-Snapshots`) before Xcode MCP / MobileBuildMCP; 8 tests passed.
- Reports `AGENTS.md` mismatches: missing "NPO Start iPhone 17 Pro" simulator, `Xcode_26.2.app` path, deployment targets 16.6 vs 16.4/15.0, a target group on Swift 5.0.
- Found a real `request-for-change` (Downloads ↔ Plus navigation loop), noticed a later `develop` commit fixes another finding, flagged an `opacity(0)` button still tappable/VoiceOver-reachable as `optional`.
- MobileBuildMCP fails on private SSH packages ("Repository not found") in its own workspace → falls back.
- Pre-existing test failure outside the diff (`didSelect_shouldInvokeChoice`, flaky in full suite) correctly kept out of findings.
- Side finding for the NPO team: `.agents/skills/*` are broken symlinks (`submodules/…` relative to `.agents/skills/`, submodules not checked out), so those skills load nowhere.

### Real-project testing (Thuisarts, branch `bugfix/TAA-0002-broken-searchbar`, only `.github/copilot-instructions.md`, TCA, no tests)

- First run ignored `copilot-instructions.md` → fixed by the "project instructions" definition.
- Rerun read it, used its `xcodebuild -scheme "Thuisarts - Debug"` command first (BUILD SUCCEEDED, 2.3 min), reported "no test targets" from the instructions, applied its "verify on iPhone and iPad" rule, and found a stale `SharedLibrary/Package.resolved` (TCA 1.25.5 vs documented pin `1.26.0..<1.26.2`).
- Earlier run (Xcode open on Thuisarts): Xcode MCP `XcodeListWindows` picked the right window among three projects, `BuildProject` succeeded in 49 s.

### Coverage so far

| Situation / route | Status |
| --- | --- |
| No project instructions (KNMI) / `AGENTS.md` (NPO) / only Copilot instructions (Thuisarts) | works |
| Project-selected route, `xcodebuild` fallback, MobileBuildMCP, Xcode MCP build | works |
| Xcode MCP **tests** (`RunSomeTests`) | not yet confirmed: needs a simulator selected as run destination in Xcode |
| TCA (KNMI, Thuisarts), MVVM-C (NPO) | works |
| `drive-ios` through the `mobilebuildmcp` CLI | works (all eval runs); through MCP tools with UI automation enabled: not yet tested |

### Lessons from 2026-10-16 evaluations

- Baselines without skills find real issues; the skills mainly add discipline: project instructions first, fixed area coverage, reachability before severity, company labels, shared output shape, and clean-up.
- Fresh DerivedData per run is slow, leaves many GB, and fails on private SSH packages; `tooling.md` now requires reusing the existing DerivedData, `-skipPackageUpdates -disableAutomaticPackageResolution` when packages are untouched, unique `mktemp -d` folders, deleting only own folders, and `-collect-test-diagnostics never`.
- A subagent instruction "read nothing else in aicelerate" blocked reading `review-ios` for the output shape; skills now link the section and require reading it.
- `drive-ios` must never take irreversible simulator actions (keychain reset, erase) on a simulator it did not create without asking; prefer a temporary simulator.
- Real findings for the client projects (security, localization, flaky tests, broken symlinks) exist only in the session's eval outputs; they were not saved or shared.

## 5. Open Items

1. ~~How `review-ios` gets invoked~~ — decided: only manually or through an `aimate-ios` block in the project's `AGENTS.md` (snippet in the plugin README; ideally in the company template). Generic `aimate` must never call it (tech lead: keep `aimate` generic; a Delphi developer does not need iOS behavior). Standalone runs on large changes review file by file.
2. ~~`ios-standards` description~~ — decided: reworded as internal, "not for direct use".
3. ~~Run eval 4 (TCA)~~ — done; both runs met the expected outcome, the skill run added version-verified evidence (see `results.md`).
4. **`swift-style.md`**: blocked on the user recovering their modified Ray Wenderlich/Kodeco Swift-style rules. Do not write it from memory.
5. Evals were run manually; raw outputs not persisted.
6. Template repository: its `AGENTS.md` should state the architecture (change in the template, not this plugin).
7. Confirm Xcode MCP tests: select a simulator destination in Xcode for the project, then rerun a review.
8. Untested: the README's MobileBuildMCP delete command with `derivedData` in `--classes`.
9. **Security (2026-10-16)**: added company `ios-standards/references/security.md` (own text, Apple sources), a Security module in `review-ios`, and evals 5–6 (RED-GREEN recorded in `results.md`). `dpearson2699/swift-ios-skills` `swift-security` was **rejected** by the user (PolyForm Perimeter 1.0.0, non-OSI, although its frontmatter says MIT); recorded under Rejected in `capability-matrix.md`. Do not copy its content.
10. **`test-ios` (2026-10-16)**: added (simulator only, never edits source). RED-GREEN on KNMI, NPO Start, and Thuisarts recorded in `test-ios/evals/results.md`; `tooling.md` gained DerivedData, package-flag, result-bundle, and `-collect-test-diagnostics never` rules (shared with `review-ios`). Not yet covered: Xcode MCP/MobileBuildMCP routes, `-only-testing` on covered changes, a confirmed failure. Side finding for NPO: `.github/copilot-instructions.md` is a broken symlink.
11. **`security-audit-ios` (2026-10-16)**: added (user chose the name). Read-only whole-project audit over every `security.md` area, `review-ios` YAML output. RED-GREEN on the three projects recorded in `security-audit-ios/evals/results.md`; `security.md` gained seven areas from the baselines (client-only enforcement, app lock, server-supplied content, analytics, debug features, per-target privacy manifests, dependencies and CI). The YAML-shape fix was verified only on NPO. Real findings per project are in the eval runs, not shared with the teams yet.
12. **`drive-ios` (2026-10-16)**: added (user chose the name over `reproduce-ios`/`explore-ios`, so it can later also serve demos). Goals `reproduce`, `validate`, `capture`; never edits source. RED-GREEN on Thuisarts, KNMI, NPO in `drive-ios/evals/results.md`. Post-eval rules not re-evaluated: temporary simulator for fresh state, ask before keychain reset or erase, let carousels settle. Manual user test in OpenCode: the MCP server lacked UI tools and the agent used a deep link instead of the described steps → skill now performs described steps through the UI only and stops with what to enable; README documents `MOBILEBUILDMCP_ENABLED_WORKFLOWS`. Eval 4 covers this; not yet run.
13. **`localization-audit-ios` (2026-10-16)**: added (user chose static-only scope and the name). Company reference `localization.md` also feeds a Localization module in `review-ios`. RED-GREEN on the three projects in `localization-audit-ios/evals/results.md`; no changes needed after evaluation.
14. **Deferred by the user**: XCUITest generation and physical-device runs (MobileBuildMCP 2.7.1 supports devices only for build, install, launch, stop, and tests; UI automation, screenshots, and LLDB attach are simulator-only), live client demos with `drive-ios`, and a visual localization pass (per language, pseudo-languages, truncation).
15. **Local setup on the user's machine**: OpenCode global config `~/.config/opencode/opencode.json` has Xcode MCP; its `skills.paths` points to a clone at `~/.config/opencode/plugins/aicelerate` on `main`, which lacks `aimate-ios`. To test uncommitted work, add `/Users/alex-egeniq/Documents/git/aicelerate/plugins/aimate-ios/skills` and a `mobilebuildmcp` MCP entry with the workflows variable (snippets in the plugin README). Not changed by the agent; the user decides. Claude Code: `claude --plugin-dir ~/Documents/git/aicelerate/plugins/aimate-ios` in the project directory; no Xcode or MobileBuildMCP MCP configured yet.
16. **Disk**: MobileBuildMCP's KNMI workspace (`~/Library/Developer/MobileBuildMCP/workspaces/knmi-app-ios-…`, 5.4 GB) was left for the user to purge.

## 6. Next Steps

1. **User tests the skills hands-on** in OpenCode or Claude Code (setup in item 15). First check: rerun the "open Thuisarts, type 'hoofdpijn', open the article" flow with and without UI automation enabled (`drive-ios` eval 4). Then `test-ios` with Xcode open and a simulator destination (Xcode MCP route, open item 7). Adjust skills from the user's feedback.
2. Review the uncommitted changes with the user; commit only when asked (end commit messages with the attribution line from the session instructions). PR still blocked on repository rights.
3. Decide whether to save the client findings (security, localization) as local reports outside the repo for the teams; ask first, they are sensitive.
4. Optionally re-run the KNMI and Thuisarts `security-audit-ios` evals to confirm the YAML-shape fix, and re-run `drive-ios` evals after the post-eval rule changes.
5. Later capabilities, each with RED-GREEN evaluation first: `implement-ios` (first write-enabled skill), `build-swiftui` (re-evaluate `AvdLee/SwiftUI-Agent-Skill` vs `swiftui-pro`), then the deferred items in open item 14. `swift-style.md` stays blocked (open item 4).
6. Update the plan's Task 6 checkboxes (`docs/superpowers/plans/2026-10-15-aimate-ios-v1.md`) to reflect the skills added.

## 7. Working Preferences

- Go through decisions one item at a time; do not edit files until the user says so.
- Prefer native Apple tooling and company-owned references over third-party installs.
- The user approves design-level decisions explicitly and may skip detailed review of docs.
- Never commit unasked.
- The user chooses skill names; offer a short table of options with a recommendation.
- Keep skills goal-neutral where future uses are likely (for example `drive-ios` for QA, validation, screenshots, and later demos).
- When a capability is missing, the agent must stop and say what to enable instead of finding a workaround that changes what the user asked to test.
- Prefer the smallest first version (for example static-only localization) and defer extensions explicitly.
- Do not change the user's global agent configuration; show the snippet and let the user apply it.
