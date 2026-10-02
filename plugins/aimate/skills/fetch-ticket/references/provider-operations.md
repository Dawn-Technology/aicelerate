# Provider operations for reading a ticket

Concrete identifier rules, routes, commands, and field mappings used by [`fetch-ticket`](../SKILL.md). Other skills link here for the routing table; the commands that write to a tracker or a code host stay with the skill that writes.

Rules that apply to every command here:

- Use `acli`, `gh`, `glab`, or the matching MCP server. Never use raw `curl`. Use `git` only for local repository reads.
- Never pass `--show-token`, and never ask the user for a token in chat.
- GitLab always uses `glab`; there is no GitLab MCP route. Confluence and Figma are MCP-only.
- **Never guess a flag.** Where a section says to verify against `--help`, verify before running. If `--help` does not offer the capability, use the MCP route.
- Replace `{key}` (Jira), `{owner}`, `{repo}`, `{issue_number}` (GitHub), and `{project_path}`, `{issue_iid}` (GitLab) with the parsed identifiers. GitLab project paths are URL-encoded in API endpoints: `group/project` becomes `group%2Fproject`.
- `glab api` has no `--jq` flag; pipe its output to `jq` instead. The high-level `glab issue` commands do accept `--jq`.
- Everything here is read-only. Nothing creates, edits, transitions, assigns, or comments on anything.

---

## Identifier parsing

| Input shape | Provider | Identifiers |
| --- | --- | --- |
| `ABC-123` | jira | `{key}` |
| `https://{site}.atlassian.net/browse/ABC-123` | jira | `{key}` from the path |
| `https://{site}.atlassian.net/jira/software/projects/ABC/boards/1?selectedIssue=ABC-123` | jira | `{key}` from `selectedIssue` |
| `https://github.com/{owner}/{repo}/issues/{n}` | github | `{owner}`, `{repo}`, `{issue_number}` |
| `https://{ghes-host}/{owner}/{repo}/issues/{n}` | github | same, plus the host for `--hostname` |
| `https://gitlab.com/{group}/{project}/-/issues/{n}` | gitlab | `{project_path}`, `{issue_iid}` |
| `https://{gitlab-host}/{group}/{sub}/{project}/-/issues/{n}` | gitlab | full path including subgroups |
| `#{n}` or a bare number | from `git remote get-url origin` | issue number or iid |

Disambiguation, before fetching anything:

- A URL containing `/pull/`, `/pulls/`, or `/-/merge_requests/` is a pull or merge request, not a ticket. Return `stop_reason: pull-request`.
- A Jira key is `PROJECT-NUMBER`. `PROJECT` alone is a project, not a work item — return `stop_reason: not-a-ticket`.
- A GitHub issue number and a pull request number share one sequence in a repository, so `#42` can be either. `gh issue view 42` fails on a pull request; that failure is the answer, not an error to work around.
- A GitLab issue iid and merge request iid are separate sequences, so the path segment is the only reliable signal.

## Route resolution

Follow the `aimate:tool-routing` block in the project's `AGENTS.md`: an explicit instruction in the request, then the preferred route, then the configured fallback. Without a block, use this order:

| Provider | Preferred | Fallback | Never |
| --- | --- | --- | --- |
| jira | `acli` | Atlassian MCP | — |
| github | `gh` | GitHub MCP | raw `curl` |
| gitlab | `glab` | none | GitLab MCP, raw `curl` |

Validate the route read-only, then stop asking:

```bash
acli jira auth status
gh auth status --active --hostname {host}
glab auth status --hostname {host}
```

Validate an MCP route with tool discovery plus, only when authentication is still in doubt, one harmless read-only metadata call.

When no route works, return `status: stopped`, `stop_reason: no-route`, and the login command (`acli jira auth login`, `gh auth login`, `glab auth login`), or Aimate's `configure-mcp` skill when the project has no route configured at all. The caller decides whether to continue from pasted text.

The same table and checks serve a caller that needs a code-host route (`gh` or `glab`) for its own writes.

Compare the authenticated host with the ticket's host. A GitLab.com route cannot read a self-hosted issue, and a `github.com` route cannot read a GitHub Enterprise one.

## Repository match

| Tracker | `repo_match` |
| --- | --- |
| github | `match` when `{owner}/{repo}` equals the `origin` remote's path, else `mismatch` |
| gitlab | `match` when `{project_path}` equals the `origin` remote's path, else `mismatch` |
| jira | No repository binding exists. Decide from the ticket: code references, component, linked PRs/MRs, and linked PRs/MRs. Return `undetermined` with that evidence; the caller decides once it has tested the ticket against the checkout. |
| none | `match` |

## Canonical ticket model

Normalize into this shape and return it. Nothing in a calling skill should need a provider field name.

