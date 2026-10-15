#!/usr/bin/env node
// Builds the human-readable eval report: findings grouped by requirement with
// a verdict and curated evidence, not a log of how the sweep executed.
//
// Reads per-run JSONs (from one or more results directories), groups every
// requirement-tagged check by its requirement id, and renders:
//   1. "What this sweep says" — per requirement: holding / failing / mixed /
//      no data, one or two evidence quotes, affected cases, and the same
//      pass-rate for the vanilla control when control runs are present.
//   2. Skill routing — which skills fired per case, since nothing else in a
//      run matters when no skill engaged.
//   3. Case-specific expectations (checks without a requirement id).
//   4. Scorecard appendix — the per-case, per-pipeline table.
//   5. Suite health — grader failures, timeouts: problems with the eval
//      itself, kept apart from findings about the subject.
//
// Usage:
//   node evals/runner/report.mjs [resultsDir ...] [--out report.md]
//   (no dirs: aggregate everything under evals/results/)

import { readFileSync, readdirSync, writeFileSync, statSync, existsSync } from "node:fs";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(here, "..", "..");

// --- requirement titles from the requirements doc ---
export function loadRequirementTitles() {
  const text = readFileSync(join(repoRoot, "evals/rubrics/requirements.md"), "utf8");
  const titles = {};
  for (const m of text.matchAll(/\*\*(R\d+) — ([^.*]+)[.*]/g)) titles[m[1]] = m[2].trim();
  return titles;
}

export function loadRuns(dirs) {
  const runs = [];
  for (const root of dirs) {
    if (!existsSync(root) || !statSync(root).isDirectory()) continue;
    for (const f of readdirSync(root).filter((f) => f.endsWith(".json"))) {
      try {
        const r = JSON.parse(readFileSync(join(root, f), "utf8"));
        if (r.case && r.pipeline && Array.isArray(r.checks)) runs.push(r);
      } catch { /* not a run file */ }
    }
  }
  return runs;
}

const pct = (pass, total) => (total ? Math.round((100 * pass) / total) : null);

function verdict(pass, total) {
  if (!total) return "no data";
  if (pass === total) return "holding";
  if (pass === 0) return "failing";
  return "mixed";
}
const VERDICT_ICON = { holding: "✅", failing: "❌", mixed: "⚠️", "no data": "—" };

