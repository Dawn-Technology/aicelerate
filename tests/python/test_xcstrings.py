import json
import tempfile
import unittest
from pathlib import Path

from support import RepoTestCase, git, load_script, requires_git, run_script

SCRIPT = "fix-localization-ios/scripts/xcstrings.py"
xc = load_script(SCRIPT)

# Written the way Xcode writes a catalog: " : " separators, two-space indent, empty objects with a blank line.
XCODE_CATALOG = """{
  "sourceLanguage" : "en",
  "strings" : {
    "" : {

    },
    "Hello" : {
      "localizations" : {
        "nl" : {
          "stringUnit" : {
            "state" : "translated",
            "value" : "Hallo"
          }
        }
      }
    },
    "Items %lld" : {
      "extractionState" : "stale",
      "localizations" : {
        "nl" : {
          "variations" : {
            "plural" : {
              "one" : {
                "stringUnit" : {
                  "state" : "translated",
                  "value" : "%lld item"
                }
              },
              "other" : {
                "stringUnit" : {
                  "state" : "translated",
                  "value" : "%lld items"
                }
              }
            }
          }
        }
      }
    },
    "Zebra" : {

    }
  },
  "version" : "1.0"
}
"""


def catalog(strings, source="en"):
    return {"sourceLanguage": source, "strings": strings, "version": "1.0"}


def unit(value, state="translated"):
    return {"stringUnit": {"state": state, "value": value}}


class DumpTests(unittest.TestCase):
    def test_xcode_catalog_round_trips_byte_for_byte(self):
        self.assertEqual(xc.dump(json.loads(XCODE_CATALOG)) + "\n", XCODE_CATALOG)

    def test_non_ascii_is_kept_literal(self):
        self.assertEqual(xc.dump({"k": "Café “quoted”"}), '{\n  "k" : "Café “quoted”"\n}')

    def test_empty_list_gets_blank_line(self):
        self.assertEqual(xc.dump({"a": []}), '{\n  "a" : [\n\n  ]\n}')


class InsertSortedTests(unittest.TestCase):
    def test_inserts_case_insensitively_and_keeps_existing_order(self):
        strings = {"apple": 1, "Cherry": 2, "banana": 3}  # existing order is kept even when unsorted
        result = xc.insert_sorted(strings, "Blueberry", 4)
        self.assertEqual(list(result), ["apple", "Blueberry", "Cherry", "banana"])

    def test_appends_when_last(self):
        self.assertEqual(list(xc.insert_sorted({"a": 1}, "z", 2)), ["a", "z"])


class SpecifierTests(unittest.TestCase):
    def test_counts_types_ignoring_positions_and_flags(self):
        types, invalid = xc.specifiers("%1$@ has %2$lld of %.2f%% done")
        self.assertEqual(types, {"%@": 1, "%lld": 1, "%f": 1})
        self.assertEqual(invalid, 0)

    def test_lone_percent_is_invalid(self):
        _, invalid = xc.specifiers("50%, %@")
        self.assertEqual(invalid, 1)

    def test_normalized_key_folds_quotes_spaces_and_case(self):
        self.assertEqual(xc.normalized_key("Don’t  Stop"), xc.normalized_key("don't stop"))


class LintTests(unittest.TestCase):
    def lint(self, data, name="Localizable.xcstrings", ref=None):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / name
            path.write_text(xc.dump(data))
            return xc.lint(str(path), ref)

    def test_clean_catalog_has_no_findings(self):
        data = catalog({"Hello %@": {"localizations": {"nl": unit("Hallo %@")}}})
        self.assertEqual(self.lint(data), [])

    def test_specifier_mismatch_and_invalid_sequence(self):
        findings = self.lint(catalog({
            "Hello %@": {"localizations": {"nl": unit("Hallo %lld")}},
            "Save %@": {"localizations": {"nl": unit("Bespaar 50%, %@")}},
        }))
        self.assertTrue(any(f.startswith("format specifiers differ") and "Hello" in f for f in findings), findings)
        self.assertTrue(any(f.startswith("invalid format sequence") and "Save" in f for f in findings), findings)

    def test_plural_variations_compare_against_source_key(self):
        data = catalog({"%lld items": {"localizations": {"nl": {"variations": {"plural": {
            "one": unit("%lld item"), "other": unit("items")}}}}}})
        findings = self.lint(data)
        self.assertEqual(len(findings), 1, findings)
        self.assertIn("plural.other", findings[0])

    def test_edge_whitespace_untranslated_and_near_duplicate_keys(self):
        findings = self.lint(catalog({
            "Name: ": {"localizations": {"nl": unit("Naam:")}},
            "Settings": {"localizations": {"nl": unit("Settings")}},
            "Don't": {},
            "Don’t": {},
        }))
        self.assertTrue(any(f.startswith("leading or trailing space") for f in findings), findings)
        self.assertTrue(any(f.startswith("same text as en") for f in findings), findings)
        self.assertTrue(any(f.startswith("keys differ only by") for f in findings), findings)

    def test_short_identical_values_are_not_flagged(self):
        self.assertEqual(self.lint(catalog({"OK": {"localizations": {"nl": unit("OK")}}})), [])

    def test_infoplist_key_outside_infoplist_catalog(self):
        data = catalog({"NSCameraUsageDescription": {}})
        self.assertTrue(any("Info.plist key" in f for f in self.lint(data)))
        self.assertEqual(self.lint(data, name="InfoPlist.xcstrings"), [])


class CommandTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "Localizable.xcstrings"
        self.path.write_text(XCODE_CATALOG)

    def tearDown(self):
        self._tmp.cleanup()

    def run_ok(self, *args):
        result = run_script(SCRIPT, *args)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def strings(self):
        return json.loads(self.path.read_text())["strings"]

    def test_check(self):
        self.run_ok("check", self.path)
        self.path.write_text(json.dumps(json.loads(XCODE_CATALOG), indent=2))
        result = run_script(SCRIPT, "check", self.path)
        self.assertEqual(result.returncode, 1)
        self.assertIn("DIFFERS", result.stdout)

    def test_set_new_key_is_sorted_and_diff_is_minimal(self):
        self.run_ok("set", self.path, "--key", "goodbye", "--lang", "nl", "--value", "Doei")
        self.assertEqual(list(self.strings()), ["", "goodbye", "Hello", "Items %lld", "Zebra"])
        self.assertEqual(self.strings()["goodbye"]["localizations"]["nl"]["stringUnit"],
                         {"state": "needs_review", "value": "Doei"})
        self.run_ok("check", self.path)
        self.run_ok("delete", self.path, "--key", "goodbye")
        self.assertEqual(self.path.read_text(), XCODE_CATALOG)

    def test_set_existing_key_clears_stale_and_keeps_other_languages(self):
        self.run_ok("set", self.path, "--key", "Items %lld", "--lang", "de", "--value", "%lld Dinge",
                    "--state", "translated")
        entry = self.strings()["Items %lld"]
        self.assertNotIn("extractionState", entry)
        self.assertEqual(sorted(entry["localizations"]), ["de", "nl"])

    def test_delete_missing_key_fails_without_writing(self):
        result = run_script(SCRIPT, "delete", self.path, "--key", "Hello", "--key", "Nope")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.path.read_text(), XCODE_CATALOG)

    def test_rename_key(self):
        self.run_ok("rename-key", self.path, "--from", "Hello", "--to", "Aloha")
        strings = self.strings()
        self.assertEqual(list(strings), ["", "Aloha", "Items %lld", "Zebra"])
        self.assertEqual(strings["Aloha"]["localizations"]["nl"]["stringUnit"]["value"], "Hallo")

    def test_rename_key_replaces_empty_target_but_refuses_localized_one(self):
        self.run_ok("rename-key", self.path, "--from", "Hello", "--to", "Zebra")
        self.assertEqual(list(self.strings()), ["", "Items %lld", "Zebra"])
        result = run_script(SCRIPT, "rename-key", self.path, "--from", "Items %lld", "--to", "Zebra")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already has localizations", result.stderr)

    def test_create(self):
        new = self.path.parent / "InfoPlist.xcstrings"
        self.run_ok("create", new, "--source-language", "nl")
        self.assertEqual(new.read_text(),
                         '{\n  "sourceLanguage" : "nl",\n  "strings" : {\n\n  },\n  "version" : "1.0"\n}\n')
        self.assertNotEqual(run_script(SCRIPT, "create", new).returncode, 0)


@requires_git
class LintBaseTests(RepoTestCase):
    def test_reports_regressions_against_base_revision(self):
        path = self.write("Localizable.xcstrings", xc.dump(catalog({
            "Settings": {"localizations": {"nl": unit("Instellingen")}},
            "Profile": {"localizations": {"nl": unit("Profiel")}},
        })) + "\n")
        self.commit()
        git(self.repo, "tag", "base")
        path.write_text(xc.dump(catalog({
            "Settings": {"localizations": {"nl": unit("Settings")}},
            "Profile": {"localizations": {"nl": unit("Profiel", "needs_review")}},
        })) + "\n")
        findings = xc.lint(str(path), "base")
        self.assertTrue(any(f.startswith("changed into en text") for f in findings), findings)
        self.assertTrue(any("1 value(s) in nl changed from translated to needs_review" in f for f in findings),
                        findings)

    def test_missing_file_at_base(self):
        self.write("README", "x")
        self.commit()
        path = self.write("New.xcstrings", xc.dump(catalog({})))
        self.assertIn("no version of this file at HEAD", xc.lint(str(path), "HEAD"))


if __name__ == "__main__":
    unittest.main()
