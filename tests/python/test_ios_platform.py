import unittest

from support import PBXPROJ, RepoTestCase, requires_git, run_json, run_script

SCRIPT = "review-architecture-ios/scripts/ios_platform.py"

PACKAGE_SWIFT = """// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "Networking",
    platforms: [.iOS(.v15), .macOS(.v13)],
    products: [.library(name: "Networking", targets: ["Networking"])],
    dependencies: [
        .package(url: "https://github.com/apple/swift-log.git", branch: "main"),
        .package(url: "https://github.com/onevcat/Kingfisher.git", exact: "7.0.0"),
        .package(url: "https://github.com/kean/Nuke.git", from: "12.0.0"),
        .package(url: "https://github.com/example/Beta.git", from: "2.0.0-beta.1")
    ],
    targets: [
        .target(name: "Networking", swiftSettings: [.enableUpcomingFeature("ExistentialAny")])
    ]
)
"""


def resolved(**pins):
    """Package.resolved (version 2); a value starting with 'branch ' is a branch pin."""
    entries = []
    for identity, value in pins.items():
        state = {"revision": "0123456789abcdef"}
        if value.startswith("branch "):
            state["branch"] = value[len("branch "):]
        else:
            state["version"] = value
        entries.append({"identity": identity, "kind": "remoteSourceControl",
                        "location": f"https://example.com/{identity}.git", "state": state})
    return {"pins": entries, "version": 2}


APP_RESOLVED = "App.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved"


@requires_git
class IosPlatformTests(RepoTestCase):
    def setUp(self):
        super().setUp()
        self.write("App.xcodeproj/project.pbxproj", PBXPROJ)
        self.write(APP_RESOLVED, resolved(alamofire="5.9.0", **{"swift-log": "branch main"}))
        self.write("Packages/Networking/Package.swift", PACKAGE_SWIFT)
        self.write("Packages/Networking/Package.resolved", resolved(alamofire="5.8.0", **{"swift-log": "branch main"}))
        self.write("App/Feature.swift", "\n".join([
            "if #available(iOS 15, *) {}",
            "if #available(iOS 16.0, *) {}",
            "if #available(iOS 17.4, *) {}",
            "@available(iOS 17.4, macOS 14, *)",
            "struct New {}",
        ]))
        self.write(".build/checkouts/Dep/Old.swift", "if #available(iOS 9, *) {}")
        self.commit()
        self.result = run_json(self, SCRIPT, "--repo", self.repo)

    def test_xcode_target_settings_include_project_defaults(self):
        target = self.result["xcode_targets"]["App.xcodeproj/project.pbxproj: App"]
        self.assertEqual(target["IPHONEOS_DEPLOYMENT_TARGET"], ["16.0", "17.0"])
        self.assertEqual(target["SDKROOT"], ["iphoneos"])
        self.assertEqual(target["SWIFT_STRICT_CONCURRENCY"], ["complete"])
        self.assertEqual(self.result["xcode_settings"]["IPHONEOS_DEPLOYMENT_TARGET"]["16.0"]["count"], 2)

    def test_manifest_summary(self):
        (manifest,) = self.result["manifests"]
        self.assertEqual(manifest["tools_version"], "5.9")
        self.assertEqual(manifest["platforms"], ["iOS(.v15)", "macOS(.v13)"])
        self.assertEqual(manifest["swift_settings"], ['enableUpcomingFeature("ExistentialAny")'])

    def test_pinned_requirements(self):
        pins = {(p["kind"], p["url"]) for p in self.result["pinned_requirements"]}
        self.assertEqual(pins, {
            ("branch", "https://github.com/apple/swift-log.git"),
            ("exact", "https://github.com/onevcat/Kingfisher.git"),
            ("pre-release 2.0.0-beta.1", "https://github.com/example/Beta.git"),
            ("branch", "https://github.com/Alamofire/Alamofire.git"),
        })

    def test_resolved_files_drift_and_branch_pins(self):
        self.assertEqual(self.result["app_resolved_files"], [APP_RESOLVED])
        self.assertEqual(self.result["resolved_drift"], {"alamofire": {
            APP_RESOLVED: "5.9.0", "Packages/Networking/Package.resolved": "5.8.0"}})
        self.assertEqual(self.result["resolved_branch_pins"][APP_RESOLVED], {"swift-log": "branch main"})

    def test_availability_uses_lowest_app_target_and_built_platforms(self):
        availability = self.result["availability"]
        self.assertEqual(availability["platforms_built"], ["iOS"])
        self.assertEqual(availability["minimum_deployment_targets"], {"iOS": "16.0"})
        self.assertEqual(availability["total"], 4)  # the .build checkout is skipped
        self.assertEqual(availability["platform_clauses"], 5)
        self.assertEqual(availability["dead_checks"], {
            "iOS 15 (at or below iOS 16.0)": 1,
            "iOS 16.0 (at or below iOS 16.0)": 1,
            "macOS 14 (platform not built)": 1,
        })
        self.assertEqual(availability["needed_checks"], {"iOS 17.4": 2})

    def test_text_output(self):
        result = run_script(SCRIPT, "--repo", self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Availability checks: 4 total, naming 5 platform versions", result.stdout)
        self.assertIn("alamofire: " + APP_RESOLVED + "=5.9.0", result.stdout)


@requires_git
class PackageOnlyRepoTests(RepoTestCase):
    def test_package_platforms_count_when_there_is_no_xcode_project(self):
        self.write("Package.swift", PACKAGE_SWIFT)
        self.write("Sources/Networking/Client.swift", "if #available(macOS 13, *) {}\nif #available(iOS 16, *) {}")
        self.commit()
        availability = run_json(self, SCRIPT, "--repo", self.repo)["availability"]
        self.assertEqual(availability["minimum_deployment_targets"], {"iOS": "15.0", "macOS": "13.0"})
        self.assertEqual(availability["dead_checks"], {"macOS 13 (at or below macOS 13.0)": 1})
        self.assertEqual(availability["needed_checks"], {"iOS 16": 1})


if __name__ == "__main__":
    unittest.main()
