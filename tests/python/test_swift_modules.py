import shutil
import tempfile
import unittest
from pathlib import Path

from support import PBXPROJ, RepoTestCase, load_script, requires_git, run_json

SCRIPT = "review-architecture-ios/scripts/swift_modules.py"
sm = load_script(SCRIPT)

PACKAGE_SWIFT = """// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "Core",
    platforms: [.iOS(.v16)],
    products: [.library(name: "Feature", targets: ["Feature"])],
    dependencies: [
        .package(url: "https://github.com/Alamofire/Alamofire.git", from: "5.0.0"),
        .package(url: "https://github.com/onevcat/Kingfisher.git", exact: "7.0.0"),
    ],
    targets: [
        .target(name: "Models"),
        .target(name: "Networking", dependencies: ["Models", .product(name: "Alamofire", package: "Alamofire")]),
        .target(name: "Feature", dependencies: ["Networking", "Utils"]),
        .target(name: "Utils"),
        .testTarget(name: "FeatureTests", dependencies: ["Feature"]),
    ]
)
"""


class ImportTests(unittest.TestCase):
    def imported(self, line):
        match = sm.IMPORT_RE.match(line)
        return match.group(1) if match else None

    def test_import_forms(self):
        self.assertEqual(self.imported("import UIKit"), "UIKit")
        self.assertEqual(self.imported("@testable import App"), "App")
        self.assertEqual(self.imported("@_spi(Internal) @preconcurrency import Core"), "Core")
        self.assertEqual(self.imported("import struct Foundation.URL"), "Foundation")
        self.assertEqual(self.imported("    import class Models.User"), "Models")

    def test_non_imports(self):
        self.assertIsNone(self.imported("// import Nope"))
        self.assertIsNone(self.imported("let important = 1"))


class DependencyTests(unittest.TestCase):
    def test_dep_names(self):
        names = {"Models"}
        self.assertEqual(sm.dep_names({"target": ["Models", None]}, names), ("internal", "Models"))
        self.assertEqual(sm.dep_names({"byName": ["Models", None]}, names), ("internal", "Models"))
        self.assertEqual(sm.dep_names({"byName": ["Alamofire", None]}, names), ("external", "Alamofire"))
        self.assertEqual(sm.dep_names({"product": ["Alamofire", "Alamofire", None, None]}, names),
                         ("external", "Alamofire"))

    def test_package_of(self):
        self.assertEqual(sm.package_of({"product": ["Logging", "swift-log", None, None]}), "swift-log")
        self.assertEqual(sm.package_of({"byName": ["Alamofire", None]}), "alamofire")
        self.assertIsNone(sm.package_of({"target": ["Models", None]}))

    def test_version_tuple(self):
        self.assertEqual(sm.version_tuple("5"), (5, 0, 0))
        self.assertEqual(sm.version_tuple("1.2.3-beta.1"), (1, 2, 3))

    def test_satisfies(self):
        up_to_next_major = {"range": [{"lowerBound": "5.0.0", "upperBound": "6.0.0"}]}
        self.assertTrue(sm.satisfies("5.9.1", up_to_next_major))
        self.assertTrue(sm.satisfies("5.0.0", up_to_next_major))
        self.assertFalse(sm.satisfies("6.0.0", up_to_next_major))
        self.assertFalse(sm.satisfies("4.9.9", up_to_next_major))
        self.assertTrue(sm.satisfies("7.0.0", {"exact": ["7.0.0"]}))
        self.assertFalse(sm.satisfies("7.0.1", {"exact": ["7.0.0"]}))
        self.assertIsNone(sm.satisfies(None, up_to_next_major))
        self.assertIsNone(sm.satisfies("1.0.0", {"branch": ["main"]}))

    def test_target_dir(self):
        self.assertEqual(sm.target_dir("Pkg", {"name": "A", "type": "regular"}), "Pkg/Sources/A")
        self.assertEqual(sm.target_dir("Pkg", {"name": "ATests", "type": "test"}), "Pkg/Tests/ATests")
        self.assertEqual(sm.target_dir("Pkg", {"name": "Gen", "type": "plugin"}), "Pkg/Plugins/Gen")
        self.assertEqual(sm.target_dir("Pkg", {"name": "A", "type": "regular", "path": "Code/A/"}), "Pkg/Code/A")
        self.assertEqual(sm.target_dir("", {"name": "A", "type": "regular"}), "Sources/A")


