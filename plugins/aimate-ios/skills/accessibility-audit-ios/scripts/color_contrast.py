#!/usr/bin/env python3
"""Resolve asset-catalog colors and compute WCAG contrast ratios.

Reads every tracked `*.colorset/Contents.json` in the repository and resolves its
light and dark (and high-contrast) values. Lists them, or computes the contrast
ratio of foreground/background pairs in light and dark appearance.

A color is named by its folder path inside the asset catalog, such as
`Foreground/Base`, so colors with the same name in different folders stay
apart. The short name (`Base`) works when it is unique; an ambiguous short name
is an error that lists the full names. A hex value is `#RRGGBB` for both
appearances or `#RRGGBB/#RRGGBB` for light/dark.

Colors that reference a system color (for example systemBlueColor) cannot be
resolved from the repository and are reported as `system`; check those in the
running app. Display P3 values are treated as sRGB, which is close enough for a
first check but not exact.

Usage:
  color_contrast.py --repo PATH --list
  color_contrast.py --repo PATH --pair Foreground/Base Background/Base [--pair FG BG ...] [--json]
  color_contrast.py --repo PATH --pair "#737373/#8A8A8A" Background/Base
"""
import argparse
import json
import os
import subprocess
import sys


def component(value):
    text = str(value).strip()
    if text.lower().startswith("0x"):
        return int(text, 16) / 255
    number = float(text)
    return number / 255 if number > 1 else number


def parse_color(entry):
    color = entry.get("color", {})
    if "reference" in color or "platform" in color and "components" not in color:
        return "system"
    comps = color.get("components")
    if not comps:
        return None
    try:
        return tuple(component(comps[k]) for k in ("red", "green", "blue"))
    except (KeyError, ValueError):
        return None


def load_colors(repo):
    out = subprocess.run(["git", "-C", repo, "ls-files", "-z"], capture_output=True, text=True, check=True).stdout
    colors = {}
    for path in out.split("\0"):
        if not path.endswith(".colorset/Contents.json"):
            continue
        inside = path.split(".xcassets/", 1)[1] if ".xcassets/" in path else os.path.basename(os.path.dirname(path)) + "/x"
        name = os.path.dirname(inside)[: -len(".colorset")]
        if name in colors:  # the same path in two catalogs
            name = f"{os.path.basename(path.split('.xcassets/')[0])}:{name}"
        try:
            with open(os.path.join(repo, path), encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, ValueError):
            continue
        variants = {}
        for entry in data.get("colors", []):
            appearances = {a.get("value") for a in entry.get("appearances", [])}
            key = "dark" if "dark" in appearances else "light"
            if "high" in appearances:
                key += "-high-contrast"
            if entry.get("idiom", "universal") in ("universal", "iphone", "ipad"):
                variants.setdefault(key, parse_color(entry))
        variants.setdefault("dark", variants.get("light"))
        colors[name] = {"file": path, **variants}
    return colors


def to_hex(rgb):
    if rgb in (None, "system"):
        return str(rgb)
    return "#" + "".join(f"{round(c * 255):02X}" for c in rgb)


def luminance(rgb):
    def channel(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(fg, bg):
    if fg in (None, "system") or bg in (None, "system"):
        return None
    hi, lo = sorted((luminance(fg), luminance(bg)), reverse=True)
    return round((hi + 0.05) / (lo + 0.05), 2)


def hex_rgb(value):
    return tuple(int(value[i:i + 2], 16) / 255 for i in (1, 3, 5))


def full_name(token, colors):
    if token in colors:
        return token
    matches = [n for n in colors if n.split("/")[-1] == token]
    if len(matches) > 1:
        raise SystemExit(f"Ambiguous color name {token!r}; use one of: {', '.join(sorted(matches))}")
    return matches[0] if matches else None


def resolve(token, colors, appearance):
    if token.startswith("#"):
        parts = token.split("/")
        if all(len(p) == 7 and p.startswith("#") for p in parts) and len(parts) in (1, 2):
            return hex_rgb(parts[0] if appearance == "light" or len(parts) == 1 else parts[1])
        return None
    name = full_name(token, colors)
    return colors[name].get(appearance) if name else None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--pair", nargs=2, action="append", metavar=("FOREGROUND", "BACKGROUND"), default=[])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    colors = load_colors(os.path.abspath(args.repo))

    if args.list or not args.pair:
        short = {}
        for n in colors:
            short.setdefault(n.split("/")[-1], []).append(n)
        rows = [{"name": n, "light": to_hex(c.get("light")), "dark": to_hex(c.get("dark")), "file": c["file"],
                 "ambiguous_short_name": len(short[n.split("/")[-1]]) > 1}
                for n, c in sorted(colors.items())]
        if args.json:
            print(json.dumps(rows, indent=2))
        else:
            for row in rows:
                mark = "  (short name is ambiguous)" if row["ambiguous_short_name"] else ""
                print(f"{row['name']:<44} light {row['light']:<8} dark {row['dark']:<8}{mark}")
            print(f"{len(rows)} colors. Name colors by their folder path; short names work only when unique.")
        return 0

    results = []
    for fg, bg in args.pair:
        entry = {"foreground": fg, "background": bg}
        for appearance in ("light", "dark"):
            f, b = resolve(fg, colors, appearance), resolve(bg, colors, appearance)
            entry[appearance] = {"foreground": to_hex(f), "background": to_hex(b), "ratio": ratio(f, b)}
        results.append(entry)
    if args.json:
        print(json.dumps(results, indent=2))
        return 0
    for entry in results:
        parts = []
        for appearance in ("light", "dark"):
            r = entry[appearance]["ratio"]
            parts.append(f"{appearance} {r if r is not None else 'unresolved'}:1"
                         f" ({entry[appearance]['foreground']} on {entry[appearance]['background']})")
        print(f"{entry['foreground']} on {entry['background']}: " + "; ".join(parts))
    print("Thresholds: 4.5:1 normal text, 3:1 large text (about 24 pt, or 19 pt bold) and non-text elements.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
