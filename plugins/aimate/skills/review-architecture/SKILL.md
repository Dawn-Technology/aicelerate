---
name: review-architecture
description: "Read-only architecture and design-quality review of an existing codebase. Finds hot spots from git churn, file growth, complexity and files that change together, then checks them against layering, dependency direction, cohesion, SOLID, simplicity, test safety and platform-support rules (runtime and framework end of life, deprecated dependencies), and writes a findings report with a three-step refactoring roadmap. Use this whenever the user asks for an architecture review, design review, technical debt assessment, code health check, codebase audit, hot spot or churn analysis, SOLID or clean-architecture review, end-of-life or dependency health check, or asks where the code is hardest to change or what to refactor first, even if they don't say \"architecture\". It measures how costly the code is to change and whether its platform is supported; it does not cover runtime performance or the delivery pipeline. Not for reviewing a diff, commit or PR (use review-local or review-pr) or for security (use asvs-audit)."
metadata:
  author: "Martin Roest <martin.roest@dawn.tech>"
  version: 1.2.0
argument-hint: "Optional: path or module to limit the review to, a history window such as 6 months, and known pain points or upcoming work"
---

# Architecture Review

Find where a codebase's design is hurting the team, prove it from the code, and say what to fix first. The review is aimed at the places that change most, because a design flaw in a file edited every week costs every week. It also lists the large, complex files nobody touches, because code is often left alone for the reason that it is frightening, and it checks whether the runtime and dependencies are still supported.

It does not cover runtime performance, scale, reliability or the build and deploy pipeline, and it does not look for security vulnerabilities. Say that in "Method and limits".

The review is read-only. Do not edit, stage, commit, branch, `git fetch` or install anything. The only file you write is the report, and it goes into the reviewed repo's `docs/` folder (see Phase 3), as an untracked file. Every subagent you start gets the same rule, in the briefing in Phase 2.

## Inputs

- **Target repo**: the repository to review. Default: the current working directory. A path argument that is the root of a repository is the target. A path inside a repository limits the review to that folder (the scope).
- **Scope** (optional): a subdirectory or module to limit the review to. In a monorepo with no scope given, run the churn script over the whole repo first. Then review each top-level component that holds at least 20% of the changes in the module table, up to three, by re-running the script with `--path`. List the others as not reviewed.
- **Window** (optional): how much history to use. Default: 12 months before the last commit.
- **Context** (optional): what the team already knows hurts, and what is coming (a migration, a new tenant model, a deadline). Take it from the user's message or arguments; do not ask for it. It does not change what counts as a finding. It changes where you look first (Phase 1, step 1) and what the roadmap puts first (Phase 3).

Ask a question only if the target repo cannot be found. Everything else has a default.

## Exclusions

Leave out third-party and generated code: `node_modules/`, `vendor/`, `dist/`, `build/`, `out/`, `target/`, `.next/`, minified bundles, generated clients, migrations and lock files. The churn and dependency scripts skip these and test files. Because migration folders are skipped, schema churn is not measured. The platform script still reads manifests and lockfiles, because that is where versions and deprecation flags live.

Do not open `.env`, `.env.*`, key files, credential files or `secrets.*`. Never copy a secret into the report.

## Workflow

### Phase 0: Context

Before any analysis, learn what the codebase is trying to be. You need this to judge it fairly.

1. Profile the stack: language, framework, database, how it is deployed. Read the manifest files (`package.json`, `composer.json`, `pyproject.toml`, `*.csproj`, `go.mod`, and so on) and the README. Then run the platform script:

   ```bash
   python3 <skill-dir>/scripts/packages.py --repo <target-repo> [--path <scope>]
   ```

   It lists the runtimes, frameworks and base images the repo declares (from version files, manifests, lockfiles, Dockerfiles, compose files and CI workflows), with end-of-life status from endoflife.date. It also lists packages the lockfile marks as deprecated or abandoned, unpinned versions, lockfile age and update automation. Keep its output; Phase 2 uses it. It makes one request per product to endoflife.date and sends nothing from the repo but the product name. Use `--offline` if the network is off limits; the status is then "not checked". Never fill in an end-of-life date from memory.
