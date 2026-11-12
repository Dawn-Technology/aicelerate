---
name: security-audit-ios
description: Use when the user asks for a security audit of a whole iOS app or Swift project, for example when taking over a legacy iOS project or before an App Store release. Read-only static audit against OWASP MASVS 2.1 and the MASTG iOS tests, per Xcode target, of secrets, Keychain use, client-only checks, App Transport Security, deep links and web views, analytics, debug features, privacy manifests, SwiftPM dependencies, and CI, with a coverage status per MASVS control and reachability-checked findings in the shared review format. For security review of a single change, use review-ios instead.
metadata:
  author: "Dawn Technology"
  version: 0.2.0
  role: "security-audit"
  writes_source: "false"
  external_dependencies: "none"
---

# Security Audit iOS

Audit the whole repository against the company security reference and OWASP MASVS 2.1, using the MASTG iOS tests that can be checked from source, and report reachable problems with evidence. This skill is read-only: it never edits files, changes git state, builds, or runs the app. It complements `review-ios`, which reviews one change.

## Policy

Always read these shared references before auditing:

- [`../ios-standards/references/security.md`](../ios-standards/references/security.md)
- [`../ios-standards/references/masvs-mastg.md`](../ios-standards/references/masvs-mastg.md)
- [`../ios-standards/references/precedence.md`](../ios-standards/references/precedence.md)

Read [`../ios-standards/references/apple-docs.md`](../ios-standards/references/apple-docs.md) before a version-sensitive Apple API claim.

If a reference cannot be read, retry with another file-reading tool. If it still fails, name it in the report and do not apply its rules from memory.

## Workflow

### 1. Baseline

Check every project-instruction location listed in `precedence.md` with a file listing, read each file that exists, and note security-relevant rules, accepted risks, and environments. An accepted risk recorded there is reported as accepted, not as a new finding.

List the targets (app, extensions, widgets, watch, tvOS, macOS, local packages) with their Info.plists, entitlements, and privacy manifests; audit each target separately. Record the deployment targets, the authentication model (accounts, tokens, none), and the kinds of personal data the app handles, such as health information, children's profiles, or location.

Decide the MAS profiles with the `masvs-mastg.md` Profiles table: L1 and P always, L2 when the evidence above shows sensitive data or the project's instructions ask for it, R only when the project's instructions ask for it. Record each decision with its evidence; the in-scope MASTG tests follow from it.

### 2. Search Every Area and Test

Work through every row of the `security.md` Checks table, then every in-scope MASTG test in `masvs-mastg.md` that is checked from `source`, `build settings`, `source + advisories`, or `SBOM`. Most tests fall under an area you already searched; add the searches the test needs, such as `UIPasteboard`, `NSKeyedUnarchiver`, `evaluateJavaScript`, or `NSPinnedDomains`. Search the tracked sources and configuration (`git ls-files`, then `git grep`), not build output, `DerivedData`, `.build`, or checked-out dependencies. Record the searches used as evidence.

For the advisory lookup in test 0273, follow `masvs-mastg.md`: it is the only step that contacts an outside service, and it runs only when the project's instructions or the user allow it. Never mark `runtime` or `binary` tests as passed.

Exclude test targets, previews, and third-party package internals from app findings; mention a third-party issue only when the app's own use of it makes it reachable.

### 3. Trace Before Classifying

For every hit, read the code path and answer: who can trigger it (another app, a website, a network attacker, a person with the unlocked device, someone with the IPA, an insider with CI access), which build configurations contain it, and what they gain. Drop hits that no one can reach. Classify the rest with the `security.md` severity table, and label each with its MASVS control and the MASTG test that found it, if any. Do not report default-redacted `Logger` interpolation, values that are public by design (such as a restricted Firebase API key), or debug-only code compiled out of release.

When a finding depends on server behavior, state the assumption and mark it unverified. Never print a full secret, key, or token; show only a prefix such as `AIza***`.

### 4. Report

Open with these sections:

- `Baseline`: project instruction files found and the rules applied, targets audited, authentication model, personal-data categories, and the references read.
- `Profiles`: the MAS profiles in scope, each with the reason and evidence.
- `MASVS coverage`: one row per MASVS control: status (`fail`, `pass`, `not checked`, `not applicable` as `masvs-mastg.md` defines), the MASTG tests checked, the findings that cause a `fail`, and the in-scope tests left for runtime.
- `Coverage`: every `security.md` area with its result: findings, checked without findings (with the search used), or not applicable (with the reason).
- `Findings`: app findings first, then CI and build findings, each with severity, MASVS control and MASTG test, `file:line`, who can reach it and how, impact, and a fix direction.
- `Not checked`: every in-scope `runtime` and `binary` MASTG test by ID and title, any test whose advisory lookup or SBOM was not available, server-side behavior, and anything else outside static inspection.

Then return the YAML shape from [`../review-ios/SKILL.md`](../review-ios/SKILL.md) section "6. Return Compatible Output" exactly, with no extra fields or totals, so a calling workflow can aggregate it. Read that section before writing the YAML. Use `category: security` for every finding, put the MASVS control and MASTG test in `title` (for example `[MASVS-STORAGE-2 / MASTG-TEST-0297]`), put the area and who can reach it in `body`, put "whole-project audit" in `summary.scope`, and put the baseline, the profiles, and the `Not checked` items in `summary.residual_gaps`. CI findings use the same severities, with "CI:" at the start of the title.

## Final Check

Before returning, confirm:

- project instructions were checked with a file listing;
- the profiles are stated with evidence, and every MASVS control appears in `MASVS coverage` with one status;
- every in-scope MASTG test is either checked or listed under `Not checked`, and no runtime or binary test is marked passed;
- every `security.md` area appears in `Coverage`;
- every finding has evidence, a reachability answer, and a company severity label;
- no secret value is printed in full;
- nothing was edited, built, or run, git state is unchanged, and no outside service was contacted without permission.
