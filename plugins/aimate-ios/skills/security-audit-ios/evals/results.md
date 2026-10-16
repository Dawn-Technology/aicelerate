# Security Audit iOS Evaluation Results

Evaluated 2026-10-16 in Claude Code using general-purpose subagents on real local checkouts, static only. Each prompt in `evals.json` ran once without the skill (baseline) and once with `../SKILL.md`.

## Reproduce

1. Use the checkouts below.
2. Start a fresh agent per prompt without the skill, instructed to audit read-only and redact secrets.
3. Start a fresh agent per prompt that loads `../SKILL.md` and follows it exactly, without reading this folder.
4. Check each result against the expected outcome in `evals.json`.

## Baseline Pattern

All three baselines found real, project-specific issues: the shipped feedback HMAC secret and release-reachable config editor in KNMI, the device-only parental PIN and release secrets in PR builds in NPO Start, and the app-wide ATS exception, bundled API key, and health searches in analytics in Thuisarts. They differed in what they checked, used their own Medium/Low scales, did not read project instructions, and only one checked the privacy manifest. Their recurring finding types (client-only enforcement, app lock on foreground, server-supplied links and remote config, analytics data, debug features in release, dependencies and CI) were added to `security.md`, which `review-ios` also uses.

## KNMI (eval 1)

`knmi-app-ios` `develop` at `455f7add`; no project instructions; no accounts.

With the skill, the run listed seven targets with their entitlements and privacy-manifest membership, covered every `security.md` area, and marked Keychain, biometrics, web content, analytics, and app lock as not applicable with the search used. Beyond the baseline it found the incomplete privacy manifest and that remote config can enable mock weather data in release builds. It used company severities and separated CI findings. Its YAML did not follow `review-ios`, because the skill named the shape without linking it.

## NPO Start (eval 2)

`npo-start-ios` `develop` at `e990b44420`; `AGENTS.md`.

With the skill, the run read `AGENTS.md`, reported the broken `.github/copilot-instructions.md` symlink and the deployment-target mismatch, audited the iOS, tvOS, and RichPush targets separately, and verified library defaults (KeychainAccess accessibility) at the pinned revisions. Beyond the baseline it found that reinstalling escapes the child lock while reusing the Keychain session, the missing explicit accessibility class, the privacy manifest gap, and the developer menu compiled into release. It read `review-ios` and returned the exact YAML shape.

## Thuisarts (eval 3)

`thuisarts-ios` `bugfix/TAA-0002-broken-searchbar` at `13a6f42`; only `.github/copilot-instructions.md`.

With the skill, the run read the Copilot instructions and applied their keep-backups rule over the company default, verified the default file-protection class in Apple documentation, and covered every area. Beyond the baseline it found that the app lock can be switched off without authentication, that hostless URLs such as `javascript:` count as internal, and that the Debug scheme archives with the Debug configuration. Its YAML had the same shape defect as KNMI.

## Change After Evaluation

`SKILL.md` now links the `review-ios` output section, requires reading it, and forbids extra fields. The NPO run, which read that section, shows the intended result; KNMI and Thuisarts were not rerun.
