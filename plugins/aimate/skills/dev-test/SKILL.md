---
name: devtest
description: Use when the user wants to know how to manually test code changes on a branch - analyzes the diff, identifies what changed, and produces a step-by-step guide a real person can follow to verify the feature or fix works, including any required setup like fixtures, mock SPs, or config. Also use when asked for a test plan, QA checklist, or "how do I test this PR".
metadata:
  author: Kay Joosten <kay.joosten@dawn.tech>
  version: 1.1.0
agents:
  - claude
  - copilot
---

# DevTest — Manual Testing Guide

## Overview

Analyze the code changes on the current branch and produce a clear, step-by-step manual testing guide a real person can follow to verify the changes work. Include setup requirements, test scenarios, and expected outcomes.

## Process

### Step 0 — Detect input mode

Determine how the diff will be obtained before proceeding. There are two modes:

**Mode A — MR URL provided**
The user has given a GitLab MR URL (e.g. `https://gitlab.com/org/repo/-/merge_requests/123`).

1. Detect provider from URL:
   - URL contains `gitlab.com` or a self-hosted GitLab domain → `provider = "gitlab"`
   - If ambiguous, ask the user
2. Verify GitLab MCP tools are available in the current session.
   If missing → **do not proceed silently**. Use one of the following approaches:

   **Option A — inline guidance** (when the user just needs quick instructions):
   > GitLab MCP is not installed. See the `install-mcp-server` skill for setup instructions, then re-run this skill with the MR URL.

   **Option B — dispatch as subagent** (when running inside an automated workflow):
   > Dispatch the `install-mcp-server` skill as a subagent with input: `provider = "gitlab"`. Wait for confirmation that installation succeeded, then continue from step 3 below.

   After either option, if MCP is still unavailable → fall back to Mode B and notify the user.

3. Extract `project_path` and `merge_request_iid` from the URL.
4. Fetch MR details using GitLab MCP:
   - Title, description, source/target branches, author
   - The MR diff (changed files + hunks)
   - Existing discussion threads (to understand intent and any prior review context)
5. Store `diff_source = "gitlab_mcp"` and proceed to Step 1 using the fetched diff.

**Mode B — local branch (default)**
No MR URL was provided, or GitLab MCP is unavailable.

Use git to obtain the diff locally:

```bash
git log main...HEAD --oneline
git diff main...HEAD --stat
git diff main...HEAD
```

Store `diff_source = "local_git"` and proceed to Step 1.

---

### Step 1 — Understand the changes

Using the diff obtained in Step 0, answer:
- What is the intent of the change? (feature, bug fix, config, refactor)
- Which user-facing behaviors are affected?
- Are there any setup requirements (fixtures, flags, config values, mock clients)?
- **Are there non-user-visible changes (logging, metrics, internal refactors)?** If so, note this explicitly — the test guide must describe how to verify them indirectly.

### Step 2 — Identify test scenarios

For each behavior changed:
- **Happy path** — the thing that should now work
- **Edge cases** — boundary conditions touched by the change
- **Regression** — existing behavior that should still work

### Step 3 — Discover project context

Before identifying setup requirements, understand how this project runs. Work through the following sources in order, stopping as soon as you have enough confidence.

**3a — Read agent instruction files**

Check for existing AI context files in the project root:

```bash
cat CLAUDE.md 2>/dev/null
cat .github/copilot-instructions.md 2>/dev/null
cat .copilot-instructions.md 2>/dev/null
cat AGENTS.md 2>/dev/null
```

Extract from these files:
- How to start / run the application locally
- How to run tests
- How to load fixtures or seed data
- Any project-specific commands or environment requirements

**3b — Detect infrastructure from project files**

If agent instruction files are absent or incomplete, scan the project root:

```bash
ls -1 docker-compose*.yml Makefile justfile package.json composer.json \
       Dockerfile .env.example README.md 2>/dev/null
```

Use what you find to infer the stack:

| Signal | Inferred setup pattern |
|--------|----------------------|
| `docker-compose.yml` | Use `docker compose up` / `docker compose exec` for commands |
| `Makefile` | Run `make help` or scan targets for `test`, `start`, `fixtures` |
| `composer.json` | PHP project — check `scripts` block for test/lint commands |
| `package.json` | JS/TS project — check `scripts` block |
| `Dockerfile` only | Container-based — infer run commands from `CMD`/`ENTRYPOINT` |
| `.env.example` | Read for required env vars and service URLs |
| `README.md` | Last resort — scan for "getting started" or "running locally" section |

**3c — Ask if still uncertain**

If after 3a and 3b you cannot confidently answer all of the following, **stop and ask the user** before writing the guide:

- How do I start the application for local testing?
- How do I run the test suite?
- Is there a fixture/seed command, and if so what is it?
- How do I access logs?

Ask only the questions you cannot answer from the project files. Do not guess and embed wrong commands in the guide.

Store the discovered context as `project_context` — use it to populate all commands in Step 4.

### Step 4 — Identify setup requirements

Using `project_context` from Step 3, check whether testing requires any of the following:

| Category | Examples (generic — adapt to project) |
|----------|---------------------------------------|
| Fixtures / seed data | Seeding command found in Makefile, composer scripts, or README |
| Mock services | External services referenced in `.env.example` that need a local stub |
| Config / parameters | Feature flags, env vars that must be set to enable the changed behavior |
| Database state | Specific records that must exist before the scenario can run |
| Frontend build | Asset compilation step required before testing UI changes |
| External service | Third-party integrations referenced in the diff |
| Security / authz | Required roles, permissions, or auth state for the scenario to be reachable |

### Step 5 — Write the guide

Structure the output as follows:

---

## Manual Testing Guide: [Feature/Fix Name]

### Context
[One sentence: what was changed and why]

### Stack
[One line summary of how the project runs, e.g. "PHP/Symfony app via docker compose" or "Next.js app, run with `npm run dev`"]

### Prerequisites
- [ ] [Environment requirement derived from project_context]
- [ ] [Setup step with the exact command as discovered in Step 3]
- [ ] [Any additional services or state required]

### Test Scenarios

#### Scenario 1: [Scenario name]
1. [Navigate to / open / run — use exact URLs or commands from project_context]
2. [Perform action]
3. **Expected:** [What you should see or happen]

#### Scenario 2: [Regression check — describe what should still work]
1. ...
2. **Expected:** ...

### Cleanup (if needed)
- [Any state to reset after testing]

### Verdict
**Testable by:** [developer / QA / both]
**Risk level:** [low / medium / high] — [one sentence why]
**Confidence check:** Is this change covered by automated tests? [yes / partial / no — describe gap]

---

## Tips for Good Guides

- Use exact commands as discovered from the project — never invent commands
- For API changes: include example curl commands with real endpoints from the project
- For UI changes: mention which environment or theme to use if the project supports multiple
- If changes are behind a feature flag or config toggle: specify exactly how to enable it using the project's actual config mechanism
- If the change is not user-visible (e.g. logging, internal refactor): say so clearly in the Context block and describe how to verify indirectly — e.g. check logs using the command discovered in Step 3, run a specific flow and confirm no errors appear
- Never write "verify it works" without a concrete expected outcome — every scenario needs an explicit Expected line
- Flag scenarios that cannot be tested without production data