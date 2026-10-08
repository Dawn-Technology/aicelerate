<!-- Fill-ins. Drop every HTML comment from the finished report.
Header values come from the top of the hotspots.py output, or from the "meta" block
of its --json output: git_commit = head, branch = branch, dirty_note = " (uncommitted
changes)" when working_tree_dirty is true and empty otherwise, window_since =
window_since, window_until = head_date, changes_read = changes_with_source_files.
skill_version comes from the `version` in SKILL.md's frontmatter.

Status words. Use this scale for the verdict in the Summary:
Healthy = no High or Medium findings in that area.
Strained = Medium findings, or a single High.
Broken = two or more High findings.
Count all findings.

No tables, except the hot spot table in Appendix A and the vital signs in Appendix F.
Use short sentences, short lists and regular headings. Keep every table cell short:
a number, a path or a few words. Anything longer goes in a sentence below the table. -->

# {{ project_name }} · Architecture Review

**Report date**: {{ report_date }}  
**Git commit**: {{ git_commit }}{{ dirty_note }} on `{{ branch }}`  
**Scope**: {{ scope }}  
**History window**: {{ window_since }} to {{ window_until }}, {{ changes_read }} changes  
**Skill version**: {{ skill_version }}  
**Reviewed & finalized by**: _____________________ <!-- Leave blank. A person fills it in. -->

## Summary

<!-- Open with the verdict: Healthy, Strained or Broken. Then two to four
sentences. Say where the design is healthy, where it is hurting, and the single
change that would help most. A reader who stops here must know what to do first.
No bullets. Write this last. -->

**{{ verdict }}.** {{ summary }}

**Top findings**: {{ one line each for the three most important findings, as "H1 title", "H2 title", "M1 title" }}  
**Start with**: Milestone 1, {{ milestone 1 title }}

---

## 1. Where the design stands

<!-- A short overview for someone who has not seen the code. Plain prose and short
bullets, no tables, about 150 to 250 words in total. Four parts, in this order. The
findings and the appendix hold the evidence, so do not repeat it here, and do not
repeat the verdict from the Summary.

Patterns and concepts: the three to six patterns or ideas the code is really built
on, as you saw them in the code and not as the README names them (layered, hexagonal,
MVC, Active Record, repository, CQRS, event sourcing, feature folders, and so on).
One line each: what it is, and the one or two folders that carry it. Give no
ratings. Include the intended architecture as one line: where it is declared, or
"none declared".

Current state: two to four sentences. What is sound, with one fact behind it, and
what is not. If the architecture is over-built or under-built for the size and
change rate of the code, say so here. Use plain words and name finding IDs where it
helps.

Main breaking points: up to four bullets, most important first. Each says the
violation in plain words, in which part of the code, and the finding ID. No file
lists and no rule names; the findings have them.

Where the roadmap should aim: two or three sentences. The part of the code the
refactoring should target first and why, with the milestone numbers, and the part to
leave alone because it is healthy.

Test: a new developer who reads only this section can say how the system is built,
where it hurts, and what the refactoring will focus on. If a sentence would be true
of any codebase, rewrite it with a fact from this one.

Too vague: "The design holds up where the team followed it and breaks where it did
not."
Clear: "The core is event sourced and clean. The Project module skips it, and
carries most of the change." -->

**Patterns and concepts**

- {{ pattern or concept }}: {{ what it is, and the folders that carry it }}
- Intended architecture: {{ declared in X, or "none declared; judged against the conventions of {{ framework }}", or "declared in X but stale; see M{{ n }}" }}

**Current state**

{{ two to four sentences }}

**Main breaking points**

- {{ the violation in plain words, in which part of the code, finding ID }}

**Where the roadmap should aim**

{{ two or three sentences, with milestone numbers }}

### Since the last review

<!-- Only when Phase 0 found a previous review in docs/. Otherwise delete this
subsection. Match findings by file and rule, not by ID, because IDs are renumbered
each time. One sentence on the direction: better, the same, or worse, and why. -->

