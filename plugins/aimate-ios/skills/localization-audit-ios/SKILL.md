---
name: localization-audit-ios
description: Use when the user asks to check whether a whole iOS app is localized correctly, such as missing translations, text that bypasses localization, wrong-bundle lookups, plurals, and date or number formatting. Read-only static audit with findings in the shared review format. For localization review of a single change, use review-ios instead.
metadata:
  author: "Dawn Technology"
  version: 0.1.0
  role: "localization-audit"
  writes_source: "false"
  external_dependencies: "none"
---

# Localization Audit iOS

Audit the whole repository against the company localization reference and report what users of each supported language actually see. This skill is read-only: it never edits files, changes git state, builds, or runs the app. It does not judge on-screen layout.

## Policy

Always read these shared references before auditing:

- [`../ios-standards/references/localization.md`](../ios-standards/references/localization.md)
- [`../ios-standards/references/precedence.md`](../ios-standards/references/precedence.md)

If a reference cannot be read, retry with another file-reading tool. If it still fails, name it in the report and do not apply its rules from memory.

## Workflow

### 1. Baseline

Check every project-instruction location listed in `precedence.md` with a file listing and read each file that exists; note supported languages, single-language decisions, tone of voice, and translation workflow (for example SwiftGen or an external translation service).

Determine the supported languages as `localization.md` describes and report every source and any disagreement. List the targets and packages with their catalogs or `.strings` tables, and whether strings are generated (SwiftGen `L10n`, generated symbols).

### 2. Inventory With Scripts

Parse the catalogs and tables with a script instead of reading them by eye: per catalog and language, the number of keys, missing entries, and states; stale keys; duplicate keys in `.strings`; and values whose language does not match. Then extract every key looked up in code per module with its bundle argument and match it exactly against that bundle's catalog. Keep the scripts outside the repository and name where they are.

### 3. Check Every Area

Work through every row of the `localization.md` Checks table over tracked sources (`git ls-files`, `git grep`). Exclude logs, debug menus compiled out of release, previews, tests, and third-party packages. Stay within localization; report unrelated problems at most as a one-line note.

### 4. Trace Before Classifying

For each hit, establish which users see it (which supported language), on which screen or path, and whether that path is reachable in release builds. Classify with the `localization.md` severity table. A Dutch-only product that leaves English values in Dutch is reported against the project's own decision, not against company defaults.

### 5. Report

Open with these sections:

- `Baseline`: project instruction files and the rules applied, supported languages with their sources and disagreements, targets and catalogs, and the references read.
- `Inventory`: per catalog or table and language, key count, missing, `needs_review`, `new`, and stale.
- `Coverage`: every `localization.md` area with its result: findings, checked without findings (with the search or script used), or not applicable.
- `Findings`: ordered by severity, each with `file:line`, the language and screen affected, what users see, and a fix direction.
- `Not checked`: layout and truncation, server-delivered text, images, and anything else outside static inspection.

Then return the YAML shape from [`../review-ios/SKILL.md`](../review-ios/SKILL.md) section "6. Return Compatible Output" exactly, with no extra fields or totals. Read that section before writing the YAML. Use `category: documentation` for missing or wrong text and `maintainability` for catalog hygiene, put "whole-project localization audit" in `summary.scope`, and put the baseline and `Not checked` items in `summary.residual_gaps`.

## Final Check

Before returning, confirm:

- project instructions were checked with a file listing, and supported languages are stated with their sources;
- keys used in code were matched exactly against the catalog of the bundle each lookup uses;
- every `localization.md` area appears in `Coverage`;
- every finding names the affected language and what users see, with a company severity label;
- nothing was edited, built, or run, and git state is unchanged.
