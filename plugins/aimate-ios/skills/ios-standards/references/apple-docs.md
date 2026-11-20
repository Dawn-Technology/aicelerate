# Apple Documentation

Read for version-sensitive Apple API claims: availability, deprecation, declarations, and recommended usage.

Use the first source that answers the question:

1. Installed SDK and compiler evidence: the project's deployment target, compiler diagnostics, and SDK interfaces. These outrank every documentation source.
2. Xcode MCP `DocumentationSearch` when Xcode is connected: semantic search for concepts and usage, with a `query` and optional `frameworks`. It returns article text, not structured availability.
3. Apple documentation JSON for exact symbol facts: `https://developer.apple.com/tutorials/data/documentation/<framework>/<symbol>.json`, using the lowercase path from the web URL. Read `metadata.platforms` (`introducedAt`, `deprecatedAt`, `message`), `abstract`, and the `declarations` section of `primaryContentSections`. The HTML pages render in the browser and return no useful content when fetched.
4. Sosumi for readable Markdown, the Human Interface Guidelines, and WWDC transcripts: replace `developer.apple.com` with `sosumi.ai` in the URL.

Name the source for each version claim. When sources disagree, the installed SDK wins.
