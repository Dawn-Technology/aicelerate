---
name: reset-atomic-commits
description: Resets the current branch back to its merge-base with the default branch and rebuilds its history as a series of logical, reviewable atomic commits. DESTRUCTIVE — only invoke this skill when the user explicitly asks to "reset" the branch (or clearly equivalent wording, e.g. "reset en herbouw", "reset this branch into atomic commits"). Never invoke automatically for a generic request to "commit my changes", "split this into commits", or "clean up my commits" — those are not a reset request.
metadata:
  author: "Janne de Vos <janne.de.vos@dawn.tech>"
  version: 1.0.0
---

# Reset Branch into Atomic Commits

## Purpose

Take everything that changed on the current branch relative to the default
branch — regardless of how it is currently committed — and rebuild it from
scratch as a small number of logical, atomic commits so a reviewer can review
the branch commit-by-commit instead of as one large diff.

## When to use this skill

**Only** when the user's request explicitly uses the word "reset" (or an
unambiguous synonym for discarding and rebuilding the branch's history —
e.g. "herbouw de geschiedenis", "rewrite history from scratch"). Examples that
qualify:

- "Reset deze branch en bouw hem opnieuw op in atomic commits"
- "Kun je de huidige branch resetten en herstructureren in logische commits"
- "Reset this branch into atomic commits"

Do **not** self-trigger this skill for adjacent-sounding but different
requests — these are out of scope and must not cause an automatic reset:

- "Commit my changes" / "maak hier een commit van"
- "Split this diff into commits" (without "reset")
- "Clean up my last commit" / "squash these commits"
- "Write me a good commit message"

If a request is ambiguous about whether a destructive reset is wanted, ask
the user to confirm before proceeding — do not assume.

## Guardrails

- **Never run on the default/protected branch.** If the current branch is the
  repo's default branch (or another obviously protected branch such as
  `main`, `master`, `develop`, `release/*`), refuse and explain that this
  skill only rewrites a feature branch.
- **Always create a backup ref before any destructive operation.** Before
  touching HEAD, create `backup/<branch>-<yyyymmdd-HHMMSS>` pointing at the
  current tip, and tell the user it exists and how to recover
  (`git reset --hard backup/<branch>-<timestamp>`).
- **Never force-push, and never ask to push.** This skill only rewrites local
  history. Pushing (force-with-lease) the rewritten branch is left entirely
  to the user.
- **Always present the commit plan and get explicit approval before
  rewriting anything.** Do not perform the reset or create any commit until
  the user has confirmed the plan.
- Refuse (or double-check with the user) if the working tree is mid-merge,
  mid-rebase, or has unresolved conflict markers — resolve that state first.
- Never discard a backup ref (branch or tag) yourself without explicit,
  per-run confirmation from the user — see Step 2.

## Workflow

### Step 1 — Verify preconditions

1. Run `git status` and `git rev-parse --abbrev-ref HEAD` to confirm a clean
   enough state (no in-progress merge/rebase/cherry-pick) and to get the
   current branch name.
2. Refuse if the current branch is the default branch or another protected
   branch.
3. Determine the repo's default branch: prefer
   `git symbolic-ref refs/remotes/origin/HEAD` (strip `origin/`), falling
   back to `git remote show origin` output, then to `main`/`master` if
   neither resolves. Confirm the detected default branch with the user only
   if it could not be determined unambiguously.

### Step 2 — Compute scope, check for leftover backups, then create a new one

1. Fetch the latest default branch ref: `git fetch origin <default-branch>`.
2. Compute the merge-base: `git merge-base HEAD origin/<default-branch>`.
3. Look for backup refs left over from previous runs of this skill on this
   branch: `git for-each-ref refs/heads/backup/<branch>-* refs/tags/backup/<branch>-*`
   (and, more broadly, `git for-each-ref refs/heads/backup/* refs/tags/backup/*`
   in case the branch was renamed since).
4. If any are found, list them to the user (name + commit date) and ask
   whether they may be deleted. Only delete the specific ones the user
   confirms — `git branch -D <ref>` or `git tag -d <ref>` as appropriate —
   never delete a backup ref without that explicit confirmation, and never
   delete one silently as part of a larger batch action.
5. Create a fresh backup ref for this run: `git branch backup/<branch>-<timestamp> HEAD`.
6. Show the user the full scope of what will be rebuilt:
   `git diff <merge-base>..HEAD --stat` combined with any uncommitted
   changes (`git status --porcelain`), so both already-committed work and
   uncommitted work on top are accounted for.

### Step 3 — Unpack the branch into one working diff

1. `git reset --soft <merge-base>` — moves HEAD to the merge-base without
   touching the working tree or index.
2. `git reset` (mixed, no ref) — unstages everything, so the entire set of
   changes (previously committed + anything that was uncommitted) now shows
   up as one unstaged diff against the merge-base.
3. Confirm nothing was lost: `git diff <merge-base> --stat` should match what
   was shown in Step 2.4.

### Step 4 — Determine the commit convention to use

Look for repo-specific AI/commit-convention docs, in this order, and use the
first one found instead of the default style below:

- `commit-message.instructions.md` (repo root)
- `CLAUDE.md` / `.claude/CLAUDE.md` (project-level, not the user's global one)
- `AGENTS.md`
- `.github/copilot-instructions.md`
- `CONTRIBUTING.md` (only if it defines a commit message format)

**Default style (used only if none of the above define a convention):**
Conventional Commits, atomic per commit — `<type>(<scope>): <subject>`,
imperative mood, one logical change per commit, short body explaining the
*why* when the change isn't self-evident.

### Step 5 — Plan the atomic commits

Analyze the full diff from Step 3 and group hunks by **logical concern**, not
by file and not by directory — the same way a developer would split a large
change for review: e.g. "add feature X", "refactor Y to support X", "update
tests for X", "update docs/config". A single file may end up split across
multiple commits if it contains unrelated hunks; a single commit may span
multiple files if they belong to the same concern.

Order commits so the branch is buildable/reviewable at every step (e.g.
foundational/shared code before the code that uses it, implementation before
its tests, unless the convention found in Step 4 says otherwise).

For each proposed commit, prepare:

- The list of files/hunks it contains.
- A draft commit message following the convention from Step 4.

### Step 6 — Present the plan (HARD STOP)

Show the user the full proposed commit plan: ordered list of commits, each
with its files/hunks summary and full draft message. Ask for explicit
confirmation before making any changes.

Do **not** call any git write commands after presenting the plan in that same
response. Wait for the user's next message.

### Step 7 — Execute (only after confirmation)

For each planned commit, in order:

1. Stage exactly the files/hunks belonging to that commit — use
   `git add <file>` when the whole file belongs to one commit, or
   `git apply --cached` with an extracted hunk patch (or an interactive
   `git add -p` selection) when a file's hunks are split across commits.
2. Verify staged content matches the plan: `git diff --cached --stat`.
3. Commit with the prepared message: `git commit -m "<message>"` (use a
   heredoc or `-F` for multi-line/body messages).

If reality doesn't quite match the plan once staging (e.g. a hunk can't be
isolated cleanly), stop and tell the user rather than silently improvising a
different split.

### Step 8 — Report

Show the rebuilt history (`git log --oneline <merge-base>..HEAD`) and remind
the user:

- The backup ref name, in case they want to recover the old history.
- That the branch has **not** been pushed — if the branch previously existed
  on the remote, a subsequent push will need `--force-with-lease`, which is
  left to them.