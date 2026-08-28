---
name: estimate-size
description: Estimate software tickets and work items with a configurable relative-sizing workflow. Respect dedicated estimators and local project rules, and use the built-in defaults when no local rules are provided.
---

# Estimate Size

Estimate the relative size of a software ticket, issue, story, bug, spike, or other work item. Produce a transparent estimate grounded in the actual scope, complexity, uncertainty, dependencies, and validation effort.

This skill is for relative sizing such as story points or an equivalent team scale. It sizes a whole work item in points; it does not size the subtasks inside a plan (that is `write-plan`), and it is not a time-registration or delivery-date calculator. For an implementation plan use `write-plan`, and for an hour estimate of that plan use `estimate-time`.

## Scope and Precedence

This skill supports four valid operating modes:

1. **Dedicated estimator:** If the project, team, or domain has another skill that owns estimation for this work, use that skill alone. Do not add this skill's rules or output to it.
2. **Local policy overlay:** If the project provides buckets, anchor examples, exceptions, or other estimation rules but no dedicated estimator, use this skill's workflow with those local rules replacing the corresponding defaults.
3. **Built-in policy:** If the project provides no estimation rules, use the complete workflow and default scale in this skill as the project's estimation approach.
4. **One-off custom scale:** If the user supplies a scale or special rule for one estimate, use it for that request only and do not treat it as a lasting project policy.

A project may provide only part of an estimation policy. For example, it may define allowed values or special rules while relying on this skill for the assessment process. Keep the generic defaults for every aspect that the project or user has not overridden.

If two applicable sources conflict, prefer the explicitly requested or more specific source, explain the conflict, and ask for clarification only when it could change the estimate. A project without a dedicated estimator or local policy is a supported configuration, not a missing prerequisite.

## Policy Discovery

Before estimating, determine which operating mode applies and establish the rules for that mode. Use only sources available in the current context:

- Other skills that explicitly own estimation for the project, team, or domain.
- Project instructions, contribution guides, team handbooks, or estimation documentation.
- Tracker configuration, issue fields, workflow rules, or labels when the tracker is accessible.
- A small sample of comparable, recently estimated work items from the same team or project.
- The user's stated scale, exceptions, and calibration preferences.

Record each important policy fact as **Observed**, **Provided**, or **Assumed**. If no local policy is found, record that explicitly and use the built-in policy; do not treat the absence of local rules as a blocker. If a dedicated estimator applies, stop this workflow and defer to it.

When updating a tracker, verify that the selected value is accepted by the target field. If the tracker constraints are unavailable, report that validity is unverified. Ask for clarification only when the tracker rejects the selected scale or when a one-off custom scale cannot be represented in the target field.

## Estimation Principles

- Estimate relative size, not hours, cost, calendar time, or individual performance.
- Size the complete requested outcome, including implementation, relevant tests, integration, migration, rollout, and documentation work.
- Base the estimate on scope, complexity, uncertainty, dependencies, and validation effort.
- Inspect the affected code, configuration, interfaces, and adjacent tests when repository context is available.
- Use historical items to calibrate the team's scale, not to copy an estimate mechanically.
- Prefer the smallest defensible estimate that covers the stated outcome and its risks.
- Do not use issue type, priority, assignee, epic, labels, title wording, or ticket age as the primary size driver.
- Do not infer size from the number of words in a description or from detailed technical language alone.
- Do not add points simply because work is important or urgent.
- Do not convert points to hours unless the user explicitly asks for a separate, clearly labelled forecast based on team data.

## Scale Selection

Use the scale supplied by the project or team, including any allowed values, anchor examples, and special cases. Preserve the team's terminology in the result. If local rules define only part of the scale, use the built-in definitions for the remaining buckets.

If the user supplies a one-off scale, use it instead of the project or built-in scale for the current estimate. State that it is request-specific and do not infer project-wide rules from it.

If no project or request-specific scale is available, use this built-in policy:

- `0`: no meaningful implementation work; for example, administrative, duplicate, obsolete, or clarification-only work.
- `1`: smallest meaningful, isolated change.
- `2`: small, bounded slice with limited coordination.
- `3`: moderate slice with several related changes or some investigation.
- `5`: substantial slice with multiple moving parts or cross-boundary work.
- `8`: large slice that should normally be split.
- `13`: very large initiative that should almost always be split.

