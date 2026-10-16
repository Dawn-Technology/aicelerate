# Localization Audit iOS Evaluation Results

Evaluated 2026-10-16 in Claude Code using general-purpose subagents on real local checkouts, static only. Each prompt in `evals.json` ran once without the skill (baseline) and once with `../SKILL.md`.

## Reproduce

1. Use the checkouts below.
2. Start a fresh agent per prompt without the skill, instructed to audit read-only.
3. Start a fresh agent per prompt that loads `../SKILL.md` and every file it links, without reading this folder.
4. Check each result against the expected outcome in `evals.json`.

## Baseline Pattern

All three baselines found real issues: the KNMI thunderstorm notification body that stays English because the code key contains a non-breaking space, wrong-bundle lookups and Dutch `en` values in Thuisarts, and duplicate keys and test copy in NPO Start. None read project instructions, all used their own High/Medium/Low scales, and the NPO run drifted into non-localization issues (formatter thread safety). The NPO baseline rated the "Dit is een test" copy High without checking whether its screen is reachable.

## KNMI (eval 1)

`knmi-app-ios` `develop` at `455f7add`; no project instructions; en and nl.

With the skill, the run found no instruction files and took the supported languages from the README, reported the nl/en source-language disagreement, inventoried 32 catalogs and three `.strings` tables with a script, and matched 745 lookups exactly against their bundles. It found everything the baseline found plus raw `Double` temperatures on the measurements map, the widget picker showing "Live", package banner labels looked up in `Bundle.main`, and orphan `.strings` tables. 17 `request-for-change` and 12 `optional`, exact `review-ios` YAML.

## NPO Start (eval 2)

`npo-start-ios` `develop` at `e990b44420`; `AGENTS.md`; Dutch only.

With the skill, the run read `AGENTS.md` (SwiftGen workflow), confirmed Dutch-only from all sources without counting the GoogleCast SDK languages, verified that the generated `L10n` matches all 653 keys, and judged findings against the Dutch-only product. Beyond the baseline it found a stray `<` in the profanity VoiceOver label and an English "Chromecast device" fallback; by tracing the feature gate it rated the "Dit is een test" copy `optional` because the screen is unreachable today.

## Thuisarts (eval 3)

`thuisarts-ios` `bugfix/TAA-0002-broken-searchbar` at `13a6f42`; only `.github/copilot-instructions.md`; en and nl declared.

With the skill, the run read the Copilot instructions and applied their per-module catalog rule, recorded that no instruction decides whether the app is Dutch-only, applied company defaults, and offered both resolutions. It matched 136 lookups, read every value for language mismatches, and covered every area with the script or search used.

## Outcome

The skill adds project instructions, supported-language determination, a scripted inventory and exact key matching on every run, reachability-based company severities, and the shared output shape. No changes were needed after evaluation.
