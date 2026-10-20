#!/usr/bin/env python3
"""Swift module graph for an iOS repository (read-only).

Reads every tracked Package.swift through `swift package dump-package` run on a
copy of the manifest in a temporary folder, so nothing is written to the repo.
Maps each target to its tracked source files and import statements, and reports:

- targets with type, files, lines, declared internal and external dependencies;
- imports of internal modules that the target does not declare (transitive leaks);
- declared internal dependencies that the target never imports;
- fan-in, fan-out, instability, and transitive dependency count per target;
- dependency cycles between internal targets, from imports;
- which internal modules each Xcode app or extension target links;
- source targets without a test target that depends on them.

Runs on Python 3.9, the version Xcode ships; run it with `xcrun python3`.

Usage: xcrun python3 swift_modules.py --repo <path> [--json]
"""

import argparse
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys

if sys.version_info < (3, 9):
    sys.exit("Needs Python 3.9 or newer. Run it with Xcode's Python: xcrun python3 " + sys.argv[0])
import tempfile
from collections import defaultdict

IMPORT_RE = re.compile(
    r"^\s*(?:@\w+(?:\([^)]*\))?\s+)*import\s+"
    r"(?:(?:struct|class|enum|protocol|typealias|func|var|let)\s+)?([A-Za-z_]\w*)"
)
SKIP_PARTS = {".build", "DerivedData", "checkouts", "Pods", "Carthage", "node_modules"}


def git_files(repo):
    out = subprocess.run(["git", "-C", repo, "ls-files"], capture_output=True, text=True, check=True).stdout
    return [f for f in out.splitlines() if not (set(f.split("/")) & SKIP_PARTS)]


def dump_package(manifest_path):
    tmp = tempfile.mkdtemp(prefix="swiftmod-")
    try:
        shutil.copy(manifest_path, os.path.join(tmp, "Package.swift"))
        res = subprocess.run(["swift", "package", "dump-package"], cwd=tmp, capture_output=True, text=True, timeout=300)
        if res.returncode != 0:
            return None, res.stderr.strip()[-500:]
        return json.loads(res.stdout), None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def dep_names(dep, target_names):
    kind, value = next(iter(dep.items()))
    if kind == "target" or (kind == "byName" and value[0] in target_names):
        return "internal", value[0]
    if kind in ("product", "byName"):
        return "external", value[0]
    return "other", str(value)


def package_of(dep):
    kind, value = next(iter(dep.items()))
    if kind == "product" and len(value) > 1 and value[1]:
        return value[1].lower()
    if kind == "byName":
        return value[0].lower()
    return None


def requirement(dep):
    kind, value = next(iter(dep.items()))
    info = value[0] if isinstance(value, list) else value
    ident = info.get("identity")
    req = info.get("requirement") or {}
    return ident, req


