---
name: review-ios
description: Use when the user explicitly asks for an iOS review, or when the project's AGENTS.md routes Swift or Xcode reviews to review-ios. Covers SwiftUI, UIKit, concurrency, lifecycle, accessibility, TCA, MVVM + Coordinators, XCTest, XCUITest, Swift Testing, deployment targets, and Apple-platform API compatibility.
metadata:
  author: "Dawn Technology"
  version: 0.1.0
  role: "ios-review-specialist"
---

# iOS Specialist Review

## Purpose

Add deterministic Apple-platform coverage to a code review without replacing generic correctness, security, and maintainability review. This skill is read-only and returns evidence-backed findings that a local or PR review workflow can combine with its generic findings.

Run only when the user asks for it or the project's `AGENTS.md` routes Swift or Xcode reviews here. Generic `aimate` review skills do not call it.

## Inputs

Collect the requested diff or files plus:

- repository path and applicable `AGENTS.md` or ADRs;
- project/workspace, scheme, package, deployment-target, and Swift language evidence relevant to the change;
- established architecture and test frameworks;
- available optional iOS specialist skills and executable Xcode routes;
- tests or build results already supplied by the caller.
- output target: `chat`, `inline-comments`, `report`, or `calling-skill`.

If execution is unavailable, continue with static review and state that limitation. Do not invent a build or test result.

## Policy

Read these shared references before classifying iOS-specific findings:

- [`../ios-standards/references/precedence.md`](../ios-standards/references/precedence.md)
- [`../ios-standards/references/architecture.md`](../ios-standards/references/architecture.md)
- [`../ios-standards/references/legacy-projects.md`](../ios-standards/references/legacy-projects.md)
- [`../ios-standards/references/testing.md`](../ios-standards/references/testing.md)
- [`../ios-standards/references/tooling.md`](../ios-standards/references/tooling.md)
- [`../ios-standards/references/capability-providers.md`](../ios-standards/references/capability-providers.md)

Also read these when they apply:

- [`../ios-standards/references/tca.md`](../ios-standards/references/tca.md) when the project imports `ComposableArchitecture`;
- [`../ios-standards/references/apple-docs.md`](../ios-standards/references/apple-docs.md) before making an availability, deprecation, or other version-sensitive Apple API claim.

Use accepted optional specialists when available and relevant. They deepen one module; they do not override project precedence or supply evidence by themselves. Do not stop because an optional skill is absent.

## Workflow

### 1. Establish the Baseline

Determine the actual deployment target, toolchain constraints, UI framework, architecture, dependency versions, and test framework from project evidence. Record conflicts between project policy and company defaults before reviewing.

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
| Privacy and platform | sensitive API usage, permissions, manifests, entitlements, storage, logging, background behavior |

Use `apple-docs.md` for version-sensitive Apple claims and `tca.md` for TCA claims. Prefer compiler/project evidence over an external skill's assumed future toolchain.

For every changed asynchronous operation, explicitly answer four questions before leaving this module: who owns the task, what cancels it, what prevents an older result replacing a newer one, and how cancellation is distinguished from failure and a valid empty result. Actor isolation prevents data races; it does not answer those lifecycle and semantic questions.

### 4. Classify Findings

Report only reachable or demonstrable problems:

- `security-violation`: reachable security or privacy violation.
- `request-for-change`: correctness, lifecycle, compatibility, accessibility, or release-safety defect that should block the change.
- `optional`: concrete improvement with bounded value that does not block release.

Do not report continued use of UIKit, MVVM, XCTest, or another established pattern by itself. Recommend migration separately only when evidence shows the current design blocks safe change or testing.

### 5. Return Compatible Output

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

- every finding has code or executed-tool evidence;
- version claims use the project's actual baseline;
- no optional provider was treated as required;
- no architecture or framework migration was proposed without demonstrated need;
- unexecuted build, test, simulator, and device checks are named explicitly.
