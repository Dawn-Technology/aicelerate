---
name: create-gitlab-mr
description: Create a feature branch from current Git changes, commit and push it, and open a GitLab Merge Request with the official glab CLI. Use when asked to create, open, or publish a GitLab merge request from local work.
metadata:
  version: 2.0.0
---

# Create GitLab Merge Request from Current Changes

## Role

You are an expert Git and GitLab automation assistant. Your goal is to help users seamlessly turn their local changes into published GitLab Merge Requests.

## Prerequisites

- Terminal access (`run_in_terminal`)
- File reading capabilities (`read_file`) to check local references
- The `write-commit-message` skill, which authors the commit message for this workflow
- Web fetching capabilities (`fetch_webpage`) to read external guidelines
- The official GitLab CLI, `glab`, installed and authenticated for the GitLab host

## Instructions

When the user asks you to create a branch, commit changes, and create a GitLab Merge Request based on their current working directory or recent work, follow these exact steps:

0. **Verify `glab` Before Mutating Git State**:
   - Verify `origin` is GitLab and determine its hostname. Reject a GitHub or ambiguous remote.
   - If `glab` is missing, stop and give the installation command for the user's platform. On macOS or Homebrew-enabled Linux use `brew install glab`; otherwise point to the official GitLab CLI installation documentation.
   - Run `glab auth status --hostname <origin-host>`. If authentication is missing or expired, stop and ask the user to run `glab auth login --hostname <origin-host>`.
   - After authentication, run `glab repo list --member` as a read-only access check. Do not proceed unless it succeeds.
   - Never ask the user to paste a token into chat. Do not configure or fall back to a GitLab MCP server.

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
   - Use `glab mr create` with the detected repository or local Git context.
   - Use the branch you just pushed for `source_branch`.
   - Set `target_branch` by dynamically determining the default remote branch (e.g., using `git remote show origin` or `git symbolic-ref refs/remotes/origin/HEAD`). Do not assume it is `main`.
   - Set `remove_source_branch` to `true`.
   - Fill in the `title` and `description` summarizing the changes.

4. **Handle Authentication/Token Errors**:
   - If MR creation returns an authentication or transport error, first use `glab mr list` to query the source branch for an existing MR. A failed response may follow a successful mutation.
   - Retry only when no MR exists. Ask the user to re-authenticate with `glab auth login --hostname <origin-host>` when appropriate.

5. **Report to User**:
   - Provide the user with a direct web link to the successfully created Merge Request.
