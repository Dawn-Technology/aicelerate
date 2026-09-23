---
name: playwright-test-pr
description: Test a PR or MR like a human QA engineer using Playwright MCP. Analyzes the diff (or diffs, for a multi-service/microservice feature spanning several PRs) to generate a scenario list (Phase 1), then executes each scenario live in a browser with inline logging and screenshots (Phase 2). Use when asked to "test this PR with Playwright", "browser-test this MR", "QA this PR", "QA this PR automatically", "run Playwright on this branch", "run browser tests on this PR", or "test this feature across these PRs/services".
metadata:
  author: Kay Joosten <kay.joosten@dawn.tech>
  version: 2.0.0
---

# playwright-test-pr

Test a PR or MR like a human QA engineer using the Playwright MCP. Two phases: static analysis generates a scenario list you can edit, then live browser execution runs each scenario and reports inline.

Supports both a **single PR/branch** and a **multi-service feature** — a feature split across several PRs in different repos (e.g. a microservice architecture where a frontend PR, an API PR, and an auth-service PR must all be running together to test the full flow).

---

## Step 0 — Verify Playwright MCP

Before any other action, verify Playwright MCP is installed by checking the current session's available tools for one matching Microsoft's official `@playwright/mcp` tool family. Do NOT require an exact match on the bare name `browser_navigate` — different agent runtimes expose MCP tools under different naming conventions. Some runtimes (e.g. GitHub Copilot CLI) namespace tool names with the MCP server name, e.g. `playwright-client-browser_navigate` instead of `browser_navigate`. Treat the check as satisfied if any available tool name **ends with** `browser_navigate` (and, ideally, sibling tools like `browser_click` and `browser_snapshot` also exist under the same prefix). If a tool-search capability is available, use it to search by suffix rather than relying on an exact string match.

This skill requires Microsoft's official `@playwright/mcp` package (`browser_*` tools, accessibility-snapshot based). It is NOT compatible with other Playwright MCP servers — in particular `@executeautomation/playwright-mcp-server` (`playwright_*` tools, raw HTML/text based) — if that server is installed instead, it must be replaced.

**If no tool matching `browser_navigate` (exact or suffix) is available — hard stop:**

> ❌ **Playwright MCP not installed.**
>
> Run the `configure-mcp` skill and select **Playwright** when asked which additional integrations this project needs — it adds the correctly pinned `@playwright/mcp` server with no further setup.
>
> If you need to add it manually instead, add an MCP server entry that runs `npx -y @playwright/mcp@0.0.79` (use this exact pinned version — do not use `latest` or an unpinned version, since a newer major/minor release could change the tool surface this skill relies on) over stdio, with `tools: ["*"]`. Consult your agent's MCP configuration mechanism (config file or `mcp add`-style command) for the exact syntax, since this varies by runtime and version — do not guess at a specific file path here.
>
> After installation, restart your agent session and re-run this skill.

Do NOT proceed. Do NOT attempt any browser action. Do NOT fall back silently.

---

## Step 1 — Fetch the Diff(s) via `review-pr`

> **Note on "delegate":** "Delegate to `review-pr`" means perform the specific `review-pr` steps described below (provider detection, MCP availability check, diff fetching) yourself, following that skill's documented behavior for those steps. If your agent runtime supports invoking `review-pr` as a literal nested skill/tool call, prefer that for consistency; otherwise, perform the equivalent steps directly. Either way, do not go beyond the steps listed below (no worktree, no findings, no comments).

**Determine scope first:**
- If the user provided a single PR/MR URL or referenced the current local branch → single-service mode (unchanged behavior).
- If the user provided multiple PR/MR URLs, or says this feature spans several repos/services → multi-service mode.

**Multi-service mode:**
1. For each PR/MR URL provided, ask the user (in one message, if not already stated) to label it with a short service name, e.g.:
   > Which service does each PR belong to? `https://github.com/org/frontend/pull/12` → ?, `https://github.com/org/auth-service/pull/7` → ?
