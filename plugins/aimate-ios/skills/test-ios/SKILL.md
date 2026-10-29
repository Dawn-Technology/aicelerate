---
name: test-ios
description: Use when the user asks to run iOS tests, such as the tests affected by a change, a named test, class, target, or test plan, or the full suite, on a simulator. Builds and runs tests through Xcode MCP, MobileBuildMCP, or xcodebuild and reports results; never edits source or test files.
metadata:
  author: "Dawn Technology"
  version: 0.1.0
  role: "simulator-test-runner"
  writes_source: "false"
  external_dependencies: "optional"
---

# Test iOS

Run the tests the user asks for on a simulator and report exactly what ran and what happened. This skill builds and tests; it never edits source, test, project, or scheme files, never changes git state, and never fixes a failing test. Suggest a fix only when asked.

## Policy

Always read these shared references before running anything:

- [`../ios-standards/references/precedence.md`](../ios-standards/references/precedence.md)
- [`../ios-standards/references/tooling.md`](../ios-standards/references/tooling.md)

Read [`../ios-standards/references/testing.md`](../ios-standards/references/testing.md) when reporting missing coverage, and [`../ios-standards/references/capability-providers.md`](../ios-standards/references/capability-providers.md) before using `MobileBuildMCP`.

If a reference cannot be read, retry with another file-reading tool. If it still fails, name it in the report and do not apply its rules from memory.

## Workflow

### 1. Baseline

Check every project-instruction location listed in `precedence.md` with a file listing, read each file that exists, and use its build and test commands, schemes, test plans, simulators, and known flaky tests. Report every place where they disagree with this machine, such as a missing simulator or Xcode path, and the substitute used.

Find the workspace or project, the schemes, the test plans (`*.xctestplan` and scheme test actions), and the test targets, including `.testTarget` entries in local packages. Pick a simulator that the instructions name, or an available iPhone simulator whose runtime meets the deployment target; name it by id when names are ambiguous.

### 2. Select Tests

Decide what to run before running anything:

| Request | Selection |
| --- | --- |
| Named test, class, or target | Exactly that, with `-only-testing:<Target>/<Class>/<test>` |
| Test plan or full suite | That plan, or the scheme's default plan as the instructions specify |
| Tests affected by a change | Map each changed file to the target that compiles it (`project.pbxproj` or `Package.swift`), find test targets that depend on that target, then search those for tests that use the changed types. Run only those. |

When no test exists or none covers the change, say so with the evidence (for example "LocationQuery.swift is compiled only into WidgetsExtension; no test target depends on it"). Do not run unrelated tests and present them as verifying the change. Instead build the affected scheme and report it as a build, not a test, and offer the full suite.

When the project has no test targets at all, confirm it from the project files without trying test actions, build the scheme from the instructions as the only available verification, and report it as such.

### 3. Run

Use the routes in `tooling.md` order, starting with the project-selected route, and follow its DerivedData, package, and result-bundle rules. Use the longest available command timeout; run long builds in the background and wait for them rather than restarting them.

When a test fails, rerun only the failing tests once. A test that passes on rerun is reported as flaky, not as passing. A failure that a project instruction lists as known flaky is reported as such. Without either, say whether the failure is in code the change touches; do not claim it is pre-existing without evidence. Never switch branches or stash changes to compare with a base.

UI tests (XCUITest) and snapshot tests run only when requested, when they cover the change, or when the selected plan contains them; say when they were skipped. Physical devices are out of scope: report `device-not-run: not in V1`.

### 4. Report

Open with these sections:

- `Baseline`: project instruction files found and their disagreements with this machine, workspace or project, scheme, test plan, destination (name, runtime, id), and Xcode version.
- `Verification`: every route in `tooling.md` order with its exact state (`available` with the outcome, `fallback`, `unavailable` with the observed reason, or not run with the reason), and the exact commands or tool calls used.
- `Selection`: what was selected and why, including changed files mapped to targets and tests, or the evidence that no test covers them.
- `Results`: passed, failed, skipped, and flaky counts from the result bundle or tool output. For each failure: test identifier, assertion message, `file:line`, and whether the rerun confirmed it.
- `Gaps`: what was not run and why, including missing coverage for the change and the build-only verification used instead.

Never report tests as passed when only a build ran, and never invent counts.

## Final Check

Before returning, confirm:

- project instructions were checked with a file listing and their commands were used first;
- tests were selected before running, and unrelated tests were not presented as covering the change;
- no source, test, project, or scheme file was edited, and git state is unchanged;
- only folders this run created were deleted;
- every route has an exact state, and every count comes from tool output.
