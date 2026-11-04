#!/usr/bin/env node
// Tier 2 trigger and routing checks.
//
// Ranks every prompt in prompts.json against skill descriptions using
// stemmed TF-IDF, a lexical approximation of skill routing. It catches the two
// failure modes behind most real trigger bugs: a description missing the
// vocabulary users actually type (false negative) and an over-broad
// description that outranks the right skill (false positive).
//
// Two passes over every plugin listed in marketplace.json:
//   1. per plugin: prompts rank only against that plugin's own skills (positive
//      must rank #1, negative must not, --min-rank1 floor and description
//      collisions apply within the plugin)
//   2. all plugins together: fails only when the #1 skill belongs to a different
//      plugin than the expected skill (a cross-plugin takeover); swaps inside one
//      plugin are tolerated because adding skills shifts the TF-IDF weights.
//      Descriptions are also checked for collisions across plugins.
//
// A failure here usually means: fix the skill's description, not this eval.
// It cannot judge semantics — that is what the behavioral tier is for.
//
// Usage:
//   node tests/triggers/run-triggers.mjs                 # report + exit 1 on violations
//   node tests/triggers/run-triggers.mjs --min-rank1 90  # enforce a positive-prompt floor (%)
//   node tests/triggers/run-triggers.mjs --verbose       # show top-3 ranking per prompt

import { readFileSync, readdirSync, statSync, existsSync } from "node:fs";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(here, "..", "..");

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

