#!/usr/bin/env python3
"""Inventory the UIKit user interface of an iOS repository for a SwiftUI migration plan.

Reads only git-tracked files and the Xcode project files (with `plutil`). It finds the
main app target (the application target with the most source files) and scopes the
inventory to its project and to local Swift packages; other Xcode projects in the
repository (developer tools, samples) are reported but not counted. It lists view
controllers (including subclasses of third-party controllers such as MessageKit),
UIKit views and cells, storyboards and XIBs, UIKit-only APIs, base classes,
containers, controllers that embed SwiftUI, MVC screens, shared views, possibly
unused files, dependencies, and the app lifecycle of the main app target. Every
screen gets a complexity class (see COMPLEXITY and the conversion guide).

Path comparison follows the file system: case-insensitive volumes (the macOS
default) match `arsenal/` and `Arsenal/` as one folder.

Usage: uikit_inventory.py --repo PATH [--json] [--exclude GLOB ...] [--include-vendored]
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
    "UIAlertController", "UIInputViewController", "UIDocumentBrowserViewController", "UIHostingController",
    # Apple framework controllers outside UIKit
    "AVPlayerViewController", "SFSafariViewController", "QLPreviewController", "MFMailComposeViewController",
    "MFMessageComposeViewController", "UIImagePickerController", "PHPickerViewController", "CNContactViewController",
    "EKEventEditViewController", "UIActivityViewController", "UIDocumentPickerViewController",
}
CONTAINER_ROOTS = {"UITabBarController", "UINavigationController", "UISplitViewController", "UIPageViewController"}
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
    ("third-party base class", r"$^", 2),  # set from the class hierarchy, never by regex
    ("web view", r"\bWKWebView\b", 1),
    ("map with overlays", r"\bMKOverlayRenderer\b|rendererFor\s*overlay|\bMKTileOverlay\b|\bMKPolyline\b|\bMKPolygon\b|\bMKCircle\b", 2),
    ("map", r"\bMKMapView\b", 1),
    ("video player", r"\bAVPlayerViewController\b|\bAVPlayerLayer\b", 1),
    ("camera or image picker", r"\bUIImagePickerController\b|\bAVCaptureSession\b|\bPHPickerViewController\b", 2),
    ("mail or message composer", r"\bMFMailComposeViewController\b|\bMFMessageComposeViewController\b", 1),
    ("document picker", r"\bUIDocumentPickerViewController\b|\bUIDocumentInteractionController\b", 1),
    ("PDF", r"\bPDFView\b", 1),
    ("page view controller", r"\bUIPageViewController\b", 1),
    ("custom transition", r"UIViewControllerAnimatedTransitioning|UIViewControllerTransitioningDelegate|:\s*UIPresentationController\s*\{|func animateTransition\(", 2),
    # Layout subclasses defined in the project are added per screen from the class hierarchy:
    # a UICollectionViewLayout subclass is weight 2, a flow-layout subclass weight 1.
    ("compositional layout", r"\bUICollectionViewCompositionalLayout\b|\bNSCollectionLayoutSection\b", 1),
    ("diffable data source", r"UITableViewDiffableDataSource|UICollectionViewDiffableDataSource", 1),
    ("drag and drop", r"UIDragInteraction|UIDropInteraction|dragDelegate|dropDelegate", 2),
    ("rich text editing", r"\bUITextView\b.*(attributedText|textStorage)|NSTextStorage|NSLayoutManager|TextKit", 2),
    ("keyboard handling", r"keyboardWillShowNotification|keyboardWillChangeFrameNotification|IQKeyboardManager", 1),
    ("custom drawing", r"override func draw\(_|CAShapeLayer|CADisplayLink|UIGraphicsImageRenderer", 1),
    ("gesture recognizers", r"UI(Pan|Pinch|Rotation|Swipe|LongPress|ScreenEdgePan)GestureRecognizer", 1),
    ("child view controllers", r"addChild\(|willMove\(toParent|didMove\(toParent", 1),
    ("search controller", r"\bUISearchController\b", 1),
    ("ad banners", r"\bGADBannerView\b|\bGAMBannerView\b|\bAdManagerBannerView\b|\bBannerView\b|GoogleMobileAds", 1),
    ("RxSwift or RxCocoa", r"import RxSwift|import RxCocoa|\bDisposeBag\b|\.rx\.|\bBehaviorRelay\b|\bPublishRelay\b|\bPublishSubject\b", 2),
    ("remote images", r"\bsd_setImage\b|\bSDWebImage|\.kf\.setImage|\bKingfisher\b|\bNuke\b", 0),
    ("auto layout in code", r"NSLayoutConstraint|\.snp\.|SnapKit|anchor\(equalTo|constraint\(equalTo", 0),
    ("imports Combine", r"import Combine", 0),
    ("context menu or swipe actions", r"UIContextMenuConfiguration|UISwipeActionsConfiguration|trailingSwipeActionsConfiguration", 0),
    ("pull to refresh", r"\bUIRefreshControl\b", 0),
]
CLASS_RE = re.compile(r"^\s*(?:@\w+(?:\([^)]*\))?\s+)*(?:(?:public|open|internal|private|fileprivate|final)\s+)*class\s+(\w+)\s*(?:<[^>]*>)?\s*:\s*([\w.]+)", re.M)
OBJC_RE = re.compile(r"@interface\s+(\w+)\s*:\s*(\w+)")
COORDINATOR_RE = re.compile(r"^\s*(?:(?:public|open|internal|private|fileprivate|final)\s+)*(class|struct|actor|protocol)\s+(\w*Coordinator(?:ing|Protocol)?)\b", re.M)
# Loading another controller from a storyboard is not this controller's Interface Builder layout.
IB_CODE_RE = re.compile(r"UINib\(|loadNibNamed|@IBOutlet|@IBAction")
NIB_NAME_RE = re.compile(r'nibName:\s*(?:"(\w+)"|String\(describing:\s*(\w+)(?:\.self)?\)|(Self)\b|(\w+)\.self)')
UIKIT_EXTENSION_RE = re.compile(r"\bextension\s+(?:UIViewController|UINavigationController|UITabBarController|UIWindow|UIApplication)\b[^{]*\{")
# Presenting only alerts is not screen navigation.
NAVIGATION_RE = re.compile(r"pushViewController|setViewControllers|showDetailViewController|UINavigationController\(|present\((?![^\n]*[Aa]lert)")
HELPER_RE = re.compile(r"(DataSource|Delegate|Provider|Adapter|Factory|Builder)$")
VENDORED_NAMES = ("ThirdParty", "ThirdParties", "Vendor", "vendor", "External")
ORDER = ["S", "M", "L", "XL"]
COMPLEXITY = """Size = the class with its extensions, its root view in full, and the views, cells, and data-source
helpers it uses (reached through code and Interface Builder custom classes): in full when only it uses them, half when
two controllers do, and not at all when three or more do (those are shared foundation).
A size within 5% above a boundary is marked `near_boundary`.
S: up to 150 lines, at most one flag of weight 1, no flag of weight 2, and not from Interface Builder unless both the class (80 lines or less) and its layout (15 elements or less) are small.
M: up to 400 lines, or from a storyboard or XIB with a class over 80 lines or more than 15 layout elements, or flags of weight 1 adding up to 2 or more.
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


