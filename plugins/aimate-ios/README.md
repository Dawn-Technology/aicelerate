# aimate-ios

Optional native iOS specialist skills that work standalone and compose with `aimate` when its generic delivery or review workflows are installed. The plugin keeps company policy small, uses native Xcode tooling first, and composes a few optional third-party skills where they add depth.

## Status

Version 0.1 pilots `review-ios`, `security-audit-ios`, `localization-audit-ios`, and the simulator-only `test-ios` and `drive-ios`. Implementation, physical-device testing, and visual SwiftUI capabilities are planned only after independent skill evaluations.

## Install

Install `aimate-ios` from the `aicelerate` marketplace. Install `aimate` separately when the project also needs its generic SDLC workflows. Other departments can continue installing only `aimate`.

```bash
copilot plugin install aimate-ios@aicelerate
claude plugin install aimate-ios@aicelerate
```

### OpenCode

OpenCode reads the same portable `SKILL.md` files. Add this plugin's skills directory to the project or global configuration:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "skills": {
    "paths": ["/absolute/path/to/aicelerate/plugins/aimate-ios/skills"]
  }
}
```

OpenCode loads configuration at startup; restart it after changing the path or skill files.

Alternatively, install or symlink the skill folders into `.opencode/skills/`, `~/.config/opencode/skills/`, or a shared `.agents/skills/` directory.

### Codex and other Agent Skills hosts

Install or symlink the individual skill folders into the host's Agent Skills directory. The user-facing skills use standard `SKILL.md` frontmatter and do not depend on Claude-specific hooks. Keep the complete `aimate-ios/skills` tree together so relative references resolve.

## Skills

### `review-ios`

Read-only specialist review for Swift and native iOS code. It applies project precedence, checks iOS-specific risk areas, composes optional specialist skills when available, and returns findings compatible with generic `aimate` review workflows.

Generic `aimate` review skills never call `review-ios`, so teams that do not build iOS apps are unaffected. Run it in one of two ways:

- **Manually**: ask for an iOS review, for example "run review-ios on this branch".
- **Per project**: add this block to the project's `AGENTS.md`, ideally in the company iOS template so new projects get it automatically.

```markdown
<!-- aimate-ios:start -->
## aimate-ios

- Architecture: TCA <!-- or: MVVM + Coordinators -->
- When a review includes Swift or Xcode project files, also run `review-ios` from `aimate-ios` and merge its findings with the generic review.
<!-- aimate-ios:end -->
```

### `test-ios`

Builds and runs tests on a simulator and reports what ran: the tests affected by a change, a named test, class, target, or test plan, or the full suite. It uses the project's own build and test commands first, then Xcode MCP, `MobileBuildMCP`, or `xcodebuild`. When no test covers a change, it says so and builds the affected scheme instead. It never edits source or test files and never fixes failing tests.

Ask for it by name, for example "run test-ios for the tests affected by my last commit".

### `drive-ios`

Operates the app on a simulator towards a goal and reports the steps with evidence: `reproduce` a QA ticket or crash, `validate` that a flow works, or `capture` screenshots of screens. It builds the app, reaches screens through deep links or `MobileBuildMCP` UI automation, collects screenshots, crash reports, and logs, and restores the simulator afterwards. It never edits source. Physical devices and live client demos are not supported yet.

Ask for it by name and paste the ticket, for example "use drive-ios to reproduce this QA ticket: …".

### `security-audit-ios`

Read-only security audit of a whole iOS project, for example when taking over a legacy project or before a release. It checks every area in the company security reference (secrets, Keychain, client-only checks, transport, deep links and web content, analytics, debug features, privacy manifests, dependencies, and CI) per target, traces each hit to who can reach it, and reports with the same severity labels and output shape as `review-ios`. It never edits, builds, or runs anything and redacts secret values. For security review of a single change, `review-ios` already includes a Security module.

Ask for it by name, for example "run security-audit-ios on this project".

### `localization-audit-ios`

Read-only localization audit of a whole iOS project. It determines the languages the app actually supports, counts missing and unreviewed translations per catalog, matches every key used in code against the catalog of the bundle it is looked up in, and checks text that bypasses localization, values in the wrong language, concatenated sentences and plurals, locale-aware formatting, permission texts, and extensions. It reports with the same severity labels and output shape as `review-ios`. It does not judge on-screen layout; for localization review of a single change, `review-ios` includes a Localization module.

Ask for it by name, for example "run localization-audit-ios on this project".

### `ios-standards`

Internal company-policy foundation used by the user-facing iOS skills. It is not a replacement for official Apple or maintained community guidance.

## Xcode Tools

When Xcode is open with the project, the skills use Xcode's built-in MCP tools first for builds, tests, compiler diagnostics, previews, and documentation search. Add `xcrun mcpbridge` as a stdio MCP server in your agent host, for example:

```bash
claude mcp add xcode -- xcrun mcpbridge
```

Xcode may ask you to allow the agent's connection. Read-only skills such as `review-ios` never use Xcode's file-editing tools.

## Optional Capability Providers

By default the `MobileBuildMCP` server only exposes its build and simulator tools. `drive-ios` also needs UI automation and debugging, so enable those workflows when adding the server:

```bash
claude mcp add -s user mobilebuildmcp \
  -e MOBILEBUILDMCP_SENTRY_DISABLED=true \
  -e MOBILEBUILDMCP_ENABLED_WORKFLOWS=simulator,ui-automation,debugging \
  -- mobilebuildmcp mcp
```

For OpenCode, add the same under `mcp` in `opencode.json`:

```json
"mobilebuildmcp": {
  "type": "local",
  "command": ["mobilebuildmcp", "mcp"],
  "environment": {
    "MOBILEBUILDMCP_SENTRY_DISABLED": "true",
    "MOBILEBUILDMCP_ENABLED_WORKFLOWS": "simulator,ui-automation,debugging"
  }
}
```

Without UI automation, `drive-ios` stops and says so instead of taking another route through the app.

See the [`capability providers` reference](skills/ios-standards/references/capability-providers.md). Optional providers improve depth or execute builds and automation; their absence never prevents static review. When using `MobileBuildMCP` on client work, set `MOBILEBUILDMCP_SENTRY_DISABLED=true` to turn off its error telemetry.

`MobileBuildMCP` keeps a separate build cache and test products per project under `~/Library/Developer/MobileBuildMCP/workspaces/`. The first review of a project is a full build, and one project can take tens of gigabytes (about 18 GB for a mid-sized TCA app). Check and clean it from the project directory:

```bash
mobilebuildmcp purge --scope workspace --report
mobilebuildmcp purge --scope workspace --workspace-key <key> --classes derivedData,logs,resultBundles,testProducts,stateTransients --delete --confirm delete-mobilebuildmcp-storage
```

Because `MobileBuildMCP` resolves packages in that separate workspace, projects with private packages fetched over SSH may fail to resolve there ("Repository not found"). The skills then fall back to `xcodebuild`.

The `<key>` is the folder name shown by `--report`. `--classes all` keeps the build cache; list `derivedData` explicitly to remove it as well.

Projects should record approved providers and project-specific architecture or toolchain rules in `AGENTS.md`. Explicit project policy and actual Xcode settings outrank company defaults.

## Scope

V1 excludes signing changes, provisioning, certificates, archives, TestFlight, App Store Connect, release automation, and incidental architecture migrations.
