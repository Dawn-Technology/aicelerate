#!/usr/bin/env node
// Aggregate behavioral eval runs into one comparison report.
//
// Reads every per-run JSON under the given results directories (or all of
// evals/results/ when none are given), groups by case and pipeline, and prints
// a markdown comparison: checks passed, which skills fired, turns, cost and
// wall-clock, plus every failed check grouped by case. With several runs per
// case it shows pass-count spread, worst run first.
//
// Usage:
//   node evals/runner/compare.mjs [resultsDir ...] [--out file.md]

import { readFileSync, readdirSync, writeFileSync, statSync } from "node:fs";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(here, "..", "..");

const argv = process.argv.slice(2);
const outIdx = argv.indexOf("--out");
const outFile = outIdx === -1 ? null : argv[outIdx + 1];
const dirs = argv.filter((a, i) => !a.startsWith("--") && i !== outIdx + 1);
const roots = dirs.length
  ? dirs
  : readdirSync(join(repoRoot, "evals", "results")).map((d) => join(repoRoot, "evals", "results", d));

const runs = [];
for (const root of roots) {
  if (!statSync(root).isDirectory()) continue;
  for (const f of readdirSync(root).filter((f) => f.endsWith(".json"))) {
    try {
      const r = JSON.parse(readFileSync(join(root, f), "utf8"));
      if (r.case && r.pipeline) runs.push(r);
    } catch { /* not a run file */ }
  }
}
if (!runs.length) {
  console.error("no run JSONs found");
  process.exit(1);
}

const cases = [...new Set(runs.map((r) => r.case))].sort();
const pipelines = [...new Set(runs.map((r) => r.pipeline))].sort();

const fmt = (n, d = 2) => (n == null ? "?" : n.toFixed(d));
const lines = [
  "# Behavioral eval comparison", "",
  `Runs aggregated: ${runs.length} (${pipelines.join(", ")})`, "",
  `| case | ${pipelines.map((p) => `${p} checks | ${p} cost | ${p} turns`).join(" | ")} |`,
  `|------|${pipelines.map(() => "---|---:|---:").join("|")}|`,
];
for (const c of cases) {
  const cells = pipelines.map((p) => {
    const rs = runs.filter((r) => r.case === c && r.pipeline === p);
    if (!rs.length) return "— | — | —";
    const scores = rs.map((r) => `${r.pass}/${r.total}`);
    const cost = rs.reduce((s, r) => s + (r.costUsd ?? 0), 0) / rs.length;
    const turns = rs.reduce((s, r) => s + (r.turns ?? 0), 0) / rs.length;
    return `${[...new Set(scores)].join(" ")} | $${fmt(cost, 3)} | ${fmt(turns, 0)}`;
  });
  lines.push(`| ${c} | ${cells.join(" | ")} |`);
}

lines.push("", "## Skills fired per case (aimate runs)", "");
for (const c of cases) {
  const fired = [...new Set(runs.filter((r) => r.case === c && r.pipeline === "aimate").flatMap((r) => r.skillsFired))];
  lines.push(`- ${c}: ${fired.length ? fired.join(", ") : "none"}`);
}

lines.push("", "## Failed checks", "");
for (const c of cases) {
  for (const p of pipelines) {
    for (const r of runs.filter((r) => r.case === c && r.pipeline === p)) {
      for (const ch of (r.checks ?? []).filter((x) => !x.pass)) {
        lines.push(`- **${c}** [${p}${r.run > 1 || runs.filter((x) => x.case === c && x.pipeline === p).length > 1 ? ` run ${r.run}` : ""}]${ch.req ? ` (${ch.req})` : ""}: ${ch.check} — ${ch.evidence}`);
      }
    }
  }
}

const text = lines.join("\n") + "\n";
if (outFile) {
  writeFileSync(outFile, text);
  console.log(`written: ${outFile}`);
} else {
  console.log(text);
}
