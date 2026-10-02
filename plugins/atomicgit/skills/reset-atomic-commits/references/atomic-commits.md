# Atomic Commits — Reference

Background context for building commits, whether by an AI or a person. Use
this to judge whether a proposed commit split is "atomic" enough before
committing, and as the default convention when a repo defines none of its
own (see `SKILL.md` Step 4).

## What "atomic" means here

A commit is atomic when it contains **exactly one logical change** and
nothing else:

- It can be described in one sentence without "and".
- Reverting it cleanly undoes that one thing, no more, no less.
- It doesn't mix unrelated concerns — e.g. a bug fix and an unrelated
  formatting pass, or a new feature and a refactor it happened to need.
- It's self-contained enough that `git bisect` lands on it and the reason
  for the change is obvious from the diff plus the message.

Atomic does **not** mean "small" — a single logical change can span many
files (e.g. renaming a function and updating every call site). It also
doesn't mean "one file" — a large file can rightfully contain hunks that
belong to several different commits.

## Why this matters more for AI-generated commits

An AI building commits from a large diff tends toward two failure modes if
not explicitly constrained:

1. **One giant commit.** Fastest to produce, but useless for review —
   reviewers can't approve or reject a `git bisect`-sized slice of it, and a
   revert takes everything with it.
2. **File-by-file commits.** Looks granular but isn't atomic — splitting by
   file (or by directory) instead of by concern produces commits that don't
   build, don't pass tests, or don't make sense in isolation, because a
   single logical change is scattered across several of them.

The fix in both cases is the same: group by **logical concern**, not by
file, directory, or chronology of when the change was written.

## How to split a diff into atomic commits

1. **Read the whole diff first.** Don't start staging before you understand
   everything that changed — a hunk that looks unrelated on its own often
   turns out to belong to a concern you haven't identified yet.
2. **Identify concerns**, e.g.:
   - New capability (feature/endpoint/skill)
   - Supporting/foundational change the above depends on (schema, shared
     util, config)
   - Bug fix (ideally isolated from feature work, even if found together)
   - Tests for a concern above
   - Docs/README/changelog for a concern above
   - Unrelated cleanup (formatting, renames, dead code) — kept separate so
     it doesn't obscure the functional diff
3. **Order for buildability.** Each commit, applied in sequence, should
   leave the branch in a state that at least compiles/builds — foundational
   code before the code that uses it, implementation before its tests,
   unless a project convention says otherwise.
4. **One file, multiple commits is fine.** Use hunk-level staging
   (`git add -p`, or a hand-built patch via `git apply --cached`) when a
   file legitimately contains hunks from more than one concern. Don't force
   a whole file into one commit just because splitting it is more work.
5. **Say why, not just what.** The diff already shows *what* changed; the
   message body should explain *why*, when it isn't obvious from the code
   alone (e.g. why this approach, what it fixes, what it unblocks).

## Message format

Default when no repo convention is found (see `SKILL.md` Step 4 for the
lookup order that overrides this):

```
<type>(<scope>): <subject>

<optional body — the *why*, wrapped at ~72 cols>
```

- Type: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `build`,
  `ci` (Conventional Commits).
- Subject: imperative mood ("add", not "added"/"adds"), no trailing period.
- Body: only when the reasoning isn't self-evident from subject + diff.

## Quick self-check before committing

- [ ] Can I describe this commit in one sentence without "and"?
- [ ] Does reverting it undo exactly one thing?
- [ ] Would the branch still build/pass tests if I stopped right after this
      commit?
- [ ] Is anything in here unrelated to the stated concern? (If yes, split
      it out.)
