#!/usr/bin/env node
// Tier 1 structural validation for the aicelerate marketplace and the aimate plugin.
// Deterministic and dependency-free; runs in CI and blocks merge.
//
// Checks:
//   1. marketplace.json parses, every plugin source path exists, versions match plugin.json
//   2. plugin.json parses and its version matches the latest RELEASE_NOTES.md entry
//   3. every skill directory has a SKILL.md with frontmatter name + description,
//      and the frontmatter name matches the directory name
//   4. every relative markdown link in a skill's SKILL.md and references/ resolves
//   5. no SKILL.md exceeds the line budget

import { readFileSync, readdirSync, existsSync, statSync } from "node:fs";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const LINE_BUDGET = 500; // the one knob: max lines per SKILL.md

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const failures = [];
const fail = (msg) => failures.push(msg);

function readJson(relPath) {
  const abs = join(repoRoot, relPath);
  if (!existsSync(abs)) {
    fail(`${relPath}: file missing`);
    return null;
  }
  try {
    return JSON.parse(readFileSync(abs, "utf8"));
  } catch (e) {
    fail(`${relPath}: invalid JSON (${e.message})`);
    return null;
  }
}

// Minimal frontmatter parser: top-level `key: value` pairs between --- fences.
function parseFrontmatter(text, relPath) {
  if (!text.startsWith("---")) {
    fail(`${relPath}: missing frontmatter`);
    return {};
  }
  const end = text.indexOf("\n---", 3);
  if (end === -1) {
    fail(`${relPath}: unterminated frontmatter`);
    return {};
  }
  const fields = {};
  for (const line of text.slice(3, end).split("\n")) {
    const m = line.match(/^([A-Za-z_][\w-]*):\s*(.*)$/);
    if (m) fields[m[1]] = m[2].replace(/^["']|["']$/g, "").trim();
  }
  return fields;
}

// --- 1. marketplace.json ---
const marketplace = readJson("marketplace.json");
const pluginEntries = marketplace?.plugins ?? [];
for (const entry of pluginEntries) {
  const src = entry.source?.replace(/^\.\//, "");
  if (!src || !existsSync(join(repoRoot, src))) {
    fail(`marketplace.json: plugin "${entry.name}" source "${entry.source}" does not exist`);
  }
}

// --- 2. plugin.json vs marketplace.json vs RELEASE_NOTES.md ---
const pluginJson = readJson("plugins/aimate/plugin.json");
if (pluginJson) {
  const marketEntry = pluginEntries.find((p) => p.name === "aimate");
  if (marketEntry && marketEntry.version !== pluginJson.version) {
    fail(`version mismatch: marketplace.json has ${marketEntry.version}, plugin.json has ${pluginJson.version}`);
  }
  const notesPath = join(repoRoot, "plugins/aimate/RELEASE_NOTES.md");
  if (!existsSync(notesPath)) {
    fail("plugins/aimate/RELEASE_NOTES.md: file missing");
  } else {
    const latest = readFileSync(notesPath, "utf8").match(/^## (\d+\.\d+\.\d+)/m)?.[1];
    if (!latest) {
      fail("RELEASE_NOTES.md: no '## x.y.z' version heading found");
    } else if (latest !== pluginJson.version) {
      fail(`version mismatch: RELEASE_NOTES.md latest is ${latest}, plugin.json has ${pluginJson.version}`);
    }
  }
}

// --- 3, 4, 5. skills ---
const skillsRoot = join(repoRoot, "plugins/aimate/skills");
const skillDirs = existsSync(skillsRoot)
  ? readdirSync(skillsRoot).filter((d) => statSync(join(skillsRoot, d)).isDirectory())
  : (fail("plugins/aimate/skills: directory missing"), []);

function checkLinks(absFile, relFile) {
  const text = readFileSync(absFile, "utf8");
  // [label](target) — skip images' size suffixes, absolute URLs, anchors, mailto
  for (const m of text.matchAll(/\[[^\]]*\]\(([^)\s]+)\)/g)) {
    const target = m[1];
    if (/^(https?:|mailto:|#)/.test(target)) continue;
    if (/^(…|\.{3})$/.test(target)) continue; // placeholder link in example content
    const clean = target.split("#")[0];
    if (!clean) continue;
    if (!existsSync(resolve(dirname(absFile), clean))) {
      fail(`${relFile}: broken relative link "${target}"`);
    }
  }
}

for (const dir of skillDirs) {
  const rel = `plugins/aimate/skills/${dir}`;
  const skillFile = join(skillsRoot, dir, "SKILL.md");
  if (!existsSync(skillFile)) {
    fail(`${rel}: SKILL.md missing`);
    continue;
  }
  const text = readFileSync(skillFile, "utf8");
  const fm = parseFrontmatter(text, `${rel}/SKILL.md`);
  if (!fm.name) fail(`${rel}/SKILL.md: frontmatter missing "name"`);
  else if (fm.name !== dir) fail(`${rel}/SKILL.md: frontmatter name "${fm.name}" != directory "${dir}"`);
  if (!fm.description) fail(`${rel}/SKILL.md: frontmatter missing "description"`);

  const lines = text.split("\n").length;
  if (lines > LINE_BUDGET) fail(`${rel}/SKILL.md: ${lines} lines exceeds budget of ${LINE_BUDGET}`);

  checkLinks(skillFile, `${rel}/SKILL.md`);
  const refsDir = join(skillsRoot, dir, "references");
  if (existsSync(refsDir)) {
    for (const f of readdirSync(refsDir).filter((f) => f.endsWith(".md"))) {
      checkLinks(join(refsDir, f), `${rel}/references/${f}`);
    }
  }
}

// --- report ---
if (failures.length) {
  console.error(`FAIL — ${failures.length} structural violation(s):\n`);
  for (const f of failures) console.error(`  • ${f}`);
  process.exit(1);
}
console.log(`OK — ${skillDirs.length} skills validated, versions consistent, links resolve, all within ${LINE_BUDGET}-line budget.`);
