#!/usr/bin/env python3
"""Edit Xcode String Catalogs (.xcstrings) without reformatting them.

Writes files exactly the way Xcode does (two-space indent, " : " separators,
key order kept, empty objects written with a blank line), so a change shows up
as a small diff. New keys are inserted in case-insensitive order, like Xcode.

Commands:
  check FILE...                       verify each file round-trips unchanged
  set FILE --key K --lang L --value V [--state needs_review]
                                      set one string unit (default state needs_review)
  delete FILE --key K [--key K2 ...]  remove entries (stale or unused keys)
  rename-key FILE --from OLD --to NEW move an entry to a new key (for example a
                                      key that differs from the code by a
                                      non-breaking space); refuses to overwrite
                                      an entry that already has localizations
  lint FILE... [--base REF]           report likely translation mistakes: format
                                      specifiers that differ from the source
                                      language or are invalid, leading or trailing
                                      spaces that differ from the source (joined
                                      fragments lose their separator), values equal
                                      to the source text, and keys that differ only
                                      by apostrophes, quotes, or spaces, and
                                      Info.plist keys outside an InfoPlist catalog;
                                      with --base,
                                      also values that changed into the source
                                      language and translated->needs_review changes
                                      compared with that git revision

Runs on Python 3.9, the version Xcode ships; run it with `xcrun python3`.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict

if sys.version_info < (3, 9):
    sys.exit("Needs Python 3.9 or newer. Run it with Xcode's Python: xcrun python3 " + sys.argv[0])


def dump(value, indent=0):
    pad = "  " * indent
    inner = "  " * (indent + 1)
    if isinstance(value, dict):
        if not value:
            return "{\n\n" + pad + "}"
        items = [f"{inner}{json.dumps(k, ensure_ascii=False)} : {dump(v, indent + 1)}" for k, v in value.items()]
        return "{\n" + ",\n".join(items) + "\n" + pad + "}"
    if isinstance(value, list):
        if not value:
            return "[\n\n" + pad + "]"
        items = [f"{inner}{dump(v, indent + 1)}" for v in value]
        return "[\n" + ",\n".join(items) + "\n" + pad + "]"
    return json.dumps(value, ensure_ascii=False)


def load(path):
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()
    return raw, json.loads(raw)


def save(path, data, raw):
    out = dump(data)
    if raw.endswith("\n"):
        out += "\n"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(out)


def insert_sorted(strings, key, entry):
    items = list(strings.items())
    pos = len(items)
    for i, (k, _) in enumerate(items):
        if k.lower() > key.lower():
            pos = i
            break
    items.insert(pos, (key, entry))
    return dict(items)


SPECIFIER = re.compile(r"%(?:\d+\$)?[-+ 0#']*\d*(?:\.\d+)?(?:hh|h|ll|l|q|L|z|t|j)?[@dDiuUxXoOfFeEgGcCsSaAp]")


INFOPLIST_KEY = re.compile(r"^(NS\w+UsageDescription|CFBundleDisplayName|CFBundleName|NSHumanReadableCopyright|"
                           r"NSUserActivityTypes|INAlternativeAppNames)$")


def units(entry, lang):
    """Yield (variant path, state, value) for every string unit of one language."""
    loc = entry.get("localizations", {}).get(lang)
    if not loc:
        return
    stack = [("", loc)]
    while stack:
        path, node = stack.pop()
        if "stringUnit" in node:
            unit = node["stringUnit"]
            yield path or "-", unit.get("state", ""), unit.get("value", "")
        for kind, variants in node.get("variations", {}).items():
            for name, sub in variants.items():
                stack.append((f"{path}/{kind}.{name}".lstrip("/"), sub))


def specifiers(value):
    clean = value.replace("%%", "")
    found = SPECIFIER.findall(clean)
    types = Counter(re.sub(r"^%(?:\d+\$)?[-+ 0#']*\d*(?:\.\d+)?", "%", s) for s in found)
    invalid = len(re.findall("%", clean)) - len(found)
    return types, invalid


def normalized_key(key):
    for a, b in (("\u2019", "'"), ("\u2018", "'"), ("\u201c", '"'), ("\u201d", '"'), ("\u00a0", " ")):
        key = key.replace(a, b)
    return " ".join(key.split()).casefold()


def base_catalog(path, ref):
    top = subprocess.run(["git", "-C", os.path.dirname(os.path.abspath(path)), "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True).stdout.strip()
    rel = os.path.relpath(os.path.abspath(path), top)
    out = subprocess.run(["git", "-C", top, "show", f"{ref}:{rel}"], capture_output=True, text=True)
    return json.loads(out.stdout) if out.returncode == 0 else None


def lint(path, ref):
    _, data = load(path)
    strings = data.get("strings", {})
    source = data.get("sourceLanguage", "en")
    findings = []
    groups = defaultdict(list)
    infoplist_table = os.path.basename(path).startswith("InfoPlist")
    for key, entry in strings.items():
        if key.strip():
            groups[normalized_key(key)].append(key)
        if not infoplist_table and INFOPLIST_KEY.match(key):
            findings.append(f"Info.plist key in a table iOS never reads for Info.plist: {key!r} "
                            "(move it to the InfoPlist catalog of the target that owns the Info.plist)")
        langs = set(entry.get("localizations", {})) | {source}
        src_units = {p: v for p, _, v in units(entry, source)} or {"-": key}
        for lang in sorted(langs - {source}):
            for vpath, _, value in units(entry, lang):
                src = src_units.get(vpath, src_units.get("-", key))
                s_types, _ = specifiers(src)
                v_types, invalid = specifiers(value)
                where = f"{key!r} [{lang}{'' if vpath == '-' else ' ' + vpath}]"
                if invalid:
                    findings.append(f"invalid format sequence: {where} = {value!r}")
                elif s_types != v_types:
                    findings.append(f"format specifiers differ from {source}: {where} = {value!r}, {source} = {src!r}")
                if (src[:1].isspace(), src[-1:].isspace()) != (value[:1].isspace(), value[-1:].isspace()):
                    findings.append(f"leading or trailing space differs from {source}: {where} = {value!r}, {source} = {src!r}")
                if value == src and re.search(r"[^\W\d_]{4,}", value):
                    findings.append(f"same text as {source} (untranslated?): {where} = {value!r}")
    for keys in groups.values():
        if len(keys) > 1:
            findings.append(f"keys differ only by quotes, apostrophes, or spaces: {keys!r}")
    if ref:
        base = base_catalog(path, ref)
        if base is None:
            findings.append(f"no version of this file at {ref}")
        else:
            states = Counter()
            for key, entry in strings.items():
                old = base.get("strings", {}).get(key)
                if not old:
                    continue
                for lang in entry.get("localizations", {}):
                    old_units = {p: (s, v) for p, s, v in units(old, lang)}
                    src_new = {p: v for p, _, v in units(entry, source)} or {"-": key}
                    for vpath, state, value in units(entry, lang):
                        if vpath not in old_units:
                            continue
                        old_state, old_value = old_units[vpath]
                        if old_state == "translated" and state == "needs_review":
                            states[lang] += 1
                        if lang != source and value != old_value and value == src_new.get(vpath, key) and old_value != value:
                            findings.append(f"changed into {source} text: {key!r} [{lang}] {old_value!r} -> {value!r}")
            for lang, count in sorted(states.items()):
                findings.append(f"{count} value(s) in {lang} changed from translated to needs_review since {ref}")
    return findings


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("files", nargs="+")
    s = sub.add_parser("set")
    s.add_argument("file")
    s.add_argument("--key", required=True)
    s.add_argument("--lang", required=True)
    s.add_argument("--value", required=True)
    s.add_argument("--state", default="needs_review", choices=["needs_review", "translated", "new"])
    dl = sub.add_parser("delete")
    dl.add_argument("file")
    dl.add_argument("--key", action="append", required=True)
    r = sub.add_parser("rename-key")
    r.add_argument("file")
    r.add_argument("--from", dest="old", required=True)
    r.add_argument("--to", dest="new", required=True)
    li = sub.add_parser("lint")
    li.add_argument("files", nargs="+")
    li.add_argument("--base", help="git revision to compare with, such as the branch the change starts from")
    args = ap.parse_args()

    if args.cmd == "lint":
        total = 0
        for f in args.files:
            for line in lint(f, args.base):
                print(f"{f}: {line}")
                total += 1
        print(f"{total} finding(s) in {len(args.files)} file(s); judge each against the code before reporting it")
        return

    if args.cmd == "check":
        failed = 0
        for f in args.files:
            raw, data = load(f)
            out = dump(data) + ("\n" if raw.endswith("\n") else "")
            if out != raw:
                failed += 1
                print(f"DIFFERS {f}")
        print(f"{len(args.files) - failed}/{len(args.files)} round-trip unchanged")
        sys.exit(1 if failed else 0)

    raw, data = load(args.file)
    strings = data.setdefault("strings", {})
    if args.cmd == "set":
        if args.key not in strings:
            strings = insert_sorted(strings, args.key, {})
            data["strings"] = strings
        entry = strings[args.key]
        entry.setdefault("localizations", {})[args.lang] = {
            "stringUnit": {"state": args.state, "value": args.value}
        }
        entry.pop("extractionState", None) if entry.get("extractionState") == "stale" else None
        save(args.file, data, raw)
        print(f"set {args.lang} for {args.key!r} ({args.state})")
    elif args.cmd == "delete":
        missing = [k for k in args.key if k not in strings]
        if missing:
            sys.exit(f"keys not found: {missing!r}")
        for k in args.key:
            strings.pop(k)
        save(args.file, data, raw)
        print(f"deleted {len(args.key)} key(s)")
    elif args.cmd == "rename-key":
        if args.old not in strings:
            sys.exit(f"key not found: {args.old!r}")
        if strings.get(args.new, {}).get("localizations"):
            sys.exit(f"target key already has localizations: {args.new!r}; merge by hand")
        entry = strings.pop(args.old)
        strings.pop(args.new, None)
        data["strings"] = insert_sorted(strings, args.new, entry)
        save(args.file, data, raw)
        print(f"renamed {args.old!r} to {args.new!r}")


if __name__ == "__main__":
    main()
