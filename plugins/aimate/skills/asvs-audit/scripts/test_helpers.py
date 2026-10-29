import csv
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).parent
import fingerprint as fp
import report as reports

requires_git = unittest.skipUnless(shutil.which("git"), "git is not installed")


def git(*args):
    subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test@example.com",
         "-c", "protocol.file.allow=always", *args],
        check=True, capture_output=True,
    )


def symlink_or_skip(test, link, target):
    try:
        link.symlink_to(target)
    except OSError as error:
        test.skipTest(f"symlinks unavailable: {error}")


class FingerprintTests(unittest.TestCase):
    def test_non_git_changes_and_exclusions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "app.py"
            source.write_text("original")
            original = fp.fingerprint(root)
            self.assertEqual(original, fp.fingerprint(root))
            for ignored in ("vendor/lib.py", "docs/app-ASVS-L1-audit-2026-10-28.md"):
                path = root / ignored
                path.parent.mkdir(exist_ok=True)
                path.write_text("ignored")
            self.assertEqual(original, fp.fingerprint(root))
            source.write_text("changed")
            self.assertNotEqual(original, fp.fingerprint(root))
            source.write_text("original")
            added = root / "new.py"
            added.write_text("new")
            self.assertNotEqual(original, fp.fingerprint(root))
            added.unlink()
            self.assertEqual(original, fp.fingerprint(root))
            source.rename(root / "renamed.py")
            self.assertNotEqual(original, fp.fingerprint(root))

    @requires_git
    def test_git_ignored_untracked_and_deleted_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            git("init", "-q", directory)
            (root / ".gitignore").write_text("ignored/\n")
            tracked = root / "tracked.py"
            tracked.write_text("tracked")
            git("-C", directory, "add", ".")
            original = fp.fingerprint(root)
            (root / "ignored").mkdir()
            (root / "ignored" / "data").write_text("ignored")
            self.assertEqual(original, fp.fingerprint(root))
            (root / "untracked.py").write_text("untracked")
            self.assertNotEqual(original, fp.fingerprint(root))
            tracked.unlink()
            self.assertNotIn(Path("tracked.py"), fp.scoped_files(root))
            self.assertEqual(8, len(fp.fingerprint(root)))

    @requires_git
    def test_submodule_and_nested_repository_use_git_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            library, app = Path(directory, "library"), Path(directory, "app")
            git("init", "-q", str(library))
            (library / "lib.py").write_text("one")
            git("-C", str(library), "add", ".")
            git("-C", str(library), "commit", "-qm", "one")
            git("init", "-q", str(app))
            (app / "app.py").write_text("app")
            git("-C", str(app), "submodule", "add", "-q", library.as_uri(), "lib")
            git("-C", str(app), "add", ".")
            pinned = fp.fingerprint(app)
            (app / "lib" / "lib.py").write_text("unstaged checkout change")
            self.assertEqual(pinned, fp.fingerprint(app))
            git("-C", str(app / "lib"), "commit", "-qam", "two")
            git("-C", str(app), "add", "lib")
            self.assertNotEqual(pinned, fp.fingerprint(app))
            nested = app / "nested"
            git("init", "-q", str(nested))
            (nested / "inner.py").write_text("inner")
            with_nested = fp.fingerprint(app)
            self.assertIn(Path("nested"), fp.scoped_files(app))
            (nested / "inner.py").write_text("changed")
            self.assertEqual(with_nested, fp.fingerprint(app))

    def test_symlink_is_not_followed_and_type_changes_are_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            link = root / "link"
            symlink_or_skip(self, link, "missing-target")
            original = fp.fingerprint(root)
            self.assertEqual(original, fp.fingerprint(root))
            link.unlink()
            link.write_text("missing-target")
            self.assertNotEqual(original, fp.fingerprint(root))

    def test_empty_scope_and_git_errors_are_not_fingerprints(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "empty"):
                fp.fingerprint(Path(directory))
            with patch.object(fp.subprocess, "run") as run:
                run.return_value.returncode = 128
                run.return_value.stderr = b"fatal: detected dubious ownership"
                with self.assertRaisesRegex(ValueError, "Git scope check failed"):
                    fp.fingerprint(Path(directory))

    def test_missing_git_uses_filesystem_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "app.py").write_text("source")
            with patch.object(fp.subprocess, "run", side_effect=FileNotFoundError):
                self.assertEqual(8, len(fp.fingerprint(root)))

    def test_file_read_failure_is_not_a_fingerprint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "app.py").write_text("source")
            with patch.object(Path, "open", side_effect=PermissionError("blocked")):
                with self.assertRaises(PermissionError):
                    fp.fingerprint(root)


