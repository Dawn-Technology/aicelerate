---
name: create-gitlab-mr
description: Creates a new feature branch from current git changes, commits them, pushes to the remote, and opens a GitLab Merge Request using the GitLab MCP server. Use this skill when asked to create a gitlab merge request 
metadata:
   version: 1.0.0
---

# Create GitLab Merge Request from Current Changes

## Role
You are an expert Git and GitLab automation assistant. Your goal is to help users seamlessly turn their local changes into published GitLab Merge Requests.

## Prerequisites
- Terminal access (`run_in_terminal`)
- File reading capabilities (`read_file`) to check local references
- Web fetching capabilities (`fetch_webpage`) to read external guidelines
- GitLab MCP server must be configured and authenticated

## Instructions
When the user asks you to create a branch, commit changes, and create a GitLab Merge Request based on their current working directory or recent work, follow these exact steps:

1. **Analyze Current Changes**:
   - Run `git status`, `git diff`, and `git diff --staged` in the terminal to inspect what has changed.
   - Fetch the git remote using `git remote -v` to determine the project origin.
   - Based on the changed files and their content, determine an appropriate branch name, a descriptive title for the Merge Request, and formulate a clear commit message. 
   - **Important:** When formatting the commit message, fetch and strictly follow the comprehensive guidelines from the online reference using the raw markdown link: `https://raw.githubusercontent.com/ibuildingsnl/reusable-ai-prompts/main/commit-message-instructions.md`.

2. **Create Branch, Commit, and Push**:
   - Use the `run_in_terminal` tool to checkout the new branch, stage the changes, commit, and push to origin.
   - Example: `git checkout -b <branch-name> && git add . && git commit -m "<commit-message>" && git push -u origin <branch-name>`

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
