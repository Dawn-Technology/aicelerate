---
name: write-commit-message
description: >
  Writes high-quality git commit messages following the seven rules of great
  commit messages (Chris Beams) and a fixed subject+body template. Auto-triggers
  whenever a commit is being authored or suggested — e.g. the user asks to
  "commit", "commit this", "git commit", or the agent itself is about to run
  git commit — not only when explicitly asked to "write a commit message".
  Runs autonomously: reads the staged diff, drafts the message, and commits
  it without stopping for approval, then reports what was committed.
metadata:
  version: 1.0.0
  author: "Johan Kromhout <johan.kromhout@dawn.tech>"
---

# Write commit message

## Role

You draft the **git commit message** any time a commit is being created —
whether the user explicitly asks you to write one, or you (the agent) are
about to run `git commit` as part of a task. Never skip this and never
hand-wave a generic message like "fix stuff" or "update files".

This skill owns the commit workflow: gather context, compose, commit, report.
The **format rules themselves live in one shared file**,
[`./references/commit-message-rules.md`](./references/commit-message-rules.md),
which the repo-root `commit-message.instructions.md` forwards to as well.
Maintain the rules there, never here.

Other skills that produce commits (e.g. `create-gitlab-mr`) delegate the
message to this skill instead of writing their own.

## Autonomy

Run end to end without a confirmation step. Draft the message, commit it, and
report what was committed afterwards.

- Never ask the user to approve, confirm, or review the draft before
  committing, and never present a draft and wait.
- Never ask which files to stage, whether to proceed, or which wording to
  prefer. Decide, using the rules file and the diff, and commit.
- No question is needed for anything this skill covers — every gap has a
  default below. If something is genuinely unresolvable (e.g. the repository
  has no commits and no identity configured), do the part you can and report
  the blocker; do not stall waiting on an answer.
- A user who wants to intervene will amend or reset afterwards. `git commit`
  is cheap to redo; a blocked agent is not.

## Persistence

ACTIVE for every commit in this session, not just when explicitly requested.
Applies even mid-task, e.g. right before running `git commit` as one step of
a larger change.

## Step 1 — Gather context

1. Run `git diff --cached` to see the staged changes. This is the primary
   source for _what_ changed.
   - If nothing is staged, do not stop to ask. Read `git status --short` and
     `git diff`, stage the changes that belong to the work at hand with
     `git add <paths>` (or `git add -A` when the intent is to commit
     everything), and continue. Name the files you staged in the report at
     the end.
   - Leave out anything obviously unrelated to the task — build output, local
     scratch files, unrelated edits already in the tree. Skipping a file is a
     decision you make silently; it is not a question for the user.
2. Get the current branch: `git rev-parse --abbrev-ref HEAD`.
3. Extract a Jira ticket key from the branch name using the pattern
   `[A-Z]+-\d+` (e.g. `PROJ-156`, `ABC-1211`).
   - If no key is found in the branch name, skip the ticket lookup and omit
     the links line gracefully — do not block the commit on this.

## Step 2 — Compose the message

**Read [`./references/commit-message-rules.md`](./references/commit-message-rules.md) now and follow it.**
It defines the format, the seven rules, what belongs in each paragraph, the
symptom-not-mechanics requirement, the self-check, and the worked examples.
Do not compose from memory.

Use the template below as scaffolding while you write. The `#` lines are
**prompts that guide you** — they are NOT part of the final commit. They must
be stripped from the actual commit (git only strips them under
`--cleanup=strip`; see Step 3). Never leave `#` lines visible in the committed
message.

```
<subject line>

# If applied, this commit will...
<subject line's action, restated/completed if useful>

# Why is this change needed?
Prior to this change, <the problem / prior behavior, grounded in the diff and ticket context>

# How does it address the issue?
This change <the conceptual approach taken, and WHY this approach>

# Provide links to any relevant tickets, articles or other resources
<Jira ticket key/link if one was found — omit this line entirely if none>
```

Before committing, run the self-check from the rules file against your draft
and fix what it catches. Its two failures — a subject that names code instead
of an outcome, and a "how" that walks through the diff — are the ones that
actually happen. This is your own check, not a round trip to the user.

## Step 3 — Commit

Commit straight away. Do not show the draft first and wait.

- Commit so the `#` prompt lines are stripped: write the full template
  (including `#` lines) to a temp file and commit with
  **`git commit --cleanup=strip -F <tmpfile>`**, then delete the temp file.
  Do NOT use `-F` without `--cleanup=strip` (default cleanup for `-F`/`-m` is
  `whitespace`, which leaves the `#` lines in the commit). Verify afterwards
  with `git show -s --format=%B <sha>` that no `#` lines remain.
- `--cleanup=strip` drops **every** line starting with `#`, not only the
  template prompts. If a body or links line would start with an issue
  reference such as `#123`, rewrite it (`Ref: #123`) or move the reference
  inline — otherwise it silently disappears from the commit.
- When another skill drives the commit, hand it the temp file path and the
  same `git commit --cleanup=strip -F <tmpfile>` invocation. Never let a
  multi-line message be collapsed into `git commit -m`.

## Step 4 — Report

After committing, show the user what landed: the short SHA, the committed
message as `git show -s --format=%B` returns it, and the files you staged if
you staged anything yourself. This is a report of work done, not a request for
approval — do not append a question to it.

If the message needs changing, the fix is `git commit --amend`, not a
pre-commit approval round.
