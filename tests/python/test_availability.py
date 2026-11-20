import unittest

from support import RepoTestCase, load_script, requires_git, run_json, run_script

SCRIPT = "raise-minimum-ios/scripts/availability.py"
av = load_script(SCRIPT)

IOS17 = {"iOS": av.version("17.0")}


class ClassifyTests(unittest.TestCase):
    def verdict(self, kind, args, minimums=IOS17):
        return av.classify(kind, args, minimums)[0]

    def test_version_pads_to_three_parts(self):
        self.assertEqual(av.version("17"), (17, 0, 0))
        self.assertEqual(av.version("15.4.1"), (15, 4, 1))

    def test_checks_at_or_below_minimum_are_always_true(self):
        self.assertEqual(self.verdict("#available", "iOS 15, *"), "always-true")
        self.assertEqual(self.verdict("#available", "iOS 17.0, *"), "always-true")
        self.assertEqual(self.verdict("@available", "iOS 16.4, *"), "always-true")
        self.assertEqual(self.verdict("@available", "iOS, introduced: 15"), "always-true")

    def test_checks_above_minimum_are_needed(self):
        self.assertEqual(self.verdict("#available", "iOS 17.0.1, *"), "needed")
        self.assertEqual(self.verdict("#available", "iOS 18, *"), "needed")

    def test_unavailable_below_minimum_is_always_false(self):
        self.assertEqual(self.verdict("#unavailable", "iOS 16"), "always-false")
        self.assertEqual(self.verdict("#unavailable", "iOS 18"), "needed")

    def test_platform_without_new_minimum_keeps_check_needed(self):
        self.assertEqual(self.verdict("#available", "iOS 15, macOS 12, *"), "needed")
        both = {"iOS": av.version("17"), "macOS": av.version("14")}
        self.assertEqual(self.verdict("#available", "iOS 15, macOS 12, *", both), "always-true")

    def test_app_extension_counts_as_ios(self):
        self.assertEqual(self.verdict("@available", "iOSApplicationExtension 15, *"), "always-true")

    def test_wildcard_annotations_are_skipped(self):
        self.assertIsNone(self.verdict("@available", "*, deprecated, message: \"use x\""))
        self.assertIsNone(self.verdict("@available", "*, noasync"))

    def test_deprecated_at_or_below_minimum_is_backport_candidate(self):
        self.assertEqual(self.verdict("@available", "iOS, deprecated: 16.0, message: \"use system\""),
                         "backport-candidate")
        self.assertEqual(self.verdict("@available", "iOS, introduced: 13, deprecated: 18"), "needed")

    def test_unclassified_forms_need_review(self):
        self.assertEqual(self.verdict("@available", "iOS, introduced: 13, obsoleted: 16"), "review")
        self.assertEqual(self.verdict("@available", "iOS, unavailable"), "review")
        self.assertEqual(self.verdict("#available", "iOS, *"), "review")
        self.assertEqual(self.verdict("#available", "*"), "review")


@requires_git
class CommandTests(RepoTestCase):
    def test_scans_tracked_swift_and_skips_generated_and_build_folders(self):
        checks = "if #available(iOS 15, *) {}\nif #available(iOS 18, *) {}\n"
        self.write("App/View.swift", checks + "@available(*, unavailable)\nfunc f() {}\n")
        self.write("App/Generated/Strings.swift", checks)
        self.write("App/Model.generated.swift", checks)
        self.write("Pods/Lib/Lib.swift", checks)
        self.write("App/notes.md", checks)
        self.commit()
        rows = run_json(self, SCRIPT, "--repo", self.repo, "--min", "iOS=17.0")
        self.assertEqual([(r["location"], r["verdict"]) for r in rows],
                         [("App/View.swift:1", "always-true"), ("App/View.swift:2", "needed")])

    def test_text_output_has_totals(self):
        self.write("A.swift", "guard #available(iOS 14, *) else { return }\n")
        self.commit()
        result = run_script(SCRIPT, "--repo", self.repo, "--min", "iOS=16", "--min", "tvOS=16")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Minimums: iOS 16.0.0, tvOS 16.0.0", result.stdout)
        self.assertIn("Totals: always-true 1", result.stdout)


if __name__ == "__main__":
    unittest.main()