class ReportTests(unittest.TestCase):
    def setUp(self):
        with (reports.SKILL / "assets/OWASP_Application_Security_Verification_Standard_5.0.0_L1_en.csv").open(
            encoding="utf-8", newline="",
        ) as source:
            self.requirements = list(csv.DictReader(source))
        self.metadata = {
            "project_name": "sample", "app_version": "unknown", "git_commit_hash": "abc1234",
            "report_date": "2026-10-28", "skill_version": "3.0.0",
            "coordinator_model": "unknown", "worker_models": "unknown",
            "model_provenance": "host did not report models", "execution_mode": "one-model",
            "executive_summary": "Review the verified findings.",
            "dependency_audit_statement": "No dependency audit could run.",
            "dependency_audit_summary": "The package manager was unavailable.",
            "conclusion_text": "Resolve the findings.",
            "components": [{
                "component": "API", "component_path": ".", "language": "Python",
                "framework": "None", "database": "None", "auth_method": "None",
                "key_libraries": "None",
            }],
        }
        sections = []
        for n, requirement in enumerate(self.requirements, 1):
            req_id = requirement["req_id"]
            status = {10: "FAIL", 16: "NEEDS_REVIEW", 23: "N/A", 49: "FAIL"}.get(n, "PASS")
            finding = review = rejected = ""
            checked = rejected_count = 0
            short_evidence = "Verified control"
            if n == 1:
                checked = rejected_count = 1
                rejected = "- #1 `src/cache.py:1`: harmless cache key."
            if n == 49:
                checked = 1
                finding = (
                    f"### #{n} {req_id} Authorization: Mass assignment\n\n"
                    "- **Severity**: 🟠 High\n"
                    "- **Description**: A client supplies its own role.\n"
                    "- **Locations**:\n\n"
                    "  | Location | Code | Why it fails | Severity |\n"
                    "  |---|---|---|---|\n"
                    "  | `src/profile.py:4` | `update(body)` | Accepts a role. | High |\n\n"
                    "- **Remediation**: Allow only editable fields."
                )
                short_evidence = "See finding #49, 1 location"
            if n == 10:
                finding = "See finding #49."
                short_evidence = "See finding #49, shared location"
            if status == "NEEDS_REVIEW":
                review = f"| #{n} {req_id} | `deployment` | Does the proxy set HSTS? | Proxy configuration |"
            blocks = {
                "finding": finding, "review": review,
                "verification": (
                    f"| #{n} {req_id} | Chapter | Requirement | "
                    f"{reports.STATUS_ICONS[status]} {status} | {short_evidence} |"
                ),
                "evidence": (
                    f"### #{n} {req_id}: {status}\n\n"
                    "- Searched: `git grep -n -F control`: 0 hits, 0 first-party"
                ),
                "rejected": rejected,
            }
            sections.append(
                f"## #{n}\nStatus: {status}. Candidates: {checked} checked, {rejected_count} rejected.\n"
                + self.blocks(blocks) + f"\n<!-- end #{n} -->"
            )
        sections.append(
            "## other-findings\nCandidates: 0 checked, 0 rejected.\n"
            + self.blocks({
                "finding": "", "review": "", "verification": "",
                "evidence": "### Other-findings checklist\n\n- Searched: `secrets`: 0 hits, 0 first-party",
                "rejected": "",
            }) + "\n<!-- end other-findings -->"
        )
        self.verdicts = "\n\n".join(sections)

    def blocks(self, values):
        return "\n".join(f"<!-- {key} -->\n{values[key]}" for key in reports.BLOCKS)

    def test_complete_report_counts_and_shared_findings(self):
        rendered = reports.assemble(self.metadata, self.verdicts)
        self.assertIn("❌ FAIL: 2 (🔴 Critical 0 · 🟠 High 2", rendered)
        self.assertIn("✅ PASS: 66", rendered)
        self.assertIn("**Compliance score**: 95.7%, up to 97.1%", rendered)
        self.assertIn("2 candidate failure locations checked, 1 rejected", rendered)
        findings = rendered.split("## Findings\n", 1)[1].split("## Other findings\n", 1)[0]
        self.assertIn("### #49 V8.3.1", findings)
        self.assertNotIn("### #10", findings)
        self.assertIn("| #10 V2.2.1 |", rendered)
        self.assertNotIn("{{", rendered)
        self.assertNotIn("<!--", rendered)

    def test_incomplete_duplicate_and_wrong_requirement_are_rejected(self):
        for invalid in (
            self.verdicts.replace("<!-- end #70 -->", ""),
            self.verdicts.replace("## #2\n", "## #1\n"),
            self.verdicts.replace("| #1 V1.2.1 |", "| #1 V1.2.2 |"),
            self.verdicts.replace("<!-- evidence -->", "<!-- missing -->", 1),
        ):
            with self.subTest(invalid=invalid[:50]), self.assertRaises(ValueError):
                reports.assemble(self.metadata, invalid)

    def test_review_and_shared_reference_must_be_valid(self):
        for invalid in (
            self.verdicts.replace("`deployment` | Does", "`unknown` | Does"),
            self.verdicts.replace("See finding #49.", "See finding #1."),
            self.verdicts.replace(
                "## #10\nStatus: FAIL. Candidates: 0 checked, 0 rejected.",
                "## #10\nStatus: FAIL. Candidates: 1 checked, 0 rejected.",
            ),
        ):
            with self.subTest(invalid=invalid[:50]), self.assertRaises(ValueError):
                reports.assemble(self.metadata, invalid)

    def test_missing_metadata_is_an_error(self):
        del self.metadata["report_date"]
        with self.assertRaisesRegex(ValueError, "report_date"):
            reports.assemble(self.metadata, self.verdicts)

    def test_other_findings_are_sorted_numbered_and_counted(self):
        low = (
            "### O: Hardening\n\n- **Severity**: 🟢 Low\n\n"
            "  | Location | Code | Why it is a problem |\n"
            "  |---|---|---|\n"
            "  | `src/z.py:1` | `setting` | Hardening gap. |"
        )
        high = low.replace("Hardening", "Dependency").replace("🟢 Low", "🟠 High")
        verdicts = self.verdicts.replace(
            "## other-findings\nCandidates: 0 checked, 0 rejected.\n<!-- finding -->\n",
            "## other-findings\nCandidates: 0 checked, 0 rejected.\n<!-- finding -->\n"
            + low + "\n\n" + high + "\n",
        )
        rendered = reports.assemble(self.metadata, verdicts)
        self.assertIn("### O1: Dependency", rendered)
        self.assertIn("### O2: Hardening", rendered)
        self.assertIn("**Other findings**: 2 (🔴 0 · 🟠 1 · 🟡 0 · 🟢 1)", rendered)

    def test_cli_writes_only_a_complete_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "metadata.json").write_text(json.dumps(self.metadata), encoding="utf-8")
            verdicts = root / "verdicts.md"
            verdicts.write_text(self.verdicts, encoding="utf-8")
            output = root / "report.md"
            command = [
                sys.executable, "-B", str(SCRIPTS / "report.py"),
                "--metadata", str(root / "metadata.json"),
                "--verdicts", str(verdicts), "--output", str(output),
            ]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            expected = reports.assemble(self.metadata, self.verdicts)
            self.assertEqual(expected, output.read_text(encoding="utf-8"))
            verdicts.write_text(self.verdicts.replace("<!-- end #70 -->", ""), encoding="utf-8")
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(1, result.returncode)
            self.assertIn("unfinished section", result.stderr)
            self.assertEqual(expected, output.read_text(encoding="utf-8"))

    def test_cli_accepts_byte_order_mark_and_windows_line_endings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            metadata, verdicts = root / "metadata.json", root / "verdicts.md"
            metadata.write_text(json.dumps(self.metadata), encoding="utf-8-sig")
            verdicts.write_bytes(self.verdicts.replace("\n", "\r\n").encode("utf-8-sig"))
            output = root / "report.md"
            result = subprocess.run([
                sys.executable, "-B", str(SCRIPTS / "report.py"), "--metadata", str(metadata),
                "--verdicts", str(verdicts), "--output", str(output),
            ], capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(
                reports.assemble(self.metadata, self.verdicts),
                output.read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
