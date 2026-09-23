# Agent-Ready Description Template and Rules

Authoritative template, rules, and examples for rewriting ticket descriptions in [`validate-ticket`](../SKILL.md).

---

## Description Rules

1. **Intent first, always.** The description opens with the why. An implementer who knows the goal recovers from the ambiguity the instructions did not anticipate; one who only has steps cannot. Nothing goes above it but the one-line not-ready banner in the template: no context block, no question list, no metadata header.
2. **Follow skill voice.** Keep technical identifiers out of Why, Goal, Scope, and Requirements.
3. **Separate the problem from the result.** Why states the current problem and its cost. Goal states the observable end state. Do not repeat the task in either section.
4. **Use exact technical details where implementation depends on them.** Put paths, types, endpoints, fields, and commands in Context, Acceptance criteria, Decisions and assumptions, or Definition of done. Do not use "as discussed", "the usual pattern", or an unclear pronoun in place of a named subsystem.
5. **Record provenance in the structured sections.** Mark Observed with evidence, Decision with who and when, Assumption with a rationale, and unverifiable facts as unconfirmed. Do not add these labels to Why, Goal, Scope, or Requirements.
6. **Keep every assumption visible.**
7. **Give a required action for every prohibition.**
8. **State both in-scope and out-of-scope work.**
9. **Make the ticket self-contained.** Put each required fact in the description or name the repository path that contains it. External links may add detail but may not carry a required fact.
10. **Add one concrete example when behaviour is format-sensitive.**
11. **Use exact validation commands in Definition of done.** Do not write only "tests pass".
12. **Keep the template section order and preserve every original requirement and constraint.** List any deliberate removal and its reason in the report.

---

## Title Rules

The title is the Goal, shortened to one line and written as an instruction. A reader who opens nothing else should know what will be different, and for whom, once it ships.

- Write it from the Goal, not from the original title.
- Say what someone can do, see, or no longer suffers. Not the work, the symptom, or the fix.
- Use the words the people who use the product would use. Product and service names are allowed. Class, method, table, column, and config names are not, and neither are engineering terms such as tenant, endpoint, webhook, migration, or refactor unless the team uses them as product terms.
- Write one clause. Aim for 60 characters and never exceed 80.
- Do not add a trailing period, ticket-id prefix, area tag, or type prefix such as "Bug:".
- Do not append an explanation with a colon, dash, or second sentence; it belongs in Why. Two outcomes joined by "and" mean the ticket may need splitting.
- Keep the original title when it already passes. Titles for split tickets follow the same rules.

The instruction form is deliberate. A present-tense title on a bug, such as "Payouts leave out refunded orders", reads as a report of the bug rather than the change wanted.

Before proposing the title, check:

1. Would someone who has never seen the code know what changes for them?
2. Would it still be true if the work were built another way? If not, it names the fix.
3. Does it say the same thing as the Goal?

> ❌ `Refactor PayoutCalculator to filter refunded order_lines` — names a class and a table; says nothing about who is affected.  
> ✅ `Stop refunded orders inflating the merchant payout`

> ❌ `Onboard the factory as a tenant of itself` — names the fix in engineering terms; a reader cannot tell what they gain.  
> ✅ `Let the factory work on its own backlog`

> ❌ `Add CSV export to the reports page` — describes the work, not what anyone gets.  
> ✅ `Let finance export any report as CSV`

---

## Spec Files vs. Tickets

The convention this plugin assumes is that the spec lives in the repository under `docs/specs/` and the tracker links it rather than pasting it, so nobody ends up reading a stale copy. Therefore:

- **A spec file exists for this ticket** — the description carries the why, the goal, the scope boundary, the decisions and assumptions ledger, the definition of done, the entry-point paths, and a link to the spec pinned to a commit. It does not restate the spec's requirements or acceptance criteria.
- **No spec file exists** — the ticket *is* the spec, so it carries everything, requirements and acceptance criteria included.

---

## Template

Fixed section order, and the why is always the first thing anyone reads.

