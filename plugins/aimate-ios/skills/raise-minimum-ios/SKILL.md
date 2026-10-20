---
name: raise-minimum-ios
description: Use when the user wants to raise an iOS app's minimum deployment target (for example from iOS 16 to 18) and clean up code that only existed for the older versions. Scans first and presents a plan; changes code only after the developer confirms, on a new branch, without committing.
metadata:
  author: "Dawn Technology"
  version: 0.1.0
  role: "deployment-target-upgrade"
  writes_source: "true"
  external_dependencies: "optional"
---

# Raise Minimum iOS

Raise the minimum iOS version and remove what only existed for older versions: always-true availability checks, backport wrappers, and backport packages. Work in three phases: scan, plan with confirmation, execute. Never change a file before the developer confirms the plan.

## Policy

Always read:

- [`../ios-standards/references/precedence.md`](../ios-standards/references/precedence.md)
- [`../ios-standards/references/tooling.md`](../ios-standards/references/tooling.md) for build and test routes, DerivedData, and package flags.
- [`../ios-standards/references/architecture.md`](../ios-standards/references/architecture.md), so cleanup follows the project's architecture.

Read [`../ios-standards/references/tca.md`](../ios-standards/references/tca.md) when the project uses TCA, and [`../ios-standards/references/apple-docs.md`](../ios-standards/references/apple-docs.md) before claiming that an API is available or deprecated at a version.

If a reference cannot be read, retry with another file-reading tool. If it still fails, name it and do not apply its rules from memory.

## Phase 1: Scan (read-only)

Check every project-instruction location in `precedence.md` and read what exists. Then collect, with evidence:

1. **Minimums**: every Xcode target and package with its iOS minimum, from `xcrun python3 ../review-architecture-ios/scripts/ios_platform.py --repo <repo>` (relative to this skill's folder; it prints settings per Xcode target and every `Package.swift` platform). Mark which will be raised. Count only targets that build for iOS (`SDKROOT` `iphoneos` or `iphoneos` in `SUPPORTED_PLATFORMS`); an inherited `IPHONEOS_DEPLOYMENT_TARGET` on a tvOS, watchOS, or macOS target does nothing and is not a step. Targets already above the new minimum, and other platforms, stay unchanged unless the user asks.
2. **Availability checks**: run `xcrun python3 <skill-dir>/scripts/availability.py --repo <repo> --min iOS=<new>`, adding `--min` for other platforms only when they are raised too. Group results into always-true, always-false, backport candidates, review, and still needed.
3. **Backports**: modules, files, and wrappers that exist only for older iOS (a `Backport` module, `.backport.` modifiers, wrappers marked `deprecated:` at or below the new minimum) and the system API each one maps to.
4. **Backport packages**: packages that become unused or only pass through to the system at the new minimum (for example `navigation-stack-backport`, or `SwiftUIIntrospect` calls for old versions).
5. **Required migrations**: changes the build will force at the new minimum. Known cases:

   | From | Trigger | Change |
   | --- | --- | --- |
   | `swift-perception` (`@Perception.Bindable`, `WithPerceptionTracking`, `@Perceptible`) | iOS 17 or higher | `@Bindable`, unwrap `WithPerceptionTracking`, `@Observable`, `import Observation`; required because Perception makes its API unavailable or deprecated at iOS 17 |
   | `NavigationStackBackport` | iOS 16 or higher | system `NavigationStack` and `navigationDestination` |

   Anything else surfaces in phase 3; follow the rule there.
6. **Expected new deprecation warnings**: APIs the project uses that are deprecated at or below the new minimum, for example `onChange(of:perform:)` at iOS 17. List only deprecations confirmed with `apple-docs.md` or seen in a build; do not list "likely" ones.
7. **Documents and scripts** that state the old minimum: README, project instructions, CI scripts, fastlane, license or metadata files.
8. **Follow-ups not done by this skill**: modernizations the new minimum allows but does not require (`ObservableObject` to `@Observable`, `NavigationView` to `NavigationStack`), removing extension targets or legacy widget setups that only served old versions, and other platforms' minimums.
9. **Verification plan**: schemes and test plans to build and run, with known limits (for example snapshot tests that already fail, or test targets that are disabled).

## Phase 2: Plan and Confirm

Present the plan and stop. Open with a short summary that a developer can decide from without reading further, at most about ten lines:

- from and to version, and the targets and packages that change;
- per step, one line with the number of places or files;
- risks and decisions the developer must make (for example other platforms sharing code, or generated files);
- your recommended selection and the base branch.

Then give the details in these sections:
- `Steps`: numbered, each with what changes and how many places: 1 minimums, 2 dead availability code, 3 backport wrappers, 4 backport packages, 5 required migrations, 6 new deprecation warnings, 7 documents and scripts.
- `Not changed`: targets and platforms left alone and why.
- `Follow-ups`: from scan item 8.
- `Verification`: the build and test plan and its limits.
- `Branch`: the branch name to create, for example `chore/ios-<new>-minimum`, and the base branch to create it from. Propose the project's integration branch (for example `develop` or `main`) rather than an unrelated feature or bugfix branch, and ask when unsure.

Ask the developer to choose: all steps, selected step numbers, or stop. Do nothing until they answer.

## Phase 3: Execute (after confirmation)

1. Require a clean working tree; if it is not clean, stop and say so. Create the branch from the confirmed base branch. Never commit or push.
2. Before changing anything, do a clean build of the affected schemes (route from `tooling.md`) and save the full warning list, then run the test plans from the verification plan and save their results. An incremental build gives an incomplete warning list, and without a test run on the unchanged code a later failure cannot be attributed.
3. Carry out the confirmed steps in order. Keep the code in the remaining branch exactly when removing an availability check; keep checks for other platforms. Delete a wrapper or package only when nothing uses it any more.
4. Build after each step, so a failure points to one step. When a build failure or warning needs a change outside the confirmed steps (an unpredicted migration, a type-checker timeout, a concurrency error), stop and ask, describing the change and why the build needs it.
5. Run the same test plans again and compare them with the run from step 2, and do a clean build to compare warnings with the first build: report new ones, and fix those the raise caused when step 6 was confirmed.
6. Leave `Package.resolved` to Xcode unless a removed package must leave it for the build to resolve; say which.

## Report

End with:

- `Changes`: per step, what changed and how many places, with the files most affected.
- `Not changed`: with reasons.
- `Verification`: the build and test results before and after, warnings before and after, and what could not be verified.
- `Follow-ups`: from the plan, plus anything found during execution.
- `Git`: the branch, that nothing is committed, and the changed-file count.

## Final Check

Before returning, confirm:

- nothing was changed before the developer confirmed, and only confirmed steps were carried out;
- work happened on a new branch, nothing was committed or pushed;
- no target above the new minimum and no other platform was lowered or changed unasked;
- every removed availability check kept the code of the branch that is always taken;
- builds and tests ran before and after, and the report says what was not verified.
