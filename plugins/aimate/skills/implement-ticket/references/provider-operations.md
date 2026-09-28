# Provider operations for delivering a ticket

The code-host operations used by [`implement-ticket`](../SKILL.md): finding work in flight, naming the branch, opening the PR/MR, and linking it to the ticket. Reading the ticket — identifier parsing, route resolution, repository match, fetching — belongs to [`fetch-ticket`](../../fetch-ticket/SKILL.md).

Two providers are in play on every run, and they can differ:

- **The tracker** holds the ticket — Jira, GitHub, GitLab, or none for pasted text. `fetch-ticket` resolves it as `ticket_route`.
- **The code host** receives the PR/MR — GitHub or GitLab, taken from the `origin` remote. Resolve it as `code_route` per [the code-host route](#the-code-host-route) below.

A Jira ticket delivered as a GitHub PR is normal. Keep the two routes separate and resolve each on its own.

Rules that apply to every command here:

- Use `gh`, `glab`, or the GitHub MCP server for every provider call, and `git` for local, worktree, and push operations.
- Authentication stays with the CLI or MCP login, and tokens stay hidden.
- **Check every flag.** Where a section says to verify against `--help`, verify before running.
- The only remote writes are the branch push and the PR/MR. The ticket is read only.

---

## The code-host route

Pick the route once, check it, then keep using it:

1. Follow the `aimate:tool-routing` block in the project's `AGENTS.md`: an explicit instruction in the request first, then its preferred route, then its fallback.
2. Without a block, GitHub uses `gh`, with the GitHub MCP server as the fallback. GitLab always uses `glab`, on its own.
3. Check the route read-only: `gh auth status --active --hostname {host}` or `glab auth status --hostname {host}`. For the GitHub MCP server, check that its tools are listed.
4. Log in to the `origin` host itself: a GitHub Enterprise or self-hosted GitLab remote needs a login for that host.

When no route works, stop and give the login command — `gh auth login` or `glab auth login` — or point to the `configure-mcp` skill when the project has no route set up at all.

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
| jira | the key, upper-case: `feat-ABC-123-slug` | the key, which `write-commit-message` reads from the branch name |
| github | the number: `feat-137-slug` | `Ref: #137` |
| gitlab | the iid: `feat-137-slug` | `Ref: #137` |
| pasted text | the slug only: `feat-slug` | — |

Follow the branch naming already in `git branch -a` when the repository has one; keep the Jira key in it either way, since both `write-commit-message` and Jira's development panel find the ticket through it. Write the reference as `Ref: #137`, because `git commit --cleanup=strip` removes every line that starts with `#`.

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

| Tracker | Last line of the body | Effect on merge |
| --- | --- | --- |
| github | `Closes #{issue_number}` | issue closes |
| gitlab | `Closes #{issue_iid}` | issue closes when merged into the default branch |
| jira | `{key}` with its browse URL | the work item stays linked through the key, with its status left as it is |
| pasted text | — | — |

## Failure handling

- A push or PR/MR create that fails ambiguously may have landed. List the branch's PRs/MRs through the same route before retrying, so the branch ends up with exactly one PR/MR.
- Finish each write on the route it started on.
- When a push is rejected, report it and keep the branch as it is. Every push is a plain `git push`.
