#!/usr/bin/env python3
"""Check how a codebase's modules depend on each other, from its import lines.

Reports:
  - coverage: how many imports it could match to a file in the repo, per
    language, so a "no cycles" result can be judged;
  - per module: fan-in, fan-out, instability, and how many of its files other
    modules import;
  - dependency cycles between modules, with the import lines that form them;
  - with --layer: imports that point the wrong way (domain -> application or
    infrastructure, application -> infrastructure);
  - with a domain layer: imports of ORM, framework, HTTP, queue, config, logging
    and UI libraries, and hidden dependencies (clock, random, env reads, static
    facades, persistence annotations, infrastructure exceptions), each with
    file:line.

Reads Python, JavaScript/TypeScript, Java/Kotlin/Scala/Groovy, PHP, C# and Go.
Other languages are counted and listed as not covered. Standard library only.
Read-only. Files are read from the working tree, so line numbers match what a
reviewer opens.
"""

import argparse
import bisect
import fnmatch
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.dont_write_bytecode = True  # do not leave a __pycache__ in the skill folder
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hotspots as hs  # noqa: E402  (shared file filters and module grouping)

LANGUAGES = {
    "py": "python",
    **dict.fromkeys(("js", "jsx", "ts", "tsx", "mjs", "cjs", "vue", "svelte"), "javascript"),
    **dict.fromkeys(("java", "kt", "kts", "scala", "groovy"), "jvm"),
    "php": "php",
    "cs": "csharp",
    "go": "go",
}
LAYER_RANK = {"domain": 0, "application": 1, "infrastructure": 2}
MAX_FILE_BYTES = 1_500_000

# --- reading imports ---------------------------------------------------------

JS_FROM = re.compile(r"""\b(?:import|export)\b[^'"`;]*?\bfrom\s*['"]([^'"\n]+)['"]""")
JS_SIDE_EFFECT = re.compile(r"""(?m)^\s*import\s*['"]([^'"\n]+)['"]""")
JS_CALL = re.compile(r"""\b(?:require|import)\(\s*['"]([^'"\n]+)['"]\s*\)""")
PY_FROM = re.compile(r"^[ \t]*from[ \t]+(\.*)([\w.]*)[ \t]+import[ \t]+(.+)$", re.M)
PY_IMPORT = re.compile(r"^[ \t]*import[ \t]+(.+)$", re.M)
JVM_PACKAGE = re.compile(r"^\s*package\s+([\w.]+)", re.M)
JVM_IMPORT = re.compile(r"^\s*import\s+(?:static\s+)?([\w.]+?)(\.\*)?(?:\s+as\s+\w+)?\s*;?\s*$", re.M)
PHP_NAMESPACE = re.compile(r"^\s*namespace\s+([\w\\]+)\s*[;{]", re.M)
PHP_USE = re.compile(r"^use\s+(?:function\s+|const\s+)?([\w\\]+?)(?:\s+as\s+\w+)?\s*;", re.M)
PHP_USE_GROUP = re.compile(r"^use\s+(?:function\s+|const\s+)?([\w\\]+)\\\{([^}]*)\}\s*;", re.M)
CS_NAMESPACE = re.compile(r"^\s*namespace\s+([\w.]+)\s*[;{]?", re.M)
CS_USING = re.compile(r"^\s*(?:global\s+)?using\s+(?:static\s+)?(?:\w+\s*=\s*)?([\w.]+)\s*;", re.M)
GO_BLOCK = re.compile(r"\bimport\s*\(([^)]*)\)")
GO_SINGLE = re.compile(r'\bimport\s+(?:[\w.]+\s+)?"([^"\n]+)"')
GO_QUOTED = re.compile(r'"([^"\n]+)"')
GO_MODULE = re.compile(r"^module\s+(\S+)", re.M)

STDLIB = getattr(sys, "stdlib_module_names", frozenset())
JS_EXTS = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte")
# Imports of non-code files (styles, images, data) are not dependencies between modules.
JS_ASSET = re.compile(r"\.(css|scss|sass|less|svg|png|jpe?g|gif|webp|avif|ico|json|mdx?|"
                      r"woff2?|ttf|eot|mp[34]|html|txt|graphql|gql|ya?ml)$", re.I)


def line_of(starts, offset):
    return bisect.bisect_right(starts, offset)


