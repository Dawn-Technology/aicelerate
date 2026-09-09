---
name: write-summary
description: Summarize a branch, pull request, merge request, commit range, patch, or local code changes in plain language. Use when the user asks for a branch summary, code change summary, change description, or short and long descriptions of completed development work.
metadata:
    author: "Piotr Ramotowski <piotr.ramotowski@dawn.tech>"
    version: 1.0.0
---

# Write Summary

Explain the purpose and outcomes of a bounded set of code changes. Produce text a person can understand without reading the diff.

This is a read-only skill. Inspect the available context, then reply in chat. Do not edit files, commit, push, open or update a pull request or merge request, post comments, or publish the result anywhere.

## Resolve the scope

Honor an explicitly supplied change set, comparison target, and task description first. Supported inputs include:

- the current branch compared with its target branch;
- a pull request or merge request and its description;
- a commit or commit range;
- staged, unstaged, or other local changes;
- a supplied diff or patch.

For a local branch, determine the target from explicit context, pull-request metadata, the remote default branch, or repository conventions, in that order. Compare from the merge base so unrelated target-branch changes are excluded. Do not silently include uncommitted work in a committed branch summary; include it only when the request covers local or unfinished changes.

Use read-only provider tooling when a pull-request or merge-request URL is the only source. Never turn a summary request into a provider write action.

If the requested scope cannot be determined or read, state exactly what context is missing instead of guessing.

## Understand the change

Read the complete diff and the supplied task, ticket, or change description. Inspect nearby code or documentation only when needed to translate the diff into observable behavior.

Determine:

- the problem or objective;
- what capability or behavior was added, changed, fixed, removed, or improved;
- who or what is affected;
- the user-facing or system-level outcome;
- any important boundary on the outcome that prevents an overstatement.

Treat the diff as evidence of what changed and the task description as context for why. Reconcile the two; do not repeat claims that the changes do not support. When the reason is not evidenced, describe the verified outcome without inventing a motive.

## Write the summaries

Return exactly these two sections unless the user requests a different format:

```markdown
## Short version

[One or two direct sentences.]

## Long version

[One concise paragraph with enough context to explain the purpose, changed behavior, and outcome.]
```

Both versions must stand on their own. The long version expands the short version; it does not become a file-by-file inventory.

Apply these rules to both versions:

- Lead with what changed and why it matters.
- Describe outcomes and behavior, not the implementation sequence.
- Use plain language and concrete verbs.
- Mention both user-facing and system-level effects when both are material.
- If the work is entirely internal, explain its operational effect without pretending it adds user-visible functionality.
- Avoid class names, method or function names, file paths, configuration keys, database fields, and technical variable names.
- Avoid commit-by-commit narration, diff statistics, exhaustive lists, and test details unless the user explicitly asks for them.
- Avoid marketing language, filler, praise, and vague claims such as "enhanced," "seamless," "robust," or "cutting-edge."
- Do not begin with process commentary such as "I reviewed the branch" or end with an offer to publish the text.

Before replying, verify that every material claim is supported by the change set or supplied context, that no implementation identifier leaked into the prose, and that the short and long versions differ meaningfully in depth.
