# Release notes

## 2.0.0

`aimate` is now skills-first. The plugin no longer bundles Figma, GitLab, or Atlassian MCP connections globally. Projects configure only the integrations they need through `configure-mcp` or the supplied project templates.

The setup wizard now validates existing official CLIs and MCP connections before changing anything. GitLab workflows always use the official `glab` CLI and no GitLab MCP template is shipped. GitHub and Jira can save a CLI/MCP preference in `AGENTS.md`; Confluence and Figma keep using MCP where no equivalent CLI exists. Sentry uses MCP for investigations and `sentry-cli` for release assets.

### Breaking change

- Removed the plugin-level `.mcp.json`.
- Removed `mcpServers` from `plugin.json`.
- Removed the GitLab MCP setup and made `glab` a prerequisite for GitLab workflows.
- GitLab.com is no longer assumed for every repository.
- Figma and Atlassian authentication is no longer requested merely because Aimate is installed.

### Migration from 1.x

1. Upgrade or reinstall the Aimate plugin.
2. Install `glab` (`brew install glab` on Homebrew platforms).
3. Authenticate with `glab auth login` and verify access with `glab repo list --member`.
4. If the MCP host retains the old plugin-owned `figma`, `gitlab`, or `atlassian/atlassian-mcp-server` entries, remove or disconnect those old entries in the host.
5. In every client checkout, run `configure-mcp`.
6. Keep the detected working project integrations or select GitLab/GitHub and optional Atlassian, Figma, and Sentry integrations.
7. Save `Automatic`, `Prefer CLI`, or `Prefer MCP` for GitHub and Jira when prompted, so skills do not ask again.
8. Reload or restart the MCP host when requested.
9. Complete OAuth for each newly named MCP connection.

Project configuration must not contain real tokens. Self-hosted Sentry uses a
secret input placeholder; hosted MCP connections use host-managed OAuth.

This release supersedes and closes [#16](https://github.com/Dawn-Technology/aicelerate/issues/16).
