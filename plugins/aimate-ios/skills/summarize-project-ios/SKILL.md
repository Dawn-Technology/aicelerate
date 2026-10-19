---
name: summarize-project-ios
description: Use when the user asks for an overview of an iOS project, for example when joining or taking over a project or estimating work. Read-only static summary with an onboarding part (what the app is, structure, how to get it running, gotchas) and an assessment part (risks, debt, complexity hotspots).
metadata:
  author: "Dawn Technology"
  version: 0.1.0
  role: "project-summary"
  writes_source: "false"
  external_dependencies: "none"
---

# Summarize Project iOS

Give a developer joining the project, and a tech lead assessing it, an accurate picture of the project in one report. This skill is read-only and static: it never edits files, changes git state, builds, or runs anything. It is a summary, not a review: it names the most important points with evidence and points to the specialist skills for depth.

## Policy

Always read [`../ios-standards/references/precedence.md`](../ios-standards/references/precedence.md) for the list of project-instruction locations. Read [`../ios-standards/references/architecture.md`](../ios-standards/references/architecture.md) to name the architecture.

If a reference cannot be read, retry with another file-reading tool. If it still fails, name it in the report and do not apply its rules from memory.

## Workflow

### 1. Read What the Team Wrote

Check every project-instruction location in `precedence.md` and the README and other docs with a file listing; read each that exists. Follow symlinks and report broken ones. Treat these documents as claims to check, not as facts: every concrete value they state (Xcode version, simulators, deployment targets, script names, commands, architecture) is compared with the project in step 3.

### 2. Map the Project

From project files, record: what the app does; targets and extensions; platforms and deployment targets; architecture; modules and local packages; key dependencies with how they are pinned; environments and backends per build configuration and scheme; code generation; test targets, frameworks, and plans; CI and release setup. Count size with tracked files only (`git ls-files`), separating generated code.

### 3. Check the Gotchas

Run each check and record the result with its evidence, even when nothing is found:

| Check | How |
| --- | --- |
| Instruction drift | Every value from step 1 against the project and this machine (`xcodebuild -version`, `xcrun simctl list`, project settings, scripts on disk). |
| Broken links | `find . -xtype l -not -path './.build/*'` and symlinked instruction or skill files. |
| Private access | Package and submodule URLs (`Package.swift`, `Package.resolved`, `.gitmodules`) over SSH or private hosts, and what access a newcomer needs. |
| Files that must come from elsewhere | Files the project or code references that are gitignored, empty, or written by CI or setup scripts (xcconfig, `.env`, plist keys, secrets), and how a developer gets them locally. |
| Required tools | Setup scripts, Brewfile, Mintfile, Gemfile, Git LFS, submodules, JDK or other toolchains, plugins and macros that need trust. |
| Backends per configuration | Which server each scheme and configuration talks to by default, especially Debug builds that use production. |
| Scheme surprises | Archive, test, and run configurations per shared scheme; test targets that exist but are not in any plan; commented-out targets. |
| Lockfile consistency | Every `Package.resolved` against the others and against `Package.swift` requirements. |
| Generated code | What is generated, by which script, and whether CI checks it is up to date. |
| Dead platforms and targets | Targets, platforms, or test plans that cannot build or are not maintained. |

### 4. Find the Hotspots

Use git history, not file size alone: files changed most in the last six months (`git log --since=6.months --name-only --format=`), excluding generated code, combined with their size; recent fix commits and the areas they touch; TODO and FIXME clusters. Name the three to five areas where a change is most likely to cause regressions, and why.

### 5. Assess

Pick the most important risks and debt for a tech lead, at most ten, each with impact (High, Medium, Low), evidence, and whether it is verified in files or inferred. Do not audit security or localization in depth: when signs point there, add one line that recommends `security-audit-ios` or `localization-audit-ios`, and recommend `test-ios` when the test setup is unclear. A behavior bug read in code but not reproduced is labeled as inferred. Report knowledge concentration (for example most recent commits by one author) as counts and shares, without naming individuals.

### 6. Report

Return a chat report with two parts:

**Onboarding**

- `What it is`: one paragraph.
- `Structure`: targets, modules, architecture, and where to start reading.
- `Getting it running`: numbered steps from a fresh clone to a running app and tests, including access, files, and tools from step 3.
- `Gotchas`: the most important items from step 3, at most ten, each with evidence.

**Assessment**

- `Strengths`: a few lines.
- `Hotspots`: from step 4.
- `Risks and debt`: from step 5.
- `Recommended next steps`: ordered, including which specialist skills to run.
- `Checked`: every check from step 3 with its result, including those without findings.
- `Not checked`: anything that needs a build, run, server, or access the session did not have.

Mark every claim that is not directly read from a file or command output as inferred.

## Final Check

Before returning, confirm:

- instruction files and docs were read and every concrete value in them was checked against the project;
- every check from step 3 appears in `Checked`;
- hotspots come from git history;
- gotchas and risks are capped at ten each, with evidence, and inferred claims are labeled;
- security and localization are summarized with a pointer to their audit skill, not audited in depth;
- nothing was edited, built, or run, and git state is unchanged.