def imports_in(lang, text):
    """(line, specifier) for every import in the file."""
    starts = [0]
    for m in re.finditer("\n", text):
        starts.append(m.end())
    found = []
    if lang == "javascript":
        for rx in (JS_FROM, JS_SIDE_EFFECT, JS_CALL):
            found += [(line_of(starts, m.start(1)), m.group(1)) for m in rx.finditer(text)]
    elif lang == "python":
        for m in PY_FROM.finditer(text):
            names = re.sub(r"[()\\]|#.*", " ", m.group(3))
            found.append((line_of(starts, m.start()),
                          (m.group(1), m.group(2), [n.split()[0] for n in names.split(",") if n.split()])))
        for m in PY_IMPORT.finditer(text):
            for part in re.sub(r"#.*", "", m.group(1)).split(","):
                if part.split():
                    found.append((line_of(starts, m.start()), ("", part.split()[0], [])))
    elif lang == "jvm":
        for m in JVM_IMPORT.finditer(text):
            found.append((line_of(starts, m.start()), (m.group(1), bool(m.group(2)))))
    elif lang == "php":
        for m in PHP_USE_GROUP.finditer(text):
            for name in m.group(2).split(","):
                if name.strip():
                    found.append((line_of(starts, m.start()),
                                  m.group(1).lstrip("\\") + "\\" + name.split()[0].strip()))
        for m in PHP_USE.finditer(text):
            found.append((line_of(starts, m.start()), m.group(1).lstrip("\\")))
    elif lang == "csharp":
        found = [(line_of(starts, m.start()), m.group(1)) for m in CS_USING.finditer(text)]
    elif lang == "go":
        for block in GO_BLOCK.finditer(text):
            for q in GO_QUOTED.finditer(block.group(1)):
                found.append((line_of(starts, block.start(1) + q.start()), q.group(1)))
        found += [(line_of(starts, m.start(1)), m.group(1)) for m in GO_SINGLE.finditer(text)]
    return found


def declared_namespace(lang, text):
    rx = {"jvm": JVM_PACKAGE, "php": PHP_NAMESPACE, "csharp": CS_NAMESPACE}.get(lang)
    m = rx.search(text) if rx else None
    return m.group(1) if m else None


# --- matching imports to files ------------------------------------------------


def load_jsonc(text):
    """Parse JSON that may hold comments and trailing commas (tsconfig.json)."""
    text = re.sub(r'("(?:\\.|[^"\\])*")|//[^\n]*|/\*.*?\*/',
                  lambda m: m.group(1) or "", text, flags=re.S)
    return json.loads(re.sub(r",(\s*[}\]])", r"\1", text))


