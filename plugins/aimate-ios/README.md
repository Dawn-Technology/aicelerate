# aimate-ios

Native iOS specialist skills for Swift projects, as an add-on to `aimate`. The review skills (`review-ios`, `review-architecture-ios`) are layers on top of `aimate`'s review skills: they run the generic review and add iOS depth to it, instead of keeping their own copy. The audit skills return findings in the output format of `aimate`'s `code-review`. The plugin keeps company policy small, uses native Xcode tooling first, and composes a few optional third-party skills where they add depth.

## Status

Version 0.1 pilots nine skills, each evaluated on real projects before it was added. Most are read-only. The two that change code, `fix-localization-ios` and `raise-minimum-ios`, first scan and present a plan, and only change files after the developer confirms, on a new branch, without committing. Feature implementation, physical-device testing, and visual SwiftUI capabilities are planned only after independent skill evaluations.

## Install

Install `aimate` and `aimate-ios` from the `aicelerate` marketplace: `aimate-ios` requires `aimate`, and its review skills stop with a message when `aimate` is missing. Other departments can continue installing only `aimate`.

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

| Skill | Use it to | Changes |
| --- | --- | --- |
| `review-ios` | Review a pull request or local changes with `aimate`'s review, plus iOS depth | Nothing (comments only when asked) |
| `test-ios` | Run the tests affected by a change, or named tests, on a simulator | Nothing |
| `security-audit-ios` | Audit a whole project for security problems against OWASP MASVS | Nothing |
| `accessibility-audit-ios` | Validate a whole app's accessibility against WCAG 2.2 A and AA | One report file in `docs/`; a temporary UI test only after confirmation |
| `fix-localization-ios` | Find and fix localization problems | Code and string catalogs, after confirmation |
| `raise-minimum-ios` | Raise the minimum iOS version and remove code for older versions | Code and project files, after confirmation |
| `migrate-swiftui-ios` (alpha) | Convert UIKit screens to SwiftUI, with a time and token estimate; use at your own risk | A plan in `docs/`; code and project files after approval |
| `review-architecture-ios` | Review architecture and design quality, with a refactoring roadmap | One report file in `docs/` |
| `summarize-project-ios` | Get an overview, gotchas, and risks of a project | Nothing |

Ask for a skill by name. In Claude Code you can also use `/aimate-ios:<skill>`.

### `review-ios`

Review of Swift and native iOS changes as a layer on top of `aimate`. It runs `aimate`'s `review-pr` (for a pull or merge request) or `review-local` (for local changes), which review through `code-review`, and adds iOS depth to that same review: the project's iOS baseline (deployment target, frameworks, architecture), the iOS checks for each module the change touches (Swift, concurrency, SwiftUI, UIKit, accessibility, localization, security, compatibility, tests), the company `ios-standards`, and a build and test run through Xcode. It passes these to `code-review` as its `review_baseline`, `focus_areas`, and `constraints`, so there is one review with one set of findings, severities, and comments, and fixes to `aimate`'s review apply to iOS reviews automatically.

Generic `aimate` review skills never call `review-ios`, so teams that do not build iOS apps are unaffected. Run it in one of two ways:

- **Manually**: ask for an iOS review, for example "run review-ios on this branch".
- **Per project**: add this block to the project's `AGENTS.md`, ideally in the company iOS template so new projects get it automatically.

```markdown
<!-- aimate-ios:start -->
## aimate-ios

- Architecture: TCA <!-- or: MVVM + Coordinators -->
- When a review includes Swift or Xcode project files, run it through `review-ios` from `aimate-ios`, which runs the generic review with iOS depth added.
<!-- aimate-ios:end -->
```

### `test-ios`

Builds and runs tests on a simulator and reports what ran: the tests affected by a change, a named test, class, target, or test plan, or the full suite. It uses the project's own build and test commands first, then Xcode MCP or `xcodebuild`. When no test covers a change, it says so and builds the affected scheme instead. It never edits source or test files and never fixes failing tests.

Ask for it by name, for example "run test-ios for the tests affected by my last commit".

### `security-audit-ios`

