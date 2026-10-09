"""Acceptance tests for wcag-audit deterministic components. Run: python3 -m unittest discover -s tests -v"""
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCAN = os.path.join(SKILL, "scripts", "scan.py")
REPORT = os.path.join(SKILL, "scripts", "report.py")
FIXTURE = os.path.join(SKILL, "tests", "fixtures", "sample-site")
EXPECTED = os.path.join(SKILL, "tests", "fixtures", "sample-site.expected.json")
ROWS = list(csv.DictReader(open(os.path.join(SKILL, "assets", "wcag-2.2-aa.csv"), encoding="utf-8")))
LIMIT_S = 120


def run(*args):
    t = time.time()
    p = subprocess.run([sys.executable, *args], capture_output=True, text=True, timeout=LIMIT_S)
    p.elapsed = time.time() - t
    return p


def final_doc(overrides=None, drop=(), models=("model-a", "model-b")):
    """A valid 55-row final.json for the fixture, mirroring what a coordinator would write."""
    v = []
    for r in ROWS:
        if r["sc_id"] in drop:
            continue
        if r["static_analyzable"] == "no":
            e = {"verdict": "NEEDS_REVIEW", "evidence": "rendering-dependent", "verify": f"Check {r['sc_id']} in a browser", "priority": "Serious"}
        else:
            e = {"verdict": "PASS", "evidence": "index.html:2 <html lang=\"en\">"}
        e["sc_id"] = r["sc_id"]
        v.append(e)
    by = {x["sc_id"]: x for x in v}
    by.get("1.1.1", {}).update({"verdict": "FAIL", "severity": "Serious", "evidence": "broken.html:8 <img src=\"chart.png\"> no alt",
                                "instances": ["broken.html:8 <img> missing alt"], "total": "1",
                                "remediation": "Add a text alternative describing the chart data."})
    for sid, patch in (overrides or {}).items():
        by[sid] = {**by.get(sid, {"sc_id": sid}), **patch}
    meta = {"project": "sample-site", "target": FIXTURE, "commit": "unknown", "stack": "Plain HTML",
            "scope": "whole fixture", "coordinator_model": "coord", "evaluator_models": list(models), "date": "2026-10-08"}
    return {"meta": meta, "verdicts": list(by.values())}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def write(self, name, obj):
        p = os.path.join(self.tmp, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(obj if isinstance(obj, str) else json.dumps(obj))
        return p

    def build(self, doc, *extra, name="r.md"):
        out = os.path.join(self.tmp, "docs", name)
        return run(REPORT, "build", self.write("final.json", doc), "--out", out, *extra), out


class T01_Checklist(unittest.TestCase):
    def test_55_rows_levels_columns(self):
        self.assertEqual(len(ROWS), 55)
        self.assertEqual(len({r["sc_id"] for r in ROWS}), 55)
        self.assertEqual(list(ROWS[0].keys()), ["sc_id", "name", "level", "wcag_version", "static_analyzable", "check_hint"])
        self.assertEqual(sum(r["level"] == "A" for r in ROWS), 31)
        self.assertEqual(sum(r["level"] == "AA" for r in ROWS), 24)
        self.assertNotIn("4.1.1", {r["sc_id"] for r in ROWS})
        self.assertTrue(all(r["static_analyzable"] in ("yes", "partial", "no") for r in ROWS))

    def test_rendering_dependent_flags(self):
        flags = {r["sc_id"]: r["static_analyzable"] for r in ROWS}
        for sid in ("1.4.3", "1.4.10", "1.4.11", "2.4.7"):
            self.assertEqual(flags[sid], "no", sid)

    def test_skill_frontmatter_and_links(self):
        text = open(os.path.join(SKILL, "SKILL.md"), encoding="utf-8").read()
        fm = text.split("---")[1]
        self.assertRegex(fm, r"\nname: wcag-audit\n")
        self.assertIn("[FRONTIER REASONING MODEL REQUIRED]", fm)
        self.assertNotRegex(text, r"Opus 4\.6|GPT-5\.5")
        self.assertRegex(fm, r"wcag-version: 2\.2\.0")
        self.assertIn("argument-hint:", fm)
        for link in re.findall(r"\]\(\./([^)]+)\)", text):
            self.assertTrue(os.path.exists(os.path.join(SKILL, link)), link)
        for ref in ("REPORT-TEMPLATE.md", "evidence-patterns.md", "severity-guidance.md", "framework-notes.md", "EXAMPLES.md"):
            self.assertTrue(os.path.isfile(os.path.join(SKILL, "references", ref)), ref)


class T02_Scan(Base):
    def scan(self, target):
        out = os.path.join(self.tmp, "inv.json")
        p = run(SCAN, target, "--out", out)
        return p, (json.load(open(out)) if p.returncode == 0 else None)

    def test_known_violations_found_with_lines(self):
        p, inv = self.scan(FIXTURE)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertLess(p.elapsed, LIMIT_S)
        got = {(g["sc_id"], g["rule"], i["file"], i["line"]) for g in inv["lead_groups"] for i in g["instances"]}
        expected = {("1.1.1", "img-missing-alt", "broken.html", 8), ("3.1.1", "html-no-lang", "broken.html", 2),
                    ("2.4.2", "document-no-title", "broken.html", 2), ("1.3.5", "personal-input-no-autocomplete-token", "broken.html", 10),
                    ("1.3.5", "personal-input-no-autocomplete-token", "broken.html", 17),
                    ("3.3.2", "input-no-label-hook", "broken.html", 10), ("2.4.4", "ambiguous-link-text", "broken.html", 12),
                    ("2.4.3", "positive-tabindex", "broken.html", 13), ("4.1.2", "iframe-no-title", "broken.html", 14),
                    ("1.2.2", "video-no-track", "broken.html", 15), ("1.4.4", "viewport-blocks-zoom", "broken.html", 4),
                    ("4.1.2", "click-on-non-interactive-no-role", "broken.html", 7),
                    ("2.1.1", "click-on-non-interactive-no-keyboard", "broken.html", 7)}
        self.assertEqual(expected - got, set(), "missing expected leads")
        # '<img' inside a quoted script string is not markup.
        self.assertNotIn(("1.1.1", "img-missing-alt", "broken.html", 18), got)

    def test_accessible_example_has_no_leads(self):
        _, inv = self.scan(FIXTURE)
        noisy = [i for g in inv["lead_groups"] for i in g["instances"] if i["file"] == "index.html"]
        self.assertEqual(noisy, [])

    def test_manual_case_is_lead_not_finding(self):
        _, inv = self.scan(FIXTURE)
        g = [g for g in inv["lead_groups"] if g["sc_id"] == "2.4.7"]
        self.assertTrue(g and g[0]["instances"][0]["file"] == "styles.css")
        self.assertIn("not findings", inv["note"])

    def test_applicability_features(self):
        _, inv = self.scan(FIXTURE)
        f = inv["features"]
        self.assertGreater(f["video"]["count"], 0)
        self.assertEqual(f["audio"]["count"], 0)
        self.assertEqual(f["caption_track"]["count"], 0)
        self.assertEqual(f["device_motion"]["count"], 0)
        self.assertIn("Plain HTML", inv["stack"])

    def test_missing_target(self):
        p, _ = self.scan(os.path.join(self.tmp, "nope"))
        self.assertEqual(p.returncode, 2)

    def test_empty_target(self):
        d = os.path.join(self.tmp, "empty")
        os.makedirs(d)
        p, _ = self.scan(d)
        self.assertEqual(p.returncode, 2)

    def test_exclusions_and_secrets(self):
        d = os.path.join(self.tmp, "repo")
        os.makedirs(os.path.join(d, "node_modules", "lib"))
        os.makedirs(os.path.join(d, "dist"))
        open(os.path.join(d, "node_modules", "lib", "x.html"), "w").write("<img src=a>")
        open(os.path.join(d, "dist", "y.html"), "w").write("<img src=a>")
        open(os.path.join(d, "app.min.js"), "w").write("x")
        open(os.path.join(d, ".env"), "w").write("SECRET_TOKEN=abc123")
        open(os.path.join(d, "page.html"), "w").write('<html lang="en"><title>t</title><img src="a" alt="x"></html>')
        p, inv = self.scan(d)
        self.assertEqual(p.returncode, 0)
        blob = json.dumps(inv)
        self.assertNotIn("abc123", blob)
        self.assertNotIn("node_modules", blob)
        self.assertNotIn("dist/", blob)
        self.assertEqual(inv["counts"]["files_scanned"], 1)
        self.assertEqual(inv["counts"]["skipped_sensitive"], 1)

    def test_max_files_bound(self):
        d = os.path.join(self.tmp, "many")
        os.makedirs(d)
        for i in range(30):
            open(os.path.join(d, f"p{i}.html"), "w").write("<p>x</p>")
        out = os.path.join(self.tmp, "inv.json")
        p = run(SCAN, d, "--out", out, "--max-files", "10")
        inv = json.load(open(out))
        self.assertEqual(inv["counts"]["files_scanned"], 10)
        self.assertTrue(inv["counts"]["truncated_at_max_files"])

    def test_deterministic(self):
        _, a = self.scan(FIXTURE)
        _, b = self.scan(FIXTURE)
        self.assertEqual(a, b)

    def test_broken_skip_link(self):
        d = os.path.join(self.tmp, "site")
        os.makedirs(d)
        open(os.path.join(d, "layout.html"), "w").write('<html lang="en"><title>t</title>\n<a href="#main-content">Skip to main content</a>\n<a href="#top">Skip to nav</a></html>')
        open(os.path.join(d, "ok.html"), "w").write('<main id="main-content">x</main>')
        open(os.path.join(d, "article.html"), "w").write('<div>\n<main class="article" role="main">x</main></div>')
        _, inv = self.scan(d)
        got = {(g["rule"].split(" ")[0], i["file"], i["line"]) for g in inv["lead_groups"] if g["sc_id"] == "2.4.1" for i in g["instances"]}
        self.assertIn(("main-without-skip-target", "article.html", 2), got)
        self.assertIn(("skip-link-target-missing", "layout.html", 3), got)
        self.assertNotIn("ok.html", {f for _, f, _ in got})


class T03_Build(Base):
    def test_valid_report(self):
        p, out = self.build(final_doc(), "--verify-citations", FIXTURE)
        self.assertEqual(p.returncode, 0, p.stdout)
        text = open(out, encoding="utf-8").read()
        rows = re.findall(r"^\| (\d\.\d+\.\d+) \| [^|]+ \| (?:A|AA) \|", text, re.M)
        self.assertEqual(rows, [r["sc_id"] for r in ROWS])
        self.assertIn("not a certified conformance claim", text)
        for regime in ("EN 301 549", "Section 508", "ADA", "European Accessibility Act"):
            self.assertIn(regime, text)
        self.assertRegex(text, r"### 1\.1\.1 .*❌ FAIL — Serious")
        self.assertRegex(text, r"\| 1\.4\.3 \| Contrast \(Minimum\) \| AA \| ⚠️ NEEDS_REVIEW")
        self.assertIn("| Serious | 1 | 1.1.1 |", text)
        self.assertIn("dual-model: model-a + model-b", text)
        c = run(REPORT, "check", out)
        self.assertEqual(c.returncode, 0, c.stdout)

    def test_reproducible_output(self):
        _, out1 = self.build(final_doc(), name="a.md")
        _, out2 = self.build(final_doc(), name="b.md")
        self.assertEqual(open(out1).read(), open(out2).read())

    def test_existing_report_not_overwritten(self):
        _, out = self.build(final_doc())
        p, _ = self.build(final_doc())
        self.assertEqual(p.returncode, 2)
        self.assertIn("already exists", p.stderr)
        p, _ = self.build(final_doc(), "--overwrite")
        self.assertEqual(p.returncode, 0, p.stdout)

    def assertRejected(self, doc, msg, *extra):
        p, out = self.build(doc, *extra)
        self.assertEqual(p.returncode, 1, p.stdout)
        self.assertIn(msg, p.stdout)
        self.assertFalse(os.path.exists(out), "report must not be written on validation failure")

    def test_gate_no_row_cannot_pass(self):
        self.assertRejected(final_doc({"1.4.3": {"verdict": "PASS", "evidence": "styles.css:1 ok"}}), "1.4.3: static_analyzable=no")

    def test_gate_no_row_cannot_fail(self):
        self.assertRejected(final_doc({"2.4.7": {"verdict": "FAIL", "severity": "Serious", "instances": ["styles.css:4 outline:none"],
                                                  "total": "1", "remediation": "x", "evidence": "styles.css:4"}}), "2.4.7: static_analyzable=no")

    def test_missing_row(self):
        self.assertRejected(final_doc(drop={"3.3.8"}), "3.3.8: missing verdict")

    def test_unknown_and_invalid(self):
        self.assertRejected(final_doc({"4.1.1": {"verdict": "PASS", "evidence": "index.html:1"}}), "4.1.1: not a WCAG 2.2")
        self.assertRejected(final_doc({"1.3.1": {"verdict": "MAYBE"}}), "invalid verdict")

    def test_fail_requirements(self):
        self.assertRejected(final_doc({"1.1.1": {"instances": []}}), "1-10 representative instances")
        self.assertRejected(final_doc({"1.1.1": {"instances": [f"broken.html:{i} x" for i in range(1, 12)]}}), "1-10 representative")
        self.assertRejected(final_doc({"1.1.1": {"severity": "High"}}), "severity must be")
        self.assertRejected(final_doc({"1.1.1": {"instances": ["somewhere"]}}), "lacks file:line")

    def test_pass_needs_citation_and_review_needs_verify(self):
        self.assertRejected(final_doc({"3.1.1": {"evidence": "looks fine"}}), "PASS needs a file:line")
        self.assertRejected(final_doc({"1.4.10": {"verify": ""}}), "needs a concrete 'verify'")

    def test_generic_needs_review_rejected(self):
        doc = final_doc({"1.3.1": {"verdict": "NEEDS_REVIEW", "evidence": "verify across CMS content", "verify": "check"}})
        self.assertRejected(doc, "1.3.1: NEEDS_REVIEW on a partial row must cite")
        p, _ = self.build(final_doc({"1.4.3": {"evidence": "rendered colours"}}))
        self.assertEqual(p.returncode, 0, p.stdout)  # 'no' rows need no citation

    def test_manual_plan_grouped_by_session(self):
        p, out = self.build(final_doc({"1.4.10": {"verify": "translate with |t and recheck"}}))
        self.assertEqual(run(REPORT, "check", out).returncode, 0)  # escaped pipe in a cell
        text = open(out, encoding="utf-8").read()
        self.assertRegex(text, r"### Visual and zoom session \(\d+ checks\)")
        self.assertRegex(text, r"### Keyboard session \(\d+ checks\)")
        self.assertIn("outside the scope of this audit", text)

    def test_models_must_be_distinct(self):
        self.assertRejected(final_doc(models=("m", "m")), "two distinct models")
        doc = final_doc(models=("m",))
        doc["meta"]["single_model_authorized"] = True
        p, _ = self.build(doc)
        self.assertEqual(p.returncode, 0, p.stdout)

    def test_fabricated_citation_rejected(self):
        self.assertRejected(final_doc({"1.1.1": {"instances": ["broken.html:999 <img>"]}}), "beyond end of file", "--verify-citations", FIXTURE)
        self.assertRejected(final_doc({"1.1.1": {"instances": ["ghost.html:3 <img>"]}}), "cited file not found", "--verify-citations", FIXTURE)

    def test_unique_bare_filename_accepted(self):
        d = os.path.join(self.tmp, "t", "deep", "dir")
        os.makedirs(d)
        open(os.path.join(d, "broken.html"), "w").write("\n" * 20)
        open(os.path.join(d, "index.html"), "w").write("\n" * 20)
        p, _ = self.build(final_doc(), "--verify-citations", os.path.join(self.tmp, "t"))
        self.assertEqual(p.returncode, 0, p.stdout)
        os.makedirs(os.path.join(self.tmp, "t", "other"))
        open(os.path.join(self.tmp, "t", "other", "broken.html"), "w").write("x\n" * 20)
        os.remove(os.path.join(self.tmp, "docs", "r.md"))
        self.assertRejected(final_doc(), "bare name not unique", "--verify-citations", os.path.join(self.tmp, "t"))

    def test_malformed_json(self):
        p = run(REPORT, "build", self.write("bad.json", "{not json"), "--out", os.path.join(self.tmp, "x.md"))
        self.assertEqual(p.returncode, 2)

    def test_partial(self):
        doc = final_doc(drop={"4.1.2", "4.1.3"})
        doc["meta"]["stop_reason"] = "budget exhausted"
        p, out = self.build(doc, "--partial", name="x-PARTIAL.md")
        self.assertEqual(p.returncode, 0, p.stdout)
        text = open(out).read()
        self.assertIn("PARTIAL REPORT", text)
        self.assertIn("Not evaluated: 4.1.2, 4.1.3", text)
        self.assertEqual(text.count("⏳ NOT_EVALUATED"), 3)  # 2 rows + scorecard


class T04_Merge(Base):
    def test_disagreement_and_union(self):
        a = final_doc()
        b = final_doc({"3.1.1": {"verdict": "FAIL", "severity": "Serious", "instances": ["broken.html:2 <html> no lang"],
                                 "total": "1", "remediation": "add lang"},
                       "1.1.1": {"instances": ["broken.html:8 <img> missing alt", "other.html:3 <img> missing alt"]}})
        a["meta"]["model"], b["meta"]["model"] = "model-a", "model-b"
        b["verdicts"] = [x for x in b["verdicts"] if x["sc_id"] != "2.2.1"]
        out = os.path.join(self.tmp, "m.json")
        p = run(REPORT, "merge", self.write("a.json", a), self.write("b.json", b), "--out", out)
        self.assertEqual(p.returncode, 0, p.stderr)
        m = json.load(open(out))
        self.assertIn("3.1.1", m["disagree"])
        self.assertIn("2.2.1", m["missing"])
        self.assertIn("2.2.1", m["disagree"])
        row = next(r for r in m["rows"] if r["sc_id"] == "1.1.1")
        self.assertEqual(row["union_instances"], ["broken.html:8 <img> missing alt", "other.html:3 <img> missing alt"])
        self.assertEqual(m["agree"] + len(m["disagree"]), 55)
        flags = {r["sc_id"]: r["static_analyzable"] for r in ROWS}
        self.assertIn("1.1.1", m["verify"])  # agreed FAIL
        self.assertNotIn("3.1.1", m["verify"])  # disagreement goes to arbitrate instead
        self.assertTrue(all(flags[s] == "partial" or s == "1.1.1" for s in m["verify"]))
        self.assertFalse(any(flags[s] == "yes" for s in m["verify"] if s != "1.1.1"))

    def test_same_model_warns(self):
        a = final_doc()
        a["meta"]["model"] = "same"
        p = run(REPORT, "merge", self.write("a.json", a), self.write("b.json", a), "--out", os.path.join(self.tmp, "m.json"))
        self.assertIn("WARNING", p.stdout)

    def test_agreed_needs_review_routing(self):
        nr = lambda ev: {"verdict": "NEEDS_REVIEW", "evidence": ev, "verify": "v"}
        doc = final_doc({"2.4.2": nr("index.html:6 title wiring"),  # yes row
                         "1.3.1": nr("index.html:12 depends on editorial content"),  # partial + content
                         "1.3.2": nr("index.html:12 CSS order")})  # partial, runtime
        out = os.path.join(self.tmp, "m.json")
        run(REPORT, "merge", self.write("a.json", doc), self.write("b.json", doc), "--out", out)
        m = json.load(open(out))
        self.assertIn("2.4.2", m["verify"])
        self.assertIn("1.3.1", m["verify"])
        self.assertNotIn("1.3.2", m["verify"])
        self.assertNotIn("1.4.3", m["verify"])


class T05_Check(Base):
    def test_check_detects_tampering(self):
        _, out = self.build(final_doc())
        text = open(out).read()
        bad = text.replace("| 1.4.3 | Contrast (Minimum) | AA | ⚠️ NEEDS_REVIEW", "| 1.4.3 | Contrast (Minimum) | AA | ✅ PASS")
        p = run(REPORT, "check", self.write("t.md", bad))
        self.assertEqual(p.returncode, 1)
        self.assertIn("rendering-dependent", p.stdout)
        p = run(REPORT, "check", self.write("t2.md", text.replace("not a certified conformance claim", "")))
        self.assertIn("disclaimer missing", p.stdout)


class T06_Expected(Base):
    """Expected verdicts for the fixture; set WCAG_RUN_FINAL=/path/final.json to score a real audit run."""

    def setUp(self):
        super().setUp()
        self.exp = json.load(open(EXPECTED, encoding="utf-8"))["verdicts"]

    def test_expected_file_is_consistent(self):
        flags = {r["sc_id"]: r["static_analyzable"] for r in ROWS}
        self.assertEqual(sorted(self.exp, key=lambda s: [int(x) for x in s.split(".")]), [r["sc_id"] for r in ROWS])
        for sid, e in self.exp.items():
            self.assertTrue(set(e["allowed"]) <= {"PASS", "N/A", "NEEDS_REVIEW", "FAIL"}, sid)
            if flags[sid] == "no":
                self.assertFalse({"PASS", "FAIL"} & set(e["allowed"]), f"{sid} is rendering-dependent")
        for sid in ("1.1.1", "1.3.5", "2.4.2", "3.1.1"):
            self.assertEqual(self.exp[sid]["allowed"], ["FAIL"])
        for sid in ("1.4.3", "1.4.10", "2.4.7"):
            self.assertEqual(self.exp[sid]["allowed"], ["NEEDS_REVIEW"])

    def matching_doc(self):
        over = {}
        for sid, e in self.exp.items():
            v = e["allowed"][0]
            if v == "FAIL":
                c = e["cite"][0]
                over[sid] = {"verdict": "FAIL", "severity": "Serious", "instances": [c + " x"], "total": "1",
                             "remediation": "fix", "evidence": c}
            elif v == "NEEDS_REVIEW":
                over[sid] = {"verdict": v, "evidence": "index.html:2 x", "verify": "check"}
            elif v == "N/A":
                over[sid] = {"verdict": v, "evidence": "N/A - absent"}
            else:
                over[sid] = {"verdict": v, "evidence": "index.html:2 ok"}
        return final_doc(over)

    def test_compare_match_and_mismatch(self):
        doc = self.matching_doc()
        p = run(REPORT, "compare", self.write("ok.json", doc), EXPECTED)
        self.assertEqual(p.returncode, 0, p.stdout)
        self.assertIn("55/55", p.stdout)
        for v in doc["verdicts"]:
            if v["sc_id"] == "1.4.3":
                v.update(verdict="PASS")
            if v["sc_id"] == "1.1.1":
                v.update(instances=["broken.html:80 x"], evidence="broken.html:80")
        p = run(REPORT, "compare", self.write("bad.json", doc), EXPECTED)
        self.assertEqual(p.returncode, 1)
        self.assertIn("1.4.3: got PASS", p.stdout)
        self.assertIn("1.1.1: FAIL cites none", p.stdout)

    @unittest.skipUnless(os.environ.get("WCAG_RUN_FINAL"), "set WCAG_RUN_FINAL to score a real audit run")
    def test_real_run(self):
        p = run(REPORT, "compare", os.environ["WCAG_RUN_FINAL"], EXPECTED)
        self.assertEqual(p.returncode, 0, p.stdout)


if __name__ == "__main__":
    unittest.main()
