# Release notes

## 0.1.0 (2026-11-27)

First release. `/session-board` opens a pane with this session's task board and a progress bar, and shows the progress in the status line. The skill tells Claude to keep the board current with one small edit per milestone, without being asked. Boards are stored in `~/.claude/boards/<session-id>.md`, outside every repository. When a session has no board of its own, the pane falls back to `.claude/board.md` or a `TASKS.md` marked `<!-- board -->`.
