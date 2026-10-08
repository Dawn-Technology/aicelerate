#!/usr/bin/env python3
"""Check platform and dependency health from the package manager files.

Reports:
  - runtimes, frameworks and base images the repo declares (Node, PHP, Python,
    Go, .NET, Java, Ruby, Rails, Laravel, Symfony, Django, Spring Boot, React,
    Angular, Vue, Next.js, Postgres, Redis and more), with their end-of-life
    status from endoflife.date. Versions come from version files (.nvmrc,
    .tool-versions), manifests (engines, require.php, requires-python, go.mod,
    *.csproj, pom.xml), lockfiles, Dockerfiles, compose files and CI workflows;
  - packages the lockfile itself marks as deprecated (package-lock.json) or
    abandoned (composer.lock);
  - unpinned versions, packages locked in many versions, packages missing from
    the lockfile, and Dockerfile images without a version tag;
  - how long ago each manifest and lockfile last changed in git, how often they
    changed in the window, and whether Dependabot or Renovate is configured.

The end-of-life lookup is the only network use: one request per product to
endoflife.date, which carries nothing from the repo but the product name. Use
--offline to skip it; the versions are then listed with status "not checked".

Not covered: known vulnerabilities (use asvs-audit or the package manager's
audit command), and how far each package is behind its latest release.

Standard library only. Read-only.
"""

import argparse
import datetime
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections import Counter, defaultdict

sys.dont_write_bytecode = True  # do not leave a __pycache__ in the skill folder
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hotspots as hs  # noqa: E402  (shared git helper and folder filters)

EOL_BASE = "https://endoflife.date/api"
MAX_FILE_BYTES = 60_000_000
SOON_DAYS = 183

# How a Docker image name maps to an endoflife.date product.
IMAGE_PRODUCTS = {
    "node": "nodejs", "python": "python", "php": "php", "golang": "go", "ruby": "ruby",
    "eclipse-temurin": "eclipse-temurin", "openjdk": "eclipse-temurin",
    "aspnet": "dotnet", "sdk": "dotnet", "runtime": "dotnet",
    "postgres": "postgresql", "mysql": "mysql", "mariadb": "mariadb", "mongo": "mongodb",
    "redis": "redis", "nginx": "nginx", "alpine": "alpine-linux", "ubuntu": "ubuntu",
    "debian": "debian", "elasticsearch": "elasticsearch",
}
# `<setup action> -version:` keys in CI workflows.
CI_VERSION_KEYS = {"node": "nodejs", "python": "python", "php": "php", "go": "go",
                   "ruby": "ruby", "java": "eclipse-temurin", "dotnet": "dotnet"}
TOOL_VERSIONS = {"nodejs": "nodejs", "node": "nodejs", "python": "python", "ruby": "ruby",
                 "golang": "go", "php": "php", "java": "eclipse-temurin"}
NPM_FRAMEWORKS = {"react": "react", "next": "nextjs", "vue": "vue", "@angular/core": "angular",
                  "nuxt": "nuxt", "express": "express"}
COMPOSER_FRAMEWORKS = {"laravel/framework": "laravel", "symfony/symfony": "symfony",
                       "symfony/framework-bundle": "symfony", "drupal/core": "drupal"}
UNPINNED_NPM = re.compile(r"^(\*|latest|next|x|)$|^(git\+|github:|file:|link:|https?:)")


def line_of(text, needle, start=0):
    i = text.find(needle, start)
    return text.count("\n", 0, i) + 1 if i >= 0 else 1


def floor_version(constraint):
    """The lowest version a constraint such as '>=7.4 <8.2' or '^20 || ^22' allows."""
    nums = re.findall(r"\d+(?:\.\d+)*", constraint or "")
    return min(nums, key=lambda n: tuple(int(x) for x in n.split("."))) if nums else None


def first_version(text):
    m = re.search(r"(\d+(?:\.\d+)*)", text or "")
    return m.group(1) if m else None