def version_tuple(v):
    parts = []
    for x in str(v).split("."):
        num = "".join(ch for ch in x if ch.isdigit())
        parts.append(int(num) if num else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def satisfies(version, req):
    if not version or not req:
        return None
    v = version_tuple(version)
    if "range" in req:
        r = req["range"][0]
        return version_tuple(r["lowerBound"]) <= v < version_tuple(r["upperBound"])
    if "exact" in req:
        return v == version_tuple(req["exact"][0])
    return None


def target_dir(pkg_dir, target):
    if target.get("path"):
        return os.path.normpath(os.path.join(pkg_dir, target["path"]))
    base = "Tests" if target["type"] == "test" else "Sources"
    if target["type"] == "plugin":
        base = "Plugins"
    return os.path.normpath(os.path.join(pkg_dir, base, target["name"]))


def find_cycles(graph):
    index, low, stack, on, sccs, counter = {}, {}, [], set(), [], [0]

    def visit(v):
        index[v] = low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        on.add(v)
        for w in graph.get(v, ()):
            if w not in index:
                visit(w)
                low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop()
                on.discard(w)
                comp.append(w)
                if w == v:
                    break
            if len(comp) > 1:
                sccs.append(sorted(comp))

    sys.setrecursionlimit(10000)
    for v in list(graph):
        if v not in index:
            visit(v)
    return sccs


def closure(graph, start):
    seen, todo = set(), list(graph.get(start, ()))
    while todo:
        n = todo.pop()
        if n not in seen:
            seen.add(n)
            todo.extend(graph.get(n, ()))
    return seen


def xcode_links(repo, files, internal_names):
    links = {}
    for pbx in [f for f in files if f.endswith("project.pbxproj")]:
        text = open(os.path.join(repo, pbx), encoding="utf-8", errors="replace").read()
        products = dict(re.findall(r"(\w{24}) /\* ([^*]+?) \*/ = \{\s*isa = XCSwiftPackageProductDependency;", text))
        for m in re.finditer(r"\w{24} /\* ([^*]+?) \*/ = \{\s*isa = PBXNativeTarget;(.*?)\n\t\t\};", text, re.S):
            name, body = m.group(1), m.group(2)
            block = re.search(r"packageProductDependencies = \((.*?)\);", body, re.S)
            ids = re.findall(r"(\w{24})", block.group(1)) if block else []
            linked = sorted({products[i] for i in ids if i in products})
            links[f"{pbx}: {name}"] = {
                "internal": [p for p in linked if p in internal_names],
                "external": [p for p in linked if p not in internal_names],
            }
    return links


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--layer", action="append", default=[],
                    help="name=pattern[,pattern] on target names, innermost layer first, e.g. domain=*Models,*Core")
    args = ap.parse_args()
    repo = os.path.abspath(args.repo)
    files = git_files(repo)
    manifests = [f for f in files if os.path.basename(f) == "Package.swift"]

    targets, errors, packages = {}, [], []
    for m in manifests:
        data, err = dump_package(os.path.join(repo, m))
        if err:
            errors.append({"manifest": m, "error": err})
            continue
        pkg_dir = os.path.dirname(m)
        packages.append({
            "manifest": m,
            "name": data.get("name"),
            "platforms": {p["platformName"]: p["version"] for p in data.get("platforms") or []},
            "products": [p["name"] for p in data.get("products", [])],
            "product_targets": {p["name"]: p.get("targets", []) for p in data.get("products", [])},
        })
        names_in_pkg = {t["name"] for t in data.get("targets", [])}
        used_packages = set()
        for t in data.get("targets", []):
            for d in t.get("dependencies", []):
                pk = package_of(d)
                if pk:
                    used_packages.add(pk)
            for u in t.get("pluginUsages") or []:
                kind, value = next(iter(u.items()))
                if kind == "plugin" and len(value) > 1 and value[1]:
                    used_packages.add(value[1].lower())
        declared_packages = {}
        for d in data.get("dependencies", []):
            ident, req = requirement(d)
            if ident:
                declared_packages[ident.lower()] = req
        packages[-1]["unused_packages"] = sorted(
            i for i in declared_packages
            if i not in used_packages and not any(i.replace("-", "") in u.replace("-", "") for u in used_packages)
        )
        packages[-1]["requirements"] = declared_packages
        for t in data.get("targets", []):
            deps = [dep_names(d, names_in_pkg) for d in t.get("dependencies", [])]
            tdir = target_dir(pkg_dir, t)
            prefix = tdir.rstrip("/") + "/"
            srcs = [f for f in files if f.startswith(prefix) and f.endswith(".swift")]
            imports = defaultdict(list)
            lines = 0
            for f in srcs:
                try:
                    content = open(os.path.join(repo, f), encoding="utf-8", errors="replace").read().splitlines()
                except OSError:
                    continue
                lines += len(content)
                for i, line in enumerate(content, 1):
                    mm = IMPORT_RE.match(line)
                    if mm:
                        imports[mm.group(1)].append(f"{f}:{i}")
            targets[t["name"]] = {
                "package": m,
                "type": t["type"],
                "dir": tdir,
                "files": len(srcs),
                "lines": lines,
                "declared_internal": sorted({n for k, n in deps if k == "internal"}),
                "declared_external": sorted({n for k, n in deps if k == "external"}),
                "imports": dict(imports),
            }

    internal = set(targets)
    product_names = {p for pk in packages for p in pk["products"]}
    local_products = {}
    for pk in packages:
        local_products.update(pk["product_targets"])
    # A product of another local package is an internal dependency on its targets.
    for t in targets.values():
        for prod in [d for d in t["declared_external"] if d in local_products]:
            t["declared_external"].remove(prod)
            t["declared_internal"] = sorted(set(t["declared_internal"]) | set(local_products[prod]))
    import_graph, declared_graph = {}, {}
    for name, t in targets.items():
        imported_internal = sorted(i for i in t["imports"] if i in internal and i != name)
        t["imported_internal"] = imported_internal
        t["undeclared_internal_imports"] = {
            i: t["imports"][i][:3] for i in imported_internal if i not in t["declared_internal"]
        }
        t["declared_not_imported"] = [
            d for d in t["declared_internal"] if d not in t["imports"] and targets.get(d, {}).get("type") not in ("plugin", "macro", "binary")
        ]
        if t["type"] != "test":
            import_graph[name] = imported_internal
            declared_graph[name] = [d for d in t["declared_internal"] if d in internal]

    fan_in = defaultdict(int)
    for name, deps in declared_graph.items():
        for d in deps:
            fan_in[d] += 1
    for name, t in targets.items():
        if t["type"] == "test":
            continue
        fo = len(declared_graph.get(name, []))
        fi = fan_in.get(name, 0)
        t["fan_in"], t["fan_out"] = fi, fo
        t["instability"] = round(fo / (fi + fo), 2) if fi + fo else None
        t["transitive_internal"] = len(closure(declared_graph, name))

    tested = set()
    for t in targets.values():
        if t["type"] == "test":
            tested.update(t["declared_internal"])
            tested.update(t.get("imported_internal", []))
    untested = sorted(n for n, t in targets.items() if t["type"] == "regular" and n not in tested)

    violations = []
    for r in [f for f in files if os.path.basename(f) == "Package.resolved"]:
        try:
            data = json.loads(open(os.path.join(repo, r), encoding="utf-8").read())
        except (OSError, json.JSONDecodeError):
            continue
        pins = data.get("pins") or data.get("object", {}).get("pins", [])
        resolved_versions = {(p.get("identity") or p.get("package", "")).lower(): p.get("state", {}).get("version") for p in pins}
        for pk in packages:
            for ident, req in pk["requirements"].items():
                ok = satisfies(resolved_versions.get(ident), req)
                if ok is False:
                    violations.append({"resolved": r, "manifest": pk["manifest"], "package": ident,
                                       "version": resolved_versions.get(ident), "requirement": req})

    layers = []
    for spec in args.layer:
        name, _, pats = spec.partition("=")
        layers.append((name, [x.strip() for x in pats.split(",") if x.strip()]))

    def layer_of(target):
        for i, (_, pats) in enumerate(layers):
            if any(fnmatch.fnmatch(target, pat) for pat in pats):
                return i
        return None

    wrong_direction = []
    if layers:
        for n, t in targets.items():
            ln = layer_of(n)
            if ln is None or t["type"] == "test":
                continue
            for mod in t.get("imported_internal", []):
                lm = layer_of(mod)
                if lm is not None and lm > ln:
                    wrong_direction.append({"from": n, "from_layer": layers[ln][0], "to": mod,
                                            "to_layer": layers[lm][0], "at": t["imports"][mod][:3]})
    unmapped = sorted(n for n, t in targets.items() if layers and t["type"] != "test" and layer_of(n) is None)

    result = {
        "layers": [l[0] for l in layers],
        "wrong_direction_imports": wrong_direction,
        "unmapped_targets": unmapped,
        "packages": packages,
        "resolved_outside_requirement": violations,
        "manifest_errors": errors,
        "targets": targets,
        "import_cycles": find_cycles(import_graph),
        "untested_targets": untested,
        "xcode_links": xcode_links(repo, files, internal | product_names),
    }

    if args.json:
        json.dump(result, sys.stdout, indent=2)
        return

    print(f"Packages: {len(packages)}  Targets: {len(targets)}  Manifest errors: {len(errors)}")
    for p in packages:
        print(f"  {p['manifest']}: {p['name']} platforms={p['platforms']}")
    for e in errors:
        print(f"  ERROR {e['manifest']}: {e['error']}")
    print("\nTargets (non-test) by transitive internal dependencies:")
    print(f"  {'target':40} {'type':9} {'files':>5} {'lines':>6} {'in':>3} {'out':>3} {'inst':>5} {'trans':>5}")
    rows = sorted((t for t in targets.items() if t[1]["type"] != "test"), key=lambda kv: -kv[1]["transitive_internal"])
    for n, t in rows:
        print(f"  {n:40} {t['type']:9} {t['files']:>5} {t['lines']:>6} {t['fan_in']:>3} {t['fan_out']:>3} {str(t['instability']):>5} {t['transitive_internal']:>5}")
    print("\nImport cycles between internal targets:", result["import_cycles"] or "none")
    def support(n, t):
        return t["type"] == "test" or re.search(r"Mock|Stub|Snapshot|Preview|Testing", n)

    print("\nImports of internal modules not declared as a direct dependency (production targets):")
    found = False
    for n, t in targets.items():
        if support(n, t):
            continue
        for mod, locs in t["undeclared_internal_imports"].items():
            found = True
            print(f"  {n} imports {mod}: {', '.join(locs)}")
    if not found:
        print("  none")
    support_count = sum(len(t["undeclared_internal_imports"]) for n, t in targets.items() if support(n, t))
    print(f"  plus {support_count} in test, mock, snapshot, and preview targets (see --json)")
    if layers:
        print("\nImports pointing outward (inner layer imports outer layer):")
        for w in wrong_direction or [None]:
            print("  none" if w is None else f"  {w['from']} ({w['from_layer']}) imports {w['to']} ({w['to_layer']}): {', '.join(w['at'])}")
        print("  targets in no layer:", ", ".join(unmapped) or "none")
    print("\nDeclared internal dependencies never imported (a hint: members of indirectly imported modules can be used without an import; confirm in code):")
    found = False
    for n, t in targets.items():
        if t["declared_not_imported"]:
            found = True
            print(f"  {n}: {', '.join(t['declared_not_imported'])}")
    if not found:
        print("  none")
    print("\nPackage dependencies no target uses:")
    for p in packages:
        if p["unused_packages"]:
            print(f"  {p['manifest']}: {', '.join(p['unused_packages'])}")
    print("\nPackage.resolved pins outside the manifest requirement:", "none" if not violations else "")
    for v in violations:
        print(f"  {v['resolved']}: {v['package']} {v['version']} vs {v['manifest']} {json.dumps(v['requirement'])}")
    print("\nSource targets without a test target that depends on them:", ", ".join(untested) or "none")
    print("\nXcode targets and linked package products:")
    for k, v in result["xcode_links"].items():
        print(f"  {k}: internal={v['internal']} external={v['external']}")


if __name__ == "__main__":
    main()
