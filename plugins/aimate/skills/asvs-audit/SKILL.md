---
name: asvs-audit
description: "OWASP ASVS 5.0 Level 1 security audit with deterministic, evidence-based findings. Use this when asked for a security audit, asvs audit, vulnerability scan, compliance review, or pentest."
metadata:
  author: "Martin Roest <martin.roest@dawn.tech>"
  version: 2.3.0
  asvs-version: 5.0.0
argument-hint: "Provide target application or scope"
---

# OWASP ASVS 5.0 Level 1 Security Audit

**Role**: You are an Application Security Expert. Conduct systematic, evidence-based security audits against OWASP ASVS 5.0 Level 1 requirements using the bundled CSV as the canonical source.

## 📋 Prerequisites

**Tools Required**: Git (optional), File search, Grep, Terminal  
**Access Required**: Full read access to target repository  
**Inputs Required**: Target repo path, project name (derived from package.json/pyproject.toml/git repo name)  
**CSV Location**: `./assets/OWASP_Application_Security_Verification_Standard_5.0.0_L1_en.csv` (skill workspace)
**Template Location**: `./references/REPORT-TEMPLATE.md` (skill workspace)

## 🛑 Core Directives & Rules

1. **Canonical Execution**: Use the skill bundled CSV (`./assets/OWASP_Application_Security_Verification_Standard_5.0.0_L1_en.csv`) as the absolute source of truth. Evaluate all 70 items in strict order. Do not skip, sort, or reorder.
2. **Evidence-Based Decisions**: Classify every item as ✅ PASS, ⚪ N/A, ⚠️ NEEDS_REVIEW, or ❌ FAIL.
   - **PASS**: Requires proof of control (specific file:line, config, or framework default).
   - **N/A**: Requires proof of irrelevance (e.g., "SQLi check on NoSQL DB").
   - **FAIL**: Requires proof of missing control or bypass.
3. **Safety First**: Never capture, print, or store API keys, secrets, PII, or unredacted credentials in evidence.
4. **Strict Reporting**:
   - Use `./references/REPORT-TEMPLATE.md` exactly. Do not alter structure.
   - Build report in memory. Write to disk once at the very end.
5. **Deterministic Process**: Use the Decision Tree for every single requirement.

## Exclusions

Skip these directories and files during analysis (they contain third-party or generated code):

- `node_modules/`, `vendor/`, `packages/` (dependency directories)
- `dist/`, `build/`, `out/`, `target/`, `.next/` (build outputs)
- `.git/`, `.svn/`, `.hg/` (version control)
- `*.min.js`, `*.bundle.js` (minified/bundled files)
- `coverage/`, `.nyc_output/` (test coverage)
- `__pycache__/`, `*.pyc`, `.pytest_cache/` (Python cache)
- Test files: `*.test.*`, `*.spec.*`, `*_test.*`, `test_*.*`, `__tests__/`, `tests/`, `spec/` (test code)

