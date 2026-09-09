# Provider operations for ticket validation

Concrete identifier rules, commands, and field mappings used by [`validate-ticket`](../SKILL.md). Read the section you need at the step that needs it.

Rules that apply to every command here:

- Use `acli`, `gh`, `glab`, or the matching MCP server. Never use raw `curl`. Use `git` only for local repository reads.
- Never pass `--show-token`, and never ask the user for a token in chat.
- GitLab always uses `glab`; there is no GitLab MCP route. Confluence and Figma are MCP-only.
- **Never guess a flag.** Where a section says to verify against `--help`, verify before running. If `--help` does not offer the capability, use the MCP route, or ask the user to run it. A wrong flag on a write is a corrupted ticket.
- Replace `{key}` (Jira), `{owner}`, `{repo}`, `{issue_number}` (GitHub), and `{project_path}`, `{issue_iid}` (GitLab) with the identifiers resolved in Step 0. GitLab project paths are URL-encoded in API endpoints: `group/project` becomes `group%2Fproject`.
- `glab api` has no `--jq` flag; pipe its output to `jq` instead. The high-level `glab issue` commands do accept `--jq`.
- Every read here is read-only. Nothing in the fetch sections creates, edits, transitions, or assigns anything.

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

- A URL containing `/pull/`, `/pulls/`, or `/-/merge_requests/` is a pull or merge request, not a ticket. Stop and say so.
- A Jira key is `PROJECT-NUMBER`. `PROJECT` alone is a project, not a work item — ask which item.
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

When no route works, stop before any fetch and point at the login command (`acli jira auth login`, `gh auth login`, `glab auth login`), or at Aimate's `configure-mcp` skill when the project has no route configured at all. Then offer to continue from ticket text the user pastes, with `provider = none`.

Compare the authenticated host with the ticket's host. A GitLab.com route cannot read a self-hosted issue, and a `github.com` route cannot read a GitHub Enterprise one.

## Canonical ticket model

Normalize into this shape in Step 2, and let nothing downstream know provider field names.

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

There is nothing to fetch. Treat the pasted text as `description`, set every other field to null, and record in `provider_limits` that no field metadata, comments, or links were available. Every remote write sub-step in Step 8 is unavailable, so the report in chat — including the proposed description in full — is the only output.

## Posting a comment

Write the body to a file first, so quoting and markdown survive the shell.

### Jira

Verify the comment subcommand and its body flag before using it:

```bash
acli jira workitem --help    # locate the comment subcommand on this build
```

Post through that subcommand, or through the Atlassian MCP route's add-comment tool. Prefer MCP for a long, structured body: it takes the content as a parameter rather than through shell quoting.

### GitHub

```bash
gh issue comment {issue_number} --repo {owner}/{repo} --body-file {file}
```

### GitLab

```bash
glab issue note {issue_iid} --repo {project_path} -m "$(cat {file})"
```

Confirm the subcommand name against `glab issue --help` first; some builds expose it as `glab issue comment`. When the body is large enough to strain the shell, post it through `glab api` instead:

```bash
glab api --method POST "projects/{project_path_encoded}/issues/{issue_iid}/notes" --input {json_file}
```

Verify the request-input flag against `glab api --help` before running it.

## Updating the description

Only with explicit approval, and only once the original description is preserved outside the conversation — provider edit history, or a comment carrying it posted before the overwrite.

### Jira

The description is a formatted field, so the write path is the risky one. Verify the edit subcommand and its description flag:

```bash
acli jira workitem edit --help
```

If the build cannot set a description from a file, use the Atlassian MCP route's issue-edit tool rather than forcing a long body through shell arguments. Re-read the field afterwards, always.

### GitHub

```bash
gh issue edit {issue_number} --repo {owner}/{repo} --body-file {file}
gh issue view {issue_number} --repo {owner}/{repo} --json body --jq '.body' | head -40
```

### GitLab

```bash
glab issue update {issue_iid} --repo {project_path} --description "$(cat {file})"
glab issue view {issue_iid} --repo {project_path} --output json --jq '.description' | head -40
```

When the body is too large for an argument, use the API with a JSON body:

```bash
glab api --method PUT "projects/{project_path_encoded}/issues/{issue_iid}" --input {json_file}
```

## Description formatting

The [agent-ready description template](../SKILL.md#agent-ready-description-template) is markdown. What that means per provider:

- **GitHub** — markdown renders as written, including `- [ ]` task lists, tables, and fenced code. Post it unchanged.
- **GitLab** — the same, with GitLab-flavoured markdown. `- [ ]` becomes a clickable task list. Post it unchanged.
- **Jira** — markdown is **not** the field format. A description written in markdown and posted through an ADF or wiki-markup field renders as literal `##` and `- [ ]`, which is worse than the original. Before writing:
  1. Establish which format the resolved route accepts — ADF, wiki markup, or a markdown input the route converts for you. Check the route's own documentation or `--help`; do not infer it from a successful write.
  2. Convert headings and lists to that format. In wiki markup, `## Why` becomes `h2. Why` and a bullet becomes `* item`.
  3. Where a construct has no equivalent, degrade to something that survives — bold labels and plain bullets rather than tables and checkboxes — and keep the section order and every word of the content.
  4. Re-read the field and confirm it rendered. If it did not, restore the preserved original and report it.

Never lose content to a format conversion. Losing a checkbox is acceptable; losing an acceptance criterion is not.

## Write failure reconciliation

A comment or description write that fails ambiguously may already have landed.

1. Re-read the ticket through the same route before retrying — comments first, then the description field.
2. Post or write only what is actually missing. Never resend a batch.
3. Never switch routes mid-write. A retry on the other route is how a ticket ends up with the same comment twice.
4. If a description write half-applied, restore the preserved original before trying again.
5. Report what landed, with the comment or note id, and what did not.