class Resolver:
    """Match an import to a file in the repo. Returns (file or None, looks_internal)."""

    def __init__(self, files, texts, root="", listed=()):
        self.root = root
        self.files = set(files)
        self.js_configs = {}  # directory -> {"base": dir, "paths": {...}} from tsconfig/jsconfig
        self.js_packages = {}  # workspace package name -> directory
        self._load_js_projects(listed)
        self.fqn = {}  # "pkg.Class" -> file, for jvm / php / csharp
        self.ns_files = defaultdict(list)  # namespace -> files
        self.py_tail = defaultdict(list)  # dotted module tail -> files
        self.go_dirs = defaultdict(list)  # directory -> files
        self.go_modules = {}  # module path -> directory of its go.mod (filled by main)
        self.ns_roots = {"jvm": set(), "php": set(), "csharp": set()}
        for path, lang in files.items():
            stem = os.path.basename(path).rsplit(".", 1)[0]
            ns = declared_namespace(lang, texts[path]) if lang in self.ns_roots else None
            if ns:
                sep = "\\" if lang == "php" else "."
                self.fqn[(lang, ns + sep + stem)] = path
                self.ns_files[(lang, ns)].append(path)
                depth = 2 if lang == "jvm" else 1
                self.ns_roots[lang].add(tuple(re.split(r"[.\\]", ns)[:depth]))
            if lang == "python":
                parts = path[:-3].split("/")
                if parts[-1] == "__init__":
                    parts = parts[:-1]
                for i in range(len(parts)):
                    self.py_tail[".".join(parts[i:])].append(path)
            if lang == "go":
                self.go_dirs[os.path.dirname(path)].append(path)
        self.py_tops = {k.split(".")[0] for k in self.py_tail}

    def resolve(self, lang, src, spec):
        return getattr(self, f"_{lang}")(src, spec)

    def _read_json(self, path):
        try:
            with open(os.path.join(self.root, path), encoding="utf-8", errors="replace") as fh:
                return load_jsonc(fh.read(500_000))
        except (OSError, ValueError):
            return None

    def _tsconfig(self, path, depth=0):
        """Effective baseUrl and paths of a tsconfig, following relative `extends`."""
        data = self._read_json(path)
        if not isinstance(data, dict) or depth > 5:
            return {}
        here = os.path.dirname(path)
        eff = {}
        parent = data.get("extends")
        if isinstance(parent, str) and parent.startswith("."):
            ppath = os.path.normpath(os.path.join(here, parent))
            eff = dict(self._tsconfig(ppath if ppath.endswith(".json") else ppath + ".json",
                                      depth + 1))
        options = data.get("compilerOptions") or {}
        if "baseUrl" in options:
            eff["base"] = os.path.normpath(os.path.join(here, options["baseUrl"]))
        if isinstance(options.get("paths"), dict):
            eff["paths"] = options["paths"]
            eff["paths_dir"] = here
        return eff

    def _load_js_projects(self, listed):
        for path in listed:
            name = os.path.basename(path)
            if name in ("tsconfig.json", "jsconfig.json"):
                eff = self._tsconfig(path)
                if eff:
                    eff.setdefault("paths", {})
                    eff["resolve_from"] = eff.get("base") or eff.get("paths_dir") or os.path.dirname(path)
                    self.js_configs.setdefault(os.path.dirname(path), eff)
            elif name == "package.json":
                data = self._read_json(path)
                if isinstance(data, dict) and isinstance(data.get("name"), str):
                    entry = {"dir": os.path.dirname(path), "main": data.get("main") or
                             data.get("module") or data.get("source") or ""}
                    self.js_packages.setdefault(data["name"], entry)

    def _js_file(self, base):
        """The file a path points at: x.ts, x.js for x.ts, or x/index.ts."""
        stripped = re.sub(r"\.(c|m)?jsx?$", "", base)
        cands = [base] + [stripped + e for e in JS_EXTS] + [base + e for e in JS_EXTS] + \
            [f"{base}/index{e}" for e in JS_EXTS]
        for cand in cands:
            if cand in self.files:
                return cand
        return None

    def _javascript(self, src, spec):
        if JS_ASSET.search(spec):
            return None, False
        here = os.path.dirname(src)
        if spec.startswith("."):
            return self._js_file(os.path.normpath(os.path.join(here, spec))), True
        # path aliases from the nearest tsconfig / jsconfig
        folder, config = here, None
        while True:
            if folder in self.js_configs:
                config = self.js_configs[folder]
                break
            if not folder:
                break
            folder = os.path.dirname(folder)
        internal = False
        if config:
            for pattern, targets in config["paths"].items():
                prefix, star, suffix = pattern.partition("*")
                if spec == pattern or (star and spec.startswith(prefix) and spec.endswith(suffix)
                                       and len(spec) >= len(prefix) + len(suffix)):
                    internal = True
                    middle = spec[len(prefix):len(spec) - len(suffix)] if star else ""
                    for target in targets:
                        hit = self._js_file(os.path.normpath(os.path.join(
                            config["resolve_from"], target.replace("*", middle))))
                        if hit:
                            return hit, True
            if config.get("base") is not None:
                hit = self._js_file(os.path.normpath(os.path.join(config["base"], spec)))
                if hit:
                    return hit, True
        if spec.startswith(("@/", "~/")):
            # a common alias for `src/` of the nearest package
            folder = here
            while True:
                for base in (os.path.join(folder, "src", spec[2:]), os.path.join(folder, spec[2:])):
                    hit = self._js_file(os.path.normpath(base))
                    if hit:
                        return hit, True
                if not folder:
                    break
                folder = os.path.dirname(folder)
            return None, True
        # packages of this repo (npm / yarn / pnpm workspaces)
        for name, entry in self.js_packages.items():
            if spec == name or spec.startswith(name + "/"):
                sub = spec[len(name):].lstrip("/")
                pkg = entry["dir"]
                if sub:
                    bases = [os.path.join(pkg, sub), os.path.join(pkg, "src", sub)]
                else:
                    main = re.sub(r"^\./", "", entry["main"])
                    bases = ([os.path.join(pkg, main)] if main else []) + [
                        os.path.join(pkg, "src", "index"), os.path.join(pkg, "index"),
                        os.path.join(pkg, "lib", "index")]
                for base in bases:
                    hit = self._js_file(os.path.normpath(base))
                    if hit:
                        return hit, True
                return None, True
        return None, internal

    def _python(self, src, spec):
        level, mod, names = spec
        if level:
            pkg = os.path.dirname(src)
            for _ in range(len(level) - 1):
                pkg = os.path.dirname(pkg)
            base = os.path.join(pkg, mod.replace(".", "/")) if mod else pkg
            cands = [f"{base}/{n}.py" for n in names] + [f"{base}/{n}/__init__.py" for n in names]
            cands += [f"{base}.py", f"{base}/__init__.py"]
            for cand in cands:
                if os.path.normpath(cand) in self.files:
                    return os.path.normpath(cand), True
            return None, True
        top = mod.split(".")[0]
        if top in STDLIB:
            return None, False
        for dotted in [f"{mod}.{n}" for n in names] + [mod]:
            hits = self.py_tail.get(dotted)
            if hits:
                return min(hits, key=lambda p: (p.count("/"), p)), True
        return None, top in self.py_tops

    def _jvm(self, src, spec):
        name, wildcard = spec
        parts = name.split(".")
        for n in range(len(parts), 0, -1):
            hit = self.fqn.get(("jvm", ".".join(parts[:n])))
            if hit:
                return hit, True
        files = self.ns_files.get(("jvm", name if wildcard else ".".join(parts[:-1])))
        if files:
            return sorted(files)[0], True
        return None, tuple(parts[:2]) in self.ns_roots["jvm"]

    def _php(self, src, spec):
        parts = spec.split("\\")
        internal = tuple(parts[:1]) in self.ns_roots["php"]
        for n in range(len(parts), 0, -1):
            hit = self.fqn.get(("php", "\\".join(parts[:n])))
            if hit:
                return hit, True
        return None, internal

    def _csharp(self, src, spec):
        internal = tuple(spec.split(".")[:1]) in self.ns_roots["csharp"]
        files = self.ns_files.get(("csharp", spec))
        if files:
            return sorted(files)[0], True
        return None, internal

    def _go(self, src, spec):
        for mod, directory in self.go_modules.items():
            if spec == mod or spec.startswith(mod + "/"):
                target = os.path.normpath(os.path.join(directory, spec[len(mod):].lstrip("/")))
                files = self.go_dirs.get(target if target != "." else "")
                return (sorted(files)[0], True) if files else (None, True)
        return None, False


