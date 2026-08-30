# Commit Message Rules

The single source of truth for commit message content and format at Dawn
Technology. Maintain this file only — the `write-commit-message` skill and the
repo-root `commit-message.instructions.md` (which serves VS Code's Generate
Commit Message button) both point here rather than restating the rules.

This file defines **what a good message says**. It does not describe how to
gather the diff or run `git commit` — that workflow lives in the skill's
`SKILL.md`.

## Core principles

- **Clarity**: the message explains _what_ changed and _why_.
- **Security**: 🚫 NEVER include secrets, API keys, credentials, or PII.
- **Consistency**: one format, everywhere. No Conventional Commits prefixes, no
  type/scope, no emoji.

## Format

```text
<subject line>

<why: the problem or the prior behavior>

<how: the conceptual approach taken, and why that approach>

<ticket key, if there is one>
```

The structure lives in the paragraph order, not in markup. The finished message
carries no section headings, labels, or prompt lines.

## The seven rules

1. **Separate subject from body with a blank line.**
2. **Limit the subject line to ~50 characters** (72 is the hard cap; GitHub
   truncates beyond that).
3. **Capitalize the subject line.**
4. **Do not end the subject line with a period.**
5. **Use the imperative mood in the subject line** — it must complete the
   sentence "If applied, this commit will \_\_\_" (e.g. "Refactor subsystem X
   for readability", not "Fixed bug" or "Refactoring subsystem X").
6. **Wrap the body at 72 characters.**
7. **Use the body to explain _what_ and _why_, not _how_** — the diff already
   shows how; the body's job is context that would otherwise be lost. This
   applies to the "how does it address the issue?" paragraph too: describe the
   approach and its rationale, not the code mechanics.

## Subject line — write the SYMPTOM, not the mechanics

The single most common failure is describing the **code** that changed instead
of the **problem a human observed**. The subject must lead with the _user /
operator / business-observable_ symptom or goal — what someone actually saw go
wrong, or what capability was missing — **not** the classes, methods, columns,
or internal nouns involved.

Write it as if for a reader who has **never seen this code**. If the subject
only makes sense to someone who knows the internals, rewrite it.

Ban from the subject line: class names, method names (`extendDueDate()`), DB
column names (`dueDate`), and internal jargon. Name the outcome instead.

- ❌ `Fix invoice dueDate leaking payment window to frontend`
  ← names a column and an internal concept; a reader can't tell what broke.
- ✅ `Fix dashboard showing incorrect due date`

## Body — why is this change needed?

Open on the observable problem or the missing capability, never on a method,
class, or column. Start with "Prior to this change, …" and describe the prior
behavior, grounded in the diff and the ticket context. Implementation nouns may
appear later, only where they clarify the symptom.

- ❌ "Prior to this change, calling extendDueDate() on the Invoice entity
  persisted a 99-day window directly onto the dueDate column." ← opens on a
  method call and a column.
- ✅ "Prior to this change, the dashboard showed the wrong due date — the
  99-day payment-provider window instead of the customer's original 30-day
  payment term. That window only exists to satisfy the provider's expiry
  requirement; it was never meant to be shown to the customer."

## Body — how does it address the issue?

Start with "This change …" and describe the **conceptual approach** and the
**reasoning behind it**: what strategy solves the problem, why it was chosen
over the alternatives, and any consequences or trade-offs.

This is **not** a technical walkthrough of the code. The diff already shows
which classes were added, which methods, the retry logic, the env var names.
Repeating that is wasted effort and rots as the code changes. A future reader
has the diff for the _how_; they read the message for the _why_ behind the
approach.

- ✅ "Introduces a shared, reusable client so future Salesforce objects and
  triggers can hook in without re-implementing auth and error handling.
  Wiring a concrete caller is deliberately deferred to a follow-up ticket."
- ❌ "Adds SalesforceAuthenticator (OAuth2 client-credentials with cached
  token), SalesforceClient (create/upsert/get with one-time 401 retry and a
  typed SalesforceApiException), and CaseClient. Reads env vars
  SALESFORCE_URL/CLIENT_ID/CLIENT_SECRET…" ← this is the diff's job, not the
  commit message's.

## Links

Close with the ticket key on its own line — a bare key such as `PROJ-429`, or a
full URL where the tracker needs one. Extract the key from the branch name
using the pattern `[A-Z]+-\d+` (e.g. `PROJ-156`, `ABC-1211`).

If the branch name holds no key, omit the line entirely. Never invent a key,
and never block a commit on a missing one.

Do not start any line with `#`. Under `git commit --cleanup=strip` every such
line is removed from the message, so an issue reference written as `#123` at
the start of a line silently disappears. Write `Ref: #123` instead, or keep the
reference inline.

## Be terse

Good messages are short. The worked examples below are 2–5 lines of body — some
are two sentences. Do not pad. Say the symptom, say the approach, stop.

## Self-check before the message is final

- Could a reader who has **never seen this code** understand, from the
  **subject alone**, what changed for them? If it only makes sense to someone
  who knows the internals, rewrite it.
- Does the **first sentence of the body** describe an observable problem or a
  missing capability — _not_ a method, class, or column? If it opens on code,
  rewrite it.
- Is there a class, method, or column name in the subject line? Remove it.
- Does the message contain a secret, key, credential, or PII? Remove it.

## Worked examples

Real, approved messages, shown exactly as committed.

```text
Send billing notifications

Prior to this change, no billing notifications were sent to customers,
so they would not be triggered to update their company info and/or
enable/disable automatic subscription renewal.

This change sends notification emails to all users of a company 6 weeks
prior to the subscription expiring. The mails are sent after 5 am.

PROJ-218
```

```text
Link added users to their company

Prior to this change, added users were dangling.

This change properly links users to the company.

PROJ-105
```

```text
Expose company name for read-only user

Prior to this change, the dashboard could not show the company name
of the read-only user, because that user cannot fetch other companies
(as intended).

This change exposes the name directly on the profile response.
```

```text
Fix dashboard showing incorrect due date

Prior to this change, the dashboard showed the wrong due date — the
99-day payment-provider window instead of the customer's original
30-day payment term. That window only exists to satisfy the provider's
expiry requirement; it was never meant to be shown to the customer.

This change treats the payment-provider window as a provider concern
computed at request time, rather than a fact stored on the invoice. The
invoice's due date is no longer mutated, so the customer always sees the
original term while the provider still receives its required window.

PROJ-429
```