These buckets are the complete default scale for projects using this skill without local rules. They are relative sizes, not a universal industry standard. Any work requiring implementation, configuration, migration, testing, or documentation belongs at `1` or above. If the supplied scale is non-numeric, map the same size categories to the team's labels rather than converting them to points.

## Zero-Sized Work

Use `0` when the ticket has no meaningful implementation work. This includes administrative, duplicate, obsolete, or clarification-only work. Do not use `0` merely because the work is small; a small implementation or validation change is `1`.

Project-specific rules or a one-off request may refine which work belongs at `0`, but they should not be needed for ordinary use of this skill.

## Size Drivers

Assess the following dimensions before selecting a bucket:

### Scope

- Number of user-visible outcomes or acceptance criteria.
- Number of components, services, repositories, or layers affected.
- Whether data, permissions, APIs, UI, background jobs, or deployment configuration change together.

### Complexity

- New domain behavior versus a local modification.
- Algorithmic, state-management, concurrency, security, or migration complexity.
- Number and strength of interactions between the affected parts.

### Uncertainty

- Unknown architecture, external behavior, or technical feasibility.
- Missing requirements, examples, test data, or acceptance details.
- Need for research, prototyping, or coordination before implementation.

### Dependencies and Risk

- Reliance on other teams, services, vendors, environments, or unfinished work.
- Compatibility, rollout, migration, observability, or rollback concerns.
- Blast radius if the change is incorrect.

### Validation

- Unit, integration, contract, end-to-end, migration, accessibility, security, or operational checks needed to establish the outcome.
- Test data, fixtures, environments, or manual verification that materially expands the work.

Use the dimensions to explain the estimate. Do not pretend that they form a precise mathematical formula unless the team has defined one.

## Splitting Guidance

Recommend splitting before assigning a high bucket when the work contains independent outcomes or can be delivered through vertical slices. Useful split boundaries include:

- Separate user outcomes or acceptance criteria.
- Backend/domain work from a separately deliverable UI or integration slice.
- Data migration preparation from the feature that consumes the migrated data.
- Discovery or prototype work from committed implementation.
- Enablement, rollout, or cleanup work from the initial behavior change.

Do not split merely to force a smaller number. A ticket may remain large when the breadth is intentional, the pieces are tightly coupled, or splitting would create unusable partial outcomes. Explain why in that case.

## Decision Procedure

Follow this sequence:

1. Identify the work item's requested outcome and acceptance boundary.
2. Resolve the applicable project or team policy and scale.
3. Apply any special category or override defined by the selected policy.
4. Inspect repository and tracker context when available.
5. Identify the main scope, complexity, uncertainty, dependency, and validation drivers.
6. Compare with a few relevant historical items, if available.
7. Select the smallest scale bucket that covers the complete outcome.
8. If the result is near the team's split threshold, recommend concrete slices and explain whether the estimate applies before or after splitting.
9. State assumptions, evidence, confidence, and any policy question that could change the result.

## Required Output

For every estimate, provide:

### Estimate

- **Size:** one value from the applicable scale.
- **Scale:** project/team policy, user-provided scale, or this skill's built-in policy.
- **Confidence:** high, medium, or low.

### Evidence and Rationale

- The requested outcome and implementation boundary.
- The two or three strongest size drivers.
- Relevant repository, tracker, policy, or historical evidence.
- What is explicitly known versus assumed.

### Split Recommendation

- State whether the ticket is appropriately sized as one unit.
- For a large or uncertain item, list concrete candidate slices.
- If no split is recommended, explain briefly why the work remains cohesive.

### Policy Notes

- Identify any unknown or conflicting rule, if one exists.
- State whether the estimate is safe to record in the tracker.
- State whether the selected scale comes from a project/team policy, the user's one-off instructions, or this skill's built-in policy.

## Consistency Checks

When reviewing an existing estimate rather than creating one:

- Verify that the value belongs to the applicable scale.
- Check that the estimate covers the full acceptance boundary.
- Check for omitted validation, integration, migration, rollout, or dependency work.
- Check whether a policy exception was applied consistently.
- Check whether a high estimate should be split.
- Recommend a revised value only after explaining the evidence and policy used.

If the project uses this skill's built-in policy, review the estimate against that policy. Report a consistency gap only when the applicable policy is conflicting, incomplete in a material way, or impossible to identify.
