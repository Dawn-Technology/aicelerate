import shutil
import tempfile
import unittest
from pathlib import Path

from support import PBXPROJ, RepoTestCase, load_script, requires_git, run_json, run_script

SCRIPT = "migrate-swiftui-ios/scripts/uikit_inventory.py"
ui = load_script(SCRIPT)


class BlockTests(unittest.TestCase):
    def test_block_at_skips_braces_in_strings(self):
        text = 'extension A { let s = "}{\\"}"; func f() { } }\nlet after = 1'
        self.assertEqual(ui.block_at(text, 0, 0), text.split("\n")[0])
        self.assertIsNone(ui.block_at("extension A", 0, 0))
        self.assertIsNone(ui.block_at("extension A { unclosed", 0, 0))

    def test_class_body(self):
        text = "import UIKit\n\nfinal class Screen: UIViewController {\n    let s = \"}\"\n}\n\nclass Other {}\n"
        body, lines = ui.class_body(text, "Screen")
        self.assertTrue(body.startswith("class Screen") and body.endswith("}"))
        self.assertNotIn("Other", body)
        self.assertEqual(lines, 3)
        self.assertEqual(ui.class_body(text, "Missing"), (text, 8))

    def test_extensions_of(self):
        texts = {"A+UI.swift": "extension Screen {\n  func a() {}\n}\nprivate extension Screen: UITableViewDelegate { }\n",
                 "Notes.md": "extension Screen { }"}
        found = ui.extensions_of(texts)
        self.assertEqual(list(found), ["Screen"])
        self.assertEqual(len(found["Screen"]), 2)

    def test_commented_out(self):
        self.assertTrue(ui.commented_out("// import UIKit\n/* class A {\n} */\n\n"))
        self.assertFalse(ui.commented_out("// header\nimport UIKit\n"))


class ComplexityTests(unittest.TestCase):
    def test_by_lines(self):
        self.assertEqual([ui.complexity(n, n, [], False) for n in (150, 151, 400, 401, 800, 801)],
                         ["S", "M", "M", "L", "L", "XL"])

    def test_by_flags(self):
        self.assertEqual(ui.complexity(10, 10, [("map", 1)], False), "S")
        self.assertEqual(ui.complexity(10, 10, [("map", 1), ("pdf", 1)], False), "M")
        self.assertEqual(ui.complexity(10, 10, [("drag", 2)], False), "L")
        self.assertEqual(ui.complexity(10, 10, [("drag", 2), ("camera", 2)], False), "XL")
        self.assertEqual(ui.complexity(10, 10, [("info", 0)] * 5, False), "S")

    def test_by_interface_builder(self):
        self.assertEqual(ui.complexity(100, 80, [], True, elements=15), "S")
        self.assertEqual(ui.complexity(100, 81, [], True, elements=15), "M")
        self.assertEqual(ui.complexity(100, 80, [], True, elements=16), "M")

    def test_highest_class_wins(self):
        self.assertEqual(ui.complexity(900, 900, [("map", 1)], True, elements=1), "XL")


class ParsingTests(unittest.TestCase):
    def test_ib_elements_counts_only_the_classes_scene(self):
        storyboard = ('<scenes><scene sceneID="1"><viewController customClass="A"><view><label/><button/></view>'
                      '</viewController></scene><scene sceneID="2"><viewController customClass="B"><view/>'
                      '</viewController></scene></scenes>')
        self.assertEqual(ui.ib_elements(storyboard, "A"), 3)
        self.assertEqual(ui.ib_elements(storyboard, "B"), 1)
        self.assertEqual(ui.ib_elements(storyboard, "C"), 0)
        self.assertEqual(ui.ib_elements("<view><stackView><label/></stackView></view>", "Cell"), 3)

    def test_composed_types(self):
        code = ("let header = HeaderView()\nvar cells: [ProfileCell]\n"
                "tableView.register(RowCell.self)\nlet ds = Source<Item>()\n"
                "// let old = OldView()\n/* FooView() */\n<view customClass=\"BadgeView\"/>")
        found = set(ui.composed_types(code))
        self.assertTrue({"HeaderView", "ProfileCell", "RowCell", "Item", "BadgeView"} <= found, found)
        self.assertFalse({"OldView", "FooView"} & found)

    def test_class_regex(self):
        text = "@MainActor\npublic final class Screen<T>: Base.Controller {\n}\nclass NoParent {}\n"
        self.assertEqual(ui.CLASS_RE.findall(text), [("Screen", "Base.Controller")])

    def test_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Package.resolved").write_text(
                '{"pins": [{"identity": "kingfisher"}], "version": 2}')
            (root / "Old.resolved").write_text('{"object": {"pins": [{"package": "SnapKit"}]}, "version": 1}')
            (root / "Podfile.lock").write_text(
                "PODS:\n  - Alamofire (5.8.0)\n  - Firebase/Core (10.0.0):\n    - FirebaseCore\n"
                "\nDEPENDENCIES:\n  - Ignored\n")
            (root / "Cartfile.resolved").write_text('github "ReactiveX/RxSwift" "6.5.0"\n')
            files = ["Package.resolved", "Old.resolved", "Podfile.lock", "Cartfile.resolved"]
            # Old.resolved is not named Package.resolved and is ignored; nested pod lines are skipped.
            self.assertEqual(ui.dependencies(directory, files),
                             ["Alamofire", "Firebase", "kingfisher", "ReactiveX/RxSwift"])  # subspecs count as their pod