def case_insensitive(repo):
    return os.path.exists(os.path.join(repo, ".git")) and os.path.exists(os.path.join(repo, ".GIT"))


def block_at(text, begin, after):
    """Return the text from `begin` to the brace that closes the first `{` after `after`, or None."""
    start = text.find("{", after)
    if start == -1:
        return None
    depth, i = 0, start
    while i < len(text):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[begin:i + 1]
        elif c == '"':
            end = text.find('"', i + 1)
            while end != -1 and text[end - 1] == "\\":
                end = text.find('"', end + 1)
            i = end if end != -1 else i
        i += 1
    return None


def extensions_of(texts):
    """Map type name -> list of extension blocks (text) found in the given Swift files."""
    found = defaultdict(list)
    for path, text in texts.items():
        if not path.endswith(".swift"):
            continue
        for match in re.finditer(r"^\s*(?:(?:public|private|fileprivate|internal)\s+)?extension\s+(\w+)\b", text, re.M):
            block = block_at(text, match.start(), match.end())
            if block:
                found[match.group(1)].append(block)
    return found


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
        elif c == '"':
            end = text.find('"', i + 1)
            while end != -1 and text[end - 1] == "\\":
                end = text.find('"', end + 1)
            i = end if end != -1 else i
        i += 1
    return text[match.start():], text[match.start():].count("\n") + 1


def load_projects(repo, files, key):
    """Parse every tracked project.pbxproj: group-tree files, synchronized folders, and native targets."""
    projects, ok = [], True
    for pbx in [f for f in files if f.endswith(".xcodeproj/project.pbxproj")]:
        proj_dir = os.path.dirname(os.path.dirname(pbx))
        try:
            data = json.loads(subprocess.run(["plutil", "-convert", "json", "-o", "-", os.path.join(repo, pbx)],
                                             capture_output=True, text=True, check=True).stdout)
            objects, root = data["objects"], data["objects"][data["rootObject"]]
        except (OSError, subprocess.CalledProcessError, ValueError, KeyError):
            ok = False
            continue
        paths, synced = {}, {}

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
                paths[oid] = here
                for child in obj.get("children", []):
                    walk(child, here)
            elif isa == "PBXFileReference":
                paths[oid] = here
            elif isa == "PBXFileSystemSynchronizedRootGroup":
                synced[oid] = here

        walk(root["mainGroup"], proj_dir or ".")
        targets = []
        for tid in root.get("targets", []):
            target = objects.get(tid, {})
            if target.get("isa") != "PBXNativeTarget":
                continue
            sources = set()
            for phase in target.get("buildPhases", []):
                for build_file in objects.get(phase, {}).get("files", []):
                    ref = objects.get(build_file, {}).get("fileRef")
                    for child in [ref] + objects.get(ref, {}).get("children", []):
                        if child in paths:
                            sources.add(key(paths[child]))
            settings = {}
            config_list = objects.get(target.get("buildConfigurationList"), {})
            for config in config_list.get("buildConfigurations", []):
                for k, v in objects.get(config, {}).get("buildSettings", {}).items():
                    settings.setdefault(k, v)
            targets.append({
                "name": target.get("name"),
                "type": target.get("productType", "").replace("com.apple.product-type.", ""),
                "sources": sources,
                "synced": [key(synced[g]) for g in target.get("fileSystemSynchronizedGroups", []) if g in synced],
                "settings": settings,
            })
        projects.append({"file": pbx, "dir": proj_dir, "members": {key(p) for p in paths.values()},
                         "synced": [key(p) for p in synced.values()], "targets": targets})
    return projects, ok


