# playwright-cli backend

Use this file when Step 0 selected `backend = cli`. The skill body names `@playwright/mcp` tools; run the
command in this table instead. Both come from Microsoft's Playwright and share the same snapshot and
`ref` model, so every rule in the skill (fresh snapshot before targeting, one retry, field read-back,
console and network checks) applies unchanged.

Verified against `@playwright/cli` 0.1.22.

## Session

Run every command against one named session so it never touches a browser the user has open:
`playwright-cli -s=test-pr-e2e <command>`. Below, `pw` stands for that prefix.

- Open once in Step 5: `pw open <entry_url>`. Close in Step 8: `pw close`.
- The browser stays open between commands, so cookies and storage carry over between scenarios the same
  way they do in an MCP session. Do not use `state-save`: it writes the logged-in session to disk.
- Quote every text argument. Use single quotes, and escape any single quote inside the value.

## Tool mapping

| MCP tool | CLI command | Notes |
|---|---|---|
| `browser_navigate` | `pw goto <url>` | A failed navigation prints a `### Error` block: treat that as the reachability failure. |
| `browser_navigate_back` | `pw go-back` | |
| `browser_click` | `pw click <ref>` | No `element` argument: keep the human-readable description for the log only. |
| `browser_hover` | `pw hover <ref>` | |
| `browser_type` | `pw fill <ref> '<text>'` | `fill` replaces the value. Add `--submit` to press Enter after. |
| `browser_fill_form` | one `pw fill` per field, then the read-back | There is no single-call form fill, so the field read-back in Step 6 is mandatory here, even for two fields. |
| `browser_select_option` | `pw select <ref> '<value>'` | |
| `browser_snapshot` | `pw snapshot` | Prints the tree inline. `goto` and `open` save their snapshot to a `.yml` file instead and print its path; run `pw snapshot` when you need the tree. |
| `browser_find` | `pw find '<text>'` or `pw find --regex '/…/i'` | |
| `browser_take_screenshot` | `pw screenshot --filename=<path>.png` | Always a file. Open it with the agent's file-reading tool to see it, and put the path in the report. |
| `browser_wait_for` (`text`) | `pw run-code "async page => { await page.getByText('<text>').first().waitFor({ timeout: 10000 }); }"` | No wait command exists. A timeout prints `### Error`. |
| `browser_wait_for` (`textGone`) | same, with `waitFor({ state: 'hidden', timeout: 10000 })` | |
| `browser_wait_for` (`time`) | `pw run-code "async page => page.waitForTimeout(<ms>)"` | |
| `browser_evaluate` | `pw eval '<function>'` | The value is in the `### Result` block. |
| `browser_console_messages` (`level: "warning"`) | `pw console warning` | Warnings and errors since the last navigation; resets on `goto`, like MCP. |
| `browser_network_requests` | `pw requests` | Since the last navigation; resets on `goto`. Static assets are hidden by default. Lines read `N. [METHOD] url => [status] text`: filter for status ≥ 400. `pw request <N>` shows one request in full. |
| `browser_resize` | `pw resize <w> <h>` | |
| `browser_tabs` list / select | `pw tab-list` / `pw tab-select <index>` | |
| `browser_cookie_clear`, `browser_localstorage_clear`, `browser_sessionstorage_clear` | `pw cookie-clear`, `pw localstorage-clear`, `pw sessionstorage-clear` | Always available, HttpOnly cookies included, so the `browser_evaluate` fallback is never needed. |
| JS `alert` / `confirm` dialog | `pw dialog-accept` / `pw dialog-dismiss` | |

## Recording

CLI-only: the MCP path has no equivalent, so it never records. Per scenario, with `recording` from Step 4:

| Moment | `video` | `trace` |
|---|---|---|
| Scenario start | `pw video-start <dir>/<id>-<viewport>.webm`, `pw video-chapter '<id>: <name>' --duration=1500`, `pw video-show-actions` | `pw tracing-start` |
| Scenario end | `pw video-stop` (prints the saved path) | `pw tracing-stop` (prints the `.trace` and `.network` paths) |

- `video-show-actions` labels each click and fill on the video, so a reviewer can follow the steps without the log.
- Save videos in a folder you create for the run (or the report's folder when the user saves the report), never inside the repo's tracked files.
- Traces land in `.playwright-cli/traces/` under the shell's working directory as raw files (`.trace`, `.network`, `resources/`), not a zip. Report the `.trace` path; opening it needs the Playwright trace viewer.
- `both` runs the two sets together.

## Output

Every command prints Markdown sections: `### Result`, `### Error`, `### Page`, `### Snapshot`. Read
`### Error` as the call failing, the same as an MCP tool error.
