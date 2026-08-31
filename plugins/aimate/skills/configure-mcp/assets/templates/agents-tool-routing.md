<!-- aimate:tool-routing:start -->
## Aimate tool routing

| Capability | Preferred route | Fallback route |
| --- | --- | --- |
| GitHub repository operations | `{github-primary}` | `{github-fallback}` |
| GitLab repository operations | `glab` | none |
| Jira operations | `{jira-primary}` | `{jira-fallback}` |
| Confluence operations | `{atlassian-client}` MCP | none |
| Figma design context | `{figma-client}` MCP | none |
| Sentry investigation | `{sentry-client}` MCP | none |
| Sentry release artifacts | `sentry-cli` | none |

- Keep only capabilities selected for this project.
- An explicit instruction in the current request overrides this table.
- Use the preferred route when it is available and authenticated.
- If it is unavailable, try the configured fallback without asking again.
- Briefly report when a fallback was used.
- After an ambiguous remote write, reconcile remote state before retrying or changing routes.
- Ask for configuration only when neither route works.
<!-- aimate:tool-routing:end -->
