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

1. Xcode MCP (`xcrun mcpbridge`) when Xcode is open with the project: `BuildProject`, `GetBuildLog`, `XcodeListNavigatorIssues`, `XcodeRefreshCodeIssuesInFile`, `GetTestList`, `RunSomeTests`, `RunAllTests`, and `RenderPreview`. It uses the active scheme and test plan; report which ones.
2. `MobileBuildMCP` when installed: builds and tests without Xcode open, and simulator control.
3. `xcodebuild` and `xcrun simctl`.
4. Static inspection, naming what was not run.

Before using Xcode MCP, call `XcodeListWindows` and confirm that an open workspace belongs to the reviewed repository. When Xcode is not running, exposes no tools, or has only other projects open, report Xcode MCP as `unavailable` with the reason and use the next route. Never build or test another project.

To use `MobileBuildMCP`, first call `session_set_defaults` with the project or workspace, the app scheme whose test plan contains the affected tests, and a simulator; then call `build_sim` and `test_sim`, passing `-only-testing:<Target>/<Class>/<test>` in `extraArgs`. Tests in a local Swift package usually run through the app scheme's test plan; a test missing from the scheme list does not make this route unavailable until the app scheme has been tried.

`MobileBuildMCP` keeps its own DerivedData and test products per project under `~/Library/Developer/MobileBuildMCP/workspaces/`, so its first run is a full build and the storage can reach tens of gigabytes. Do not purge it during a run; the developer cleans it with `mobilebuildmcp purge`. Developers easily miss this extra cache, so after any run that used `MobileBuildMCP`, measure the project's workspace (`du -sh ~/Library/Developer/MobileBuildMCP/workspaces/<project>-*`) and state its size in the report. When it is larger than 10 GB, add a reminder that it can be cleaned, with the commands from the plugin README ("Optional Capability Providers"). Because it resolves packages in that separate workspace, private packages fetched over SSH can fail with "Repository not found"; report that as `unavailable` and use the next route.

When Xcode MCP builds but tests return no results, the active run destination may not be a simulator. Report that and use the next route for tests.

For `xcodebuild`, reuse the project's existing DerivedData when Xcode is not building, so the run is incremental and already-fetched private packages are reused. Use a separate `-derivedDataPath` only when Xcode is building the same project; create it with a unique name (`mktemp -d`), delete only that folder after the run, and never delete a folder this run did not create. When the change does not touch `Package.resolved` or `Package.swift`, add `-skipPackageUpdates -disableAutomaticPackageResolution` so the run does not refetch packages; a fresh package fetch can fail on private SSH repositories this machine cannot read.

Pass `-collect-test-diagnostics never` to test runs: after a failure, the default diagnostics collection can wait 10 minutes for the simulator, and failure details come from the result bundle instead. Pass `-resultBundlePath` with a unique temporary path and read counts and failures with `xcrun xcresulttool get test-results summary --path <bundle> --compact` (`tests` and `test-details` for more). Delete the bundle afterwards unless the user wants it.

Read-only skills use only Xcode MCP tools that read, build, test, report diagnostics, render previews, or search documentation. They never call `XcodeWrite`, `XcodeUpdate`, `XcodeMV`, `XcodeRM`, or `XcodeMakeDir`.

## Reporting

Report each relevant capability as:

- `available`: native Xcode route or accepted optional provider used;
- `fallback`: command-line or company fallback used;
- `unavailable`: the route was tried or confirmed missing, with the observed reason, such as "no Xcode tools in this session", not a guessed cause; a route that was not attempted is reported as not run, never as `unavailable`;
- `not-required`: irrelevant to this task.

For automation, distinguish `simulator-verified`, `device-verified`, and `device-not-run: <reason>`. Physical-device operations require prior trust, Developer Mode, valid signing, and explicit project/tool capability. Never manage credentials, certificates, profiles, trust, passcodes, biometrics, or device-management controls.

GitHub operations remain in generic `aimate` and use its saved `gh` route. Do not reimplement them here.
