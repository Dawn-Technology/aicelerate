#!/usr/bin/env python3
"""iOS platform and dependency health for a repository (read-only, offline).

Reports, from tracked files only:

- deployment targets per platform in Xcode projects and Package.swift files;
- Swift language version, strict concurrency, and swift-tools-version settings;
- package requirements pinned to a branch, a revision, or an exact version;
- every tracked Package.resolved, and pins that differ between them;
- availability code: #available, #unavailable, and @available counts per
  platform version, and the files with the most checks;
- the local Xcode version, for comparison with what the project requires.

It never fetches anything and never states support or end-of-life dates.

Runs on Python 3.9, the version Xcode ships; run it with `xcrun python3`.

Usage: xcrun python3 ios_platform.py --repo <path> [--json]
"""

import argparse
import json
import os
import re
import subprocess
import sys

if sys.version_info < (3, 9):
    sys.exit("Needs Python 3.9 or newer. Run it with Xcode's Python: xcrun python3 " + sys.argv[0])
from collections import Counter, defaultdict

SKIP_PARTS = {".build", "DerivedData", "checkouts", "Pods", "Carthage", "node_modules"}
SETTINGS = [
    "IPHONEOS_DEPLOYMENT_TARGET", "TVOS_DEPLOYMENT_TARGET", "WATCHOS_DEPLOYMENT_TARGET",
    "MACOSX_DEPLOYMENT_TARGET", "XROS_DEPLOYMENT_TARGET", "SWIFT_VERSION",
    "SWIFT_STRICT_CONCURRENCY", "SWIFT_APPROACHABLE_CONCURRENCY", "SWIFT_DEFAULT_ACTOR_ISOLATION",
    "SWIFT_UPCOMING_FEATURE_EXISTENTIAL_ANY",
]
AVAIL_RE = re.compile(r"(#available|#unavailable|@available)\s*\(([^)]*)\)")
PLATFORM_VER_RE = re.compile(r"\b(iOS|tvOS|watchOS|macOS|visionOS|macCatalyst)\s+(\d+(?:\.\d+)?)")


def git_files(repo):
    out = subprocess.run(["git", "-C", repo, "ls-files"], capture_output=True, text=True, check=True).stdout
    return [f for f in out.splitlines() if not (set(f.split("/")) & SKIP_PARTS)]


