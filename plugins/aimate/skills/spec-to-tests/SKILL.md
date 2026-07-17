---
name: spec-to-tests
description: Read the acceptance-criteria block from a PRD or spec and scaffold failing test stubs in the repository's own test framework, one or more per criterion, each tagged with its criterion id. Use when the user wants to generate tests from a spec, scaffold tests from the PRD, or turn acceptance criteria into a test skeleton.
metadata:
  author: "Dawn Technology"
  version: 1.0.0
---

# Spec to Tests

## Purpose

Turn the acceptance criteria in a spec into executable test stubs. Each criterion in the spec becomes at least one test stub in the repository's own test framework, tagged with the criterion id so the link between spec and test is traceable in both directions.

The stubs are stubs. They lay down the arrange/act/assert structure and leave a failing or pending assertion for a human or a coding agent to complete. This skill never writes a passing test — a green suite for behaviour nobody has implemented is worse than no test at all.

This skill reads the shared canonical acceptance-criteria format defined in [`../../shared/acceptance-criteria.md`](../../shared/acceptance-criteria.md). It does not define its own format. Read that file before parsing a spec.

## Inputs

- **Spec file** — a PRD produced by `write-prd`, or any spec that ends with an `## Acceptance Criteria` block in the shared format. If the user gives a path, use it. If not, look under `docs/spec/` and, if several specs exist, ask which one.

## Workflow

Follow the steps in order.

### Step 1 — Locate and parse the acceptance-criteria block

1. Open the spec file and find the `## Acceptance Criteria` block bounded by the `<!-- acceptance-criteria:start format=gwt/v1 -->` and `<!-- acceptance-criteria:end -->` sentinels.
2. If the block is missing, stop and tell the user: the spec has no machine-readable acceptance criteria, so re-run `write-prd` to add one, or point this skill at a spec that has one.
3. If the `format=` marker is a version this skill does not recognise, stop and report the mismatch rather than guessing at the grammar.
4. Extract each criterion: its id (`AC-<n>`), title, and the Given/When/Then lines. Keep the id exactly as written — it is the join key you will stamp onto every stub.

### Step 2 — Detect the test framework

Inspect the repository rather than assuming. Do not proceed on a guess — the framework decides the file layout, naming, and assertion style of every stub. Look for these signals and settle on the framework the evidence supports:

| Stack | Detection signals | Default framework | Test file convention |
|-------|-------------------|-------------------|----------------------|
| PHP | `composer.json`, `phpunit.xml` / `phpunit.xml.dist`; `pestphp/pest` in `composer.json` | PHPUnit (Pest if present) | `tests/`, `*Test.php` |
| JavaScript / TypeScript | `package.json` dev deps `jest` or `vitest`; `jest.config.*`, `vitest.config.*` | Jest or Vitest (match what is installed) | `__tests__/` or `*.test.ts` / `*.spec.ts` next to source |
| Python | `pyproject.toml`, `pytest.ini`, `setup.cfg` `[tool:pytest]`, a `tests/` dir | pytest | `tests/`, `test_*.py` |
| Go | `go.mod` | `testing` (standard library) | `*_test.go` beside source |

Confirm the choice against how the project already writes tests: find an existing test file and match its directory, naming, imports, and assertion style. Existing repo convention wins over the table default.

**If no framework can be detected**, degrade gracefully. Do not silently pick one. State clearly what you looked for and did not find, and ask the user to name the framework and test directory. Offer to emit framework-neutral pseudocode stubs (arrange/act/assert as comments) as a fallback so the criteria are still captured.

### Step 3 — Map criteria to stubs

Map each criterion to at least one stub:

- One criterion, one behaviour, at least one test stub. Split into several stubs when a criterion has multiple `**Then**` outcomes that are worth asserting independently.
- Every stub carries its criterion id in a form the framework makes greppable — the test name and a comment both contain `AC-<n>`. This gives traceability in both directions: from a criterion you can find its tests, and from a test you can find its criterion.
- Translate the criterion straight into structure: `**Given**` → arrange, `**When**` → act, `**Then**` → assert. Leave the arrange/act sections as clearly marked TODOs and the assert as a failing or pending assertion.

Group stubs into files following the convention confirmed in Step 2. Name files after the feature or spec, not after this skill.

### Step 4 — Generate the stubs

Write each stub with the arrange/act/assert skeleton and an assertion that keeps the suite red. Prefer the framework's idiomatic "incomplete/pending" marker; where none exists, use an explicit failing assertion. Never leave a stub that passes.

PHPUnit:

```php
/** @covers AC-1: Account balance is shown on the home screen */
public function testAc1AccountBalanceIsShownOnHomeScreen(): void
{
    // Given a logged-in user
    // TODO: arrange the logged-in user

    // When the user opens the app
    // TODO: act — open the app

    // Then the account balance is displayed prominently on the home screen
    $this->markTestIncomplete('AC-1 not yet implemented');
}
```

Jest / Vitest:

```ts
// AC-1: Account balance is shown on the home screen
test('AC-1 account balance is shown on the home screen', () => {
  // Given a logged-in user
  // TODO: arrange the logged-in user

  // When the user opens the app
  // TODO: act — open the app

  // Then the account balance is displayed prominently on the home screen
  throw new Error('AC-1 not yet implemented');
});
```

pytest:

```python
def test_ac1_account_balance_is_shown_on_home_screen():
    """AC-1: Account balance is shown on the home screen."""
    # Given a logged-in user
    # TODO: arrange the logged-in user

    # When the user opens the app
    # TODO: act — open the app

    # Then the account balance is displayed prominently on the home screen
    pytest.fail("AC-1 not yet implemented")
```

Go:

```go
// TestAC1AccountBalanceIsShownOnHomeScreen covers AC-1.
func TestAC1AccountBalanceIsShownOnHomeScreen(t *testing.T) {
	// Given a logged-in user
	// TODO: arrange the logged-in user

	// When the user opens the app
	// TODO: act — open the app

	// Then the account balance is displayed prominently on the home screen
	t.Fatal("AC-1 not yet implemented")
}
```

### Step 5 — Report

After writing the files, report back:

- The framework detected and the evidence that led to it.
- Each file created or modified.
- A mapping table of criterion id → test name(s) → file, so the user can see every criterion is covered by a stub.
- The command to run the new tests, discovered from the project config. Note that they are expected to fail until implemented.

## Guardrails

- Never fabricate a passing test. Every generated stub must fail or report as incomplete until a human or agent implements it.
- Never invent a criteria format. Read only the shared canonical block; if it is absent or a newer grammar version, stop and report.
- Match the repository's existing test conventions over the table defaults.
- Keep the criterion id verbatim across the spec, the test name, and the comment — it is the join key.