class GraphTests(unittest.TestCase):
    def test_find_cycles(self):
        graph = {"a": ["b"], "b": ["c"], "c": ["a"], "d": ["a"], "e": ["e"], "f": []}
        self.assertEqual(sm.find_cycles(graph), [["a", "b", "c"]])
        self.assertEqual(sm.find_cycles({"x": ["y"], "y": []}), [])

    def test_closure(self):
        graph = {"a": ["b", "c"], "b": ["d"], "c": ["d"], "d": []}
        self.assertEqual(sm.closure(graph, "a"), {"b", "c", "d"})
        self.assertEqual(sm.closure(graph, "d"), set())
        self.assertEqual(sm.closure({"a": ["b"], "b": ["a"]}, "a"), {"a", "b"})

    def test_xcode_links(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "App.xcodeproj" / "project.pbxproj"
            path.parent.mkdir()
            path.write_text(PBXPROJ)
            links = sm.xcode_links(directory, ["App.xcodeproj/project.pbxproj"], {"Networking"})
        self.assertEqual(links, {"App.xcodeproj/project.pbxproj: App": {
            "internal": ["Networking"], "external": ["Alamofire"]}})


@requires_git
@unittest.skipUnless(shutil.which("swift"), "swift is not installed")
class EndToEndTests(RepoTestCase):
    def setUp(self):
        super().setUp()
        package = "Packages/Core"
        self.write(f"{package}/Package.swift", PACKAGE_SWIFT)
        self.write(f"{package}/Package.resolved", {"pins": [
            {"identity": "alamofire", "state": {"version": "6.1.0"}},
            {"identity": "kingfisher", "state": {"version": "7.0.0"}}], "version": 2})
        self.write(f"{package}/Sources/Models/User.swift", "import Foundation\nimport Feature\n")
        self.write(f"{package}/Sources/Networking/Client.swift", "import Models\nimport Alamofire\n")
        self.write(f"{package}/Sources/Feature/Screen.swift", "import Networking\nimport Models\n\nstruct S {}\n")
        self.write(f"{package}/Sources/Utils/Util.swift", "import Foundation\n")
        self.write(f"{package}/Tests/FeatureTests/ScreenTests.swift", "@testable import Feature\n")
        self.write("App.xcodeproj/project.pbxproj", PBXPROJ)
        self.commit()
        self.result = run_json(self, SCRIPT, "--repo", self.repo, "--layer", "domain=Models",
                               "--layer", "data=Networking,Utils", "--layer", "ui=Feature")
        self.targets = self.result["targets"]

    def test_package_and_targets(self):
        self.assertEqual(self.result["manifest_errors"], [])
        (package,) = self.result["packages"]
        self.assertEqual(package["name"], "Core")
        self.assertEqual(package["unused_packages"], ["kingfisher"])
        self.assertEqual(sorted(self.targets), ["Feature", "FeatureTests", "Models", "Networking", "Utils"])
        feature = self.targets["Feature"]
        self.assertEqual((feature["files"], feature["lines"]), (1, 4))
        self.assertEqual(self.targets["Networking"]["declared_external"], ["Alamofire"])

    def test_dependency_findings(self):
        feature = self.targets["Feature"]
        self.assertEqual(feature["undeclared_internal_imports"],
                         {"Models": ["Packages/Core/Sources/Feature/Screen.swift:2"]})
        self.assertEqual(feature["declared_not_imported"], ["Utils"])
        self.assertEqual((feature["fan_in"], feature["fan_out"], feature["instability"]), (0, 2, 1.0))
        self.assertEqual(feature["transitive_internal"], 3)
        self.assertEqual(self.targets["Models"]["instability"], 0.0)
        self.assertEqual(self.result["import_cycles"], [["Feature", "Models", "Networking"]])
        self.assertEqual(self.result["untested_targets"], ["Models", "Networking", "Utils"])

    def test_layers_resolved_pins_and_xcode_links(self):
        self.assertEqual([(w["from"], w["to"]) for w in self.result["wrong_direction_imports"]],
                         [("Models", "Feature")])
        self.assertEqual(self.result["unmapped_targets"], [])
        (violation,) = self.result["resolved_outside_requirement"]
        self.assertEqual((violation["package"], violation["version"]), ("alamofire", "6.1.0"))
        self.assertEqual(self.result["xcode_links"]["App.xcodeproj/project.pbxproj: App"],
                         {"internal": ["Networking"], "external": ["Alamofire"]})


if __name__ == "__main__":
    unittest.main()
