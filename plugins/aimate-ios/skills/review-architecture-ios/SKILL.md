---
name: review-architecture-ios
description: Use when the user asks for an architecture or design-quality review of an iOS, Swift, or Xcode project, where an iOS codebase is hardest to change, iOS hot spots, or refactoring priorities for an iOS app. The iOS layer on top of aimate's review-architecture (requires the aimate plugin): same method and report, with Swift module-graph analysis, iOS platform and SwiftPM dependency checks, and TCA and MVVM + Coordinators rules. Read-only on source; writes one untracked report to docs/.
argument-hint: "Optional: path or module to limit the review to, a history window such as 6 months, and known pain points or upcoming work"
allowed-tools:
  - Bash(xcrun python3 ${CLAUDE_SKILL_DIR}/scripts/swift_modules.py *)
  - Bash(xcrun python3 ${CLAUDE_SKILL_DIR}/scripts/ios_platform.py *)
  - Bash(xcrun python3 */review-architecture/scripts/hotspots.py *)
metadata:
  author: "Dawn Technology"
  version: 0.4.0
  role: "architecture-review"
  writes_source: "false"
  requires: "aimate (review-architecture)"
---

# Review Architecture iOS

Find where an iOS codebase's design costs the team the most, prove it from the code, and say what to fix first. This skill uses the method and report of `aimate`'s `review-architecture` and replaces the parts that do not fit iOS: the dependency and platform scripts, the layer mapping, and the platform and dependency rules.

It is read-only: do not edit, stage, commit, branch, `git fetch`, build, or install anything. The only file written is the report (step 6). Every subagent gets the same rule.

## Policy

Always read:

- [`../ios-standards/references/precedence.md`](../ios-standards/references/precedence.md) for the project-instruction locations;
- [`../ios-standards/references/architecture.md`](../ios-standards/references/architecture.md) to name the architecture;
- [`references/ios-design-rules.md`](references/ios-design-rules.md) for the iOS layer mapping, signals, platform, and dependency rules.

If a reference cannot be read, retry with another file-reading tool. If it still fails, name it in the report and do not apply its rules from memory.

## 1. Load the Generic Skill

Load `aimate`'s `review-architecture` skill with the host's skill mechanism: in Claude Code as `aimate:review-architecture`, in hosts that load skills by bare name (GitHub Copilot, OpenCode) as `review-architecture`. Read its `SKILL.md`, `references/design-rules.md`, and `references/REPORT-TEMPLATE.md` from the folder the host reports for that skill, and follow them with the overrides below. Its scripts (`hotspots.py`) are in the same folder.

If the skill cannot be loaded, stop and say: "review-architecture-ios is a layer on top of the aimate plugin; install aimate from the same marketplace and run the review again." Do not review without it.

## 2. Context (overrides Phase 0)

- Check every project-instruction location in `precedence.md` and the README with a file listing, and read what exists. The declared architecture often lives in `AGENTS.md` or `.github/copilot-instructions.md`, not in the README.
- Name the architecture from code with `architecture.md` and map layers with `ios-design-rules.md`. Record the TCA version when the project uses TCA; read `tca.md` and version docs only when a finding depends on how TCA behaves.
- Instead of `deps.py` and `packages.py`, run this skill's scripts (they write nothing to the repo; `swift_modules.py` evaluates each `Package.swift` copy with `swift package dump-package` in a temporary folder):

  ```bash
  xcrun python3 <skill-dir>/scripts/swift_modules.py --repo <target-repo>
  xcrun python3 <skill-dir>/scripts/ios_platform.py --repo <target-repo>
  ```

  In Claude Code, `<skill-dir>` is `${CLAUDE_SKILL_DIR}`: use that absolute path as written, so the skill's pre-approved commands match and the developer is not asked for each run. Run each script as a command of its own: no `cd`, variable assignments, or output redirects in the same call, because any of those makes the host ask for approval again; read the output from the command result. Read files with the host's file-reading tool (in Claude Code: Read) and search with its search tools when the session has them; otherwise search with one plain read-only command per call, such as `git grep -n <pattern> -- <path>` or `git log --no-merges --format=%s -- <file>`, without pipes, `cd`, or redirects. Never use `sed` or `awk` to read code.

  Run every script, including the generic skill's `hotspots.py`, with `xcrun python3`: Xcode ships Python 3.9, so no other Python install is needed and the version is the same on every machine. If `xcrun python3` is missing, Xcode or its command-line tools are not installed; say so and stop, because the module and platform analysis needs them.

