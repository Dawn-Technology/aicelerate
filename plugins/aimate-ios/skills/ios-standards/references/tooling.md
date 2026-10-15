# Tool and Host Resolution

Resolve capabilities, not brand-specific command names:

1. Honor a route explicitly selected by the user or project.
2. Use an accepted optional specialist already available.
3. Use native host/Xcode integration.
4. Use an approved local command-line route.
5. Perform static inspection and report unexecuted verification.

OpenCode, Claude Code, Codex, and GitHub Copilot are supported skill hosts. Tool availability differs; never claim a build, test, launch, screenshot, simulator, or device check that did not execute.

Report each relevant capability as:

- `available`: accepted optional provider used;
- `fallback`: native or company fallback used;
- `unavailable`: execution could not be performed, with reason;
- `not-required`: irrelevant to this task.

For automation, distinguish `simulator-verified`, `device-verified`, and `device-not-run: <reason>`. Physical-device operations require prior trust, Developer Mode, valid signing, and explicit project/tool capability. Never manage credentials, certificates, profiles, trust, passcodes, biometrics, or device-management controls.

GitHub operations remain in generic `aimate` and use its saved `gh` route. Do not reimplement them here.
