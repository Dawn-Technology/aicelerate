# Legacy Projects

A legacy project is constrained, not exempt from quality.

- Preserve deployment targets, language mode, UI framework, dependency strategy, and test framework unless changing them is explicit scope.
- Match established boundaries and naming unless they create a concrete defect.
- Add behavior using the project's existing observation, navigation, dependency, and test seams.
- Prefer a small local correction over a parallel architecture.
- Do not introduce packages solely to modernize one change.
- Use availability-safe APIs required by the declared target; never raise the target incidentally.

Call out constraints that prevent the ideal implementation and state the smallest follow-up that would remove the constraint. Do not describe continued UIKit, XCTest, or MVVM use as a finding by itself.
