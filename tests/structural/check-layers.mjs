#!/usr/bin/env node
// Tier 1 check that aimate still has everything the aimate-ios layers rely on.
// Deterministic and dependency-free; runs in CI and blocks merge.
//
// review-ios and review-architecture-ios run aimate's skills and change parts of
// them by name: phases, input fields, report rows, script flags. Three more iOS
// skills return code-review's output format. When aimate renames or removes one
// of those anchors, the iOS skill still loads but quietly does the wrong thing.
// This check fails instead, naming the anchor and the iOS skill that uses it.
//
// When it fails after an aimate change: update the iOS skill to the new name and
// the anchor here in the same pull request. Do not delete an anchor the iOS
// skill still uses.

import { readFileSync, existsSync } from "node:fs";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const AIMATE = "plugins/aimate/skills";

// file in aimate -> [text that must appear, iOS skills that rely on it]
const ANCHORS = {
  "code-review/SKILL.md": [
    ["## Input Interface", "review-ios"],
    ["review_baseline:", "review-ios"],
    ["focus_areas:", "review-ios"],
    ["constraints:", "review-ios"],
    ["calling-skill", "review-ios"],
    ["Use the provided `review_baseline`", "review-ios"],
    ["## Output Interface", "review-ios, security-audit-ios, accessibility-audit-ios, fix-localization-ios"],
    ["**Machine mode**", "review-ios, security-audit-ios, accessibility-audit-ios, fix-localization-ios"],
    ["severity: security-violation | request-for-change | optional", "review-ios, ios-standards (severity tables)"],
    ["category: syntax | logic | security | style | documentation | maintainability", "security-audit-ios, accessibility-audit-ios, fix-localization-ios"],
    ["title:", "security-audit-ios, accessibility-audit-ios"],
    ["  scope:", "fix-localization-ios"],
    ["residual_gaps", "review-ios, security-audit-ios"],
  ],
  "review-pr/SKILL.md": [
    ["### Step 2 — Checkout PR/MR Branch", "review-ios (stops after the checkout)"],
    ["git worktree add", "review-ios (reviews in review-pr's worktree)"],
    ["### Step 5 — Invoke Code Review Core", "review-ios (adds its context to code-review's input)"],
    ["Report Only", "review-ios (report-only requests)"],
    ["### Step 8 — Clean Up", "review-ios (cleanup before reporting)"],
  ],
  "review-local/SKILL.md": [
    ["### Step 1 — Resolve Local Scope", "review-ios (stops after the scope)"],
    ["### Step 2 — Invoke Code Review Core", "review-ios (adds its context to code-review's input)"],
  ],
  "review-architecture/SKILL.md": [
    ["### Phase 0", "review-architecture-ios (overrides Phase 0)"],
    ["### Phase 1", "review-architecture-ios (overrides Phase 1)"],
    ["### Phase 2", "review-architecture-ios (overrides Phase 2)"],
    ["deps.py", "review-architecture-ios (replaced by swift_modules.py)"],
    ["packages.py", "review-architecture-ios (replaced by ios_platform.py)"],
    ["docs/<project-name>-architecture-review-<YYYY-MM-DD>.md", "review-architecture-ios (same report path)"],
    ["  version:", "review-architecture-ios (names the method version)"],
  ],
  "review-architecture/references/design-rules.md": [
    ["Supported Platform", "review-architecture-ios"],
    ["Dependency Health", "review-architecture-ios"],
    ["Tested Where It Changes", "review-architecture-ios"],
  ],
  "review-architecture/references/REPORT-TEMPLATE.md": [
    ["Healthy", "review-architecture-ios (verdict sentence)"],
    ["Strained", "review-architecture-ios (verdict sentence)"],
    ["Broken", "review-architecture-ios (verdict sentence)"],
    ["Complexity and dependency checks", "review-architecture-ios (appendix D)"],
    ["End-of-life lookup", "review-architecture-ios (appendix D)"],
    ["Runtimes, frameworks and images", "review-architecture-ios (appendix E)"],
    ["Deprecated or abandoned packages", "review-architecture-ios (appendix E)"],
    ["Lockfiles and updates", "review-architecture-ios (appendix E)"],
    ["Keep the rows; add none", "review-architecture-ios (appendix F)"],
    ["Source files / test files", "review-architecture-ios (appendix F)"],
    ["Hot spots with no test by name", "review-architecture-ios (appendix F)"],
    ["Cycles between modules", "review-architecture-ios (appendix F)"],
    ["Imports pointing the wrong way", "review-architecture-ios (appendix F)"],
    ["Months since the main lockfile", "review-architecture-ios (appendix F)"],
    ["Large, complex, rarely changed", "review-architecture-ios (appendix F)"],
    ["Domain leaks", "review-architecture-ios (appendix F)"],
    ["Components past end of life", "review-architecture-ios (appendix F)"],
    ["Deprecated or abandoned direct packages", "review-architecture-ios (appendix F)"],
  ],
  "review-architecture/scripts/hotspots.py": [
    ["--repo", "review-architecture-ios"],
    ["--path", "review-architecture-ios"],
    ["--module-depth", "review-architecture-ios"],
    ["--keep-dir", "review-architecture-ios"],
    ["Left out", "review-architecture-ios (reads the \"Left out\" line)"],
    ["hare a name", "review-architecture-ios (\"Share a name\" caveat)"],
    ["Tests by name", "review-architecture-ios"],
    ['"swift"', "review-architecture-ios (Swift files count as source)"],
  ],
};

const failures = [];
let checked = 0;
for (const [file, anchors] of Object.entries(ANCHORS)) {
  const path = join(repoRoot, AIMATE, file);
  if (!existsSync(path)) {
    failures.push(`${AIMATE}/${file}: missing; used by ${[...new Set(anchors.map(([, s]) => s))].join("; ")}`);
    continue;
  }
  const text = readFileSync(path, "utf8");
  for (const [needle, users] of anchors) {
    checked++;
    if (!text.includes(needle)) failures.push(`${AIMATE}/${file}: no longer contains ${JSON.stringify(needle)}; used by ${users}`);
  }
}

if (failures.length) {
  console.error(`FAIL — ${failures.length} aimate anchor(s) the aimate-ios layers rely on are gone:\n`);
  for (const f of failures) console.error(`  • ${f}`);
  console.error("\nUpdate the iOS skill to aimate's new wording and the anchor in tests/structural/check-layers.mjs together.");
  process.exit(1);
}
console.log(`OK — ${checked} aimate anchors used by the aimate-ios layers are present.`);
