---
name: install-git-provider-mcp
description: Use when the GitHub MCP server, GitLab MCP server, or both need to be installed or verified. A single developer or project may have both installed simultaneously — for example when working across GitHub and GitLab clients. Referenced by skills like review-pr and devtest.
metadata:
  author: Kay Joosten <kay.joosten@dawn.tech>
  version: 1.0.0
agents:
  - claude
  - copilot
---

# Install GitHub / GitLab MCP Server

## Purpose

Install and verify the GitHub MCP server, the GitLab MCP server, or both. Having both installed simultaneously is normal and expected — for example when working across multiple clients, one on GitHub and one on GitLab. Each server is configured independently and does not interfere with the other.

## Step 1 — Determine what needs to be installed

Determine which server(s) are needed from context:
- Caller mentioned `github.com` or a GitHub PR URL → install/verify GitHub MCP
- Caller mentioned `gitlab.com` or a self-hosted GitLab domain → install/verify GitLab MCP
- Both providers mentioned, or working across multiple clients → install/verify both — this is fine and recommended for consultancy use
- Ambiguous → ask the user: "Are you working with GitHub, GitLab, or both?"

## Step 2 — Check if already installed

Before installing, verify whether the MCP server is already configured:

```bash
# Claude Code
cat ~/.claude/claude_desktop_config.json 2>/dev/null | grep -i "github\|gitlab"

# Copilot CLI / VS Code
cat ~/.vscode/mcp.json 2>/dev/null | grep -i "github\|gitlab"
cat ~/Library/Application\ Support/Code/User/settings.json 2>/dev/null | grep -i "mcp"
```

If the server is already listed and has a valid token configured → skip to Step 4 (verify).

## Step 3 — Install

### GitHub MCP

**Claude Code:**
```bash
claude mcp add github-mcp-server \
  --transport stdio \
  -- npx -y @modelcontextprotocol/server-github
```

Then add your GitHub token to the config:
```json
{
  "mcpServers": {
    "github-mcp-server": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "<your_token>"
      }
    }
  }
}
```

Required token scopes: `repo`, `read:org`

Generate a token at: https://github.com/settings/tokens

---

**Copilot CLI / VS Code:**

Add to `~/.vscode/mcp.json` (or workspace `.vscode/mcp.json`):
```json
{
  "servers": {
    "github": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "<your_token>"
      }
    }
  }
}
```

---

### GitLab MCP

**Claude Code:**
```bash
claude mcp add gitlab-mcp-server \
  --transport stdio \
  -- npx -y @modelcontextprotocol/server-gitlab
```

Then configure:
```json
{
  "mcpServers": {
    "gitlab-mcp-server": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-gitlab"],
      "env": {
        "GITLAB_PERSONAL_ACCESS_TOKEN": "<your_token>",
        "GITLAB_API_URL": "https://gitlab.com/api/v4"
      }
    }
  }
}
```

For self-hosted GitLab, replace `GITLAB_API_URL` with your instance URL, e.g.:
`"GITLAB_API_URL": "https://gitlab.dawn.tech/api/v4"`

Required token scopes: `api`, `read_repository`

Generate a token at: https://gitlab.com/-/user_settings/personal_access_tokens
(or your self-hosted equivalent)

---

**Copilot CLI / VS Code:**

Add to `~/.vscode/mcp.json`:
```json
{
  "servers": {
    "gitlab": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-gitlab"],
      "env": {
        "GITLAB_PERSONAL_ACCESS_TOKEN": "<your_token>",
        "GITLAB_API_URL": "https://gitlab.com/api/v4"
      }
    }
  }
}
```

## Step 4 — Verify installation

After installing, restart Claude Code / VS Code and verify the server is reachable:

**GitHub:**
```bash
# Should return your GitHub username
curl -s -H "Authorization: token <your_token>" https://api.github.com/user | grep login
```

**GitLab:**
```bash
# Should return your GitLab username
curl -s -H "PRIVATE-TOKEN: <your_token>" https://gitlab.com/api/v4/user | grep username
# For self-hosted:
curl -s -H "PRIVATE-TOKEN: <your_token>" https://gitlab.dawn.tech/api/v4/user | grep username
```

If the MCP server shows up in the agent's tool list, you're good. Ask the agent: "what MCP tools do you have available?" to confirm.

## Step 5 — Return to the calling skill

Once the server is installed and verified, return to the skill that triggered this install:
- If called from **review-pr**: proceed with Step 1 of that skill
- If called from **devtest**: proceed with Mode A of Step 0 in that skill
- If called standalone: confirm to the user which server(s) are now active

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `npx: command not found` | Install Node.js: https://nodejs.org |
| `401 Unauthorized` on API call | Token is missing required scopes — regenerate with correct scopes |
| MCP server not appearing in tool list | Restart the agent after config changes |
| Self-hosted GitLab: SSL error | Add `"NODE_TLS_REJECT_UNAUTHORIZED": "0"` to env (dev only) |
| Rate limit errors | Use a dedicated service account token instead of a personal token |