2. **Establish the intended architecture.** Look for a declared one: folders named `Domain`, `Application`, `Infrastructure`, `core`, `adapters`, `ports`; ADRs; an architecture section in the README or `docs/`. Then map the actual folders onto the three layers from [design-rules.md](./references/design-rules.md) (Domain, Application, Infrastructure). For a frontend or mobile app, use the mapping at the top of section 1 of the rules file. Write the mapping down; the dependency script in Phase 2 needs it. Section 5 of the rules file says what counts as "declared".
3. **Name the design patterns the code really uses**, from the code and not from the README: layered, hexagonal, MVC, Active Record, repository, CQRS, event-driven, plugin registry, strategy, and so on. Note where each one lives. Open about ten files for this at most (an entry point, one use case, one model, one repository, the place dependencies are wired); the history picks the rest of the files in Phase 1. Phase 2 checks whether the code keeps to the patterns, and section 1 of the report names them.
4. Look for rules the team already enforces: `deptrac.yaml`, `.dependency-cruiser.js`, `.importlinter`, `import-linter` settings in `pyproject.toml`, ArchUnit or NetArchTest tests, ESLint boundary rules, Nx module-boundary tags. They state the intended architecture better than folder names do. If the tool is already installed, run it read-only and use its output as evidence.
5. Look for a previous review: `docs/*-architecture-review-*.md` in the repo root. If there is one, read its Summary, its findings (title, files, rule) and its Appendix F, and keep them for the comparison in Phase 3. Do not let it steer Phases 1 and 2. Do the review with fresh eyes, then compare.
6. Record `git rev-parse --short HEAD`, the branch, today's date, and whether the working tree is dirty. The churn script reads `HEAD`; if the tree is dirty, line numbers from files on disk may not match it, so say so in "Method and limits".

The rules describe a layered, domain-centred design. Hold a codebase to the architecture it declared. For the rest, flag mixing only where it causes pain you can show, such as in a hot spot, a rule that cannot be tested, or a file edited again and again.

### Phase 1: Churn analysis

Do not start by reading files at random. Let the history tell you where to look.

Run the bundled script from the skill directory against the target repo:

```bash
python3 <skill-dir>/scripts/hotspots.py --repo <target-repo> [--path <scope>] [--months <n>]
```

It needs only Python 3 and git. It prints, for the window:

- the hot spots, ranked by score (changes × log2(2 + complexity)), with the number of authors, size now, growth over the window, complexity, and the test files whose names match. It scores at least the 40 most-changed files, so a file with fewer changes but far more complexity can still rank high;
- large, complex files that changed at most twice, with the date each last changed. Churn cannot see these;
- churn rolled up per module, with the share of its source files that have a test by name;
- pairs of files that are usually changed together, cross-module pairs with unrelated names first;
- for each hot spot, how many files it moves with and its strongest partners;
- what it left out, with the most-changed file for each reason.

A "change" is one entry on the first-parent history: a merged PR, a squash-merged PR, or a direct commit. On merge and squash workflows the coupling numbers mean "changed in the same PR"; on direct-to-trunk work they mean "changed in the same commit". Branch syncs, release merges, and changes that touch more than 200 source files (formatter runs, mass renames) are left out and counted in the header. Renamed files keep their history. Authors are people, counted as a number, bots left out; never put names in the report. Run `--help` for the thresholds. Add `--json` if you want to process the output.

Complexity is a count of decision keywords per file, with comments, docstrings and string contents removed. Compare files within one language, not across languages. It is not a real cyclomatic number. When `lizard` is installed, the output also names the most complex function in each file.

Read the script's warnings and act on them before you interpret anything:

- **Left out**: the line names the most-changed file for each reason. Check each one. Real code in a folder it skipped (`migrate`, `external`, `target`, or a test-like name such as `spec` or `testing`): re-run with `--keep-dir <name>`. Real code in other file types (`proto`, `graphql`, `html`): re-run with `--ext proto,graphql`. A repo whose logic is mostly templates, config or markdown: `--all-files`.
- **Linear history**: if most changes carry no PR reference and there are no merges, PRs may have been rebase-merged. Then one PR counts as several changes. Say so in "Method and limits" and treat change counts as relative, not exact.
- **Hit `--max-changes`**: the window is shorter than you asked for. Re-run with the higher cap the warning suggests. If it still hits the cap, say so in "Method and limits".
- **Thin history**: fewer than 30 changes touched source files. Re-run with `--months 24`, then `--months 36`. If it is still thin, or there is no git history, rank files by size and complexity alone and say so in "Method and limits".
- **Aggregate merges**: if most changes were left out as branch syncs or release merges, the branch is a release branch. Review the integration branch (`develop`) instead, or say that the churn numbers are rough.
- **Modules**: if the module table lumps unrelated areas together or splits one feature apart, re-run with `--module-depth 1`. In a repo organised by layer (`controllers/`, `services/`, `entities/`) a module is a layer, so "cross-module" says little: use the "Share a name" column.
- **Scope**: with a scope, files outside it are invisible, so coupling to them is missing. Say so in "Method and limits".