Compared with `{{ previous report path }}` ({{ its date }}, commit {{ its commit }}).

- **Resolved**: {{ findings from the last review that no longer apply, with the reason }}
- **Still open**: {{ findings that remain, with their new IDs }}
- **New**: {{ findings that were not in the last review, with their new IDs }}

{{ direction }}

---

## 2. Findings

<!-- High first, then Medium, then Low. Give every finding one ID across all
severities, in the order shown: H1, H2, M1, M2, L1. The roadmap cites these IDs.
Give each a short title that names the problem in plain words. One finding per
root cause: group repeats of one pattern into one finding, with extra places as
extra rows under Where. Repeat the block below for each finding. If there are no
findings, say the design is healthy and drop this section's blocks.

Write for a developer who has never seen this code. Use everyday words and
short sentences. Say what the code does, then why that is a problem. The rule
name goes in the label line, not in the explanation. Explain any term such as
"coupling" or "cohesion" in plain words, or leave it out. Where a rule says
"many" or "large", give the number, so the reader can disagree with it.

Evidence: "read in full" = you read the code and the finding follows from it.
"sampled" = you read some of the places, or part of the file. "tool output" = it
comes from a script result you did not confirm in the file.

Too abstract: "Violates Single Reason to Change; responsibilities are mixed."
Clear: "OrderService works out discounts, builds the invoice and sends the
email. A change to any one of those means editing this file. That is why 14 of
its last 20 changes were about unrelated things." -->

### H1 · {{ short title }}

**Severity**: {{ High, Medium or Low }} · **Rule**: {{ rule name from design-rules.md }} · **Evidence**: {{ read in full, sampled or tool output }}

#### What is wrong

<!-- Two to four sentences in everyday English. What the code does today, and
why that is a problem. No rule jargon. -->

{{ explanation }}

#### Where

<!-- One bullet per place, at most five. Every bullet is a place you opened and
read. Put the sentence first, in plain words: what happens there. Put the location
on the next line (end the first line with two spaces), as the path from the repo
root and the lines, in backticks. When several places in one file show the same
point, list their lines together: `path/to/file.php:42-88, 120`. If there are more
than five places, show the five that matter most and end with a bullet such as "and
7 more of the same pattern". For a platform or dependency finding the place is the
manifest, Dockerfile or workflow line the platform script reports. -->

- {{ one short sentence: what happens there }}  
  `{{ path/from/repo/root.ext:42-88 }}`

#### Why it matters

<!-- One to three sentences: what gets harder, slower or riskier. When the file
is a hot spot, use its numbers: how often it changes, how many people change it,
and whether it has tests. When it is a large, complex, rarely changed file, say so
and give the date it last changed. When the team named this area as a pain point,
or it blocks upcoming work they named, say so. -->

{{ impact }}

#### What to do

<!-- One to three sentences: the first concrete step, specific enough to start
on. The roadmap holds the full plan. -->

{{ action }}

---

## 3. Refactoring roadmap

<!-- Up to three milestones, most valuable first. Use fewer if fewer findings are
worth acting on, and delete the unused blocks.

Each milestone must ship on its own without breaking callers: add the new path,
move callers over, then remove the old path. In Resolves, cite the IDs of the
findings it fixes. Effort: S = under a day, M = a few days, L = more. Risk: low,
medium or high. Done when = an outcome someone can observe.

Guardrail = the check that stops the problem coming back, in the repo's own tools:
a boundary rule in deptrac, import-linter, dependency-cruiser or ESLint, an
architecture test, a CI step, or a Dependabot or Renovate config. Name the tool and
the rule. The dependency script's output says which rule to write. Write "none
practical" if there is no check, and say why.

If the file a milestone changes has no tests, its steps start with tests that pin
down today's behaviour. Do not propose restructuring an untested hot spot first.

