# Review Architecture iOS Evaluation Results

Evaluated 2026-10-20 in Claude Code using general-purpose subagents on real local checkouts. The baseline is `aimate`'s `review-architecture` 1.2.0 run unchanged on each iOS project; the GREEN run is `../SKILL.md`. Reports were written to a scratchpad instead of the projects' `docs/` folders so the client repositories stayed untouched.

## Reproduce

1. Use the checkouts named in `evals.json`. First confirm the scripts still run on Xcode's Python 3.9: `for s in ../scripts/*.py; do xcrun python3 "$s" --repo <checkout> > /dev/null || echo "FAIL $s"; done`.
2. Run `aimate`'s `review-architecture` per project with the report path redirected outside the repo.
3. Start a fresh agent per prompt that loads `../SKILL.md` and every file it links, with the same redirect, without reading this folder.
4. Check each result against the known architecture facts and shared criteria in `evals.json`.

## Baseline Pattern

The generic skill found real design problems on all three projects (duplicated tap and link routing whose copies differ, an overloaded root reducer, Domain importing UIKit and SwiftUI), so its method transfers. Its tooling did not: `deps.py` read 0 Swift files, `packages.py` found no package manifest, `hotspots.py` lumped all targets into one module and ranked generated OpenAPI files and a minified `proj4.js` as hot spots, "Share a name" treated `*Feature` reducers as one slice, endoflife.date reported iOS 15 and 16 as not end of life, and the Domain/Application/Infrastructure rules had nothing for TCA, MVVM-C, or Apple frameworks. Every run rebuilt the module graph, platform facts, and lockfile comparison by hand.

## GREEN Results

- **Thuisarts**: found the four-way link routing whose copies disagree, three overloaded reducers, and hand-written `==` on `SearchFeature.Action` covering 20 of 32 cases (even `.onAppear == .onAppear` is false); the iOS signals produced that finding.
- **NPO Start**: confirmed the lane-tap routing copied in four view models with differing behavior, profile rules in the repository and a screen instead of the domain, and recommended `test-ios` and `security-audit-ios` where relevant.
- **KNMI**: found `MainFeature` (1,170 lines, three core tests skipped since April 2025), a live-location permission rule copied three times with differing results after one commit changed only one copy, and hand-written equality hiding state from `TestStore` in two reducers.

All three wrote one report outside the repo, stated no iOS support dates, and left git state unchanged.

## Changes After Evaluation

From the GREEN runs' notes: `swift_modules.py` now treats plain-name dependencies as products unless they name a target, maps local package products to their targets, lists unused package dependencies (counting build plugins as use), checks `Package.resolved` pins against manifest requirements, separates production from test and mock targets in the undeclared-import list, and accepts `--layer` patterns to report outward imports. `ios_platform.py` now reads multi-line `.package(` declarations (revision pins, pre-release requirements) and prints build settings per Xcode target. `SKILL.md` clarified the path to the generic skill, multi-package churn, registries, test matching for scoped runs, commit subjects on merge workflows, the vital-signs rows, and the report version line; `ios-design-rules.md` defines "recorded deviation" and default severities. The script changes were verified on the three repositories; the skill text changes were not re-evaluated with a full run.

## Python Version (2026-10-20)

The user chose to run all scripts with `xcrun python3`, the Python 3.9.6 that Xcode ships, instead of whatever `python3` is on the path. Both scripts now exit with a clear message below Python 3.9. Verified: `swift_modules.py`, `ios_platform.py`, and `aimate`'s `hotspots.py` run on Xcode's Python 3.9.6 against all three projects.
