# Completing a version bump

Read in full before moving any pin. Used by [`fix-ci`](../SKILL.md) when a failure is a version conflict between pins.

A dependency bump, usually from a bot, sometimes lands only partly. One file moves a package to a new version and other files still pin the old one, so the build cannot resolve both. The author already chose the new version. Moving the other pins to it carries that choice out; it makes no new one.

## Allowed only when all of these hold

- The failure is a version conflict between pins of **one package**, and the log or the manifests show it.
- The PR/MR itself moved at least one of those pins. Check against the target: `git diff {base_sha}...{head_sha} -- <manifest>`.
- The PR/MR set the package to **one** version. If its own pins disagree about the target, there is no version to complete to.
- Every pin you move goes to **exactly that version**, in the same form: an exact pin stays an exact pin, a range keeps its shape.
- Every move goes **up**.
- The move is a **patch or minor** change. A **major** change is allowed only when the PR/MR itself crossed that same major boundary for this package. If the PR/MR moved a pin from 1.x to 2.x, another pin at 1.x may go to 2.x. A pin at 0.x may not, and neither may a pin at 1.x when the PR/MR moved 2.x to 3.x. In 0.y.z versions a change in `y` counts as major. For a scheme that is not semver, every change counts as major.
- The head is trusted. On an untrusted head the lockfile cannot be regenerated, so this is not allowed.
- The lockfile is regenerated the narrow way (see Change limits in SKILL.md), and the conflict is gone.

## Never

Move a pin by a major the PR/MR did not cross. Pick a version the PR/MR did not introduce. Touch a package the PR/MR does not change. Roll the PR/MR's own bump back. Widen or loosen a constraint. Add or remove a dependency. Bump anything just because a newer version exists.

If the pins disagree and the PR/MR moved none of them, that is the author's decision. Leave it and report it as blocked.

## Report it

A bump can change behavior, a build tool or a library most of all. That risk belongs to the PR/MR that chose the version. Every moved pin is still reported in the chat, with the old and new version and the size of the move, as Step 9 says, so it is seen.
