---
name: fix-localization-ios
description: Use when the user asks to check or fix localization across a whole iOS app, such as missing or wrong translations, text that bypasses localization, wrong-bundle lookups, plurals, and date or number formatting. Scans first and presents what it will fix; changes code and string catalogs only after the developer approves, on a new branch, without committing. Stopping after the scan gives a localization audit. For localization review of a single change, use review-ios instead.
metadata:
  author: "Dawn Technology"
  version: 0.2.0
  role: "localization-fix"
  writes_source: "true"
  external_dependencies: "none"
---

# Fix Localization iOS

Find what users of each supported language actually see wrong, present the fixes, and apply them after the developer approves. Work in three phases: scan, plan with approval, fix. Never change a file before the developer approves. It does not judge on-screen layout.

## Policy

Always read these shared references:

- [`../ios-standards/references/localization.md`](../ios-standards/references/localization.md)
- [`../ios-standards/references/precedence.md`](../ios-standards/references/precedence.md)
- [`../ios-standards/references/tooling.md`](../ios-standards/references/tooling.md) for the build in phase 3.

If a reference cannot be read, retry with another file-reading tool. If it still fails, name it and do not apply its rules from memory.

## Phase 1: Scan (read-only)

### Baseline

Check every project-instruction location listed in `precedence.md` with a file listing and read each file that exists; note supported languages, single-language decisions, tone of voice (for example informal "je" or formal "u"), terminology, and translation workflow (SwiftGen, generated symbols, an external translation service, or files exported to translators).

Determine the supported languages as `localization.md` describes and report every source and any disagreement. List the targets and packages with their catalogs or `.strings` tables.

### Inventory With Scripts

Parse the catalogs and tables with a script instead of reading them by eye: per catalog and language, the number of keys, missing entries, and states; stale keys; duplicate keys in `.strings`; and values whose language does not match. Then extract every key looked up in code per module with its bundle argument and match it exactly against that bundle's catalog. Keep these scripts outside the repository and name where they are.

### Check Every Area

Work through every row of the `localization.md` Checks table over tracked sources (`git ls-files`, `git grep`). Exclude logs, debug menus compiled out of release, previews, tests, and third-party packages. Stay within localization; report unrelated problems at most as a one-line note.

### Trace Before Classifying

For each hit, establish which users see it (which supported language), on which screen or path, and whether that path is reachable in release builds. Classify with the `localization.md` severity table. A single-language product is judged against its own decision, not company defaults; when no decision is recorded, say so and ask in the plan.

## Phase 2: Plan and Approve

Present the findings as a fix plan and stop. Open with a short summary that a developer can decide from without reading further, at most about ten lines:

- the supported languages and any decision the team must make first;
- per fix category, one line with the number of items and one example of what users see now and after;
- the open questions;
- your recommended selection and the base branch.

Then give the details in these sections:

- `Baseline`: instruction files and rules applied, supported languages with sources, catalogs, tone and terminology.
- `Inventory`: per catalog or table and language: keys, missing, `needs_review`, `new`, stale.
- `Fixes`: numbered categories, each with every item (`file:line`, language, what users see now, what it will say after), so the developer can approve item by item if needed:
  1. Lookups that miss: wrong bundle, missing `bundle: .module`, keys that differ from the catalog (spaces, non-breaking spaces, punctuation).
  2. Wrong values: text in the wrong language, typos, placeholder or test copy, stray characters.
  3. Missing translations: per language, the keys and the proposed translation.
  4. Text outside localization: user-facing literals moved into the module's catalog.
  5. Plurals and sentences: plural variations, and concatenated fragments replaced by one format string.
  6. Formatting: fixed date, number, and unit formats replaced with locale-aware APIs.
  7. Catalog hygiene: stale and unused keys, duplicate keys, empty entries.
- `Questions`: decisions only the team can make (for example whether the app is single-language, or terminology choices).
- `Not fixed`: findings left alone and why (server-delivered text, layout, product decisions).
- `Verification`: the build to run and what cannot be verified statically.
- `Branch`: the branch name to create, for example `chore/fix-localization`, and its base branch.

Agent-written translations follow the project's tone and terminology and are marked `needs_review`, so a translator or native speaker checks them before release. Ask the developer to choose: all categories, selected categories or items, or stop. When the developer stops here, or asked only for an audit, return the plan as the audit report followed by the YAML shape from [`../review-ios/SKILL.md`](../review-ios/SKILL.md) section "6. Return Compatible Output" (read that section; `category: documentation` for wrong or missing text, `maintainability` for hygiene; "whole-project localization audit" in `summary.scope`).

## Phase 3: Fix (after approval)

1. Require a clean working tree; if it is not clean, stop and say so. Create the branch from the confirmed base. Never commit or push.
2. Edit String Catalogs only through [`scripts/xcstrings.py`](scripts/xcstrings.py) (`xcrun python3 scripts/xcstrings.py set|delete|rename-key|check`), so files keep Xcode's exact format and diffs stay small. Run `check` on every catalog before editing; if one does not round-trip, report it and edit it in Xcode format by hand with the smallest possible change.
3. Translations written by the agent get state `needs_review` in String Catalogs; in `.strings` files add a `/* needs review */` comment above the line. Values the developer supplied or confirmed get `translated`.
4. When moving text into a catalog or fixing a lookup in package code, pass `bundle: .module` (or the module's own resource accessor) and add the key to that module's catalog with every supported language.
5. When the project generates code from strings (SwiftGen `L10n`), run its documented generation command after editing the tables, and report if it cannot run.
6. When a fix needs a change outside the approved items, stop and ask.
7. Build the affected schemes with the `tooling.md` route, and run the tests when the project has them. Run `xcstrings.py check` on every catalog you changed.

## Report

End with:

- `Changes`: per category, the items fixed, with files.
- `Needs review`: every translation written by the agent, per language, for a translator.
- `Not changed`: with reasons, and any questions still open.
- `Verification`: build and test results, catalog checks, and what was not verified (layout, truncation, VoiceOver); suggest `drive-ios` with a `capture` per language for a visual check.
- `Git`: the branch, that nothing is committed, and the changed-file count.

## Final Check

Before returning, confirm:

- supported languages are stated with their sources, and keys used in code were matched exactly against each lookup's bundle;
- nothing was changed before approval, and only approved items were fixed;
- catalogs were edited through `xcstrings.py` and still round-trip, and agent translations are marked `needs_review`;
- work happened on a new branch, nothing was committed or pushed, and the build ran.
