#!/usr/bin/env python3
"""Deterministic static inventory for wcag-audit.

Walks a target repository (applying the skill's exclusions), detects the stack,
records which WCAG-governed features are present, and emits candidate leads
with file:line. Leads are NOT findings; the auditor must confirm each one.

Usage: scan.py TARGET [--out inventory.json] [--max-files N]
Exit codes: 0 ok, 2 bad input (missing/empty target).
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date

EXCLUDED_DIRS = {
    "node_modules", "dist", "build", "out", "target", ".next", ".nuxt", ".git", ".svn", ".hg",
    "coverage", ".nyc_output", "__pycache__", ".pytest_cache", ".cache", ".turbo", "storybook-static",
    "__tests__", "__mocks__", "test", "tests", "spec", "e2e", "cypress", "fixtures",
    "cache", "tmp", "var", "bower_components",
}
# Third-party or generated trees identified by path (Composer vendor, Drupal core/contrib/libraries, CMS files).
THIRD_PARTY_PATH = re.compile(r"(^|/)(vendor|core|contrib|libraries|sites/[^/]+/files)(/|$)|(^|/)files/(cache|php|css|js|styles)(/|$)")
SENSITIVE = re.compile(r"(^\.env(\..*)?$|^secrets\.json$|^credentials\.json$|\.(pem|key|pub|p12|pfx)$)", re.I)
SKIP_NAME = re.compile(r"(\.min\.(js|css)$|\.bundle\.js$|\.map$|\.(test|spec|stories|story)\.[a-z]+$|"
                       r"^(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|composer\.lock)$)", re.I)
MARKUP = {".html", ".htm", ".twig", ".jsx", ".tsx", ".vue", ".svelte", ".php", ".erb", ".hbs",
          ".handlebars", ".njk", ".liquid", ".astro", ".cshtml", ".razor", ".jinja", ".j2"}
SCRIPT = {".js", ".mjs", ".cjs", ".ts"}
STYLE = {".css", ".scss", ".sass", ".less", ".styl"}
MAX_BYTES = 1_000_000
LEAD_CAP = 25

# Feature presence decides applicability (N/A) — governed SC IDs listed per feature.
FEATURES = {
    "video": (r"<video\b|<iframe\b[^>]*(youtube|vimeo)|\bvideo\.js\b|plyr", ["1.2.1", "1.2.2", "1.2.3", "1.2.4", "1.2.5", "1.4.2"]),
    "audio": (r"<audio\b|new\s+Audio\(", ["1.2.1", "1.4.2"]),
    "caption_track": (r"<track\b[^>]*kind=[\"']?(captions|subtitles)", ["1.2.2", "1.2.4"]),
    "img": (r"<img\b|<Image\b|<picture\b", ["1.1.1", "1.4.5"]),
    "svg": (r"<svg\b", ["1.1.1", "1.4.11"]),
    "canvas": (r"<canvas\b", ["1.1.1"]),
    "iframe": (r"<iframe\b", ["4.1.2"]),
    "form": (r"<form\b|<input\b|<select\b|<textarea\b|<Form\b|<Input\b", ["1.3.5", "3.3.1", "3.3.2", "3.3.3", "3.3.4", "3.3.7"]),
    "password_or_login": (r"type=[\"']?password|autocomplete=[\"']?(current|new)-password|captcha", ["3.3.8"]),
    "autoplay": (r"\bautoplay\b", ["1.4.2", "2.2.2"]),
    "marquee_blink": (r"<marquee\b|<blink\b", ["2.2.2", "2.3.1"]),
    "css_animation": (r"@keyframes|animation\s*:|requestAnimationFrame", ["2.2.2", "2.3.1"]),
    "meta_refresh_or_timeout": (r"http-equiv=[\"']?refresh|setTimeout\([^)]*location", ["2.2.1"]),
    "session_timeout": (r"session.{0,20}(timeout|expire)|idle.?timeout", ["2.2.1"]),
    "key_handlers": (r"keydown|keyup|keypress|onKeyDown|@keydown|\(keydown\)|hotkeys|mousetrap", ["2.1.1", "2.1.4"]),
    "drag": (r"draggable|dragstart|ondrag|sortable|dnd-kit|react-beautiful-dnd|pointermove", ["2.5.7"]),
    "gestures": (r"touchstart|touchmove|gesture|pinch|swipe|hammerjs|Hammer\(", ["2.5.1", "2.5.2"]),
    "pointer_down": (r"mousedown|pointerdown|touchstart|onMouseDown|onPointerDown", ["2.5.2"]),
    "device_motion": (r"devicemotion|deviceorientation|DeviceMotionEvent|accelerometer", ["2.5.4"]),
    "orientation_lock": (r"orientation\.lock|@media[^{]*orientation\s*:", ["1.3.4"]),
    "lang_switch": (r"\blang=[\"'][a-z]{2}", ["3.1.1", "3.1.2"]),
    "dialog": (r"role=[\"']dialog|<dialog\b|aria-modal", ["2.1.2", "2.4.3", "4.1.2"]),
    "live_region": (r"aria-live|role=[\"'](status|alert|log)", ["4.1.3"]),
    "tooltip_hover": (r"role=[\"']tooltip|:hover|mouseenter|onMouseEnter|title=", ["1.4.13"]),
    "help_mechanism": (r"contact|help|support|chat|faq", ["3.2.6"]),
    "nav": (r"<nav\b|role=[\"']navigation", ["2.4.1", "2.4.5", "3.2.3"]),
    "skip_link": (r"href=[\"']#(main|content|main-content|skip)", ["2.4.1"]),
}

ATTR = lambda tag, name: re.search(r"(?<![\w-])" + name + r"\s*=", tag, re.I)
INPUT_SKIP = re.compile(r"type\s*=\s*[\"']?(hidden|submit|button|reset|image)", re.I)
PURPOSE_NAME = re.compile(r"(?:name|id)\s*=\s*[\"'][^\"']*(e-?mail|phone|tel|first.?name|last.?name|"
                          r"given.?name|family.?name|full.?name|postal|zip|street|address|city|country|birth)"
                          r"|type\s*=\s*[\"']?(email|tel)\b", re.I)
WEAK_AUTOCOMPLETE = re.compile(r"autocomplete\s*=\s*[\"']?(off|on|none|false|)[\"']?(?=[\s/>])", re.I)


def tags(text, name):
    for m in re.finditer(r"(?<![\"'])<" + name + r"\b[^>]*?/?>", text, re.I | re.S):
        yield m


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def snip(s):
    return re.sub(r"\s+", " ", s)[:160]


SKIP_LINK = re.compile(r"<a\b[^>]*href=[\"']#([\w-]+)[\"'][^>]*>(?:(?!</a>).){0,200}?(skip|main content|naar (de )?(hoofd)?inhoud|spring)", re.I | re.S)
STATIC_ID = re.compile(r"\bid\s*=\s*[\"']([\w-]+)[\"']")


def skip_link_leads(markup):
    """Cross-file: skip-link targets that exist nowhere, and <main> elements that lack the skip target id."""
    targets, ids, mains = {}, set(), []
    for path, text in markup:
        for m in SKIP_LINK.finditer(text):
            targets.setdefault(m.group(1), []).append((path, text, m))
        ids.update(STATIC_ID.findall(text))
        for m in re.finditer(r"(?<![\"'])<main\b[^>]*>", text, re.I):
            mains.append((path, text, m))
    out = []
    for tid, links in sorted(targets.items()):
        if tid not in ids:
            for path, text, m in links:
                out.append({"sc_id": "2.4.1", "rule": "skip-link-target-missing", "file": path,
                            "line": line_of(text, m.start()), "snippet": snip(m.group(0))})
    if targets:
        for path, text, m in mains:
            tag = m.group(0)
            got = STATIC_ID.search(tag)
            if "{{" in tag or (got and got.group(1) in targets):
                continue
            out.append({"sc_id": "2.4.1", "rule": f"main-without-skip-target (#{'/#'.join(sorted(targets))})",
                        "file": path, "line": line_of(text, m.start()), "snippet": snip(tag)})
    return out


def lead_rules(path, ext, text):
    out = []

    def add(sc, rule, m):
        out.append({"sc_id": sc, "rule": rule, "file": path, "line": line_of(text, m.start()), "snippet": snip(m.group(0))})

    if ext in MARKUP:
        for m in tags(text, "img"):
            if not ATTR(m.group(0), "alt") and not re.search(r"\{\s*\.\.\.", m.group(0)):
                add("1.1.1", "img-missing-alt", m)
        for m in tags(text, "input"):
            t = m.group(0)
            if INPUT_SKIP.search(t):
                continue
            if not any(ATTR(t, a) for a in ("aria-label", "aria-labelledby", "id", "title", ":id", "\\[id\\]")):
                add("3.3.2", "input-no-label-hook", m)
            if PURPOSE_NAME.search(t) and (not ATTR(t, "autocomplete") or WEAK_AUTOCOMPLETE.search(t)):
                add("1.3.5", "personal-input-no-autocomplete-token", m)
        for m in tags(text, "iframe"):
            if not ATTR(m.group(0), "title") and not ATTR(m.group(0), "aria-label"):
                add("4.1.2", "iframe-no-title", m)
        for m in re.finditer(r"<button\b[^>]*>\s*</button>", text, re.I | re.S):
            if not re.search(r"aria-label|aria-labelledby|title=", m.group(0), re.I):
                add("4.1.2", "empty-button", m)
        for m in re.finditer(r"<(div|span|li|td|img)\b[^>]*(onClick|onclick|@click|v-on:click|\(click\))\s*=[^>]*>", text, re.S):
            t = m.group(0)
            if not ATTR(t, "role"):
                add("4.1.2", "click-on-non-interactive-no-role", m)
            if not re.search(r"tabindex|tabIndex", t) or not re.search(r"key(down|up|press)|onKey", t, re.I):
                add("2.1.1", "click-on-non-interactive-no-keyboard", m)
        for m in re.finditer(r"tab[iI]ndex\s*=\s*[\"'{]?\s*([1-9]\d*)", text):
            add("2.4.3", "positive-tabindex", m)
        for m in re.finditer(r"<a\b[^>]*>\s*(click here|here|read more|more|lees meer|meer|klik hier|learn more)\s*</a>", text, re.I | re.S):
            add("2.4.4", "ambiguous-link-text", m)
        for m in re.finditer(r"<a\b[^>]*>\s*</a>", text, re.I | re.S):
            if not re.search(r"aria-label|aria-labelledby|title=", m.group(0), re.I):
                add("2.4.4", "empty-link", m)
        for m in tags(text, "html"):
            if not ATTR(m.group(0), "lang") and not re.search(r"html_attributes|\{\{|\{%|<\?", m.group(0)):
                add("3.1.1", "html-no-lang", m)
        if re.search(r"<html\b", text, re.I) and not re.search(r"<title\b|<Title\b|head_title|\{\{\s*title", text):
            m = re.search(r"<html\b", text, re.I)
            add("2.4.2", "document-no-title", m)
        for m in tags(text, "video"):
            if not re.search(r"<track\b", text[m.start():m.start() + 4000], re.I):
                add("1.2.2", "video-no-track", m)
            if ATTR(m.group(0), "autoplay") and not ATTR(m.group(0), "muted"):
                add("1.4.2", "autoplay-unmuted-media", m)
        for m in tags(text, "audio"):
            if ATTR(m.group(0), "autoplay"):
                add("1.4.2", "autoplay-audio", m)
        for m in re.finditer(r"<(marquee|blink)\b", text, re.I):
            add("2.2.2", "marquee-blink", m)
        for m in re.finditer(r"<meta\b[^>]*http-equiv=[\"']?refresh[^>]*>", text, re.I):
            add("2.2.1", "meta-refresh", m)
        for m in re.finditer(r"<meta\b[^>]*name=[\"']?viewport[^>]*>", text, re.I):
            if re.search(r"user-scalable\s*=\s*(no|0)|maximum-scale\s*=\s*1(\.0)?\b", m.group(0), re.I):
                add("1.4.4", "viewport-blocks-zoom", m)
        for m in re.finditer(r"<select\b[^>]*(onchange|onChange|@change)\s*=[^>]*(submit|location)[^>]*>", text, re.I | re.S):
            add("3.2.2", "select-onchange-navigates", m)
    if ext in SCRIPT or ext in MARKUP:
        for m in re.finditer(r"\.key\s*===?\s*[\"'][a-zA-Z0-9?/]['\"]|keyCode\s*===?\s*(?:[4-8]\d|9[0])\b", text):
            add("2.1.4", "single-char-key-shortcut", m)
        for m in re.finditer(r"orientation\.lock\s*\(", text):
            add("1.3.4", "orientation-lock", m)
        for m in re.finditer(r"addEventListener\(\s*[\"']devicemotion", text):
            add("2.5.4", "device-motion-handler", m)
    if ext in STYLE or ext in MARKUP:
        for m in re.finditer(r"outline\s*:\s*(none|0)\b[^;}]*", text, re.I):
            add("2.4.7", "outline-removed (manual check: replacement focus style?)", m)
    return out


def manifests(root, name):
    found = [os.path.join(root, name)] + sorted(
        os.path.join(root, d, name) for d in os.listdir(root) if d not in EXCLUDED_DIRS and not d.startswith("."))
    return [p for p in found if os.path.isfile(p)][:3]


def detect_stack(root, exts):
    stack = []
    for pkg in manifests(root, "package.json"):
        try:
            data = json.load(open(pkg, encoding="utf-8"))
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            for key, label in (("next", "Next.js"), ("react", "React"), ("vue", "Vue"), ("nuxt", "Nuxt"),
                               ("@angular/core", "Angular"), ("svelte", "Svelte"), ("astro", "Astro")):
                if key in deps:
                    stack.append(f"{label} {deps[key]}")
        except (ValueError, OSError):
            stack.append("package.json (unparseable)")
    for comp in manifests(root, "composer.json"):
        txt = open(comp, encoding="utf-8", errors="replace").read()
        if "drupal/core" in txt:
            stack.append("Drupal")
        if "symfony/" in txt:
            stack.append("Symfony")
        if "laravel/" in txt:
            stack.append("Laravel")
    if exts.get(".twig"):
        stack.append("Twig templates")
    if not stack and (exts.get(".html") or exts.get(".htm")):
        stack.append("Plain HTML")
    return list(dict.fromkeys(stack)) or ["unknown (audit generically)"]


def git_meta(root):
    def run(*a):
        try:
            return subprocess.run(["git", "-C", root, *a], capture_output=True, text=True, timeout=10).stdout.strip() or "unknown"
        except (OSError, subprocess.SubprocessError):
            return "unknown"
    return {"commit": run("rev-parse", "HEAD"), "branch": run("rev-parse", "--abbrev-ref", "HEAD")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("--out")
    ap.add_argument("--max-files", type=int, default=20000)
    a = ap.parse_args()
    root = os.path.abspath(a.target)
    if not os.path.isdir(root):
        print(f"ERROR: target not a directory: {root}", file=sys.stderr)
        return 2

    files = {"markup": [], "script": [], "style": []}
    exts, skipped_sensitive, skipped_large, truncated = {}, 0, 0, False
    features = {k: {"count": 0, "files": [], "governs": v[1]} for k, v in FEATURES.items()}
    feat_re = {k: re.compile(v[0], re.I) for k, v in FEATURES.items()}
    leads, seen, markup_texts = [], 0, []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDED_DIRS and not d.startswith("."))
        rel_dir = os.path.relpath(dirpath, root)
        if THIRD_PARTY_PATH.search(rel_dir):
            dirnames[:] = []
            continue
        for fn in sorted(filenames):
            if SENSITIVE.search(fn):
                skipped_sensitive += 1
                continue
            if SKIP_NAME.search(fn):
                continue
            ext = os.path.splitext(fn)[1].lower()
            kind = "markup" if ext in MARKUP else "script" if ext in SCRIPT else "style" if ext in STYLE else None
            if not kind:
                continue
            if seen >= a.max_files:
                truncated = True
                break
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root)
            try:
                if os.path.getsize(full) > MAX_BYTES:
                    skipped_large += 1
                    continue
                text = open(full, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            seen += 1
            exts[ext] = exts.get(ext, 0) + 1
            files[kind].append(rel)
            for k, rx in feat_re.items():
                if rx.search(text):
                    features[k]["count"] += 1
                    if len(features[k]["files"]) < 10:
                        features[k]["files"].append(rel)
            leads.extend(lead_rules(rel, ext, text))
            if kind == "markup":
                markup_texts.append((rel, text))
        if truncated:
            break

    if seen == 0:
        print(f"ERROR: no auditable markup/script/style files under {root}", file=sys.stderr)
        return 2
    leads.extend(skip_link_leads(markup_texts))

    by_rule = {}
    for l in leads:
        by_rule.setdefault((l["sc_id"], l["rule"]), []).append(l)
    lead_groups = [{"sc_id": sc, "rule": rule, "total": len(v), "instances": v[:LEAD_CAP]}
                   for (sc, rule), v in sorted(by_rule.items())]
    inv = {
        "target": root,
        "scan_date": date.today().isoformat(),
        "git": git_meta(root),
        "stack": detect_stack(root, exts),
        "counts": {"files_scanned": seen, "by_extension": exts, "skipped_sensitive": skipped_sensitive,
                   "skipped_over_1MB": skipped_large, "truncated_at_max_files": truncated},
        "files": files,
        "features": features,
        "lead_groups": lead_groups,
        "note": "Leads are regex candidates, not findings. Confirm each in source before any FAIL.",
    }
    out = json.dumps(inv, indent=1)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(out)
        print(f"inventory: {a.out} | files={seen} leads={len(leads)} rules={len(lead_groups)} truncated={truncated}")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