IB_ELEMENT_RE = re.compile(r"<(?:label|button|textField|textView|imageView|tableView|collectionView|switch|slider|"
                           r"segmentedControl|stackView|scrollView|view|mapView|webView|pageControl|activityIndicatorView)\b")


def ib_elements(text, name):
    """Count layout elements in the storyboard scene or XIB that belongs to class `name`."""
    if "<scene" in text:
        for scene in re.findall(r"<scene\b.*?</scene>", text, re.S):
            if f'customClass="{name}"' in scene:
                return len(IB_ELEMENT_RE.findall(scene))
        return 0
    return len(IB_ELEMENT_RE.findall(text))


def complexity(lines, class_lines, flags, from_ib, elements=0):
    heavy = sum(1 for _, w in flags if w == 2)
    light = sum(w for _, w in flags if w == 1)
    by_lines = 0 if lines <= 150 else 1 if lines <= 400 else 2 if lines <= 800 else 3
    by_flags = 3 if heavy >= 2 else 2 if heavy == 1 else 1 if light >= 2 else 0
    by_ib = 1 if from_ib and (class_lines > 80 or elements > 15) else 0
    return ORDER[max(by_lines, by_flags, by_ib)]


def dependencies(repo, files):
    deps = set()
    for path in files:
        if path.endswith("Package.resolved"):
            try:
                data = json.loads(read(repo, path))
            except ValueError:
                continue
            for pin in data.get("pins") or data.get("object", {}).get("pins", []):
                deps.add(pin.get("identity") or pin.get("package") or "?")
        elif path.endswith("Podfile.lock"):
            text = read(repo, path).split("\nDEPENDENCIES:")[0]
            deps.update(re.findall(r"^  - ([\w.+-]+)", text, re.M))
        elif path.endswith("Cartfile.resolved"):
            deps.update(re.findall(r'^\w+ "([^"]+)"', read(repo, path), re.M))
    return sorted(deps, key=str.lower)


COMPOSITION_RES = [
    re.compile(r"\b([A-Z]\w+)\s*\("),                 # created: Name(...)
    re.compile(r":\s*\[?\s*([A-Z]\w+)\s*\]?[!?]?"),   # stored or passed: let x: Name, [Name]
    re.compile(r"\b([A-Z]\w+)\.self\b"),              # registered: Name.self
    re.compile(r"<\s*([A-Z]\w+)\s*>"),                 # generic argument
    re.compile(r'customClass="(\w+)"'),                 # Interface Builder
]


def composed_types(text):
    """Type names a piece of code creates, stores, or registers; casts and comments do not count."""
    code = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    code = re.sub(r"//[^\n]*", "", code)
    found = []
    for rx in COMPOSITION_RES:
        found += rx.findall(code)
    return found


