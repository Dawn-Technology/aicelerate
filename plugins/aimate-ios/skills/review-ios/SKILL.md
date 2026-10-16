---
name: review-ios
description: Use when the user explicitly asks for an iOS review, or when the project's instructions (such as AGENTS.md) route Swift or Xcode reviews to review-ios. Covers SwiftUI, UIKit, concurrency, lifecycle, accessibility, TCA, MVVM + Coordinators, XCTest, XCUITest, Swift Testing, deployment targets, and Apple-platform API compatibility.
metadata:
  author: "Dawn Technology"
  version: 0.1.0
  role: "ios-review-specialist"
---

# iOS Specialist Review

## Purpose

Add deterministic Apple-platform coverage to a code review without replacing generic correctness, security, and maintainability review. This skill is read-only and returns evidence-backed findings that a local or PR review workflow can combine with its generic findings.

Run only when the user asks for it or the project instructions (see `precedence.md`) route Swift or Xcode reviews here. Generic `aimate` review skills do not call it.

## Inputs

Collect the requested diff or files plus:

- repository path, project instructions, and ADRs;
- project/workspace, scheme, package, deployment-target, and Swift language evidence relevant to the change;
- established architecture and test frameworks;
- available optional iOS specialist skills and executable Xcode routes;
- tests or build results already supplied by the caller.
- output target: `chat`, `inline-comments`, `report`, or `calling-skill`.

If no execution route works, continue with static review and state that limitation. Do not invent a build or test result.

## Policy

Always read these shared references before reviewing:

- [`../ios-standards/references/precedence.md`](../ios-standards/references/precedence.md)
- [`../ios-standards/references/architecture.md`](../ios-standards/references/architecture.md)
- [`../ios-standards/references/tooling.md`](../ios-standards/references/tooling.md)

Read these when the change or project involves them:

- [`../ios-standards/references/tca.md`](../ios-standards/references/tca.md) when the project imports `ComposableArchitecture`;
- [`../ios-standards/references/testing.md`](../ios-standards/references/testing.md) when tests change or changed behavior lacks tests;
- [`../ios-standards/references/legacy-projects.md`](../ios-standards/references/legacy-projects.md) when the project uses an older or mixed architecture, UI framework, or test framework;
- [`../ios-standards/references/security.md`](../ios-standards/references/security.md) when the change touches secrets, authentication, biometrics, cryptography, networking configuration, logging, deep links, web content, file storage, analytics, entitlements, the privacy manifest, or CI;
- [`../ios-standards/references/apple-docs.md`](../ios-standards/references/apple-docs.md) before making an availability, deprecation, or other version-sensitive Apple API claim;
- [`../ios-standards/references/capability-providers.md`](../ios-standards/references/capability-providers.md) before using or reporting optional providers.

If a reference cannot be read, retry with another file-reading tool. If it still fails, name it in `residual_gaps` and do not apply its rules from memory.

Use accepted optional specialists when available and relevant. They deepen one module; they do not override project precedence or supply evidence by themselves. Do not stop because an optional skill is absent.

## Workflow

### 1. Establish the Baseline

Determine the actual deployment target, toolchain constraints, UI framework, architecture, dependency versions, and test framework from project evidence. Record conflicts between project policy and company defaults before reviewing.

Check every project-instruction location listed in `precedence.md` with a file listing, then read each file that exists and name them. When none exist, say "No project instructions; baseline inferred from project evidence" and name the evidence used for each item. When they exist, report every place where they disagree with the project files or this machine, such as deployment targets, Xcode paths, or simulator names.

List project-local skills and say for each whether it was used and why. Check `.agents/skills/`, `.claude/skills/`, and `skills-lock.json` with a file listing first; report "none found" only after that check. They rank with project instructions in `precedence.md`.

Start `residual_gaps` with this baseline: which project instruction files exist and their disagreements, project skills, architecture, deployment targets, key dependency versions such as TCA, test frameworks, and each relevant capability with its exact `tooling.md` state (`available`, `fallback`, `unavailable`, or `not-required`) and reason.

For `chat` output, open with a `Baseline` section and a `Verification` section in that form, then list findings with their exact severity labels (`security-violation`, `request-for-change`, `optional`).

### 2. Trace Changed Behavior

Read the changed code in context and trace state owners, callers, dependencies, asynchronous work, lifecycle boundaries, navigation, persistence, and tests. Review every requested file. A framework label is not evidence of correctness or a defect.

### 3. Apply Relevant Modules

Check only modules engaged by the change:

