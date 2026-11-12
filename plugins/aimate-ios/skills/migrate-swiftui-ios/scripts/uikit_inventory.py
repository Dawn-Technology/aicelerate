#!/usr/bin/env python3
"""Inventory the UIKit user interface of an iOS repository for a SwiftUI migration plan.

Reads only git-tracked files. Finds view controllers and UIKit views (following
superclasses defined in the project), storyboard and XIB scenes, UIKit-only APIs
that need a wrapper or a decision, existing SwiftUI and bridging code, and the app
lifecycle, and gives every view controller a complexity class.

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
# UIKit-only or hard-to-convert APIs: (flag, regex, weight). Weight 2 = needs a wrapper or a design decision.
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
    ("auto layout in code", r"NSLayoutConstraint|\.snp\.|SnapKit|anchor\(equalTo|constraint\(equalTo", 0),
    ("RxSwift or RxCocoa", r"import RxSwift|import RxCocoa", 2),
    ("Combine bindings", r"import Combine", 0),
    ("child view controllers", r"addChild\(|willMove\(toParent|didMove\(toParent", 1),
    ("search controller", r"\bUISearchController\b", 1),
    ("context menu or swipe actions", r"UIContextMenuConfiguration|UISwipeActionsConfiguration|trailingSwipeActionsConfiguration", 0),
    ("pull to refresh", r"\bUIRefreshControl\b", 0),
]
CLASS_RE = re.compile(r"^\s*(?:@\w+(?:\([^)]*\))?\s+)*(?:(?:public|open|internal|private|fileprivate|final)\s+)*class\s+(\w+)\s*(?:<[^>]*>)?\s*:\s*([\w.]+)", re.M)
OBJC_RE = re.compile(r"@interface\s+(\w+)\s*:\s*(\w+)")


def git_files(repo):
    out = subprocess.run(["git", "-C", repo, "ls-files", "-z"], capture_output=True, text=True, check=True).stdout
    return [p for p in out.split("\0") if p]


def read(repo, path):
    try:
        with open(os.path.join(repo, path), encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except OSError:
        return ""


def root_of(name, supers, roots, seen=None):
    seen = seen or set()
    while name in supers and name not in seen:
        seen.add(name)
        parent = supers[name].split(".")[-1]
        if parent in roots:
            return parent
        name = parent
    return None


def complexity(lines, flag_weight, from_ib):
    score = 0
    score += 0 if lines <= 150 else 1 if lines <= 400 else 2 if lines <= 800 else 3
    score += min(flag_weight, 3)
    score += 1 if from_ib else 0
    return "S" if score <= 1 else "M" if score <= 2 else "L" if score <= 4 else "XL"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--exclude", action="append", default=[],
                        help="glob of paths to skip, for example 'Pods/*' (tests and previews are skipped by default)")
    args = parser.parse_args()
    repo = os.path.abspath(args.repo)
    default_excludes = ["*Tests/*", "*Tests.swift", "*UITests/*", "Pods/*", "Carthage/*", "*/Preview Content/*"]
    files = [f for f in git_files(repo) if not any(fnmatch.fnmatch(f, g) for g in default_excludes + args.exclude)]

    supers, defined_in, texts = {}, {}, {}
    for path in files:
        if path.endswith(".swift") or path.endswith(".h") or path.endswith(".m"):
            text = read(repo, path)
            texts[path] = text
            regex = CLASS_RE if path.endswith(".swift") else OBJC_RE
            for name, parent in regex.findall(text):
                supers.setdefault(name, parent)
                defined_in.setdefault(name, path)

    controllers, views = [], []
    for name, path in defined_in.items():
        vc_root = supers[name] if supers[name] in VC_ROOTS else root_of(name, supers, VC_ROOTS)
        view_root = None if vc_root else (supers[name] if supers[name] in VIEW_ROOTS else root_of(name, supers, VIEW_ROOTS))
        if not (vc_root or view_root):
            continue
        text = texts[path]
        lines = text.count("\n") + 1
        flags = [(flag, w) for flag, rx, w in FLAGS if re.search(rx, text)]
        item = {"class": name, "file": path, "lines": lines, "language": "objc" if path.endswith((".m", ".h")) else "swift",
                "superclass": supers[name], "uikit_base": vc_root or view_root,
                "flags": [f for f, _ in flags]}
        if vc_root:
            from_ib = bool(re.search(r"instantiateViewController|UIStoryboard\(|nibName|IBOutlet", text))
            item["interface_builder"] = from_ib
            item["complexity"] = complexity(lines, sum(w for _, w in flags), from_ib)
            controllers.append(item)
        else:
            views.append(item)

    storyboards = []
    for path in files:
        if path.endswith((".storyboard", ".xib")):
            text = read(repo, path)
            storyboards.append({
                "file": path,
                "scenes": len(re.findall(r"<scene\b", text)) or (1 if path.endswith(".xib") else 0),
                "custom_classes": sorted(set(re.findall(r'customClass="(\w+)"', text))),
                "segues": len(re.findall(r"<segue\b", text)),
            })

    swift_texts = {p: t for p, t in texts.items() if p.endswith(".swift")}
    bridging = Counter()
    flag_files = defaultdict(set)
    for path, text in swift_texts.items():
        if "import SwiftUI" in text:
            bridging["files importing SwiftUI"] += 1
        bridging["UIHostingController uses"] += len(re.findall(r"\bUIHostingController\b", text))
        bridging["UIViewRepresentable types"] += len(re.findall(r":\s*UIViewRepresentable\b|,\s*UIViewRepresentable\b", text))
        bridging["UIViewControllerRepresentable types"] += len(re.findall(r"UIViewControllerRepresentable\b", text))
        for flag, rx, _ in FLAGS:
            if re.search(rx, text):
                flag_files[flag].add(path)

    all_text = "\n".join(swift_texts.values())
    lifecycle = {
        "swiftui_app": bool(re.search(r"@main\s+struct\s+\w+\s*:\s*App\b", all_text)),
        "app_delegate": bool(re.search(r"UIApplicationDelegate", all_text)),
        "scene_delegate": bool(re.search(r"UIWindowSceneDelegate", all_text)),
        "coordinators": len(re.findall(r"class\s+\w*Coordinator\b", all_text)),
        "objc_files": sum(1 for p in texts if p.endswith(".m")),
    }

    result = {
        "repo": repo,
        "view_controllers": sorted(controllers, key=lambda c: (c["file"], c["class"])),
        "uikit_views": sorted(views, key=lambda v: (v["file"], v["class"])),
        "storyboards_and_xibs": storyboards,
        "bridging": dict(bridging),
        "lifecycle": lifecycle,
        "flags": {flag: sorted(paths) for flag, paths in sorted(flag_files.items())},
        "totals": {
            "view_controllers": len(controllers),
            "by_complexity": dict(Counter(c["complexity"] for c in controllers)),
            "view_controller_lines": sum(c["lines"] for c in controllers),
            "uikit_views": len(views),
            "uikit_view_lines": sum(v["lines"] for v in views),
            "storyboard_scenes": sum(s["scenes"] for s in storyboards if s["file"].endswith(".storyboard")),
            "xibs": sum(1 for s in storyboards if s["file"].endswith(".xib")),
        },
    }
    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    t = result["totals"]
    print(f"Repository: {repo}")
    print(f"View controllers: {t['view_controllers']} ({t['view_controller_lines']} lines), by complexity {t['by_complexity']}")
    print(f"UIKit views and cells: {t['uikit_views']} ({t['uikit_view_lines']} lines)")
    print(f"Storyboard scenes: {t['storyboard_scenes']}, XIBs: {t['xibs']}")
    print(f"Bridging and SwiftUI: {result['bridging']}")
    print(f"Lifecycle: {lifecycle}")
    print("\nView controllers:")
    for c in result["view_controllers"]:
        ib = " IB" if c["interface_builder"] else ""
        flags = f" [{', '.join(c['flags'])}]" if c["flags"] else ""
        print(f"  {c['complexity']:<2} {c['class']} ({c['uikit_base']}, {c['lines']} lines{ib}) {c['file']}{flags}")
    print("\nFiles per UIKit-only API or pattern:")
    for flag, paths in result["flags"].items():
        print(f"  {flag}: {len(paths)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
