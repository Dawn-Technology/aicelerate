---
name: review-ios
description: Use when the user explicitly asks for an iOS review, or when the project's instructions (such as AGENTS.md) route Swift or Xcode reviews to review-ios. Runs aimate's review of a pull request or local changes with iOS depth added to it, covering SwiftUI, UIKit, concurrency, lifecycle, accessibility, TCA, MVVM + Coordinators, XCTest, XCUITest, Swift Testing, deployment targets, and Apple-platform API compatibility. Requires the aimate plugin.
metadata:
  author: "Dawn Technology"
  version: 0.2.0
  role: "ios-review-layer"
  requires: "aimate (review-pr, review-local, code-review)"
---

# iOS Review

## Purpose

Review an iOS change with `aimate`'s review skills and add Apple-platform depth to that same review. This skill is a layer, not a separate reviewer: `aimate`'s `review-pr` (for a pull or merge request) or `review-local` (for local changes, commits, or files) does the review through `code-review`, which owns the review method, severities, output format, and posting of comments. This skill adds what only an iOS review needs: the iOS baseline, the iOS checks per module, `ios-standards`, and a build and test run through Xcode. It never edits code.

## Requires aimate

Before anything else, check that the entry skill you will use (step 1) and `aimate`'s `code-review` are available in the host's skill list: in Claude Code as `aimate:review-pr` or `aimate:review-local` and `aimate:code-review`; in hosts that load skills by bare name (GitHub Copilot, OpenCode) as `review-pr` or `review-local` and `code-review`. Only check here; load and run the entry skill in step 5, after the iOS context is ready. If they are not available, stop and say: "review-ios is a layer on top of the aimate plugin; install aimate from the same marketplace and run the review again." Do not review without it.

## Policy

Always read these shared references before reviewing:

- [`../ios-standards/references/precedence.md`](../ios-standards/references/precedence.md)
- [`../ios-standards/references/architecture.md`](../ios-standards/references/architecture.md)
- [`../ios-standards/references/tooling.md`](../ios-standards/references/tooling.md)

Read these when the change or project involves them:

- [`../ios-standards/references/tca.md`](../ios-standards/references/tca.md) when the change touches reducers, stores, or other TCA code;
- [`../ios-standards/references/testing.md`](../ios-standards/references/testing.md) when the change adds or changes tests;
- [`../ios-standards/references/legacy-projects.md`](../ios-standards/references/legacy-projects.md) when the project uses an older or mixed architecture, UI framework, or test framework;
- [`../ios-standards/references/security.md`](../ios-standards/references/security.md) when the change touches secrets, authentication, biometrics, cryptography, networking configuration, logging, deep links, web content, file storage, analytics, entitlements, the privacy manifest, or CI;
- [`../ios-standards/references/accessibility.md`](../ios-standards/references/accessibility.md) when the change touches user interface, text styles, colors, images, controls, gestures, media, forms, or navigation;
- [`../ios-standards/references/localization.md`](../ios-standards/references/localization.md) when the change adds or changes user-facing text, string catalogs or `.strings` files, date, number, or unit formatting, or Info.plist texts;
- [`../ios-standards/references/apple-docs.md`](../ios-standards/references/apple-docs.md) before making an availability, deprecation, or other version-sensitive Apple API claim;
- [`../ios-standards/references/capability-providers.md`](../ios-standards/references/capability-providers.md) before using or reporting optional providers.

If a reference cannot be read, retry with another file-reading tool. If it still fails, name it in the baseline's gaps and do not apply its rules from memory.

Use accepted optional specialists when available and relevant. They deepen one module; they do not override project precedence or supply evidence by themselves. Do not stop because an optional skill is absent.

## Workflow

### 1. Choose the Review Entry

- A pull or merge request (URL or number): `review-pr`.
- Local changes, a commit, a branch comparison, or files: `review-local`.
- Called by another skill with a diff and `output_target: calling-skill`: `code-review` directly, in machine mode.

Pass the user's request (scope, output target, whether to post comments) through unchanged. The entry skill owns provider access, scope sizing, chunking, comments, and approvals.

### 2. Establish the iOS Baseline

Determine the actual deployment target, toolchain constraints, UI framework, architecture, dependency versions, and test framework from project evidence. Record conflicts between project policy and company defaults.

Check every project-instruction location listed in `precedence.md` with a file listing, then read each file that exists and name them. When none exist, say "No project instructions; baseline inferred from project evidence" and name the evidence used for each item. When they exist, report every place where they disagree with the project files or this machine, such as deployment targets, Xcode paths, or simulator names.

List project-local skills and say for each whether it was used and why. Check `.agents/skills/`, `.claude/skills/`, and `skills-lock.json` with a file listing first; report "none found" only after that check. They rank with project instructions in `precedence.md`.

### 3. Verify

