#!/usr/bin/env python3
"""Deterministic merge, gate, render, and check for wcag-audit reports.

  report.py merge A.json B.json --out merged.json   # diff two evaluator outputs
  report.py build final.json --out REPORT.md [--partial] [--verify-citations TARGET]
  report.py check REPORT.md
  report.py compare final.json EXPECTED.json        # score a run against expected verdicts

Evaluator/final verdict file: {"meta": {...}, "verdicts": [ {sc_id, verdict, evidence, ...}, ... ]}
Exit codes: 0 ok, 1 validation failed, 2 bad input.
"""
import argparse
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "..", "assets", "wcag-2.2-aa.csv")
TEMPLATE = os.path.join(HERE, "..", "references", "REPORT-TEMPLATE.md")
VERDICTS = {"PASS": "✅ PASS", "N/A": "⚪ N/A", "NEEDS_REVIEW": "⚠️ NEEDS_REVIEW", "FAIL": "❌ FAIL"}
NOT_EVAL = "⏳ NOT_EVALUATED"
SEVERITIES = ["Critical", "Serious", "Moderate", "Minor"]
CITE = re.compile(r"([\w./@\-\[\]]+\.[A-Za-z0-9]+):(\d+)")
DISCLAIMER_MARK = "not a certified conformance claim"
# NEEDS_REVIEW justified by editor content contradicts the scope rule, so the coordinator re-checks it.
CONTENT_HINT = re.compile(r"\b(content|editor\w*|editorial|cms|author(ed|ing)?|route titl\w*)\b", re.I)
# Manual checks are grouped so a tester runs a few sessions instead of one task per criterion.
SESSIONS = [
    ("Keyboard", "2.1.1 2.1.2 2.1.4 2.2.1 2.2.2 1.4.2 2.4.1 2.4.3 2.4.7 2.5.1 2.5.2 2.5.4 2.5.7 3.2.1"),
    ("Visual and zoom", "1.3.4 1.4.1 1.4.3 1.4.4 1.4.5 1.4.10 1.4.11 1.4.12 1.4.13 2.3.1 2.4.11 2.5.8"),
    ("Screen reader", "1.1.1 1.3.1 1.3.2 1.3.3 2.4.2 2.4.4 2.4.6 2.5.3 3.1.1 3.1.2 4.1.2 4.1.3"),
    ("Forms and errors", "1.3.5 3.2.2 3.3.1 3.3.2 3.3.3 3.3.4 3.3.7 3.3.8"),
    ("Media", "1.2.1 1.2.2 1.2.3 1.2.4 1.2.5"),
    ("Navigation consistency", "2.4.5 3.2.3 3.2.4 3.2.6"),
]
SESSION_OF = {sid: name for name, ids in SESSIONS for sid in ids.split()}


