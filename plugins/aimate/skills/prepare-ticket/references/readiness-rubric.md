# Readiness Rubric and Finding Format

Authoritative rubric, verdict rules, and finding formatting used by [`prepare-ticket`](../SKILL.md).

---

## Readiness Rubric

Twelve criteria, assessed provisionally in Decide and scored against the actual draft and its active sources after [Challenge](../SKILL.md#5-challenge). Record **pass**, **fail**, or **not-applicable with a reason**. Use not-applicable only where the check names an absent concern, such as no dependencies or required references; do not use it for missing intent, goal, scope, criteria, or evidence.

This table is not report content: show failed checks as findings, not one line per pass. `Closable from` identifies who or what can close a check, not authority to invent the answer. Apply the authoritative [Decision rules](../SKILL.md#decision-rules); this rubric is the sole readiness scoring instrument.

| # | Criterion | Passes when | Closable from |
| --- | --- | --- | --- |
| 1 | **Why** | The user or business reason is stated, and it is a reason rather than a restatement of the task | human |
| 2 | **Goal** | The desired end state is observable, and someone could tell from outside whether it holds | human |
| 3 | **Title** | It states that outcome in plain language, per the [title rules](description-template.md#title-rules) | skill |
| 4 | **Scope** | One coherent, independently assessable outcome; requirements and boundaries are explicit. Several requirements or technical surfaces can serve that outcome | authoritative requirements, human |
| 5 | **Claims and coverage** | The full ticket and comments were read. Every material factual prerequisite has appropriate evidence. Contradicted, stale, missing, or unverifiable material premises are resolved or no longer relied on by the agreed draft | repo, permitted supporting evidence, accepted corrections |
| 6 | **Material decisions** | Every material branch closes under Decision rules as **Observed** or **Decision**, with no authority conflict or dependent decision left open | accepted constraints, authoritative requirements, human |
| 7 | **Acceptance criteria** | Every requirement has testable primary, material edge, and failure criteria in the active source, tracing to accepted requirements or decisions. The handoff challenge found no unresolved materially different compliant outcomes. Criteria placement follows [Spec Files vs. Tickets](description-template.md#spec-files-vs-tickets) | authoritative requirements, accepted constraints, human; skill writes the wording |
| 8 | **Definition of done** | Observable validation outcomes, relevant regression checks, documentation obligations, and any existing-data or rollout conditions are explicit. Runner commands and internal test design need not be settled | requirements, repo, skill |
| 9 | **Dependencies** | Material prerequisites are named with status, owner, and evidence. They are satisfied, or the work can independently proceed against a settled, available contract without guessing. Otherwise the draft is blocked; naming a pending dependency is not enough | repo, permitted supporting evidence, human |
| 10 | **Necessary constraints** | Required public contracts, compatibility promises, safeguards, and measurable limits are explicit where relevant. Internal implementation choices remain open; exact code landmarks are optional discovery aids | accepted constraints, authoritative requirements, human |
| 11 | **Required sources** | Every source the active contract relies on is accessible to the implementer and consistent with accepted decisions. Repository-spec mode names a pinned version and exact criteria sections. Inaccessible optional background is omitted or labelled non-essential | repo, permitted source reads |
| 12 | **Size** | The outcome can be delivered and accepted as one ticket without unresolved discovery first. Independent outcomes or necessary discovery are separated before this check passes; merely proposing a needed split does not pass it | requirements, repo, human |

Distinguish original-ticket findings from the final draft's state:

- Every required check still failing in the final draft is a `blocker`, whether it needs a human decision, factual evidence, source correction, or another action. Name the closing action and owner.
- A gap repaired safely in the draft from evidence, an accepted correction, or a permitted non-material default is a `request-for-change` about the original, not a remaining failure.
- A material decision answered by an authorized person closes as a **Decision**. Do not keep reporting that answered question as a blocker.
- `optional` findings do not represent failed required checks.

Apply these cases consistently:

- **Title:** rewrite a bad title from the accepted Goal before scoring the draft. Do not block on the original wording; if no outcome is settled, the Goal check fails.
- **Corrected claims:** keep the original ledger verdict and record its accepted correction. Once the active draft no longer relies on the false premise and the resulting scope is settled, that historical mistake does not block it.
- **Unknown facts:** an explanation of why evidence is unavailable does not establish a material premise. A human choice can change scope, but cannot turn a runtime guess into a verified fact.
- **Inherited behaviour:** code can support a preservation criterion only where authoritative requirements establish that it must remain. New behaviour cannot close from current code alone.
- **Dependencies:** an unfinished dependency is not automatically blocking if its settled, available contract permits independent implementation and verification. An unavailable capability required to proceed is blocking even when its ticket and owner are known.

---

## Verdict Rules

- `ready` — every applicable required check passes, every not-applicable check has a valid reason, and there is no **Assumption**.
- `ready-with-assumptions` — the same checks pass, but at least one genuinely non-material supporting **Assumption** remains visible. None may choose an acceptance outcome or weaken a material constraint.
- `not-ready` — any required check still fails, including incomplete ticket coverage, a material unknown, or an inconsistent active specification. There need not be an unanswered human question.

Never return either ready verdict when the active draft relies on a false or unsupported material premise, a material branch is open, the work is already done, or a necessary split remains unmade. Re-score affected checks after answers and corrections, and all checks after the last draft has been challenged. Map each unresolved counterexample to its affected criteria rather than inventing a separate challenge score.

Say **proposed draft** until the approved contract is saved and re-read; an unchanged ticket does not inherit its proposed draft's verdict. Missing publication permission or preservation prevents a write, not readiness of an otherwise complete draft.

---

## Finding Format Rules

A finding follows the skill voice rules and contains no ids, slugs, severity tokens, or category names.

Use two paragraphs:

1. A bold problem statement followed by the relevant evidence, or the explicit evidence limitation, in no more than two sentences.
2. One action paragraph starting with `→`. For a blocking decision, follow [How to ask](../SKILL.md#how-to-ask). For an evidence or prerequisite blocker, state what must be obtained or done and how it will resolve the gap; do not invent options for a factual unknown.

```text
**{The problem, as a short claim.}** {What the repository actually shows, with the path.}
→ {The one action, imperative.} {*Owner*, only when it is not the person reading.}
```

Written out, that reads:

> **The refund exclusion claim is wrong.** The description says refunds are already out of the payout total; `src/Payout.php:88` adds them back after the filter runs.
> → Correct the current-behaviour claim from the trace, then confirm whether the intended change and scope remain the same. *Ticket author.*

> **Nothing says what a customer sees when the payment provider stops answering.** Everywhere else in payments the charge is retried twice and the customer is told the outcome later (`src/Payments/Charge.php:61`); this ticket is silent.
> → Decide: keep the charge alive and tell them once we know, or fail it in front of them and let them start again? Recommend keeping it alive, since that is what the rest of payments already promises. Failing in front of them is a change customers see, so it needs product sign-off and its own acceptance criteria.

### Grouping Findings

Group findings by what the reader does about them, and use these exact words as headings:

| Group | Means | Reader's job |
| --- | --- | --- |
| **Blocking** | Nobody should start until this is resolved | Make the named decision or obtain the required evidence or prerequisite |
| **Filled in for you** | The draft closes an original gap from evidence, an accepted correction, or a non-material default | Nothing, unless you disagree |
| **Worth a look** | Small, optional | Ignore it freely |

Rules:

- The bold lead must carry the gist on its own, because that is all a skim reads.
- Code evidence cites a path and line actually read; other factual evidence cites its permitted source and date. Missing evidence says so rather than inventing a reference. Citations stay in the evidence sentence, not the question.
- A **Blocking** decision carries its own context, question, recommendation, and later cost, answerable without opening the code. Other blockers name their missing evidence or action and owner. Do not duplicate them in a separate report question list.
- A **Filled in for you** finding says what closed it, such as an accepted correction or a verified preservation constraint; it must not hide an outcome decision as a default.
- Name an owner only when it is not the reader.
- Order: **Blocking**, then **Filled in for you**, then **Worth a look**; most consequential first inside each group.