Unless the user asks for a static-only review, build the affected scheme and run the tests that cover the changed code before the review, so the review can use the results. Resolve the route in the `tooling.md` order, starting with Xcode MCP, and run only build and test operations. Prefer the specific affected tests over the full suite. For each route, name the scheme, test plan, and destination, and report every route in the `tooling.md` order: `available` with the outcome, `unavailable` with the observed reason, or not run with the reason. Never invent a build or test result.

### 4. Build the iOS Review Context

Prepare what goes into `code-review`'s input, using the fields `code-review` defines. When the entry skill builds that input in step 5, add to it as follows; never replace what the entry skill puts there:

- `review_baseline` (under `code_input`): the baseline from step 2; the build and test results from step 3 (a failure the change causes is evidence for a finding, a pre-existing failure is a gap); the checks of every engaged module from the table below; and the rules of the `ios-standards` references read for this change, with their severity notes.
- `focus_areas`: append the engaged modules by name (for example "Concurrency, SwiftUI, Accessibility") to the entry skill's own focus areas.
- `constraints`: append the real deployment target and dependency versions, and the iOS review rules below, to the entry skill's own constraints.

Because a baseline is supplied, `code-review` and the entry skill use it instead of gathering the same project context again; they still read the changed code and whatever the change needs.

Engaged modules, checked only when the change touches them:

| Module | Concrete risks to trace |
| --- | --- |
| Swift | ownership, mutation, error semantics, API contracts, value/reference behavior |
| Concurrency | actor isolation, `Sendable`, task ownership, cancellation, ordering, stale results, continuation safety |
| SwiftUI | state ownership, identity, update loops, bindings, navigation, lifecycle, adaptive layout, previews |
| UIKit | lifecycle ordering, containment, reuse, bindings, main-thread UI work, interoperability |
| Architecture | explicit dependencies and effects, state ownership, test seams, consistency with scoped project pattern |
| Accessibility | the `accessibility.md` criteria the change touches: labels and traits, Dynamic Type and clipping, contrast, touch targets, focus, gestures and motion alternatives, forms and sign-in, status announcements; put the WCAG criterion in the title (for example `[WCAG 2.5.8]`) |
| Localization | new text localized for every supported language, keys matching the bundle's catalog, plurals, concatenation, locale-aware formatting; checks and severities in `localization.md` |
| Compatibility | availability against the real deployment target and resolved dependency versions |
| Tests | observable behavior, deterministic async control, failure/cancellation/order cases, suitable framework and naming |
| Security | secret storage, Keychain use, biometrics bound to secrets, client-only enforcement, logging privacy, transport exceptions and trust, cryptography, deep links and server-supplied links, web content bridges, analytics data, debug features in release, CI changes; checks and severities in `security.md` |
| Privacy and platform | permissions and usage descriptions, privacy manifest, entitlements, data at rest, background behavior |

iOS review rules to pass as constraints:

- For every changed asynchronous operation, answer four questions: who owns the task, what cancels it, what prevents an older result replacing a newer one, and how cancellation is distinguished from failure and a valid empty result. Actor isolation prevents data races; it does not answer those questions.
- Version-sensitive Apple claims follow `apple-docs.md`, and TCA claims `tca.md`. A finding that depends on framework or dependency behavior cites documentation or source at the resolved version; otherwise the concern is a residual gap, not a finding (`code-review`'s rule). Prefer compiler and project evidence over an external skill's assumed future toolchain.
- Do not report continued use of UIKit, MVVM, XCTest, or another established pattern by itself; recommend a migration only when evidence shows the current design blocks safe change or testing.
- Severity follows `code-review`'s shared standard. The severity tables in `accessibility.md`, `localization.md`, and `security.md` explain how iOS cases fit its labels (`security-violation`, `request-for-change`, `optional`); when they would differ, `code-review`'s standard decides.

### 5. Run the Review

Load and run the entry skill from step 1 with the user's request. When it assembles `code-review`'s input, add the context from step 4 as described there; when calling `code-review` directly, put the context in its input yourself. Let the entry skill finish as it normally does: its report, comments, and output are the review's result. Severities, categories, finding format, deduplication, and the machine-mode output are `code-review`'s; do not restate or change them. In hosts where all skills run in one agent, keep `code-review`'s output structure anyway; it is what the entry skill presents.

When the user gets the result in chat, show a `Baseline` section and a `Verification` section (steps 2 and 3) first, then the entry skill's report unchanged.

## Final Check

Before returning, confirm:

- aimate's skills were available, and the review ran through `review-pr`, `review-local`, or `code-review`;
- the always-read references were read, or the failure is named in the baseline;
- project instruction files and project skills were checked with a file listing before being reported;
- the engaged modules and their `ios-standards` rules reached `code-review` as `review_baseline`, `focus_areas`, and `constraints`, added to (not replacing) the entry skill's own values;
- a build and the affected tests were attempted unless the review was static-only, and no route is reported `unavailable` without an attempt or observed reason;
- no optional provider was treated as required, and no migration was proposed without demonstrated need.
