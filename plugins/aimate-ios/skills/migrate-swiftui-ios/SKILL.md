---
name: migrate-swiftui-ios
description: Use when the user wants to convert a UIKit iOS app, or most of its screens, to SwiftUI. Scans the project, presents a conversion plan per screen with estimated time and token usage, agrees with the developer what is feasible, converts the approved screens on a new branch with a build after every batch, and ends with what succeeded and the tokens it used. To raise the deployment target first, use raise-minimum-ios.
metadata:
  author: "Dawn Technology"
  version: 0.1.0
  role: "uikit-to-swiftui-migration"
  writes_source: "true"
  external_dependencies: "none"
---

# Migrate to SwiftUI iOS

Convert a UIKit app to SwiftUI, screen by screen, so the app keeps building and working after every batch. Work in four phases: scan, plan, agree on what is feasible, convert, then report. Never change a file before the developer approves the plan.

## Policy

Always read:

- [`references/conversion-guide.md`](references/conversion-guide.md)
- [`../ios-standards/references/precedence.md`](../ios-standards/references/precedence.md)
- [`../ios-standards/references/architecture.md`](../ios-standards/references/architecture.md)
- [`../ios-standards/references/tooling.md`](../ios-standards/references/tooling.md) for builds and tests.
- [`../ios-standards/references/legacy-projects.md`](../ios-standards/references/legacy-projects.md)

Read [`../ios-standards/references/tca.md`](../ios-standards/references/tca.md) when the project uses TCA, [`../ios-standards/references/accessibility.md`](../ios-standards/references/accessibility.md) and [`../ios-standards/references/localization.md`](../ios-standards/references/localization.md) when converting screens, [`../ios-standards/references/testing.md`](../ios-standards/references/testing.md) when tests change, and [`../ios-standards/references/apple-docs.md`](../ios-standards/references/apple-docs.md) before a version-sensitive API claim.

If a reference cannot be read, retry with another file-reading tool. If it still fails, name it and do not apply its rules from memory.

## Token Measurement

Measure tokens from the start of phase 1, so the report can compare the estimate with what the work used.

- In Claude Code, run `python3 <skill-dir>/scripts/token_usage.py now` at the start and save the timestamp. Later, `python3 <skill-dir>/scripts/token_usage.py sum --since <timestamp>` totals the session's main conversation and its subagents per model. Mark the start of phase 4 the same way.
- On another host, or when the script exits with status 2, ask the developer to read the host's usage or cost view at the start and at the end, and use their numbers. If no counter exists, say the actual usage is unknown. Never invent a number.
- A conversion that continues in a new session needs a new mark per session; add the sessions together in the report.

## Phase 1: Scan (read-only)

