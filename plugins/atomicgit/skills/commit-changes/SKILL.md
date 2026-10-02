---
name: commit-changes
description: Writes a conventional commit message for the current changes and commits them. Use for plain "commit my changes", "commit this", "write me a commit message", "maak hier een commit van" requests — everyday, non-destructive commits. Does NOT rewrite existing history or touch prior commits; for that, see reset-atomic-commits instead (only triggered by an explicit "reset" request).
metadata:
  author: "Janne de Vos <janne.de.vos@dawn.tech>"
  version: 1.0.0
---

# Commit Changes

## Purpose

Turn the current working-tree changes into one well-formed, conventional
commit: figure out what's actually being committed, draft a message that
follows the repo's convention (or a sane default), get a quick confirmation,
and commit.

This is the everyday counterpart to `reset-atomic-commits`: it never rewrites
existing commits or branch history, it only ever adds one new commit on top
of HEAD.

## When to use this skill

Triggers on ordinary commit requests: "commit my changes", "commit this",
"write me a commit message", "maak hier een commit van", "commit dit".

Do **not** use this skill, and defer to `reset-atomic-commits` instead, when
the request is about rewriting or restructuring commits that already exist
(e.g. "reset this branch into atomic commits", "rebuild the history",
"split my last 3 commits"). If unsure which the user wants, ask.

If the pending changes clearly contain **multiple unrelated concerns** that
don't belong in one commit, say so and suggest splitting them (either
manually or via `reset-atomic-commits` if commits already exist) rather than
silently writing one commit message that papers over a mixed diff.

## Guardrails

- Refuse (or double-check) if the working tree is mid-merge, mid-rebase, or
  has unresolved conflict markers — resolve that first.
- Never run `git add -A` / `git add .` silently. If nothing is staged, ask
  whether to stage everything or only specific files — never guess.
- Never amend, reset, or rewrite an existing commit. This skill only ever
  creates one new commit on top of the current HEAD.
- Never force-push, and never push at all unless the user explicitly asks.
- Present the drafted message and ask for confirmation before running
  `git commit`. A one-line "look good?" is enough — this isn't a destructive
  operation, but it still changes the repo's history, so don't commit
  silently on the user's behalf.
- Don't add AI attribution trailers (e.g. "Generated with ...",
  "Co-Authored-By: Claude") unless the repo's own convention (see Step 2)
  calls for one, or the user explicitly asks for one.

## Workflow

### Step 1 — Determine what's being committed

1. Run `git status` to see staged, unstaged, and untracked changes, and
   confirm there's no in-progress merge/rebase/conflict.
2. If changes are already staged (`git diff --cached --stat` is non-empty),
   use exactly that as the commit scope — don't add anything else.
3. If nothing is staged but the working tree has changes, ask the user
   whether to stage everything or only specific files, then stage
   accordingly.

### Step 2 — Determine the commit message convention

Look for repo-specific AI/commit-convention docs, in this order, and use the
first one found instead of the default style below:

- `commit-message.instructions.md` (repo root)
- `CLAUDE.md` / `.claude/CLAUDE.md` (project-level, not the user's global one)
- `AGENTS.md`
- `.github/copilot-instructions.md`
- `CONTRIBUTING.md` (only if it defines a commit message format)

**Default style** (used only if none of the above define a convention): see
[`../reset-atomic-commits/references/atomic-commits.md`](../reset-atomic-commits/references/atomic-commits.md)
— Conventional Commits, `<type>(<scope>): <subject>`, imperative mood, short
body explaining the *why* when it isn't obvious from subject + diff.

### Step 3 — Check the diff is one logical concern

Read the full staged diff. If it clearly mixes unrelated concerns (e.g. a
bug fix plus an unrelated feature, or app code plus generated/vendored
files that shouldn't ship together), tell the user what you see and ask
whether to proceed as one commit anyway or split it first. Don't silently
force a misleading single message onto a mixed diff.

### Step 4 — Draft the message

Write one commit message following the convention from Step 2. Show it to
the user (message text + `git diff --cached --stat` as scope) and ask for
confirmation.

### Step 5 — Commit (only after confirmation)

`git commit -m "<message>"` — use a heredoc or `-F` for a multi-line message
with a body. Do not push.

### Step 6 — Report

Show `git log -1 --stat` so the user can see exactly what landed.
