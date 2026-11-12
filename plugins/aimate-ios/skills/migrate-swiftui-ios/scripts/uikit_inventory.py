#!/usr/bin/env python3
"""Inventory the UIKit user interface of an iOS repository for a SwiftUI migration plan.

Reads only git-tracked files. Finds view controllers and UIKit views (following
superclasses defined in the project), storyboard and XIB scenes, UIKit-only APIs
that need a wrapper or a decision, base classes with their subclass counts,
unreferenced controllers, shared views, UI dependencies, existing SwiftUI and
bridging code, and the app lifecycle. Every view controller gets a complexity
class (see COMPLEXITY below and the conversion guide).

Files that are not part of an Xcode project or a Swift package are reported as
`in_project: false` (orphans) and left out of the totals. Membership is read from
project.pbxproj with `plutil`; when that fails, membership is `null` (unknown).

Usage: uikit_inventory.py --repo PATH [--json] [--exclude GLOB ...]
"""
import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict

VC_ROOTS = {
    "UIViewController", "UITableViewController", "UICollectionViewController", "UINavigationController",
    "UITabBarController", "UIPageViewController", "UISplitViewController", "UISearchController",
    "UIAlertController", "UIInputViewController", "UIDocumentBrowserViewController",
}
VIEW_ROOTS = {
    "UIView", "UIControl", "UIButton", "UILabel", "UIImageView", "UIStackView", "UIScrollView",
    "UITableView", "UICollectionView", "UITableViewCell", "UICollectionViewCell",
    "UICollectionReusableView", "UITableViewHeaderFooterView", "UITextField", "UITextView",
    "UISwitch", "UISlider", "UISegmentedControl", "UIPageControl", "UIVisualEffectView",
    "UINavigationBar", "UITabBar", "UIToolbar", "UISearchBar",
}
# UIKit-only or hard-to-convert APIs: (flag, regex, weight).
# Weight 2 = needs a wrapper or a design decision; 1 = extra work; 0 = informational.
FLAGS = [
    ("web view", r"\bWKWebView\b", 1),
    ("map", r"\bMKMapView\b", 2),
    ("video player", r"\bAVPlayerViewController\b|\bAVPlayerLayer\b", 1),
    ("camera or image picker", r"\bUIImagePickerController\b|\bAVCaptureSession\b|\bPHPickerViewController\b", 2),
    ("mail or message composer", r"\bMFMailComposeViewController\b|\bMFMessageComposeViewController\b", 1),
    ("document picker", r"\bUIDocumentPickerViewController\b|\bUIDocumentInteractionController\b", 1),
    ("PDF", r"\bPDFView\b", 1),
    ("page view controller", r"\bUIPageViewController\b", 1),
    ("custom transition", r"UIViewControllerAnimatedTransitioning|UIViewControllerTransitioningDelegate|UIPresentationController\b", 2),
    ("compositional or custom layout", r"UICollectionViewCompositionalLayout|UICollectionViewFlowLayout\s*\{|:\s*UICollectionViewLayout\b", 2),
    ("diffable data source", r"UITableViewDiffableDataSource|UICollectionViewDiffableDataSource", 1),
    ("drag and drop", r"UIDragInteraction|UIDropInteraction|dragDelegate|dropDelegate", 2),
    ("rich text editing", r"\bUITextView\b.*(attributedText|textStorage)|NSTextStorage|NSLayoutManager|TextKit", 2),
    ("keyboard handling", r"keyboardWillShowNotification|keyboardWillChangeFrameNotification|IQKeyboardManager", 1),
    ("custom drawing", r"override func draw\(_|CAShapeLayer|CADisplayLink|UIGraphicsImageRenderer", 1),
    ("gesture recognizers", r"UI(Pan|Pinch|Rotation|Swipe|LongPress|ScreenEdgePan)GestureRecognizer", 1),
    ("child view controllers", r"addChild\(|willMove\(toParent|didMove\(toParent", 1),
    ("search controller", r"\bUISearchController\b", 1),
    ("RxSwift or RxCocoa", r"import RxSwift|import RxCocoa", 2),
    ("auto layout in code", r"NSLayoutConstraint|\.snp\.|SnapKit|anchor\(equalTo|constraint\(equalTo", 0),
    ("imports Combine", r"import Combine", 0),
    ("context menu or swipe actions", r"UIContextMenuConfiguration|UISwipeActionsConfiguration|trailingSwipeActionsConfiguration", 0),
    ("pull to refresh", r"\bUIRefreshControl\b", 0),
]
CLASS_RE = re.compile(r"^\s*(?:@\w+(?:\([^)]*\))?\s+)*(?:(?:public|open|internal|private|fileprivate|final)\s+)*class\s+(\w+)\s*(?:<[^>]*>)?\s*:\s*([\w.]+)", re.M)
OBJC_RE = re.compile(r"@interface\s+(\w+)\s*:\s*(\w+)")
COORDINATOR_RE = re.compile(r"^\s*(?:(?:public|open|internal|private|fileprivate|final)\s+)*(class|struct|actor|protocol)\s+(\w*Coordinator(?:ing|Protocol)?)\b", re.M)
ORDER = ["S", "M", "L", "XL"]
COMPLEXITY = """S: up to 150 lines, at most one flag of weight 1, no flag of weight 2, not from Interface Builder.
M: up to 400 lines, or from a storyboard or XIB, or flags of weight 1 adding up to 2 or more.
L: up to 800 lines, or one flag of weight 2.
XL: more than 800 lines, or two or more flags of weight 2.
The class is the highest that applies."""