2. For each labeled PR, invoke `review-pr` Steps 0 and 1 independently:
   - Provider detection (GitHub / GitLab / local)
   - MCP availability check and fallback logic
   - Fetching PR/MR title, description, source/target branches, and raw diff
3. Build a list of service entries, each storing:
   - `service`: the label (e.g. `"frontend"`, `"auth-service"`)
   - `pr_title`: the PR/MR title
   - `provider`: `"github"` / `"gitlab"` / `"local"`
   - `diff`: the full raw diff text

**Single-service mode:**

Do not implement diff fetching here. Delegate it entirely to the `review-pr` skill.

Invoke `review-pr` Steps 0 and 1 only:
- Provider detection (GitHub / GitLab / local)
- MCP availability check and fallback logic
- Fetching PR/MR title, description, source/target branches, and raw diff

Extract and store from the result:
- `pr_title`: the PR/MR title
- `provider`: `"github"` / `"gitlab"` / `"local"`
- `diff`: the full raw diff text

In both modes: do NOT continue into `review-pr` Steps 2 onwards (no worktree, no findings, no comments). Stop after the diff(s) are in hand and proceed to Step 2 below.

---

## Phase 1 — Static Analysis

### Step 2 — Identify Scenarios via `test-pr-guide`

Do not implement diff analysis or scenario identification here. Delegate it to the `test-pr-guide` skill — see the note under Step 1 above for what "delegate" means in practice.

**Single-service mode:** Invoke `test-pr-guide` Steps 1 and 2 using the `diff` obtained in Step 1.

**Multi-service mode:** Invoke `test-pr-guide` Steps 1 and 2 once **per service entry**, using that service's `diff`. Tag every resulting scenario with its `service` label before moving to Step 3. In Step 1 of `test-pr-guide`, additionally ask it to flag any cross-service touchpoints it can infer from the diff (e.g. an API endpoint or contract the diff calls or changes) — carry these forward as notes for de-duplication in Step 3.

In both modes — Step 1: Understand the changes (intent, affected behaviors, setup requirements, non-visible changes). Step 2: Identify test scenarios (happy path, edge cases, regression).

Do NOT continue into `test-pr-guide` Steps 3 onwards (no project context discovery, no guide writing). Stop after scenarios are identified.

### Step 3 — Convert to Playwright Scenario Format

Take the scenarios from `test-pr-guide` and convert each one into the following structured format. Add the Playwright-specific fields that `test-pr-guide` does not produce:

| Field | Description |
|-------|-------------|
| `id` | `S1`, `S2`, … |
| `name` | Short label (e.g. "Submit form with valid data") |
| `service` | Which PR/service this scenario originates from (e.g. `"frontend"`) — omit or set to `"n/a"` in single-service mode |
| `type` | `happy path`, `edge case`, or `regression` |
| `description` | Step-by-step browser actions — translate the human guide steps into Playwright actions |
| `expected` | Concrete, observable success criterion — never "it works" |
| `testable` | `true` / `false` — false if test-pr-guide flagged it as non-user-visible or indirect |
| `risk` | `high`, `medium`, or `low` — infer from the scenario's position and the affected behavior |
| `route` | URL path to navigate to — scan the diff for `href`, `router.push(...)`, `<Link>`, `path:` patterns to populate this |
| `requires_data` | `true` / `false` — true if test-pr-guide mentioned fixtures, seed data, or existing records |
| `requires_clean_state` | `true` / `false` — true for logout flows, fresh-user onboarding, or session-sensitive scenarios |

**Maximum 8 scenarios total across all services (not per service).** Prioritize by risk — cut the lowest-risk ones if needed and note them in the report. De-duplicate: merge scenarios that test the same action via the same route.

**Minimum per-service floor (multi-service mode only):** Before cutting scenarios for the cap, guarantee at least 1 scenario survives per service that produced any `testable: true` scenario, even if that service's remaining scenario ranks lowest-risk overall. Only cut a service down to zero scenarios if it produced none that are `testable: true` in the first place (e.g. entirely backend-only with no reachable UI route). If applying this floor pushes the total above 8, cut additional lowest-risk scenarios from services that already have 2+ surviving scenarios first, rather than removing a service's only scenario. If the floor itself already exceeds 8 — i.e. more than 8 services each contributed exactly one `testable: true` scenario, leaving no service with 2+ scenarios to trim from — keep the 8 highest-risk single-scenario services and drop the rest, listing each dropped service and its cut scenario under "Scenarios cut" in the report.