# --- leaks -------------------------------------------------------------------

# Library name prefixes, lower case and dotted (`/` and `\` become `.`). An import
# matches when it equals a prefix or starts with it plus a dot. Checked in order.
LEAK_PREFIXES = {
    "HTTP client": [
        "requests", "httpx", "aiohttp", "urllib3", "axios", "node-fetch", "superagent",
        "okhttp3", "com.squareup.okhttp3", "org.apache.http", "org.apache.hc",
        "java.net.http", "org.springframework.web.client", "guzzlehttp",
        "system.net.http"],
    "web framework": [
        "fastapi", "flask", "starlette", "django.http", "django.urls", "django.views",
        "django.shortcuts", "rest_framework", "express", "koa", "fastify", "@nestjs",
        "next", "nuxt", "org.springframework.web", "javax.servlet", "jakarta.servlet",
        "symfony.component.httpfoundation", "symfony.component.httpkernel",
        "symfony.component.routing", "illuminate.http", "illuminate.routing",
        "microsoft.aspnetcore", "net.http", "github.com.gin-gonic", "github.com.gorilla",
        "github.com.labstack"],
    "database / ORM": [
        "sqlalchemy", "django.db", "peewee", "tortoise", "pymongo", "psycopg",
        "psycopg2", "sqlite3", "mysql", "asyncpg", "typeorm", "@prisma", "prisma",
        "sequelize", "mongoose", "knex", "mikro-orm", "@mikro-orm", "drizzle-orm", "pg",
        "mysql2", "mongodb", "org.hibernate", "javax.persistence", "jakarta.persistence",
        "org.jooq", "org.springframework.data", "java.sql", "doctrine",
        "illuminate.database", "microsoft.entityframeworkcore", "system.data",
        "gorm.io", "database.sql", "github.com.jmoiron.sqlx", "github.com.jackc"],
    "queue / cache / cloud SDK": [
        "celery", "pika", "kombu", "bull", "bullmq", "amqplib", "kafkajs", "redis",
        "ioredis", "aioredis", "boto3", "botocore", "@aws-sdk", "aws-sdk",
        "org.apache.kafka", "org.springframework.amqp", "org.springframework.kafka",
        "com.rabbitmq", "com.amazonaws", "php-amqplib", "predis", "illuminate.queue",
        "illuminate.cache", "masstransit", "rabbitmq.client", "confluent.kafka",
        "azure", "github.com.aws", "github.com.segmentio"],
    "config / environment": [
        "dotenv", "decouple", "environ", "pydantic_settings",
        "microsoft.extensions.configuration", "org.springframework.core.env",
        "github.com.spf13.viper"],
    "logging": [
        "logging", "structlog", "loguru", "winston", "pino", "bunyan", "log4js",
        "org.slf4j", "org.apache.logging", "org.apache.log4j", "java.util.logging",
        "ch.qos.logback", "monolog", "psr.log", "illuminate.support.facades.log",
        "serilog", "microsoft.extensions.logging", "log", "github.com.sirupsen",
        "go.uber.org.zap"],
    "UI framework": [
        "react", "react-dom", "vue", "@angular", "svelte", "@reduxjs", "redux", "vuex",
        "pinia", "android", "androidx", "javax.swing", "javafx", "tkinter", "pyqt5",
        "pyside6"],
}
HIDDEN_DEPENDENCIES = {
    "clock / random": re.compile(
        r"\b(datetime\.(now|utcnow|today)|date\.today|time\.time|Date\.now|new Date\(\)|"
        r"DateTime\.(Now|UtcNow|Today)|Instant\.now|LocalDate(Time)?\.now|"
        r"ZonedDateTime\.now|Carbon::now|Time\.(now|current)|Math\.random|"
        r"random\.(random|randint|choice)|uuid\.uuid4|UUID\.randomUUID|Guid\.NewGuid|"
        r"mt_rand)\b|\bnow\(\)|\brand\("),
    "environment / config read": re.compile(
        r"\b(process\.env|os\.environ|os\.getenv|System\.getenv|"
        r"Environment\.GetEnvironmentVariable|ConfigurationManager|ENV\[)|"
        r"\bgetenv\(|\benv\(|\bconfig\(|\$_(ENV|SERVER)\b"),
    "static facade / global": re.compile(
        r"\b(DB|Cache|Log|Auth|Storage|Mail|Queue|Http|Event|Session|Redis|Config)::\w+|"
        r"\bRails\.(logger|cache)\b|\bcurrent_user\b|\bgetCurrentUser\("),
    "new on an infrastructure class": re.compile(
        r"\bnew\s+\w*(Client|Mailer|Connection|DbContext|PDO|Pool|Producer|Consumer)\w*\s*\("),
}
DOMAIN_ONLY = {
    "persistence annotation": re.compile(
        r"^\s*(@(Entity|Table|Column|Id|Document|MappedSuperclass|OneToMany|ManyToOne|"
        r"ManyToMany|OneToOne|JoinColumn)\b|#\[ORM\\|\[(Table|Column|Key|ForeignKey)\b)|@ORM\\"),
    "infrastructure exception": re.compile(
        r"\b(except|catch)\b[^\n]*\b(SQLException|PDOException|QueryException|"
        r"IntegrityError|OperationalError|DatabaseError|DataIntegrityViolationException|"
        r"HttpException|AxiosError|RequestException|ConnectionError|DbUpdateException)\b"),
}