def load_csv():
    with open(CSV_PATH, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    ids = [r["sc_id"] for r in rows]
    if len(rows) != 55 or len(set(ids)) != 55 or "4.1.1" in ids:
        sys.exit("ERROR: canonical CSV must have 55 unique rows and no 4.1.1")
    return rows


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        print(f"ERROR: cannot read {path}: {e}", file=sys.stderr)
        sys.exit(2)
    if isinstance(data, list):
        data = {"meta": {}, "verdicts": data}
    if not isinstance(data.get("verdicts"), list):
        print(f"ERROR: {path} has no 'verdicts' list", file=sys.stderr)
        sys.exit(2)
    return data


def index(verdicts):
    out, dupes = {}, []
    for v in verdicts:
        sid = str(v.get("sc_id", "")).strip()
        if sid in out:
            dupes.append(sid)
        out[sid] = v
    return out, dupes


def cmd_merge(a):
    rows = load_csv()
    A, B = load_json(a.a), load_json(a.b)
    ia, da = index(A["verdicts"])
    ib, db = index(B["verdicts"])
    merged, agree, disagree, missing, verify = [], 0, [], [], []
    for r in rows:
        sid = r["sc_id"]
        va, vb = ia.get(sid), ib.get(sid)
        ra = (va or {}).get("verdict")
        rb = (vb or {}).get("verdict")
        if not va or not vb:
            missing.append(sid)
        entry = {"sc_id": sid, "name": r["name"], "static_analyzable": r["static_analyzable"],
                 "a": va, "b": vb, "status": "agree" if ra and ra == rb else "disagree"}
        if entry["status"] == "agree":
            agree += 1
            # Agreement between evaluators is not proof: consequential verdicts get a coordinator check.
            if ra == "FAIL" or (ra == "PASS" and r["static_analyzable"] == "partial"):
                verify.append(sid)
            elif ra == "NEEDS_REVIEW" and r["static_analyzable"] != "no" and (
                    r["static_analyzable"] == "yes" or CONTENT_HINT.search(va.get("evidence", "") + " " + vb.get("evidence", ""))):
                verify.append(sid)
            # Union of unique FAIL instances from both evaluators.
            if ra == "FAIL":
                inst = []
                for x in (va.get("instances", []) + vb.get("instances", [])):
                    if x not in inst:
                        inst.append(x)
                entry["union_instances"] = inst
        else:
            disagree.append(sid)
        merged.append(entry)
    res = {"meta_a": A.get("meta", {}), "meta_b": B.get("meta", {}), "agree": agree,
           "disagree": disagree, "verify": verify, "missing": missing, "duplicates": sorted(set(da + db)), "rows": merged}
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    ma, mb = A.get("meta", {}).get("model"), B.get("meta", {}).get("model")
    print(f"merged: {a.out} | agree={agree} disagree={len(disagree)} missing={len(missing)}")
    print("arbitrate:", ", ".join(disagree) or "none")
    print("verify:", ", ".join(verify) or "none")
    if not ma or not mb or ma == mb:
        print(f"WARNING: evaluator models not distinct/explicit (a={ma!r}, b={mb!r})")
    return 0


def resolve(target, path, cache={}):
    """Return the cited file under target; a bare filename is accepted if it is unique in the target."""
    full = os.path.join(target, path)
    if os.path.isfile(full) or "/" in path:
        return full if os.path.isfile(full) else None
    if target not in cache:
        names = {}
        for dp, dn, fns in os.walk(target):
            dn[:] = [d for d in dn if d not in ("node_modules", ".git", "vendor", "dist", "build")]
            for fn in fns:
                names.setdefault(fn, []).append(os.path.join(dp, fn))
        cache[target] = names
    hits = cache[target].get(path, [])
    return hits[0] if len(hits) == 1 else None


def validate(data, rows, partial, target):
    errs = []
    meta = data.get("meta", {})
    for k in ("project", "target", "commit", "stack", "scope", "coordinator_model", "evaluator_models"):
        if not meta.get(k):
            errs.append(f"meta.{k} missing")
    models = meta.get("evaluator_models") or []
    if not meta.get("single_model_authorized") and (len(models) != 2 or len(set(models)) != 2):
        errs.append("meta.evaluator_models must list two distinct models (or set single_model_authorized)")
    idx, dupes = index(data["verdicts"])
    for d in dupes:
        errs.append(f"{d}: duplicate verdict")
    known = {r["sc_id"] for r in rows}
    for sid in idx:
        if sid not in known:
            errs.append(f"{sid}: not a WCAG 2.2 A/AA criterion in the canonical CSV")
    for r in rows:
        sid, flag = r["sc_id"], r["static_analyzable"]
        v = idx.get(sid)
        if not v:
            if not partial:
                errs.append(f"{sid}: missing verdict")
            continue
        verdict = v.get("verdict")
        if verdict == "NOT_EVALUATED":
            if not partial:
                errs.append(f"{sid}: NOT_EVALUATED only allowed with --partial")
            continue
        if verdict not in VERDICTS:
            errs.append(f"{sid}: invalid verdict {verdict!r}")
            continue
        if not str(v.get("evidence", "")).strip():
            errs.append(f"{sid}: evidence empty")
        if flag == "no" and verdict in ("PASS", "FAIL"):
            errs.append(f"{sid}: static_analyzable=no permits only N/A or NEEDS_REVIEW, got {verdict}")
        if verdict == "PASS" and not CITE.search(v.get("evidence", "")):
            errs.append(f"{sid}: PASS needs a file:line citation in evidence")
        if verdict == "FAIL":
            if v.get("severity") not in SEVERITIES:
                errs.append(f"{sid}: FAIL severity must be one of {SEVERITIES}")
            inst = v.get("instances") or []
            if not 1 <= len(inst) <= 10:
                errs.append(f"{sid}: FAIL needs 1-10 representative instances, got {len(inst)}")
            for i in inst:
                if not CITE.search(i):
                    errs.append(f"{sid}: instance lacks file:line: {i!r}")
            if not str(v.get("total", "")).strip():
                errs.append(f"{sid}: FAIL needs total (e.g. '3' or 'at least 12')")
            if not str(v.get("remediation", "")).strip():
                errs.append(f"{sid}: FAIL needs remediation")
        if verdict == "NEEDS_REVIEW" and not str(v.get("verify", "")).strip():
            errs.append(f"{sid}: NEEDS_REVIEW needs a concrete 'verify' instruction")
        if verdict == "NEEDS_REVIEW" and flag != "no" and not CITE.search(v.get("evidence", "")):
            errs.append(f"{sid}: NEEDS_REVIEW on a {flag} row must cite the unresolved instance (file:line)")
        if target and verdict in ("PASS", "FAIL", "NEEDS_REVIEW"):
            text = v.get("evidence", "") + " " + " ".join(v.get("instances") or [])
            for path, line in CITE.findall(text):
                full = resolve(target, path)
                if not full:
                    errs.append(f"{sid}: cited file not found (or bare name not unique): {path}")
                    continue
                with open(full, encoding="utf-8", errors="replace") as f:
                    n = sum(1 for _ in f)
                if int(line) > n:
                    errs.append(f"{sid}: {path}:{line} beyond end of file ({n} lines)")
    return errs


def cell(s):
    return str(s).replace("|", "\\|").replace("\n", " ").strip()


def cmd_build(a):
    rows = load_csv()
    data = load_json(a.final)
    if os.path.exists(a.out) and not a.overwrite:
        print(f"ERROR: {a.out} already exists; reports are written once (use --overwrite to replace)", file=sys.stderr)
        return 2
    errs = validate(data, rows, a.partial, a.verify_citations)
    if errs:
        print("VALIDATION FAILED:", *errs, sep="\n  ")
        return 1
    meta, (idx, _) = data["meta"], index(data["verdicts"])
    counts = {k: 0 for k in VERDICTS}
    sev = {s: [] for s in SEVERITIES}
    table, findings, manual = [], [], {name: [] for name, _ in SESSIONS}
    not_eval = []
    for r in rows:
        sid = r["sc_id"]
        v = idx.get(sid) or {"verdict": "NOT_EVALUATED", "evidence": "not evaluated in this run"}
        vd = v["verdict"]
        if vd == "NOT_EVALUATED":
            not_eval.append(sid)
            label = NOT_EVAL
        else:
            counts[vd] += 1
            label = VERDICTS[vd]
        table.append(f"| {sid} | {cell(r['name'])} | {r['level']} | {label} | {cell(v.get('evidence', ''))} |")
        if vd == "FAIL":
            sev[v["severity"]].append(sid)
            inst = "\n".join(f"  - `{cell(i)}`" for i in v["instances"])
            findings.append(
                f"### {sid} {r['name']} (Level {r['level']}) — ❌ FAIL — {v['severity']}\n\n"
                f"- **Evidence:** {v['evidence']}\n- **Representative instances ({len(v['instances'])} shown, total {v['total']}):**\n{inst}\n"
                f"- **Remediation:** {v['remediation']}\n")
        elif vd == "NEEDS_REVIEW":
            manual[SESSION_OF[sid]].append(f"| {sid} | {cell(r['name'])} | {cell(v.get('priority', '—'))} | {cell(v['verify'])} |")
    evaluated = sum(counts.values())
    scorecard = "\n".join([
        "| Verdict | Count |", "|---|---|",
        *(f"| {VERDICTS[k]} | {counts[k]} |" for k in VERDICTS),
        *( [f"| {NOT_EVAL} | {len(not_eval)} |"] if not_eval else []),
        f"| **Total** | **{evaluated + len(not_eval)}** |"])
    severity = "\n".join(["| Severity | Count | Criteria |", "|---|---|---|",
                          *(f"| {s} | {len(sev[s])} | {', '.join(sev[s]) or '—'} |" for s in SEVERITIES)])
    models = meta.get("evaluator_models", [])
    mode = "single-model (user-authorized)" if meta.get("single_model_authorized") else \
        f"dual-model: {models[0]} + {models[1]}; arbitration by {meta['coordinator_model']}"
    partial_note = ""
    if a.partial:
        partial_note = (f"> **PARTIAL REPORT.** Stopping condition: {meta.get('stop_reason', 'not stated')}. "
                        f"Not evaluated: {', '.join(not_eval) or 'none'}. Not evaluated criteria are excluded "
                        "from verdict totals.\n")
    manual_blocks = [f"### {name} session ({len(rows_)} checks)\n\n| SC | Name | Priority | What to verify |\n|---|---|---|---|\n" + "\n".join(rows_)
                     for name, rows_ in manual.items() if rows_]
    subs = {
        "PROJECT": meta["project"], "DATE": meta.get("date", ""), "TARGET": meta["target"],
        "COMMIT": meta["commit"], "STACK": meta["stack"], "SCOPE": meta["scope"], "MODE": mode,
        "SCAN": meta.get("scan_summary", "—"), "PARTIAL_NOTE": partial_note,
        "SCORECARD": scorecard, "SEVERITY": severity, "TABLE": "\n".join(table),
        "FINDINGS": "\n".join(findings) or "No FAIL findings.",
        "MANUAL": (f"{sum(map(len, manual.values()))} checks in {len(manual_blocks)} test sessions.\n\n" + "\n\n".join(manual_blocks))
        if manual_blocks else "No NEEDS_REVIEW items.",
    }
    with open(TEMPLATE, encoding="utf-8") as f:
        out = f.read()
    for k, val in subs.items():
        out = out.replace("{{" + k + "}}", str(val))
    left = re.findall(r"\{\{[A-Z_]+\}\}", out)
    if left:
        print("ERROR: unfilled placeholders:", left)
        return 1
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"report: {a.out}")
    print(" ".join(f"{k}={counts[k]}" for k in VERDICTS) + (f" NOT_EVALUATED={len(not_eval)}" if not_eval else ""))
    return 0