Milestone 1 tackles the top High finding, or the top Medium one if there is no
High. Exception: if the user named upcoming work and a finding blocks it, that
finding comes first, and the Summary says why. If Milestone 1 is then large (L) and
high risk, say so in the Summary, and name a smaller first step inside it.
Milestone 1 carries a before and after snippet. The "before" is real code from the
repo, trimmed to the lines that matter, with its file:lines. The "after" is your
proposal in the same language and style as the codebase; it is a sketch you did not
compile, so label it that way. Keep both short, about 10 to 30 lines each. A
platform or dependency milestone needs no snippet. -->

### Milestone 1: {{ title }}

**Resolves**: {{ finding IDs, e.g. H1, M2 }}  
**Effort / risk**: {{ S, M or L }} / {{ low, medium or high }}  
**Steps**: {{ steps }}  
**Guardrail**: {{ the check that keeps the fix, or "none practical: reason" }}  
**Done when**: {{ observable outcome }}

**Before** (`{{ file:lines }}`, trimmed from the current code):

```{{ language }}
{{ before_snippet }}
```

**After** (proposed sketch, not compiled):

```{{ language }}
{{ after_snippet }}
```

### Milestone 2: {{ title }}

**Resolves**: {{ finding IDs, e.g. H1, M2 }}  
**Effort / risk**: {{ S, M or L }} / {{ low, medium or high }}  
**Steps**: {{ steps }}  
**Guardrail**: {{ the check that keeps the fix, or "none practical: reason" }}  
**Done when**: {{ observable outcome }}

### Milestone 3: {{ title }}

**Resolves**: {{ finding IDs, e.g. H1, M2 }}  
**Effort / risk**: {{ S, M or L }} / {{ low, medium or high }}  
**Steps**: {{ steps }}  
**Guardrail**: {{ the check that keeps the fix, or "none practical: reason" }}  
**Done when**: {{ observable outcome }}

---

## Appendix

Evidence behind the findings. Read it to check a claim, not to follow the report.

### A. Hot spots

<!-- The top 10 hot spots from Phase 1, highest score first, then any files named
by the team (say "named by the team" in the role). Keep every cell short. Role = the
architectural role the file actually plays, in a few words (domain, application,
infrastructure, UI, registry, mixed). "Mixed" is itself a finding; add its ID.
Authors = the number of people who changed it in the window, bots left out; never
names. Tests = the test file name, or "none found". Put anything longer under the
table. -->

| # | File | Changes | Authors | LOC (growth) | Complexity | Apparent role | Tests |
|---|---|---|---|---|---|---|---|
| 1 | `{{ path }}` | {{ changes }} | {{ authors }} | {{ loc }} ({{ growth }}) | {{ complexity }} | {{ role }} | {{ tests }} |

<!-- Large, complex files that rarely change: the top 3 from Phase 1 (more if they
matter). Verdict = finished, feared or dead, with the reason you saw. A list, because
the verdicts are sentences. Leave it out if the script listed none. -->

#### Large, complex files that rarely change

- `{{ path }}` — {{ finished / feared / dead }}: {{ the reason you saw }}  
  {{ changes }} changes, {{ loc }} lines, complexity {{ complexity }}, last changed {{ date }}.

### B. Coupling patterns

<!-- One regular subsection per pattern, with a plain heading that names it and says
whether it is a smell (with the finding ID) or expected. Under each, two to three
sentences: which files, how often they changed together, and why that points at a
problem or not. Smells first. Put the expected coupling that explains something in
one last subsection, "Expected coupling". Leave out expected coupling that explains
nothing. -->

#### {{ pattern name }} (smell, {{ finding ID }})

{{ which files, how often they changed together, and why it is a problem }}

#### {{ pattern name }} (smell, {{ finding ID }})

{{ which files, how often they changed together, and why it is a problem }}

#### Expected coupling

{{ the pairs that move together for a good reason, in one or two sentences }}

### C. Dependency leaks

