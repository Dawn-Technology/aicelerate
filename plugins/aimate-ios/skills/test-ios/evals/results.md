# Test iOS Evaluation Results

Evaluated 2026-10-16 in Claude Code using general-purpose subagents on real local checkouts, with Xcode 26.6 not running and no Xcode MCP or `MobileBuildMCP` tools in the session, so every run used `xcodebuild`. Each prompt in `evals.json` ran once without the skill (baseline) and once with `../SKILL.md`.

## Reproduce

1. Check out the projects at the commits below and close Xcode.
2. Start a fresh agent per prompt without the skill; save what it ran and reported.
3. Start a fresh agent per prompt that loads `../SKILL.md` and follows it exactly, without reading this folder.
4. Check each result against the expected outcome and the shared criteria: project instructions read first, tests selected before running, no unrelated tests presented as coverage, build reported as build, every route with an exact state, counts from tool output, no source or git changes, only own folders deleted.

## KNMI: Affected Tests (eval 1)

`knmi-app-ios` `develop` at `455f7add`; the commit changes `Widgets/ForecastWidget/LocationQuery.swift`.

The baseline correctly found that no test covers the widget extension and built `WidgetsExtension`, but used a fresh DerivedData folder (a full build), reported no capability routes, and deleted a shared temporary folder that another run was using. With the skill, the run checked the instruction locations, mapped the file to `WidgetsExtension` with evidence, built it incrementally in the existing DerivedData with package updates skipped, reported every route, deleted only its own folder, and offered the full suite.

## NPO Start: Unit Tests (eval 2)

`npo-start-ios` `develop` at `e990b44420`; `AGENTS.md` present.

The baseline used the unit-test plan but first built in a fresh DerivedData folder, which failed to fetch a private SSH package; the rerun in the existing DerivedData passed (1,854 passed, 3 skipped). With the skill, the run followed the `AGENTS.md` `build-for-testing`/`test-without-building` pattern, reported the missing Xcode 26.2 and "NPO Start iPhone 17 Pro" simulator with their substitutes, reused DerivedData, read counts with `xcresulttool`, and reran the one failing test alone: it passed, so it was reported as flaky with its assertion and location. It also found that `.github/copilot-instructions.md` is a broken symlink. Its test run spent 10 minutes collecting simulator diagnostics after the failure; `tooling.md` now passes `-collect-test-diagnostics never`.

## Thuisarts: No Tests (eval 3)

`thuisarts-ios` `bugfix/TAA-0002-broken-searchbar` at `13a6f42`; only `.github/copilot-instructions.md`.

The baseline did not read the Copilot instructions, tried three test actions in fresh DerivedData before finding that every test target is commented out, and never built the branch. With the skill, the run read the instructions, confirmed from `Package.swift`, the project, and the scheme that no tests exist without trying a test action, ran the instructions' build command (succeeded), reported it as a build, not tests, and pointed to the instructions' manual iPhone and iPad check.

## Not Yet Covered

- Xcode MCP and `MobileBuildMCP` routes: Xcode was closed and no MCP tools were connected.
- A change that tests do cover, with `-only-testing` selection.
- A confirmed (non-flaky) failure.
