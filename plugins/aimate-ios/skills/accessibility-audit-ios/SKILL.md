---
name: accessibility-audit-ios
description: Use when the user asks to check or validate the accessibility of a whole iOS app or Swift project, for example against WCAG 2.2 or WCAG 2.1 AA, before a release, or for the European Accessibility Act. Static scan per screen of VoiceOver labels and traits, Dynamic Type, contrast, touch targets, focus, gestures, forms, sign-in, and media, with a status per WCAG criterion in an untracked report in docs/. Then offers a thorough check that runs Apple's automated accessibility audit in XCUITest on a simulator. For accessibility review of a single change, use review-ios instead.
metadata:
  author: "Dawn Technology"
  version: 0.1.0
  role: "accessibility-audit"
  writes_source: "true"
  external_dependencies: "none"
---

# Accessibility Audit iOS

Validate a whole iOS app against WCAG 2.2 Level A and AA, applied to native screens, and write the result to a report. Work in two parts: a static scan that only reads the repository and writes the report, then an optional thorough check that builds the app and runs Apple's automated accessibility audit, only when the developer asks for it.

## Policy

Always read these shared references:

- [`../ios-standards/references/accessibility.md`](../ios-standards/references/accessibility.md)
- [`../ios-standards/references/precedence.md`](../ios-standards/references/precedence.md)

Read [`../ios-standards/references/tooling.md`](../ios-standards/references/tooling.md) and [`../ios-standards/references/testing.md`](../ios-standards/references/testing.md) before the thorough check, and [`../ios-standards/references/apple-docs.md`](../ios-standards/references/apple-docs.md) before a version-sensitive Apple API claim.

If a reference cannot be read, retry with another file-reading tool. If it still fails, name it in the report and do not apply its rules from memory.

## Part 1: Static Scan (read-only)

Do not edit, stage, commit, branch, or build in this part, and do not run the app. Read-only commands are allowed (`git ls-files`, `git grep`, `git status`, `xcrun simctl list`), and so are the bundled scripts in `scripts/`. The only file written is the report.

### 1. Baseline

Check every project-instruction location listed in `precedence.md` with a file listing and read each file that exists; note accessibility rules, a target level (for example WCAG 2.1 AA or an accessibility statement), accepted exceptions, design tokens, and UI test conventions.

List the app targets and extensions with their UI frameworks (SwiftUI, UIKit, storyboards and XIBs, mixed), deployment targets, supported orientations, and localizations. Also note what the thorough check in Part 3 would need, so Part 2 can name it: whether a UI test target exists, and whether an iOS 17 or later simulator runtime is installed (`xcrun simctl list runtimes`).

### 2. Screen Inventory

List the screens: SwiftUI views used as navigation destinations, tabs, sheets, and full-screen covers; `UIViewController` subclasses and storyboard scenes; alerts and custom overlays. Group them by feature with their main file. Mark screens that show web content (`WKWebView`, `SFSafariViewController`), media playback, forms, sign-in, payments, and onboarding, and note which are behind a gate: login, biometrics, a feature flag or remote config, consent, or an offline or error state.

### 3. Check Every Criterion

Work through every row of the `accessibility.md` Criteria table and the Platform Settings section. The report's `Criteria` table has a row for each criterion in that table and no others; a finding may name several of those criteria. Search tracked sources, storyboards and XIBs, asset catalogs, and Info.plists, not build output or third-party packages, and record the searches used as evidence.

Work search-first, so a large app stays manageable:

1. Run the search hints in `accessibility.md` over the whole app and group the hits by screen and by shared component.
2. Read the shared components (buttons, rows, cells, text styles, colors, navigation bars) once; a problem in one affects every screen that uses it.
3. Read each screen's own code around the hits. When the app has many screens, read every screen with hits and a sample of at least one screen per feature without hits; list the screens read and not read in `Method and limits`.
4. When the host can run subagents, split the work by feature or by criterion group, give each the same references, and merge their results into one row per criterion.

When source cannot settle a criterion (rendered contrast, clipping, real VoiceOver order, behavior on older iOS versions), give it `needs check` and say what to check; do not guess a `pass` or a `fail`.

For contrast, run `python3 <skill-dir>/scripts/color_contrast.py --repo <repo> --list` to resolve asset-catalog colors in light and dark appearance, then `--pair <foreground> <background>` for pairs you can show are used together (name the file and line). Name colors by their folder path (`Foreground/Base`) when a short name is ambiguous, and give a hex color used only in one appearance as `#light/#dark`. Work out which color reaches the text with Resolving Colors and Content in `accessibility.md`. A pair taken from design tokens without a confirmed use is an assumption: say so and give it `needs check`, not `fail`.

### 4. Trace Before Classifying

For each hit, establish the screen, whether it is reachable in release builds, and which users it affects (VoiceOver, Voice Control, Switch Control, Full Keyboard Access, large text, low vision, limited dexterity). Drop false positives, such as an `Image` inside a `Button` that has a text label, a font that scales (`Font.custom(_:size:)`, text styles, `@ScaledMetric`, `UIFontMetrics`), or a decorative image already hidden. See the false-positive notes in `accessibility.md`. Classify with the `accessibility.md` severity table.

Give every criterion one status:

| Status | When |
| --- | --- |
| `fail` | A reachable finding for the criterion. |
| `pass` | Checked from source without findings, and nothing about it needs a running app or a person. |
| `needs check` | Source shows no failure, but the criterion also needs the automated audit or a tester (the `audit:` or `manual` marks in `accessibility.md`). Say what to check. |
| `not applicable` | The app has no such content (for example no video for 1.2.x), with the evidence. |