**Multi-service de-duplication:** If two services independently produced a scenario exercising the same end-to-end route (e.g. the frontend scenario "user logs in" and the auth-service scenario "auth endpoint validates credentials"), merge them into a single scenario driven through the frontend, and list all contributing services in `service` (e.g. `"frontend + auth-service"`). Prefer the scenario framed from the user-facing entry point — backend-only scenarios with no reachable UI route should be marked `testable: false` and noted as `🚫 not browser-testable (backend-only, covered indirectly via [dependent scenario id])`.

### Step 3.5 — Confirm How the App Under Test Should Be Run

Before asking the user for `entry_url` in Step 4, check whether the target repo documents its own required way of running/reaching the app for manual or QA testing — e.g. a `README`, `CONTRIBUTING.md`, `copilot-instructions.md`/`CLAUDE.md`, or a `docker-compose.yml` / devcontainer / dev-environment bootstrap script. Do this by looking at the repo root (already available from the worktree/diff fetched in Step 1) for these files, not by asking the user first.

- If the repo documents a specific containerized or scripted dev environment (e.g. Docker Compose, a `start-dev-env.sh`-style script, a devcontainer), assume that is the intended way to reach the app, and ask the user to confirm it's already running and reachable at a specific URL — do NOT default to an ad hoc workaround (bare language-runtime dev server, spoofed hostnames, self-signed certs invented on the fly) unless the user explicitly says the documented environment isn't available.
- If no such documentation exists, fall back to the plain `entry_url` question in Step 4 as before.
- If you find conflicting or ambiguous guidance, ask the user which environment to target rather than guessing.

This check exists because defaulting to an improvised environment can change the app's real behavior (different config, different origin/entity IDs, different cert trust) enough to produce misleading results that look like application bugs but are actually artifacts of the wrong test environment.

### Step 4 — Present Scenarios & Collect Inputs (hard stop)

Present the scenario list and ask these questions in one message. Show only summary columns in the table — keep `description` and `expected` internal. In multi-service mode, add a `Service` column.

```
Here are the scenarios I identified (sorted by risk):

| # | Name | Service | Type | Risk | Testable |
|---|------|---------|------|------|----------|
| S1 | [name] | frontend | happy path | 🔴 high | ✅ |
| S2 | [name] | frontend + auth-service | edge case | 🟡 medium | ✅ |
| S3 | [name] | auth-service | regression | 🟢 low | 🚫 (non-browser) |

Scenarios cut (risk-based): [list or "none"]

Before I start, I need a few things:
1. **Skip any scenarios?** Reply with IDs (e.g. `S2 S4`) or `none`.
2. **Screenshots?** Reply: `all` / `failures_only` / `none`.
3. **Entry URL?** The user-facing app Playwright will drive (e.g. `http://localhost:3000`). If Step 3.5 found no repo-documented dev environment, this defaults to `http://localhost:3000` if omitted. If Step 3.5 found a documented environment, do NOT apply the `localhost:3000` default — ask again for the specific URL that environment exposes.
4. **[Multi-service mode only] Backend service URLs?** For each non-UI service (e.g. `auth-service`), give a reachable health-check URL (e.g. `http://localhost:4001/health`) so I can confirm it's running before testing. Reply `skip` for a service to skip its reachability check (scenarios depending on it will still run, but failures may be harder to diagnose).
5. **Stop on first failure?** Reply: `yes` (default) / `no` (run all scenarios and report all failures at end).
6. **Viewport?** Reply: `desktop` (default, 1280×800) / `mobile` (390×844, iPhone 14) / `both` (run each scenario twice).
```

**Wait for the user's reply. Do NOT start Phase 2 until all answers are received.**

Parse the response:
- `skip_ids`: list of scenario IDs to skip (empty if "none")
- `screenshot_pref`: `all`, `failures_only`, or `none`
- `entry_url`: base URL for browser navigation — default to `http://localhost:3000` if not provided AND Step 3.5 found no repo-documented dev environment, mentioning this assumption. If Step 3.5 found a documented environment, do not apply this default; re-ask the user for the specific URL instead.
- `service_urls`: (multi-service mode only) map of `service label → health-check URL` (or `"skip"`)
- `fail_fast`: `true` (default) / `false`
- `viewport`: `desktop` (default) / `mobile` / `both`