| Module | Concrete risks to trace |
| --- | --- |
| Swift | ownership, mutation, error semantics, API contracts, value/reference behavior |
| Concurrency | actor isolation, `Sendable`, task ownership, cancellation, ordering, stale results, continuation safety |
| SwiftUI | state ownership, identity, update loops, bindings, navigation, lifecycle, adaptive layout, previews |
| UIKit | lifecycle ordering, containment, reuse, bindings, main-thread UI work, interoperability |
| Architecture | explicit dependencies and effects, state ownership, test seams, consistency with scoped project pattern |
| Accessibility | meaningful labels/actions, traits, focus, Dynamic Type, contrast, motion alternatives, touch targets |
| Compatibility | availability against the real deployment target and resolved dependency versions |
| Tests | observable behavior, deterministic async control, failure/cancellation/order cases, suitable framework and naming |
| Security | secret storage, Keychain use, biometrics bound to secrets, client-only enforcement, logging privacy, transport exceptions and trust, cryptography, deep links and server-supplied links, web content bridges, analytics data, debug features in release, CI changes; checks and severities in `security.md` |
| Privacy and platform | permissions and usage descriptions, privacy manifest, entitlements, data at rest, background behavior |

Use `apple-docs.md` for version-sensitive Apple claims and `tca.md` for TCA claims. A finding that depends on how a framework or dependency behaves cites documentation or source at the resolved version; otherwise mark the claim unverified in the finding. Prefer compiler/project evidence over an external skill's assumed future toolchain.

For every changed asynchronous operation, explicitly answer four questions before leaving this module: who owns the task, what cancels it, what prevents an older result replacing a newer one, and how cancellation is distinguished from failure and a valid empty result. Actor isolation prevents data races; it does not answer those lifecycle and semantic questions.

### 4. Verify

Unless the user asks for a static-only review, try to build the affected scheme and run the tests that cover the changed code. Resolve the route in the `tooling.md` order, starting with Xcode MCP, and run only build and test operations. Prefer the specific affected tests over the full suite.

For each route used, name the scheme, test plan, and destination. Report every route in the `tooling.md` order, including skipped ones: `available` with the outcome, or `unavailable` with the observed reason, such as "not installed". A route that was not attempted is reported as not run, with the reason, never as `unavailable`. A build or test failure caused by the change is a finding; an unrelated pre-existing failure goes in `residual_gaps`.

### 5. Classify Findings

Report only reachable or demonstrable problems:

- `security-violation`: reachable security or privacy violation.
- `request-for-change`: correctness, lifecycle, compatibility, accessibility, or release-safety defect that should block the change.
- `optional`: concrete improvement with bounded value that does not block release.

A problem outside the diff that the change does not introduce or make reachable is at most `optional`, with a suggested follow-up ticket.

Do not report continued use of UIKit, MVVM, XCTest, or another established pattern by itself. Recommend migration separately only when evidence shows the current design blocks safe change or testing.

### 6. Return Compatible Output

Return the generic `code-review` shape so callers can aggregate the specialist result without an adapter. Use the closest generic category and put the specific iOS module in the title or body:

```yaml
summary:
  submission: short description of reviewed input
  scope: reviewed files or change set
  residual_gaps: project baseline, capability routes, commands/tools actually run, and outstanding checks
totals:
  security-violation: 0
  request-for-change: 0
  optional: 0
findings:
  - id: path/to/File.swift:123:short-slug
    severity: security-violation | request-for-change | optional
    category: syntax | logic | security | style | documentation | maintainability | scope-consistency
    title: short evidence-backed label
    body: why the reachable behavior matters
    location:
      file: path/to/File.swift
      line: 123
      line_type: added | deleted | context | unknown
    suggestion: concise direction, without forcing an unrelated migration
report: chat-ready ordered findings
comment_bodies: provider-neutral comment text keyed by finding id; include for `calling-skill` or `inline-comments`, omit otherwise
```

When composing with generic review, deduplicate by underlying behavior and keep the stronger evidence. Do not inflate severity because two reviewers found the same issue.

When running alongside a generic review, that review is responsible for scope sizing and chunking; when it supplies a chunk, review only that chunk. When running on its own over a large change, review file by file and record that in `residual_gaps`. `review-ios` is a specialist pass, never a substitute for generic `code-review`.

## Final Check

Before returning, confirm:

- the always-read references were read, or the failure is named in `residual_gaps`;
- `residual_gaps` starts with the baseline, including which project instruction files were found and read;
- project skills were checked with a file listing before being reported;
- every finding has code or executed-tool evidence;
- version claims use the project's actual baseline, and framework-behavior claims cite documentation or source or are marked unverified;
- no optional provider was treated as required;
- no architecture or framework migration was proposed without demonstrated need;
- a build and the affected tests were attempted unless the review was static-only, and no route is reported `unavailable` without an attempt or observed reason;
- unexecuted build, test, simulator, and device checks are named explicitly.