PROFILE = """import UIKit
import WebKit

final class ProfileViewController: UIViewController {
    private let avatar = AvatarView()
    private let web = WKWebView()

    override func viewDidLoad() {
        super.viewDidLoad()
        view.addSubview(avatar)
    }
}

final class AvatarView: UIView {
    let label = UILabel()
}
"""

SETTINGS = """import UIKit
import MapKit

final class SettingsViewController: UIViewController {
    let viewModel = SettingsViewModel()
    let map = MKMapView()

    func route() {
        map.addOverlay(MKPolyline())
    }

    func open() {
        navigationController?.pushViewController(ProfileViewController(), animated: true)
    }
}
"""

STORYBOARD = """<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.Storyboard.XIB" version="3.0">
    <scenes>
        <scene sceneID="a1">
            <objects>
                <viewController id="v1" customClass="ProfileViewController" sceneMemberID="viewController">
                    <view key="view" id="r1"><subviews><label id="l1"/></subviews></view>
                </viewController>
            </objects>
        </scene>
    </scenes>
</document>
"""


@requires_git
@unittest.skipUnless(shutil.which("plutil"), "plutil is not installed (macOS only)")
class EndToEndTests(RepoTestCase):
    def setUp(self):
        super().setUp()
        self.write("App.xcodeproj/project.pbxproj", PBXPROJ)
        self.write("App/AppDelegate.swift",
                   "import UIKit\n\n@main\nclass AppDelegate: UIResponder, UIApplicationDelegate {\n}\n")
        self.write("App/ProfileViewController.swift", PROFILE)
        self.write("App/SettingsViewController.swift", SETTINGS)
        self.write("App/Main.storyboard", STORYBOARD)
        self.write("App/Old.swift", "// class OldViewController: UIViewController {}\n")
        self.write("Tools/Unlisted.swift", "import UIKit\nclass ToolViewController: UIViewController {}\n")
        self.write("ThirdParty/Lib/VendorViewController.swift",
                   "import UIKit\nclass VendorViewController: UIViewController {}\n")
        self.write("AppTests/ProfileTests.swift", "class ProfileTestsViewController: UIViewController {}\n")
        self.write("Podfile.lock", "PODS:\n  - Alamofire (5.8.0)\n\nDEPENDENCIES:\n")
        self.commit()
        self.result = run_json(self, SCRIPT, "--repo", self.repo)
        self.controllers = {c["class"]: c for c in self.result["view_controllers"]}

    def test_scope_and_membership(self):
        self.assertEqual(self.result["membership"], "project.pbxproj")
        self.assertEqual(self.result["lifecycle"]["main_app_target"], "App (App.xcodeproj/project.pbxproj)")
        self.assertTrue(self.result["lifecycle"]["app_delegate"])
        self.assertFalse(self.result["lifecycle"]["swiftui_app"])
        self.assertEqual(self.result["vendored_folders_skipped"], ["ThirdParty"])
        self.assertEqual(sorted(self.controllers), ["ProfileViewController", "SettingsViewController"])
        self.assertIn("Tools/Unlisted.swift", self.result["not_in_project"])
        self.assertEqual(self.result["commented_out_files"], ["App/Old.swift"])
        self.assertEqual(self.result["dependencies"], ["Alamofire"])

    def test_screens(self):
        profile, settings = self.controllers["ProfileViewController"], self.controllers["SettingsViewController"]
        self.assertTrue(profile["interface_builder"])
        self.assertIn("AvatarView", profile["related_views"])
        self.assertFalse(profile["has_view_model"])
        self.assertTrue(settings["has_view_model"])
        self.assertEqual(settings["complexity"], "L")  # map with overlays is a weight-2 flag
        self.assertEqual(self.result["files_per_flag"]["web view"], ["App/ProfileViewController.swift"])
        self.assertEqual(self.result["totals"]["screens"], 2)
        self.assertEqual(self.result["totals"]["storyboard_scenes"], 1)

    def test_text_output(self):
        result = run_script(SCRIPT, "--repo", self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Screens to plan: 2", result.stdout)


if __name__ == "__main__":
    unittest.main()
