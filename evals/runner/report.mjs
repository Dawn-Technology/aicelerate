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
  lines.push(`Skills fired in ${firedCases.length} of ${cases.length} cases. A run without a fired skill measures the base model, not ${subject} — which is also what a developer typing that prompt gets today.`, "");
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
  lines.push(graderFailures.length ? `Grader failures (these are eval problems, not ${subject} findings):` : "No grader failures.");
  for (const g of graderFailures) lines.push(`- ${g}`);
  if (timeouts.length) { lines.push("Timed-out runs:"); for (const t of timeouts) lines.push(`- ${t}`); }
  const runsPerCase = Math.max(...cases.map((c) => subjectRuns.filter((r) => r.case === c).length), 0);
  if (runsPerCase < 3) lines.push("", `Only ${runsPerCase} run(s) per case: exploratory numbers. Treat verdicts as directional; a formal baseline needs 3 runs and the spread read before the mean.`);
  lines.push("", `Reproduce one case: \`node evals/runner/run-eval.mjs <case-id> --pipeline ${subject}\``);

  return lines.join("\n") + "\n";
}

// --- HTML twin: same content as the markdown, readable in a browser ---
// A small converter for the constructs this report actually emits (headings,
// tables, bold, blockquotes, lists, inline code), wrapped in self-contained CSS.
export function mdToHtml(md, title = "Eval report") {
  const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const inline = (s) => esc(s)
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>");
  const lines = md.split("\n");
  const out = [];
  let i = 0;
  while (i < lines.length) {
    const l = lines[i];
    if (/^### /.test(l)) { out.push(`<h3>${inline(l.slice(4))}</h3>`); i++; continue; }
    if (/^## /.test(l)) { out.push(`<h2>${inline(l.slice(3))}</h2>`); i++; continue; }
    if (/^# /.test(l)) { out.push(`<h1>${inline(l.slice(2))}</h1>`); i++; continue; }
    if (/^\|/.test(l)) {
      const rows = [];
      while (i < lines.length && /^\|/.test(lines[i])) { rows.push(lines[i]); i++; }
      const cells = (r) => r.replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
      out.push("<table><thead><tr>" + cells(rows[0]).map((c) => `<th>${inline(c)}</th>`).join("") + "</tr></thead><tbody>");
      for (const r of rows.slice(2)) out.push("<tr>" + cells(r).map((c) => `<td>${inline(c)}</td>`).join("") + "</tr>");
      out.push("</tbody></table>");
      continue;
    }
    if (/^> /.test(l)) {
      const q = [];
      while (i < lines.length && /^> /.test(lines[i])) { q.push(inline(lines[i].slice(2))); i++; }
      out.push(`<blockquote>${q.join("<br>")}</blockquote>`);
      continue;
    }
    if (/^- /.test(l)) {
      out.push("<ul>");
      while (i < lines.length && /^- /.test(lines[i])) { out.push(`<li>${inline(lines[i].slice(2))}</li>`); i++; }
      out.push("</ul>");
      continue;
    }
    if (l.trim() === "") { i++; continue; }
    out.push(`<p>${inline(l)}</p>`);
    i++;
  }
  return `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(title)}</title><style>
:root{--bg:#fff;--fg:#1a1a1a;--muted:#667;--line:#dde;--accent:#2563eb;--quote:#f6f7f9}
@media (prefers-color-scheme: dark){:root{--bg:#111418;--fg:#e8eaed;--muted:#99a;--line:#2a2f36;--accent:#60a5fa;--quote:#1a1f26}}
body{background:var(--bg);color:var(--fg);font:15px/1.6 system-ui,sans-serif;max-width:920px;margin:2rem auto;padding:0 16px}
h1{font-size:1.6rem;border-bottom:2px solid var(--line);padding-bottom:.4rem}
h2{font-size:1.25rem;margin-top:2.2rem;border-bottom:1px solid var(--line);padding-bottom:.3rem}
h3{font-size:1.05rem;margin-top:1.6rem}
table{border-collapse:collapse;width:100%;margin:.8rem 0;font-size:.92em}
th,td{border:1px solid var(--line);padding:.45rem .6rem;text-align:left;vertical-align:top}
th{background:var(--quote)}
blockquote{margin:.6rem 0;padding:.5rem .9rem;border-left:3px solid var(--accent);background:var(--quote);color:var(--muted);font-size:.93em}
code{background:var(--quote);padding:.1em .35em;border-radius:4px;font-size:.9em}
li{margin:.15rem 0}
</style></head><body>${out.join("\n")}</body></html>`;
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
  if (outFile) {
    writeFileSync(outFile, text);
    const htmlFile = outFile.replace(/\.md$/, "") + (outFile.endsWith(".md") ? ".html" : ".html");
    writeFileSync(htmlFile, mdToHtml(text, "Eval report"));
    console.log(`written: ${outFile} and ${htmlFile}`);
  } else console.log(text);
}