// plugins: { pluginName: { skillName: description } }, one entry per marketplace plugin
const marketplace = JSON.parse(readFileSync(join(repoRoot, "marketplace.json"), "utf8"));
const plugins = {};
for (const entry of marketplace.plugins ?? []) {
  const skillsRoot = join(repoRoot, entry.source, "skills");
  plugins[entry.name] = {};
  if (!existsSync(skillsRoot)) continue;
  for (const dir of readdirSync(skillsRoot)) {
    const file = join(skillsRoot, dir, "SKILL.md");
    if (!statSync(join(skillsRoot, dir)).isDirectory() || !existsSync(file)) continue;
    plugins[entry.name][dir] = readDescription(readFileSync(file, "utf8"));
  }
}
const pluginOf = {};
for (const [pluginName, skills] of Object.entries(plugins)) {
  for (const skill of Object.keys(skills)) pluginOf[skill] = pluginName;
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
// An index covers one set of skills ({ name: { plugin, desc } }); IDF is computed over that set.
function buildIndex(skillSet) {
  const docs = Object.entries(skillSet).map(([name, { plugin, desc }]) => ({
    name,
    plugin,
    terms: [...tokens(name), ...tokens(name), ...tokens(name), ...tokens(desc)],
  }));
  const df = new Map();
  for (const d of docs) for (const t of new Set(d.terms)) df.set(t, (df.get(t) ?? 0) + 1);
  const idf = (t) => Math.log(1 + docs.length / (df.get(t) ?? docs.length));
  for (const d of docs) {
    d.vec = new Map();
    for (const t of d.terms) d.vec.set(t, (d.vec.get(t) ?? 0) + 1);
    for (const [t, tf] of d.vec) d.vec.set(t, (1 + Math.log(tf)) * idf(t));
    d.norm = Math.sqrt([...d.vec.values()].reduce((n, w) => n + w * w, 0)) || 1;
  }
  // Cosine scoring: normalizing by the description's vector length stops long,
  // example-rich descriptions from outranking everything on raw overlap.
  function rank(prompt) {
    const q = tokens(prompt);
    return docs
      .map((d) => {
        let dot = 0;
        for (const t of q) dot += d.vec.get(t) ?? 0;
        return { name: d.name, plugin: d.plugin, score: dot / d.norm };
      })
      .sort((a, b) => b.score - a.score);
  }
  return { docs, rank };
}

const skillSetOf = (pluginNames) =>
  Object.fromEntries(
    pluginNames.flatMap((pl) => Object.entries(plugins[pl]).map(([name, desc]) => [name, { plugin: pl, desc }]))
  );

const suite = JSON.parse(readFileSync(join(here, "prompts.json"), "utf8"));
const failures = [];
const pluginNames = Object.keys(plugins);

// --- description collision check ---
const allow = new Set((suite.collision_allow ?? []).map((pair) => [...pair].sort().join("|")));
function cosine(a, b) {
  let dot = 0, na = 0, nb = 0;
  for (const [t, w] of a) { na += w * w; if (b.has(t)) dot += w * b.get(t); }
  for (const [, w] of b) nb += w * w;
  return dot / (Math.sqrt(na) * Math.sqrt(nb) || 1);
}
// crossPlugin: only report pairs from different plugins (same-plugin pairs are pass 1's job)
function checkCollisions(docs, crossPlugin) {
  for (let i = 0; i < docs.length; i++) {
    for (let j = i + 1; j < docs.length; j++) {
      if (crossPlugin === (docs[i].plugin === docs[j].plugin)) continue;
      const key = [docs[i].name, docs[j].name].sort().join("|");
      const sim = cosine(docs[i].vec, docs[j].vec);
      if (sim > 0.6 && !allow.has(key)) {
        const where = crossPlugin ? ` (plugins "${docs[i].plugin}" and "${docs[j].plugin}")` : "";
        failures.push(`collision: "${docs[i].name}" and "${docs[j].name}"${where} descriptions are ${(sim * 100).toFixed(0)}% similar — likely to misroute (allow-list the pair in prompts.json if intentional)`);
      }
    }
  }
}

// prompts.json stays one file; each prompt's skill maps to the plugin that contains it
const promptsByPlugin = Object.fromEntries(pluginNames.map((pl) => [pl, []]));
for (const [skill, prompts] of Object.entries(suite.skills)) {
  if (!(skill in pluginOf)) failures.push(`prompts.json names unknown skill "${skill}" (not found in any marketplace plugin)`);
  else promptsByPlugin[pluginOf[skill]].push([skill, prompts]);
}

// --- pass 1: each plugin on its own ---
const rates = [];
for (const pl of pluginNames) {
  const { docs, rank } = buildIndex(skillSetOf([pl]));
  let posTotal = 0;
  let posTop1 = 0;
  for (const [skill, { positive = [], negative = [] }] of promptsByPlugin[pl]) {
    for (const p of positive) {
      posTotal++;
      const ranked = rank(p);
      const top = ranked[0];
      if (top.name === skill && top.score > 0) posTop1++;
      else failures.push(`[${pl}] positive: "${p}" → ranked #1 is "${top.name}", expected "${skill}" (which ranked #${ranked.findIndex((r) => r.name === skill) + 1})`);
      if (VERBOSE) console.log(`  [${pl}/${skill}] "${p}" → ${ranked.slice(0, 3).map((r) => `${r.name}:${r.score.toFixed(1)}`).join("  ")}`);
    }
    for (const p of negative) {
      const top = rank(p)[0];
      if (top.name === skill) failures.push(`[${pl}] negative: "${p}" must not route to "${skill}" but ranked it #1`);
    }
  }
  checkCollisions(docs, false);
  const rate = posTotal ? Math.round((100 * posTop1) / posTotal) : 100;
  rates.push({ pl, posTop1, posTotal, rate });
}

// --- pass 2: all plugins together, cross-plugin takeovers only ---
const all = buildIndex(skillSetOf(pluginNames));
for (const [skill, { positive = [] }] of Object.entries(suite.skills)) {
  if (!(skill in pluginOf)) continue;
  for (const p of positive) {
    const top = all.rank(p)[0];
    if (top.score > 0 && top.plugin !== pluginOf[skill]) {
      failures.push(`cross-plugin: "${p}" expects "${skill}" (plugin "${pluginOf[skill]}") but ranked #1 is "${top.name}" (plugin "${top.plugin}")`);
    }
  }
}
checkCollisions(all.docs, true);

// --- report ---
for (const { pl, posTop1, posTotal, rate } of rates) {
  console.log(`[${pl}] Positive prompts rank-1: ${posTop1}/${posTotal} (${rate}%, floor ${minRank1}%)`);
  if (rate < minRank1) failures.push(`[${pl}] rank-1 rate ${rate}% is below the ${minRank1}% floor`);
}
const tier3 = Object.values(suite.skills).reduce((n, s) => n + (s.tier3_only?.length ?? 0), 0);
if (tier3) console.log(`Deferred to behavioral tier (semantic routing, e.g. non-English): ${tier3} prompt(s)`);

if (failures.length) {
  console.error(`\nFAIL — ${failures.length} routing violation(s):\n`);
  for (const f of failures) console.error(`  • ${f}`);
  console.error("\nA failure here usually means a description needs the vocabulary users type — fix the description, not the eval.");
  process.exit(1);
}
console.log("OK — routing checks passed.");