def commented_out(text):
    code = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    code = re.sub(r"//[^\n]*", "", code)
    return not code.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--exclude", action="append", default=[],
                        help="extra glob of tracked paths to skip; tests, previews, Pods, Carthage, binary frameworks, "
                             "and ThirdParty/ThirdParties/Vendor/External folders are skipped by default")
    parser.add_argument("--explain", metavar="CLASS",
                        help="print how each controller reaches CLASS (its chain of views and helpers), then exit")
    parser.add_argument("--include-vendored", action="store_true",
                        help="do not skip ThirdParty/ThirdParties/Vendor/External folders")
    args = parser.parse_args()
    repo = os.path.abspath(args.repo)
    ci = case_insensitive(repo)
    key = (lambda p: os.path.normpath(p).lower()) if ci else os.path.normpath

    all_files = git_files(repo)
    default_excludes = ["*Tests/*", "*Tests.swift", "*UITests/*", "Pods/*", "Carthage/*", "*/Preview Content/*",
                        "*.xcframework/*", "*.framework/*"]
    vendored_roots = set()
    if not args.include_vendored:
        for f in all_files:
            parts = f.split("/")
            for i, part in enumerate(parts[:-1]):
                if part in VENDORED_NAMES:
                    vendored_roots.add("/".join(parts[:i + 1]))
                    break
    files = [f for f in all_files
             if not any(fnmatch.fnmatch(f, g) for g in default_excludes + args.exclude)
             and not any(f.startswith(v + "/") for v in vendored_roots)]

    projects, ok = load_projects(repo, all_files, key)
    apps = [(p, t) for p in projects for t in p["targets"] if t["type"] == "application"]
    main_project, main_app = max(apps, key=lambda pt: len(pt[1]["sources"])) if apps else (None, None)
    package_dirs = [key(os.path.dirname(f) or ".") for f in all_files if os.path.basename(f) == "Package.swift"]

    def scope(path):
        k = key(path)
        if any(d == "." or k.startswith(d + "/") for d in package_dirs):
            return "package"
        for project in projects:
            if k in project["members"] or any(k.startswith(s + "/") for s in project["synced"]):
                return "main" if main_project is None or project is main_project else "other:" + project["file"]
        return "none" if ok and projects else "unknown"

    def targets_of(path):
        if not main_project:
            return []
        k = key(path)
        return [t["name"] for t in main_project["targets"]
                if k in t["sources"] or any(k.startswith(s + "/") for s in t["synced"])]

    texts, where = {}, {}
    for path in files:
        if path.endswith((".swift", ".h", ".m", ".storyboard", ".xib")):
            texts[path] = read(repo, path)
            where[path] = scope(path)

    def in_scope(p):
        return where.get(p) in ("main", "package", "unknown")

    live_texts = {p: t for p, t in texts.items() if in_scope(p)}
    swift_live = {p: t for p, t in live_texts.items() if p.endswith(".swift")}
    other_projects = Counter(where[p].split(":", 1)[1] for p in where if where[p].startswith("other:"))
    not_in_project = sorted(p for p in where if where[p] == "none")
    dead_files = sorted(p for p, t in texts.items() if p.endswith(".swift") and commented_out(t))

    storyboards, scene_of = [], defaultdict(list)
    for path, text in live_texts.items():
        if not path.endswith((".storyboard", ".xib")):
            continue
        classes = sorted(set(re.findall(r'customClass="(\w+)"', text)))
        for name in classes:
            scene_of[name].append(path)
        storyboards.append({
            "file": path, "custom_classes": classes,
            "scenes": (len(re.findall(r"<scene\b", text)) - len(re.findall(r"<viewControllerPlaceholder\b", text))
                       or (1 if path.endswith(".xib") else 0)),
            "segues": len(re.findall(r"<segue\b", text)),
            "launch_screen": "LaunchScreen" in os.path.basename(path),
        })
    xib_names = {os.path.basename(s["file"])[:-4] for s in storyboards if s["file"].endswith(".xib")}

    # Lifecycle of the main app target.
    app_files = [p for p in swift_live if not main_app or main_app["name"] in targets_of(p)] or list(swift_live)
    app_text = "\n".join(swift_live[p] for p in app_files)
    settings = main_app["settings"] if main_app else {}
    plist_text = ""
    if settings.get("INFOPLIST_FILE"):
        plist_rel = re.sub(r"^\$\((SRCROOT|PROJECT_DIR)\)/", "", settings["INFOPLIST_FILE"])
        plist_text = read(repo, os.path.join(main_project["dir"], plist_rel))
    main_storyboard = bool(re.search(r"<key>UI(Main|Scene)StoryboardFile</key>\s*<string>\s*[^<\s]", plist_text)) or \
        bool(str(settings.get("INFOPLIST_KEY_UIMainStoryboardFile", "")).strip())
    lifecycle = {
        "main_app_target": f"{main_app['name']} ({main_project['file']})" if main_app else "unknown",
        "swiftui_app": bool(re.search(r"@main\s+struct\s+\w+\s*:\s*App\b", app_text)),
        "app_delegate": bool(re.search(r"UIApplicationDelegate|@UIApplicationMain", app_text)),
        "scene_delegate": bool(re.search(r"UIWindowSceneDelegate", app_text)),
        "main_storyboard": main_storyboard,
        "objc_files": sum(1 for p in live_texts if p.endswith(".m")),
    }

    definitions = defaultdict(list)
    for path, text in texts.items():
        if path.endswith((".swift", ".h", ".m")):
            regex = CLASS_RE if path.endswith(".swift") else OBJC_RE
            for name, parent in regex.findall(text):
                definitions[name].append((path, parent.split(".")[-1]))

    def live(defs):
        for path, parent in defs:
            if in_scope(path):
                return path, parent
        return defs[0]

    supers = {n: live(d)[1] for n, d in definitions.items()}
    descendants = Counter()
    for name in supers:
        seen, parent = set(), supers[name]
        while parent in supers and parent not in seen:
            seen.add(parent)
            descendants[parent] += 1
            parent = supers[parent]

    def root_of(name):
        """(UIKit or external root, is third-party): the first UIKit ancestor, or an external *Controller ancestor."""
        seen = set()
        while name in supers and name not in seen:
            seen.add(name)
            parent = supers[name]
            if parent in VC_ROOTS or parent in VIEW_ROOTS:
                return parent, False
            if parent not in supers:
                if re.search(r"Controller$", parent):
                    return parent, True
                return None, False
            name = parent
        return None, False

    def ancestors(name):
        chain, seen = [], set()
        while name in supers and name not in seen:
            seen.add(name)
            name = supers[name]
            chain.append(name)
        return chain

    ref_cache = {}

    def referencing_files(word, exclude, pool=None):
        pool = live_texts if pool is None else pool
        cache_key = (word, id(pool))
        if cache_key not in ref_cache:
            rx = re.compile(r"\b" + re.escape(word) + r"\b")
            ref_cache[cache_key] = [p for p, t in pool.items() if rx.search(t)]
        return [p for p in ref_cache[cache_key] if p not in exclude]

    info, orphans = {}, []
    extensions = extensions_of(live_texts)
    for name, defs in definitions.items():
        path, parent = live(defs)
        root, third_party = root_of(name)
        if not root:
            continue
        for other, _ in defs:
            if where.get(other) == "none":
                orphans.append({"class": name, "file": other})
        if not in_scope(path):
            continue
        if path.endswith(".swift"):
            body, lines = class_body(texts[path], name)
            # Extensions of the class, in the same file or in files such as `Name+UI.swift`, are part of its work.
            for block in extensions.get(name, []):
                body += "\n" + block
                lines += block.count("\n") + 1
        else:
            body, lines = texts[path], texts[path].count("\n") + 1
        info[name] = {"path": path, "parent": parent, "root": root, "third_party": third_party,
                      "is_vc": root in VC_ROOTS or third_party, "body": body, "lines": lines,
                      "own": {p for p, _ in defs}}

    flow_layouts = {n for n in supers if "UICollectionViewFlowLayout" in ancestors(n)}
    custom_layouts = {n for n in supers if "UICollectionViewLayout" in ancestors(n)} - flow_layouts
    # Data sources, delegates, factories, and similar helpers the screens create count as part of their work.
    helpers = {}
    for name, defs in definitions.items():
        hpath = live(defs)[0]
        if name not in info and HELPER_RE.search(name) and in_scope(hpath) and hpath.endswith(".swift"):
            hbody, hlines = class_body(texts[hpath], name)
            helpers[name] = {"path": hpath, "body": hbody, "lines": hlines}
    # Only screen-specific helpers: ones that at most two controllers mention directly.
    for h in list(helpers):
        direct = sum(1 for n, c in info.items() if c["is_vc"] and re.search(r"\b" + re.escape(h) + r"\b", c["body"]))
        if direct > 2:
            del helpers[h]
    xib_by_name = {os.path.basename(s["file"])[:-4]: s["file"] for s in storyboards if s["file"].endswith(".xib")}

    def ib_text(name, is_vc):
        """Interface Builder text that belongs to a class: its scenes and a XIB named after it."""
        parts = []
        for f in scene_of.get(name, []) if is_vc else []:
            text = live_texts.get(f, "")
            if "<scene" in text:  # only the scene whose controller is this class
                parts += [s for s in re.findall(r"<scene\b.*?</scene>", text, re.S)
                          if re.search(r'<(?:viewController|tableViewController|collectionViewController|navigationController|'
                                       r'tabBarController|pageViewController)\b[^>]*customClass="' + re.escape(name) + '"', s)]
        if name in xib_by_name:  # its own XIB, never XIBs that merely use it
            parts.append(live_texts.get(xib_by_name[name], ""))
        return "\n".join(parts)
    hosted_swiftui = set()
    for path in app_files:
        text = swift_live[path]
        if "UIHostingController" not in text:
            continue
        hosted_swiftui |= {g for g in re.findall(r"UIHostingController<(\w+)>", text) if g != "AnyView"}
        for arg in re.findall(r"UIHostingController(?:<\w+>)?\(\s*rootView:\s*(?:AnyView\(\s*)?([\w.]+)", text):
            if arg[:1].isupper():
                hosted_swiftui.add(arg.split(".")[0].split("(")[0])
            else:  # a variable: find what it is set to in the same file
                hosted_swiftui |= set(re.findall(r"\b" + re.escape(arg) + r"\s*=\s*(?:AnyView\(\s*)?([A-Z]\w+)\(", text))
    hosted_swiftui = sorted(hosted_swiftui - {"AnyView"})

    # Pass A: per controller, its root view and the views, cells, and helpers it uses, followed transitively.
    merged = {}  # controller -> the controller it is part of
    for name, c in info.items():
        parent = c["parent"]
        if c["is_vc"] and parent in info and descendants.get(parent, 0) == 1 and info[parent]["is_vc"]:
            merged[parent] = name
    for name, c in info.items():
        if not c["is_vc"] or name in merged or descendants.get(name, 0):
            continue
        same_file = [o for o, oc in info.items() if o != name and oc["is_vc"] and oc["path"] == c["path"]]
        users = {p for p in referencing_files(name, c["own"]) if not p.endswith((".xib", ".storyboard"))}
        if same_file and users <= {c["path"]} and c["lines"] <= 80:
            merged[name] = max(same_file, key=lambda o: info[o]["lines"])
    uses = {}
    for name, c in info.items():
        if not c["is_vc"]:
            continue
        root_views, cells, seen = [], [], {name}
        via = {}
        queue = [(c["body"] + "\n" + ib_text(name, True), True, name)]
        for _ in range(5):
            next_queue = []
            for part, is_controller, source in queue:
                found_roots = (re.findall(r"\bview\s*=\s*(\w+)\(", part) + re.findall(r"\bview\s+as[!?]?\s+(\w+)", part)
                               if is_controller else [])
                words = composed_types(part)
                for other in dict.fromkeys(found_roots + words):
                    if other in seen:
                        continue
                    if other in info and not info[other]["is_vc"]:
                        seen.add(other)
                        via[other] = source
                        (root_views if is_controller and other in found_roots else cells).append(other)
                        next_queue.append((info[other]["body"] + "\n" + ib_text(other, False), False, other))
                    elif other in helpers:
                        seen.add(other)
                        via[other] = source
                        cells.append(other)
                        next_queue.append((helpers[other]["body"], False, other))
            queue = next_queue
        uses[name] = (root_views, cells)
        if args.explain and args.explain in via:
            chain, node = [args.explain], args.explain
            while node in via:
                node = via[node]
                chain.append(node)
            print(" <- ".join(chain))

    if args.explain:
        return 0
    # A view is shared when three or more screens use it; shared views are foundation, not part of a screen.
    users_of = defaultdict(set)
    for name, (root_views, cells) in uses.items():
        for view in root_views + cells:
            users_of[view].add(name)
            if descendants.get(name, 0) >= 2:  # used by a base class: every subclass uses it
                users_of[view].update(f"{name}:{i}" for i in range(descendants[name]))

    def is_shared(view):
        return len(users_of[view]) >= 3

    controllers, views = [], []
    for name, c in info.items():
        path, body = c["path"], c["body"]
        ext_files = {p for p, tx in live_texts.items() if re.search(r"\bextension\s+" + re.escape(name) + r"\b", tx)
                     and len(re.findall(r"\b" + re.escape(name) + r"\b", tx)) == len(re.findall(r"\bextension\s+" + re.escape(name) + r"\b", tx))}
        own_files = c["own"] | ext_files | ({xib_by_name[name]} if name in xib_by_name else set())
        refs = referencing_files(name, own_files)
        subs = descendants.get(name, 0)
        item = {"class": name, "file": path, "targets": targets_of(path), "superclass": c["parent"],
                "uikit_base": c["root"], "subclasses": subs, "referenced_by": len(refs), "referenced_from": refs,
                "language": "objc" if path.endswith((".m", ".h")) else "swift"}
        if not c["is_vc"]:
            used_by = sorted(users_of.get(name, set()))
            item.update({"lines": c["lines"],
                         "flags": [f"{f} ({w})" for f, rx, w in FLAGS if re.search(rx, body)],
                         "role": "base class" if subs >= 2 else "view",
                         "used_by_controllers": sorted({u.split(":")[0] for u in used_by}), "shared": is_shared(name)})
            views.append(item)
            continue

        root_views, cells = uses[name]
        # Root views count fully; a cell or view used by two controllers counts half; shared ones are foundation.
        own_views = root_views + [v for v in cells if not is_shared(v)]
        part_of = lambda v: info[v] if v in info else helpers[v]
        merged_children = [m for m, host in merged.items() if host == name]
        extra = sum(part_of(v)["lines"] if v in root_views else part_of(v)["lines"] // max(1, len(users_of[v]))
                    for v in own_views) + sum(info[m]["lines"] for m in merged_children)
        own_imports = "\n".join(re.findall(r"^import [^\n]+", "\n".join(texts[part_of(v)["path"]] for v in own_views), re.M))
        own_text = "\n".join([body] + [part_of(v)["body"] for v in own_views]
                             + [info[m]["body"] for m in merged_children] + [own_imports])
        file_imports = "\n".join(re.findall(r"^import [^\n]+", texts[path], re.M))
        flags = [(f, w) for f, rx, w in FLAGS if re.search(rx, own_text + "\n" + file_imports)]
        if any(re.search(r"\b" + re.escape(layout) + r"\b", own_text) for layout in custom_layouts):
            flags.append(("custom collection layout", 2))
        elif any(re.search(r"\b" + re.escape(layout) + r"\b", own_text) for layout in flow_layouts):
            flags.append(("custom flow layout", 1))
        if any(f == "map with overlays" for f, _ in flags):
            flags = [(f, w) for f, w in flags if f != "map"]
        rx_flag = dict((f, rx) for f, rx, _ in FLAGS)["RxSwift or RxCocoa"]
        if any(f == "RxSwift or RxCocoa" for f, _ in flags) and not re.search(rx_flag, body + "\n" + file_imports):
            flags = [(("RxSwift in views only", 1) if f == "RxSwift or RxCocoa" else (f, w)) for f, w in flags]
        if c["third_party"]:
            flags.insert(0, ("third-party base class", 2))

        scenes = scene_of.get(name, [])
        nib_names = set()
        for literal, described, self_ref, dot_self in NIB_NAME_RE.findall(body):
            nib_names.add(literal or described or dot_self or (name if self_ref else ""))
        nib_exists = any(n and n in xib_names for n in nib_names)
        from_ib = bool(IB_CODE_RE.search(body)) or bool(scenes) or (nib_exists and "func loadView" not in body)

        outside_text = texts[path].replace(body, "")
        entry_funcs = []
        for ext in UIKIT_EXTENSION_RE.finditer(outside_text):
            ext_body = block_at(outside_text, ext.start(), ext.start()) or ""
            entry_funcs += [f for f in re.findall(r"(?<!override )func\s+(\w+)", ext_body) if len(f) > 3]
        entry_refs = sorted({p for f in entry_funcs for p in referencing_files(f, own_files)
                             if re.search(r"\b" + re.escape(f) + r"\s*\(", live_texts[p])})

        embeds_swiftui = c["root"] == "UIHostingController" or (
            "UIHostingController" in body and bool(re.search(r"addChild\(|\bview\s*=\s*\w+\.view\b", body))
            and not re.search(r"\bUITableView|\bUICollectionView", body))
        # A pager is a container when its pages are full controllers (not presented ones, not small page classes
        # in the same file); a factory that returns a base class with subclasses also builds full controllers.
        not_presented = "\n".join(l for l in body.split("\n") if not re.search(r"present\(|pushViewController|show\(", l))
        page_screens = {w for w in re.findall(r"\b([A-Z]\w+Controller)\b", not_presented)
                        if w in info and info[w]["is_vc"] and w != name and w not in ancestors(name)
                        and merged.get(w) != name and info[w]["lines"] > 80}
        for factory in set(re.findall(r"\b([A-Z]\w*Factory)\b", body)):
            for ftext in swift_live.values():
                fmatch = re.search(r"\b(?:class|struct|enum)\s+" + re.escape(factory) + r"\b", ftext)
                if fmatch:
                    fbody = block_at(ftext, fmatch.start(), fmatch.end()) or ""
                    page_screens |= {r for r in re.findall(r"->\s*(\w+)", fbody) if descendants.get(r, 0) >= 2}
                    break
        is_pager = c["root"] == "UIPageViewController" or "UIPageViewController" in body
        pages = is_pager and len(page_screens) >= 1
        # Tab-like containers set an array of two or more child controllers.
        tab_like = bool(re.search(r"(?:\bviewControllers\s*=|setViewControllers\()\s*\[[^\]]*,", body)) and not is_pager
        if subs >= 2:
            role = "base class"
        elif name in merged:
            role = f"merged into {merged[name]}"
        elif embeds_swiftui:
            role = "SwiftUI host"
        elif (c["root"] in CONTAINER_ROOTS - {"UIPageViewController"} or "TabBar" in name
              or tab_like or pages):
            role = "container"
        else:
            role = "screen"

        ib_files = set(scenes) | {s["file"] for s in storyboards
                                  if os.path.basename(s["file"])[:-4] in ({name} | set(own_views) | nib_names)}
        identifiers = len(re.findall(r"accessibilityIdentifier", own_text)) + sum(
            len(re.findall(r"<accessibility\b[^>]*\bidentifier=", live_texts.get(f, ""))) for f in ib_files)
        total = c["lines"] + extra
        # Unknown layout (outlets but no storyboard scene or XIB found) counts as large.
        elements = (sum(ib_elements(live_texts.get(f, ""), name if f in scenes else "") for f in ib_files)
                    if ib_files or not from_ib else 99)
        size_class = complexity(total, c["lines"], [], from_ib, elements)
        controller_class = complexity(c["lines"], c["lines"], [], False)
        near = any(b < total <= b * 1.05 for b in (150, 400, 800))
        item.update({
            "lines": total, "class_lines": c["lines"], "related_views": own_views,
            "shared_views_used": [v for v in cells if is_shared(v)],
            "flags": [f"{f} ({w})" for f, w in flags], "interface_builder": from_ib, "storyboards": scenes,
            "role": role, "complexity": complexity(total, c["lines"], flags, from_ib, elements),
            "class_from_size": size_class, "class_from_controller": controller_class, "near_boundary": near,
            "ib_elements": elements,
            "entry_point_refs": entry_refs,
            "has_view_model": bool(re.search(r"\b\w*(ViewModel|Presenter|Interactor|Store)\b", body)),
            "accessibility_identifiers": identifiers,
            "possibly_unreferenced": not refs and not entry_refs and subs == 0,
        })
        controllers.append(item)

    # Storyboards and XIBs that nothing loads by name.
    unused_ib = []
    for s in storyboards:
        is_board = s["file"].endswith(".storyboard")
        base = os.path.basename(s["file"])[:-len(".storyboard")] if is_board else os.path.basename(s["file"])[:-4]
        if s["launch_screen"] or (is_board and base.lower() in plist_text.lower() and lifecycle["main_storyboard"]):
            continue
        loaded = bool(referencing_files(base, {s["file"]}, swift_live)) or any(
            f'storyboardName="{base}"' in t or f'"{base}"' in t
            for p, t in live_texts.items() if p != s["file"] and p.endswith((".storyboard", ".xib")))
        if not loaded:
            unused_ib.append(s["file"])

    coordinators = {}
    for path, text in swift_live.items():
        for kind, name in COORDINATOR_RE.findall(text):
            if name == "Coordinator" or kind == "protocol":
                continue
            body, _ = class_body(text, name) if kind == "class" else (text, 0)
            coordinators[name] = "navigation" if NAVIGATION_RE.search(body) else "service"

    swiftui_files = Counter()
    for path, text in texts.items():
        if path.endswith(".swift") and "import SwiftUI" in text:
            if where[path].startswith("other:"):
                swiftui_files["other projects"] += 1
            elif in_scope(path):
                for target in targets_of(path) or ["package or no target"]:
                    swiftui_files[target] += 1
    flag_files = defaultdict(set)
    for path, text in swift_live.items():
        for flag, rx, _ in FLAGS:
            if re.search(rx, text):
                flag_files[flag].add(path)

    screens = [c for c in controllers if c["role"] == "screen"]
    ui_test_files = [f for f in all_files if re.search(r"UITests?/", f) and f.endswith(".swift")]
    result = {
        "repo": repo,
        "membership": "project.pbxproj" if ok else "unknown (plutil failed)",
        "case_insensitive_paths": ci,
        "other_projects_not_counted": dict(other_projects),
        "vendored_folders_skipped": sorted(vendored_roots),
        "complexity_rules": COMPLEXITY,
        "view_controllers": sorted(controllers, key=lambda c: (c["file"], c["class"])),
        "uikit_views": sorted(views, key=lambda v: (v["file"], v["class"])),
        "storyboards_and_xibs": sorted(storyboards, key=lambda s: s["file"]),
        "possibly_unused_storyboards_and_xibs": sorted(unused_ib),
        "not_in_project": sorted(set(not_in_project + [o["file"] for o in orphans])),
        "commented_out_files": dead_files,
        "duplicate_class_names": {n: [p for p, _ in d] for n, d in definitions.items()
                                  if len({p for p, _ in d}) > 1 and (n in info or any(o["class"] == n for o in orphans))},
        "dependencies": dependencies(repo, all_files),
        "swiftui_files_per_target": dict(swiftui_files),
        "swiftui_views_hosted_from_uikit": hosted_swiftui,
        "lifecycle": lifecycle,
        "coordinators": dict(sorted(coordinators.items())),
        "files_per_flag": {flag: sorted(paths) for flag, paths in sorted(flag_files.items())},
        "totals": {
            "screens": len(screens),
            "screens_by_complexity": {k: sum(1 for c in screens if c["complexity"] == k) for k in ORDER},
            "screen_lines": sum(c["lines"] for c in screens),
            "screens_without_view_model": sum(1 for c in screens if not c["has_view_model"]),
            "swiftui_hosts": [c["class"] for c in controllers if c["role"] == "SwiftUI host"],
            "containers": [c["class"] for c in controllers if c["role"] == "container"],
            "controller_base_classes": [f"{c['class']} ({c['subclasses']} subclasses)" for c in controllers
                                        if c["role"] == "base class"],
            "view_base_classes": [f"{v['class']} ({v['subclasses']} subclasses)" for v in views
                                  if v["role"] == "base class"],
            "possibly_unreferenced_controllers": [c["class"] for c in controllers if c["possibly_unreferenced"]],
            "possibly_unused_views": [v["class"] for v in views
                                      if not v["referenced_by"] and not v["subclasses"] and not users_of.get(v["class"])],
            "uikit_views": len(views),
            "shared_views": [f"{v['class']} ({len(users_of[v['class']])} uses)"
                             for v in sorted(views, key=lambda v: -len(users_of[v["class"]])) if v["shared"]],
            "navigation_coordinators": [n for n, k in coordinators.items() if k == "navigation"],
            "storyboard_scenes": sum(s["scenes"] for s in storyboards
                                     if s["file"].endswith(".storyboard") and not s["launch_screen"]),
            "storyboard_segues": sum(s["segues"] for s in storyboards),
            "xibs": sum(1 for s in storyboards if s["file"].endswith(".xib")),
            "ui_test_files": len(ui_test_files),
        },
    }
    if args.json:
        print(json.dumps(result, indent=2, default=list))
        return 0

    t = result["totals"]
    print(f"Repository: {repo}")
    print(f"Main app target: {lifecycle['main_app_target']}; membership from {result['membership']}"
          f"{'; paths compared case-insensitively' if ci else ''}")
    if other_projects:
        print(f"Other Xcode projects (not counted): {dict(other_projects)}")
    if vendored_roots:
        print(f"Vendored folders skipped (use --include-vendored to scan them): {', '.join(sorted(vendored_roots))}")
    print(f"Screens to plan: {t['screens']} ({t['screen_lines']} lines incl. own views and cells), "
          f"by complexity {t['screens_by_complexity']}; MVC (no view model, presenter, or store): "
          f"{t['screens_without_view_model']}")
    print(f"Controllers that embed SwiftUI (already SwiftUI): {', '.join(t['swiftui_hosts']) or 'none'}")
    print(f"SwiftUI views hosted from UIKit: {', '.join(hosted_swiftui) or 'none'}")
    print(f"Containers (navigation work): {', '.join(t['containers']) or 'none'}")
    print(f"Controller base classes (foundation work): {', '.join(t['controller_base_classes']) or 'none'}")
    print(f"View and cell base classes (converted with their screens): {', '.join(t['view_base_classes']) or 'none'}")
    print(f"Possibly unreferenced controllers (check entry points before removing): "
          f"{', '.join(t['possibly_unreferenced_controllers']) or 'none'}")
    print(f"Possibly unused views (nothing references them): {', '.join(t['possibly_unused_views']) or 'none'}")
    print(f"UIKit views and cells: {t['uikit_views']}; shared (used by 3+ controllers): "
          f"{', '.join(t['shared_views']) or 'none'}")
    print(f"Storyboard scenes (no launch screen): {t['storyboard_scenes']}, segues: {t['storyboard_segues']}, "
          f"XIBs: {t['xibs']}, UI test files: {t['ui_test_files']}")
    for s in result["storyboards_and_xibs"]:
        if s["file"].endswith(".storyboard") and not s["launch_screen"]:
            print(f"  {s['file']}: {s['scenes']} scenes, {s['segues']} segues")
    print(f"Possibly unused storyboards and XIBs (nothing loads them by name): {', '.join(unused_ib) or 'none'}")
    print(f"Not in any Xcode project or package (left out): {', '.join(result['not_in_project']) or 'none'}")
    print(f"Swift files that are entirely commented out: {', '.join(dead_files) or 'none'}")
    if result["duplicate_class_names"]:
        print(f"UIKit class names defined in several files: {result['duplicate_class_names']}")
    print(f"Files importing SwiftUI per target: {dict(swiftui_files)}")
    print(f"Lifecycle: {lifecycle}")
    print(f"Coordinators: {result['coordinators'] or 'none'}")
    print(f"Dependencies: {', '.join(result['dependencies']) or 'none'}")
    print("\nView controllers: class + own views (role, UIKit base, lines incl. extensions and own views, "
          "IB = storyboard/XIB, refs = other files that mention it) [flags with weight]:")
    for c in result["view_controllers"]:
        ib = " IB" if c["interface_builder"] else ""
        role = ", " + (f"base class of {c['subclasses']}" if c["role"] == "base class" else
                       "embeds SwiftUI" if c["role"] == "SwiftUI host" else c["role"])
        mvc = ", MVC" if c["role"] == "screen" and not c["has_view_model"] else ""
        ids = f", {c['accessibility_identifiers']} a11y ids" if c["accessibility_identifiers"] else ""
        entry = (f", entry points used in {len(c['entry_point_refs'])} files"
                 if c["entry_point_refs"] and not c["referenced_by"] else "")
        unref = ", POSSIBLY UNREFERENCED" if c["possibly_unreferenced"] else ""
        rel = f" + {', '.join(c['related_views'])}" if c["related_views"] else ""
        flags = f" [{', '.join(c['flags'])}]" if c["flags"] else ""
        mark = "~" if c.get("near_boundary") else " "
        label = c["complexity"] if c["role"] == "screen" else "-"
        print(f"  {label:<2}{mark}{c['class']}{rel} ({role[2:]}, {c['uikit_base']}, {c['lines']} lines{ib}, "
              f"refs {c['referenced_by']}{mvc}{ids}{entry}{unref}) {c['file']}{flags}")
    print("\nFiles per UIKit-only API or pattern (file counts):")
    for flag, paths in result["files_per_flag"].items():
        print(f"  {flag}: {len(paths)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
