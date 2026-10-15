# Agent-Ready Description Template and Rules

Authoritative template, rules, and examples for rewriting ticket descriptions in [`prepare-ticket`](../SKILL.md).

---

## Description Rules

1. **Write for the reviewer first, then the implementer.** The description has two parts split by a horizontal rule. Above it is what will be built and how anyone knows it worked: Why, Goal, What changes, Out of scope, the open questions on a not-ready ticket, Decisions and assumptions to check, and Definition of done. Below it are the Implementation notes and References. A human reviews the ticket before anyone builds it and an agent reads every line, so the order is chosen for the human: a reviewer who stops at the rule can approve the ticket, and the agent loses nothing.
2. **Keep the part above the rule to one screen**, about 400 words on a typical ticket. When it runs longer, the cause is usually evidence or code detail that belongs below the rule or in the comment, not more requirements. When it is long because the work is large, check the ticket for a split.
3. **Intent first, always.** The description opens with the why. An implementer who knows the goal recovers from the ambiguity the instructions did not anticipate; one who only has steps cannot. Only the one-line not-ready banner goes above it: no context block, question list, or metadata header.
4. **Follow the skill voice above the rule.** Keep technical identifiers out of Why, Goal, What changes, Out of scope, and the bold line of each decision, so the person who owns the outcome can read and confirm them without opening the code. A criterion names a technical detail only when the outcome itself is technical, such as an API response or an exit code. Definition of done may name commands and paths, because it is a checklist for whoever does the work.
5. **Separate the problem from the result.** Why states the current problem and its cost, with one sentence on how we know. Goal states the observable end state and ends with **How to check:** one test anyone could run from outside. Repeating the task in either leaves the implementer with steps and no way to judge a trade-off.
6. **Give behaviour one list: requirements, each with its acceptance criteria under it.** Each requirement is a short numbered heading saying what changes, in plain words. Its criteria sit directly under it in Given/When/Then and cover the primary flow, the known edge cases, and the error paths. Every criterion belongs to exactly one requirement. There is no separate in-scope list and no separate criteria list, because parallel lists of the same behaviour drift apart and the implementer cannot tell which one wins. A reviewer reads the headings to see what will be built; the implementer reads the criteria to know when it is done.
7. **Trace every criterion to the design tree.** Each outcome comes from an Observed fact, a Decision, or a non-blocking Assumption; mark a criterion that rests on an Assumption with *(assumed)*. A user-visible outcome nobody has decided is a blocking question, not a criterion to draft, because writing it would be the agent making a product decision and then grading it as settled. On a not-ready ticket, a requirement whose outcome waits on an open question names that question in place of its criteria.
8. **Name what is out of scope, and why.** An agent fills an unstated boundary with whatever looks related. Name the adjacent work a reader would assume is included, and say why it is left out or which ticket owns it.
9. **Give a required action for every prohibition.** "Do not change the export format" leaves the implementer guessing what to do instead; "Keep the export format byte-identical; add the new column to the JSON export only" does not.
10. **List only what a human should check under Decisions and assumptions.** That is every **Decision** and every **Assumption**, as a list rather than a table, because long reasons in table cells are hard to read. Each entry leads with what was chosen in bold and plain words, then its status, then who decided and when, or why this default and what changes if it is wrong. **Observed** facts are not decisions; they go in the Implementation notes. Work the run found that the ticket needs, such as a wrong reference to fix while there, goes in What changes or Definition of done, where it will be done, never here.
11. **Keep every assumption visible.** An assumption the implementer cannot see is one they cannot challenge, and it ships as if someone had decided it.
12. **Write Implementation notes as facts, not instructions.** They have three parts, each optional when empty: **Suggested approach**, how this run would build it, which the implementer may set aside; **Where the code is**, one line per path saying what it does today; and **Constraints to honour**, contracts and conventions the work must keep. One fact per bullet, two sentences at most. A path listed as a fact reads to an implementer as an order to edit it, so a view on what to change goes only under Suggested approach.
13. **Cite code by path and symbol, not by line.** Write `src/Payout.php` (`PayoutCalculator::total`), and name the evidence commit once at the top of the Implementation notes. The description outlives its line numbers; a symbol can still be found after the file changes, and the commit tells a reader how old each fact is.
14. **Put the evidence in the comment, not the description.** Measurements, run and log identifiers, the claim ledger, and the argument for the diagnosis go in the comment this skill posts, which the implementer reads too. The description keeps one sentence of proof in Why and links the comment under References. Evidence in the body buries what will be built under why we believe it is needed.
15. **Make the ticket self-contained.** Put each required fact in the description or name the repository path that contains it. External links may add detail but may not carry a required fact, because the implementer may not be able to open them. The evidence comment is part of the ticket, so it counts.
16. **Add one concrete example when behaviour is format-sensitive**, under the requirement it belongs to. A payload, an error string, or a rendered value settles in one line what a paragraph of description leaves open to interpretation.
17. **Use exact validation commands in Definition of done.** "Tests pass" leaves the implementer to guess which tests; the command is what lets them check their own work before anyone reviews it.
18. **Keep the template section order and preserve every original requirement and constraint.** Each one lands in What changes, Out of scope, or the Implementation notes. List any deliberate removal and its reason in the report, so nothing the author asked for disappears silently.

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

