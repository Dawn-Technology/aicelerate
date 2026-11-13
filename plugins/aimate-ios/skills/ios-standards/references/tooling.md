# Tool and Host Resolution

Resolve capabilities, not brand-specific command names:

1. Honor a route explicitly selected by the user or project.
2. Use native host/Xcode integration.
3. Use an accepted optional provider already available.
4. Use an approved local command-line route.
5. Perform static inspection and report unexecuted verification.

OpenCode, Claude Code, Codex, and GitHub Copilot are supported skill hosts. Tool availability differs; never claim a build, test, launch, screenshot, simulator, or device check that did not execute.

## Build and Test

Build or test commands given in any project instruction file (see `precedence.md`) are the project-selected route: use them first, before the routes below, and keep their scheme, test plan, and destination. When a path, Xcode version, or simulator they name does not exist on this machine, report the difference (for example "AGENTS.md names Xcode_26.2.app; used Xcode 26.6") and use the closest available match.

Otherwise:

1. Xcode MCP (`xcrun mcpbridge`, Xcode 27 or later): `BuildProject`, `GetBuildLog`, `XcodeRefreshCodeIssuesInFile`, `GetTestList`, `RunSomeTests`, `RunAllTests`, and `RenderPreview`. It uses the active scheme, test plan, and run destination; report which ones.
2. `xcodebuild` and `xcrun simctl`.
3. Static inspection, naming what was not run.

Before using Xcode MCP, call `XcodeListWorkspaces` and use the workspace that belongs to the reviewed repository. When Xcode is running but the project is not open, open it with `XcodeOpenWorkspace` and close it with `XcodeCloseWorkspace` at the end of the run. When Xcode is not running or exposes no tools, report Xcode MCP as `unavailable` with the reason and use the next route. Never build or test another project.

Select the scheme, test plan, and run destination with `XcodeSwitchScheme`, `XcodeSwitchTestPlan`, and `XcodeSwitchRunDestination` when the active ones do not fit the task. These change what the developer sees in Xcode, so note the original values and switch back at the end of the run.

When Xcode MCP builds but tests return no results, the active run destination may not be a simulator. Switch it to a simulator, or report that and use the next route for tests.

For `xcodebuild`, reuse the project's existing DerivedData when Xcode is not building, so the run is incremental and already-fetched private packages are reused. Use a separate `-derivedDataPath` when Xcode is building the same project, and for a worktree or clone other than the one the existing DerivedData belongs to (Xcode being open on another checkout is not a reason by itself); create it with a unique name (`mktemp -d`), delete only that folder after the run, and never delete a folder this run did not create. When the change does not touch `Package.resolved` or `Package.swift`, add `-skipPackageUpdates -disableAutomaticPackageResolution` so the run does not refetch packages; a fresh package fetch can fail on private SSH repositories this machine cannot read. A fresh worktree or clone has no DerivedData and no packages yet: the first build must resolve them (without those two flags), and only later runs skip resolution. When the first resolution fails on a private package, report the package and the error as the blocker.

### Simulator Builds and Signing

Builds and tests for a simulator need no provisioning profile, certificate, or Apple account: Xcode signs simulator apps locally. Missing signing material, `certs/` folders, or `.mobileprovision` files are not a reason to skip a simulator build. Try the build and report what actually fails. With `xcodebuild`, a simulator destination (`-destination 'platform=iOS Simulator,name=<device>'`) is enough; add `CODE_SIGNING_ALLOWED=NO` only when the build still fails on signing.

Projects often run their own build-phase scripts (provisioning hashes, version stamps, generated code) whatever the destination. Read such a script before deciding it blocks the build, and compare `git status` before and after the first build. When it rewrites tracked files, note them, restore them after each build (`git checkout -- <file>`), and report that you did, so the working tree only holds the intended changes. When a build really needs something this machine does not have (a private package it cannot fetch, a secret in a generated file), report it as the blocker with the observed error; never create, copy, or ask for credentials.

