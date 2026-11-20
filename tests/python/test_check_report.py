import tempfile
import unittest
from pathlib import Path

from support import load_script, run_script

SCRIPT = "accessibility-audit-ios/scripts/check_report.py"
cr = load_script(SCRIPT)

REFERENCE = """# Accessibility

| SC | Level | In 2.1 AA | What to check |
|---|---|---|---|
| 1.1.1 Non-text Content | A | yes | labels |
| 1.4.3 Contrast (Minimum) | AA | yes | contrast |
| 2.5.8 Target Size (Minimum) | AA | no | sizes |
"""

HEADER = "| SC | Level | In 2.1 AA | Status | Evidence |\n|---|---|---|---|---|\n"


def report(rows, before="", after="\n## Findings\n\n| 9.9.9 not a criterion row | x |\n"):
    return f"# Audit\n\n{before}## Criteria\n\n{HEADER}{rows}{after}"


GOOD_ROWS = ("| 1.1.1 Non-text Content | A | yes | **fail** | `Icon.swift:12` |\n"
             "| 1.4.3 Contrast (Minimum) | AA | yes | needs check | measured 4.4:1, the pass mark is 4.5:1 |\n"
             "| 2.5.8 Target Size (Minimum) | AA | no | not applicable | - |\n")


class CheckReportTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.reference = self.dir / "accessibility.md"
        self.reference.write_text(REFERENCE)

    def tearDown(self):
        self._tmp.cleanup()

    def check(self, text):
        path = self.dir / "report.md"
        path.write_text(text)
        return run_script(SCRIPT, "--report", path, "--reference", self.reference)

    def test_valid_report_passes_and_counts_statuses(self):
        result = self.check(report(GOOD_ROWS))
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Criteria in accessibility.md: 3; rows in report: 3", result.stdout)
        self.assertIn("Counts: fail 1, needs check 1, pass 0, not applicable 1", result.stdout)

    def test_only_rows_under_criteria_heading_count(self):
        rows = cr.report_rows(self._write(report(GOOD_ROWS, before="| 1.1.1 summary row | pass |\n\n")))
        self.assertEqual([i for i, _ in rows], ["1.1.1", "1.4.3", "2.5.8"])

    def test_missing_duplicate_and_unknown_criteria(self):
        rows = GOOD_ROWS.replace("| 2.5.8 Target Size (Minimum) | AA | no | not applicable | - |\n",
                                 "| 1.1.1 Non-text Content | A | yes | pass | again |\n"
                                 "| 4.1.2 Name, Role, Value | A | yes | pass | x |\n")
        result = self.check(report(rows))
        self.assertEqual(result.returncode, 1)
        self.assertIn("2.5.8: missing", result.stdout)
        self.assertIn("1.1.1: listed 2 times", result.stdout)
        self.assertIn("4.1.2: not in accessibility.md", result.stdout)

    def test_row_needs_exactly_one_status(self):
        rows = GOOD_ROWS.replace("**fail**", "failing").replace("needs check |", "pass | needs check |")
        result = self.check(report(rows))
        self.assertEqual(result.returncode, 1)
        self.assertIn("1.1.1: needs exactly one status cell", result.stdout)
        self.assertIn("1.4.3: needs exactly one status cell", result.stdout)

    def test_report_without_criteria_section(self):
        result = self.check("# Audit\n\n| 1.1.1 x | pass |\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("no `Criteria` section", result.stdout)

    def test_default_reference_is_found(self):
        path = Path(cr.__file__).parent / ".." / ".." / "ios-standards" / "references" / "accessibility.md"
        self.assertGreater(len(cr.criteria_ids(path)), 30)

    def _write(self, text):
        path = self.dir / "report.md"
        path.write_text(text)
        return path


if __name__ == "__main__":
    unittest.main()
