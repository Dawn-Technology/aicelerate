---
name: review-architecture
description: "Read-only architecture and design-quality review of an existing codebase. Finds hot spots from git churn, file growth, complexity and files that change together, then checks them against layering, dependency direction, cohesion, SOLID and simplicity rules, and writes a findings report with a three-step refactoring roadmap. Use this whenever the user asks for an architecture review, design review, technical debt assessment, code health check, codebase audit, hot spot or churn analysis, SOLID or clean-architecture review, or asks where the code is hardest to change or what to refactor first, even if they don't say \"architecture\". Not for reviewing a diff, commit or PR (use review-local or review-pr) or for security (use asvs-audit)."
metadata:
  author: "Martin Roest <martin.roest@dawn.tech>"
  version: 1.0.0
argument-hint: "Optional: path or module to limit the review to, and a history window such as 6 months"
---

# Architecture Review

Find where a codebase's design is hurting the team, prove it from the code, and say what to fix first. The review is aimed at the places that change most, because a design flaw in a file nobody touches costs little, while the same flaw in a file edited every week costs every week.

The review is read-only. Do not edit, stage, commit or branch. The only file you write is the report.

## Inputs

- **Target repo**: the repository to review. Default: the current working directory.
- **Scope** (optional): a subdirectory or module to limit the review to. In a monorepo with no scope given, review the components that dominate the churn and say which ones you left out.
- **Window** (optional): how much history to use. Default: 12 months before the last commit.

Ask a question only if the target repo cannot be found. Everything else has a default.

## Exclusions

Leave out third-party and generated code: `node_modules/`, `vendor/`, `dist/`, `build/`, `out/`, `target/`, `.next/`, minified bundles, generated clients, migrations and lock files. The churn script already skips these and test files.

Do not open `.env`, `.env.*`, key files, credential files or `secrets.*`. Never copy a secret into the report.

## Workflow

### Phase 0: Context

Before any analysis, learn what the codebase is trying to be. You need this to judge it fairly.

1. Profile the stack: language, framework, database, how it is deployed. Read the manifest files (`package.json`, `composer.json`, `pyproject.toml`, `*.csproj`, `go.mod`, and so on) and the README.
2. **Establish the intended architecture.** Look for a declared one: folders named `Domain`, `Application`, `Infrastructure`, `core`, `adapters`, `ports`; ADRs; an architecture section in the README or `docs/`. Then map the actual folders onto the three layers from [design-rules.md](./references/design-rules.md) (Domain, Application, Infrastructure). Write the mapping down; the report needs it.
3. Record `git rev-parse --short HEAD` and today's date.

Why this matters: the rules in this skill describe a layered, domain-centred design. A small Laravel or Rails app built on Active Record never promised a pure domain, and flagging every model that touches the database helps nobody. Hold a codebase to the architecture it declared, and for the rest, flag mixing only where it causes pain you can show, such as in a hot spot, a rule that cannot be tested, or a file edited again and again.

### Phase 1: Churn analysis

Do not start by reading files at random. Let the history tell you where to look.

Run the bundled script from the skill directory against the target repo:

```bash
python3 <skill-dir>/scripts/hotspots.py --repo <target-repo> [--path <scope>] [--months <n>]
```

It needs only Python 3 and git. It prints, for the window:

- the most changed files, with their size now, growth over the window, complexity and a combined score;
- churn rolled up per module;
- pairs of files that are usually changed together, cross-module pairs first;
- for each hot spot, how many files it moves with and its strongest partners.

A "change" is one entry on the first-parent history: a merged PR, a squash-merged PR, or a direct commit. That makes the coupling numbers mean "changed in the same PR". Run `--help` for the thresholds. Add `--json` if you want to process the output.

Complexity comes from `lizard` when it is installed and from a count of decision keywords otherwise. The keyword count is per file, not per function, so use it to compare files, not as a real cyclomatic number. The report states which one ran.

Then interpret the output:

1. **Pick the hot spots.** Take the top 10 to 15 files by score. The most suspicious are files that change often, are large or complex, and grew a lot in the window: that combination is how mixed responsibilities build up. Note each file's apparent role (domain, application, infrastructure, UI, registry, or mixed).
2. **Sort the coupling.** Drop coupling that is expected: a file and its translation twin, an interface and its only implementation, a route table that every feature registers in, and the files of one feature's vertical slice (controller, command, handler, entity, repository) when they live in the layers you would expect. Keep coupling that points at a problem: files in unrelated modules or features that move together, a backend and frontend file that repeat the same rule, or a hot spot coupled to many files across modules.
3. **Write the hot spot note** now, before reading any code: the hot spot list, their roles, and the coupling patterns you kept. This becomes section 1 of the report. Writing it first fixes where Phase 2 looks, so the review follows the evidence rather than whatever file looked interesting.