Read-only security audit of a whole iOS project, for example when taking over a legacy project or before a release. It checks every area in the company security reference (secrets, Keychain, client-only checks, transport, deep links and web content, pasteboard and keyboards, analytics, debug features, privacy manifests, dependencies, and CI) per target, plus the OWASP MASTG iOS tests that can be checked from source. It decides which MAS profiles apply (L1 and privacy always, L2 when the app handles sensitive data such as accounts, payments, or health data, resilience only when the project asks for it) and reports a status per OWASP MASVS 2.1 control. It traces each hit to who can reach it and reports with the same severity labels and output shape as `review-ios`, with the MASVS control and MASTG test on every finding. MASTG tests that need a running app or the built IPA are listed as not checked. The only outside call is an optional advisory lookup of the pinned package versions, made only when allowed. It never edits, builds, or runs anything and redacts secret values. For security review of a single change, `review-ios` already includes a Security module.

Ask for it by name, for example "run security-audit-ios on this project".

### `accessibility-audit-ios`

Validates the accessibility of a whole iOS app against WCAG 2.2 Level A and AA, applied to native screens as the W3C's mobile guidance (WCAG2Mobile) describes, and marks which failures fall under WCAG 2.1 AA, the baseline of EN 301 549 and the European Accessibility Act. First it scans the repository read-only: it lists the screens, checks every criterion in the company accessibility reference (VoiceOver labels and traits, Dynamic Type and clipping, contrast from asset-catalog colors, touch targets, focus, gestures, forms and sign-in, media captions, status announcements), and writes an untracked report to `docs/` with a status per criterion, findings per screen, and the checks a person still has to do with VoiceOver or a keyboard. Bundled scripts check that the report has exactly one status per criterion and compute contrast from asset-catalog colors in light and dark appearance. Then it offers a thorough check: on a new branch, it adds a temporary XCUITest that runs Apple's automated accessibility audit (`performAccessibilityAudit()`, iOS 17 and later) on the main screens at the default and largest text size, in light and dark appearance, and updates the report. It never commits. For accessibility review of a single change, `review-ios` includes an Accessibility module.

Ask for it by name, for example "run accessibility-audit-ios on this project".

### `fix-localization-ios`

Finds and fixes localization problems across a whole iOS project in three phases. First it scans read-only: the languages the app actually supports, missing and unreviewed translations per catalog, every key used in code matched against the catalog of the bundle it is looked up in, text that bypasses localization, values in the wrong language, plurals and concatenated sentences, locale-aware formatting, permission texts, and extensions. Then it presents a fix plan per category with each item's text before and after, and stops. After the developer approves, it fixes the approved items on a new branch, edits String Catalogs through a bundled script that keeps Xcode's exact file format, marks every translation it wrote as `needs_review` for a translator, and builds. It never commits. Stopping after the plan gives a localization audit in the same shape as `review-ios`; for localization review of a single change, `review-ios` includes a Localization module.

Ask for it by name, for example "run fix-localization-ios on this project".

### `raise-minimum-ios`

Raises the app's minimum iOS version, for example from iOS 16 to 18, and removes what only existed for the older versions. It works in three phases:

1. **Scan** (read-only): current minimums per target and package, every `#available`/`@available` check classified by a bundled script (always true at the new minimum, backport wrapper, or still needed), backport modules and packages that become unused, migrations the new minimum forces (for example Perception to Observation at iOS 17), new deprecation warnings, and documents and scripts that state the old minimum.
2. **Plan**: a short summary followed by numbered steps, what stays unchanged and why, follow-ups it will not do (optional modernizations such as `ObservableObject` to `@Observable`, removing legacy extensions), the verification plan, and the branch with its base. It then stops for the developer's choice: all steps, selected steps, or stop.
3. **Execute**: on a new branch, never committing. It builds and runs the tests before changing anything, builds after each step, and compares tests and warnings afterwards. Targets already above the new minimum and other platforms are left alone; when the build needs a change outside the confirmed steps, it stops and asks.

Ask for it by name, for example "use raise-minimum-ios to raise this app to iOS 18".

### `migrate-swiftui-ios` (alpha)

> **Alpha: use at your own risk.** Tested on scans and plans of two apps and one pilot conversion that built but could not be run on the test machine. Review every change before merging, and treat its time and token estimates as rough until more pilots have been measured.

