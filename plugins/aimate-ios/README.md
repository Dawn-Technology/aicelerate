# aimate-ios

Optional native iOS specialist skills that work standalone and compose with `aimate` when its generic delivery or review workflows are installed. The plugin keeps company policy small, uses native Xcode tooling first, and composes a few optional third-party skills where they add depth.

## Status

Version 0.1 pilots `review-ios`. Implementation, simulator/device testing, and visual SwiftUI capabilities are planned only after independent skill evaluations.

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

### `ios-standards`

Internal company-policy foundation used by the user-facing iOS skills. It is not a replacement for official Apple or maintained community guidance.

## Xcode Tools

When Xcode is open with the project, the skills use Xcode's built-in MCP tools first for builds, tests, compiler diagnostics, previews, and documentation search. Add `xcrun mcpbridge` as a stdio MCP server in your agent host, for example:

```bash
claude mcp add xcode -- xcrun mcpbridge
```

Xcode may ask you to allow the agent's connection. Read-only skills such as `review-ios` never use Xcode's file-editing tools.

## Optional Capability Providers

See the [`capability providers` reference](skills/ios-standards/references/capability-providers.md). Optional providers improve depth or execute builds and automation; their absence never prevents static review. When using `MobileBuildMCP` on client work, set `MOBILEBUILDMCP_SENTRY_DISABLED=true` to turn off its error telemetry.

Projects should record approved providers and project-specific architecture or toolchain rules in `AGENTS.md`. Explicit project policy and actual Xcode settings outrank company defaults.

## Scope

V1 excludes signing changes, provisioning, certificates, archives, TestFlight, App Store Connect, release automation, and incidental architecture migrations.
