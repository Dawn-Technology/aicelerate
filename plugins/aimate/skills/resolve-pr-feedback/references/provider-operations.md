# Provider operations for feedback resolution

Concrete commands, GraphQL documents, and API payloads used by [`resolve-pr-feedback`](../SKILL.md). Read the section you need at the step that needs it.

Rules that apply to every command here:

- Use `gh`, `glab`, or the matching GitHub MCP server. Never use raw `curl`.
- Never pass `--show-token`, and never ask the user for a token in chat.
- GitLab always uses `glab`; there is no GitLab MCP route.
- Replace `{owner}`, `{repo}`, `{pull_number}` (GitHub) and `{project_path}`, `{mr_iid}` (GitLab) with the identifiers resolved in Step 0. `{n}`, `{wt}`, and `{fix_branch}` follow the [SKILL.md](../SKILL.md) notation. GitLab project paths are URL-encoded in API endpoints: `group/project` becomes `group%2Fproject`.

---

## Write access checks

Run these in Step 0, before creating a worktree.

### GitHub

```bash
# Viewer permissions on the target repository
gh api repos/{owner}/{repo} --jq '.permissions'

# Head branch location and whether maintainers may push to a fork branch
gh pr view {pull_number} --repo {owner}/{repo} \
  --json isCrossRepository,maintainerCanModify,headRefName,headRepositoryOwner,headRepository,state,isDraft
```

Pushing to the head branch requires `permissions.push` on the repository that owns it. For a cross-repository PR that means either write access on the fork or `maintainerCanModify: true` combined with write access on the base repository.

### GitLab

`glab api` has no `--jq` flag; pipe its output to `jq` instead. The high-level `glab mr` commands do accept `--jq`.

```bash
# Access level on the target project: 30 = Developer, 40 = Maintainer, 50 = Owner
glab api "projects/{project_path}" | jq '.permissions'

# MR source project, source branch, and fork push permission
glab mr view {mr_iid} --output json \
  --jq '{source_project_id, target_project_id, source_branch, allow_collaboration, state, draft}'
```

Pushing to the source branch requires at least Developer access on the source project, or `allow_collaboration: true` plus Developer access on the target project when the MR comes from a fork.

---

## Fetching threads

### GitHub

Thread grouping and resolution state only exist in GraphQL. The REST endpoints give comment bodies but not thread ids.

```bash
gh api graphql -F owner={owner} -F repo={repo} -F number={pull_number} -f query='
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      title
      baseRefName
      headRefName
      reviewThreads(first: 100) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          isOutdated
          path
          line
          startLine
          diffSide
          comments(first: 50) {
            nodes {
              id
              databaseId
              author { login }
              body
              createdAt
            }
          }
        }
      }
    }
  }
}'
```

Keep both ids per thread: the GraphQL `id` of the thread for resolving, and the `databaseId` of its **first** comment for REST replies. Page with `endCursor` when `hasNextPage` is true; a PR with more than 100 threads is common on long-running work.

Supporting data:

```bash
gh pr view {pull_number} --repo {owner}/{repo} \
  --json title,body,author,baseRefName,headRefName,labels,commits,reviews,comments,reviewDecision,isDraft
```

MCP route: use the matching GitHub MCP pull-request tools to read the PR, its reviews, and its comments. Most GitHub MCP servers expose no thread-resolution capability — when resolution is needed and the MCP route cannot do it, say so and fall back to `gh api graphql` per the project's routing table.

### GitLab

Prefer the high-level thread commands; they page and filter for you.

```bash
# Every discussion, as JSON
glab mr note list {mr_iid} --output json

# Only the unresolved diff threads — the default working set
glab mr note list {mr_iid} --type diff --state unresolved --output json

# MR metadata
glab mr view {mr_iid} --output json
```

`glab mr note` is marked experimental and is missing from older `glab` builds. If the subcommand is unavailable, fall back to the API:

```bash
glab api --paginate "projects/{project_path}/merge_requests/{mr_iid}/discussions?per_page=100"
glab api "projects/{project_path}/merge_requests/{mr_iid}"
```

Notes on the shape:

- A discussion is the thread. `notes[].resolvable` marks the ones tied to the diff; `notes[].resolved` marks the state.
- `notes[].system: true` marks activity entries (label changes, pushes). Filter them out of the working set.
- `notes[].position` carries `new_path`, `old_path`, `new_line`, `old_line`, and the `base_sha`/`start_sha`/`head_sha` triple.
- `notes[].type` is `DiffNote` for inline feedback and `DiscussionNote` for replies in a thread.

---

## Fork heads

When the head branch lives in another repository, fetch from and push to that repository instead of `origin`.

### GitHub

```bash
gh pr view {pull_number} --repo {owner}/{repo} \
  --json headRepositoryOwner,headRepository,headRefName \
  --jq '"\(.headRepositoryOwner.login)/\(.headRepository.name) \(.headRefName)"'

git remote add pr-head https://github.com/{head_owner}/{head_repo}.git
git fetch pr-head {head_branch}
git worktree add {wt} -b {fix_branch} pr-head/{head_branch}
```

Push with `git -C {wt} push pr-head {fix_branch}:{head_branch}`.

### GitLab

```bash
glab mr view {mr_iid} --output json --jq '.source_project_id'
glab api "projects/{source_project_id}" | jq -r '.http_url_to_repo'

git remote add mr-head {source_project_http_url}
git fetch mr-head {source_branch}
git worktree add {wt} -b {fix_branch} mr-head/{source_branch}
```

Push with `git -C {wt} push mr-head {fix_branch}:{source_branch}`.

Remove the temporary remote during Step 11 cleanup: `git remote remove pr-head` or `git remote remove mr-head`.

---

## Replying and resolving

### GitHub

Reply into an existing thread, using the `databaseId` of the thread's first comment:

```bash
gh api --method POST \
  repos/{owner}/{repo}/pulls/{pull_number}/comments/{first_comment_database_id}/replies \
  -f body='...'
```

Resolve the thread, using the GraphQL thread id:

```bash
gh api graphql -F threadId={thread_id} -f query='
mutation($threadId: ID!) {
  resolveReviewThread(input: { threadId: $threadId }) {
    thread { id isResolved }
  }
}'
```

Unresolve, when a thread was closed in error:

```bash
gh api graphql -F threadId={thread_id} -f query='
mutation($threadId: ID!) {
  unresolveReviewThread(input: { threadId: $threadId }) {
    thread { id isResolved }
  }
}'
```

A general PR comment, for anything that has no thread:

```bash
gh pr comment {pull_number} --repo {owner}/{repo} --body '...'
```

Re-request a review after pushing fixes:

```bash
gh api --method POST repos/{owner}/{repo}/pulls/{pull_number}/requested_reviewers \
  -f 'reviewers[]={reviewer_login}'
```

Resolution requires write access on the repository, or authorship of the PR. A permissions failure returns an error on the mutation while the reply already landed — leave the reply and report the thread as needing a human to close.

### GitLab

Reply into an existing discussion. `--reply` accepts the full discussion id or a prefix of at least eight characters:

```bash
glab mr note create {mr_iid} --reply {discussion_id} --message '...'
```

Resolve and reopen a discussion:

```bash
glab mr note resolve {mr_iid} {discussion_id}
glab mr note reopen {mr_iid} {discussion_id}
```

A general MR note, for anything that has no thread:

```bash
glab mr note create {mr_iid} --message '...'
```

API fallback, for older `glab` builds without the experimental `glab mr note` subcommands:

```bash
glab api --method POST \
  "projects/{project_path}/merge_requests/{mr_iid}/discussions/{discussion_id}/notes" \
  -f body='...'

glab api --method PUT \
  "projects/{project_path}/merge_requests/{mr_iid}/discussions/{discussion_id}?resolved=true"
```

Only resolvable discussions — those anchored to the diff — accept the resolve call. Resolving requires at least Developer access or authorship of the note. GitLab resolves the whole discussion at once; there is no per-note resolution.

---

## Failure handling

- **Ambiguous write failure**: fetch the current threads through the same route and compare before retrying. A transport error can follow a successful write, and a blind retry leaves a duplicate reply the author cannot easily remove.
- **Partial batch**: re-fetch, diff against the intended set, and post only what is missing.
- **Rate limiting**: `gh api rate_limit` shows the GitHub budget. Back off rather than switching routes mid-batch — a route switch after a partial write is how duplicates happen.
- **Route switching**: only switch to the configured fallback route before a batch starts, never in the middle of one.
