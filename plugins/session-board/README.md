# session-board

A task board for Claude Code sessions. Run `/session-board` to open a pane that shows what was agreed, what is in progress and what is done, with a progress bar. The progress also shows in the status line.

See [release notes](RELEASE_NOTES.md) for changes.

## How it works

Claude keeps the board current while it works. It adds an item when work is agreed, marks it in progress when it starts, and marks it done once it is verified. Each of these is one small edit, so the cost stays low, and you never have to ask for an update. Trivial one-off questions are skipped.

Each session has its own board in `~/.claude/boards/<session-id>.md`. It lives outside every repository, so nothing is committed and no project content ends up in a repo. If a session has no board yet, the pane falls back to `.claude/board.md` in the repository, or to a `TASKS.md` that contains `<!-- board -->`.

The format is plain markdown: `- [ ]` for to do, `- [~]` for in progress and `- [x]` for done. Headings group the items.

To fill a board from what already happened in a session, ask for it. A bundled script condenses the transcript locally, with no network and no model, and Claude writes the items from that digest. It can miss things, and Claude says so.

## Requirements

The pane uses the plugin mods API, so it needs a Claude Code version that supports it. It also needs fullscreen rendering (`/tui fullscreen`) and a terminal at least 110 columns wide. Without the pane, the skill and the board file still work.

For the most reliable auto-update, add this line to your `CLAUDE.md`:

> When this session has a board (~/.claude/boards/<session-id>.md), keep it current with small edits as work is agreed, started and verified (session-board skill), without being asked.
