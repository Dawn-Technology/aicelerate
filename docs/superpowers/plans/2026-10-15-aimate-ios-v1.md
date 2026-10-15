# Aimate iOS V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a separately installable, portable iOS specialist plugin while minimizing company-owned maintenance.

**Architecture:** Keep generic delivery and GitHub operations in `aimate`; add company iOS policy and specialist capabilities in `aimate-ios`. Resolve optional external skills and native tooling at runtime, with honest standalone fallbacks.

**Tech Stack:** Agent Skills `SKILL.md`, Markdown references, JSON marketplace manifests, Xcode/Swift ecosystem tools.

## Global Constraints

- Leave `aimate` generic.
- External capabilities are preferred but optional.
- Support OpenCode, Claude Code, Codex, and GitHub Copilot through portable skill files.
- Project policy and actual Xcode settings outrank company defaults.
- Do not mandate TCA, MVVM, or architecture migrations.
- Do not manage signing, provisioning, TestFlight, or App Store delivery in V1.
- Do not commit implementation work until the user reviews it.

---

### Task 1: Capability Governance

**Files:**
- Create: `plugins/aimate-ios/docs/capability-matrix.md`

**Produces:** An evidence-linked adopt/compose/build decision and fallback for each planned capability.

- [ ] Research official sources before community alternatives.
- [ ] Record owner, source, license, maintenance signal, host support, selection, and fallback.
- [ ] Reject candidates with unsuitable licensing or stale version assumptions.
- [ ] Verify every external URL and ensure no external dependency is marked required.

### Task 2: Plugin Shell

**Files:**
- Modify: `marketplace.json`
- Create: `plugins/aimate-ios/plugin.json`
- Create: `plugins/aimate-ios/.claude-plugin/plugin.json` symlink
- Create: `plugins/aimate-ios/README.md`

**Produces:** A separately installable plugin with documented OpenCode loading.

- [ ] Add the marketplace entry without changing `aimate` metadata.
- [ ] Add the canonical manifest and Claude compatibility link.
- [ ] Document standalone behavior, optional capability providers, and host installation paths.
- [ ] Parse both JSON manifests and verify the compatibility link target.

### Task 3: Shared Company Policy

**Files:**
- Create: `plugins/aimate-ios/skills/ios-standards/SKILL.md`
- Create: `plugins/aimate-ios/skills/ios-standards/references/precedence.md`
- Create: `plugins/aimate-ios/skills/ios-standards/references/architecture.md`
- Create: `plugins/aimate-ios/skills/ios-standards/references/legacy-projects.md`
- Create: `plugins/aimate-ios/skills/ios-standards/references/testing.md`
- Create: `plugins/aimate-ios/skills/ios-standards/references/tooling.md`

**Produces:** Minimal company-owned policy that user-facing skills can load selectively.

- [ ] Encode precedence and deviation reporting.
- [ ] Encode qualities-first architecture selection and legacy constraints.
- [ ] Encode XCTest, Swift Testing, and XCUITest conventions.
- [ ] Encode capability-based host/tool resolution and verification states.
- [ ] Keep unresolved Swift style and TCA implementation detail out of company policy.

### Task 4: Review iOS Pilot

**Files:**
- Create: `plugins/aimate-ios/skills/review-ios/SKILL.md`
- Create: `plugins/aimate-ios/skills/review-ios/evals/evals.json`

**Consumes:** Shared company policy and optional external specialists.

**Produces:** A read-only iOS specialist review compatible with `aimate` code-review findings.

- [ ] Run SwiftUI, concurrency, and legacy MVVM scenarios without the skill.
- [ ] Record what generic review misses, overstates, or handles already.
- [ ] Author only the additional deterministic coverage and composition contract.
- [ ] Run the same scenarios with the skill and compare outputs.
- [ ] Refine triggering and guidance until the skill adds value without demanding migrations.

### Task 5: Review and Gate V1 Foundation

**Files:** All files from Tasks 1-4.

- [ ] Parse manifests and validate required skill frontmatter.
- [ ] Check all relative links and symlinks.
- [ ] Run `git diff --check`.
- [ ] Inspect `git diff` and confirm generic `aimate` behavior is unchanged.
- [ ] Present uncommitted work for team review.

### Task 6: Later Capabilities

After the foundation is approved, repeat RED-GREEN skill evaluation independently for `implement-ios`, simulator-first `test-ios`, and `build-swiftui`. Do not create placeholder skills before their baseline evaluations. Add physical-device automation only after simulator behavior is reliable and a safe optional provider is selected.