def cmd_check(a):
    rows = load_csv()
    try:
        text = open(a.report, encoding="utf-8").read()
    except OSError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    errs = []
    found = re.findall(r"^\| (\d\.\d+\.\d+) \| [^|]+ \| (A|AA) \| ([^|]+) \|", text, re.M)
    ids = [f[0] for f in found]
    if ids != [r["sc_id"] for r in rows]:
        errs.append(f"conformance table must list the 55 criteria in canonical order (found {len(ids)})")
    flags = {r["sc_id"]: r["static_analyzable"] for r in rows}
    tally = {}
    for sid, _, label in found:
        label = label.strip()
        tally[label] = tally.get(label, 0) + 1
        if flags.get(sid) == "no" and label in (VERDICTS["PASS"], VERDICTS["FAIL"]):
            errs.append(f"{sid}: rendering-dependent criterion reported as {label}")
    for label, n in tally.items():
        m = re.search(r"^\| " + re.escape(label) + r" \| (\d+) \|", text, re.M)
        if not m or int(m.group(1)) != n:
            errs.append(f"scorecard count for {label} does not match table ({n})")
    fails = [sid for sid, _, l in found if l.strip() == VERDICTS["FAIL"]]
    for sid in fails:
        if not re.search(r"^### " + re.escape(sid) + r" .*❌ FAIL", text, re.M):
            errs.append(f"{sid}: FAIL lacks a detailed finding section")
    for sid, _, l in found:
        if l.strip() == VERDICTS["NEEDS_REVIEW"] and not re.search(r"^\| " + re.escape(sid) + r" \| (?:[^|\\]|\\.)+ \| (?:[^|\\]|\\.)+ \| (?:[^|\\]|\\.)+ \|$", text.split("## Manual verification plan")[-1], re.M):
            errs.append(f"{sid}: NEEDS_REVIEW lacks a manual verification row")
    if DISCLAIMER_MARK not in text:
        errs.append("compliance disclaimer missing")
    for regime in ("EN 301 549", "Section 508", "ADA", "European Accessibility Act"):
        if regime not in text:
            errs.append(f"regime reference missing: {regime}")
    if re.search(r"\{\{[A-Z_]+\}\}", text):
        errs.append("unfilled placeholder")
    if errs:
        print("CHECK FAILED:", *errs, sep="\n  ")
        return 1
    print(f"check OK: {len(ids)} rows, " + ", ".join(f"{k}={v}" for k, v in tally.items()))
    return 0