Then interpret the output:

1. **Pick the hot spots.** Take the top 10 by score (all of them if there are fewer). From here on, "hot spot" means these 10, and "top hot spots" means the first 5. The most suspicious are files that change often, are large or complex, and grew a lot in the window: that combination is how mixed responsibilities build up. Note each file's apparent role (domain, application, infrastructure, UI, registry, or mixed), judged from its path and imports. Open a file only as far as you need to tell. Many authors on a file whose commit subjects are unrelated (four or more people, in the window) adds weight to a cohesion finding; it is never a finding on its own. If the user gave context, add up to three files from the areas it names, even if they rank lower, mark them "named by the team", and treat them as hot spots from here on.
2. **Look at the large, complex, rarely changed files.** Take the top 3. For each, ask why nobody touches it: is it finished, feared or dead? Check the date it last changed and whether anything imports it. Note the answer.
3. **Sort the coupling.** Drop coupling that is expected: a file and its translation twin, an interface and its only implementation, a route table that every feature registers in, and pairs marked "Share a name" that live in the layers you would expect (one feature's slice). Keep coupling that points at a problem: files in unrelated modules or features that move together, a backend and frontend file that repeat the same rule, or a hot spot coupled to many files across modules. Three shared changes is a lead, not proof: confirm in `git log` that the changes were about the same thing.
4. **Find each hot spot's tests.** Start from the "Tests by name" column. For "none", search the test folders repo-wide for the file's main class or function before you write "none found". A hot spot without tests makes every refactor riskier, and that changes the severity and the roadmap.
5. **Draft the hot spot note** now, before you read the files in depth: the hot spot list, their roles, their tests, the stable-and-complex files with your answer for each, and the coupling patterns you kept. Keep it in your working notes; do not write a file. It becomes Appendix A and B of the report. Drafting it first fixes where Phase 2 looks, so the review follows the evidence rather than whatever file looked interesting.

### Phase 2: Design evaluation

Evaluate the codebase against the rules in [design-rules.md](./references/design-rules.md). Read it now. Each rule there comes with signals, cases not to flag, and the usual fix; the "don't flag" notes keep the report from drowning real problems in framework idiom.

Work in this order:

1. **Repo-wide dependency check.** Dependency leaks are cheap to find everywhere, so don't limit this to hot spots. Run the bundled script with the layer mapping from Phase 0:

   ```bash
   python3 <skill-dir>/scripts/deps.py --repo <target-repo> [--path <scope>] \
     --layer domain=<path> --layer application=<path> --layer infrastructure=<path>
   ```

   Repeat `--layer` for several folders. `*` works for modular layouts such as `src/*/Domain`. Leave `--layer` out when no layers can be mapped (a script collection, a small Rails app) and skip the layer checks. The script reads Python, JavaScript and TypeScript (with tsconfig paths and workspace packages), Java, Kotlin, Scala, Groovy, PHP, C# and Go. It prints:
   - coverage: how many imports it matched to a file in the repo, per language;
   - cycles between modules, with the import lines that form each one. Imports between a folder and its own subfolders are not counted; a cycle that exists only through them is marked nested;
   - imports that point the wrong way between layers. Application to infrastructure is a finding only where the declared architecture puts ports between them;
   - for the domain layer, imports of ORM, framework, HTTP, queue, config, logging and UI libraries. For domain and application, hidden dependencies: clock, random numbers, environment reads, static facades, persistence annotations, infrastructure exceptions;
   - fan-in, fan-out and instability per module, and how many files of a module other modules import.

   Read the coverage table first. Imports it cannot match are treated as external, so a cycle through one is not seen. Under about 90% for a language, say its results are partial. For languages it does not read (Ruby, Rust, Swift, C and C++, Elixir and others), search by hand: grep the domain folders for the leak patterns in the rules file, and trace the imports of the hot spots and their partners. Write in "Method and limits" what you checked. Write "no cycles found" only for what was covered. Keep the count and the first three `file:line` per pattern in your notes; the full list is in `--json`. If the repo has its own checker (`madge`, `dependency-cruiser`, `import-linter`, `deptrac`), run it read-only as a second source.
2. **Hot spot reading.** Ranks 1 to 5: read the whole file, its imports and its main callers. Ranks 6 to 10: read the imports and the parts that `git log -p` shows change most. For all ten, run `git log --format=%s -- <file>`: unrelated commit subjects on one file are strong evidence of more than one reason to change. For coupled pairs you kept, read both sides and find what they share. Read the top 3 large, complex, rarely changed files the way you read ranks 6 to 10.
3. **Platform and dependencies.** Take the output of `packages.py` from Phase 0 and apply section 4 of the rules file (Supported Platform, Dependency Health). Evidence for a finding is the file and line the script gives, plus the end-of-life date it fetched. If the status says "not checked", say so; do not substitute a date from memory. Opening the manifest line and confirming the version counts as reading it, so a platform finding can be High. Do not mix severities in one finding: report the components that make it High together, and the rest as a separate finding (see Supported Platform). Known vulnerabilities are out of scope; if they matter, tell the reader to run the package manager's audit command or the `asvs-audit` skill.
4. **Testing check.** From the Phase 1 numbers (tests by name per hot spot and per top module), read the tests of the top 3 hot spots and answer: do the tests for domain rules run without the framework, a database or the network? Would a test fail if the main business rule changed? Note what you saw. A hot spot or module with no tests at all is a finding under Tested Where It Changes.
5. **Check every rule** against what you read. When two rules disagree, such as a single-implementation interface, use section 5 of the rules file. When one problem fits several rules, cite the one whose fix you propose.
6. **Keep notes on what holds, not only what breaks.** For each pattern from Phase 0, write down where the code keeps to it and the evidence: the file you read, or the search that found nothing. Also write one sentence, with a number or a file behind it, on whether the architecture fits the size and change rate of the code: over-built (layers with one thing in them) or under-built (everything in one folder, and the hot spots show it). Section 1 of the report is a short overview built from these notes, and it needs the good news as well as the problems.

The rules are not tied to a pattern. They apply to a clean MVC app, a hexagonal one and a plain script collection alike. So check them on top of the patterns: a codebase can follow its pattern faithfully and still break a rule, or bend its pattern and keep the rules.

On a large codebase, you may hand each hot spot, or a group of related ones, to a subagent so file contents stay out of your own context. Give every subagent this briefing:

- Read only. Do not edit, stage, commit, `git fetch` or install anything. Do not open `.env`, key or credential files.
- The rules file, the intended architecture and what "declared" means for it, the layer mapping, the patterns from Phase 0, the exclusions, the severity definitions below, and the hot spot list with roles and tests.
- For each finding, the five items below and the evidence level. For each rule that holds, the file read or the search run.

Then open every `file:line` a subagent cites before you use the finding. Drop any that does not say what the subagent claims.

A finding needs all of the following, or it does not go in the report:

- A location you opened and read, with the file and its line numbers. Don't infer a violation from a file name or a folder. For platform and dependency findings the location is the manifest, Dockerfile or workflow line the script reports.
- The one rule it breaks, by name.
- A plain explanation: what the code does, and why that is a problem, in everyday words.
- The impact in concrete terms: what change gets harder, what cannot be tested, what breaks.
- A refactoring step concrete enough to start on.
- The evidence level: **read in full** (you read the code and the finding follows from it), **sampled** (you read some of the places, or part of the file), or **tool output** (it comes from a script result that you did not confirm in the file). Do not report a finding with tool output as its only evidence as High.

Give every finding an ID and a short plain-words title: H1, H2 for High, M1, M2 for Medium, L1 for Low, numbered in report order. Group repeats of one pattern into a single finding with several locations. A few well-evidenced findings help more than many thin ones. Do not pad: if the design is healthy, say so and report what you found, even if that is one finding or none. If the user named pain points, a finding in that area says so under "Why it matters".

**Severity.** "Hot spot" means the top 10 by score plus any files named by the team, "top hot spots" the first 5 by score.

- **High**: any of these.
  - It is in a hot spot, and it blocks safe change or testing.
  - The team declared a layered architecture and the domain depends on infrastructure, in a hot spot or in five or more domain files.
  - A business rule is duplicated and the copies already differ. Show both.
  - A dependency cycle runs through a hot spot, or through a module that holds the domain.
  - A large, complex, rarely changed file on a critical path (money, auth, data integrity) breaks a rule in a way that can give wrong results, and has no tests.
  - The runtime or the main framework is past its end of life, however recently. Support, and with it security fixes, stops on that date. Platform findings do not depend on churn.
- **Medium**: a clear rule violation that costs effort on each change, but sits outside the top hot spots or has a contained blast radius. Also the domain-imports-infrastructure case when the framework's idiom asks for it (Active Record, JPA entities), whether or not the file is a hot spot. In a hot spot it becomes High only if it blocks safe change or testing. Also a declared architecture that is stale (the code mostly ignores it): report the gap as one finding, and judge the rest against the conventions the code does follow. Also a runtime or framework that ends within 6 months, a component past its end of life that is not the runtime or the main framework (a database, base image, CI image or tool, unless the repo shows production running on it), and a deprecated or abandoned direct dependency. Also a top-5 hot spot with no tests at all (Tested Where It Changes).
- **Low**: local cleanup: dead code, a speculative wrapper, a slightly wide interface. Also unpinned versions, images without a version tag, a lockfile not updated for many months, no update automation, and a hot spot ranked 6 to 10 with no tests.

A top-10 hot spot with no tests moves a finding up one level (Low to Medium, Medium to High) when the missing tests are what make the file unsafe to change. A High stays High; say "no tests" under "Why it matters". Do not move a finding that is already High because it blocks testing, and do not move a finding that cites Tested Where It Changes.

### Phase 3: Report

Fill in [REPORT-TEMPLATE.md](./references/REPORT-TEMPLATE.md). Keep its sections and order, and drop the HTML comments; they say how to fill each part, including the finding format, the roadmap rules, the verdict words and the comparison with a previous review. Section 1 is a short overview: the patterns the code is built on, its current state, the main breaking points and where the roadmap should aim. Use short sentences, short lists and regular headings in the report, not tables. The two exceptions are the hot spot table in Appendix A and the vital-signs table in Appendix F, and every cell in them stays short. The order is: the answer first (Summary), then the reasons (sections 1 and 2), then the plan (section 3), then the evidence (Appendix). Write the Summary last.

If Phase 0 found a previous review, compare: match findings by file and rule, not by ID, and say what is resolved, still open and new. If there is none, leave the comparison out.

Write the report once, to `<repo-root>/docs/<project-name>-architecture-review-<YYYY-MM-DD>.md`. `<repo-root>` is the repository's top folder, even when you reviewed a scope. Create `docs/` if it does not exist. The report goes into the reviewed repo on purpose: it sits next to the code it describes, and the reader finds it there. Take the project name from the manifest or the repo folder name. If that file already exists, add `-2` (then `-3`) instead of overwriting it. If you cannot write there, write the report to the current directory and say where. The report is an untracked file; say in chat that it is there and that you did not stage or commit it.

Then reply in chat with the report path, the one-paragraph summary, and the top three findings. Keep the details in the file.

## Error handling

| Situation | Action |
|---|---|
| Target path is not a git repo, or has no commits | The churn script ranks by size and complexity on its own. Skip the coupling steps, the stable list and the author counts, and say so in "Method and limits". The dependency and platform scripts still work |
| Shallow clone | Say so. Suggest `git fetch --unshallow` in the report, but do not run it yourself |
| Churn script fails | Show the error and fix the cause (python3 missing, git too old, unreadable repo). If it cannot run, rank files by `git log --name-only` counts, say the ranking is rough, and skip scores and coupling |
| Dependency script does not read the main language | Search by hand as described in Phase 2, step 1, and say what you checked |
| No layer can be mapped (no domain folder) | Run the dependency script without `--layer`, skip the layer checks, and say so |
| `packages.py` cannot reach endoflife.date | The script says which products failed. Report the versions with "not checked". Do not fill dates from memory. Re-run with `--offline` to silence the warnings |
| No package manifest found | Say so in "Method and limits" and skip the platform and dependency findings |
| A folder you expected is missing from the hot spots | Check the script's "Left out" line, and re-run with `--keep-dir` |
| No source files match | The script falls back to all files. If the repo holds no code, say so and stop |
| Hot spots are all config, routes or generated types | Keep them in Appendix A as registries, then go down the list to the first real code files for Phase 2 |
| Too large to read every hot spot | Delegate per hot spot, or read the top 5 fully and list the rest as not read |
