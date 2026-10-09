# atomicgit

Skills for working with atomic commits.

Reusable skills for rebuilding, splitting, and reviewing git history so a branch stays reviewable commit-by-commit instead of as one large diff.

## Skills

### `reset-atomic-commits`

> Resets the current branch back to its merge-base with the default branch and rebuilds its history as a series of logical, reviewable atomic commits.

Takes everything that changed on the current branch — regardless of how it is currently committed — and rebuilds it from scratch as a small number of logical, atomic commits. Creates a backup ref before touching any history, presents the full commit plan for approval, and never force-pushes.

**DESTRUCTIVE** — only triggers on an explicit request to "reset" the branch (or a clear synonym), never on generic requests like "commit my changes" or "clean up my commits".

**Trigger phrases:** "reset this branch into atomic commits", "reset en herbouw", "rewrite history from scratch"
