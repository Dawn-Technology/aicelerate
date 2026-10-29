# Audit rules

These rules apply to the coordinator and to every worker. They exist so that two runs on the same commit reach the same statuses, and so that nothing reaches the report without evidence someone can check.

## Files in scope

Audit the files git tracks plus untracked files git does not ignore: `git ls-files --cached --others --exclude-standard` in the target repository. This leaves out installed dependencies and build output, and keeps monorepo folders such as `packages/` and `apps/` in scope. Without git, take all files and leave out `node_modules/`, `vendor/`, `dist/`, `build/`, `out/`, `target/`, `.next/`, `coverage/`, `__pycache__/` and version control folders.

Always leave out earlier reports of this skill (`docs/*-ASVS-L1-audit-*.md`). They quote requirements and search terms and would distort searches and documentation checks.

Within that list:

- **Never cite as evidence**: vendored third-party code (`vendor/`, `third_party/`, `node_modules/`), minified or bundled files (`*.min.js`, `*.bundle.js`), and generated code marked as generated.
- **Read for context, never cite for a FAIL**: tests, fixtures, examples, storybook stories and mock servers. They do not run in production. They may support a PASS, for example a test that proves a control works. One exception: a real secret committed anywhere in the repository is an other finding, because the repository itself exposes it.
- **Lock files**: read for the dependency audit and to find the installed version of a library when a decision depends on it.
- **Large files**: never sample. Search inside the file and read the matching regions with enough surrounding lines to understand them.

### Sensitive files

Never print the contents of `.env` and `.env.*` (except `.env.example`, `.env.sample` and `.env.template`), `*.pem`, `*.key`, `*.p12`, `*.pfx`, `id_rsa*`, `secrets.*`, `credentials.*`, or cloud credential files.

To decide whether such a file, or any other match from the hard-coded secrets checklist, holds a real secret, inspect it without printing values: for each candidate, print only the file, line, key name, value length, and whether the value looks like a placeholder or a reference (`changeme`, `replace`, `example`, `xxx`, `<...>`, `${...}`, `process.env`, `os.environ`). For key files, `grep -c "PRIVATE KEY"` is enough. A real secret is a non-placeholder value for a credential, key, token, password or connection string. Never report a file from its name alone; public certificates, placeholders and non-sensitive settings are not secrets.

When a quote would contain a secret, token, password, connection string or personal data, replace the value with `<redacted>`. Refer to environment variables as `env:NAME`, never with their value.

## Searching

Search the files in scope with a literal, case-sensitive search by default:

```
git grep -n -I -F --untracked -e '<term>' -- <paths>
```

Add `-i` when the term's case varies, or replace `-F` with `-E` for a regular expression; record which. Without git, use `grep -rnIF`. A hit is one matching line. Record the exact command, the number of hits, and how many of them are first-party production lines after leaving out the never-cite and test categories above.

A search tool exiting with "no matches" or an audit tool exiting non-zero because it found vulnerabilities is a result, not a tool failure.

## Statuses

Every item gets exactly one status. Decide by the first rule that matches.