def spec_text(lang, spec):
    """The library or namespace name inside an import, as a string ('' if relative)."""
    if lang == "python":
        return "" if spec[0] else spec[1]
    if lang == "jvm":
        return spec[0]
    return spec


def leak_category(name):
    """The leak category of an imported library or namespace, or None."""
    norm = re.sub(r"[/\\]", ".", name.strip().lower())
    for category, prefixes in LEAK_PREFIXES.items():
        for p in prefixes:
            if norm == p or norm.startswith(p + "."):
                return category
    return None


def is_comment(line):
    s = line.lstrip()
    return s.startswith(("//", "/*", "*", "--")) or (s.startswith("#") and not s.startswith("#["))


# --- graph -------------------------------------------------------------------


def strongly_connected(nodes, edges):
    """Tarjan's algorithm, without recursion. Returns components of size > 1."""
    graph = defaultdict(list)
    for a, b in edges:
        graph[a].append(b)
    index, low, on_stack, stack, out = {}, {}, set(), [], []
    counter = 0
    for root in sorted(nodes):
        if root in index:
            continue
        work = [(root, iter(sorted(graph[root])))]
        index[root] = low[root] = counter
        counter += 1
        stack.append(root)
        on_stack.add(root)
        while work:
            node, it = work[-1]
            advanced = False
            for nxt in it:
                if nxt not in index:
                    index[nxt] = low[nxt] = counter
                    counter += 1
                    stack.append(nxt)
                    on_stack.add(nxt)
                    work.append((nxt, iter(sorted(graph[nxt]))))
                    advanced = True
                    break
                if nxt in on_stack:
                    low[node] = min(low[node], index[nxt])
            if advanced:
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[node])
            if low[node] == index[node]:
                comp = []
                while True:
                    w = stack.pop()
                    on_stack.discard(w)
                    comp.append(w)
                    if w == node:
                        break
                if len(comp) > 1:
                    out.append(sorted(comp))
    return out


