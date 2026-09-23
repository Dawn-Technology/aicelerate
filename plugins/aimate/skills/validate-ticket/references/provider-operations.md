# Provider operations for writing to a ticket

The tracker writes used by [`validate-ticket`](../SKILL.md): comments, title and description updates, and their formatting. Identifier parsing, route resolution, field mapping, and every read live in [`fetch-ticket`'s provider operations](../../fetch-ticket/references/provider-operations.md). Read the section you need at the step that needs it.

Rules that apply to every command here:

- Use `acli`, `gh`, `glab`, or the matching MCP server. Never use raw `curl`. Use `git` only for local repository reads.
- Never pass `--show-token`, and never ask the user for a token in chat.
- GitLab always uses `glab`; there is no GitLab MCP route. Confluence and Figma are MCP-only.
- **Never guess a flag.** Where a section says to verify against `--help`, verify before running. If `--help` does not offer the capability, use the MCP route, or ask the user to run it. A wrong flag on a write is a corrupted ticket.
- Replace `{key}` (Jira), `{owner}`, `{repo}`, `{issue_number}` (GitHub), and `{project_path}`, `{issue_iid}` (GitLab) with the identifiers `fetch-ticket` returned. GitLab project paths are URL-encoded in API endpoints: `group/project` becomes `group%2Fproject`.
- `glab api` has no `--jq` flag; pipe its output to `jq` instead. The high-level `glab issue` commands do accept `--jq`.
- Write through the same `ticket_route` `fetch-ticket` returned. Never switch routes to write.

---

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

## Updating the title

Written with the description, under the same approval, and only when the title changed. The old title goes into the comment that notes the rewrite, so it survives whatever the tracker keeps in its history.

### Jira

The title is the `summary` field. Confirm the flag against `acli jira workitem edit --help` on this build, then:

```bash
acli jira workitem edit --key {key} --summary "{title}"
```

Or use the Atlassian MCP route's issue-edit tool. Re-read the summary through the same route afterwards.

### GitHub

```bash
gh issue edit {issue_number} --repo {owner}/{repo} --title "{title}"
gh issue view {issue_number} --repo {owner}/{repo} --json title --jq '.title'
```

### GitLab

```bash
glab issue update {issue_iid} --repo {project_path} --title "{title}"
glab issue view {issue_iid} --repo {project_path} --output json --jq '.title'
```

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

The [agent-ready description template](description-template.md#template) is markdown. What that means per provider:

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