- Do not fetch end-of-life data for iOS, tvOS, or watchOS; follow Platform in `ios-design-rules.md`.

## 3. Churn (overrides Phase 1)

Run the generic `hotspots.py` with settings that fit SwiftPM layouts:

- `--path` set to the package sources folder when one local package holds most code, and `--module-depth` so each Swift package target is one module: the depth counts folders below `--path`, so with `--path <Package>/Sources` each target folder is depth 1. With several local packages, run once over the whole repo for the ranking, then once per package with its own `--path` and depth for the module table. Check the module table shows targets, not one lump.
- `Package.swift` and project files that rank high are registries: keep them in the appendix, do not count them in the top 10.
- Drop generated and copied files from the hot spot list before picking the top 10: `Generated`, `GeneratedSources`, `*.generated.swift`, OpenAPI specs and their output, `.xcstrings`, `.json`/`.yml`/`.yaml` specs, and minified or vendored files in `Resources`. Name what you dropped.
- Read the "Left out" line: folders such as `Migrate` can hold real code; re-run with `--keep-dir`.
- "Share a name" is unreliable when names share suffixes (`*Feature`, `*View`, `*ViewModel`): compare the feature prefix instead.
- When change subjects are branch names (merge workflows), read the underlying commit subjects per file with `git log --no-merges --since=<window> --format=%s -- <file>` before judging unrelated reasons to change.
- A run scoped with `--path` to a sources folder cannot see `Tests/`, so take "Tests by name" from the unscoped run.
- Count parent `TestStore` tests and parent snapshot tests as tests of the children they cover.

## 4. Design Evaluation (overrides Phase 2)

- Dependency check: rerun `swift_modules.py` with the layer mapping as target-name patterns, innermost layer first (for example `--layer 'domain=*Models,ComponentTypes' --layer 'infrastructure=*Client,*Networking' --layer 'application=*Feature' --layer 'ui=*View,UIComponents' --layer 'composition=*Dependencies'`; quote each pattern, or zsh expands the `*`), and check that no target is left in no layer, apart from test-support targets (see Layer Mapping in `ios-design-rules.md`). When a target mixes layers (a UI module that also holds a reducer), an outward import from it can be a false alarm: open the importing file before reporting it. Report outward imports, low-level modules with large transitive dependency counts, undeclared internal imports in production targets, and import cycles. Open the import lines before citing them; for a long list of Low findings from the scripts (such as undeclared imports), open a sample, say how many you opened, and cite only those. "Declared but never imported" is a hint only: Swift can use members of an indirectly imported module without an import.
- Read hot spots as the generic skill says, and apply the generic rules together with the iOS signals in `ios-design-rules.md`.
- Platform and dependencies: use `ios_platform.py` output and the Platform and Dependency Health sections of `ios-design-rules.md` instead of the generic Supported Platform and Dependency Health sections.
- Severity, evidence levels, finding format, and IDs follow the generic skill.
- When the app has no tests at all, report that once as a single Tested Where It Changes finding (High when a hot spot carries business rules), and raise other findings for missing tests only in the worst hot spot; otherwise every finding would move up a level. A defect such as a broken `==` keeps its own severity; the rule only limits raising findings because tests are missing.

## 5. Specialist Pointers