def cmd_compare(a):
    rows = load_csv()
    idx, _ = index(load_json(a.final)["verdicts"])
    try:
        with open(a.expected, encoding="utf-8") as f:
            exp = json.load(f)["verdicts"]
    except (OSError, ValueError, KeyError) as e:
        print(f"ERROR: cannot read expected file {a.expected}: {e}", file=sys.stderr)
        return 2
    misses = []
    for r in rows:
        sid = r["sc_id"]
        want = exp.get(sid)
        if not want:
            misses.append(f"{sid}: no expectation defined")
            continue
        got = (idx.get(sid) or {}).get("verdict")
        if got not in want["allowed"]:
            misses.append(f"{sid}: got {got}, expected {'|'.join(want['allowed'])}")
        elif got == "FAIL" and want.get("cite"):
            cited = " ".join(idx[sid].get("instances") or []) + " " + idx[sid].get("evidence", "")
            if not any(re.search(re.escape(c) + r"(?!\d)", cited) for c in want["cite"]):
                misses.append(f"{sid}: FAIL cites none of {want['cite']}")
    print(f"compare: {55 - len(misses)}/55 match")
    for m in misses:
        print("  " + m)
    return 1 if misses else 0


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    m = sp.add_parser("merge")
    m.add_argument("a")
    m.add_argument("b")
    m.add_argument("--out", required=True)
    b = sp.add_parser("build")
    b.add_argument("final")
    b.add_argument("--out", required=True)
    b.add_argument("--partial", action="store_true")
    b.add_argument("--verify-citations", metavar="TARGET")
    b.add_argument("--overwrite", action="store_true")
    c = sp.add_parser("check")
    c.add_argument("report")
    k = sp.add_parser("compare")
    k.add_argument("final")
    k.add_argument("expected")
    a = ap.parse_args()
    return {"merge": cmd_merge, "build": cmd_build, "check": cmd_check, "compare": cmd_compare}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
