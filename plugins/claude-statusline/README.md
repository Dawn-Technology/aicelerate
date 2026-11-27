# claude-statusline

A status line for the Claude CLI (Claude Code). It is not meant for the Copilot CLI or VS Code. One line under the prompt shows how full the context is, with a hint for what to do about it, and the session id sits at the far right.

See [release notes](RELEASE_NOTES.md) for changes.

## What it shows

An example, with the parts explained below:

```text
ctx 55% wrap up │ chr 82% │ +12/-3 │ 5h 70% · ⏳00d 02h │ 7d 90% · ⏳05d 21h        sid: 3f2a9c1e-...
```

| Part | Meaning |
| --- | --- |
| `ctx 55%` | The share of the context window that is used. Green below 50%, yellow from 50%, orange from 70%, red from 85%. |
| `wrap up`, `no new`, `finish` | A hint that goes with `ctx`. At 50% start wrapping up the current task, at 70% do not start anything new, at 85% finish and hand over or clear. |
| `chr 82%` | Cache hit ratio: how much of the prompt was served from the prompt cache, as reported by Claude Code. Higher means cheaper and faster turns. |
| `+12/-3` | Lines added (green) and removed (red) in this session. |
| `5h 70% · ⏳00d 02h` | What is left of the 5-hour usage window, and how long until it resets. Green, then yellow at 40% left and red at 15% left. |
| `7d 90% · ⏳05d 21h` | The same for the 7-day usage window. |
| `sid: ...` | The session id, dimmed at the far right. It is also the name of the session's transcript and of its session board. |

Note that `ctx` counts what is used, while `5h` and `7d` count what is left. Each part is left out when Claude Code does not report it. When the terminal is too narrow, the session id moves to its own line.

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
