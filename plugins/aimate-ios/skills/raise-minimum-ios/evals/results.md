# Raise Minimum iOS Evaluation Results

Evaluated 2026-10-20 in Claude Code on local clones in the session scratchpad (`git clone --local`, gitignored build inputs and downloaded packages copied with `cp -c`), never in the user's checkouts. Builds used `-clonedSourcePackagesDirPath` with the copied packages.

## Reproduce

1. Clone each project into a scratchpad folder, copy gitignored build inputs (KNMI's KMP xcframework, NPO's xcconfigs) and the project's downloaded `SourcePackages`.
2. Baseline: a fresh agent without the skill gets the request from `evals.json`.
3. Skill run: a fresh agent loads `../SKILL.md`, stops after the plan, receives the developer's decision, then executes.
4. Check results against `evals.json`; reset clones with `git reset --hard && git clean -fd` between runs.

## Baselines (Opus)

- **Thuisarts 16.1 → 18**: deleted the Backport module, moved 30 call sites to system modifiers, removed dead checks and two unused packages, updated the Copilot instructions, launched the app on iOS 18. Did not create a branch. Migrated Perception to Observation (about 130 places), stating the build fails without it at iOS 17+.
- **KNMI 15 → 17**: raised minimums, removed iOS 15/16 code, NavigationStackBackport, and old introspect calls, migrated Perception, fixed new `onChange` warnings; clean build and unit tests passed; snapshot plan already failed on unchanged code. Did not create a branch.
- **NPO 16.4 → 18**: stopped by the user before reporting.

Lessons: always branch; separate migrations the new minimum forces from optional modernizations; fix warnings the raise introduces; let the developer decide before 100+ files change (the user's scan, plan, confirm design).

## Skill Runs (Sonnet)

- **Plan phase, all three**: no files changed. KNMI's plan found that macOS, tvOS, and watchOS apps share the package at old minimums, so Observation and NavigationStack cannot replace the backports there without splits, and asked. Thuisarts's plan proposed branching from the current bugfix branch. NPO's plan kept the tvOS-only `focusSection` and the tvOS-shared scroll-geometry wrapper.
- **Execution, NPO** (user: all steps, keep tvOS wrapper, leave inert TV settings, raise Preview): branch `chore/ios-18-minimum`, 52 files, nothing committed. iOS and tvOS built before and after every step; unit tests iOS 1,854/0 failed before and after, tvOS 1 flaky failure before, 0 after; no new warnings in a full rebuild; `availability.py` afterwards reports only the four kept tvOS checks. Snapshot plan crashed in the SnapshotTesting library and was not run on unchanged code, so it is unverified.

## Changes After Evaluation

From the plan runs: count only targets that build for iOS, list only confirmed deprecations, propose and confirm the base branch, open the plan with a short summary. From the NPO execution: run the planned tests before changing anything, and compare warnings from clean builds. Not re-evaluated.