def image_component(ref):
    """(product, version) for a Docker image reference such as node:20-alpine."""
    ref = ref.strip().strip("'\"")
    if not ref or ref.startswith("$") or ":" not in ref.rsplit("/", 1)[-1]:
        return None, None
    name, tag = ref.rsplit(":", 1)
    last = name.rsplit("/", 1)[-1]
    if "microsoft.com/dotnet" in name and last in ("aspnet", "sdk", "runtime"):
        product = "dotnet"
    else:
        product = IMAGE_PRODUCTS.get(last) if last not in ("sdk", "runtime", "aspnet") else None
    m = re.match(r"v?(\d+(?:\.\d+)*)", tag)
    return (product, m.group(1)) if product and m else (None, None)


# --- finding components ------------------------------------------------------


class Collector:
    def __init__(self):
        self.items = defaultdict(list)  # (product, version, how) -> [(file, line)]

    def add(self, product, version, path, line, how):
        if product and version:
            self.items[(product, version, how)].append((path, line))


def read(root, path):
    full = os.path.join(root, path)
    try:
        if os.path.getsize(full) > MAX_FILE_BYTES:
            return None
        with open(full, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return None


def read_json(root, path):
    text = read(root, path)
    try:
        return json.loads(text) if text else None
    except ValueError:
        return None


def collect(root, files, col):
    """Fill the collector, and return package file facts for the health table."""
    package_files = []
    for path in files:
        base = os.path.basename(path)
        low = base.lower()
        if base in (".nvmrc", ".node-version", ".python-version", ".ruby-version", ".php-version"):
            product = {".nvmrc": "nodejs", ".node-version": "nodejs", ".python-version": "python",
                       ".ruby-version": "ruby", ".php-version": "php"}[base]
            text = read(root, path) or ""
            col.add(product, first_version(text), path, 1, "pinned")
        elif base == ".tool-versions":
            for n, line in enumerate((read(root, path) or "").splitlines(), 1):
                parts = line.split()
                if len(parts) >= 2 and parts[0] in TOOL_VERSIONS:
                    col.add(TOOL_VERSIONS[parts[0]], first_version(parts[1]), path, n, "pinned")
        elif base == "package.json":
            data = read_json(root, path)
            text = read(root, path) or ""
            if isinstance(data, dict):
                engines = data.get("engines") or {}
                if isinstance(engines.get("node"), str):
                    col.add("nodejs", floor_version(engines["node"]), path,
                            line_of(text, '"node"', line_of_offset(text, '"engines"')), "minimum")
                volta = data.get("volta") or {}
                if isinstance(volta.get("node"), str):
                    col.add("nodejs", first_version(volta["node"]), path,
                            line_of(text, '"volta"'), "pinned")
                package_files.append(("npm", path, data))
        elif base == "composer.json":
            data = read_json(root, path)
            if isinstance(data, dict):
                php = (data.get("require") or {}).get("php")
                text = read(root, path) or ""
                if isinstance(php, str):
                    col.add("php", floor_version(php), path, line_of(text, '"php"'), "minimum")
                package_files.append(("composer", path, data))
        elif base == "pyproject.toml":
            text = read(root, path) or ""
            m = re.search(r"(?m)^\s*requires-python\s*=\s*[\"']([^\"']+)", text) or \
                re.search(r"(?m)^\s*python\s*=\s*[\"']([^\"']+)", text)
            if m:
                col.add("python", floor_version(m.group(1)), path,
                        text.count("\n", 0, m.start()) + 1, "minimum")
            m = re.search(r"(?mi)[\"']django\s*(?:[<>=~!]+\s*([\d.]+))", text)
            if m:
                col.add("django", first_version(m.group(1)), path,
                        text.count("\n", 0, m.start()) + 1, "minimum")
            package_files.append(("python", path, text))
        elif low.startswith("requirements") and low.endswith(".txt"):
            text = read(root, path) or ""
            for n, line in enumerate(text.splitlines(), 1):
                m = re.match(r"(?i)\s*django\s*(?:==|>=|~=|>)\s*([\d.]+)", line)
                if m:
                    col.add("django", first_version(m.group(1)), path, n,
                            "pinned" if "==" in line else "minimum")
            package_files.append(("python", path, text))
        elif base == "poetry.lock":
            text = read(root, path) or ""
            m = re.search(r'(?m)^name = "django"\nversion = "([\d.]+)"', text)
            if m:
                col.add("django", first_version(m.group(1)), path,
                        text.count("\n", 0, m.start()) + 1, "locked")
        elif base == "go.mod":
            text = read(root, path) or ""
            m = re.search(r"(?m)^go\s+(\d+\.\d+)", text)
            if m:
                col.add("go", m.group(1), path, text.count("\n", 0, m.start()) + 1, "minimum")
            package_files.append(("go", path, text))
        elif low.endswith(".csproj") or base == "Directory.Build.props":
            text = read(root, path) or ""
            for m in re.finditer(r"<TargetFrameworks?>([^<]+)<", text):
                for tfm in m.group(1).split(";"):
                    v = re.match(r"net(\d+\.\d+)$", tfm.strip()) or \
                        re.match(r"netcoreapp(\d+\.\d+)$", tfm.strip())
                    if v:
                        col.add("dotnet", v.group(1), path, text.count("\n", 0, m.start()) + 1, "pinned")
            if low.endswith(".csproj"):
                package_files.append(("dotnet", path, text))
        elif base == "pom.xml":
            text = read(root, path) or ""
            for rx in (r"<java\.version>(\d+(?:\.\d+)?)<", r"<maven\.compiler\.release>(\d+)<",
                       r"<maven\.compiler\.source>(\d+(?:\.\d+)?)<"):
                m = re.search(rx, text)
                if m:
                    col.add("eclipse-temurin", m.group(1), path, text.count("\n", 0, m.start()) + 1, "pinned")
                    break
            m = re.search(r"spring-boot-starter-parent</artifactId>\s*<version>([\d.]+)", text)
            if m:
                col.add("spring-boot", m.group(1), path, text.count("\n", 0, m.start()) + 1, "pinned")
        elif base in ("build.gradle", "build.gradle.kts"):
            text = read(root, path) or ""
            m = re.search(r"org\.springframework\.boot['\"]?\)?\s+version\s+['\"]([\d.]+)", text)
            if m:
                col.add("spring-boot", m.group(1), path, text.count("\n", 0, m.start()) + 1, "pinned")
            m = re.search(r"JavaVersion\.VERSION_(\d+)|sourceCompatibility\s*=\s*['\"]?(\d+)|"
                          r"jvmToolchain\((\d+)\)", text)
            if m:
                v = next(g for g in m.groups() if g)
                col.add("eclipse-temurin", v, path, text.count("\n", 0, m.start()) + 1, "pinned")
        elif base == "Gemfile.lock":
            text = read(root, path) or ""
            m = re.search(r"(?m)^    rails \((\d+\.\d+(?:\.\d+)?)\)", text)
            if m:
                col.add("rails", m.group(1), path, text.count("\n", 0, m.start()) + 1, "locked")
            m = re.search(r"(?m)^RUBY VERSION\n\s+ruby (\d+\.\d+(?:\.\d+)?)", text)
            if m:
                col.add("ruby", m.group(1), path, text.count("\n", 0, m.start()) + 1, "pinned")
        elif low.startswith("dockerfile") or low.endswith(".dockerfile"):
            stages = set()
            for n, line in enumerate((read(root, path) or "").splitlines(), 1):
                m = re.match(r"(?i)\s*FROM\s+(?:--platform=\S+\s+)?(\S+)(?:\s+AS\s+(\S+))?", line)
                if not m:
                    continue
                ref, alias = m.group(1), m.group(2)
                if ref not in stages:
                    product, version = image_component(ref)
                    col.add(product, version, path, n, "pinned")
                    tag = ref.rsplit("/", 1)[-1].partition(":")[2]
                    if (not tag or tag == "latest") and not ref.startswith("$") and ref != "scratch":
                        col.items[("unpinned image", ref, "")].append((path, n))
                if alias:
                    stages.add(alias)
        elif re.match(r"(docker-)?compose.*\.ya?ml$", low) or base == ".gitlab-ci.yml":
            for n, line in enumerate((read(root, path) or "").splitlines(), 1):
                m = re.match(r"\s*(?:-\s*)?(?:image|name):\s*(\S+)", line)
                if m:
                    product, version = image_component(m.group(1))
                    col.add(product, version, path, n, "pinned")
        elif path.startswith(".github/workflows/") and low.endswith((".yml", ".yaml")):
            for n, line in enumerate((read(root, path) or "").splitlines(), 1):
                m = re.match(r"\s*-?\s*(node|python|php|go|ruby|java|dotnet)-version:\s*(.+)", line)
                if m:
                    for v in re.findall(r"\d+(?:\.\d+)?", m.group(2)):
                        col.add(CI_VERSION_KEYS[m.group(1)], v, path, n, "pinned (CI)")
    return package_files


def line_of_offset(text, needle):
    i = text.find(needle)
    return max(i, 0)


# --- package health ----------------------------------------------------------


def lock_near(files, manifest, names):
    """The nearest lockfile with one of these names, in this folder or above it."""
    folder = os.path.dirname(manifest)
    while True:
        for name in names:
            cand = f"{folder}/{name}" if folder else name
            if cand in files:
                return cand
        if not folder:
            return None
        folder = os.path.dirname(folder)


def npm_health(root, files, manifest, data, col):
    deps = data.get("dependencies") or {}
    dev = data.get("devDependencies") or {}
    row = {"ecosystem": "npm", "manifest": manifest, "direct": len(deps), "dev": len(dev),
           "lock": None, "locked": None, "deprecated": [], "multi_version": [],
           "unpinned": [f"{n}@{v}" for n, v in {**deps, **dev}.items()
                        if isinstance(v, str) and UNPINNED_NPM.search(v)],
           "missing_from_lock": [], "notes": []}
    lock = lock_near(files, manifest, ("package-lock.json", "npm-shrinkwrap.json"))
    other = lock_near(files, manifest, ("yarn.lock", "pnpm-lock.yaml", "bun.lockb", "bun.lock"))
    if lock:
        row["lock"] = lock
        ldata = read_json(root, lock)
        packages = ldata.get("packages") if isinstance(ldata, dict) else None
        if isinstance(packages, dict):
            row["locked"] = max(len(packages) - 1, 0)
            versions = defaultdict(set)
            direct = set(deps) | set(dev)
            for key, info in packages.items():
                if not key or not isinstance(info, dict) or info.get("link"):
                    continue
                name = key.rsplit("node_modules/", 1)[-1]
                versions[name].add(info.get("version"))
                if info.get("deprecated"):
                    row["deprecated"].append({
                        "name": name, "version": info.get("version"),
                        "direct": key == f"node_modules/{name}" and name in direct,
                        "message": str(info["deprecated"])[:140]})
                if name in NPM_FRAMEWORKS and key == f"node_modules/{name}":
                    col.add(NPM_FRAMEWORKS[name], first_version(info.get("version")), lock,
                            1, "locked")
            row["multi_version"] = sorted(
                ((n, len(v)) for n, v in versions.items() if len(v) >= 3), key=lambda x: -x[1])[:5]
            row["missing_from_lock"] = [n for n in direct if n not in versions]
        else:
            row["notes"].append("lockfile is an old format (v1); deprecated flags are not available")
    elif other:
        row["lock"] = other
        row["notes"].append("yarn, pnpm or bun lockfile: deprecated flags and duplicate versions "
                            "are not read")
    else:
        row["notes"].append("no lockfile found")
    if not lock:
        for name, constraint in {**deps, **dev}.items():
            if name in NPM_FRAMEWORKS and isinstance(constraint, str):
                col.add(NPM_FRAMEWORKS[name], floor_version(constraint), manifest, 1, "minimum")
    return row


def composer_health(root, files, manifest, data, col):
    require, dev = data.get("require") or {}, data.get("require-dev") or {}
    row = {"ecosystem": "composer", "manifest": manifest,
           "direct": len([k for k in require if k != "php" and not k.startswith("ext-")]),
           "dev": len(dev), "lock": None, "locked": None, "deprecated": [], "multi_version": [],
           "unpinned": [f"{n}@{v}" for n, v in {**require, **dev}.items()
                        if isinstance(v, str) and (v.strip() in ("*", "dev-master", "dev-main")
                                                   or v.startswith("dev-") or "@dev" in v)],
           "missing_from_lock": [], "notes": []}
    lock = f"{os.path.dirname(manifest)}/composer.lock".lstrip("/")
    if lock in files:
        row["lock"] = lock
        ldata = read_json(root, lock)
        if isinstance(ldata, dict):
            pkgs = (ldata.get("packages") or []) + (ldata.get("packages-dev") or [])
            row["locked"] = len(pkgs)
            direct = set(require) | set(dev)
            for p in pkgs:
                if p.get("abandoned"):
                    replacement = p["abandoned"] if isinstance(p["abandoned"], str) else None
                    row["deprecated"].append({
                        "name": p.get("name"), "version": p.get("version"),
                        "direct": p.get("name") in direct, "abandoned": True,
                        "message": f"abandoned, use {replacement}" if replacement else "abandoned"})
                if p.get("name") in COMPOSER_FRAMEWORKS:
                    col.add(COMPOSER_FRAMEWORKS[p["name"]], first_version(p.get("version")),
                            lock, 1, "locked")
    else:
        row["notes"].append("no composer.lock found")
        for name, constraint in {**require, **dev}.items():
            if name in COMPOSER_FRAMEWORKS and isinstance(constraint, str):
                col.add(COMPOSER_FRAMEWORKS[name], floor_version(constraint), manifest, 1, "minimum")
    return row


def python_health(path, text):
    reqs = [ln.strip() for ln in text.splitlines()
            if ln.strip() and not ln.strip().startswith(("#", "-"))] if \
        os.path.basename(path).lower().startswith("requirements") else []
    return {"ecosystem": "python", "manifest": path,
            "direct": len(reqs) if reqs else None, "dev": None, "lock": None, "locked": None,
            "deprecated": [], "multi_version": [],
            "unpinned": [r for r in reqs if "==" not in r and "@" not in r][:20],
            "missing_from_lock": [], "notes": []}


def go_health(path, text):
    reqs = re.findall(r"(?m)^\s*(?:require\s+)?([\w./~-]+)\s+v[\w.+-]+(\s*//\s*indirect)?\s*$", text)
    return {"ecosystem": "go", "manifest": path,
            "direct": sum(1 for _, ind in reqs if not ind), "dev": None, "lock": None,
            "locked": len(reqs), "deprecated": [], "multi_version": [], "unpinned": [],
            "missing_from_lock": [],
            "notes": [f"{len(re.findall(r'(?m)^replace\\b', text))} replace directives"]
            if re.search(r"(?m)^replace\b", text) else []}


def dotnet_health(path, text):
    refs = re.findall(r"<PackageReference\b[^>]*>", text)
    return {"ecosystem": "dotnet", "manifest": path, "direct": len(refs), "dev": None,
            "lock": None, "locked": None, "deprecated": [], "multi_version": [],
            "unpinned": [r for r in refs if re.search(r'Version="[^"]*\*', r)][:20],
            "missing_from_lock": [], "notes": []}


# --- git age -----------------------------------------------------------------


def git_age(repo, scope_files, since, head_date):
    """Last change and change count in the window for each manifest and lockfile."""
    out = {}
    for path in scope_files:
        last = hs.git(repo, "log", "-1", "--format=%cs", "HEAD", "--", path, check=False).strip()
        count = len(hs.git(repo, "log", f"--since={since}", "--format=%h", "HEAD", "--", path,
                           check=False).split())
        months = None
        if last:
            a, b = datetime.date.fromisoformat(last), datetime.date.fromisoformat(head_date)
            months = (b.year - a.year) * 12 + b.month - a.month
        out[path] = {"last_changed": last or None, "months_before_head": months,
                     "changes_in_window": count}
    return out


# --- end of life -------------------------------------------------------------


class EolData:
    def __init__(self, base, offline):
        self.base, self.offline, self.cache, self.errors = base.rstrip("/"), offline, {}, {}

    def cycles(self, slug):
        if self.offline:
            return None
        if slug not in self.cache:
            try:
                req = urllib.request.Request(f"{self.base}/{slug}.json",
                                             headers={"User-Agent": "aimate-review-architecture"})
                with urllib.request.urlopen(req, timeout=8) as resp:
                    self.cache[slug] = json.load(resp)
            except (urllib.error.URLError, OSError, ValueError) as exc:
                self.cache[slug] = None
                self.errors[slug] = str(getattr(exc, "reason", exc))[:80]
        return self.cache[slug]

    def status(self, slug, version, today):
        cycles = self.cycles(slug)
        if cycles is None:
            why = "offline" if self.offline else f"lookup failed ({self.errors.get(slug, 'unknown')})"
            return {"state": "not_checked", "text": f"not checked ({why})", "eol": None}
        parts = version.split(".")
        for n in range(min(3, len(parts)), 0, -1):
            cycle = ".".join(parts[:n])
            hit = next((c for c in cycles if str(c.get("cycle")) == cycle), None)
            if hit:
                break
        else:
            coarse = any(str(c.get("cycle")).startswith(version + ".") for c in cycles)
            return {"state": "unknown", "eol": None, "text": (
                "version too coarse to pick a release line (needs a minor version)" if coarse
                else "release line not in endoflife.date data")}
        eol = hit.get("eol")
        if eol is True:
            return {"state": "eol", "text": "end of life", "eol": None, "months_past": None}
        if not eol:
            return {"state": "open", "text": "no end date set", "eol": None}
        end = datetime.date.fromisoformat(eol)
        months = (today.year - end.year) * 12 + today.month - end.month
        if end <= today:
            return {"state": "eol", "text": f"end of life since {eol} ({months} months ago)",
                    "eol": eol, "months_past": months}
        if (end - today).days <= SOON_DAYS:
            return {"state": "soon", "text": f"ends {eol}", "eol": eol, "months_past": None}
        return {"state": "ok", "text": f"supported until {eol}", "eol": eol, "months_past": None}


# --- main --------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".", help="repository path, or a folder inside one")
    ap.add_argument("--path", default="", help="report only on this subdirectory")
    ap.add_argument("--months", type=int, default=12,
                    help="window for counting manifest changes (default 12)")
    ap.add_argument("--offline", action="store_true",
                    help="do not call endoflife.date; end-of-life status is 'not checked'")
    ap.add_argument("--eol-base", default=EOL_BASE,
                    help=f"base URL of the end-of-life data (default {EOL_BASE}); "
                         "a file:// folder of <product>.json files works for tests")
    ap.add_argument("--today", default="",
                    help="treat this date (YYYY-MM-DD) as today; default is the real date")
    ap.add_argument("--json", action="store_true", help="print JSON instead of markdown")
    args = ap.parse_args()

    today = datetime.date.fromisoformat(args.today) if args.today else datetime.date.today()
    start = os.path.abspath(args.repo)
    if not os.path.isdir(start):
        print(f"error: {start} is not a directory", file=sys.stderr)
        return 2
    in_git = True
    try:
        root = hs.git(start, "rev-parse", "--show-toplevel").strip()
        prefix = hs.git(start, "rev-parse", "--show-prefix").strip().rstrip("/")
        listed = hs.git(root, "ls-files").splitlines()
    except (RuntimeError, FileNotFoundError):
        in_git, root, prefix = False, start, ""
        listed = [os.path.relpath(os.path.join(d, f), root).replace(os.sep, "/")
                  for d, _, fs in os.walk(root) for f in fs]
    scope = "/".join(x for x in (prefix, args.path.strip("/")) if x)

    def wanted(p):
        if scope and not (p == scope or p.startswith(scope + "/")):
            return False
        dirs = p.split("/")[:-1]
        return not any(d.lower() in hs.SAFE_EXCLUDED_DIRS or hs.TEST_DIR_NAME.fullmatch(d)
                       for d in dirs)

    files = [p for p in listed if wanted(p)]
    col = Collector()
    package_files = collect(root, files, col)
    fileset = set(listed)

    health = []
    for eco, path, data in package_files:
        if eco == "npm":
            health.append(npm_health(root, fileset, path, data, col))
        elif eco == "composer":
            health.append(composer_health(root, fileset, path, data, col))
        elif eco == "python":
            health.append(python_health(path, data))
        elif eco == "go":
            health.append(go_health(path, data))
        elif eco == "dotnet":
            health.append(dotnet_health(path, data))

    eol = EolData(args.eol_base, args.offline)
    components = []
    for (product, version, how), sources in sorted(col.items.items()):
        if product == "unpinned image":
            continue
        st = eol.status(product, version, today)
        components.append({"product": product, "version": version, "declared": how,
                           "sources": [f"{f}:{n}" for f, n in sources], **st})
    order = {"eol": 0, "soon": 1, "unknown": 2, "not_checked": 3, "open": 4, "ok": 5}
    components.sort(key=lambda c: (order[c["state"]], -(c.get("months_past") or 0), c["product"]))
    unpinned_images = [{"image": img, "sources": [f"{f}:{n}" for f, n in src]}
                       for (kind, img, _), src in col.items.items() if kind == "unpinned image"]

    manifest_paths = sorted({h["manifest"] for h in health} |
                            {h["lock"] for h in health if h["lock"]})
    age, head_date, since = {}, None, None
    if in_git and hs.git(root, "rev-parse", "--verify", "-q", "HEAD", check=False).strip():
        head_date = hs.git(root, "log", "-1", "--format=%cs", "HEAD").strip()
        y, m, _ = (int(x) for x in head_date.split("-"))
        m -= args.months
        while m <= 0:
            m += 12
            y -= 1
        since = f"{y:04d}-{m:02d}-01"
        age = git_age(root, manifest_paths, since, head_date)
    automation = [p for p in files if re.search(
        r"(^|/)(renovate\.json5?|\.renovaterc(\.json5?)?|dependabot\.ya?ml)$", p)]

    result = {
        "meta": {"repo": root, "scope": scope or None, "today": today.isoformat(),
                 "eol_source": "not checked (offline)" if args.offline else eol.base,
                 "eol_lookup_errors": eol.errors, "head_date": head_date,
                 "window_since": since},
        "components": components, "unpinned_images": unpinned_images,
        "package_files": [{**h, "age": age.get(h["manifest"]),
                           "lock_age": age.get(h["lock"]) if h["lock"] else None}
                          for h in health],
        "update_automation": automation,
    }
    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    print(f"# Platform and dependency health for {os.path.basename(root)}\n")
    src = ("not checked (--offline)" if args.offline else eol.base.replace("https://", ""))
    print(f"Date used as today: {today}. End-of-life data: {src}"
          + (f", scope `{scope}`" if scope else "") + ".")
    if eol.errors:
        print("WARNING: end-of-life lookup failed for: "
              + ", ".join(f"{k} ({v})" for k, v in eol.errors.items())
              + ". Do not fill those dates in from memory.")
    print("\n## Runtimes, frameworks and images\n")
    if not components:
        print("None found in version files, manifests, Dockerfiles, compose files or CI workflows.")
    else:
        print("A version declared as `minimum` is the lowest the manifest allows, not what runs.\n")
        print("| Component | Version | Declared | Where | End of life |")
        print("|---|---|---|---|---|")
        for c in components:
            where = ", ".join(f"`{s}`" for s in c["sources"][:3])
            if len(c["sources"]) > 3:
                where += f" and {len(c['sources']) - 3} more"
            print(f"| {c['product']} | {c['version']} | {c['declared']} | {where} | {c['text']} |")
    if unpinned_images:
        print("\nImages without a version tag (they float to whatever is latest): "
              + ", ".join(f"`{u['image']}` ({u['sources'][0]})" for u in unpinned_images[:6]) + ".")

    print("\n## Package files\n")
    if not health:
        print("No package manifest found.")
    else:
        print("| Manifest | Type | Direct | Dev | Locked | Lockfile | Lockfile last changed | "
              "Manifest changes in window |")
        print("|---|---|---|---|---|---|---|---|")
        for h in health:
            la = age.get(h["lock"]) if h["lock"] else None
            ma = age.get(h["manifest"])
            last = (f"{la['last_changed']} ({la['months_before_head']} months before HEAD)"
                    if la and la["last_changed"] else "n/a")
            cnt = (ma or {}).get("changes_in_window", "n/a")
            print(f"| `{h['manifest']}` | {h['ecosystem']} | {h['direct'] if h['direct'] is not None else 'n/a'} | "
                  f"{h['dev'] if h['dev'] is not None else 'n/a'} | "
                  f"{h['locked'] if h['locked'] is not None else 'n/a'} | "
                  f"{'`' + h['lock'] + '`' if h['lock'] else 'none'} | {last} | {cnt} |")
    print("\nUpdate automation: "
          + (", ".join(f"`{a}`" for a in automation) if automation else
             "no Dependabot or Renovate config found") + ".")

    flagged = [(h, d) for h in health for d in h["deprecated"]]
    print("\n## Deprecated or abandoned packages\n")
    if not flagged:
        print("None flagged by the lockfiles that carry the information (package-lock.json, "
              "composer.lock).")
    else:
        print("| Package | Version | Direct | Lockfile says | In |")
        print("|---|---|---|---|---|")
        for h, d in sorted(flagged, key=lambda x: (not x[1]["direct"], x[1]["name"] or ""))[:25]:
            print(f"| {d['name']} | {d['version']} | {'yes' if d['direct'] else 'no (transitive)'} | "
                  f"{d['message']} | `{h['manifest']}` |")
        if len(flagged) > 25:
            print(f"\nand {len(flagged) - 25} more; all are in the --json output.")

    notes = []
    for h in health:
        if h["unpinned"]:
            notes.append(f"`{h['manifest']}`: {len(h['unpinned'])} unpinned or non-registry versions "
                         f"(for example {', '.join(h['unpinned'][:3])})")
        if h["multi_version"]:
            notes.append(f"`{h['manifest']}`: locked in 3 or more versions: "
                         + ", ".join(f"{n} ({c})" for n, c in h["multi_version"]))
        if h["missing_from_lock"]:
            notes.append(f"`{h['manifest']}`: declared but missing from the lockfile (out of "
                         f"sync): {', '.join(h['missing_from_lock'][:5])}")
        notes += [f"`{h['manifest']}`: {n}" for n in h["notes"]]
    print("\n## Other signals\n")
    print("\n".join(f"- {n}" for n in notes) if notes else "None.")
    print("\n## Not checked\n")
    print("Known vulnerabilities, and how far each package is behind its latest release. "
          "Maven and Gradle dependencies are read for the Java and Spring Boot versions only.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
