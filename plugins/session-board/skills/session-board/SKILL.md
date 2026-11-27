---
name: session-board
description: Use at the start of any multi-step work and whenever a session board file exists for this session (~/.claude/boards/<session-id>.md). Keeps the session's task board current automatically while working, without being asked.
---

# Session board

Each session has its own board, shown in the `/session-board` pane: `~/.claude/boards/<session-id>.md`. The session id is the UUID in this session's scratchpad or transcript path. The file is created by `/session-board` (or by you, starting with `<!-- board -->`). It is stored outside every repo, so nothing is committed and no project content ends up in a repo.
A repo-level board also works as a fallback: `.claude/board.md`, or a `TASKS.md` containing `<!-- board -->`.

- Add an item as `- [ ] text` when work is agreed. Mark `- [~]` when you start it and `- [x]` when it is done and verified.
- Do not invent items, reorder or delete the user's items, or put secrets, ticket contents or personal data in it.
- Never copy board contents into a repo or between projects.
- It is for tracking, not a task system to obey.

## Keep it current automatically (no user prompt needed)
- If this session's board file exists, update it as you work. Do not wait to be asked.
- Cheap by design: one small Edit per milestone (work agreed, started, done and verified), never a rewrite. Do not re-read the board each turn; read it once when you first touch it, then edit by line. Never run scan_history.py for this.
- No board yet and the work is multi-step: create it with the `<!-- board -->` header and the agreed items.
- Skip trivial one-off questions.

## Fill the board from session history (only when the user asks, never automatically)
1. Run `python3 -I "${CLAUDE_PLUGIN_ROOT}/skills/session-board/scan_history.py" <session-id>` (local, no network, no model). Default cap 12000 chars (about 3k tokens); use `--max-chars 4000` for a cheaper pass. Never read the raw transcript .jsonl (it is MBs).
2. From that digest only, write items to the session board: finished work as `- [x]`, open or promised work as `- [ ]`. Group under short headings. Do not invent items; skip anything you cannot find in the digest.
3. Tell the user what you added and that it comes from a condensed digest, so it can miss things.