def git_files(repo):
    out = subprocess.run(["git", "-C", repo, "ls-files", "-z"], capture_output=True, text=True, check=True).stdout
    return [p for p in out.split("\0") if p]


def read(repo, path):
    try:
        with open(os.path.join(repo, path), encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except OSError:
        return ""


def project_members(repo, files):
    """Return (set of repo-relative files in an Xcode project, list of synchronized folders, ok flag)."""
    members, synced, ok = set(), [], True
    for pbx in [f for f in files if f.endswith(".xcodeproj/project.pbxproj")]:
        proj_dir = os.path.dirname(os.path.dirname(pbx))
        try:
            raw = subprocess.run(["plutil", "-convert", "json", "-o", "-", os.path.join(repo, pbx)],
                                 capture_output=True, text=True, check=True).stdout
            objects = json.loads(raw)["objects"]
            root = objects[json.loads(raw)["rootObject"]]
        except (OSError, subprocess.CalledProcessError, ValueError, KeyError):
            ok = False
            continue

        def walk(oid, base):
            obj = objects.get(oid, {})
            isa, path, tree = obj.get("isa"), obj.get("path"), obj.get("sourceTree", "<group>")
            if tree == "SOURCE_ROOT":
                here = os.path.normpath(os.path.join(proj_dir, path or ""))
            elif tree == "<group>":
                here = os.path.normpath(os.path.join(base, path)) if path else base
            else:
                return
            if isa in ("PBXGroup", "PBXVariantGroup", "XCVersionGroup"):
                for child in obj.get("children", []):
                    walk(child, here)
            elif isa == "PBXFileReference":
                members.add(here)
            elif isa == "PBXFileSystemSynchronizedRootGroup":
                synced.append(here)

        walk(root["mainGroup"], proj_dir or ".")
    return members, synced, ok


def membership(path, members, synced, package_dirs, ok):
    if path in members:
        return True
    if any(path.startswith(folder.rstrip("/") + "/") for folder in synced):
        return True
    if any(path.startswith(d + "/") or d == "" for d in package_dirs):
        return True
    return False if ok else None


def lineage(name, supers, roots):
    seen = set()
    while name in supers and name not in seen:
        seen.add(name)
        parent = supers[name].split(".")[-1]
        if parent in roots:
            return parent
        name = parent
    return None


def complexity(lines, flags, from_ib):
    heavy = sum(1 for _, w in flags if w == 2)
    light = sum(w for _, w in flags if w == 1)
    by_lines = 0 if lines <= 150 else 1 if lines <= 400 else 2 if lines <= 800 else 3
    by_flags = 3 if heavy >= 2 else 2 if heavy == 1 else 1 if light >= 2 else 0
    by_ib = 1 if from_ib else 0
    return ORDER[max(by_lines, by_flags, by_ib)]


def dependencies(repo, files):
    deps = set()
    for path in files:
        if path.endswith("Package.resolved"):
            try:
                data = json.loads(read(repo, path))
            except ValueError:
                continue
            pins = data.get("pins") or data.get("object", {}).get("pins", [])
            for pin in pins:
                deps.add(pin.get("identity") or pin.get("package") or "?")
        elif path.endswith("Podfile.lock"):
            text = read(repo, path).split("\nDEPENDENCIES:")[0]
            deps.update(re.findall(r"^  - ([\w.+-]+)", text, re.M))
        elif path.endswith("Cartfile.resolved"):
            deps.update(re.findall(r'^\w+ "([^"]+)"', read(repo, path), re.M))
    return sorted(deps, key=str.lower)


IB_CODE_RE = re.compile(r"instantiateViewController|UIStoryboard\(|UINib\(|loadNibNamed|@IBOutlet|@IBAction")
NIB_NAME_RE = re.compile(r'nibName:\s*(?:"(\w+)"|String\(describing:\s*(\w+)(?:\.self)?\)|(Self)\b|(\w+)\.self)')
CONTAINER_ROOTS = {"UITabBarController", "UINavigationController", "UISplitViewController", "UIPageViewController"}
UIKIT_EXTENSION_RE = re.compile(r"\bextension\s+(?:UIViewController|UINavigationController|UITabBarController|UIWindow|UIApplication)\b[^{]*\{")
VENDORED = ["ThirdParty/*", "*/ThirdParty/*", "ThirdParties/*", "*/ThirdParties/*", "Vendor/*", "*/Vendor/*",
            "vendor/*", "*/vendor/*", "External/*", "*/External/*"]
NAVIGATION_RE = re.compile(r"pushViewController|present\(|setViewControllers|UINavigationController|showDetailViewController|show\(")


def class_body(text, name):
    """Return (body text, line count) of `class name`, or the whole file when it cannot be delimited."""
    match = re.search(r"\bclass\s+" + re.escape(name) + r"\b", text)
    if not match:
        return text, text.count("\n") + 1
    start = text.find("{", match.end())
    if start == -1:
        return text, text.count("\n") + 1
    depth, i = 0, start
    while i < len(text):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                body = text[match.start():i + 1]
                return body, body.count("\n") + 1
        elif c == '"':  # skip simple string literals so braces in strings do not count
            end = text.find('"', i + 1)
            while end != -1 and text[end - 1] == "\\":
                end = text.find('"', end + 1)
            i = end if end != -1 else i
        i += 1
    return text[match.start():], text[match.start():].count("\n") + 1


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--exclude", action="append", default=[],
                        help="extra glob of tracked paths to skip, such as vendored sources; tests, previews, Pods, "
                             "Carthage, binary frameworks, and ThirdParty/ThirdParties/Vendor/External folders "
                             "are skipped by default")
    parser.add_argument("--include-vendored", action="store_true",
                        help="do not skip ThirdParty/ThirdParties/Vendor/External folders")
    args = parser.parse_args()
    repo = os.path.abspath(args.repo)
    all_files = git_files(repo)
    default_excludes = ["*Tests/*", "*Tests.swift", "*UITests/*", "Pods/*", "Carthage/*", "*/Preview Content/*",
                        "*.xcframework/*", "*.framework/*"]
    vendored = [] if args.include_vendored else VENDORED
    vendored_roots = set()
    for f in all_files:
        if any(fnmatch.fnmatch(f, g) for g in vendored):
            parts = f.split("/")
            for i, part in enumerate(parts[:-1]):
                if part in ("ThirdParty", "ThirdParties", "Vendor", "vendor", "External"):
                    vendored_roots.add("/".join(parts[:i + 1]))
                    break
    vendored_roots = sorted(vendored_roots)
    files = [f for f in all_files if not any(fnmatch.fnmatch(f, g) for g in default_excludes + vendored + args.exclude)]
    members, synced, ok = project_members(repo, all_files)
    package_dirs = [os.path.dirname(f) for f in all_files if os.path.basename(f) == "Package.swift"]

    texts, in_proj = {}, {}
    for path in files:
        if path.endswith((".swift", ".h", ".m", ".storyboard", ".xib")):
            texts[path] = read(repo, path)
            in_proj[path] = membership(path, members, synced, package_dirs, ok)
    live_texts = {p: t for p, t in texts.items() if in_proj.get(p) is not False}

    storyboards, not_in_project, scene_of = [], [], defaultdict(list)
    for path, text in texts.items():
        if not path.endswith((".storyboard", ".xib")):
            continue
        if in_proj.get(path) is False:
            not_in_project.append(path)
            continue
        classes = sorted(set(re.findall(r'customClass="(\w+)"', text)))
        for name in classes:
            scene_of[name].append(path)
        storyboards.append({
            "file": path,
            "scenes": len(re.findall(r"<scene\b", text)) or (1 if path.endswith(".xib") else 0),
            "custom_classes": classes,
            "segues": len(re.findall(r"<segue\b", text)),
            "launch_screen": "LaunchScreen" in os.path.basename(path),
        })

    xib_names = {os.path.basename(s["file"])[:-4] for s in storyboards if s["file"].endswith(".xib")}
    ui_test_files = [f for f in all_files if re.search(r"UITests?/", f) and f.endswith(".swift")]

    # Class definitions; a name defined in several files keeps every definition.
    definitions = defaultdict(list)
    for path, text in texts.items():
        if path.endswith((".swift", ".h", ".m")):
            regex = CLASS_RE if path.endswith(".swift") else OBJC_RE
            for name, parent in regex.findall(text):
                definitions[name].append((path, parent))
    duplicates = {n: [p for p, _ in d] for n, d in definitions.items()
                  if len({p for p, _ in d}) > 1 and n != "Coordinator"}

    def live(defs):
        for path, parent in defs:
            if in_proj.get(path) is not False:
                return path, parent
        return defs[0]

    supers = {n: live(d)[1] for n, d in definitions.items()}
    descendants = Counter()
    for name in supers:
        seen, parent = set(), supers[name].split(".")[-1]
        while parent in supers and parent not in seen:
            seen.add(parent)
            descendants[parent] += 1
            parent = supers[parent].split(".")[-1]

    ref_cache = {}

    def referencing_files(word, exclude):
        if word not in ref_cache:
            rx = re.compile(r"\b" + re.escape(word) + r"\b")
            ref_cache[word] = [p for p, t in live_texts.items() if rx.search(t)]
        return [p for p in ref_cache[word] if p not in exclude]

    # First pass: every UIKit class with its body.
    info, orphans = {}, []
    for name, defs in definitions.items():
        path, parent = live(defs)
        vc_root = parent if parent in VC_ROOTS else lineage(name, supers, VC_ROOTS)
        view_root = None if vc_root else (parent if parent in VIEW_ROOTS else lineage(name, supers, VIEW_ROOTS))
        if not (vc_root or view_root):
            continue
        for other, _ in defs:
            if in_proj.get(other) is False and (other != path or in_proj.get(path) is False):
                orphans.append({"class": name, "file": other})
        if in_proj.get(path) is False:
            continue
        body, lines = class_body(texts[path], name) if path.endswith(".swift") else (texts[path], texts[path].count("\n") + 1)
        info[name] = {"path": path, "parent": parent, "vc_root": vc_root, "view_root": view_root, "body": body,
                      "lines": lines, "own": {p for p, _ in defs}}

    controllers, views = [], []
    for name, c in info.items():
        path, body = c["path"], c["body"]
        refs = referencing_files(name, c["own"])
        item = {"class": name, "file": path, "lines": c["lines"],
                "language": "objc" if path.endswith((".m", ".h")) else "swift",
                "superclass": c["parent"], "uikit_base": c["vc_root"] or c["view_root"],
                "subclasses": descendants.get(name, 0), "referenced_by": len(refs), "referenced_from": refs}
        if not c["vc_root"]:
            item["flags"] = [f for f, rx, _ in FLAGS if re.search(rx, body)]
            item["role"] = "base class" if descendants.get(name, 0) >= 2 else "view"
            item["shared"] = len(refs) >= 3
            views.append(item)
            continue

        # Size: the class body, plus a dedicated root view and cells only this screen registers.
        extra, related, related_bodies = 0, [], []
        queue, seen_views, owners = [(body, path)], set(), {path}
        for _ in range(2):  # the controller, then the views it owns
            next_queue = []
            for text_part, owner in queue:
                candidates = re.findall(r"\bview\s*=\s*(\w+)\(", text_part)
                candidates += re.findall(r"\bview\s+as[!?]?\s+(\w+)", text_part)
                candidates += re.findall(r"register\(\s*(?:cellType:\s*)?(\w+)\.self", text_part)
                candidates += re.findall(r'register\(\s*UINib\(\s*nibName:\s*"(\w+)"', text_part)
                for other in dict.fromkeys(candidates):
                    if other in seen_views or other not in info or info[other]["vc_root"]:
                        continue
                    users = referencing_files(other, info[other]["own"])
                    if all(u in owners or u.endswith((".xib", ".storyboard")) for u in users):
                        seen_views.add(other)
                        extra += info[other]["lines"]
                        related.append(other)
                        related_bodies.append(info[other]["body"])
                        owners.add(info[other]["path"])
                        next_queue.append((info[other]["body"], info[other]["path"]))
            queue = next_queue
        combined = "\n".join([body] + related_bodies)
        flags = [(f, w) for f, rx, w in FLAGS if re.search(rx, combined)]
        scenes = scene_of.get(name, [])
        # Interface Builder: outlets, storyboard or XIB loading, or a nibName whose XIB exists.
        nib_names = set()
        for literal, described, self_ref, dot_self in NIB_NAME_RE.findall(body):
            nib_names.add(literal or described or dot_self or (name if self_ref else ""))
        nib_exists = any(n and n in xib_names for n in nib_names)
        from_ib = bool(IB_CODE_RE.search(body)) or bool(scenes) or (nib_exists and "func loadView" not in body)

        # Entry points: functions in UIKit extensions in the same file (for example `presentSelectionSheet`).
        outside = texts[path].replace(body, "")
        entry_funcs = []
        for ext in UIKIT_EXTENSION_RE.finditer(outside):
            ext_body, _ = class_body(outside[ext.start():].replace("extension", "class _Ext", 1), "_Ext")
            entry_funcs += [f for f in re.findall(r"(?<!override )func\s+(\w+)", ext_body) if len(f) > 3]
        entry_refs = sorted({p for f in entry_funcs for p in referencing_files(f, c["own"])
                             if re.search(r"\b" + re.escape(f) + r"\s*\(", live_texts[p])})

        hosts_swiftui = bool(re.search(r"\bUIHostingController\b", body))
        subs = descendants.get(name, 0)
        if subs >= 2 or (subs == 1 and "Base" in name):
            role = "base class"
        elif hosts_swiftui:
            role = "SwiftUI host"
        elif c["vc_root"] in CONTAINER_ROOTS and c["vc_root"] != "UIPageViewController":
            role = "container"
        else:
            role = "screen"
        has_view_model = bool(re.search(r"\b\w*(ViewModel|Presenter|Interactor|Store)\b", body))
        identifiers = len(re.findall(r"accessibilityIdentifier", combined))
        item.update({
            "lines": c["lines"] + extra, "class_lines": c["lines"], "related_views": related,
            "flags": [f for f, _ in flags], "interface_builder": from_ib, "storyboards": scenes,
            "role": role, "complexity": complexity(c["lines"] + extra, flags, from_ib),
            "entry_point_refs": entry_refs, "has_view_model": has_view_model,
            "accessibility_identifiers": identifiers,
            "possibly_unreferenced": not refs and not entry_refs and descendants.get(name, 0) == 0,
        })
        controllers.append(item)

    bridging = Counter()
    flag_files = defaultdict(set)
    coordinators = {}
    swift_texts = {p: t for p, t in live_texts.items() if p.endswith(".swift")}
    for path, text in swift_texts.items():
        if "import SwiftUI" in text:
            bridging["files importing SwiftUI"] += 1
        bridging["UIHostingController uses"] += len(re.findall(r"\bUIHostingController\b", text))
        bridging["UIViewRepresentable types"] += len(re.findall(r"[:,]\s*UIViewRepresentable\b", text))
        bridging["UIViewControllerRepresentable types"] += len(re.findall(r"[:,]\s*UIViewControllerRepresentable\b", text))
        for flag, rx, _ in FLAGS:
            if re.search(rx, text):
                flag_files[flag].add(path)
        for kind, name in COORDINATOR_RE.findall(text):
            if name == "Coordinator" or kind == "protocol":  # representable coordinators and protocols
                continue
            body, _ = class_body(text, name) if kind == "class" else (text, 0)
            coordinators[name] = "navigation" if NAVIGATION_RE.search(body) else "service"

    all_text = "\n".join(swift_texts.values())
    lifecycle = {
        "swiftui_app": bool(re.search(r"@main\s+struct\s+\w+\s*:\s*App\b", all_text)),
        "app_delegate": bool(re.search(r"UIApplicationDelegate", all_text)),
        "scene_delegate": bool(re.search(r"UIWindowSceneDelegate", all_text)),
        "main_storyboard": any("UIMainStoryboardFile" in read(repo, f) or "UISceneStoryboardFile" in read(repo, f)
                               for f in files if f.endswith("Info.plist")),
        "coordinators": dict(sorted(coordinators.items())),
        "objc_files": sum(1 for p in live_texts if p.endswith(".m")),
    }

    screens = [c for c in controllers if c["role"] == "screen"]
    shared = sorted((v for v in views if v.get("shared")), key=lambda v: -v["referenced_by"])
    result = {
        "repo": repo,
        "membership": "project.pbxproj" if ok else "unknown (plutil failed)",
        "synchronized_folders": synced,
        "vendored_folders_skipped": vendored_roots,
        "complexity_rules": COMPLEXITY,
        "view_controllers": sorted(controllers, key=lambda c: (c["file"], c["class"])),
        "uikit_views": sorted(views, key=lambda v: (v["file"], v["class"])),
        "storyboards_and_xibs": sorted(storyboards, key=lambda s: s["file"]),
        "not_in_project": sorted(set(not_in_project + [o["file"] for o in orphans])),
        "duplicate_class_names": {n: p for n, p in duplicates.items()
                                  if n in info or any(o["class"] == n for o in orphans)},
        "dependencies": dependencies(repo, all_files),
        "bridging": dict(bridging),
        "lifecycle": lifecycle,
        "files_per_flag": {flag: sorted(paths) for flag, paths in sorted(flag_files.items())},
        "totals": {
            "screens": len(screens),
            "screens_by_complexity": {k: sum(1 for c in screens if c["complexity"] == k) for k in ORDER},
            "screen_lines": sum(c["lines"] for c in screens),
            "swiftui_hosts": [c["class"] for c in controllers if c["role"] == "SwiftUI host"],
            "containers": [c["class"] for c in controllers if c["role"] == "container"],
            "screens_without_view_model": sum(1 for c in screens if not c["has_view_model"]),
            "ui_test_files": len(ui_test_files),
            "base_classes": [f"{c['class']} ({c['subclasses']} subclasses)" for c in controllers + views
                             if c["role"] == "base class"],
            "possibly_unreferenced_controllers": [c["class"] for c in controllers if c["possibly_unreferenced"]],
            "uikit_views": len(views),
            "shared_views": [f"{v['class']} ({v['referenced_by']} files)" for v in shared],
            "navigation_coordinators": [n for n, k in coordinators.items() if k == "navigation"],
            "storyboard_scenes": sum(s["scenes"] for s in storyboards
                                     if s["file"].endswith(".storyboard") and not s["launch_screen"]),
            "storyboard_segues": sum(s["segues"] for s in storyboards),
            "xibs": sum(1 for s in storyboards if s["file"].endswith(".xib")),
        },
    }
    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    t = result["totals"]
    print(f"Repository: {repo}")
    print(f"Project membership: {result['membership']}; synchronized folders: {synced or 'none'}")
    if vendored_roots:
        print(f"Vendored folders skipped (use --include-vendored to scan them): {', '.join(vendored_roots)}")
    print(f"Screens to plan: {t['screens']} ({t['screen_lines']} lines incl. dedicated views and cells), "
          f"by complexity {t['screens_by_complexity']}")
    print(f"Already SwiftUI behind a UIKit host: {', '.join(t['swiftui_hosts']) or 'none'}")
    print(f"Base classes (foundation work): {', '.join(t['base_classes']) or 'none'}")
    print(f"Containers (navigation work): {', '.join(t['containers']) or 'none'}")
    print(f"Screens without a view model, presenter, or store (MVC): {t['screens_without_view_model']} of {t['screens']}")
    print(f"UI test files: {t['ui_test_files']}")
    print(f"Possibly unreferenced controllers (check entry points before removing): "
          f"{', '.join(t['possibly_unreferenced_controllers']) or 'none'}")
    print(f"UIKit views and cells: {t['uikit_views']}; shared by 3+ files: {', '.join(t['shared_views']) or 'none'}")
    print(f"Storyboard scenes (no launch screen): {t['storyboard_scenes']}, segues: {t['storyboard_segues']}, XIBs: {t['xibs']}")
    for s in result["storyboards_and_xibs"]:
        if s["file"].endswith(".storyboard") and not s["launch_screen"]:
            print(f"  {s['file']}: {s['scenes']} scenes, {s['segues']} segues")
    if result["not_in_project"]:
        print(f"Not in any Xcode project or package (left out): {', '.join(result['not_in_project'])}")
    if result["duplicate_class_names"]:
        print(f"UIKit class names defined in several files: {result['duplicate_class_names']}")
    print(f"Bridging and SwiftUI: {result['bridging']}")
    print(f"Lifecycle: {lifecycle}")
    print(f"Dependencies: {', '.join(result['dependencies']) or 'none'}")
    print("\nView controllers (class, lines incl. related views, IB = storyboard/XIB or IB code, refs = other files):")
    for c in result["view_controllers"]:
        ib = " IB" if c["interface_builder"] else ""
        if c["role"] == "base class":
            role = f", base class of {c['subclasses']}"
        elif c["role"] == "SwiftUI host":
            role = ", SwiftUI host"
        elif c["role"] == "container":
            role = ", container"
        else:
            role = f", base of {c['subclasses']}" if c["subclasses"] else ""
        unref = ", POSSIBLY UNREFERENCED" if c["possibly_unreferenced"] else ""
        mvc = ", MVC" if c["role"] == "screen" and not c["has_view_model"] else ""
        ids = f", {c['accessibility_identifiers']} a11y ids" if c["accessibility_identifiers"] else ""
        entry = f", entry points used in {len(c['entry_point_refs'])} files" if c["entry_point_refs"] and not c["referenced_by"] else ""
        rel = f" + {', '.join(c['related_views'])}" if c["related_views"] else ""
        flags = f" [{', '.join(c['flags'])}]" if c["flags"] else ""
        print(f"  {c['complexity']:<2} {c['class']}{rel} ({c['uikit_base']}, {c['lines']} lines{ib}, refs {c['referenced_by']}"
              f"{role}{mvc}{ids}{entry}{unref}) {c['file']}{flags}")
    print("\nFiles per UIKit-only API or pattern (file counts):")
    for flag, paths in result["files_per_flag"].items():
        print(f"  {flag}: {len(paths)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
