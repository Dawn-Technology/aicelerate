# Tool and Host Resolution

Resolve capabilities, not brand-specific command names:

1. Honor a route explicitly selected by the user or project.
2. Use native host/Xcode integration.
3. Use an accepted optional provider already available.
4. Use an approved local command-line route.
5. Perform static inspection and report unexecuted verification.

OpenCode, Claude Code, Codex, and GitHub Copilot are supported skill hosts. Tool availability differs; never claim a build, test, launch, screenshot, simulator, or device check that did not execute.

## Build and Test

1. Xcode MCP (`xcrun mcpbridge`) when Xcode is open with the project: `BuildProject`, `GetBuildLog`, `XcodeListNavigatorIssues`, `XcodeRefreshCodeIssuesInFile`, `GetTestList`, `RunSomeTests`, `RunAllTests`, and `RenderPreview`. It uses the active scheme and test plan; report which ones.
2. `MobileBuildMCP` when installed: builds and tests without Xcode open, and simulator control.
3. `xcodebuild` and `xcrun simctl`.
4. Static inspection, naming what was not run.

Read-only skills use only Xcode MCP tools that read, build, test, report diagnostics, render previews, or search documentation. They never call `XcodeWrite`, `XcodeUpdate`, `XcodeMV`, `XcodeRM`, or `XcodeMakeDir`.

## Reporting

Report each relevant capability as:

- `available`: native Xcode route or accepted optional provider used;
- `fallback`: command-line or company fallback used;
- `unavailable`: execution could not be performed, with reason;
- `not-required`: irrelevant to this task.

For automation, distinguish `simulator-verified`, `device-verified`, and `device-not-run: <reason>`. Physical-device operations require prior trust, Developer Mode, valid signing, and explicit project/tool capability. Never manage credentials, certificates, profiles, trust, passcodes, biometrics, or device-management controls.

GitHub operations remain in generic `aimate` and use its saved `gh` route. Do not reimplement them here.
