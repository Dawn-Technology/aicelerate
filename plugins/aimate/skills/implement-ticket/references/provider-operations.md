# Provider operations for delivering a ticket

The code-host operations used by [`implement-ticket`](../SKILL.md): finding work in flight, naming the branch, opening the PR/MR, and linking it to the ticket. Reading the ticket — identifier parsing, route resolution, repository match, fetching — belongs to [`fetch-ticket`](../../fetch-ticket/SKILL.md) and its [provider operations](../../fetch-ticket/references/provider-operations.md).

Two providers are in play on every run, and they can differ:

- **The tracker** holds the ticket — Jira, GitHub, GitLab, or none for pasted text. `fetch-ticket` resolves it as `ticket_route`.
- **The code host** receives the PR/MR — GitHub or GitLab, taken from the `origin` remote. Resolve it as `code_route` with the same [route resolution](../../fetch-ticket/references/provider-operations.md#route-resolution) rules.

A Jira ticket delivered as a GitHub PR is normal. Keep the two routes separate and never infer one from the other.

Rules that apply to every command here:

- Use `gh`, `glab`, or the GitHub MCP server. Never use raw `curl`. Use `git` for local, worktree, and push operations.
- Never pass `--show-token`, and never ask the user for a token in chat.
- **Never guess a flag.** Where a section says to verify against `--help`, verify before running.
- Nothing here edits, transitions, assigns, labels, or comments on the ticket. The only remote writes are the branch push and the PR/MR.

---

## Finding work already in flight

Search open PRs/MRs on the code host for the ticket id and for the ticket's key terms:

```bash
gh pr list --repo {owner}/{repo} --state open --search "{ticket_id} OR {keywords}"
glab mr list --repo {project_path} --search "{ticket_id}"
```

Also check the ticket's own linked PRs/MRs from the fetch. An open one that already implements the ticket feeds the "already done" check in stage 4.

## Branch and commit references

| Tracker | Branch id segment | Commit links line |
| --- | --- | --- |
| jira | the key, upper-case: `feat-ABC-123-slug` | none needed — `write-commit-message` reads the key from the branch name |
| github | the number: `feat-137-slug` | `Ref: #137` |
| gitlab | the iid: `feat-137-slug` | `Ref: #137` |
| none | no id: `feat-slug` | none |

Follow the branch naming already in `git branch -a` when the repository has one; keep the Jira key in it either way, since both `write-commit-message` and Jira's development panel find the ticket through it. A line that starts with `#137` is dropped by `git commit --cleanup=strip`, which is why the reference is written `Ref: #137`.

## Opening the PR/MR

Write the body to a file first. Run from inside the worktree so the CLI reads the repository from `origin`.

### GitHub

```bash
gh pr create --base {default_branch} --head {branch} --title "{title}" --body-file {file}
```

On the **GitHub MCP** route, use the create-pull-request tool with the same fields.

### GitLab

```bash
glab mr create --source-branch {branch} --target-branch {default_branch} \
  --title "{title}" --description-file {file} --yes
```

Verify the flags against `glab mr create --help` first.

### Linking the ticket

| Tracker | In the title | Last line of the body | Effect on merge |
| --- | --- | --- | --- |
| github | — | `Closes #{issue_number}` | issue closes |
| gitlab | — | `Closes #{issue_iid}` | issue closes when merged into the default branch |
| jira | `{key}: ` prefix | `{key}` with its browse URL | none — the work item is linked through the key, never transitioned |
| none | — | nothing | — |

## Failure handling

- A push or PR/MR create that fails ambiguously may have landed. List the branch's PRs/MRs through the same route before retrying, and never create a second one.
- Never switch routes mid-write.
- A rejected push is never force-pushed. Report it and keep the branch.