If the history is too thin to trust (under about 30 changes in the window, a shallow clone, or no git at all), widen the window once. If it is still thin, rank files by size and complexity alone, and say so in the report's "Method and limits".

### Phase 2: Design evaluation

Evaluate the codebase against the rules in [design-rules.md](./references/design-rules.md). Read it now. Each rule there comes with signals, cases not to flag, and the usual fix; the "don't flag" notes keep the report from drowning real problems in framework idiom.

Work in this order:

1. **Repo-wide dependency check.** Dependency leaks are cheap to find everywhere, so don't limit this to hot spots. Grep the domain folders for imports of ORM, framework, HTTP, queue, config and logging types. Record every hit with `file:line`, grouped by pattern.
2. **Hot spot reading.** For each hot spot, read the whole file, its imports, and its main callers. For coupled pairs you kept, read both sides and find what they share. Use `git log --format=%s -- <file>` to see why a hot spot keeps changing: unrelated commit subjects on one file are strong evidence of more than one reason to change.
3. **Check every rule** against what you read. When two rules disagree, such as a single-implementation interface, use section 4 of the rules file.

On a large codebase, you may hand each hot spot, or a group of related ones, to a subagent so file contents stay out of your own context. Give each one the rules file, the hot spot list, and the finding format below, and ask for findings with evidence back. Check their evidence before you use it.

A finding needs all of the following, or it does not go in the report:

- A location you opened and read, given as `file:line` or `file:start-end`. Don't infer a violation from a file name or a folder.
- The one rule it breaks, by name.
- The impact in concrete terms: what change gets harder, what cannot be tested, what breaks.
- A refactoring step concrete enough to start on.

Group repeats of one pattern into a single finding with several locations. Ten to twenty well-evidenced findings help more than fifty thin ones.

**Severity:**

- **High**: in a hot spot, and it blocks safe change or testing. Or the domain depends directly on infrastructure. Or a business rule is duplicated and has already drifted.
- **Medium**: a clear rule violation that costs effort on each change, but sits outside the top hot spots or has a contained blast radius.
- **Low**: local cleanup: dead code, a speculative wrapper, a slightly wide interface.

### Phase 3: Report

Fill in [REPORT-TEMPLATE.md](./references/REPORT-TEMPLATE.md). Keep its structure and section order; drop the HTML comments. The sections are:

1. **Exploration Summary**: the hot spots with their roles, and the coupling patterns.
2. **Architectural Boundary Health**: status per layer, and every dependency leak.
3. **Actionable Findings**: High, then Medium, then Low, each with Location, Violation, Impact and Recommended Action.
4. **Refactoring Roadmap**: three milestones, most valuable first.

For the roadmap, each milestone must ship on its own without breaking callers. The safe shape is: add the new path, move the callers over, then remove the old path. Milestone 1 tackles the top High finding and carries a before and after snippet. The "before" is real code from the repo, trimmed to the lines that matter, with its `file:lines`. The "after" is your proposal in the same language and style as the codebase. Keep both short, about 10 to 30 lines each.

Write the Summary last, in plain language: where the design is healthy, where it hurts, and the one change that would help most.

Write the report once, to `<target-repo>/docs/<project-name>-architecture-review-<YYYY-MM-DD>.md`. Create `docs/` if it does not exist. Take the project name from the manifest or the repo folder name.

Then reply in chat with the report path, the one-paragraph summary, and the top three findings. Keep the full tables in the file.

## Error handling

| Situation | Action |
|---|---|
| Target path is not a git repo | Skip Phase 1's history steps, rank by size and complexity, say so in "Method and limits" |
| Shallow clone | Say so. Suggest `git fetch --unshallow` in the report, but do not run it yourself |
| Script fails | Run the equivalent `git log --first-parent -m --numstat` by hand, and note it |
| No source files match | The script falls back to all files. If the repo holds no code, say so and stop |
| Hot spots are all config, routes or generated types | Keep them in section 1 as registries, then go down the list to the first real code files for Phase 2 |
| Too large to read every hot spot | Delegate per hot spot, or cover the top 5 fully and list the rest as not read |
