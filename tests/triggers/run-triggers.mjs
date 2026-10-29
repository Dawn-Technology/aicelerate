#!/usr/bin/env node
// Tier 2 trigger and routing checks.
//
// Ranks every prompt in prompts.json against all skill descriptions using
// stemmed TF-IDF, a lexical approximation of skill routing. It catches the two
// failure modes behind most real trigger bugs: a description missing the
// vocabulary users actually type (false negative) and an over-broad
// description that outranks the right skill (false positive).
//
// A failure here usually means: fix the skill's description, not this eval.
// It cannot judge semantics — that is what the behavioral tier is for.
//
// Usage:
//   node tests/triggers/run-triggers.mjs                 # report + exit 1 on violations
//   node tests/triggers/run-triggers.mjs --min-rank1 90  # enforce a positive-prompt floor (%)
//   node tests/triggers/run-triggers.mjs --verbose       # show top-3 ranking per prompt

import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(here, "..", "..");
const skillsRoot = join(repoRoot, "plugins/aimate/skills");

const args = process.argv.slice(2);
const VERBOSE = args.includes("--verbose");
const minRank1 = args.includes("--min-rank1")
  ? Number(args[args.indexOf("--min-rank1") + 1])
  : 90;

// --- load skill descriptions (handles plain, quoted and folded `>` scalars) ---
function readDescription(text) {
  const end = text.indexOf("\n---", 3);
  const fm = text.slice(3, end).split("\n");
  for (let i = 0; i < fm.length; i++) {
    const m = fm[i].match(/^description:\s*(.*)$/);
    if (!m) continue;
    let val = m[1].trim();
    if (val === ">" || val === "|" || val === "") {
      const lines = [];
      for (let j = i + 1; j < fm.length && /^\s+\S/.test(fm[j]); j++) lines.push(fm[j].trim());
      val = lines.join(" ");
    }
    return val.replace(/^["']|["']$/g, "");
  }
  return "";
}

const skills = {};
for (const dir of readdirSync(skillsRoot)) {
  if (!statSync(join(skillsRoot, dir)).isDirectory()) continue;
  skills[dir] = readDescription(readFileSync(join(skillsRoot, dir, "SKILL.md"), "utf8"));
}

// --- tokenization: lowercase, strip punctuation, drop stopwords, crude stem ---
const STOP = new Set(
  "a an and are as at be by for from has how i in is it its me my of on or our so that the this to use user when with you your we want asks ask asked".split(" ")
);
function stem(w) {
  if (w.length > 4 && w.endsWith("ies")) return w.slice(0, -3) + "y";
  return w.replace(/(ing|ed|es|s)$/, (m) => (w.length - m.length >= 3 ? "" : m));
}
// Unigrams plus adjacent bigrams: "pull request" or "commit message" carries
// far more routing signal than either word alone.
function tokens(text) {
  const words = text
    .toLowerCase()
    .replace(/[^a-z0-9à-ÿ\s-]/g, " ")
    .split(/[\s-]+/)
    .filter((w) => w.length > 1 && !STOP.has(w))
    .map(stem);
  const grams = [...words];
  for (let i = 0; i < words.length - 1; i++) grams.push(`${words[i]}_${words[i + 1]}`);
  return grams;
}

// --- build TF-IDF vectors; skill name tokens count triple ---
const docs = Object.entries(skills).map(([name, desc]) => ({
  name,
  terms: [...tokens(name), ...tokens(name), ...tokens(name), ...tokens(desc)],
}));
const df = new Map();
for (const d of docs) for (const t of new Set(d.terms)) df.set(t, (df.get(t) ?? 0) + 1);
const idf = (t) => Math.log(1 + docs.length / (df.get(t) ?? docs.length));
for (const d of docs) {
  d.vec = new Map();
  for (const t of d.terms) d.vec.set(t, (d.vec.get(t) ?? 0) + 1);
  for (const [t, tf] of d.vec) d.vec.set(t, (1 + Math.log(tf)) * idf(t));
}

// Cosine scoring: normalizing by the description's vector length stops long,
// example-rich descriptions from outranking everything on raw overlap.
function rank(prompt) {
  const q = tokens(prompt);
  return docs
    .map((d) => {
      let dot = 0, norm = 0;
      for (const [, w] of d.vec) norm += w * w;
      for (const t of q) dot += d.vec.get(t) ?? 0;
      return { name: d.name, score: dot / (Math.sqrt(norm) || 1) };
    })
    .sort((a, b) => b.score - a.score);
}

// --- run the prompt suite ---
const suite = JSON.parse(readFileSync(join(here, "prompts.json"), "utf8"));
const failures = [];
let posTotal = 0;
let posTop1 = 0;

for (const [skill, { positive = [], negative = [] }] of Object.entries(suite.skills)) {
  if (!(skill in skills)) {
    failures.push(`prompts.json names unknown skill "${skill}"`);
    continue;
  }
  for (const p of positive) {
    posTotal++;
    const ranked = rank(p);
    const top = ranked[0];
    if (top.name === skill && top.score > 0) posTop1++;
    else failures.push(`positive: "${p}" → ranked #1 is "${top.name}", expected "${skill}" (which ranked #${ranked.findIndex((r) => r.name === skill) + 1})`);
    if (VERBOSE) console.log(`  [${skill}] "${p}" → ${ranked.slice(0, 3).map((r) => `${r.name}:${r.score.toFixed(1)}`).join("  ")}`);
  }
  for (const p of negative) {
    const top = rank(p)[0];
    if (top.name === skill) failures.push(`negative: "${p}" must not route to "${skill}" but ranked it #1`);
  }
}

// --- description collision check ---
const allow = new Set((suite.collision_allow ?? []).map((pair) => [...pair].sort().join("|")));
function cosine(a, b) {
  let dot = 0, na = 0, nb = 0;
  for (const [t, w] of a) { na += w * w; if (b.has(t)) dot += w * b.get(t); }
  for (const [, w] of b) nb += w * w;
  return dot / (Math.sqrt(na) * Math.sqrt(nb) || 1);
}
for (let i = 0; i < docs.length; i++) {
  for (let j = i + 1; j < docs.length; j++) {
    const key = [docs[i].name, docs[j].name].sort().join("|");
    const sim = cosine(docs[i].vec, docs[j].vec);
    if (sim > 0.6 && !allow.has(key)) {
      failures.push(`collision: "${docs[i].name}" and "${docs[j].name}" descriptions are ${(sim * 100).toFixed(0)}% similar — likely to misroute (allow-list the pair in prompts.json if intentional)`);
    }
  }
}

// --- report ---
const rate = posTotal ? Math.round((100 * posTop1) / posTotal) : 100;
const tier3 = Object.values(suite.skills).reduce((n, s) => n + (s.tier3_only?.length ?? 0), 0);
console.log(`Positive prompts rank-1: ${posTop1}/${posTotal} (${rate}%, floor ${minRank1}%)`);
if (tier3) console.log(`Deferred to behavioral tier (semantic routing, e.g. non-English): ${tier3} prompt(s)`);
if (rate < minRank1) failures.push(`rank-1 rate ${rate}% is below the ${minRank1}% floor`);

if (failures.length) {
  console.error(`\nFAIL — ${failures.length} routing violation(s):\n`);
  for (const f of failures) console.error(`  • ${f}`);
  console.error("\nA failure here usually means a description needs the vocabulary users type — fix the description, not the eval.");
  process.exit(1);
}
console.log("OK — routing checks passed.");
