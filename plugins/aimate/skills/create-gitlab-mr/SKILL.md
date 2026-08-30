---
name: create-gitlab-mr
description: Creates a new feature branch from current git changes, commits them, pushes to the remote, and opens a GitLab Merge Request using the GitLab MCP server. Use this skill when asked to create a gitlab merge request
metadata:
  version: 1.1.0
---

# Create GitLab Merge Request from Current Changes

## Role

You are an expert Git and GitLab automation assistant. Your goal is to help users seamlessly turn their local changes into published GitLab Merge Requests.

## Prerequisites

- Terminal access (`run_in_terminal`)
- File reading capabilities (`read_file`) to check local references
- The `write-commit-message` skill, which authors the commit message for this workflow
- GitLab MCP server must be configured and authenticated

## Instructions

When the user asks you to create a branch, commit changes, and create a GitLab Merge Request based on their current working directory or recent work, follow these exact steps:

1. **Analyze Current Changes**:
   - Run `git status`, `git diff`, and `git diff --staged` in the terminal to inspect what has changed.
   - Fetch the git remote using `git remote -v` to determine the project origin.
   - Based on the changed files and their content, determine an appropriate branch name and a descriptive title for the Merge Request.
   - **Important:** Do not write the commit message yourself. Invoke the **`write-commit-message`** skill and use the message it produces verbatim. It owns the commit message format, maintained in its `references/commit-message-rules.md`, and it runs autonomously — do not add an approval step of your own. Do not fetch `commit-message.instructions.md`; it is the VS Code entry point, forwarding to those same rules, which the skill already reads.

2. **Create Branch, Commit, and Push**:
   - Use the `run_in_terminal` tool to checkout the new branch, stage the changes, commit, and push to origin.
   - Create the branch and stage first: `git checkout -b <branch-name> && git add .`
   - Then commit using the message file that `write-commit-message` produced, so its `#` prompt lines are stripped: `git commit --cleanup=strip -F <tmpfile>`. Never collapse a multi-line message into `git commit -m`.
   - Finally: `git push -u origin <branch-name>`

3. **Create the GitLab Merge Request**:
   - Call the `mcp_gitlab_create_merge_request` tool to open the MR on GitLab.
   - Use the URL-encoded project path for `project_id` (derived from the git remote, e.g., `namespace%2Fproject-name`).
   - Use the branch you just pushed for `source_branch`.
   - Set `target_branch` by dynamically determining the default remote branch (e.g., using `git remote show origin` or `git symbolic-ref refs/remotes/origin/HEAD`). Do not assume it is `main`.
   - Set `remove_source_branch` to `true`.
   - Fill in the `title` and `description` summarizing the changes.

4. **Handle Authentication/Token Errors**:
   - If the `mcp_gitlab_create_merge_request` tool returns an unauthorized or token expired error, kindly ask the user to restart or re-authenticate their GitLab MCP server and retry.

5. **Report to User**:
   - Provide the user with a direct web link to the successfully created Merge Request.
