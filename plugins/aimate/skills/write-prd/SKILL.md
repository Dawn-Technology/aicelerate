---
name: write-prd
description: Create a PRD and user stories through user interview, codebase exploration, and component design. Use when user wants to write a PRD, create a product requirements document, user stories or plan a new feature.
metadata:
  author: "Martin Roest <martin.roest@dawn.tech>"
  based_on: "https://github.com/mattpocock/skills/blob/main/write-a-prd/SKILL.md"
  version: 0.0.8
---

## Steps

This skill will be invoked when the user wants to create a PRD or write user stories. You may skip steps if you don't consider them necessary.

1. Ask the user for a long, detailed description of the problem they want to solve and any potential ideas for solutions.

2. Explore the repo to verify their assertions and understand the current state of the codebase.

3. Interview the user relentlessly about every aspect of this plan until you reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one.

4. Sketch out the major components you will need to build or modify to complete the implementation. Actively look for opportunities to extract deep components that can be tested in isolation.

A deep component (as opposed to a shallow component) is one which encapsulates a lot of functionality in a simple, testable interface which rarely changes.

Check with the user that these components match their expectations. Check with the user which components they want tests written for.

5. Once you have a complete understanding of the problem and solution, use the template below to write the PRD. Save the PRD as a Markdown file in the project's root folder to `<YYYY-MM-DD>-<feature-name>.md`.

## Template

<prd-template>

## Problem Statement

The problem that the user is facing, from the user's perspective.

**If feature changes the current behavior of the system, include a description of the current behavior and why it is insufficient.**

## Solution

The solution to the problem, from the user's perspective.

## User Stories

A LONG, numbered list of user stories inluding title, description, conversation/notes, acceptance criteria. Use the INVEST checklist to ensure each story is Independent, Negotiable, Valuable, Estimable, Small, and Testable. Follow the Given-When-Then format for acceptance criteria. Each user story description should be in the format of:

1. As an <actor>, I want a <feature>, so that <benefit>

<user-story-example>
1. Display account balance

As a mobile bank customer, I want to see balance on my accounts, so that I can make better informed decisions about my spending

Conversation/Notes:

- This is a core feature of any banking app, and is expected by users. It should be easily accessible from the home screen.

Acceptance Criteria:

- Given that I am a logged-in user, when I open the app, then I should see my account balance displayed prominently on the home screen.
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

</prd-template>
