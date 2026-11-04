#!/usr/bin/env node
// Tier 1 structural validation for the aicelerate marketplace and every plugin it lists.
// Deterministic and dependency-free; runs in CI and blocks merge.
//
// Checks (2-5 run once per plugin in marketplace.json, using its source path):
//   1. marketplace.json parses, every plugin source path exists, no tracked symlinks,
//      .claude-plugin/marketplace.json is identical to marketplace.json
//   2. <source>/plugin.json parses, <source>/.claude-plugin/plugin.json is identical to it,
//      and its version matches the marketplace entry and the latest RELEASE_NOTES.md entry
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

function checkMirror(mirror, source) {
  const abs = join(repoRoot, mirror);
  if (!existsSync(abs)) fail(`${mirror}: file missing (the Claude Code CLI reads from here)`);
  else if (!existsSync(join(repoRoot, source))) fail(`${source}: file missing`);
  else if (readFileSync(abs, "utf8") !== readFileSync(join(repoRoot, source), "utf8")) {
    fail(`${mirror}: differs from ${source} — keep both identical`);
  }
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

// --- 1b. no tracked symlinks, and the .claude-plugin mirrors stay identical ---
// A committed symlink materializes as a text file holding its target path on
// checkouts with core.symlinks=false (typical for Windows clones), which breaks
// plugin installation with a JSON parse error. Mirrors must be real, equal files.
import { execSync } from "node:child_process";
try {
  const symlinks = execSync("git ls-files -s", { cwd: repoRoot, encoding: "utf8" })
    .split("\n")
    .filter((l) => l.startsWith("120000"))
    .map((l) => l.split("\t")[1]);
  for (const s of symlinks) fail(`${s}: tracked as a symlink — commit a real file instead (symlinks break core.symlinks=false checkouts)`);
} catch {
  /* not a git checkout (e.g. exported archive): the mirror checks below still apply */
}
for (const [mirror, source] of [[".claude-plugin/marketplace.json", "marketplace.json"]]) {
  checkMirror(mirror, source);
}

// --- per plugin: 2. manifest mirror and versions, 3-5. skills ---
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

const summary = [];
for (const entry of pluginEntries) {
  const root = entry.source?.replace(/^\.\//, "").replace(/\/$/, "");
  if (!root || !existsSync(join(repoRoot, root))) continue; // already reported in check 1
  const name = entry.name;

  checkMirror(`${root}/.claude-plugin/plugin.json`, `${root}/plugin.json`);
  const pluginJson = readJson(`${root}/plugin.json`);
  if (pluginJson) {
    if (entry.version !== pluginJson.version) {
      fail(`${root}/plugin.json: version mismatch: marketplace.json has ${entry.version}, plugin.json has ${pluginJson.version}`);
    }
    const notesPath = join(repoRoot, root, "RELEASE_NOTES.md");
    if (!existsSync(notesPath)) {
      fail(`${root}/RELEASE_NOTES.md: file missing`);
    } else {
      const latest = readFileSync(notesPath, "utf8").match(/^## (\d+\.\d+\.\d+)/m)?.[1];
      if (!latest) {
        fail(`${root}/RELEASE_NOTES.md: no '## x.y.z' version heading found`);
      } else if (latest !== pluginJson.version) {
        fail(`${root}/RELEASE_NOTES.md: version mismatch: latest is ${latest}, plugin.json has ${pluginJson.version}`);
      }
    }
  }

  const skillsRoot = join(repoRoot, root, "skills");
  const skillDirs = existsSync(skillsRoot)
    ? readdirSync(skillsRoot).filter((d) => statSync(join(skillsRoot, d)).isDirectory())
    : (fail(`${root}/skills: directory missing`), []);
  summary.push(`${name}: ${skillDirs.length} skills`);

  for (const dir of skillDirs) {
    const rel = `${root}/skills/${dir}`;
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
}

// --- report ---
if (failures.length) {
  console.error(`FAIL — ${failures.length} structural violation(s):\n`);
  for (const f of failures) console.error(`  • ${f}`);
  process.exit(1);
}
console.log(`OK — ${summary.join("; ")}; versions consistent, links resolve, all within ${LINE_BUDGET}-line budget.`);