export function buildReport(runs, meta = {}) {
  const titles = loadRequirementTitles();
  const subject = meta.subject ?? "aimate";
  const control = "vanilla";
  const subjectRuns = runs.filter((r) => r.pipeline === subject);
  const controlRuns = runs.filter((r) => r.pipeline === control);
  const pipelines = [...new Set(runs.map((r) => r.pipeline))].sort();
  const cases = [...new Set(runs.map((r) => r.case))].sort();

  const statsFor = (rs, req) => {
    const checks = rs.flatMap((r) => r.checks.filter((c) => c.req === req).map((c) => ({ ...c, case: r.case, run: r.run })));
    return { checks, pass: checks.filter((c) => c.pass).length, total: checks.length };
  };

  const reqIds = [...new Set(subjectRuns.flatMap((r) => r.checks.map((c) => c.req).filter(Boolean)))].sort();
  const lines = [
    `# Eval report — ${subject}`,
    "",
    `${subjectRuns.length} ${subject} run(s) over ${cases.length} case(s)` +
      (controlRuns.length ? `, with ${controlRuns.length} ${control} control run(s)` : ", no control runs") +
      (meta.header ? ` — ${meta.header}` : ""),
    "",
    "## What this sweep says",
    "",
  ];

  // committed baseline, for the reviewer's "did my change regress anything"
  const baselinePath = join(repoRoot, "evals", "baseline.json");
  const baseline = existsSync(baselinePath) ? JSON.parse(readFileSync(baselinePath, "utf8")) : null;

  for (const req of reqIds) {
    const s = statsFor(subjectRuns, req);
    const v = verdict(s.pass, s.total);
    const c = statsFor(controlRuns, req);
    const failing = s.checks.filter((x) => !x.pass);
    const failCases = [...new Set(failing.map((x) => x.case))];
    lines.push(`### ${VERDICT_ICON[v]} ${req} ${titles[req] ?? ""} — ${v}`);
    lines.push("");
    let head = `${s.pass}/${s.total} checks passed`;
    if (c.total) head += ` (${control} control: ${c.pass}/${c.total})`;
    const b = baseline?.requirements?.[req];
    if (b) {
      const now = pct(s.pass, s.total), was = pct(b.pass, b.total);
      if (now != null && was != null) head += ` — baseline ${was}%, now ${now}%${now < was ? " **(regression)**" : now > was ? " (improvement)" : ""}`;
    }
    if (failCases.length) head += `. Failing in: ${failCases.join(", ")}.`;
    lines.push(head);
    for (const ev of failing.sort((a, b) => a.evidence.length - b.evidence.length).slice(0, 2)) {
      lines.push(`> ${ev.case}: ${ev.evidence}`);
    }
    lines.push("");
  }

  // routing
  lines.push("## Skill routing", "");
  const firedCases = cases.filter((c) => subjectRuns.some((r) => r.case === c && r.skillsFired?.length));
  lines.push(`Skills fired in ${firedCases.length} of ${cases.length} cases. A run without a fired skill measures the base model, not ${subject}.`, "");
  for (const c of cases) {
    const fired = [...new Set(subjectRuns.filter((r) => r.case === c).flatMap((r) => r.skillsFired ?? []))];
    lines.push(`- ${c}: ${fired.length ? fired.join(", ") : "none"}`);
  }
  lines.push("");

  // case-specific (unkeyed) checks
  const unkeyed = subjectRuns.flatMap((r) => r.checks.filter((c) => !c.req).map((c) => ({ ...c, case: r.case })));
  if (unkeyed.length) {
    lines.push("## Case-specific expectations", "");
    for (const u of unkeyed.filter((u) => !u.pass)) lines.push(`- ❌ **${u.case}**: ${u.check} — ${u.evidence}`);
    const okCount = unkeyed.filter((u) => u.pass).length;
    lines.push(`- ✅ ${okCount} other case-specific check(s) passed`, "");
  }

  // strategy race: delivery runs carry a strategy and an entry state. The
  // reader's question is "which path should this kind of work take?" —
  // quality first (held-out acceptance, then review findings), cost as tiebreak.
  const raceRuns = runs.filter((r) => r.strategy);
  if (raceRuns.length) {
    lines.push("## Strategy race (per entry state)", "");
    lines.push("Quality decides; cost only breaks ties at equal quality. Acceptance = held-out tests the agent never saw.", "");
    const states = [...new Set(raceRuns.map((r) => r.entryState ?? "unknown"))].sort();
    for (const state of states) {
      const stateRuns = raceRuns.filter((r) => (r.entryState ?? "unknown") === state);
      const raceCases = [...new Set(stateRuns.map((r) => r.case))].sort();
      lines.push(`### Entry state: ${state}`, "");
      lines.push("| case | strategy | acceptance | review C/M/m | avg cost | avg turns |");
      lines.push("|------|----------|-----------|--------------|---------:|----------:|");
      for (const c of raceCases) {
        for (const strat of [...new Set(stateRuns.filter((r) => r.case === c).map((r) => r.strategy))].sort()) {
          const rs = stateRuns.filter((r) => r.case === c && r.strategy === strat);
          const accChecks = rs.map((r) => r.checks.find((x) => x.check.startsWith("held-out acceptance")));
          const measured = accChecks.some(Boolean);
          const accPass = accChecks.filter((a) => a?.pass).length;
          const rev = rs.map((r) => r.review).filter(Boolean);
          const revStr = rev.length
            ? `${(rev.reduce((s, x) => s + (x.critical ?? 0), 0) / rev.length).toFixed(1)}/${(rev.reduce((s, x) => s + (x.major ?? 0), 0) / rev.length).toFixed(1)}/${(rev.reduce((s, x) => s + (x.minor ?? 0), 0) / rev.length).toFixed(1)}`
            : "—";
          const cost = rs.reduce((s, r) => s + (r.costUsd ?? 0), 0) / rs.length;
          const turns = rs.reduce((s, r) => s + (r.turns ?? 0), 0) / rs.length;
          const spikes = rs[0]?.spikeAttemptsPassed ? ` (spikes passing: ${rs.map((r) => r.spikeAttemptsPassed).join(", ")})` : "";
          const accCell = measured ? `${accPass}/${rs.length}${spikes}` : "not measured (judge-only)";
          lines.push(`| ${c} | ${strat} | ${accCell} | ${revStr} | $${cost.toFixed(3)} | ${turns.toFixed(0)} |`);
        }
      }
      lines.push("");
    }
  }

  // scorecard appendix
  lines.push("## Scorecard (appendix)", "");
  lines.push(`| case | ${pipelines.map((p) => `${p} checks | ${p} cost | ${p} turns`).join(" | ")} |`);
  lines.push(`|------|${pipelines.map(() => "---|---:|---:").join("|")}|`);
  const fmt = (n, d = 3) => (n == null ? "?" : n.toFixed(d));
  for (const c of cases) {
    const cells = pipelines.map((p) => {
      const rs = runs.filter((r) => r.case === c && r.pipeline === p);
      if (!rs.length) return "— | — | —";
      const scores = [...new Set(rs.map((r) => `${r.pass}/${r.total}`))].join(" ");
      const cost = rs.reduce((s, r) => s + (r.costUsd ?? 0), 0) / rs.length;
      const turns = rs.reduce((s, r) => s + (r.turns ?? 0), 0) / rs.length;
      return `${scores} | $${fmt(cost)} | ${fmt(turns, 0)}`;
    });
    lines.push(`| ${c} | ${cells.join(" | ")} |`);
  }
  lines.push("");

  // suite health
  const graderFailures = runs.flatMap((r) =>
    (r.notes ?? "").match(/unparseable|invalid/i) ? [`${r.case} [${r.pipeline}] run ${r.run}: ${r.notes.slice(0, 120)}`] : []);
  const timeouts = runs.filter((r) => r.timedOut).map((r) => `${r.case} [${r.pipeline}] run ${r.run}`);
  lines.push("## Suite health", "");
  lines.push(graderFailures.length ? `Grader failures (these are eval problems, not ${subject} findings):` : "No grader failures.");
  for (const g of graderFailures) lines.push(`- ${g}`);
  if (timeouts.length) { lines.push("Timed-out runs:"); for (const t of timeouts) lines.push(`- ${t}`); }
  const runsPerCase = Math.max(...cases.map((c) => subjectRuns.filter((r) => r.case === c).length), 0);
  if (runsPerCase < 3) lines.push("", `Only ${runsPerCase} run(s) per case: exploratory numbers. Treat verdicts as directional; a formal baseline needs 3 runs and the spread read before the mean.`);
  lines.push("", `Reproduce one case: \`node evals/runner/run-eval.mjs <case-id> --pipeline ${subject}\``);

  return lines.join("\n") + "\n";
}