1. Check every project-instruction location in `precedence.md` with a file listing and read what exists: architecture, navigation, design system, UI test conventions, and any rules about SwiftUI.
2. Run `python3 <skill-dir>/scripts/uikit_inventory.py --repo <repo>` (add `--json` for the plan's data). It lists view controllers with a complexity class, UIKit views and cells, storyboard and XIB scenes, UIKit-only APIs per file, existing SwiftUI and bridging code, and the app lifecycle. Add `--exclude` for vendored code the project keeps in the repository.
3. Run `xcrun python3 <skill-dir>/../review-architecture-ios/scripts/ios_platform.py --repo <repo>` for the deployment targets, and check them against the Deployment Target table in the guide.
4. Map the navigation: how each screen is presented (coordinator, segue, push from another controller, tab, deep link), and which screens are leaves.
5. Read each screen's controller, view model, and storyboard scene or XIB enough to confirm the inventory's class and to choose a decision from the guide (`convert`, `convert with wrapper`, `keep UIKit`, `remove`). Find shared UIKit components and styles used by several screens.
6. Note how the project adds files (synchronized folders, XcodeGen or Tuist, or classic groups; see Project Files in the guide) and which UI and snapshot tests cover each screen. Do not build yet; the baseline build runs in phase 4.

## Phase 2: Plan

Present the plan and stop. Write it also to `<repo-root>/docs/<project-name>-swiftui-migration-plan-<YYYY-MM-DD>.md`, untracked, so a later session can continue from it. Open with a summary a developer can decide from, at most about ten lines:

- what the app has: screens by class, storyboard scenes and XIBs, shared components, and the deployment target;
- the recommended scope: how many screens to convert, wrap, keep, or remove;
- the estimate for that scope as ranges: agent time, developer review and testing time, and tokens (all types and output);
- decisions the developer must make first.

Then the details:

- `Screens`: one row per screen, ordered as the guide's strategy converts them: name, files, class, decision with its reason, wrappers needed, tests that cover it, agent time, tokens, and developer time.
- `Foundation`: shared styles and components to convert first.
- `Navigation and lifecycle`: what stays UIKit, and the optional steps to convert coordinators and the app lifecycle, each with its estimate.
- `Batches`: groups of screens converted and built together, in order. The first batch is a pilot of one or two typical S or M screens.
- `Risks`: deployment-target limits, UIKit-only APIs, Rx or other binding frameworks, project-file changes, visual differences, and screens without tests.
- `Estimate`: totals per part and in all, as ranges from the guide's Estimates table, saying that the pilot will correct them.
- `Verification`: builds and tests per batch, and what needs manual checking.
- `Branch`: the branch to create, for example `feature/swiftui-migration`, from the project's integration branch.

## Phase 3: Agree What Is Feasible

Go through the plan with the developer before changing anything. Ask, at least:

- per screen or batch, whether they agree with the decision, and which screens to leave out;
- whether to convert navigation and the app lifecycle now or later;
- deployment-target limits, and whether to raise the minimum first with `raise-minimum-ios`;
- visual differences they accept, and design references to follow;
- how to change the project file when its folders are not synchronized;
- whether the agent may make one local commit per batch on the migration branch (never push), or leaves everything uncommitted;
- the base branch, and when to stop for review (after the pilot, after every batch, or only at the end).

Update the plan file with the answers. Do nothing until the developer approves the final selection.

## Phase 4: Convert (after approval)

1. Require a clean working tree, apart from the untracked plan; if it is not clean, stop and say so. Create the branch from the confirmed base. Never push.
2. Mark the token start of this phase. Build the affected schemes and run the test plans with the `tooling.md` route, and save the results as the baseline, so later failures can be attributed.
3. Convert in the approved batch order, following the guide's Mapping and Must Stay the Same sections. Per screen: write the SwiftUI view, connect it to the existing view model, host it where the controller was presented, keep accessibility identifiers and localization keys, and remove the old controller, scene, or XIB only when nothing else uses them.
4. After every batch: build, run the tests that cover the batch, fix failures the conversion caused, and update the plan file's progress. Commit locally only when the developer allowed it, with a message naming the screens.
5. After the pilot batch: measure its tokens and time, recalculate the estimate for the remaining batches with the measured numbers, show both, and ask the developer to continue, adjust, or stop.
6. When a screen needs a change outside the approved plan (a new wrapper, a change to a shared component, a model change, a deployment-target issue), or the same build failure persists after three attempts, stop and ask. Mark a screen that cannot be finished as not converted and restore its UIKit version, so the app still works.
7. At the end: a clean build of all affected schemes, the full test plans compared with the baseline, and the token total.

## Report

End with, and add to the plan file:

- `Converted`: per screen, the result (converted, converted with wrapper, kept UIKit, removed, not converted) and its files.
- `Not converted`: each screen that failed or was stopped, why, and what is needed to finish it.
- `Verification`: builds, test results compared with the baseline, and what needs manual checking per screen (look, animations, VoiceOver, keyboard, iPad); suggest running `accessibility-audit-ios` on the converted screens.
- `Tokens and time`: the estimate from the plan, the corrected estimate after the pilot, and the actual tokens per type and per model (main conversation and subagents) with the source of the numbers, plus the agent's working time. Name sessions that could not be measured.
- `Follow-ups`: navigation or lifecycle steps not done, wrappers that could become SwiftUI at a higher deployment target, and dead code left.
- `Git`: the branch, the commits made or that nothing is committed, and the changed-file count.

## Final Check

Before returning, confirm:

- nothing changed before the developer approved the plan, and only approved screens were converted;
- every batch was built and its tests run, and the final results were compared with the baseline;
- every converted screen kept its accessibility identifiers, localization keys, and entry points;
- the app builds, and any screen that could not be converted still works in UIKit;
- token numbers come from `token_usage.py` or the developer's host counter, or are reported as unknown;
- the plan file is up to date, nothing was pushed, and commits were made only if allowed.
