# Aimate iOS Design

## Purpose

Add a separately installable `aimate-ios` plugin for native iOS teams without making the generic `aimate` plugin Apple-specific. The iOS plugin supplies company policy and composes existing specialist skills and tools wherever those are suitable.

## Principles

1. `aimate` remains provider- and platform-neutral.
2. External capabilities are preferred over company-owned copies, but remain optional.
3. `aimate-ios` works without optional integrations and reports reduced verification honestly.
4. Project instructions and demonstrable repository constraints outrank company defaults.
5. Architecture is selected by required qualities, not by mandating TCA or MVVM.
6. Existing applications are not migrated incidentally.
7. Workflows use portable `SKILL.md` files and thin host-specific tooling guidance.

## Distribution

`aimate-ios` is a second plugin in the `aicelerate` marketplace. iOS teams install it alongside `aimate`; Delphi and other teams install only what they need. Android can add an independently owned plugin later. A shared mobile layer should be extracted only after stable duplication exists.

OpenCode, Claude Code, Codex, and GitHub Copilot are V1 compatibility targets. The portable skill format is the common layer. Marketplace installation may differ by host; OpenCode can load the skill directory through `skills.paths` or a standard external skill directory.

## Capability Resolution

For every capability:

1. Honor an explicit user-selected tool or skill.
2. Use an accepted external skill already available.
3. Use native host or Xcode capability.
4. Apply the smaller company-owned fallback.
5. Fall back to static inspection and name outstanding verification.

External skills are never hard dependencies. Each capability reports `available`, `fallback`, `unavailable`, or `not-required`.

## Policy Precedence

1. Current user instruction.
2. `AGENTS.md`, accepted ADRs, and project-local skills.
3. Xcode project, workspace, package, deployment-target, and toolchain constraints.
4. Strong repository evidence.
5. Company iOS policy.
6. General Apple guidance.

When company policy is not followed, report the policy, evidence for the deviation, and whether a safe incremental alignment exists. Do not silently redesign an application.

## Architecture

The standard values clear state and side-effect ownership, explicit dependencies, testable business logic, predictable navigation, structured concurrency, cancellation, and cohesive units. TCA, MVVM, UIKit patterns, and native SwiftUI state are possible implementations.

New work selects the smallest architecture that satisfies the feature. Existing work follows the repository unless a migration is explicitly scoped or a concrete defect requires a local correction.

## Planned Skills

- `review-ios`: specialist, read-only review. This is the V1 pilot.
- `implement-ios`: Swift/iOS implementation and refactoring after review policy is validated.
- `test-ios`: simulator-first build, XCTest, Swift Testing, XCUITest, screenshots, and best-effort physical-device automation.
- `build-swiftui`: tool-neutral visual design to adaptive, accessible SwiftUI with progressive visual validation.

The names describe desired capabilities, not an obligation to own all implementation. An accepted external skill may satisfy most of a capability while `aimate-ios` keeps only company policy and composition.

## Testing Policy

- Prefer Swift Testing for supported new unit and integration tests.
- Continue XCTest in existing suites unless migration directly benefits the scoped change.
- Use XCUITest for UI automation.
- Follow established legacy-project conventions.
- Keep migrations explicit and separate.

Behavioral naming uses subject, condition, and expected observable behavior:

```swift
func test_loadProfile_withValidResponse_shouldReturnProfile() async throws

@Test("loadProfile with a valid response returns the profile")
func loadProfileWithValidResponseReturnsProfile() async throws
```

Use Arrange-Act-Assert structure; comments are optional when the phases are obvious. Add `async` and `throws` only when required.

## Automation Boundary

Simulator automation is a required target. Physical-device automation is best effort and requires connection, trust, Developer Mode, existing signing, and suitable tooling. Skills never manage signing identities, provisioning, credentials, trust, passcodes, biometrics, or device-management controls.

Verification distinguishes `simulator-verified`, `device-verified`, and `device-not-run: <reason>`.

## V1 Exclusions

Signing changes, certificate/profile management, archives, TestFlight, App Store Connect, release automation, automatic architecture migrations, and mandatory snapshot-test dependencies are excluded.

## Governance

Adopt external work directly where possible. Prefer composition over wrappers, upstream contributions over forks, and forks only for abandoned business-critical capabilities. Record source, version, license, supported hosts, selection reason, and fallback in the capability matrix. Re-evaluate on failure or relevant Swift/Xcode upgrades rather than on an arbitrary schedule.

The Swift style standard remains intentionally incomplete until the earlier Ray Wenderlich/Kodeco-derived rules and company modifications are recovered and reviewed against current Swift guidance.
