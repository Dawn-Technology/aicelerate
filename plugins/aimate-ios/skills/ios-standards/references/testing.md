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

Describe the subject, condition, and observable expectation.

```swift
func test_loadProfile_withValidResponse_shouldReturnProfile() async throws

func test_login_withValidCredentials_shouldShowHomeScreen() throws

@Test("loadProfile with a valid response returns the profile")
func loadProfileWithValidResponseReturnsProfile() async throws
```

For Swift Testing, put the readable behavior in the `@Test` display name and use normal lower-camel-case for the function. Use parameterized tests when they remove repetitive cases.

Company naming wins over provider suggestions: do not use raw-identifier test names such as ``func `load profile with a valid response`()`` unless the project already does.

Use Arrange-Act-Assert structure. Add phase comments only where phases are not obvious. Add `async` and `throws` only when required.

Tests should exercise observable behavior and deterministic state transitions. Include cancellation, ordering, lifecycle, and error behavior when the production path makes those risks reachable.