1. **❌ FAIL**: at least one failure survived verification. For requirements that demand something exist (a password change function, a rate limit, a size limit), its verified absence is a FAIL. A failure stays a FAIL even when other parts of the item could not be checked; name those parts in the finding.
2. **⚪ N/A**: the item's "Applies when" condition in [requirements-guide.md](./requirements-guide.md) is false in production code and configuration. Decide this by reading the search hits, not by counting them: a constant `fetch("/health")` does not make user-controlled outbound URLs apply. Zero hits support N/A only after you also checked the inventory and the framework's own way of doing the same thing. Never use N/A because something is hard to check.
3. **⚠️ NEEDS_REVIEW**: the deciding evidence is unavailable, for one of these reasons only:
   - `deployment`: the setting lives in infrastructure that is not in the repository (TLS termination, proxy headers, hosting).
   - `external-docs`: the requirement depends on documentation and none was found in the repository or provided by the user.
   - `external-system`: an external service owns the behavior or the deciding data, and it is not in the repository (a hosted identity provider's password policy, advisory publication dates the audit tool does not give).
   - `tool-failure`: a file or command needed for the decision failed twice.

   Code you can read is never NEEDS_REVIEW: read it and decide. Every NEEDS_REVIEW states the reason code and the exact question a person must answer to close it.
4. **✅ PASS**: the control exists and covers every relevant location in the inventory, or, where the requirement is about something being absent (for example #7 dynamic code execution, #39 password hints), the searches show it is absent. A control that covers some routes but not others is a FAIL for the uncovered ones.

When an application has several components, decide per component, then give the item the worst result in this order: FAIL, NEEDS_REVIEW, PASS, N/A.

## Evidence

Every claim is an evidence entry with three parts:

- `location`: `path:line` or `path:start-end`, relative to the repository root. Two special forms exist: `framework:<name>@<version>:<feature>` for a framework default, always paired with a second entry pointing to where that framework is set up, and `audit:<command> (<lock file>)` for a dependency audit result.
- `quote`: a self-contained excerpt of at most 200 characters that shows the operation and the value or argument the reason depends on. Use the whole line when it fits; for long or multi-line code, the smallest contiguous excerpt that is still understandable. A function or command name alone is not enough. Redact secrets and personal data. Leave it empty only for `framework:` and `audit:` entries.
- `reason`: one sentence saying why this location passes or fails the requirement.

What each status needs:

- **FAIL**: one entry per failing location, listing every location, not a sample. When the failure is a missing control, the entry points to where the control should be (the route, handler or config file) and the searches show it is absent.
- **PASS**: at least one entry pointing at the control itself and the searches showing nothing bypasses it; or, for a PASS by absence, no entries and the searches.
- **N/A**: the searches and one sentence on why the condition is false.
- **NEEDS_REVIEW**: the reason code, the question, and what was searched.

Every item records its searches as described in § Searching.

Overlapping or touching ranges are not duplicates by themselves. Merge them only when they describe the same vulnerability, keeping the range and quote that cover the full vulnerable operation; otherwise keep both, even when they cite the same lines.

In report tables, escape `|` in a quote as `\|`, and wrap a quote that contains a backtick in double backticks (``` `` ... `` ```).

When one vulnerability breaks several requirements, put its detailed finding under the most specific requirement (tie: lowest item number), keep the other affected items FAIL with a reference to that finding, and count the candidate once at its owner. Do not merge issues that need different fixes.

## Verification

The coordinator runs these checks before anything enters the report. Read the code yourself.

For each FAIL location in code or configuration:

1. **It exists.** Open the file at the cited lines and confirm the quoted code is there, allowing `<redacted>` in place of a secret value. If it is not, reject it. When the location is valid but the quote is only a bare function or command name, replace the quote with a proper excerpt from the file (see § Evidence) instead of rejecting the candidate.
2. **It is production code.** Not a test, fixture, example, dead code (nothing calls it) or a development-only path (guarded by a development environment check, or a script that never ships). Otherwise reject it.
3. **It is reachable.** Trace from an inventory entry point to the location. For injection and similar issues, input the user controls must reach it without passing a check that already stops the attack. If no path exists, reject it. If the path leaves the repository (for example an external caller), keep it and say so in the reason.
4. **Nothing else already protects it.** Look for a compensating control on the path: global middleware, framework configuration, validation earlier in the call chain, or proxy configuration in the repository. If one fully covers the location, reject it.
5. **It breaks this requirement.** Re-read the requirement text. A real issue that belongs to a different item moves to that item; one that belongs to none becomes an other finding.

Two kinds of finding are checked differently, because they do not depend on running code:

- **Dependency advisories**: confirm the package and installed version appear in the lock file and that the advisory's affected range includes that version.
- **Committed secrets**: confirm the file is in scope and the value is a real secret by the inspection in § Sensitive files. Reachability does not matter.

For an absent control, also re-run the worker's searches plus the search terms in requirements-guide.md. If the control turns up, re-evaluate the item.

For coverage, re-run the searches for every applicable item and for the other-findings checklist. Every first-party hit must be cited by a worker or explained as harmless; evaluate any other hit and send failures through the checks above.

For each PASS: open the cited control and confirm it does what the reason says, and that it applies to every relevant inventory entry point (for example, middleware mounted globally rather than on one router). Gaps become FAIL locations, which go through the FAIL checks. For a PASS by absence, re-run the searches.

For each N/A: re-run the searches and read the hits. If any shows the condition is true in production, the item applies.

For each NEEDS_REVIEW: confirm the reason is one of the four codes and the deciding evidence really is unavailable. If you can read it, decide the item.

### Counting candidates

The report's verification line counts candidates. A candidate is one unique failing location (`path:line` and vulnerability) in code or configuration proposed by either worker, after exact duplicates are merged. Dependency advisories are not candidates; they are counted in the dependency audit summary. A candidate moved to another requirement or to the other findings is judged and counted at its destination: verified if it survives verification there, rejected if it fails there. Never count it as rejected merely because it moved.

## Working files

The coordinator keeps audit state in a private working folder outside the target repository, so a context reset does not lose finished work and large outputs stay out of the conversation. [SKILL.md](../SKILL.md) says when each file is written.

| File | Contents |
|---|---|
| `profile.md` | Target path, git commit, scoped-file fingerprint, skill version, project profile, inventory, and a short dependency audit summary per lock file. |
| `deps-<n>.txt` | Raw output of one dependency audit command. Never printed whole to the conversation. |
| `ASVS-A1.json`, `ASVS-A2.json` | Worker output (§ Worker output). |
| `verdicts.md` | Finished item verdicts and the other-findings verdicts, written in the report's own Markdown format. |
| `reassigned.md` | Claims moved to another item or to the other findings during verification, until their target is verified. |
| `report-metadata.json` | Report identity, component rows and narrative text, in the schema below. Counts come from verdicts, not this file. |
| `report.md` | The assembled report before it is copied to `docs/`. |

- Working files hold only redacted evidence, never raw secret values (§ Sensitive files). The same applies to workers.
- Treat the folder as confidential: it holds vulnerability details. Delete it once the report is published.
- Workers read `profile.md` and write only their own JSON file in the folder. They never write anywhere else.

### Report metadata

The report helper takes these fields from `profile.md` and the coordinator's summary. All scalar values are non-empty strings; use `unknown` or `None` explicitly where appropriate. Include one component object per deployable unit. Do not put counts, verdicts or unredacted secrets here.

```json
{
  "project_name": "<normalized project name>",
  "app_version": "<version or unknown>",
  "git_commit_hash": "<commit, dirty details and fingerprint, or unknown with fingerprint>",
  "report_date": "<YYYY-MM-DD>",
  "skill_version": "<skill version>",
  "coordinator_model": "<reported model or unknown>",
  "worker_models": "<reported models or unknown>",
  "model_provenance": "<what the host reported>",
  "execution_mode": "<two-model or one-model, with its limitation>",
  "executive_summary": "<overall posture and priorities>",
  "dependency_audit_statement": "<whether and when the audit ran>",
  "dependency_audit_summary": "<commands and advisory counts, or why unavailable>",
  "conclusion_text": "<risks and recommended order of work>",
  "components": [
    {
      "component": "<name>",
      "component_path": "<root path>",
      "language": "<languages>",
      "framework": "<frameworks and versions>",
      "database": "<database or None>",
      "auth_method": "<authentication method or None>",
      "key_libraries": "<security libraries or None>"
    }
  ]
}
```

## Worker output

Workers produce one JSON object:

```json
{
  "worker": "ASVS-A1",
  "model": "<model the host reports for this worker, otherwise unknown>",
  "inventory_additions": [
    { "kind": "entry-point", "location": "src/routes/export.ts:12", "note": "GET /export, requires login" }
  ],
  "items": [
    {
      "item": 4,
      "req_id": "V1.2.4",
      "status": "FAIL",
      "evidence": [
        {
          "location": "src/repo/orders.ts:41",
          "quote": "db.query(`SELECT * FROM orders WHERE id = ${req.params.id}`)",
          "reason": "Route parameter interpolated into SQL text."
        }
      ],
      "searches": [
        { "command": "git grep -n -I -F --untracked -e 'query(' -- src/", "hits": 7, "first_party_hits": 5 }
      ],
      "review_reason": null,
      "review_question": null
    }
  ],
  "other_findings_searches": [
    { "command": "git grep -n -I -F --untracked -e 'pickle.loads' -- .", "hits": 0, "first_party_hits": 0 }
  ],
  "other_findings": [
    {
      "title": "Hard-coded API key",
      "evidence": [
        { "location": "src/lib/mail.ts:5", "quote": "const KEY = \"<redacted>\"", "reason": "Live API key committed to source." }
      ],
      "proposed_severity": "High"
    }
  ]
}
```

`items` has exactly 70 entries in CSV order. `status` is one of `PASS`, `FAIL`, `N/A`, `NEEDS_REVIEW`. `review_reason` is one of the four codes when the status is NEEDS_REVIEW, otherwise `null`. `model` is the model the host reports for this worker, otherwise `unknown`. Never guess.

The worker writes this object to `ASVS-A1.json` or `ASVS-A2.json` in the working folder (see § Working files) and replies with one line only: the number of items and the count per status.

## Other findings

Report a security issue that none of the 70 items covers, with the same evidence and verification as a FAIL. Do not report a problem here when it fits one of the 70 items.

Always run this checklist and record the searches in `other_findings_searches`, also when nothing is found. Report anything else you notice the same way.

- **Hard-coded secrets**: `password =`, `secret =`, `api_key`, `apiKey`, `token =`, `Bearer `, `AKIA`, `sk_live_`, `ghp_`, `xox`, `-----BEGIN`, connection strings with a password (`://user:pass@`). Matches are candidates; confirm each with the inspection in § Sensitive files. These terms do not catch every format, so also look at configuration files (JSON, YAML, `export NAME=`) in the inventory.
- **Tracked secret files**: the sensitive-file rules above.
- **Known vulnerable dependencies**: every advisory from the dependency audit that is not already a FAIL under #69, grouped per lock file, with the advisory's severity (Medium when the tool gives none).
- **Password storage**: how stored passwords are hashed. Anything other than a password hashing function (bcrypt, scrypt, Argon2, PBKDF2) is a finding: `md5(`, `sha1(`, `sha256(`, `createHash(` near password handling.
- **Unsafe deserialization**: `pickle.loads`, `yaml.load(` without a safe loader, `unserialize(`, `BinaryFormatter`, `ObjectInputStream`, `Marshal.load`, `node-serialize`, applied to data the user controls.
- **Debug mode in production**: `DEBUG = True`, `app.debug`, `debug: true`, `UseDeveloperExceptionPage` outside a development check, stack traces returned in error responses.
- **Mass assignment**: request bodies passed whole to create or update calls (`create(req.body)`, `update(req.body)`, `**request.data`, `$request->all()`, `permit!`).