**[Multi-service mode only] Pre-flight environment check:**

Before Phase 2 starts, verify every service is actually running:
1. For `entry_url`, this is verified naturally by the Step 5 session-initialization navigate — no separate check needed here.
2. For each entry in `service_urls` that is not `"skip"`, issue a lightweight reachability check (e.g. `browser_navigate` to the health-check URL, or an equivalent HTTP check if available) and confirm a non-error response.
3. If any service fails the check:
   > ⚠️ `[service]` is not reachable at `[url]`. Scenarios depending on it (`[scenario ids]`) may fail or produce misleading results.
   Ask the user: continue anyway, skip the affected scenarios, or abort. Do NOT guess — wait for a reply.
4. If all services respond, log:
   > ✅ All services reachable: [service: url, …]. Proceeding to Phase 2.

---

## Phase 2 — Browser Execution

For each scenario where `testable = true` AND `id` not in `skip_ids`, in order:

### Step 5 — Session Initialization (once per run)

Before the first scenario, navigate to `entry_url` via `browser_navigate` and store the resulting session state (cookies, localStorage) for reuse. This avoids re-authenticating on every scenario. In multi-service mode, all browser interaction still goes through `entry_url` only — backend services in `service_urls` are never navigated to directly by the user flow, only checked for reachability in Step 4.

If `viewport = "mobile"` or `viewport = "both"`, call `browser_resize` with `width: 390, height: 844` (iPhone 14) before this first navigation. `browser_resize` is a core `@playwright/mcp` tool and always available — no capability check or fallback is needed.

If a login wall is detected (see below), perform login **once** at this step. After a successful login, all subsequent `browser_navigate` calls in this run will reuse the established session. If a scenario still triggers a login screen (e.g. after a logout action), handle it inline at that point.

**Console and network monitoring (no setup required):**

`@playwright/mcp` exposes `browser_console_messages` and `browser_network_requests` as built-in tools — no script injection is needed, and there is nothing to re-inject after a navigation. Both calls default to messages/requests captured **since the last navigation** and reset automatically on every `browser_navigate`. Pass `all: true` on either tool only when full-session history is explicitly needed (e.g. final failure diagnostics spanning multiple navigations).

### Step 6 — Execution Loop

**Start each scenario:**

Log: `▶ Running [id]: [name]`

**Console/network isolation between scenarios:**

`browser_console_messages` and `browser_network_requests` both auto-scope to activity **since the last navigation**, so no manual buffer reset is needed. To guarantee a clean window per scenario, every scenario must begin with an explicit `browser_navigate` to its `route` (falling back to `entry_url` if `route` is empty) before executing its steps — this is also how "Clean state check" and viewport switching below hook in.

**Clean state check:**

If `requires_clean_state = true` for this scenario, wipe the session before the scenario's opening navigation:

1. Check whether the current MCP session exposes `browser_cookie_clear`, `browser_localstorage_clear`, and `browser_sessionstorage_clear` (these tools only exist when the server is configured with `--caps=storage`; the `configure-mcp` bundled template does not enable this by default). If all three are available, call them — this clears cookies (including HttpOnly ones) and both storage areas at the browser-context level, with no caveats.
2. If they are not available, fall back to `browser_evaluate`:

   ```js
   () => {
     localStorage.clear();
     sessionStorage.clear();
     document.cookie.split(';').forEach(c => {
       document.cookie = c.trim().split('=')[0] + '=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/';
     });
   }
   ```

   > ⚠️ **HttpOnly cookie limitation (fallback path only):** JavaScript cannot read or delete HttpOnly cookies — which most session tokens are. If the app uses HttpOnly session cookies, this fallback wipe will not fully clear the session. To work around this, attempt to navigate to a known logout endpoint (e.g. `/logout`, `/auth/signout`) before wiping storage. If no logout endpoint is known, log: `⚠️ HttpOnly cookies may persist — clean state is best-effort for this scenario.` and continue.

