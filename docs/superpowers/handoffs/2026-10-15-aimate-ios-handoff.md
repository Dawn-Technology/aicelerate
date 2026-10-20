# Aimate iOS V1 — Session Handoff

Date: 2026-10-15, last updated 2026-10-20 (nine user-facing skills; two write-enabled skills in evaluation) · Branch: `feature/ai-mate-ios-v0` · Repo: `Dawn-Technology/aicelerate`

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
5. **Testing standard**: Swift Testing for new unit tests; existing XCTest suites continue; XCUITest for UI; naming `test_<subject>_with<Condition>_should<Expectation>()` for XCTest and Swift Testing alike, with a readable `@Test("…")` display name for Swift Testing (user decision 2026-10-19; replaces lower-camel-case Swift Testing names); no raw-identifier names unless the project already uses them; AAA structure; minimal `async`/`throws`.
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

- Commits on `feature/ai-mate-ios-v0` (all by the user; pushed state not checked): `09da24c` (plugin, spec, plan), `74d9574` (provider review, handoff), `8941128` (security audit, test-ios, drive-ios), `1bfe11e` (drive-ios, localization audit), `c0bb015` (testing tweaks, tooling, summarize-project-ios), `ed7870f` (WIP: review-architecture-ios and related changes).
- **Uncommitted (2026-10-20)**: `raise-minimum-ios` (new), the rename of `localization-audit-ios` to `fix-localization-ios` with its fix phase and `scripts/xcstrings.py`, updated references in `summarize-project-ios` and `review-architecture-ios`, README, and this handoff. `claude plugin validate plugins/aimate-ios` passes.
- **Evaluation clones** with the NPO `raise-minimum-ios` and Thuisarts `fix-localization-ios` results are in `scratchpad/raise/` of session `3f0842c9-ffde-4fc1-9cbf-74caf636f96c` (temporary); both runs are recorded in the skills' `evals/results.md`. If the scratchpad is gone, rerun from fresh clones as described in the skills' `evals/`.

### Skills

