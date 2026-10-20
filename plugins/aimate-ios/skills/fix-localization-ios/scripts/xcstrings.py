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

Runs on Python 3.9, the version Xcode ships; run it with `xcrun python3`.
"""

import argparse
import json
import sys

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
    args = ap.parse_args()

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