Then navigate to `entry_url` fresh via `browser_navigate`. Do NOT reuse the stored session credentials — if a login wall appears, ask the user again.

**Viewport:**

Before the scenario's opening navigation, set the viewport for the pass being run:
- `mobile` pass (or `viewport = "mobile"`): `browser_resize` with `width: 390, height: 844` (iPhone 14).
- `desktop` pass (default, or the desktop pass of `viewport = "both"`): `browser_resize` with `width: 1280, height: 800`.

`browser_resize` is a core `@playwright/mcp` tool and always available — no capability check or fallback is needed.

**Execute steps via Playwright MCP:**

Use these tools to interact with the browser. After each meaningful action, log a one-line summary inline. `browser_click`, `browser_type`, `browser_select_option`, and `browser_hover` all take an `element` (human-readable description, used in logs/errors) and a `ref` (obtained from the most recent `browser_snapshot` or `browser_find`) — take a fresh snapshot after any action that may have changed the DOM before targeting a new element, since a stale `ref` will error.

| Action | Tool |
|--------|------|
| Navigate to URL | `browser_navigate` with `url` |
| Go back | `browser_navigate_back` |
| Click element | `browser_click` with `element` + `ref` |
| Fill one input | `browser_type` with `element` + `ref` + `text` |
| Fill multiple inputs on one form | `browser_fill_form` with a `fields` array (element/ref/value per field) — one call, avoids the focus/event race a per-field fill approach is prone to |
| Select option | `browser_select_option` |
| Capture page structure + text | `browser_snapshot` |
| Search for text/element on the page | `browser_find` |
| Take screenshot | `browser_take_screenshot` |
| Wait for text to appear/disappear, or a fixed delay | `browser_wait_for` (takes `text` / `textGone` / `time` — **not** a CSS selector) |
| Run JS in browser | `browser_evaluate` |
| Read console messages since last navigation | `browser_console_messages` |
| Read network requests since last navigation | `browser_network_requests` |
| Resize viewport | `browser_resize` |
| Manage tabs | `browser_tabs` |

**Timeout & retry strategy:**

`browser_click`, `browser_type`, `browser_select_option`, and `browser_fill_form` include Playwright's native actionability auto-waiting — the call itself blocks until the target element is visible, enabled, and stable, up to the server's action timeout (typically 5 seconds). Do not add a manual pre-wait before these calls. If a call still times out or errors on the first attempt, wait 2 seconds, take a fresh `browser_snapshot` (the `ref` may now be stale), and retry once. If the second attempt also fails, treat it as a scenario failure (not a flaky skip). Log: `⚠️ Action failed after retry: [element description]`.

Use `browser_wait_for` explicitly only when a scenario needs to wait for asynchronous content to appear or disappear (e.g. a toast message, a spinner clearing) before the next action — pass `text`/`textGone`, never a selector.

**Form fill verification (multi-field forms):**

`browser_fill_form` fills every listed field in a single call, which removes most of the focus/event race a per-field fill approach was prone to. Still verify multi-field forms before submitting, since this remains a tooling-level risk, not an app bug, if left unchecked:

Whenever a scenario fills **two or more** fields on the same form before submitting:
- After all fills for that form are complete and immediately before the submitting click, run one `browser_evaluate` that reads back every filled field's live `.value` (e.g. `() => JSON.stringify({field1: document.getElementById('...').value, field2: ...})`) and confirm each matches exactly what was intended to be filled.
- If any field doesn't match (empty, truncated, or containing another field's text), do NOT submit yet — re-fill the mismatched field(s) via `browser_type` and re-verify before proceeding. Log: `⚠️ Field mismatch detected after fill, re-filling: [field]`.
- Only click submit once every field's actual DOM value has been confirmed correct.

