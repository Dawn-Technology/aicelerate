# Agent-Ready Description Template and Rules

Authoritative template, rules, and examples for rewriting ticket descriptions in [`prepare-ticket`](../SKILL.md).

---

## Description Rules

1. **Write for the reviewer first, then the implementer.** Above the horizontal rule are Why, Goal, What changes, Out of scope, unresolved gaps on a not-ready ticket, Decisions and assumptions to check, and Definition of done. Optional repository landmarks and References go below it. Necessary behaviour and constraints belong in the reviewer-facing contract, not hidden in technical notes.
2. **Keep the overview brief, not the contract incomplete.** Why and Goal should scan on one screen; there is no word limit for required behaviour, acceptance criteria, boundaries, or completion checks. Remove repetition and unnecessary evidence before shortening requirements. Split by independently deliverable outcomes or a necessary discovery step, never by screen length or technical surface count.
3. **Intent first, always.** The description opens with the why. An implementer who knows the goal recovers from the ambiguity the instructions did not anticipate; one who only has steps cannot. Only the one-line not-ready banner goes above it: no context block, question list, or metadata header.
4. **Follow the skill voice above the rule.** Keep technical identifiers out of Why, Goal, What changes, Out of scope, and the bold line of each decision, so the person who owns the outcome can read and confirm them without opening the code. A criterion names a technical detail only when the outcome itself is technical, such as an API response or an exit code. Definition of done may name commands and paths, because it is a checklist for whoever does the work.
5. **Separate the problem from the result.** Why states the supported problem and its consequence, with a brief source. A human-stated reason is valid without a numerical measurement; never invent costs, impact, or proof. Goal states the observable end state and ends with **How to check:** one outside observation that demonstrates it. Repeating the task in either leaves the implementer with steps and no way to judge a trade-off.
6. **Give behaviour one list: requirements, each with its acceptance criteria under it.** Use short numbered headings and testable criteria, in Given/When/Then where useful, covering the primary flow, known material edge cases, and failures. Every criterion belongs to one requirement. In explicit repository-spec mode, each heading instead points to its exact criteria section under [Spec Files vs. Tickets](#spec-files-vs-tickets). Do not maintain competing lists of the same behaviour.
7. **Trace outcomes under [Decision rules](../SKILL.md#decision-rules).** An unresolved requirement names its blocking gap instead of inventing criteria. Supporting assumptions belong in Decisions and assumptions, not in product outcomes. The completed contract undergoes [Challenge](../SKILL.md#5-challenge); do not rely on remembered conversation to fill missing criteria.
8. **Name what is out of scope, and why.** An agent fills an unstated boundary with whatever looks related. Name the adjacent work a reader would assume is included, and say why it is left out or which ticket owns it.
9. **Give a required action for every prohibition.** "Do not change the export format" leaves the implementer guessing what to do instead; "Keep the export format byte-identical; add the new column to the JSON export only" does not.
10. **List outcome decisions and non-material assumptions, not implementation choices.** Lead each entry with the choice in plain words, its status, and the decision's owner, authority, date, and source, or the assumption's rationale and why alternatives are non-material. Clear requirements already expressed in What changes need not be repeated; cite their source there. Do not invent decisions about classes, helpers, or internal layout.
11. **Keep every assumption visible.** An assumption the implementer cannot see is one they cannot challenge, and it ships as if someone had decided it.
12. **Keep Implementation notes optional and factual.** Include only useful dated landmarks or evidence supporting constraints already stated above the rule. Omit Suggested approach, edit lists, internal schema designs, and instructions to justify choosing a different implementation. Existing repository policy still applies without restating its implementation details.
13. **Keep volatile code detail out of the contract.** A useful optional landmark may cite a path and symbol rather than a line, with the evidence commit and any relevant local-change limitation. Do not require landmarks to declare readiness. Exact public formats, compatibility promises, and measurable limits remain precise acceptance criteria when they are part of the outcome.
14. **Separate evidence from the specification.** Detailed measurements and diagnosis go in an evidence comment only if posting one was authorized; otherwise keep them in the report. Why keeps a brief supported reason. Link only existing comments, never guessed URLs or placeholders. Necessary facts and constraints must remain accessible in the active contract or its required sources, regardless of comment approval.
15. **Make the active contract sufficient to build from.** The ticket contains agreed criteria unless explicit repository-spec mode applies. Required linked sources must be accessible to the implementer; copy necessary agreed facts into the active contract where permitted if a source is inaccessible, or leave a blocking evidence gap. Optional external links may add background but must not carry the only copy of a requirement.
16. **Add one concrete example when behaviour is format-sensitive**, under the requirement it belongs to. A payload, an error string, or a rendered value settles in one line what a paragraph of description leaves open to interpretation.
17. **Define validation outcomes, not a frozen test plan.** Definition of done names the behaviour to demonstrate, required regression checks, documentation obligations, and migration or rollout conditions where relevant. The implementer selects appropriate coverage and discovers current commands from the repository. A missing runner command is not a readiness gap; do not prohibit E2E coverage merely because the original ticket did not request it.
18. **Preserve valid obligations, not superseded instructions.** Map original requirements and constraints to the active contract. Record accepted corrections and superseded wording in the report and preserved history; do not append contradictions verbatim. Obtain agreement before dropping an obligation or changing scope, and leave disputed material obligations open.

---

## Title Rules

The title is the Goal, shortened to one line and written as an instruction. A reader who opens nothing else should know what will be different, and for whom, once it ships.

- Write it from the Goal, not from the original title.
- Say what someone can do, see, or no longer suffers. Not the work, the symptom, or the fix.
- Use the words the people who use the product would use. Product and service names are allowed. Class, method, table, column, and config names are not, and neither are engineering terms such as tenant, endpoint, webhook, migration, or refactor unless the team uses them as product terms.
- Write one clause. Aim for 60 characters and never exceed 80.
- Do not add a trailing period, ticket-id prefix, area tag, or type prefix such as "Bug:".
- Do not append an explanation with a colon, dash, or second sentence; it belongs in Why. Outcomes joined by "and" need splitting only when they can be delivered and accepted independently.
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

Choose one active contract; a linked file's existence does not choose it:

- **Default: the ticket is the specification.** Every requirement carries its complete agreed criteria. Linked specs are supporting context, not competing instructions; call out any superseded content.
- **Explicit repository-spec convention:** only when project instructions make a repository spec authoritative, What changes lists the requirements and points each to its exact criteria section in a pinned, accessible version. Identify that source as the active contract, and check that its scope, constraints, and criteria match all accepted decisions. Do not create a second competing criteria list in the ticket.
- **The authoritative spec needs correction:** the draft remains `not-ready` until that source contains the agreed contract. Name the gap and its owner. This skill leaves repository files untouched; rewriting the ticket or adding a decision comment cannot silently amend the linked spec.

---

## Template

Fixed section order. The title is not part of this body: it goes in the tracker's title field — the summary, on Jira — and is never repeated as a heading here. When `provider = none`, print it above the body.

On a `not-ready` write-back, add the one-line banner above Why and **Open gaps — blocking** directly after Out of scope. Include unanswered decisions, missing evidence, unsatisfied prerequisites, and other failed required checks, not only questions. Omit both on either ready verdict.

Omit **Decisions and assumptions to check** when it adds nothing beyond the sourced requirements, **Implementation notes** when there are no useful landmarks, and **References** when there are no required or useful sources. Everything else is required. Repository-spec mode uses exact section references instead of embedded criteria under each requirement.

```markdown
> ⚠️ **Not ready for development** — [N] unresolved gaps remain, under Open gaps below.

## Why

[The supported problem and its consequence, with a brief source. No invented impact or measurements. Not the task or the title said again.]

## Goal

[What is true once this is done, written so somebody who cannot read the code could confirm it.]

**How to check:** [One test anyone could run from outside to see that the goal holds.]

## What changes

### 1. [What changes, in plain words]

- [ ] Given [context], when [action], then [observable outcome].
- [ ] Given [edge case], when [action], then [observable outcome].
- [ ] Given [error condition], when [action], then [observable outcome and what the user sees].

### 2. [Next requirement]

- [ ] Given [context], when [action], then [outcome from an accepted requirement or authorized decision].

[Only when behaviour is format-sensitive: one example under the requirement it belongs to — a payload, an error string, a rendered value, or a before-and-after.]

### 3. [Requirement whose outcome is not decided yet]

Waits on open gap 1.

## Out of scope

- [Adjacent work a reader would assume is included] — [why not, or which ticket owns it].

## Open gaps — blocking

> Nobody should start building until these are resolved.

### 1. [The choice, in one plain sentence, no code names]

[What the system does today, what the ticket leaves open, and why the answer affects the work.] [What each answer means for the system and who notices.]

**Recommendation:** [the answer this would take, and why]. **Owner:** [who can answer]

[For a factual or dependency gap instead: state what is missing, why it blocks, the evidence or action needed, and its owner. Do not invent decision options for a missing fact.]

## Decisions and assumptions to check

- **[What was chosen, in plain words]** — Decision, [authorized owner, when, and source]. [Why, if it is not obvious.]
- **[Non-material supporting default]** — Assumption. [Why it is useful and why alternatives do not change an acceptance outcome or material constraint.]

## Definition of done

- [ ] Demonstrate [the required primary, edge, and failure outcomes] and preserve [relevant existing behaviour].
- [ ] Run the repository's applicable checks, discovering current commands and appropriate coverage during implementation.
- [ ] Docs: [what guidance or public contract must change, or "none"].
- [ ] [Required existing-data, compatibility, rollout, or rollback outcome, or "none"].

---

## Implementation notes

Optional discovery aids, not an edit plan. Facts as of commit `[evidence_sha]`; [relevant local-change limitation, if any].

**Where the code is**

- `path/to/entry-point.ext` (`SymbolName`) — [what it does today, one line]
- `path/to/related.ext` (`OtherSymbol`) — [what it does today, one line]

**Evidence for constraints stated above**

- `path/to/contract.ext` (`ContractName`) — [where an accepted compatibility constraint is expressed today]

## References

- Evidence: [existing comment link, only if posted with approval; otherwise omit]
- Active spec: `docs/specs/[file].md` @ `[commit]`, [exact requirement sections; only in repository-spec mode]
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

**Additional input established during preparation:**

The finance owner confirms that payouts must exclude full refunds and subtract only the refunded amount for partial refunds. They confirm that changing the refund flow and correcting payouts already sent are out of scope. Repository evidence confirms that the current calculation includes refunded amounts. These are explicit inputs to the example, not facts invented from the original wording.

**Rewritten after those decisions:**

> **Stop refunded orders inflating the merchant payout**
>
> **Why** — Refunded amounts currently remain in payout totals, so the totals include money the merchant did not keep. Finance wants payouts to exclude those amounts; the current calculation confirms the problem.
>
> **Goal** — Payouts count only the amount retained after refunds.
>
> **How to check:** refund all or part of a test order before a payout run and confirm the total excludes exactly the refunded amount.
>
> **What changes**
>
> **1. Refunded amounts no longer count towards a payout**
>
> - Given an order refunded before the payout run, when the payout is calculated, then that order is not in the total.
> - Given an order partly refunded before the payout run, when the payout is calculated, then only the amount kept is in the total.
>
> **Out of scope** — The refund flow and payouts already sent, as agreed by the finance owner. This change affects future payout calculations only.

Five things changed:

1. The title names what somebody sees rather than the class that changes.
2. The why states the supported problem and consequence, not the task restated or invented impact.
3. The goal is something a finance person could check without reading code, and says how.
4. What will be built is a short heading a reviewer can approve, with the criteria the implementer tests against under it.
5. Out of scope names the adjacent work a reader would otherwise assume was included.

The implementation hint remains in the preserved original, not as an obligation to use a particular filter or file. A useful code landmark may appear in optional Implementation notes. Verification belongs in Definition of done. The full ticket records the finance owner's decision, date, and source; partial refunds are not an assumption. If that decision had not been supplied, the ticket would retain a blocking question instead.
