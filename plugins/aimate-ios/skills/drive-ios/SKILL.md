---
name: drive-ios
description: Use when the user asks to operate an iOS app on a simulator towards a goal, such as reproducing a QA ticket or crash, validating that a flow works, or capturing screenshots of screens. Builds the app, navigates it through deep links or UI automation, and reports steps with evidence; never edits source.
metadata:
  author: "Dawn Technology"
  version: 0.1.0
  role: "simulator-app-driver"
  writes_source: "false"
  external_dependencies: "optional"
---

# Drive iOS

Operate the app on a simulator for one of three goals and report what happened with evidence:

| Goal | Typical request | Result |
| --- | --- | --- |
| `reproduce` | A QA ticket, bug, or crash report | Reproduced (with count) or not reproduced, steps, crash evidence |
| `validate` | "Check that a user can …" | Pass, fail, or blocked per check |
| `capture` | "Take screenshots of …" | Named screenshots per screen and variant |

Infer the goal from the request and state it. This skill never edits source, test, or project files, never changes git state, and never fixes the problem it finds. Physical devices and live client demos are out of scope for this version.

## Policy

Always read these shared references first:

- [`../ios-standards/references/precedence.md`](../ios-standards/references/precedence.md)
- [`../ios-standards/references/tooling.md`](../ios-standards/references/tooling.md) for building: project-selected route first, existing DerivedData, package flags, unique temporary folders.
- [`../ios-standards/references/capability-providers.md`](../ios-standards/references/capability-providers.md) before using `MobileBuildMCP`.

If a reference cannot be read, retry with another file-reading tool. If it still fails, name it in the report and do not apply its rules from memory.

## Workflow

### 1. Baseline

Check every project-instruction location listed in `precedence.md` with a file listing and read each file that exists, including test accounts, environments, launch arguments, and deep-link formats it documents.

Record the scheme and build configuration, the bundle identifier, the app version and build number (`CFBundleShortVersionString` and `CFBundleVersion` of the built app), the backend environment that configuration talks to, and the simulator (name, runtime, id). Use the simulator the user names; otherwise an available iPhone simulator that meets the deployment target. Never use or change a simulator another run is using.

### 2. Plan

Before touching the simulator, write the plan:

- `reproduce`: the ticket's steps, expected result, and reported result.
- `validate`: numbered checks, each with its expected result.
- `capture`: every screen times every variant (appearance, device, locale) requested.

Choose the shortest reliable route to each screen: a deep link or universal link (`xcrun simctl openurl`), a launch argument or environment value the project supports, then UI navigation.

Avoid side effects beyond the request: no purchases, account creation, messages, feedback submissions, or changes to real user data on a production backend. Ask before any such action. Decide how to answer permission prompts from the request (deny unless the flow needs the permission) and report each answer.

### 3. Prepare

Build and install with the `tooling.md` route. Record the starting state: whether the app was installed, and the simulator's appearance, locale, and status bar. Reinstalling keeps the app's data; uninstalling wipes it, except the keychain, which survives an uninstall. When the scenario needs a truly fresh state, prefer a temporary simulator this run creates (`xcrun simctl create`) and deletes afterwards. Never reset the keychain (`simctl keychain reset`) or erase a simulator this run did not create without asking first: both affect every app on it and cannot be undone.

For `capture`, wait for animations and rotating content (carousels) to settle and note when variants show different content. Set a clean status bar (`xcrun simctl status_bar <id> override --time 9:41 --batteryState charged --batteryLevel 100 --cellularBars 4 --wifiBars 3`) and switch appearance with `xcrun simctl ui <id> appearance light|dark`.

### 4. Drive

Navigate with `MobileBuildMCP` UI automation: `snapshot-ui`, then `tap`, `type-text`, `swipe`, or `wait-for-ui` by element reference. Take a fresh snapshot after every navigation, scroll, or sheet change. Identify elements by accessibility label or identifier, not coordinates. Take a screenshot at every step that matters (`xcrun simctl io <id> screenshot <file>`). System alerts and prompts do not appear in screenshots; use the UI snapshot text as evidence for them.

Without `MobileBuildMCP`, use deep links, launch arguments, and `simctl` only. When a step needs UI navigation that these cannot reach, mark it blocked with the manual step instead of writing UI test code.

For `reproduce`, also check whether the result persists after relaunching the app when that matters, and repeat the reproduction once to report a count such as "reproduced 2 of 2".

### 5. Crashes

When the app disappears or the snapshot shows the home screen, treat it as a possible crash:

- Collect the newest crash report for the app's process from `~/Library/Logs/DiagnosticReports/` (`.ips`), with the exception type and the top app frames.
- Collect the app's log around the crash (`xcrun simctl spawn <id> log show --last 5m --predicate 'process == "<executable>"'`).
- When the crash reproduces and a backtrace with variables would help, attach `MobileBuildMCP` debugging before the crashing step and capture `stack` and `variables`.

A hypothesis about the cause may point to `file:line`, labeled as a hypothesis.

### 6. Clean Up

Restore what this run changed: appearance, status bar (`xcrun simctl status_bar <id> clear`), locale, and location. Terminate the app. Shut down the simulator if this run booted it, and delete a simulator this run created. Delete only temporary folders this run created; keep the evidence folder, which is never inside the repository.

### 7. Report

Open with these sections:

- `Baseline`: project instruction files found, scheme, configuration, version and build, backend environment, simulator, and starting state.
- `Plan`: goal and the planned steps, checks, or screen list.
- `Steps`: numbered actions with the observed result and screenshot file per step.
- `Result`: reproduced (count) or not reproduced; pass, fail, or blocked per check; or the list of captured files with what each shows and screens that could not be reached.
- `Evidence`: folder path, crash report and log excerpts.
- `Side effects`: permission answers, data created or removed, simulator changes, and what was restored.
- `Not covered`: other paths to the same result, devices, and anything blocked.

## Final Check

Before returning, confirm:

- project instructions were checked with a file listing, and the build used the `tooling.md` route;
- the plan was written before driving, and every check or screen has a result;
- the version, build, backend environment, and simulator are named;
- every claim has a screenshot, UI snapshot, crash report, or log as evidence;
- no source or git state changed, the simulator was restored, and only this run's temporary folders were deleted.