- **A spec file exists for this ticket** — What changes lists the requirements as headings only and links the spec, pinned to a commit, for their criteria. Everything else in the template stays.
- **No spec file exists** — the ticket *is* the spec, so every requirement carries its criteria.

---

## Template

Fixed section order. The title is not part of this body: it goes in the tracker's title field — the summary, on Jira — and is never repeated as a heading here. When `provider = none`, print it above the body.

On a `not-ready` write-back, add the one-line banner above Why and the **Open questions — blocking** section directly after Out of scope. The banner is what stops somebody building; the intent still comes first, because a reader who does not understand the point of the ticket will not answer its questions. Omit both on a ready ticket.

Omit **Decisions and assumptions to check** when the run has neither, and any Implementation notes part that is empty. Everything else is required.

```markdown
> ⚠️ **Not ready for development** — [N] blocking questions are open, under Open questions below.

## Why

[The problem somebody has today and what it costs them, in one or two plain sentences, plus one sentence on how we know. Not the task, and not the title said again.]

## Goal

[What is true once this is done, written so somebody who cannot read the code could confirm it.]

**How to check:** [One test anyone could run from outside to see that the goal holds.]

## What changes

### 1. [What changes, in plain words]

- [ ] Given [context], when [action], then [observable outcome].
- [ ] Given [edge case], when [action], then [observable outcome].
- [ ] Given [error condition], when [action], then [observable outcome and what the user sees].

### 2. [Next requirement]

- [ ] Given [context], when [action], then [outcome resting on a default]. *(assumed)*

[Only when behaviour is format-sensitive: one example under the requirement it belongs to — a payload, an error string, a rendered value, or a before-and-after.]

### 3. [Requirement whose outcome is not decided yet]

Waits on open question 1.

## Out of scope

- [Adjacent work a reader would assume is included] — [why not, or which ticket owns it].

## Open questions — blocking

> Nobody should start building until these are answered.

### 1. [The choice, in one plain sentence, no code names]

[What the system does today, what the ticket leaves open, and why the answer affects the work.] [What each answer means for the system and who notices.]

**Recommendation:** [the answer this would take, and why]. **Owner:** [who can answer]

## Decisions and assumptions to check

- **[What was chosen, in plain words]** — Decision, [who, when, where it was decided]. [Why, if it is not obvious.]
- **[Default taken]** — Assumption. [Why this default, and what changes if it is wrong.]

## Definition of done

- [ ] Tests: [a test for each criterion a test can express, at the level and in the harness named, e.g. unit tests for the calculator in `tests/...`]
- [ ] Validation: `[the exact command]`
- [ ] Docs: [file to update, or "none"]
- [ ] [Migration, rollout, or flag step, or "none"]

---

## Implementation notes

For the implementer. Facts as of commit `[evidence_sha]`.

**Suggested approach** — [Optional and non-binding. How this run would build it, and why. The implementer may choose differently and says so in the PR.]

**Where the code is**

- `path/to/entry-point.ext` (`SymbolName`) — [what it does today, one line]
- `path/to/related.ext` (`OtherSymbol`) — [what it does today, one line]

**Constraints to honour**

- `path/to/contract.ext` (`ContractName`) — [the contract this work must keep]
- [Convention to follow] — as in `path/to/example.ext` (`ExampleSymbol`)
- [Fact nobody could verify from the code] — **unconfirmed**, [who can settle it]

## References

- Evidence: [link to the validation comment]
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
> **Why** — Merchants are paid for orders they have already refunded, so finance corrects every payout run by hand and merchants have stopped trusting their statements. Last month finance corrected 41 of 60 payouts.
>
> **Goal** — A refunded order never contributes to a payout total, and the statement matches what finance works out by hand.
>
> **How to check:** refund one order of a test merchant, run the payout, and see the total drop by exactly that order.
>
> **What changes**
>
> **1. Refunded orders no longer count towards a payout**
>
> - Given an order refunded before the payout run, when the payout is calculated, then that order is not in the total.
> - Given an order partly refunded, when the payout is calculated, then only the part kept is in the total. *(assumed)*
>
> **Out of scope** — The refund flow itself. Payouts already sent: correcting those is a separate ticket.

Five things changed:

1. The title names what somebody sees rather than the class that changes.
2. The why is the cost being paid today, not the task restated, with one line of proof.
3. The goal is something a finance person could check without reading code, and says how.
4. What will be built is a short heading a reviewer can approve, with the criteria the implementer tests against under it.
5. Out of scope names the adjacent work a reader would otherwise assume was included.

Everything from the original survives, below the rule where a path is useful rather than in the way. The fact goes under Where the code is (`src/Payout.php` (`PayoutCalculator::total`) sums refunded lines). The proposed fix goes into Suggested approach, where the implementer can set it aside. The test goes into Definition of done. The partial-refund rule is listed under Decisions and assumptions to check, so finance can overrule it before anyone builds it.
