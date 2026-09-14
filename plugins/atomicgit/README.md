# atomicgit

Skills for working with atomic commits.

Reusable skills for rebuilding, splitting, and reviewing git history so a branch stays reviewable commit-by-commit instead of as one large diff.

## Skills

### `commit-changes`

> Writes a conventional commit message for the current changes and commits them.

Figures out what's actually being committed (staged, or asks whether to stage the rest), drafts a message following the repo's convention (or Conventional Commits by default), and commits after a quick confirmation. Never rewrites existing commits — only ever adds one new commit on top of HEAD.

**Trigger phrases:** "commit my changes", "commit this", "write me a commit message", "maak hier een commit van"

---

### `reset-atomic-commits`

> Resets the current branch back to its merge-base with the default branch and rebuilds its history as a series of logical, reviewable atomic commits.

Takes everything that changed on the current branch — regardless of how it is currently committed — and rebuilds it from scratch as a small number of logical, atomic commits. Creates a backup ref before touching any history, presents the full commit plan for approval, and never force-pushes.

**DESTRUCTIVE** — only triggers on an explicit request to "reset" the branch (or a clear synonym), never on generic requests like "commit my changes" or "clean up my commits".

**Trigger phrases:** "reset this branch into atomic commits", "reset en herbouw", "rewrite history from scratch"