Converts a UIKit app, or most of its screens, to SwiftUI. It scans the project with a bundled script (view controllers with a complexity class, storyboard scenes and XIBs, UIKit-only APIs such as maps, cameras, and custom layouts, existing SwiftUI, and the app lifecycle) and writes a plan to `docs/`: per screen a decision (convert, convert with a wrapper, keep UIKit, or remove), the order of batches, and an estimate of agent time, developer review time, and tokens. It then goes through the plan with the developer to agree what is feasible, including whether to convert navigation and the app lifecycle and whether it may commit per batch. After approval it converts on a new branch, screen by screen, keeping each converted screen inside the existing navigation, keeping accessibility identifiers and localization keys, and building and testing after every batch. After a pilot batch it measures the real tokens and time, corrects the estimate, and asks to continue. It ends with what was converted, what was not and why, and the tokens used: in Claude Code read from the session transcript by a bundled script, on other hosts from the host's own usage view. It never pushes.

Ask for it by name, for example "run migrate-swiftui-ios on this project".

### `review-architecture-ios`

iOS layer on top of `aimate`'s `review-architecture`, which it loads by skill name (it stops with a message when `aimate` is missing): the same churn-first method, severities, roadmap, and report in `docs/`, with what the generic version cannot do for iOS. Two bundled scripts read the Swift module graph (package targets, declared dependencies, actual imports, app target links) and iOS platform health (deployment targets, Swift language settings, branch-pinned packages, `Package.resolved` drift, availability code) without writing to the repo. iOS rules cover TCA and MVVM + Coordinators layer mapping and signals such as hand-written `Equatable` that hides state from `TestStore`, side effects outside dependencies, and feature flags read in views. Uses `aimate`'s scripts and report template when `aimate` is installed and a condensed method otherwise. All scripts run with `xcrun python3`, the Python 3.9 that Xcode ships, so nothing extra needs installing. Writes one untracked report file; never edits source.

Ask for it by name, for example "run review-architecture-ios on this project".

### `summarize-project-ios`

Read-only overview of an iOS project for a developer joining and a tech lead assessing it. The onboarding part covers what the app is, its structure, numbered steps from a fresh clone to a running app, and the gotchas: instruction files that disagree with the project, broken links, private package access, files that come from CI or the team, required tools, which backend each configuration uses, scheme surprises, and lockfile drift. The assessment part covers strengths, hotspots from git history, the main risks and debt, and which specialist skills to run next. It labels every claim that is inferred rather than read from a file.

Ask for it by name, for example "run summarize-project-ios on this project".

### `ios-standards`

Internal company-policy foundation used by the user-facing iOS skills. It is not a replacement for official Apple or maintained community guidance.

## Xcode Tools

The skills work through Xcode itself, and need Xcode 27 or later running. They use Xcode's built-in MCP tools for builds, tests, compiler diagnostics, previews, and documentation search. To operate the app on a simulator, for example to reproduce a QA ticket, ask the agent in Xcode 27 directly; no plugin skill is needed. When the project is not open yet, the skills open it in Xcode, and they switch the scheme, test plan, or run destination back when they changed it. Without Xcode they fall back to `xcodebuild` for builds and tests. Add `xcrun mcpbridge` as a stdio MCP server in your agent host, for example:

```bash
claude mcp add xcode -- xcrun mcpbridge
```

Xcode may ask you to allow the agent's connection. The skills use Xcode MCP only to read, build, test, and search documentation, never its file-editing tools; the skills that change code edit files directly on their own branch after the developer confirms.

## Optional Capability Providers

See the [`capability providers` reference](skills/ios-standards/references/capability-providers.md). Optional providers add review depth; their absence never prevents static review.

Projects should record approved providers and project-specific architecture or toolchain rules in `AGENTS.md`. Explicit project policy and actual Xcode settings outrank company defaults.

## Scope

V1 excludes signing changes, provisioning, certificates, archives, TestFlight, App Store Connect, release automation, physical devices, and incidental architecture migrations. No skill commits or pushes; reviewing and committing changes stays with the developer.
