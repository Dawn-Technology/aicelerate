---
name: asvs-audit
description: "Static OWASP ASVS 5.0 Level 1 security audit of a codebase. Checks all 70 Level 1 requirements plus other security issues found on the way, verifies every finding against the code to remove false positives, runs the package manager's dependency audit, and writes a report to docs/. Use this when asked for a security audit, ASVS audit, security compliance review, or a code-level vulnerability scan. It reads code only; it is not a live penetration test."
metadata:
  author: "Martin Roest <martin.roest@dawn.tech>"
  version: 3.0.0
  asvs-version: 5.0.0
argument-hint: "Target repository path (defaults to the current directory)"
---

# OWASP ASVS 5.0 Level 1 Security Audit

This skill produces an audit report that a security reviewer can sign off: every one of the 70 ASVS 5.0 Level 1 requirements gets one status, every failure lists every place in the code where it occurs, and every claim has been checked against the code before it reaches the report. Two runs on the same commit should produce the same statuses; only the dependency result (#69) can change, because advisory databases keep growing.

You are the coordinator. You build a shared picture of the application, send two independent workers to evaluate it, check everything they return, and write the report.

## Ground rules

- **Read-only.** The only file you write in the target repository is the report. Working files go in a private folder outside it (see [audit-rules.md § Working files](./references/audit-rules.md#working-files)). Do not run the application, install dependencies, or change the target repository in any other way.
- **Static only.** Judge what the code and the configuration in the repository show. Never claim something was tested at runtime.
- **No secrets in output.** Follow the sensitive-file and redaction rules in [audit-rules.md](./references/audit-rules.md).
- **One source of truth.** The requirements are the 70 rows of `assets/OWASP_Application_Security_Verification_Standard_5.0.0_L1_en.csv`, in file order. Row number = item number (#1–#70).
- **Same rules for everyone.** [audit-rules.md](./references/audit-rules.md) defines statuses, evidence, scope and the worker output. It applies to the workers and to you.

Reference files, all relative to this skill's directory:

| File | Use |
|---|---|
| [references/audit-rules.md](./references/audit-rules.md) | Statuses, evidence format, files in scope, working files, worker output schema |
| [references/requirements-guide.md](./references/requirements-guide.md) | Per item: when it applies, what PASS and FAIL look like, what to search, default severity |
| [references/framework-defaults.md](./references/framework-defaults.md) | Protections a framework gives by default, per requirement, and how they get bypassed |
| [references/severity-guidance.md](./references/severity-guidance.md) | How to set severity |
| [references/REPORT-TEMPLATE.md](./references/REPORT-TEMPLATE.md) | The report structure |
| [EXAMPLES.md](./EXAMPLES.md) | Filled-in report fragments |

The bundled helpers need only Python 3.8 or later. On Windows, run them with `py -3` where this file says `python3`. Use them as provided; do not write replacement fingerprint or report-assembly scripts.

## Phase 1: Prepare

If you are resuming after a context reset, go to [Resuming after a reset](#resuming-after-a-reset) instead.

1. **Resolve the target.** Use the path the user gave, otherwise the current directory. Stop with an error if it does not exist or contains no source files.
2. **List the files in scope** with the rules in [audit-rules.md § Files in scope](./references/audit-rules.md#files-in-scope).
3. **Profile the project** and record:
   - Project name: use a name explicitly supplied by the user; otherwise take the first non-empty name from these root manifests in order: `package.json` (`name`), `pyproject.toml` (`project.name`, then `tool.poetry.name`), `composer.json` (`name`), `Cargo.toml` (`package.name`), a single `*.csproj` (an unambiguous literal `<AssemblyName>`, otherwise the file stem), or `go.mod` (the last segment of the `module` path, ignoring a trailing `/v2`, `/v3`, etc.). With several root `.csproj` files or no manifest name, use the `origin` remote's repository name without `.git`, otherwise the directory name. Lowercase it and replace anything other than `a-z`, digits and `-` with `-`. Keep literal manifest names even when they look like template defaults; do not guess a replacement or infer the name from earlier reports.
   - App version: the `version` field in the same manifest table, or a literal `<Version>` then `<VersionPrefix>` for `.csproj`; otherwise `unknown`.
   - Git commit: `git rev-parse --short HEAD`, otherwise `unknown`. If `git status --porcelain` lists changes, audit the files as they are on disk and record the commit as `<hash>-dirty`, with the number of changed and untracked files. The report then describes code that is not in any commit.
   - Content fingerprint: run `python3 "<skill dir>/scripts/fingerprint.py" "<target path>"` and record its eight-character output unchanged. The helper applies the Git or non-Git scope, omits deleted files and earlier audit reports, and hashes sorted paths, file types and contents. Symlinks are hashed by their link target without following them. Git submodules are hashed by the commit the repository records for them and untracked nested repositories by their path, because Git searches do not look inside either. It prints no file contents and exits non-zero on errors or an empty scope. Use this same command on resume; never recompute the fingerprint with an ad hoc command.
   - Components: every deployable unit (web front end, API, worker, and so on) with its root path. A single-app repository has one component.
   - Per component: languages, frameworks with versions, database, authentication method, key security libraries.
4. **Create the working folder.** If the host gives you a per-session folder outside the target repository (such as `<session-folder>/files/` in Copilot), run `mkdir -m 0700 -p "<session-folder>/files/asvs-audit-<project-name>"`. Otherwise run `mktemp -d "${TMPDIR:-/tmp}/asvs-audit-<project-name>-XXXXXX"`, which creates a folder only you can read. Never put it inside the target repository (including `<target>/.claude` or `<target>/.copilot`). Tell the user the path in your next progress message. Every file named below lives in this folder.
5. **Build the inventory.** Search the files in scope and record each item below with its `path:line`. This is the map both workers start from, so be exhaustive rather than quick.
   - Entry points: every HTTP route or handler (method, path, and whether it requires login), server actions, GraphQL resolvers, WebSocket handlers, queue consumers and scheduled jobs that take outside input.
   - Authentication: login, logout, registration, password change, password reset, MFA, token issuing and token validation code. Note whether an external identity provider is used.
   - Authorization: middleware, guards, policies and where they are attached.
   - Data access: database clients, ORMs, and every raw query.
   - Output: server templates, front-end frameworks, and every place that writes raw HTML.
   - Dangerous operations: process execution, file system paths built from input, outbound HTTP calls, XML parsing, deserialization, dynamic code execution.
   - Crypto and tokens: encryption, hashing, random token generation, JWT handling.
   - Cookies and security headers set in code or configuration.
   - Deployment configuration: Dockerfiles, `.dockerignore`, web server configs, infrastructure as code, platform configs (for example `vercel.json`, Helm charts, Terraform).
   - Security documentation: `SECURITY.md`, `docs/`, ADRs, API specifications.
6. **Run the dependency audit** once per lock file or dependency manifest of a production component. Use only commands that read the lock file and change nothing, for example `npm audit --omit=dev --json`, `pnpm audit --prod --json`, `yarn npm audit --environment production --json`, `composer audit --no-dev --format=json`, `govulncheck ./...`, `cargo audit --json`, or `pip-audit --no-deps --disable-pip -r requirements.txt` when `pip-audit` is already installed and every line in the requirements file pins an exact version (`==`). Never run `pip-audit` in a way that resolves or builds packages, because that can execute package code; when the requirements are not fully pinned, record that a safe audit could not run. Skip any command that would install, restore or write files. For .NET, run `dotnet list package --vulnerable --include-transitive --no-restore` only when the SDK accepts `--no-restore`. These commands send package names and versions, not code, to the package registry's advisory service. Record per lock file: the command, the counts per severity, and every advisory with package, installed version, advisory ID, severity, publication date when given, and fixed version. If no command can run for a lock file, record why.
   Redirect each command's output to `deps-<n>.txt` and read it from there with a short script or `jq`; never print raw audit output to the conversation.
7. **Write `profile.md`** with the target path, the git commit and fingerprint (record the fingerprint also for a clean tree, so a resume can detect changes), the skill version, the project profile, the inventory, and the dependency audit record per lock file.

## Phase 2: Independent evaluation

Dispatch two workers, `ASVS-A1` and `ASVS-A2`, in parallel when the host allows. Each must run on a different model, because a second worker on the same model tends to repeat the first one's mistakes. Pick the two most capable distinct models from the list this host currently lets you assign to a worker; when unsure which is more capable, take them in the order the host lists them. Do not rely on model names remembered from earlier runs; models get retired. If the host offers only one model, run `ASVS-A1` alone. This is **one-model mode**: continue without asking, and say so in the report.

Give each worker the same brief:

> You are `<label>`, an application security auditor. Audit the repository at `<target path>` against OWASP ASVS 5.0 Level 1.
> Read these files first and follow them exactly: `<skill dir>/references/audit-rules.md`, `<skill dir>/references/requirements-guide.md`, `<skill dir>/references/framework-defaults.md`, and the requirements in `<skill dir>/assets/OWASP_Application_Security_Verification_Standard_5.0.0_L1_en.csv`.
> Project profile, inventory and dependency audit results: read `<working folder>/profile.md`.
> Treat the inventory as a starting point. When you find entry points or sensitive code it misses, use them and list them in `inventory_additions`.
> Evaluate all 70 items in CSV order. For each item, check every relevant location, not just the first one you find. Record every search you ran. Then run the other-findings checklist in audit-rules.md and report issues that do not belong to any of the 70 items under `other_findings`.
> Write the JSON described in audit-rules.md § Worker output to `<working folder>/<label>.json`, with secrets redacted. Write no other files. Reply with one line only: the number of items and the count per status.

Never paste the Phase 1 output into the brief, and never ask a worker to return its JSON in the conversation.

When the workers are done, check each worker file in one command, for example:

```
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); n=sorted(i["item"] for i in d["items"]); m=sorted(set(range(1,71))-set(n)); assert "other_findings" in d and "other_findings_searches" in d, "missing other_findings"; print("missing:", m, "duplicates:", len(n)-len(set(n)))' <working folder>/ASVS-A1.json
```

If a file is missing or not valid JSON, run that worker again once. If items are missing, send the worker the missing item numbers once and ask it to add them to its file. Items still missing after that are evaluated by you.

## Phase 3: Merge and verify

This phase is what keeps false positives out of the report. Agreement between workers is not proof: both can cite the same line for the wrong reason.

Read the worker files in small batches, for example one ASVS chapter (5–10 items) at a time:

```
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); a,b=int(sys.argv[2]),int(sys.argv[3]); print(json.dumps([i for i in d["items"] if a<=i["item"]<=b], indent=1))' <working folder>/ASVS-A1.json 1 8
```

Never print a whole worker file, and never cut off an item's `evidence` list. When one item has many locations, read its `evidence` array in slices until you have seen every entry.

1. **Merge the inventory.** Add every `inventory_additions` entry that you confirm exists to `profile.md`.
2. **Collect candidates.** Scan the FAIL items and `other_findings` of both workers across all 70 items first. Record every claim that belongs to a different item, or to the other findings, in `reassigned.md` with its source and target. Then, per item, take the union of all FAIL locations from both workers plus the inbound claims for that item in `reassigned.md`. Merge duplicates only as described in [audit-rules.md § Evidence](./references/audit-rules.md#evidence), including its cross-item rule: one detailed finding per vulnerability, with references from other affected FAIL items. When several locations share one root cause, group them under that cause but keep every location. Note where the workers' statuses differ.
3. **Work through the items in order**, #1 to #70, then the other findings. For each:
   1. **Check coverage.** For an item that applies, and for the other-findings checklist, run the searches yourself and make sure every first-party hit is accounted for: cited by a worker, or explained as harmless. Evaluate every unaccounted hit; this catches what both workers missed.
   2. **Verify every candidate** with the checks in [audit-rules.md § Verification](./references/audit-rules.md#verification). Read the code yourself; do not rely on the worker's quote or reasoning. Keep a location only when every check passes. Each rejected location goes in the report's "Checked and rejected" list with a one-line reason. Count candidates as defined in [audit-rules.md § Counting candidates](./references/audit-rules.md#counting-candidates).
   3. **Set the status** with the rules in [audit-rules.md § Statuses](./references/audit-rules.md#statuses):
      - FAIL when at least one location survived verification.
      - Otherwise PASS, N/A or NEEDS_REVIEW, but only after you verified the evidence for that status as described in § Verification. When the workers disagree, decide from your own check, not from which worker sounds more confident.
      - In one-model mode, the same checks apply; there is just one set of candidates.
   4. **For the other findings**, drop one only when it describes the same underlying vulnerability as a verified FAIL under one of the 70 items; a different issue at the same location stays.
   5. **Set severity** for a FAIL item or other finding with [severity-guidance.md](./references/severity-guidance.md).
   6. **Save the verdict.** Append one section to `verdicts.md`, written in the report's own Markdown format so it can be copied into the report unchanged:

      ```
      ## #<n>
      Status: <status>. Candidates: <checked> checked, <rejected> rejected.
      <!-- finding -->
      <finding block for an owned FAIL, or "See finding #<owner>." for a shared FAIL; otherwise empty>
      <!-- review -->
      <needs-review row, NEEDS_REVIEW only; otherwise empty>
      <!-- verification -->
      <verification summary row>
      <!-- evidence -->
      <evidence appendix block>
      <!-- rejected -->
      <one checked-and-rejected line per rejected candidate; otherwise empty>
      <!-- end #<n> -->
      ```

      Keep all five block markers, even for empty blocks. A shared-only FAIL counts zero candidates here; its owner counts them once. If an item also has its own separate failures, keep its detailed finding and reference the shared issue there.

      The other findings get one `## other-findings` section with `Candidates: <checked> checked, <rejected> rejected.` and the same five block markers. Its `finding` block has findings headed `### O: <title>` (numbered and sorted by the helper), its `evidence` block has the other-findings checklist, and its `rejected` block has the rejected lines; leave `review` and `verification` empty. Finish with `<!-- end other-findings -->`. A section without its end line is unfinished.
4. **Handle claims you move during verification.** When verifying one item shows that a claim belongs to another item or to the other findings:
   - If the target is not verified yet, record the claim in `reassigned.md`. Never write a placeholder for the target in `verdicts.md`: a resume would then skip that item.
   - If the target is already in `verdicts.md`, re-open its whole section and update it (status, for example PASS to FAIL; severity; finding block; verification summary row; evidence appendix block), then mark the claim resolved in `reassigned.md`.

   Before Phase 4, every entry in `reassigned.md` must be resolved.

## Phase 4: Write the report

1. **Write `report-metadata.json`** in the working folder from `profile.md`, using [audit-rules.md § Report metadata](./references/audit-rules.md#report-metadata). Then assemble and check the report:

   ```
   python3 "<skill dir>/scripts/report.py" --metadata "<working folder>/report-metadata.json" --verdicts "<working folder>/verdicts.md" --output "<working folder>/report.md"
   ```

   The helper uses [REPORT-TEMPLATE.md](./references/REPORT-TEMPLATE.md), checks all 70 IDs, statuses, evidence blocks, needs-review rows, finding references and candidate counts, and computes totals and compliance scores. It writes nothing if these checks fail. Fix the input and rerun it; do not bypass the checks or edit the generated totals.
2. **Read `report.md`** for correctness and redaction. The helper checks structure, not whether the evidence is true or contains secrets. Confirm every failure is explained, shared failures are cross-referenced, and no secret values appear anywhere.
3. **Publish it** by copying `report.md` in one step to `<target>/docs/<project-name>-ASVS-L1-audit-<YYYY-MM-DD>.md`, using today's local date. Create `docs/` if needed. If the file exists, add `-2`, `-3`, and so on before `.md`; never overwrite a report.
4. **Delete the working folder.**
5. Tell the user the file path, the status counts, the number of failures per severity, and how many candidates were rejected during verification.

## Resuming after a reset

When the conversation was compacted or restarted mid-audit, do not start over. Find the working folder: `<session-folder>/files/asvs-audit-<project-name>`, the path you gave the user earlier, or the `asvs-audit-<project-name>-*` folder in the temp directory whose `profile.md` names this target. Then check in order:

1. `profile.md` exists, and the commit and fingerprint still match the repository. Run the exact `fingerprint.py` command from Phase 1 again; it re-lists the current files, including the non-Git fallback. If the code changed, tell the user, delete the folder, and start over from Phase 1. If a valid fingerprint cannot be computed, stop and keep the working folder; never resume using `unknown` or an empty-input hash.
2. `ASVS-A1.json` (and `ASVS-A2.json` in two-model mode) exist and pass the check in Phase 2. Run any missing or broken worker again.
3. Resume Phase 3 at the first of #1 to #70, then the other findings, then the unresolved entries in `reassigned.md`, that has no finished section in `verdicts.md`. Delete an unfinished section and redo that item from the start; keep every finished one.

## When something goes wrong

| Situation | What to do |
|---|---|
| CSV missing or not 70 rows | Stop: "ASVS CSV not found or incomplete at `<path>`". |
| Target path missing or has no source files | Stop and say which. |
| Git unavailable | Use the fallback file list in audit-rules.md; set the commit to `unknown`. |
| File inventory or fingerprint unavailable | Retry once, then stop and keep the working folder if it still fails. Do not write a report or reuse saved verdicts without a valid fingerprint. |
| A command or file read fails | First read the exit code as described in audit-rules.md § Searching; a search with no hits is not a failure. For a real failure, retry once. If it fails again, the item becomes NEEDS_REVIEW with reason `tool-failure` and the error in the question, unless the item already has a verified FAIL, which stays. |
| No dependency audit can run | Item #69 becomes NEEDS_REVIEW with reason `tool-failure`; say which command was missing. |
| The code changed since the audit started | Found on resume when the commit or fingerprint no longer matches `profile.md`. Tell the user, delete the working folder, and start over from Phase 1. |
| You cannot finish all 70 items, or the audit stops early | Do not write a report. Tell the user which items remain and why. A report always covers all 70. Give the working folder's path, warn that it holds vulnerability details, and give the command to delete it: `rm -rf <working folder>`. |