// --- CLI ---
if (resolve(process.argv[1] ?? "") === fileURLToPath(import.meta.url)) {
  const argv = process.argv.slice(2);
  const outIdx = argv.indexOf("--out");
  const outFile = outIdx === -1 ? null : argv[outIdx + 1];
  const dirs = argv.filter((a, i) => !a.startsWith("--") && i !== outIdx + 1);
  const roots = dirs.length
    ? dirs
    : readdirSync(join(repoRoot, "evals", "results")).map((d) => join(repoRoot, "evals", "results", d));
  const runs = loadRuns(roots);
  if (!runs.length) { console.error("no run JSONs found"); process.exit(1); }
  if (argv.includes("--write-baseline")) {
    const subjectRuns = runs.filter((r) => r.pipeline === "aimate");
    const reqs = {};
    for (const r of subjectRuns) for (const c of r.checks) {
      if (!c.req) continue;
      reqs[c.req] ??= { pass: 0, total: 0 };
      reqs[c.req].total++;
      if (c.pass) reqs[c.req].pass++;
    }
    const baseline = { written: new Date().toISOString(), runs: subjectRuns.length, requirements: reqs };
    writeFileSync(join(repoRoot, "evals", "baseline.json"), JSON.stringify(baseline, null, 2) + "\n");
    console.log("baseline written: evals/baseline.json");
  }
  const text = buildReport(runs);
  if (outFile) { writeFileSync(outFile, text); console.log(`written: ${outFile}`); }
  else console.log(text);
}