Do not audit security, localization, or test execution. When the review sees reasons, recommend `security-audit-ios`, `fix-localization-ios` (stopping after its scan), or `test-ios` in the roadmap.

## 6. Report

Right after the verdict word in the Summary, and in the chat reply, add one sentence that says what the verdict means, without repeating the verdict word, for example after "**Broken.**": "Two or more High findings. This rates how safely the code can be changed, not whether the app works." Use the matching wording for Healthy (no High or Medium findings) and Strained (Medium findings or a single High). Fill the generic `REPORT-TEMPLATE.md`, with "review-architecture-ios <this version> (method of review-architecture <its version>)" as the skill version (both are `metadata.version` in the skills' frontmatter; when the host shows a loaded skill without its frontmatter, read the version from that skill's `SKILL.md` file), and write it once to `<repo-root>/docs/<project-name>-architecture-review-<YYYY-MM-DD>.md` (add `-2`, `-3` instead of overwriting), so a later run of either skill finds it for comparison. The project name is the app's Xcode project or main app target, lowercased (not a worktree folder name or a package name). The file stays untracked. In "Method and limits", name this skill, the scripts and their settings, the files dropped as generated, and what was not checked (cycles inside targets, runtime behavior, builds).

For iOS, fill the template's appendices as follows:

- D. Method and limits: under "Complexity and dependency checks", name `swift_modules.py` and `ios_platform.py` with their settings instead of `deps.py` and `packages.py`; under "End-of-life lookup", write that iOS support dates are not looked up (see Platform in `ios-design-rules.md`).
- E. Platform and dependencies: "Runtimes, frameworks and images" becomes deployment targets per platform with the lowest one, the Swift language mode, and the dead and still-needed availability checks from `ios_platform.py`; "Deprecated or abandoned packages" becomes branch or revision pins, unused packages, and packages from personal forks; "Lockfiles and updates" names the `Package.resolved` the app build uses (`ios_platform.py` marks it) and pins that differ between files.
- F. Vital signs: these rows replace the template's "keep the rows; add none" for iOS, and a cell may hold a version instead of a number. Keep the template's row names word for word, so a later review, generic or iOS, finds the same row; the count each row holds follows, so runs compare like with like. Put the meaning of a bracketed number in the cell itself:
  - Findings (High / Medium / Low).
  - Source files / test files.
  - Hot spots with no test by name: the template's by-name count of the top 10, then in brackets the ones with no test at all after crediting parent `TestStore` and snapshot tests (step 3) and direct tests the generic search of the test folders found, for example "4 of 10 (no test at all: 0)".
  - Cycles between modules (not nested).
  - Imports pointing the wrong way between layers: the count `swift_modules.py` prints, then in brackets the count you confirmed in the code when they differ, for example "5 (confirmed: 3)".
  - Months since the main lockfile last changed: the app's `Package.resolved`.
  - Large, complex, rarely changed files listed: the number reviewed in Appendix A. `hotspots.py` caps its list (`--stable-top`, 10 by default), so its count measures the setting, not the code.
  - Undeclared internal imports, replacing Domain leaks and hidden dependencies (hits): the count for production targets from `swift_modules.py`.
  - Lowest deployment target per platform, and Dead availability checks, replacing Components past end of life / ending within 6 months. For dead checks, copy the "dead:" line of `ios_platform.py`, which counts both units, for example "2 platform versions in 1 check".
  - Branch or revision pins, replacing Deprecated or abandoned direct packages.
  - Source targets without tests (added).

Reply in chat with the path, the summary paragraph, and the top three findings.


## Final Check

Before returning, confirm:

- project instructions were checked, and the architecture was named from code;
- `swift_modules.py` and `ios_platform.py` ran, and every finding from them was confirmed in the file;
- generated and copied files were dropped from the hot spots, and modules are package targets;
- no iOS support or end-of-life date was stated;
- only the report file was written, and git state is otherwise unchanged.
