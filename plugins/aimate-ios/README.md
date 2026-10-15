# aimate-ios

Optional native iOS specialist skills that work standalone and compose with `aimate` when its generic delivery or review workflows are installed. The plugin keeps company policy small and prefers suitable third-party skills and native tooling for framework-specific knowledge and automation.

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

### `ios-standards`

Internal company-policy foundation used by the user-facing iOS skills. It is not a replacement for official Apple, Point-Free, or maintained community guidance.

## Optional Capability Providers

See the [`capability providers` reference](skills/ios-standards/references/capability-providers.md). Optional providers improve depth or execute builds and automation; their absence never prevents static review.

Projects should record approved providers and project-specific architecture or toolchain rules in `AGENTS.md`. Explicit project policy and actual Xcode settings outrank company defaults.

## Scope

V1 excludes signing changes, provisioning, certificates, archives, TestFlight, App Store Connect, release automation, and incidental architecture migrations.
