# Summarize Project iOS Evaluation Results

Evaluated 2026-10-19 in Claude Code using general-purpose subagents on real local checkouts, static only. Each prompt in `evals.json` ran once without the skill (baseline) and once with `../SKILL.md`. The expected outcomes list gotchas already known from earlier sessions, so a run can be checked against them.

## Reproduce

1. Use the checkouts below.
2. Start a fresh agent per prompt without the skill, instructed to summarize read-only for a developer joining and a tech lead.
3. Start a fresh agent per prompt that loads `../SKILL.md` and every file it links, without reading this folder.
4. Check each result against the known gotchas and shared criteria in `evals.json`.

## Baseline Pattern

All three baselines were long, well-informed reports with real findings, but each turned into a full code review (security, localization, reducer details) instead of a summary that points to the specialist skills. Each missed cheap, mechanical gotchas: NPO's private SSH packages and broken instruction symlinks (the baseline even repeated `copilot-instructions.md` as working), KNMI's Debug default to the production API, and Thuisarts's Debug-scheme archive. Verified facts and inferences were mixed, and only two of three used git history for hotspots.

## KNMI (eval 1)

`knmi-app-ios` `develop` at `455f7add`; no project instructions.

With the skill, the run checked every README claim against the project and this machine, found all known gotchas including the Debug default to the production API (`AppRemoteConfigClient.swift:304`), the KMP JDK and submodule setup, the injected feedback secret, branch-pinned forks, and the unbuildable macOS, tvOS, and watchOS targets. New: the CellWarn extension's iOS 26.5 deployment target against the app's iOS 15. Hotspots came from six months of git history; specialist skills were recommended instead of audited.

## NPO Start (eval 2)

`npo-start-ios` `develop` at `e990b44420`; `AGENTS.md`.

With the skill, the run found five broken links (instruction and skill symlinks), listed private SSH packages and the submodule with the access a newcomer needs, the gitignored xcconfigs and the CI-only `ACC-RELEASE.xcconfig`, and every `AGENTS.md` and README value that has drifted. New: the PROD schemes run Debug builds against the production backend and analytics, CI's "Debug DEV" uses the ACC config, and `Gemfile.lock` is empty.

## Thuisarts (eval 3)

`thuisarts-ios` `bugfix/TAA-0002-broken-searchbar` at `13a6f42`; only `.github/copilot-instructions.md`.

With the skill, the run checked each concrete claim in the Copilot instructions (four drifts), found all known gotchas with verified or inferred labels, and left security details to `security-audit-ios` (ATS appears only through that pointer). It named the author behind most recent commits as a knowledge-concentration risk.

## Change After Evaluation

`SKILL.md` now reports knowledge concentration as counts and shares without naming individuals. Not re-evaluated.