The title is not part of this body. It goes in the tracker's title field — the summary, on Jira — and is never repeated as a heading here. When `provider = none`, print it above the body.

On a `not-ready` write-back, add the one-line banner above it and the **Open questions — blocking** section directly after Scope. The banner is what stops somebody building; the intent still comes first, because a reader who does not understand the point of the ticket will not answer its questions. Omit both on a ready ticket.

Omit **Examples** unless behaviour is format-sensitive; omit **Requirements** and **Acceptance criteria** when a linked spec file owns them. Everything else is required.

```markdown
> ⚠️ **Not ready for development** — [N] blocking questions are open, under Open questions below.

## Why

[The problem somebody has today and what it costs them, in one or two plain sentences. Not the task, and not the title said again.]

## Goal

[What is true once this is done, written so somebody who cannot read the code could confirm it.]

## Scope

**In scope:** [What this ticket changes.]

**Out of scope:** [The adjacent thing that will be assumed included, and is not. Name it.]

## Open questions — blocking

> Nobody should start building until these are answered.

- **Context:** [What the system does today, what the ticket leaves open, and why the answer affects the work.] **Choice:** [The choice, in one plain sentence, no code names.] [What each answer means for the system and who notices.] **Recommendation:** [the answer this would take, and why]. **Owner:** [who can answer]

## Context

[Repository facts the implementer needs. Say where each one comes from, in plain words.]

- `path/to/entry-point.ext` — [what it does today, verified in the code]
- `path/to/contract.ext` — [the contract this work must honour]
- [Convention to follow] — as established in `path/to/example.ext`
- [Fact nobody could verify from the code] — **unconfirmed**, [who can settle it]

## Requirements

- [ ] [User-visible behaviour, one sentence, plain language, no jargon outside the product domain.]
- [ ] [Next behaviour.]

## Acceptance criteria

- [ ] Given [context], when [action], then [observable outcome].
- [ ] Given [edge case], when [action], then [observable outcome].
- [ ] Given [error condition], when [action], then [observable outcome and what the user sees].

## Examples

[Only when behaviour is format-sensitive. A payload, an error string, a rendered value, or a before-and-after.]

## Decisions and assumptions

| Branch | Status | Evidence / Rationale |
| --- | --- | --- |
| [Branch] | Observed | `path/to/file.ext:12` |
| [Branch] | Decision | [Who, when, where it was decided] |
| [Branch] | Assumption | [Why this default; challenge it if it is wrong] |

## Definition of done

- [ ] [Behaviour verified: the acceptance criteria above hold.]
- [ ] Tests: [level and harness, e.g. unit tests for the calculator in `tests/...`]
- [ ] Validation: `[the exact command]`
- [ ] Docs: [file to update, or "none"]
- [ ] [Migration, rollout, or flag step, or "none"]

## References

- Spec: `docs/specs/[file].md` @ `[commit]`
- ADR: `[repository path to the ADR]`
- [Design, dashboard, or related ticket]
```

---

## What the Opening Should Read Like

The placeholders above give the shape. This is the standard — the same ticket as it arrived, and as it should read.

**As it arrived:**

> **Payout calc refactor**
>
> PayoutCalculator sums order_lines including refunded ones. Need to fix the filter in Payout.php and add a test.

**Rewritten:**

> **Stop refunded orders inflating the merchant payout**
>
> **Why** — Merchants are paid for orders they have already refunded, so finance corrects every payout run by hand and merchants have stopped trusting their statements.
>
> **Goal** — A refunded order never contributes to a payout total, and the statement matches what finance works out by hand.
>
> **Scope — in:** the payout total and the statement it feeds. **Out:** the refund flow itself, and the payouts already sent — correcting those is a separate ticket.

Four things changed:
1. The title names what somebody sees rather than the class that changes.
2. The why is the cost being paid today, not the task restated.
3. The goal is something a finance person could check without reading code.
4. The scope names the adjacent work a reader would otherwise assume was included.

Everything from the original survives — it moved down, into Context and Definition of done, where a path and a filename are useful rather than in the way.
