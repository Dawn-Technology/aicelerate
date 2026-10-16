# Drive iOS Evaluation Results

Evaluated 2026-10-16 in Claude Code using general-purpose subagents on real local checkouts, Xcode 26.6 closed, iOS 18.0 simulators, and `MobileBuildMCP` 2.7.1 through its CLI only (no MCP tools in the session). Each prompt in `evals.json` ran once without the skill (baseline) and once with `../SKILL.md`, each project on its own simulator.

## Reproduce

1. Use the checkouts and simulators named in `evals.json`.
2. Start a fresh agent per prompt without the skill, told which tools exist on the machine.
3. Start a fresh agent per prompt that loads `../SKILL.md` and follows it exactly, without reading this folder.
4. Check each result against the expected outcome in `evals.json`.

## Baseline Pattern

All three baselines reached their goal with useful evidence: the Thuisarts deep link reproduced with the cause in `SearchFeature.swift`, the KNMI add and remove flow passed, and the NPO screens were captured in both appearances. All three built in fresh DerivedData folders (slow, 5–9 GB left behind, a private-package fetch failure for NPO), read no project instructions, named no app version or backend environment, and left their simulators booted. Two uninstalled the app without saying this wipes its data, and one left the simulator in dark mode. The validate run did not state its checks before driving.

## Thuisarts: Reproduce (eval 1)

With the skill, the run read the Copilot instructions, built incrementally with the instructions' command, named version 1.2.0 (10) and the test backend, noticed that recent searches already contained "test" from the baseline, backed up the database, and cleared it before reproducing. It reproduced 2 of 2 (app in background and cold launch from the link), confirmed each in the database, pointed to `SearchFeature.swift:318` as a labeled hypothesis, and restored the starting state.

## KNMI: Validate (eval 2)

With the skill, the run wrote five checks with expected results to `plan.md` before driving, reported pass per check with screenshot and UI snapshot evidence including persistence after relaunch, and found that the Debug build talks to the production backend. It built through `MobileBuildMCP`, as the `tooling.md` order prescribes with Xcode closed, which meant a full build in that tool's own workspace (5.4 GB).

## NPO Start: Capture (eval 3)

With the skill, the run followed the `AGENTS.md` route with existing DerivedData, captured onboarding, push priming, and home in both appearances with a clean status bar, explained why light and dark look the same (no dark variants in the color assets), named the DEV backend, and restored appearance and status bar. To get back to onboarding it reset the simulator keychain after checking that no other user app was installed. It reported this, but the step is irreversible and affects every app on the simulator.

## Changes After Evaluation

`SKILL.md` now prefers a temporary simulator created and deleted by the run for fresh states, requires asking before resetting the keychain or erasing a simulator the run did not create, and asks to let carousels settle before capturing variants. These changes were not re-evaluated.
