# Evaluate ticket preparation

These cases check whether a skill revision leaves a buildable outcome contract without inventing decisions or prescribing implementation. They include blocked cases and complete controls, so asking more questions or blocking more tickets is not automatically better.

## Run a comparison

Use [scenarios.json](scenarios.json) as fixed input. Compare the previous and proposed skill, together with each revision's own references, in separate fresh contexts. Keep the model and evaluation conditions the same. Do not run these evaluations during ordinary ticket preparation.

1. Give each preparation agent the chosen skill revision and the case's `id`, `shared_input`, and `input` without `scripted_replies`. Merge the input by top-level key, with the case taking precedence. The host retains `scripted_replies` and `expected`; do not expose either or other cases' answers.
2. Resume at the case's named concern, mapped to the equivalent phase in that revision. The supplied context is an offline snapshot; do not fetch a real ticket, inspect this repository for extra facts, invoke fetch delegates, or make real writes.
3. Act as the user with `scripted_replies`: release an answer only after the agent asks the corresponding question. If a question has no supplied answer, record it as unanswered and end that branch. Do not turn a missing answer into a default or reveal later answers early.
4. Keep each case independent. Record questions and answers in order, accepted decisions, draft changes, unresolved gaps with their owners, the verdict and whether it concerns a proposed or saved artifact, the handoff challenge, and proposed writes. For publication cases, record simulated operations and read-backs without claiming any real ticket changed.
5. Freeze both revisions' outputs before showing their expected outcomes to a separate assessment pass. Compare meaning, not exact wording. Record the evidence for each assessment rather than accepting the agent's own claim that it passed.

The same procedure works with a human running two isolated chats or a host's isolated-agent mechanism. The JSON is test input, not an executable runner. Do not treat a static JSON or link check as a behavioral evaluation.

## What to assess

For every case, mark each `must_do` and `must_not_do` expectation **pass**, **fail**, or **inconclusive**, with a short output excerpt or a precise missing result. Compare the final verdict with `expected.verdict`; when `proposed_writes` is present, compare the exact permitted write set. A proposed draft can be ready while publication is blocked.

Judge whether each revision:

- Misses a material question or leaves an answered question blocking.
- Invents an outcome, business fact, approval, or evidence.
- Confuses current facts, desired behavior, decision authority, or the active specification source.
- Keeps conflicting requirements or loses necessary behavior to shorten the description.
- Turns internal implementation freedom into a product decision.
- Detects materially different outcomes in the handoff challenge without rejecting harmless implementation alternatives.
- Proposes unauthorized writes or presents a simulated operation as a real one.

Do not score by question counts, finding counts, word counts, or mechanically filling sections. A scenario passes only when its required behavior is demonstrated, its prohibited behavior is absent, its verdict matches, and any constrained write set matches. Missing output is inconclusive, not a pass.

Record actual improvements, regressions, and unchanged cases for both revisions, including any cases not completed. Keep transcripts and comparison notes in session storage, not in ticket descriptions or this fixed fixture file. A single comparison is evidence about these cases, not proof of general reliability.