<!-- Every place an inner layer depends on an outer one, from the dependency
script and from the hot spot reading. Include dependency cycles and imports into
another module's internals. Two subsections: the leaks that became findings, and the
ones you did not flag, with the reason. One bullet per pattern: the name in bold, the
count and where, then up to three example locations on the next line (end the first
line with two spaces). If a subsection is empty, write "None" and the search you
ran. -->

#### Flagged

- **{{ leak }}**: {{ count and where, in one sentence }}. Finding {{ ID }}.  
  `{{ file:line }}`, `{{ file:line }}`

#### Not flagged

- **{{ leak }}**: {{ count and where }}. Not flagged because {{ the reason: idiom, declared style, standard interface }}.  
  `{{ file:line }}`

### D. Method and limits

<!-- Short. One to three sentences under each heading; skip a heading with nothing
to say. Only what weakens or shapes the evidence. -->

#### Window and history

{{ the window, how many changes, merge or squash or direct commits, a shallow clone, little history, a linear history where rebase merges make one PR count as several changes, aggregate merges or bulk changes the script ignored, uncommitted changes in the working tree }}

#### What was left out

{{ what the churn script left out (its "Left out" line, in a sentence), and whether you re-ran with --keep-dir, --ext or --all-files; a scope that hides coupling to files outside it; areas you did not read }}

#### Complexity and dependency checks

{{ the complexity measure; the dependency script, the layer mapping you gave it, the coverage per language, and which languages or folders you checked by hand instead. Say "no cycles found" only for what the script covered. }}

#### End-of-life lookup

{{ live from endoflife.date on the report date, or "not checked" with the reason }}

#### How the code was read

{{ whether subagents helped and that you re-opened what they cited; what you worked out by reading and did not run }}

#### Not covered

Runtime performance, scale, reliability, the delivery pipeline and security vulnerabilities. {{ add anything specific, such as production versions that are not in the repo }}

### E. Platform and dependencies

<!-- From the platform script. Three subsections. Skip the whole appendix if no
manifest was found, and say so in D. -->

#### Runtimes, frameworks and images

<!-- One bullet per component, worst first: end of life, then ending soon, then
supported. Declared = minimum allowed, pinned, or locked. Leave out "no end date set"
unless it explains a finding. -->

- **{{ product }} {{ version }}** ({{ minimum / pinned / locked }}): {{ status from the script, with the date }}.  
  `{{ file:line }}`

#### Deprecated or abandoned packages

{{ direct ones first, with the replacement the lockfile names, or "None flagged." }}

#### Lockfiles and updates

{{ when each lockfile last changed (months before HEAD) and how often the manifest changed in the window; unpinned versions; packages locked in 3 or more versions; whether Dependabot or Renovate is configured }}

### F. Vital signs

<!-- A few numbers a later review can be compared with. Fill "Now" from the
script outputs and your findings. Fill "Last review" from the previous report's
Appendix F, or write "n/a" when there is none. Keep the rows; add none. Every cell
is a number or "n / n". If a number needs a caveat, put the caveat in D. -->

| Measure | Now | Last review |
|---|---|---|
| Findings (High / Medium / Low) | {{ n / n / n }} | {{ n / n / n or n/a }} |
| Source files / test files | {{ n / n }} | {{ n / n or n/a }} |
| Hot spots with no test by name | {{ n of 10 }} | {{ n of 10 or n/a }} |
| Cycles between modules (not nested) | {{ n }} | {{ n or n/a }} |
| Imports pointing the wrong way between layers | {{ n }} | {{ n or n/a }} |
| Domain leaks and hidden dependencies (hits) | {{ n }} | {{ n or n/a }} |
| Components past end of life / ending within 6 months | {{ n / n }} | {{ n / n or n/a }} |
| Deprecated or abandoned direct packages | {{ n }} | {{ n or n/a }} |
| Months since the main lockfile last changed | {{ n }} | {{ n or n/a }} |
| Large, complex, rarely changed files listed | {{ n }} | {{ n or n/a }} |
