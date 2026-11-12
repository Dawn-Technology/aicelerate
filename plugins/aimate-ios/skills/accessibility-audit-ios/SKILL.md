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

Do not edit, stage, commit, branch, build, or run anything in this part. The only file written is the report.

### 1. Baseline

Check every project-instruction location listed in `precedence.md` with a file listing and read each file that exists; note accessibility rules, a target level (for example WCAG 2.1 AA or an accessibility statement), accepted exceptions, design tokens, and UI test conventions.

List the app targets and extensions with their UI frameworks (SwiftUI, UIKit, storyboards and XIBs, mixed), deployment targets, supported orientations, and localizations.

### 2. Screen Inventory

List the screens: SwiftUI views used as navigation destinations, tabs, sheets, and full-screen covers; `UIViewController` subclasses and storyboard scenes; alerts and custom overlays. Group them by feature with their main file. Mark screens that show web content (`WKWebView`, `SFSafariViewController`), media playback, forms, sign-in, payments, and onboarding, and note which are behind login or feature flags. When there are many screens, cover shared components (buttons, cells, text styles, colors) once and then each screen's own code.

### 3. Check Every Criterion

Work through every row of the `accessibility.md` Criteria table and the Platform Settings section. Use the search hints there, then read the code around each hit. Search tracked sources, storyboards and XIBs, asset catalogs, and Info.plists (`git ls-files`, then `git grep`), not build output or third-party packages. Record the searches used as evidence.

For contrast, resolve named colors from asset catalogs and design tokens in light and dark appearance, and compute the ratio only for foreground and background pairs you can show are used together; otherwise mark contrast for the audit or a tester.

### 4. Trace Before Classifying

For each hit, establish the screen, whether it is reachable in release builds, and which users it affects (VoiceOver, Voice Control, Switch Control, Full Keyboard Access, large text, low vision, limited dexterity). Drop false positives, such as an `Image` inside a `Button` that has a text label, a fixed font size scaled with `@ScaledMetric` or `UIFontMetrics`, or a decorative image already hidden. Classify with the `accessibility.md` severity table.

Give every criterion one status:

| Status | When |
| --- | --- |
| `fail` | A reachable finding for the criterion. |
| `pass` | Checked from source without findings, and nothing about it needs a running app or a person. |
| `needs check` | Source shows no failure, but the criterion also needs the automated audit or a tester (the `audit:` or `manual` marks in `accessibility.md`). Say what to check. |
| `not applicable` | The app has no such content (for example no video for 1.2.x), with the evidence. |

### 5. Write the Report

Write the report once to `<repo-root>/docs/<project-name>-accessibility-audit-<YYYY-MM-DD>.md` (add `-2`, `-3` instead of overwriting) and leave it untracked. Sections:

- `Summary`: the standard (WCAG 2.2 A and AA, interpreted for screens per WCAG2Mobile), counts of `fail`, `needs check`, and `pass`, how many failures are in the WCAG 2.1 AA baseline, and the three findings that affect users most.
- `Baseline`: instruction files read and rules applied, targets, UI frameworks, orientations, localizations, and the references read.
- `Screens`: the inventory, with web-content screens named as needing a web WCAG check.
- `Criteria`: one row per WCAG criterion: level, in WCAG 2.1 AA (yes or 2.2 only), status, and the findings or the evidence for the status.
- `Findings`: grouped by screen, each with severity, WCAG criterion, `file:line`, who is affected and how, and a fix direction.
- `Platform settings`: which iOS accessibility settings the app respects, as input for the App Store's Accessibility Nutrition Labels.
- `Needs a tester`: every `manual` item, written as a short test step (for example "VoiceOver: open Settings, check focus moves into the sheet").
- `Method and limits`: the searches, what static inspection cannot show (rendered contrast, clipping, real VoiceOver behavior), and that this is not a formal conformance claim.

When another skill calls this one, also return the YAML shape from [`../review-ios/SKILL.md`](../review-ios/SKILL.md) section "6. Return Compatible Output": `category: documentation` for missing labels and text, `maintainability` otherwise, the WCAG criterion in each `title` (for example `[WCAG 1.4.4]`), and "whole-app accessibility audit" in `summary.scope`.

## Part 2: Offer the Thorough Check

In the chat reply, give the report path, the summary, and the top three findings. Then ask the developer whether they want a thorough check, and explain it in a few lines:

- It adds one temporary XCUITest file that opens the main screens and runs `performAccessibilityAudit()` on each, at the default and the largest accessibility text size, in light and dark appearance.
- It confirms contrast, missing labels and traits, clipped text, Dynamic Type support, and small hit areas, which the static scan can only suspect.
- It needs a UI test target, a simulator with iOS 17 or later, and a way to reach the screens (existing UI test helpers, launch arguments, or a test account the project already uses). Name what is missing.
- It works on a new branch, builds, and runs only these tests; nothing is committed.

Stop and wait for the answer. Without a yes, the audit ends with the static report.

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
- every WCAG 2.2 A and AA criterion in `accessibility.md` has one status, with evidence, and failures in the WCAG 2.1 AA baseline are marked;
- every finding has `file:line` or audit evidence, a screen, the affected users, and a severity from `accessibility.md`;
- `manual` items are listed for a tester and none is marked `pass` from source alone;
- in Part 1 only the report was written; the thorough check ran only after the developer agreed, on a new branch, with nothing committed and the simulator appearance restored.