```yaml
ticket:
  provider: jira | github | gitlab | none
  id: ABC-123 | 42 | 42
  url: canonical browse/web url
  title: string
  description: raw body text, in the provider's own format
  type: story | bug | task | epic | spike | unknown
  status: provider status name, plus open/closed where the provider has only two states
  labels: [strings, including component and type labels]
  reporter: display name
  assignee: display name or null
  parent: {id, title, type} or null
  children: [{id, title, status}]
  links: [{relation: blocks | blocked-by | relates | duplicates, id, title, status}]
  code_refs: [{kind: pull-request | merge-request | branch | commit, id, state, url}]
  comments: [{id, author, created_at, body}]      # in chronological order
  attachments: [{name, kind}]                     # names only, never fetched
  estimate: {field, value} or null
  iteration: sprint, milestone, or iteration name or null
  ac_field: {field, value} or null                # only when the project uses one
  provider_limits: [what this tracker cannot express]
```

Field mapping:

| Canonical | Jira | GitHub | GitLab |
| --- | --- | --- | --- |
| `id` | `key` | `number` | `iid` |
| `title` | `fields.summary` | `title` | `title` |
| `description` | `fields.description` (ADF on v3, wiki on v2) | `body` (markdown) | `description` (markdown) |
| `type` | `fields.issuetype.name` | issue type, or a `type::` label | a `type::` label, or the work item type |
| `status` | `fields.status.name` | `state` + `stateReason` | `state` |
| `labels` | `fields.labels` + `fields.components` | `labels` | `labels` |
| `reporter` | `fields.reporter` | `author` | `author` |
| `assignee` | `fields.assignee` | `assignees[0]` | `assignees[0]` |
| `parent` | `fields.parent` (epic or parent) | parent issue, when sub-issues are in use | `epic`, or parent work item |
| `children` | `fields.subtasks` | sub-issues | child work items or task list |
| `links` | `fields.issuelinks` | timeline cross-references | issue links |
| `code_refs` | development field, or linked branches | timeline events and `closingIssuesReferences` | related merge requests |
| `comments` | `fields.comment.comments` | `comments` | notes, excluding system notes |
| `attachments` | `fields.attachment` | images inline in `body` | uploads inline in `description` |
| `estimate` | a story-point custom field | none natively; a project field | `weight` |
| `iteration` | a sprint custom field | `milestone` | `milestone` or `iteration` |

Record in `provider_limits` anything the tracker cannot express — GitHub has no native estimate field, GitLab has no dedicated acceptance-criteria field, a Jira project may have no sprint field. A provider limit is never a readiness finding.

## Jira custom fields

Story points, acceptance criteria, sprint, and team fields are **per-site custom fields**. Their ids differ between sites, so never hardcode one and never copy an id from an example.

Discover them instead:

- Read the field list the route exposes — `acli jira` field or work-item metadata commands, or the MCP server's field/metadata tool — and match on the field **name** (`Story Points`, `Story point estimate`, `Acceptance Criteria`).
- Prefer a route that returns rendered field names over one that returns raw `customfield_*` keys.
- If no acceptance-criteria field exists, the criteria belong in the description. That is a project convention, not a gap.

State the discovered field name and id in the report the first time you use it, so the user can correct a wrong match.

## Fetching a ticket

### Jira

Use the `acli jira workitem` command family. Confirm the available subcommands and output flags before running them, because they differ across releases:

```bash
acli jira workitem --help
acli jira workitem view --help
```

Then fetch, preferring whatever machine-readable output flag the installed build offers:

```bash
# The work item itself, with comments where the build supports it
acli jira workitem view {key}

# Linked and child items, one hop
acli jira workitem search --jql 'parent = {key} OR issue in linkedIssues("{key}")'
```

If comments are not part of the view output on the installed build, fetch them through the route's comment read command, or switch to the Atlassian MCP route and use its issue-read tool. Do not conclude a ticket has no comments because the CLI did not print any.

On the **Atlassian MCP** route, use the server's issue-read tool for the work item and its comments, and its JQL-search tool for children and links. Both are read-only.

### GitHub

```bash
# Issue, comments, and metadata in one call
gh issue view {issue_number} --repo {owner}/{repo} \
  --json number,title,body,state,stateReason,labels,assignees,author,milestone,createdAt,updatedAt,url,comments

# Cross-references, closing links, and sub-issue events
gh api repos/{owner}/{repo}/issues/{issue_number}/timeline --paginate

# Sub-issues, when the repository uses them (verify availability on GitHub Enterprise)
gh api repos/{owner}/{repo}/issues/{issue_number}/sub_issues
```

On the **GitHub MCP** route, use the server's issue-read and issue-comment-list tools with `{owner}`, `{repo}`, and `{issue_number}`.

### GitLab

```bash
# Issue and metadata
glab issue view {issue_iid} --repo {project_path} --output json

# Notes, newest last; filter out system notes before treating any as a comment
glab api "projects/{project_path_encoded}/issues/{issue_iid}/notes?per_page=100" | jq '[.[] | select(.system == false)]'

# Issue links, and merge requests that reference this issue
glab api "projects/{project_path_encoded}/issues/{issue_iid}/links" | jq '.'
glab api "projects/{project_path_encoded}/issues/{issue_iid}/related_merge_requests" | jq '.'
```

GitLab system notes ("changed the description", "mentioned in commit") are activity, not comments. Excluding them matters: a system note is never a **Decision**.

### Provider none

There is nothing to fetch. Treat the pasted text as `description`, set every other field to null, and record in `provider_limits` that no field metadata, comments, or links were available. The caller has no tracker to write to.