| Skill | What it does | Writes source | Evals |
| --- | --- | --- | --- |
| `review-ios` | Specialist review of a change; modules include Security and Localization; verifies with build and affected tests | no | evals 1–6 (5–6 security) |
| `test-ios` | Runs affected, named, plan, or full-suite tests on a simulator; builds instead when no test covers the change; reruns failures once to detect flaky tests | no | 3 real projects |
| `security-audit-ios` | Whole-project static security audit over every `security.md` area, per target, CI separate | no | 3 real projects |
| `drive-ios` | Operates the app on a simulator: `reproduce`, `validate`, `capture`; described steps always through the UI; stops when UI automation is unavailable | no (simulator only) | 3 real projects + eval 4 (not yet run) |
| `summarize-project-ios` | Onboarding and assessment summary: structure, getting it running, gotchas, hotspots, risks | no | 3 real projects |
| `review-architecture-ios` | Companion of `aimate`'s `review-architecture`: Swift module graph, iOS platform health, TCA/MVVM-C rules; report in `docs/` | report file only | 3 real projects |
| `fix-localization-ios` (was `localization-audit-ios`) | Scan, fix plan with before/after text, approval, fixes on a new branch; translations marked `needs_review` | yes, after approval | scan: 3 real projects; plan and fix: Thuisarts |
| `raise-minimum-ios` | Scan, plan, confirmation, then raise the iOS minimum and remove dead availability code and backports on a new branch | yes, after confirmation | RED: Thuisarts, KNMI; plan: 3 projects; execution: NPO |
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
13. **`localization-audit-ios`, renamed `fix-localization-ios` on 2026-10-20 (2026-10-16)**: added (user chose static-only scope and the name). Company reference `localization.md` also feeds a Localization module in `review-ios`. RED-GREEN on the three projects in `localization-audit-ios/evals/results.md`; no changes needed after evaluation.
14. **Deferred by the user**: XCUITest generation and physical-device runs (MobileBuildMCP 2.7.1 supports devices only for build, install, launch, stop, and tests; UI automation, screenshots, and LLDB attach are simulator-only), live client demos with `drive-ios`, and a visual localization pass (per language, pseudo-languages, truncation).
15. **Local setup on the user's machine**: OpenCode global config `~/.config/opencode/opencode.json` has Xcode MCP; its `skills.paths` points to a clone at `~/.config/opencode/plugins/aicelerate` on `main`, which lacks `aimate-ios`. To test uncommitted work, add `/Users/alex-egeniq/Documents/git/aicelerate/plugins/aimate-ios/skills` and a `mobilebuildmcp` MCP entry with the workflows variable (snippets in the plugin README). Not changed by the agent; the user decides. Claude Code: `claude --plugin-dir ~/Documents/git/aicelerate/plugins/aimate-ios` in the project directory; no Xcode or MobileBuildMCP MCP configured yet.
16. **Disk**: MobileBuildMCP's KNMI workspace (`~/Library/Developer/MobileBuildMCP/workspaces/knmi-app-ios-…`, 5.4 GB) was left for the user to purge.
17. **2026-10-19/20 additions** (uncommitted): `tooling.md` reports the MobileBuildMCP workspace size after runs and reminds above 10 GB (user chose 10 GB). `summarize-project-ios` (user's name; both audiences, static, chat only) with evals and results. `testing.md` naming: XCTest and Swift Testing both use `test_<subject>_with<Condition>_should<Expectation>` (user decision); resolved 2026-10-20 with the user: always the three phase comments `// Arrange`, `// Act`, `// Assert` and nothing else; `async`/`throws` only when needed; placeholder `<subject>` in lowerCamel; examples labeled Swift Testing, XCTest, XCUITest; new sections for test types and files, parameterized tests, and UI tests (accessibility identifiers). `review-architecture-ios` (user's name; companion of `aimate`'s `review-architecture`, report file in `docs/`) with `scripts/swift_modules.py`, `scripts/ios_platform.py`, `references/ios-design-rules.md`, evals and results.
18. **OpenCode failure analysis (2026-10-19)**: the user's `summarize-project-ios` run in OpenCode used `glm-5.3-flash` (`opencode-go`); it followed the skill through steps 1–2, then produced invented text after about 57k input tokens and wrote nothing. The user reran it with a stronger model and it works as expected (2026-10-20); the cause was the model, not the skill.
19. **Overlap with `aimate`**: `aimate` has `review-architecture` (now with an iOS companion) and `asvs-audit` (security audit, overlaps `security-audit-ios`). Decide whether `security-audit-ios` should reference `asvs-audit`.
20. **Python for scripts (2026-10-20)**: user chose option A: run all scripts with `xcrun python3` (Xcode's Python 3.9.6), keep them 3.9-compatible, and check that in the evals. Rejected for now: rewriting the scripts in Swift (option B), worth reconsidering if the iOS team wants to maintain them.
21. **Verdict wording (2026-10-20)**: the user read "Broken" as "the app does not work". Decision A: keep `aimate`'s Healthy/Strained/Broken scale for comparability, and `review-architecture-ios` now adds one sentence after the verdict saying it rates how safely the code can be changed, not whether the app works. Suggesting clearer words to the owner of `aimate`'s `review-architecture` was not chosen.
22. **`raise-minimum-ios` (2026-10-20, in progress)**: user's name; scan → plan → developer confirmation → execute on a new branch without committing (user's design). Scope: cleanup plus report; modernizations not required by the old minimum are follow-ups. `scripts/availability.py` classifies availability checks against new minimums. RED baselines (Opus, scratchpad clones under `scratchpad/raise/`) for Thuisarts and KNMI showed: no branch created, Perception to Observation is forced by the build at iOS 17+, new deprecation warnings fixed; NPO baseline stopped by the user. GREEN plan phase (Sonnet) done for all three. The user chose to execute NPO only (all steps; keep the tvOS-shared scroll-geometry wrapper; leave the inert IPHONEOS 15.0 on TV targets; raise Preview to 18.0; no commits); done: 52 files on `chore/ios-18-minimum` in the NPO clone, iOS and tvOS builds and unit tests pass before and after, snapshot plan unverified; results in `evals/results.md`. Afterwards the skill requires baseline test runs and clean-build warning comparison. KNMI raised a real multi-platform issue (macOS/tvOS/watchOS apps share the package at old minimums, so Observation and NavigationStack cannot replace the backports there without splits). Applied after the plan runs: count only targets that build for iOS, list only confirmed deprecations, propose and confirm the base branch, and open the plan with a short summary of at most about ten lines (also added to `fix-localization-ios` at the user's request).
23. **`fix-localization-ios` (2026-10-20)**: `localization-audit-ios` extended and renamed by the user: scan, fix plan per category with before/after text, approval, fixes on a new branch (no commits), agent translations marked `needs_review`, String Catalogs edited only through `scripts/xcstrings.py` (lossless on all 52 catalogs). References in other skills, README, and evals updated. Plan phase evaluated on Thuisarts (Sonnet); the user answered: Dutch-only, add InfoPlist.xcstrings, rename the misnamed "Privacy Policy" key to "Terms of use", formal "u" to "je"; fix phase done (28 files on `chore/fix-localization` in the Thuisarts clone, Swift compiles, catalogs round-trip, results in `evals/results.md`; `xcstrings.py delete` added afterwards). Dropping `en` from `knownRegions` is a follow-up decision.
24. **Subagent model (2026-10-20)**: user asked to use cheaper models first (saved as a memory): Sonnet for evals and builds, Haiku for lookups, Opus only when they fall short.


## 6. Next Steps

1. **Review the two write-skill results with the user** (open items 22 and 23, recorded in `evals/results.md`): the user can inspect the clones' diffs. Snapshot tests remain unverified for NPO.
2. **User hands-on testing**: the user already ran `summarize-project-ios` (works with a capable model) and `review-architecture-ios` (works; verdict wording changed). Still open: `drive-ios` eval 4 with and without UI automation, `test-ios` through Xcode MCP (open item 7).
3. Commit the uncommitted work when the user asks (end messages with the session's attribution line). PR still blocked on repository rights.
4. Decide whether to save the client findings (security, localization, architecture) as local reports for the teams; ask first, they are sensitive.
5. Optional re-runs after rule changes: `security-audit-ios` (KNMI, Thuisarts YAML shape), `drive-ios` post-eval rules, `summarize-project-ios` (no names), `review-architecture-ios` full run after the script and wording fixes.
6. Decide whether `security-audit-ios` should reference `aimate`'s `asvs-audit` (open item 19).
7. Later capabilities, each with RED-GREEN evaluation first: `implement-ios`, `build-swiftui`, then the deferred items in open item 14. `swift-style.md` stays blocked (open item 4).
8. Update the plan's Task 6 checkboxes (`docs/superpowers/plans/2026-10-15-aimate-ios-v1.md`).

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
- Subagents start on a cheaper model (Sonnet; Haiku for lookups) and escalate to Opus only when they fall short; record the model in eval results.
- Skills that change source use scan, then a plan that opens with a short summary (at most about ten lines), then explicit developer confirmation, then work on a new branch from a confirmed base branch, never committing.
- Evaluate write-enabled skills on local clones in the scratchpad, never in the user's checkouts; copy gitignored build inputs (KMP framework, xcconfigs) and downloaded packages with `cp -c`.
