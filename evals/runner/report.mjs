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
  // Infrastructure failures (usage limits, dead sessions) are excluded from
  // every statistic and reported under suite health instead.
  const invalidRuns = runs.filter((r) => r.invalidRun);
  runs = runs.filter((r) => !r.invalidRun);
  // Totals across plugin versions are not comparable: pre-fix and post-fix
  // runs would pool into one misleading number. Default to the newest stamped
  // version; meta.allVersions = true pools everything anyway (and says so).
  let versionNote = "";
  if (!meta.allVersions) {
    const vers = [...new Set(runs.map((r) => r.aimateVersion ?? "unstamped"))];
    if (vers.length > 1) {
      const semver = (v) => (v === "unstamped" ? [-1] : v.split(".").map(Number));
      const newest = vers.sort((a, b) => {
        const [x, y] = [semver(a), semver(b)];
        for (let i = 0; i < 3; i++) { if ((x[i] ?? 0) !== (y[i] ?? 0)) return (x[i] ?? 0) - (y[i] ?? 0); }
        return 0;
      }).at(-1);
      const excluded = runs.filter((r) => (r.aimateVersion ?? "unstamped") !== newest);
      runs = runs.filter((r) => (r.aimateVersion ?? "unstamped") === newest);
      versionNote = `Showing aimate ${newest} only (${runs.length} runs). Excluded as not comparable: ${excluded.length} runs from ${vers.filter((v) => v !== newest).join(", ")} — pass --all-versions to pool them anyway.`;
    }
  }
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
    ...(versionNote ? ["", versionNote] : []),
    "",
    "## What this sweep says",
    "",
    "Each verdict below covers one agreed requirement from evals/rubrics/requirements.md, graded across all runs: ✅ holding means every check passed, ❌ failing means every check failed, ⚠️ mixed means some of both. The quote under a verdict is real evidence from a run.",
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
  lines.push(`Skills fired in ${firedCases.length} of ${cases.length} cases. This line is a validity note, not a verdict: where no skill fired, the scores describe base-model behavior — which is what a developer typing that prompt gets today. That is only a problem where the fired skill measurably beats the base model (compare the control column); where the base model already meets the bar, it is evidence the skill is not needed for that request.`, "");
  const hasExplicit = runs.some((r) => r.strategy?.startsWith("aimate-"));
  const hasRace = runs.some((r) => r.strategy);
  if (hasRace && firedCases.length === 0 && !hasExplicit) {
    lines.push(`So read the strategy race below as methodology data (which workflow shape wins), not as a measure of ${subject}'s skill content. To measure skill content, run the explicit-invocation arm (--strategy aimate-plan) and compare it against spec-first, the same workflow shape without the skill.`, "");
  }
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
    lines.push("A strategy is a route from work item to working code. The arms raced here: **direct** — just implement it; **validate-implement** — first challenge the ticket against the codebase, then implement; **spec-first** — write a spec and a plan, then implement; **spikeN** — N independent attempts, and the hidden tests pick the winner.");
    lines.push("");
    lines.push("How to read the table: **acceptance** is whether hidden tests passed — tests the agent never saw, so they cannot be gamed. **review C/M/m** is how many critical, major and minor problems a code reviewer found in the result, averaged per run; 0/0/0 means a clean result, and a recurring major means a real quality gap. A **turn** is one step the agent took (a message or a tool call), and **cost** is the API spend per run. Quality decides the winner; cost only breaks ties at equal quality.", "");
    const states = [...new Set(raceRuns.map((r) => r.entryState ?? "unknown"))].sort();
    for (const state of states) {
      const stateRuns = raceRuns.filter((r) => (r.entryState ?? "unknown") === state);
      const raceCases = [...new Set(stateRuns.map((r) => r.case))].sort();
      lines.push(`### Entry state: ${state}`, "");
      lines.push("| case | strategy | acceptance | review C/M/m | avg cost | avg turns |");
      lines.push("|------|----------|-----------|--------------|---------:|----------:|");
      const armStats = [];
      for (const c of raceCases) {
        for (const strat of [...new Set(stateRuns.filter((r) => r.case === c).map((r) => r.strategy))].sort()) {
          const rs = stateRuns.filter((r) => r.case === c && r.strategy === strat);
          const accChecks = rs.map((r) => r.checks.find((x) => x.check.startsWith("held-out acceptance")));
          const measured = accChecks.some(Boolean);
          const accPass = accChecks.filter((a) => a?.pass).length;
          const rev = rs.map((r) => r.review).filter(Boolean);
          const avg = (k) => (rev.length ? rev.reduce((s, x) => s + (x[k] ?? 0), 0) / rev.length : 0);
          const [cr, ma, mi] = ["critical", "major", "minor"].map(avg);
          const revIcon = !rev.length ? "" : cr > 0 ? " ❌" : ma >= 0.5 ? " ⚠️" : " ✅";
          const revStr = rev.length ? `${cr.toFixed(1)}/${ma.toFixed(1)}/${mi.toFixed(1)}${revIcon}` : "—";
          const cost = rs.reduce((s, r) => s + (r.costUsd ?? 0), 0) / rs.length;
          const turns = rs.reduce((s, r) => s + (r.turns ?? 0), 0) / rs.length;
          const spikes = rs[0]?.spikeAttemptsPassed ? ` (spikes passing: ${rs.map((r) => r.spikeAttemptsPassed).join(", ")})` : "";
          const accIcon = !measured ? "" : accPass === rs.length ? "✅ " : accPass === 0 ? "❌ " : "⚠️ ";
          const accCell = measured ? `${accIcon}${accPass}/${rs.length}${spikes}` : "not measured (judge-only)";
          lines.push(`| ${c} | ${strat} | ${accCell} | ${revStr} | $${cost.toFixed(3)} | ${turns.toFixed(0)} |`);
          if (measured) {
            const expChecks = rs.flatMap((r) => r.checks.filter((x) => !x.check.startsWith("held-out acceptance")));
            const expRate = expChecks.length ? expChecks.filter((x) => x.pass).length / expChecks.length : 1;
            armStats.push({ strat, accRate: accPass / rs.length, expRate, cr, ma, mi, cost });
          }
        }
      }
      // name the leader: quality first (acceptance, then critical+major findings), cost as tiebreak
      if (armStats.length > 1) {
        const ranked = [...armStats].sort((a, b) =>
          b.accRate - a.accRate || b.expRate - a.expRate || (a.cr + a.ma) - (b.cr + b.ma) || a.mi - b.mi || a.cost - b.cost);
        const lead = ranked[0];
        const cheapestPassing = [...armStats].filter((a) => a.accRate === 1).sort((a, b) => a.cost - b.cost)[0];
        const majors = (n) => (n === 0 ? "no major problems" : n < 1 ? `a major problem in some runs (${n.toFixed(1)} per run on average)` : `about ${Math.round(n)} major problem(s) in every run`);
        const stateRunCount = stateRuns.length;
        let verdictText = `**In plain terms:** for ${state.replace(/-/g, " ")} work, **${lead.strat}** delivered the best quality here — ${Math.round(lead.accRate * 100)}% of its runs passed the hidden tests and reviewers found ${majors(lead.ma)}, at $${lead.cost.toFixed(2)} per run.`;
        if (lead.expRate < 1) verdictText += ` It did miss some of the case's own expectations (${Math.round(lead.expRate * 100)}% met), so read its row before trusting it.`;
        if (cheapestPassing && cheapestPassing.strat !== lead.strat) {
          verdictText += ` If you care about cost first, **${cheapestPassing.strat}** was the cheapest route that still passed every hidden test ($${cheapestPassing.cost.toFixed(2)} per run); reviewers found ${majors(cheapestPassing.ma)} in its results${cheapestPassing.expRate < 1 ? `, and it met ${Math.round(cheapestPassing.expRate * 100)}% of the case's own expectations` : ""}.`;
        }
        verdictText += ` These are early signals from ${stateRunCount} runs, not final verdicts.`;
        lines.push("", verdictText);
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
  if (invalidRuns.length) {
    lines.push(`${invalidRuns.length} run(s) were invalid for infrastructure reasons (usage limit, dead session, timeout) and are excluded from every number above — re-run them:`);
    for (const r of invalidRuns) lines.push(`- ${r.case} [${r.pipeline}${r.strategy ? `/${r.strategy}` : ""}] run ${r.run}: ${(r.notes ?? "").slice(0, 110)}`);
    lines.push("");
  }
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
  const dirs = argv.filter((a, i) => !a.startsWith("--") && i !== outIdx + 1 && argv[i - 1] !== "--last");
  const allVersions = argv.includes("--all-versions");
  // --latest: only the newest results directory (one invocation); --last N: the newest N.
  const lastIdx = argv.indexOf("--last");
  const lastN = argv.includes("--latest") ? 1 : lastIdx !== -1 ? Number(argv[lastIdx + 1]) : 0;
  let roots = dirs.length
    ? dirs
    : readdirSync(join(repoRoot, "evals", "results")).sort().map((d) => join(repoRoot, "evals", "results", d));
  if (lastN > 0 && !dirs.length) roots = roots.slice(-lastN);
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
  const text = buildReport(runs, { allVersions });
  if (outFile) { writeFileSync(outFile, text); console.log(`written: ${outFile}`); }
  else console.log(text);
}
