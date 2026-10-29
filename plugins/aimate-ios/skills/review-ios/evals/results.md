# Review iOS Evaluation Results

Evaluated 2026-10-15 in OpenCode using `github-copilot/gpt-5.6-sol` subagents. Optional iOS specialists and executable Xcode routes were explicitly unavailable in every prompt.

## Reproduce

1. Read each prompt and expected outcome from `evals.json`.
2. Start a fresh general-purpose agent for each prompt without loading `review-ios`; save its findings as the baseline.
3. Start another fresh agent for each prompt and instruct it to load `../SKILL.md` and follow it exactly; save the full structured output.
4. Check the result against the expected outcome and these shared criteria: project baseline stated, unavailable execution reported, concrete findings only, no unjustified migration, and all requested files reviewed.
5. For the concurrency case, additionally require distinct evaluation of task ownership, cancellation, stale-result prevention, and cancellation/failure/empty-success semantics.

The raw runs were session outputs rather than repository artifacts. The result summaries below record the observed differences; future automated evaluation should preserve raw outputs in an external benchmark workspace rather than growing the distributed plugin.

## SwiftUI MVVM

Baseline and skill runs both found incorrect `@ObservedObject` ownership, unordered repeated loads, and the icon-only accessibility label. Both preserved MVVM. The skill run additionally recorded unavailable build, simulator, VoiceOver, and device verification in a structured baseline.

## Search Concurrency

The baseline found stale-result ordering, task lifetime, and collapsed failure/cancellation semantics. The first skill run found ordering but omitted the distinct failure/cancellation behavior. The skill was tightened to require four answers for every asynchronous operation: task owner, cancellation, stale-result prevention, and separation of cancellation/failure/empty success. The repeated run found all required behaviors and correctly noted that `@MainActor` prevents a direct data race but not stale ordering.

## Legacy UIKit MVVM

Baseline and skill runs found the missing load/render integration. Both retained UIKit, MVVM, and XCTest because migration was explicitly outside scope. The skill run captured the project baseline and unexecuted verification.

## TCA Search

Evaluated 2026-10-15 in Claude Code using general-purpose subagents; optional specialists, Xcode routes, and a local package checkout were unavailable.

Baseline and skill runs both found the missing cancellation ID with stale-response overwrite, the directly used `SearchClient.live` instead of `@Dependency`, and the unhandled error thrown in `.run`. Both kept TCA. The baseline could not confirm that TCA 1.23.1 exists and added style and product suggestions (naming, loading state, formatting). The skill run recorded the 1.23.1 baseline, read the documentation and `Effect.swift` at the 1.23.1 tag on GitHub, quoted the version's actual unhandled-error message, answered the four asynchronous questions, reported every unavailable capability route, and limited findings to reachable defects.

## Security: Obvious Secrets (eval 5)

Evaluated 2026-10-16 in Claude Code using general-purpose subagents; Xcode routes and optional specialists were unavailable.

Before `security.md` existed, baseline and skill runs both reported the tokens in `UserDefaults`, the token logged with `privacy: .public`, the Boolean-only biometric gate, and the app-wide `NSAllowsArbitraryLoads`, so this eval does not distinguish the reference. It stays as a regression check. With `security.md`, the skill run kept all three `security-violation` findings, classified the ATS exception as `request-for-change` because no exposure was shown, proposed a staging-only `NSExceptionDomains` entry, and cited `security.md`.

## Security: Web Bridge and Keychain (eval 6)

Evaluated 2026-10-16 under the same conditions.

The baseline found the token theft through the unvalidated deep link and the unchecked `getToken` handler, the JavaScript interpolation, the retain cycle, and the Keychain write defects, but reported the redacted `Logger` email interpolation as a low/medium finding. The skill run without `security.md` found the same defects but reported the email log as `optional` (default redaction "unverified"), rated the missing Keychain accessibility class `optional`, and filed all security findings under "Privacy and platform".

With `security.md` and the Security module, the skill run reported the token handler and the unvalidated deep link as `security-violation`, the Keychain write (unchecked `OSStatus`, delete-then-add, no accessibility class) as `request-for-change`, listed the email log under "Not reported" citing Apple's default redaction, kept UIKit/MVC, and verified WebKit availability against Apple documentation JSON. It rated the JavaScript interpolation `optional` because typical tokens cannot break the literal.

## Outcome

The pilot adds deterministic scope, policy precedence, migration restraint, capability reporting, and a composable result contract. It intentionally does not duplicate generic Swift defect knowledge already demonstrated by baseline reviewers.
