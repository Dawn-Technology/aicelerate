# Severity guidance

Severity tells the reader what to fix first. To keep it the same between runs, it starts from a fixed default and changes only through the rules below.

## Levels

| Level | Icon | Meaning |
|---|---|---|
| Critical | 🔴 | An attacker with no account, or with an account anyone can create, can run code, bypass authentication, or read or change other users' data in bulk. |
| High | 🟠 | Directly exploitable against other users or their data, needing at most a normal account or one action by the victim. |
| Medium | 🟡 | Exploitable only with preconditions (network position, a specific browser, another weakness) or with limited impact. |
| Low | 🟢 | Hardening or documentation gap with no direct path to exploitation. |

## Setting severity for a FAIL item

1. Start from the default after the item's title in [requirements-guide.md](./requirements-guide.md), including any item-specific note there (for example #18 with SameSite cookies, #61 with a repository-pinned download digest, #70 with exposed password hashes).
2. Set each verified location's severity:
   - **Raise to Critical** when the location matches the Critical meaning above.
   - **Lower one level** when every path to the location requires an administrator or similarly privileged account.
   - Otherwise keep the default.
3. The item's severity is the highest severity among its locations.
4. When a rule changed the severity, write the reason in the finding's description.

No other adjustments. In particular, do not raise severity because you are unsure.

## Setting severity for other findings

Pick the default from the first match below, then apply steps 2–4 above.

1. One of these common cases:
   - A tracked secret file, or a hard-coded secret that grants access to production systems: High.
   - Unsafe deserialization of input the user controls: Critical.
   - Debug mode or detailed error pages enabled in production configuration: Medium.
   - Password storage with a fast or unsalted hash (MD5, SHA-1, SHA-256 without a password hashing function): High.
2. The default of the most similar of the 70 items.
3. The level whose meaning above fits best.
