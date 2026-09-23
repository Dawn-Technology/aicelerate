# Readiness Rubric and Finding Format

Authoritative rubric, verdict rules, and finding formatting used by [`validate-ticket`](../SKILL.md).

---

## Readiness Rubric

Thirteen criteria, scored internally. This table is the scoring instrument, not report content: the reader gets the verdict, the findings, and a count — never a line per pass. Print a criterion only when it failed, and then as a finding in plain language, or when the user asks to see the rubric.

`Closable from` lists the sources permitted to close each one, cheapest first: repository evidence, then a draft this skill writes from that evidence, then a human.

| # | Criterion | Passes when | Closable from |
| --- | --- | --- | --- |
| 1 | **Why** | The user or business reason is stated, and it is a reason rather than a restatement of the task | human |
| 2 | **Goal** | The desired end state is observable, and someone could tell from outside whether it holds | human |
| 3 | **Title** | It states that outcome in plain language, per the [title rules](description-template.md#title-rules) | skill |
| 4 | **Scope** | One change, with in-scope and out-of-scope both stated | human |
| 5 | **Claims** | Every load-bearing claim is `verified`, or `unverifiable` with a reason. No `contradicted` claim the work depends on | repo |
| 6 | **Blocking decisions** | Every blocking branch closed as **Observed** or **Decision** | repo, human |
| 7 | **Requirements** | User-visible behaviour listed in plain language a product owner can validate | repo, skill |
| 8 | **Acceptance criteria** | Testable criteria covering the primary flow, the known edge cases, and the error paths | repo, skill, human |
| 9 | **Definition of done** | Tests, docs, and the actual validation commands, plus any migration or rollout step | repo, skill |
| 10 | **Dependencies** | Blockers named with their status; nothing waiting on an unnamed thing | repo, human |
| 11 | **Agent entry point** | The exact repository paths, contracts, and conventions the implementer reads first | repo |
| 12 | **References** | Every linked spec, ADR, or design resolves, and repository links are pinned where the repo convention asks | repo |
| 13 | **Size** | The work is one ticket. If not, a split is proposed | repo, human |

Work down that list, and let where it actually closed set the severity:

- Closed from *repo* or *skill* — the ticket should have said it and the run filled it in. Report it as `request-for-change`, naming what closed it.
- Reached *human* and answered — closed as a **Decision**. No finding.
- Reached *human* and unanswered — `blocker`. That is the only path to a blocker on criteria 1, 2, 4, 6, 8, 10, and 13.

Two criteria sit outside that rule:
- **Title** can never block: the title is this skill's to fix, so a bad one is rewritten, proposed, and reported as a `request-for-change`.
- **Claims** blocks with no human in the loop: a `contradicted` load-bearing claim is a `blocker` on repository evidence alone, because the ticket asks for work built on something that is not true.

---

## Verdict Rules

- `ready` — every criterion passes, no `blocker`, and no **Assumption** anywhere in the design tree.
- `ready-with-assumptions` — every criterion passes and no `blocker`, but at least one non-blocking branch closed as an **Assumption**. The assumptions are in the description, where the implementer can challenge them.
- `not-ready` — any `blocker`.

Never return `ready` when a load-bearing claim is `contradicted`, a blocking branch is open, the repository shows the work already done, or the ticket needs splitting. Those are `blocker` by definition, whatever the rest of the rubric says.

---

## Finding Format Rules

A finding follows the skill voice rules and contains no ids, slugs, severity tokens, or category names.

Use two paragraphs:

1. A bold problem statement followed by the repository evidence, in no more than two sentences.
2. One action paragraph starting with `→`. For a **Blocking** finding, this paragraph also contains the context, choice, options, recommendation, and later cost required by Step 4.

```text
**{The problem, as a short claim.}** {What the repository actually shows, with the path.}
→ {The one action, imperative.} {*Owner*, only when it is not the person reading.}
```

Written out, that reads:

> **The refund exclusion claim is wrong.** The description says refunds are already out of the payout total; `src/Payout.php:88` adds them back after the filter runs.
> → Confirm which behaviour is correct — the code's or the ticket's. *Ticket author.*

> **Nothing says what a customer sees when the payment provider stops answering.** Everywhere else in payments the charge is retried twice and the customer is told the outcome later (`src/Payments/Charge.php:61`); this ticket is silent.
> → Decide: keep the charge alive and tell them once we know, or fail it in front of them and let them start again? Recommend keeping it alive, since that is what the rest of payments already promises. Failing in front of them is a change customers see, so it needs product sign-off and its own acceptance criteria.

### Grouping Findings

Group findings by what the reader does about them, and use these exact words as headings:

| Group | Means | Reader's job |
| --- | --- | --- |
| **Blocking** | Nobody should start until this is settled | Answer it, or accept the recommendation |
| **Filled in for you** | The ticket should have said it; this run closed it from the repository or a stated default | Nothing, unless you disagree |
| **Worth a look** | Small, optional | Ignore it freely |

Rules:

- The bold lead must carry the gist on its own, because that is all a skim reads.
- Every reference is a path with a line — `src/Payout.php:88`, never "see the payout service". The path belongs in the evidence sentence; the question and its answers stay in plain language.
- A **Blocking** finding carries its own context, question, recommendation, and what changes if answered differently, written the way Step 4 writes them and answerable without opening the code. There is no separate questions section to repeat it in.
- A **Filled in for you** finding says what closed it: "now follows `src/Importer/Errors.php`" or "assumed unit tests, since the module has no integration harness".
- Name an owner only when it is not the reader.
- Order: **Blocking**, then **Filled in for you**, then **Worth a look**; most consequential first inside each group.
