# claude-statusline

A status line for the Claude CLI (Claude Code). It is not meant for the Copilot CLI or VS Code. One line under the prompt shows how full the context is, with a hint for what to do about it, and the session id sits at the far right.

See [release notes](RELEASE_NOTES.md) for changes.

## What it shows

From left to right: `ctx` is the share of the context window that is used, coloured green, yellow, orange and red, with a hint at 50% (wrap up), 70% (no new) and 85% (finish). `chr` is the prompt cache hit ratio. The green and red numbers are lines added and removed. `5h` and `7d` show how much of each usage window is left, and how long until it resets. At the far right, dimmed, is `sid:` followed by the session id, which is the id of the transcript and of the session board.

Each part is left out when Claude Code does not report it. When the terminal is too narrow, the session id moves to its own line.

## Setup

Claude Code runs a status line from a command in your settings, and a plugin cannot set that for you. Copy the script somewhere stable and point your settings at it. Do not point at the plugin cache, because that path contains the plugin version and breaks on update.

```bash
cp "$(claude plugin list --json 2>/dev/null | jq -r '.[] | select(.id|startswith("claude-statusline@")) | .installPath')/scripts/statusline.sh" ~/.claude/statusline.sh
```

If that lookup does not work for your version, copy `scripts/statusline.sh` from this repository by hand. Then add this to `~/.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.sh",
    "refreshInterval": 60
  }
}
```

## Requirements

The script needs `bash`, `jq` and `bc`, which ship with macOS and most Linux distributions. It needs a UTF-8 terminal for the `⏳` and `│` characters. It runs locally: no network, no file writes. To test it without Claude Code, pipe sample JSON into it and set `MOCK_NOW` to a fixed epoch to freeze the countdowns.