This check must happen on the **DOM value** via `browser_evaluate`, not on the `browser_snapshot` accessibility tree — the accessible value can be trusted only for the outcome check after submission.

**Rule out test-tool flakiness before blaming the app:**

If a scenario's observed failure looks like corrupted, empty, truncated, or concatenated form/field data (e.g. multiple field values merged into one, or a value appearing where a different value was expected), this is a strong signal of an automation-layer timing artifact (see "Form fill verification" above), not a genuine product bug. Before reporting it as a failure:
1. Re-run the exact same scenario steps once more from a clean navigation (do not reuse the possibly-corrupted page state).
2. If the re-run produces correct results, treat the first run as flaky tooling, not a bug — do NOT report a failure. Log: `⚠️ [id] showed corrupted data on first attempt but passed cleanly on retry — treated as test-tooling flakiness, not an app bug.` and continue as `✅ passed`.
3. If the corruption reproduces consistently (2+ times) AND the DOM value verification above showed the fields were correct immediately before submission, only then escalate: capture the actual network request payload sent to the server (e.g. via `browser_network_requests`, browser devtools protocol, or server-side request logs if accessible) to confirm whether the corruption is present on the wire (real bug, investigate further) or only in Playwright's own DOM read (tooling artifact).

**Multi-tab & popup handling:**

If a scenario step triggers `window.open()`, an OAuth redirect, or a file download dialog:
- For new tabs: use `browser_tabs` (action: `list`) to find the new tab, `browser_tabs` (action: `select`) to switch to it, complete the required interaction, then switch back the same way. `browser_tabs` is a core `@playwright/mcp` tool and always available — no fallback or `⚠️ partial` path is needed for tab switching itself.
- For download dialogs: confirm the download was triggered by checking for a download filename or a success message — do not block on the file system.
- For OAuth popups: treat these as a login wall (see below) and ask for credentials if needed.

**Data setup check:**

Before executing a scenario where `requires_data = true`, run `browser_snapshot` (or `browser_find` for the specific expected element/text) on the relevant page to verify the required data already exists (e.g. an existing record, a pre-filled form). If the data is missing, log:
> ⚠️ Required test data not found for [id]. Skipping to avoid a false negative.
Mark as `⏭ skipped (missing data)` in the report and continue.

**After every `browser_navigate`**, run four checks in sequence:

1. **Login wall detection**
   Take a `browser_snapshot` and check whether the result contains BOTH:
   - A password field indicator (e.g. "Password", "Wachtwoord")
   - A submit/login button text (e.g. "Log in", "Sign in", "Inloggen")
   Only trigger when BOTH signals appear as primary page content — not inside a secondary embedded widget. (`browser_find` can be used instead for a cheaper targeted check once you know what to look for.)
   If detected and this is not the first scenario (login was already handled in Step 5), log:
   > 🔐 Unexpected login screen at `[current URL]`. Attempting re-login with stored credentials.
   If no stored credentials exist, pause and ask. Do NOT log or store credentials. Continue after login.

2. **App reachability check**
   If `browser_navigate` returns an error, or the following `browser_snapshot` returns an empty/error result:
   > ❌ Could not reach `[entry_url]`. Is the app running?
   Hard stop.

3. **Console error check**
   Call `browser_console_messages` with `level: "warning"` and `all: false` (the default) — this returns `warning` and more severe entries (i.e. `warning` + `error`, excluding `info`/`debug` noise) captured since the last navigation. If non-empty, log:
   > ⚠️ Console errors detected: [errors]
   No manual buffer reset is needed — the next `browser_navigate` scopes the following call to fresh entries automatically. Include all captured entries in the failure detail or as a warning in the report, even if the scenario otherwise passes. Apply these rules:
   - `level: "error"` → always surfaces as a warning in the report. If the scenario has no other failure, mark it `✅ passed (with console errors)`.
   - `level: "warning"` → log only. Never causes a scenario to fail or be flagged unless there are 5 or more `warning` entries in a single scenario, in which case surface as a notice.