def layer_of(path, layers):
    """The layer a path belongs to: the longest matching pattern wins."""
    best, best_len = None, -1
    for name, pattern in layers:
        if fnmatch.fnmatchcase(path, pattern.rstrip("/") + "/*") and len(pattern) > best_len:
            best, best_len = name, len(pattern)
    return best


def parse_layers(specs):
    layers = []
    for spec in specs:
        name, _, pattern = spec.partition("=")
        name = name.strip().lower()
        if name not in LAYER_RANK or not pattern.strip():
            raise SystemExit(f"error: --layer needs NAME=PATH with NAME one of "
                             f"{', '.join(LAYER_RANK)}; got {spec!r}")
        layers.append((name, pattern.strip().strip("/")))
    return layers


# --- main --------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".",
                    help="repository path, or a folder inside one (default: .)")
    ap.add_argument("--path", default="", help="report only on this subdirectory")
    ap.add_argument("--layer", action="append", default=[], metavar="NAME=PATH",
                    help="map a folder onto a layer: domain, application or "
                         "infrastructure. PATH is relative to the repo root and may "
                         "use * (src/*/Domain). Repeatable.")
    ap.add_argument("--module-depth", type=int, default=2,
                    help="folders deep that make up a module (default 2), as in hotspots.py")
    ap.add_argument("--top", type=int, default=15, help="rows per table (default 15)")
    ap.add_argument("--include-tests", action="store_true", help="read test files too")
    ap.add_argument("--keep-dir", action="append", default=[], metavar="NAME",
                    help="read a directory that is on the exclusion list (see hotspots.py)")
    ap.add_argument("--json", action="store_true",
                    help="print JSON with every hit instead of markdown")
    args = ap.parse_args()

    layers = parse_layers(args.layer)
    keep_dirs = {d.lower() for d in args.keep_dir}
    start = os.path.abspath(args.repo)
    if not os.path.isdir(start):
        print(f"error: {start} is not a directory", file=sys.stderr)
        return 2
    try:
        root = hs.git(start, "rev-parse", "--show-toplevel").strip()
        prefix = hs.git(start, "rev-parse", "--show-prefix").strip().rstrip("/")
        listed = hs.git(root, "ls-files").splitlines()
    except (RuntimeError, FileNotFoundError):
        root, prefix = start, ""
        listed = [os.path.relpath(os.path.join(d, f), root).replace(os.sep, "/")
                  for d, dirs, fs in os.walk(root)
                  for f in fs if not any(x.lower() in hs.SAFE_EXCLUDED_DIRS for x in
                                         os.path.relpath(d, root).split(os.sep))]
    scope = "/".join(x for x in (prefix, args.path.strip("/")) if x)

    def in_scope(path):
        return not scope or path == scope or path.startswith(scope + "/")

    source = [p for p in listed if not hs.exclusion(p, args.include_tests,
                                                    hs.SOURCE_EXTENSIONS, keep_dirs)]
    files, texts, not_covered, skipped = {}, {}, Counter(), 0
    for p in source:
        ext = hs.file_ext(p)
        lang = LANGUAGES.get(ext)
        if not lang:
            not_covered[ext or "(no extension)"] += 1
            continue
        try:
            if os.path.getsize(os.path.join(root, p)) > MAX_FILE_BYTES:
                skipped += 1
                continue
            with open(os.path.join(root, p), encoding="utf-8", errors="replace") as fh:
                texts[p] = fh.read()
        except OSError:
            skipped += 1
            continue
        files[p] = lang
    resolver = Resolver(files, texts, root, listed)
    # go.mod files are not source files; find them separately.
    for p in listed:
        if os.path.basename(p) == "go.mod":
            try:
                with open(os.path.join(root, p), encoding="utf-8", errors="replace") as fh:
                    m = GO_MODULE.search(fh.read(100_000))
                if m:
                    resolver.go_modules[m.group(1)] = os.path.dirname(p)
            except OSError:
                pass

    modmap = hs.ModuleMap(list(files), args.module_depth)
    edges = defaultdict(list)  # (module_a, module_b) -> [(file, line, target)]
    file_edges = []  # (src, line, spec, target)
    coverage = defaultdict(lambda: {"files": 0, "imports": 0, "resolved": 0,
                                    "unresolved_internal": 0, "external": 0})
    leaks = defaultdict(list)
    for path, lang in files.items():
        cov = coverage[lang]
        cov["files"] += 1
        layer = layer_of(path, layers)
        for line, spec in imports_in(lang, texts[path]):
            cov["imports"] += 1
            target, internal = resolver.resolve(lang, path, spec)
            if target:
                cov["resolved"] += 1
                if target != path:
                    file_edges.append((path, line, spec, target))
                    ma, mb = modmap.of(path), modmap.of(target)
                    if ma != mb:
                        edges[(ma, mb)].append((path, line, target))
            elif internal:
                cov["unresolved_internal"] += 1
            else:
                cov["external"] += 1
            if layer == "domain":
                category = leak_category(spec_text(lang, spec))
                if category and not target:
                    leaks[category].append({"file": path, "line": line, "layer": layer,
                                            "text": texts[path].splitlines()[line - 1].strip()[:110]})
        if layer in ("domain", "application"):
            for n, code in enumerate(hs.code_lines(texts[path], hs.file_ext(path)), 1):
                if not code:
                    continue
                for name, rx in HIDDEN_DEPENDENCIES.items():
                    if rx.search(code):
                        leaks[name].append({"file": path, "line": n, "layer": layer,
                                            "text": code[:110]})
        if layer == "domain":
            for n, raw in enumerate(texts[path].splitlines(), 1):
                if is_comment(raw):
                    continue
                for name, rx in DOMAIN_ONLY.items():
                    if rx.search(raw):
                        leaks[name].append({"file": path, "line": n, "layer": layer,
                                            "text": raw.strip()[:110]})

    # layer direction: an inner layer must not import an outer one
    wrong_way = defaultdict(list)
    for src, line, spec, target in file_edges:
        a, b = layer_of(src, layers), layer_of(target, layers)
        if a and b and LAYER_RANK[a] < LAYER_RANK[b]:
            wrong_way[(a, b)].append({"file": src, "line": line, "imports": target})

    # modules
    modules = set(modmap.of(p) for p in files)
    fan_out, fan_in, used = defaultdict(set), defaultdict(set), defaultdict(set)
    for (a, b), hits in edges.items():
        fan_out[a].add(b)
        fan_in[b].add(a)
        used[b].update(t for _, _, t in hits)
    module_files = Counter(modmap.of(p) for p in files)
    module_rows = []
    for m in modules:
        ca, ce = len(fan_in[m]), len(fan_out[m])
        module_rows.append({
            "module": m, "files": module_files[m], "fan_in": ca, "fan_out": ce,
            "instability": round(ce / (ca + ce), 2) if ca + ce else None,
            "files_used_from_outside": len(used[m]),
        })
    module_rows.sort(key=lambda r: (-(r["fan_in"] + r["fan_out"]), r["module"]))

    def cycle_entry(comp, edge_map, nested):
        inner = [(a, b, h) for (a, b), h in edge_map.items() if a in comp and b in comp]
        inner.sort(key=lambda e: (len(e[2]), e[0], e[1]))
        return {"modules": comp, "nested": nested, "edges": [
            {"from": a, "to": b, "imports": len(h),
             "example": {"file": h[0][0], "line": h[0][1], "target": h[0][2]}}
            for a, b, h in inner]}

    # A folder and its own subfolders are probably one module in practice, so imports
    # between them do not count toward a cycle. A cycle that exists only because of
    # such imports is still listed, marked as nested.
    def related(a, b):
        return a.startswith(b + "/") or b.startswith(a + "/")

    strict = {k: v for k, v in edges.items() if not related(*k)}
    cycles = [cycle_entry(c, strict, False) for c in strongly_connected(modules, strict.keys())]
    found = [set(c["modules"]) for c in cycles]
    cycles += [cycle_entry(c, edges, True) for c in strongly_connected(modules, edges.keys())
               if not any(f <= set(c) for f in found)]
    cycles.sort(key=lambda c: (c["nested"], c["modules"]))
    cycles = [c for c in cycles if not scope or any(
        any(in_scope(p) for p in files if modmap.of(p) == m) for m in c["modules"])]

    cov_rows = {}
    for lang, c in sorted(coverage.items()):
        internal = c["resolved"] + c["unresolved_internal"]
        cov_rows[lang] = {**c, "coverage": round(100 * c["resolved"] / internal) if internal else None}

    result = {
        "meta": {"repo": root, "scope": scope or None, "layers": [f"{n}={p}" for n, p in layers],
                 "files_read": len(files), "files_skipped": skipped,
                 "module_depth": args.module_depth},
        "coverage": cov_rows,
        "not_covered": dict(not_covered.most_common()),
        "cycles": cycles,
        "wrong_way_imports": {f"{a} -> {b}": v for (a, b), v in wrong_way.items()
                              if any(in_scope(x["file"]) for x in v)},
        "leaks": {k: [h for h in v if in_scope(h["file"])] for k, v in leaks.items()
                  if any(in_scope(h["file"]) for h in v)},
        "modules": [r for r in module_rows
                    if not scope or any(in_scope(p) for p in files if modmap.of(p) == r["module"])],
    }
    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    top = args.top
    print(f"# Dependencies for {os.path.basename(root)}\n")
    print(f"Read {len(files)} files (module depth {args.module_depth})"
          + (f", scope `{scope}`" if scope else "")
          + (f", layers: {', '.join(result['meta']['layers'])}" if layers else
             ". No --layer given: layer checks and domain leak search skipped")
          + ". Line numbers are from the working tree.\n")
    print("## Coverage\n")
    print("Imports matched to a file in the repo. Imports that cannot be matched are "
          "treated as external; a cycle through one of them is not seen."
          + (" Coverage counts every file read, not only the scope." if scope else "")
          + "\n")
    print("| Language | Files | Imports | Matched | Internal but unmatched | Coverage |")
    print("|---|---|---|---|---|---|")
    for lang, c in cov_rows.items():
        pct = "n/a" if c["coverage"] is None else f"{c['coverage']}%"
        print(f"| {lang} | {c['files']} | {c['imports']} | {c['resolved']} | "
              f"{c['unresolved_internal']} | {pct} |")
    if not_covered:
        shown = ", ".join(f".{e}: {n}" for e, n in not_covered.most_common(8))
        print(f"\nNot covered (no import reader): {shown}. Check these by hand.")
    if skipped:
        print(f"\n{skipped} files skipped (over {MAX_FILE_BYTES // 1000} KB or unreadable).")

    print("\n## Cycles between modules\n")
    print("Imports between a folder and its own subfolders are not counted toward a cycle.\n")
    if not cycles:
        print("None found among the imports that were matched.")
    for i, c in enumerate(cycles, 1):
        note = (" Nested: it exists only through imports between a folder and its own "
                "subfolders, so it is probably one module in practice; judge before "
                "you flag it." if c["nested"] else "")
        print(f"**Cycle {i}**: {', '.join(f'`{m}`' for m in c['modules'])}.{note} "
              f"The edge with the fewest imports is the cheapest to cut.\n")
        print("| From | To | Imports | Example |")
        print("|---|---|---|---|")
        for e in c["edges"][:top]:
            ex = e["example"]
            print(f"| `{e['from']}` | `{e['to']}` | {e['imports']} | "
                  f"`{ex['file']}:{ex['line']}` -> `{ex['target']}` |")
        print()

    if layers:
        print("## Layer direction\n")
        print("An import from domain to anything outer is a leak. Application to "
              "infrastructure is a leak only where the architecture puts ports between "
              "them (hexagonal, clean); in a classic layered app it is the normal "
              "direction.\n")
        if not result["wrong_way_imports"]:
            print("No import points from an inner layer to an outer one.")
        for key, hits in result["wrong_way_imports"].items():
            print(f"**{key}**: {len(hits)} imports. First {min(len(hits), 8)}:\n")
            for h in hits[:8]:
                print(f"- `{h['file']}:{h['line']}` imports `{h['imports']}`")
            print()

    if result["leaks"]:
        print("## Leaks and hidden dependencies\n")
        print("Domain files for the import categories; domain and application files for "
              "the hidden dependencies. Count, then the first three. All hits are in "
              "the `--json` output.\n")
        print("| What | Hits | Files | First three |")
        print("|---|---|---|---|")
        for cat, hits in sorted(result["leaks"].items(), key=lambda kv: -len(kv[1])):
            first = "; ".join(f"`{h['file']}:{h['line']}`" for h in hits[:3])
            print(f"| {cat} | {len(hits)} | {len({h['file'] for h in hits})} | {first} |")
    elif any(n == "domain" for n, _ in layers):
        print("## Leaks and hidden dependencies\n")
        print("None found in the domain layer (import categories, clock/random, "
              "environment, facades, annotations, infrastructure exceptions).")

    print("\n## Modules by number of dependencies\n")
    print("Fan-in: modules that import it. Fan-out: modules it imports. Instability = "
          "fan-out / (fan-in + fan-out). Files used from outside: how many of its "
          "files other modules import (a high share suggests no public entry point).\n")
    print("| Module | Files | Fan-in | Fan-out | Instability | Files used from outside |")
    print("|---|---|---|---|---|---|")
    for r in result["modules"][:top]:
        print(f"| `{r['module']}` | {r['files']} | {r['fan_in']} | {r['fan_out']} | "
              f"{'n/a' if r['instability'] is None else r['instability']} | "
              f"{r['files_used_from_outside']} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
