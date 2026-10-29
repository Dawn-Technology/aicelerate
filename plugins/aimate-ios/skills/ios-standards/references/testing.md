# Testing Policy

## Framework Choice

| Context | Policy |
| --- | --- |
| Supported new unit or integration test | Prefer Swift Testing |
| Existing XCTest suite | Continue XCTest unless migration directly serves the task |
| UI automation | Use XCUITest |
| Legacy project | Follow its established framework and toolchain |
| Framework migration | Keep it explicit and separately scoped |

## Naming

Describe the subject, condition, and observable expectation. XCTest and Swift Testing use the same function names.

### Test Naming Convention

`<subject>` is the function or behavior under test in lowerCamel case, such as `loadProfile`. `<Condition>` and `<Expectation>` start with a capital letter after `with` and `should`, such as `withValidResponse` and `shouldReturnProfile`.

```swift
func test_<subject>_with<Condition>_should<Expectation>() {
    // Arrange
    <set up test data and mocks>

    // Act
    <execute the code under test>

    // Assert
    <verify expectations>
}
```

For example:

```swift
// Swift Testing (new unit tests)
@Test("loadProfile with a valid response returns the profile")
func test_loadProfile_withValidResponse_shouldReturnProfile() async throws

// XCTest (existing suites)
func test_loadProfile_withValidResponse_shouldReturnProfile() async throws

// XCUITest (UI tests)
func test_login_withValidCredentials_shouldShowHomeScreen() throws
```

For Swift Testing, use the same `test_<subject>_with<Condition>_should<Expectation>` function name and put the readable behavior in the `@Test` display name. Use parameterized tests when they remove repetitive cases.

Company naming wins over provider suggestions: do not use raw-identifier test names such as ``func `load profile with a valid response`()`` unless the project already does.

### Test Types and Files

Name the type `<Subject>Tests`: a `struct` for Swift Testing, with `@Suite` only when it needs traits or a display name, and an `XCTestCase` subclass for XCTest. Put each module's tests in its own test target (`<Module>Tests`), mirror the source folder structure, and use one file `<Subject>Tests.swift` per type under test.

### Parameterized Tests

Use the same naming pattern, with the condition describing the whole set of arguments:

```swift
@Test("parseDate with each supported format returns a date", arguments: ["yyyy-MM-dd", "dd-MM-yyyy"])
func test_parseDate_withSupportedFormats_shouldReturnDate(format: String) throws
```

### UI Tests

XCUITest methods use the same naming pattern. Find elements by accessibility identifier, not by visible text, so tests keep working when copy or language changes.

## Structure and Behavior

Use Arrange-Act-Assert structure with the three phase comments `// Arrange`, `// Act`, and `// Assert` in every test, and no other explanatory comments for the phases. Add `async` only when the test awaits, and `throws` only when it calls throwing code or uses `#require`, so the signature shows what the test does.

Tests should exercise observable behavior and deterministic state transitions. Include cancellation, ordering, lifecycle, and error behavior when the production path makes those risks reachable.
