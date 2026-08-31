# Commit Message Instructions

Follow these instructions whenever you generate a git commit message.

## Apply the shared rules

The format is maintained in one file, and this file does not restate it:

[`plugins/aimate/skills/write-commit-message/references/commit-message-rules.md`](plugins/aimate/skills/write-commit-message/references/commit-message-rules.md)

Read that file and apply it in full — the format, the seven rules, what belongs in each paragraph, the self-check, and the worked examples. If it is not reachable from where you are running, read it from the raw source instead:

```text
https://raw.githubusercontent.com/Dawn-Technology/aicelerate/main/plugins/aimate/skills/write-commit-message/references/commit-message-rules.md
```

## Writing the message

- Ground the message in the staged diff. Describe what changed and why, never a file-by-file listing.
- Output only the finished commit message — no headings, labels, prompt lines, commentary, or surrounding prose.
- Take the ticket key from the branch name using the pattern `[A-Z]+-\d+` and put it on the last line. Omit that line entirely when the branch holds no key; never invent one.
- Never start a line with `#` — git strips such lines under `--cleanup=strip`. Write `Ref: #123` instead of a bare `#123`.
- Never include secrets, API keys, credentials, or PII.

## Committing from chat or the CLI

Use the `write-commit-message` skill instead. It reads the same rules file and also stages, commits, and reports the result.