**Lock files** (`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `Gemfile.lock`, `poetry.lock`): Exclude from general searches. Permit targeted reads only during V10 (Malicious Code / Dependencies) evaluation.

- **🔒 Sensitive files** (do not read): `.env`, `.env.*`, `secrets.json`, `credentials.json`, `*.pem`, `*.key`, `*.pub`, AWS credentials files

---

## How to Evaluate Requirements

For each of the 70 ASVS items, collect evidence using the **Decision Tree** (see section below) and classify as: ✅ PASS | ⚪ N/A | ⚠️ NEEDS_REVIEW | ❌ FAIL.

**Evidence must be concrete and specific**:

Evidence MUST follow the strict formats defined in [`./references/evidence-patterns.md`](./references/evidence-patterns.md). Do not use free-form text for evidence.

---

## 🌳 Decision Tree (Applies to EVERY requirement)

**Step 1: Applicability & Relevance**
_Source: `package.json`, file extensions, tech stack._

1.  **Irrelevant to Tech Stack?** (e.g., Java reqs in Node.js)
    - **YES** → 🛑 **STOP**. Mark **⚪ N/A** (Evidence: "Tech stack is X, not Y").
    - **NO** → Continue.
2.  **Feature Missing?** (Zero results for feature search like "upload", "sql")
    - **YES** → 🛑 **STOP**. Mark **⚪ N/A** (Evidence: "Feature X not utilized").
    - **NO** → Continue.

**Step 2: Framework Defaults**
_Source: [`./references/framework-defaults.md`](./references/framework-defaults.md)_

1.  **Covered by Framework?** (Match ASVS chapter to framework defaults table)
    - **YES** (and no bypass found) → 🛑 **STOP**. Mark **✅ PASS** (Evidence: `framework:<name>:<feature>`).
    - **NO** (or bypass found) → Continue.

**Step 3: Verify Implementation**
_Source: Source code, config files._

1.  **Control Exists?** (Centralized middleware or distributed checks)
    - **YES** → 🛑 **STOP**. Mark **✅ PASS** (Evidence: `file:line`).
    - **UNCLEAR** → 🛑 **STOP**. Mark **⚠️ NEEDS_REVIEW**.
2.  **Control Missing?**
    - **YES** → Proceed to Step 4 (FAIL).

**Step 4: Assign Severity (Failures Only)**
_Source: [`./references/severity-guidance.md`](./references/severity-guidance.md)_

1.  **Determine Impact**: Use ASVS Chapter baseline (e.g., Auth = High).
2.  **Mark**: ❌ **FAIL** (Evidence: `missing:<feature>` or location of bypass).

## ⚙️ Execution Flow

### Phase 1: Setup & Context

1.  **Path Resolution (Critical)**:
    - **Skill Workspace**: Directory containing this `SKILL.md` and `./assets/`. Use this path ONLY to load the CSV and references.
    - **Target Repo**: The user's application codebase. Use this path for ALL code analysis, file searching, and git commands.
2.  **Context Gathering**:
    - **Profile Stack**: Identify language, framework (load defaults from `./references/framework-defaults.md`), and database.
    - **Git Metadata**: Run `git rev-parse --short HEAD` in the **Target Repo**.
    - **Structure**: Detect monorepo structure. Prefix evidence with `[component]` if multiple exist.
3.  **Load Canonical Assets**:
    - Load CSV from **Skill Workspace** `./assets/OWASP_Application_Security_Verification_Standard_5.0.0_L1_en.csv`. - Use columns and row order (1-70) for the audit.
    - Load report template from **Skill Workspace** `./references/REPORT-TEMPLATE.md`. DO NOT deviate from template while generating the report.

### Phase 2: Dual Subagent Evaluation

To maximize thoroughness, you MUST delegate the actual evaluation to two separate subagents, running sequentially or in parallel if supported. Each subagent audits the codebase independently using a **different model** — this is mandatory to obtain genuinely diverse findings.

1. **Agent 1 — Claude Sonnet 4.6**:
   - Invoke with `model: "Claude Sonnet 4.6 (Copilot)"` (exact string for the `runSubagent` `model` parameter).
   - Provide it with the context gathered in Phase 1 and the full ASVS CSV content.
   - Instruct it to evaluate all 70 items in order using the Decision Tree and return every finding with evidence.
2. **Agent 2 — GPT-5.4**:
   - Invoke with `model: "GPT-5.4 (Copilot)"` (exact string for the `runSubagent` `model` parameter).
   - Provide it with the same context and ASVS CSV content.
   - Instruct it to independently evaluate all 70 items in order using the Decision Tree and return every finding with evidence.

> **Model diversity is the goal.** If a requested model is unavailable, choose the next most capable model that differs from the other agent's model — never use the same model for both agents.

### Phase 3: Evaluation, Analysis, & Merging

1.  **Analyze and Merge**: Once both subagents return their findings, compare their results for each of the 70 items.
    - If they agree, use the consolidated finding.
    - If they disagree (e.g., one finds a PASS, the other a FAIL), review the evidence provided by both. You are the final arbiter. Choose the most accurate, evidence-based conclusion.
    - Combine unique vulnerabilities from both into the final list.
2.  **Parse Report**: Use `./references/REPORT-TEMPLATE.md` as the mandatory skeleton.
    - **Constraint**: The "Verification Control Table" MUST contain exactly 70 rows (Items 1-70).
    - **Findings**: Include detailed evidence/remediation for FAIL items only, incorporating the best evidence from both subagents.
    - **Sanitization**: Ensure NO secrets/PII are present.
3.  **Write to Disk**:
    - Determine the output path: `{target_repo}/docs/{project_name}-ASVS-L1-audit-{YYYY-MM-DD}.md`.
    - Check whether the `docs/` directory exists in the Target Repo. If it does not, create it before writing.
    - Write the report in one operation.
4.  **Completion**: Output coverage statistics and confirm the full file path.

---

## Error Handling

| Scenario                        | Action                                                                                                      |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| CSV file missing/corrupted      | STOP audit, report error: "ASVS CSV not found at expected path"                                             |
| Target codebase empty           | STOP audit, report: "No source files found in target repository"                                            |
| Target codebase inaccessible    | STOP audit, report: "Cannot access target path: [path]"                                                     |
| Git commands fail               | Set Git Commit to `unknown`, continue audit                                                                 |
| Tool fails mid-audit            | Mark as **⚠️ NEEDS_REVIEW** with note: "Verification failed due to tooling error — manual review required". |
| Token/context limit approaching | Complete current chapter, save partial report with `[PARTIAL]` prefix, note last completed item             |
| File too large to read          | Sample first 500 lines + last 100 lines, note in Evidence: "Large file - sampled"                           |

---

## Examples

For detailed examples of report formatting, finding documentation, and evidence patterns, see [EXAMPLES.md](./EXAMPLES.md).