def read(repo, f):
    try:
        return open(os.path.join(repo, f), encoding="utf-8", errors="replace").read()
    except OSError:
        return ""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    repo = os.path.abspath(args.repo)
    files = git_files(repo)
    result = {}

    xcode = defaultdict(lambda: defaultdict(list))
    for pbx in [f for f in files if f.endswith("project.pbxproj")]:
        for i, line in enumerate(read(repo, pbx).splitlines(), 1):
            m = re.match(r"\s*(\w+) = \"?([^\";]+)\"?;", line)
            if m and m.group(1) in SETTINGS:
                xcode[m.group(1)][m.group(2)].append(f"{pbx}:{i}")
    per_target = {}
    for pbx in [f for f in files if f.endswith("project.pbxproj")]:
        text = read(repo, pbx)
        configs = {}
        for m in re.finditer(r"(\w{24}) /\* ([^*]+?) \*/ = \{\s*isa = XCBuildConfiguration;.*?buildSettings = \{(.*?)\n\t\t\t\};", text, re.S):
            vals = dict(re.findall(r"\n\s*(\w+) = \"?([^\";\n]+)\"?;", m.group(3)))
            configs[m.group(1)] = (m.group(2), {k: v for k, v in vals.items() if k in SETTINGS})
        lists = {m.group(1): re.findall(r"(\w{24})", m.group(2)) for m in re.finditer(r"(\w{24}) /\*[^*]*\*/ = \{\s*isa = XCConfigurationList;\s*buildConfigurations = \((.*?)\);", text, re.S)}
        project_defaults = {}
        pm = re.search(r"isa = PBXProject;.*?buildConfigurationList = (\w{24})", text, re.S)
        if pm:
            for cid in lists.get(pm.group(1), []):
                if cid in configs:
                    project_defaults.update(configs[cid][1])
        for m in re.finditer(r"\w{24} /\* ([^*]+?) \*/ = \{\s*isa = PBXNativeTarget;\s*buildConfigurationList = (\w{24})", text, re.S):
            merged = defaultdict(set)
            for cid in lists.get(m.group(2), []):
                if cid in configs:
                    effective = dict(project_defaults)
                    effective.update(configs[cid][1])
                    for k, v in effective.items():
                        merged[k].add(v)
            per_target[f"{pbx}: {m.group(1)}"] = {k: sorted(v) for k, v in merged.items()}
    result["xcode_targets"] = per_target
    result["xcode_settings"] = {k: {v: {"count": len(locs), "first": locs[:2]} for v, locs in vals.items()} for k, vals in xcode.items()}

    manifests = []
    pins = []
    for m in [f for f in files if os.path.basename(f) == "Package.swift"]:
        text = read(repo, m)
        tools = re.search(r"swift-tools-version:\s*([\d.]+)", text)
        langs = re.findall(r"swiftLanguageModes?:\s*\[([^\]]*)\]|swiftLanguageVersions?:\s*\[([^\]]*)\]", text)
        platforms = re.findall(r"\.(iOS|tvOS|watchOS|macOS|visionOS|macCatalyst)\(([^)]*)\)", text)
        settings = sorted(set(re.findall(r"\.(enableUpcomingFeature|enableExperimentalFeature|unsafeFlags|swiftLanguageMode)\(([^)]*)\)", text)))
        manifests.append({
            "manifest": m,
            "tools_version": tools.group(1) if tools else None,
            "language_modes": [a or b for a, b in langs],
            "platforms": [f"{p}({v})" for p, v in platforms],
            "swift_settings": [f"{k}({v})" for k, v in settings],
        })
        for mm in re.finditer(r"\.package\((.*?)\)\s*(?:,|\n|\])", text, re.S):
            body = " ".join(mm.group(1).split())
            url = re.search(r"url:\s*\"([^\"]+)\"", body)
            kind = None
            for k in ("branch", "revision", "exact"):
                if re.search(rf"\b{k}:", body) or re.search(rf"\.{k}\(", body):
                    kind = k
            pre = re.search(r"\"(\d+\.\d+\.\d+-[\w.]+)\"", body)
            if pre and not kind:
                kind = "pre-release " + pre.group(1)
            if kind:
                line = text[: mm.start()].count("\n") + 1
                pins.append({"location": f"{m}:{line}", "kind": kind, "url": url.group(1) if url else body[:120]})
    for pbx in [f for f in files if f.endswith("project.pbxproj")]:
        text = read(repo, pbx)
        for m in re.finditer(r"isa = XCRemoteSwiftPackageReference;\s*repositoryURL = \"?([^\";]+)\"?;\s*requirement = \{(.*?)\};", text, re.S):
            kind = re.search(r"kind = (\w+);", m.group(2))
            if kind and kind.group(1) in ("branch", "revision", "exactVersion"):
                line = text[: m.start()].count("\n") + 1
                pins.append({"location": f"{pbx}:{line}", "kind": kind.group(1), "url": m.group(1)})
    result["manifests"] = manifests
    result["pinned_requirements"] = pins

    resolved = {}
    for r in [f for f in files if os.path.basename(f) == "Package.resolved"]:
        try:
            data = json.loads(read(repo, r))
        except json.JSONDecodeError:
            continue
        entries = data.get("pins") or data.get("object", {}).get("pins", [])
        resolved[r] = {
            (p.get("identity") or p.get("package", "")).lower(): p.get("state", {}).get("version")
            or (("branch " + p["state"]["branch"]) if p.get("state", {}).get("branch") else None)
            or ("rev " + p.get("state", {}).get("revision", "")[:9])
            for p in entries
        }
    drift = {}
    if len(resolved) > 1:
        names = set().union(*[set(v) for v in resolved.values()])
        for n in sorted(names):
            vals = {r: pins_.get(n) for r, pins_ in resolved.items()}
            if len({v for v in vals.values() if v}) > 1:
                drift[n] = vals
    result["resolved_files"] = {r: len(v) for r, v in resolved.items()}
    result["resolved_drift"] = drift
    result["resolved_branch_pins"] = {r: {n: v for n, v in pins_.items() if v and v.startswith("branch")} for r, pins_ in resolved.items()}

    versions, per_file = Counter(), Counter()
    for f in [f for f in files if f.endswith(".swift")]:
        for m in AVAIL_RE.finditer(read(repo, f)):
            per_file[f] += 1
            for p, v in PLATFORM_VER_RE.findall(m.group(2)):
                versions[f"{p} {v}"] += 1
    result["availability"] = {
        "total": sum(per_file.values()),
        "by_platform_version": dict(versions.most_common()),
        "top_files": per_file.most_common(10),
    }

    xv = subprocess.run(["xcodebuild", "-version"], capture_output=True, text=True)
    result["local_xcode"] = xv.stdout.strip().replace("\n", " ") if xv.returncode == 0 else "not available"

    if args.json:
        json.dump(result, sys.stdout, indent=2)
        return

    print("Local Xcode:", result["local_xcode"])
    print("\nXcode build settings (value: count, first locations):")
    for k, vals in sorted(result["xcode_settings"].items()):
        print(f"  {k}: " + "; ".join(f"{v} x{d['count']} ({d['first'][0]})" for v, d in vals.items()))
    print("\nPer Xcode target (project defaults applied; several values mean configurations differ):")
    for t, vals in result["xcode_targets"].items():
        print(f"  {t}: " + ", ".join(f"{k.replace('_DEPLOYMENT_TARGET', '')}={'/'.join(v)}" for k, v in sorted(vals.items())))
    print("\nPackage manifests:")
    for m in manifests:
        print(f"  {m['manifest']}: tools {m['tools_version']}, platforms {m['platforms']}, language {m['language_modes'] or 'default'}, settings {m['swift_settings'] or 'none'}")
    print("\nRequirements pinned to a branch, revision, or exact version:")
    for p in pins or [{"location": "none", "kind": "", "url": ""}]:
        print(f"  {p['location']} {p['kind']} {p['url']}")
    print("\nPackage.resolved files:", result["resolved_files"] or "none")
    for r, b in result["resolved_branch_pins"].items():
        if b:
            print(f"  {r} branch pins: {b}")
    print("Pins that differ between Package.resolved files:", "none" if not drift else "")
    for n, vals in drift.items():
        print(f"  {n}: " + "; ".join(f"{r}={v}" for r, v in vals.items()))
    a = result["availability"]
    print(f"\nAvailability checks: {a['total']} total")
    print("  by platform version:", ", ".join(f"{k} x{v}" for k, v in a["by_platform_version"].items()) or "none")
    print("  top files:", ", ".join(f"{f} ({n})" for f, n in a["top_files"]) or "none")


if __name__ == "__main__":
    main()
