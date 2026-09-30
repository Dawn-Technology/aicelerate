# {{ project_name }} · Architecture Review

**Report date**: {{ report_date }}  
**Git commit**: {{ git_commit }}  
**Scope**: {{ scope }}  
**History window**: {{ window_since }} to {{ window_until }}, {{ changes_read }} changes  
**Complexity measure**: {{ complexity_method }}  
**Skill version**: {{ skill_version }}  
**Reviewed & finalized by**: _____________________

## Summary

<!-- Two to four sentences. Say where the design is healthy, where it is
hurting, and the single change that would help most. A reader who stops here
must know what to do first. No bullets. -->

{{ summary }}

---

## 1. Exploration Summary

### Top churned modules

<!-- The 10-15 hot spots from Phase 1, highest score first. Role = the
architectural role the file actually plays (domain, application,
infrastructure, UI, registry, mixed). "Mixed" is itself a finding. -->

| # | File or module | Changes | LOC (growth) | Complexity | Apparent role |
|---|---|---|---|---|---|
| 1 | `{{ path }}` | {{ changes }} | {{ loc }} ({{ growth }}) | {{ complexity }} | {{ role }} |

### Coupling patterns

<!-- Group the coupled pairs into patterns. For each: which files, how often
they changed together, and whether the coupling is expected (a feature's
vertical slice, a translation pair) or a smell (unrelated modules, duplicated
rules, a hub file). Leave expected coupling out unless it explains something. -->

{{ coupling_patterns }}

---

## 2. Architectural Boundary Health

### Layer separation

<!-- One short paragraph per layer, or per component in a monorepo: Domain,
Application, Infrastructure. Say which folders make up each layer, whether the
intended architecture is declared anywhere (README, ADRs, folder names), and
how well the code keeps to it. Status per layer: Healthy / Strained / Broken. -->

| Layer | Where it lives | Status | Notes |
|---|---|---|---|
| Domain | {{ domain_paths }} | {{ status }} | {{ notes }} |
| Application | {{ application_paths }} | {{ status }} | {{ notes }} |
| Infrastructure | {{ infrastructure_paths }} | {{ status }} | {{ notes }} |

### Dependency leaks

<!-- Every place an inner layer depends on an outer one, found by the
repo-wide import search as well as the hot spot reading. Group repeats: one
row per pattern, with a count and two or three example locations. Write
"None found" with the search you ran when there are none. -->

| Leak | Count | Example locations |
|---|---|---|
| {{ leak }} | {{ count }} | `{{ file:line }}` |

---

## 3. Actionable Findings

<!-- Ordered High, then Medium, then Low. Omit an empty severity heading.
Every Location is a file:line or file:start-end that you opened and read.
Violation names the rule from design-rules.md. One row per root cause; list
extra locations of the same pattern in the same cell. -->

### High

| Location | Violation | Impact | Recommended Action |
|---|---|---|---|
| `{{ file:lines }}` | {{ rule }}: {{ what is wrong, one sentence }} | {{ maintenance / testing / stability risk }} | {{ concrete refactoring step }} |

### Medium

| Location | Violation | Impact | Recommended Action |
|---|---|---|---|

### Low

| Location | Violation | Impact | Recommended Action |
|---|---|---|---|

---

## 4. Refactoring Roadmap

<!-- Three milestones, most valuable first. Each one must be shippable on its
own without breaking callers: add the new path, move callers over, then remove
the old path. Say which findings it resolves and how you will know it worked. -->

### Milestone 1: {{ title }}

**Resolves**: {{ finding references }}  
**Steps**: {{ steps }}  
**Done when**: {{ observable outcome }}

**Before** (`{{ file:lines }}`, trimmed from the current code):

```{{ language }}
{{ before_snippet }}
```

**After** (proposed):

```{{ language }}
{{ after_snippet }}
```

### Milestone 2: {{ title }}

**Resolves**: {{ finding references }}  
**Steps**: {{ steps }}  
**Done when**: {{ observable outcome }}

### Milestone 3: {{ title }}

**Resolves**: {{ finding references }}  
**Steps**: {{ steps }}  
**Done when**: {{ observable outcome }}

---

## Method and limits

<!-- Short. The window, what the churn script excluded, which complexity
measure ran, and anything that weakens the evidence: shallow clone, little
history, squash merges hiding PR boundaries, areas not read. -->

{{ method_and_limits }}