Pass `-collect-test-diagnostics never` to test runs: after a failure, the default diagnostics collection can wait 10 minutes for the simulator, and failure details come from the result bundle instead. Pass `-resultBundlePath` with a unique temporary path and read counts and failures with `xcrun xcresulttool get test-results summary --path <bundle> --compact` (`tests` and `test-details` for more). Delete the bundle afterwards unless the user wants it.

Read-only skills use only Xcode MCP tools that read, select a scheme, test plan, or run destination, build, test, run the app, report diagnostics, render previews, or search documentation. They never call `XcodeWrite`, `XcodeUpdate`, `XcodeMV`, `XcodeRM`, or `XcodeMakeDir`.

### CocoaPods

Run `pod install` (never `pod update`) when `Pods/` is missing or older than `Podfile.lock`. It may rewrite checksums or the `COCOAPODS` version in the tracked `Podfile.lock`; restore the tracked file afterwards and copy it to the ignored `Pods/Manifest.lock`, or the "[CP] Check Pods Manifest.lock" phase fails. A pod whose source cannot be fetched (a deleted or private repository) is a blocker: report the pod, version, source, and error. When an exact copy of that version exists on this machine (another checkout's `Pods/`, with a matching checksum), placing it in the CocoaPods cache so the unchanged Podfile installs it is a route the developer must approve; keep a list of every cache entry added and remove exactly those entries, by literal path, before finishing. Never edit a pod's source code.

### Build Readiness

Before a migration or another larger change, check read-only whether the project can be built and run here, so all prerequisites are agreed at once:

- **Dependency sources**: every Swift package and pod source can be reached (`git ls-remote <url> HEAD` for git sources, the CocoaPods trunk for released pods). A private or deleted repository is a blocker.
- **Toolchain gap**: the Xcode the project documents or last used (README, CI configuration, `.xcode-version`) against the installed one. A much newer Xcode rejects old deployment targets in pods (below the oldest version it supports) and can reject third-party code that misses newer availability annotations.
- **Simulator architectures**: `EXCLUDED_ARCHS[sdk=iphonesimulator*] = arm64` in pod or project settings means an x86_64-only simulator build; check `xcodebuild -showdestinations` and the installed runtimes, because recent Xcode versions offer no Rosetta destinations, so tests and launches may be impossible.
- **Test target**: whether it is expected to compile (CI status, known failures); otherwise the comparison is a compile check.

Record each finding with evidence and a proposed route. Build-only overrides (a deployment target raised in the generated `Pods` project, or `IPHONEOS_DEPLOYMENT_TARGET=<version>` on the `xcodebuild` command line) need the developer's approval, change no tracked file, and make a build that must never ship; with a raised app target the compiler no longer checks the real minimum, so availability of new code is checked by hand. Name the lasting fix (update the dependency, fix the Podfile) as a team follow-up.

### Baseline

A baseline shows what already fails before a change, so later failures can be attributed. Build it from unchanged code before writing any change: record HEAD and a clean `git status`, and never edit tracked files while a baseline build runs. To rebuild the baseline later, set the changes aside with a patch round trip (`git diff --binary > <patch>`, `git checkout -- .` and move new files out of the tree, build, then `git apply <patch>` and move them back); `git stash` is shared between worktrees, so avoid it there. Launch the app once on a simulator as a smoke test. When the test target does not compile, record the errors and compare `build-for-testing` results instead of test runs.

## Reporting

Report each relevant capability as:

- `available`: native Xcode route or accepted optional provider used;
- `fallback`: command-line or company fallback used;
- `unavailable`: the route was tried or confirmed missing, with the observed reason, such as "no Xcode tools in this session", not a guessed cause; a route that was not attempted is reported as not run, never as `unavailable`;
- `not-required`: irrelevant to this task.

For automation, distinguish `simulator-verified`, `device-verified`, and `device-not-run: <reason>`. Physical-device operations require prior trust, Developer Mode, valid signing, and explicit project/tool capability. Never manage credentials, certificates, profiles, trust, passcodes, biometrics, or device-management controls.

GitHub operations remain in generic `aimate` and use its saved `gh` route. Do not reimplement them here.
