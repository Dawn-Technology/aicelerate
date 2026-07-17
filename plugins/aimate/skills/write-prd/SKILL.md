---
name: write-prd
description: Create a PRD and user stories through user interview, codebase exploration, and component design. Use when user wants to write a PRD, create a product requirements document, user stories or plan a new feature.
metadata:
  author: "Martin Roest <martin.roest@dawn.tech>"
  based_on: "https://github.com/mattpocock/skills/blob/main/write-a-prd/SKILL.md"
  version: 1.1.0
---

> **Output contract:** Every PRD ends with a machine-readable `## Acceptance Criteria` block in the shared canonical format defined in [`../../shared/acceptance-criteria.md`](../../shared/acceptance-criteria.md). Each criterion has a stable id (`AC-1`, `AC-2`, …) that `spec-to-tests` and `review-pr` use as the join key between the spec, its tests, and its review. Do not invent a second criteria format — read and write the shared one.

## Steps

This skill will be invoked when the user wants to create a PRD or write user stories. You may skip steps if you don't consider them necessary.

1. Ask the user for a long, detailed description of the problem they want to solve and any potential ideas for solutions.

2. Explore the repo to verify their assertions and understand the current state of the codebase.

3. Interview the user relentlessly about every aspect of this plan until you reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one.

4. Sketch out the major components you will need to build or modify to complete the implementation. Actively look for opportunities to extract deep components that can be tested in isolation.

A deep component (as opposed to a shallow component) is one which encapsulates a lot of functionality in a simple, testable interface which rarely changes.

Check with the user that these components match their expectations. Check with the user which components they want tests written for.

5. Derive the acceptance criteria from the requirements you gathered in the interview. Turn the behaviour behind each user story into one or more concrete criteria in the shared canonical format defined in [`../../shared/acceptance-criteria.md`](../../shared/acceptance-criteria.md). Read that file before writing the block.

Each criterion is a checkable condition and an observable outcome, given a stable id (`AC-1`, `AC-2`, …). Walk the user through the derived criteria and ask them to confirm each one, fill any gaps, and correct anything that does not match intent — the criteria must be real, not decorative.

If a requirement cannot be expressed as a condition and an outcome, it is too vague to test. Push back and sharpen the requirement with the user rather than writing a fuzzy criterion. Keep each criterion small: one criterion asserts one behaviour.

6. Once you have a complete understanding of the problem and solution, use the template below to write the PRD. Save the PRD as a Markdown file in the project's `docs/spec` folder to `<YYYY-MM-DD>-<feature-name>.md`. Check if folder exists. If not, create it. If file already exists, append a version number to the end of the file name (e.g. `2024-06-01-new-feature-v2.md`).

## Template

<prd-template>

## Problem Statement

The problem that the user is facing, from the user's perspective.

**If feature changes the current behavior of the system, include a description of the current behavior and why it is insufficient.**

## Solution

The solution to the problem, from the user's perspective.

## User Stories

A LONG, sequentially numbered list of user stories including title, description, conversation/notes, and the ids of the acceptance criteria that cover the story. Number each story with a unique, incrementing integer (1, 2, 3, …) — never restart numbering. Use the INVEST checklist to ensure each story is Independent, Negotiable, Valuable, Estimable, Small, and Testable.

Do not restate the full criteria under each story. The full Given-When-Then criteria live once in the `## Acceptance Criteria` block (see below), which is the single source of truth. Each story lists the ids of the criteria that cover it, so the story and its criteria stay in sync. Every story must map to at least one criterion; if it maps to none, either the story is not testable or a criterion is missing.

Each user story description should be in the format of:

{N}. <Title>

As an <actor>, I want a <feature>, so that <benefit>

<user-story-example>
1. Display account balance

As a mobile bank customer, I want to see balance on my accounts, so that I can make better informed decisions about my spending

Notes:

- This is a core feature of any banking app, and is expected by users. It should be easily accessible from the home screen.

Acceptance Criteria: AC-1
  </user-story-example>

This list of user stories should be extremely extensive and cover all aspects of the feature.

## Implementation Decisions

A list of implementation decisions that were made. This can include:

- The components that will be built/modified
- The interfaces of those components that will be modified
- Technical clarifications from the developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions

Do NOT include specific file paths or code snippets. They may end up being outdated very quickly.

## Testing Decisions

A list of testing decisions that were made. Include:

- A description of what makes a good test (only test external behavior, not implementation details)
- Which components will be tested
- Prior art for the tests (i.e. similar types of tests in the codebase)

## Out of Scope

A description of the things that are out of scope for this PRD.

## Further Notes

Any further notes about the feature.

## Acceptance Criteria

The single, machine-readable source of truth for what "done" means. Write this block in the shared canonical format defined in [`../../shared/acceptance-criteria.md`](../../shared/acceptance-criteria.md): a stable heading, sentinel comments, and one `AC-<n>` criterion per checkable behaviour. Every user story above references its criteria by id. `spec-to-tests` and `review-pr` read this exact block, so do not deviate from the grammar.

<!-- acceptance-criteria:start format=gwt/v1 -->

### AC-1: Account balance is shown on the home screen
- **Given** a logged-in user
- **When** the user opens the app
- **Then** the account balance is displayed prominently on the home screen

<!-- acceptance-criteria:end -->

</prd-template>