4. **Network error check**
   Call `browser_network_requests` with `all: false` (the default) and filter the returned list for entries with `status >= 400`. If any exist, log:
   > ⚠️ Network errors detected: [url] → [status] [statusText]
   No manual buffer reset is needed, for the same reason as the console check above. A 4xx or 5xx response is treated as a test warning by default. If the scenario's `expected` outcome explicitly requires a successful API call, treat a network error as a scenario failure.

**Evaluate outcome:**

After executing all steps for a scenario, run `browser_snapshot` to capture the full accessibility-tree state of the page (structure + visible text). Scan for:
- Error keywords: `error`, `fout`, `failed`, `500`, `403`, `not found`, `undefined`, `null`
- Empty content where content is expected
- Form validation messages that shouldn't be there

Use `browser_find` instead when only a specific expected piece of text/element needs confirming, rather than scanning the full snapshot. Compare against `expected`.

**On success:**
```
✅ [id] passed: [name]
```
- If `screenshot_pref = "all"` → call `browser_take_screenshot`
- If `screenshot_pref = "failures_only"` or `"none"` → no screenshot on success

**On failure:**

Before logging a failure, apply the "Rule out test-tool flakiness before blaming the app" check above if the observed anomaly looks like corrupted/empty/concatenated field data. Only proceed with the failure report below once flakiness has been ruled out (retry reproduced the issue, or the anomaly isn't form-data corruption).

```
❌ [id] FAILED: [name]
Expected: [expected outcome]
Actual: [what was observed — page text + any JS errors detected]
```
- Call `browser_take_screenshot` unconditionally (overrides `screenshot_pref`). If the tool returns an inline image payload, it will be shown directly in this response. If it instead returns a file path, note the path in the report — do not assume every agent runtime renders screenshots inline in chat; some require the user (or a separate file-viewing tool call) to open the saved path.
- Record: `failed_id`, `steps_executed`, `expected`, `actual`, `console_errors`, `network_errors`, screenshot (inline image or saved file path)
- If `fail_fast = true` → **Stop the entire run.**
- If `fail_fast = false` → record the failure, continue, collect all for final report

---

## Step 7 — Report

After all scenarios complete or fail-stop, output the following report inline in chat.

**If the user explicitly asks to save the report to disk**, write it as `playwright-report-[branch-or-pr-id].md` in the current working directory and provide the path.

```
## Playwright Test Report: [PR title or branch name, or feature name in multi-service mode]

**Tested against:** [entry_url]
**Services (multi-service mode only):** [service: PR title/link, service: PR title/link, …]
**Service health checks (multi-service mode only):** [service: ✅ reachable / ⚠️ unreachable, …]
**Provider:** [GitHub / GitLab / local branch]
**Viewport:** [desktop / mobile / both]
**Screenshots:** [all / failures only / none]
**Scenarios cut (risk-based):** [list if any were dropped due to 8-scenario cap, or "none"]

### Results

If `viewport = "desktop"` or `"mobile"`:

| # | Scenario | Service | Type | Risk | Result |
|---|----------|---------|------|------|--------|
| S1 | [name] | frontend | happy path | 🔴 high | ✅ passed |
| S2 | [name] | frontend + auth-service | edge case | 🟡 medium | ❌ failed |
| S3 | [name] | auth-service | regression | 🟢 low | ⏭ skipped |
| S4 | [name] | frontend | happy path | 🟡 medium | 🚫 not browser-testable |
| S5 | [name] | n/a | edge case | 🟢 low | ⏭ skipped (missing data) |

If `viewport = "both"`, split each scenario into two rows — one per viewport:

| # | Scenario | Type | Risk | Viewport | Result |
|---|----------|------|------|----------|--------|
| S1 | [name] | happy path | 🔴 high | 🖥 desktop | ✅ passed |
| S1 | [name] | happy path | 🔴 high | 📱 mobile | ❌ failed |
| S2 | [name] | edge case | 🟡 medium | 🖥 desktop | ✅ passed |
| S2 | [name] | edge case | 🟡 medium | 📱 mobile | ✅ passed |

### Failure Detail(s)

#### [failed_id]: [name]

**Steps executed:** [step 1 → step 2 → …]
**Expected:** [expected outcome]
**Actual:** [what was observed]
**Console errors:** [error/warn entries captured during scenario, or "none"]
**Network errors:** [failed API calls with status codes, or "none"]
**Screenshot:** [inline image, or the saved file path if the tool returned one instead of rendering inline]

### Verdict

**Overall:** PASS / FAIL
**Risk:** [one sentence on what failed and what it means for the user]
```

Omit "Failure Detail" if all scenarios passed.

---

## Step 8 — Clean Up Environment

After the report is delivered (regardless of pass/fail outcome), check whether any temporary environment or configuration changes were made solely to make the app reachable for this test run (e.g. edited config files, generated certificates, added hosts entries, started ad hoc dev servers). If so:

1. Revert tracked config files with `git checkout -- <file>` (or equivalent) and restore untracked/gitignored config files to their prior values.
2. Stop any ad hoc processes started for this run (e.g. a bare dev server) — do NOT stop containers or processes that were already running before this skill started, or that the user asked to leave running for other purposes.
3. Remove any temporary files created for the run (e.g. generated cert files in `/tmp`).
4. Confirm cleanup with a quick `git status --short` (or equivalent) and report the result in one line, e.g. `Environment cleanup: reverted 2 config files, stopped 1 ad hoc dev server. Working tree clean.`

If no temporary changes were made, state that explicitly (e.g. `No environment cleanup needed — no temporary changes were made.`) rather than omitting this step silently.

## Error Reference

| Situation | Behavior |
|-----------|----------|
| Playwright MCP not installed | Hard stop at Step 0 — point to `configure-mcp`'s Playwright integration, or manual pinned `@playwright/mcp@0.0.79` install |
| Provider MCP not installed | Fall back to local git diff, notify user |
| Entry URL not reachable | Hard stop: "Could not reach [entry_url]. Is the app running?" |
| Entry URL not provided, no documented dev environment found (Step 3.5) | Default to `http://localhost:3000`, mention this assumption |
| Entry URL not provided, but a documented dev environment was found (Step 3.5) | Do not default — re-ask the user for the specific URL that environment exposes |
| Backend service unreachable (multi-service pre-flight) | Warn, list affected scenarios, ask user to continue / skip / abort — do not guess |
| Cross-service duplicate scenario detected | Merge into one scenario driven via the user-facing entry point; list all contributing services |
| Backend-only scenario with no reachable UI route | Mark `testable: false`, `🚫 not browser-testable (backend-only)`, note the dependent scenario that covers it indirectly |
| Login wall detected (first time) | Pause, ask credentials, reuse session for remaining scenarios |
| Login wall detected (subsequent) | Re-login automatically with stored credentials or ask |
| Action failed after retry (stale ref or timeout) | Re-snapshot and retry once; if it still fails, treat as test failure — screenshot + stop |
| Multi-field form fill | Use `browser_fill_form`; verify each field's DOM value via `browser_evaluate` after filling, before submitting; re-fill mismatches |
| Corrupted/concatenated form data observed on failure | Re-run scenario fresh before reporting; if it passes, treat as tooling flakiness, not a bug |
| `window.open()` / popup triggered | Switch tab via `browser_tabs` or handle inline as a login wall |
| Required test data missing | Skip scenario, mark `⏭ skipped (missing data)` |
| `requires_clean_state = true` | Use native `browser_cookie_clear`/`browser_localstorage_clear`/`browser_sessionstorage_clear` if available (`--caps=storage`), else `browser_evaluate`; navigate fresh |
| Console errors detected (`browser_console_messages`, `level: "warning"`) | Log as warning, no manual reset needed (auto-scoped since last navigation), include in report even on pass |
| Network errors detected (`browser_network_requests`, status ≥ 400) | Log as warning per request, treat as failure if scenario requires successful API call |
| Non-browser-testable scenario | Mark `🚫` in report, skip browser execution |
| Diff warrants >8 scenarios | Cap at 8 by risk, note dropped scenarios in report |
| Duplicate scenarios detected | Merge before presenting to user |
| User requests report saved to disk | Write `.md` file to working directory, provide path |