### 5. Write the Report

Write the report once to `<repo-root>/docs/<project-name>-accessibility-audit-<YYYY-MM-DD>.md` (add `-2`, `-3` instead of overwriting) and leave it untracked. Sections:

- `Summary`: the standard (WCAG 2.2 A and AA, interpreted for screens per WCAG2Mobile), the counts of `fail`, `needs check`, `pass`, and `not applicable` as `check_report.py` prints them, how many failures are in the WCAG 2.1 AA baseline, and the three findings that affect users most.
- `Baseline`: instruction files read and rules applied, targets, UI frameworks, orientations, localizations, and the references read.
- `Screens`: the inventory, with web-content screens named as needing a web WCAG check.
- `Criteria`: one table with exactly one row per criterion in `accessibility.md`, in its order, with the columns `SC | Level | In 2.1 AA | Status | Evidence`. The SC cell starts with the number (for example `1.4.4 Resize Text`), and the Status cell holds one of `fail`, `needs check`, `pass`, `not applicable`. Do not group criteria in one row or list them in prose.
- `Findings`: grouped by screen, each with severity, WCAG criterion, `file:line`, who is affected and how, and a fix direction.
- `Platform settings`: which iOS accessibility settings the app respects, as input for the App Store's Accessibility Nutrition Labels.
- `Needs a tester`: every `manual` item, written as a short test step (for example "VoiceOver: open Settings, check focus moves into the sheet").
- `Method and limits`: the searches, what static inspection cannot show (rendered contrast, clipping, real VoiceOver behavior), and that this is not a formal conformance claim.

Before replying, run `python3 <skill-dir>/scripts/check_report.py --report <report path>`. It checks that every criterion appears once with one status and prints the counts for the summary. Fix the report until it passes.

When another skill calls this one, also return the YAML shape from [`../review-ios/SKILL.md`](../review-ios/SKILL.md) section "6. Return Compatible Output": `category: documentation` for missing labels and text, `maintainability` otherwise, the WCAG criterion in each `title` (for example `[WCAG 1.4.4]`), and "whole-app accessibility audit" in `summary.scope`.

## Part 2: Offer the Thorough Check

In the chat reply, give the report path, the summary, and the top three findings. Then ask the developer whether they want a thorough check, and explain it in a few lines:

- It adds one temporary XCUITest file that opens the main screens and runs `performAccessibilityAudit()` on each, at the default and the largest accessibility text size, in light and dark appearance.
- It confirms contrast, missing labels and traits, clipped text, Dynamic Type support, and small hit areas, which the static scan can only suspect.
- It needs a UI test target, a simulator with iOS 17 or later, and a way to reach the screens (existing UI test helpers, launch arguments, or a test account the project already uses). Name what Part 1 found missing, for example "there is no UI test target: you would need to add one in Xcode first", so the developer can decide with that in mind.
- It works on a new branch, builds, and runs only these tests; nothing is committed.

Stop and wait for the answer; on hosts where asking ends your turn, end it. Without a yes, the audit ends with the static report.

## Part 3: Thorough Check (after the developer agrees)

1. Require a clean working tree, apart from the untracked report; if it is not clean, stop and say so. Create a branch such as `chore/accessibility-audit` from the base the developer confirms. Never commit or push.
2. Find the UI test target. If there is none, stop: explain that the developer needs to add one in Xcode, and do not create targets or edit the project file for it. If the target's folder is a synchronized group (Xcode 16 and later), add the file there; otherwise ask the developer to add the file to the target in Xcode and wait.
3. Write `AccessibilityAuditUITests.swift` with one test per screen or flow. Reuse the project's launch arguments, mock data, and navigation helpers. Use test accounts only from the project's existing test configuration, and never ask for or write credentials. Call `try app.performAccessibilityAudit(for: .all) { issue in … }` with a handler that prints one line per issue (`A11Y-AUDIT | <screen> | <size and appearance> | <issue.auditType> | <issue.element?.debugDescription> | <issue.compactDescription>`) and returns `true`, so every screen is audited instead of stopping at the first issue. Run the largest text size with the launch arguments `-UIPreferredContentSizeCategoryName UICTContentSizeCategoryAccessibilityXXXL`. Set dark appearance with `xcrun simctl ui <device> appearance dark`, and restore the simulator's original appearance afterwards.
4. Build and run only these tests through the `tooling.md` route, and collect the `A11Y-AUDIT` lines from the test output. Report a screen the test could not reach, with the reason, instead of skipping it silently.
5. Map each issue to WCAG criteria with the audit-type mapping in `accessibility.md`, and trace it to code where possible. Mark static findings the audit confirmed, static `needs check` items it resolved, and new findings. An audit issue on a system control or third-party view is reported as such, at most `optional`.
6. Update the same report: add an `Automated audit` section (screens, sizes, appearances, simulator, route, and every issue with its criterion), and update the `Criteria` statuses and `Findings`.
7. Ask the developer whether to keep the test file as a regression test (they commit it) or remove it. Do not delete the branch yourself.

## Final Check

Before returning, confirm:

- project instructions were checked with a file listing, and the screen inventory names web-content screens;
- `check_report.py` passes: every criterion in `accessibility.md` has exactly one row and one status, with evidence, no other criteria are listed, and the summary counts are the ones it printed; failures in the WCAG 2.1 AA baseline are marked;
- every finding has `file:line` or audit evidence, a screen, the affected users, and a severity from `accessibility.md`;
- `manual` items are listed for a tester and none is marked `pass` from source alone;
- in Part 1 only the report was written; the thorough check ran only after the developer agreed, on a new branch, with nothing committed and the simulator appearance restored.
