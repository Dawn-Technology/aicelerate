# Dawn Technology · OWASP ASVS 5.0 Level 1 · Security Audit Report

**Project**: {{ project_name }}  
**App version**: {{ app_version }}  
**Git commit**: {{ git_commit_hash }}  
<!-- With uncommitted changes: "abc1234-dirty (12 files changed since this commit)". -->
**Report date**: {{ report_date }}  
**Skill version**: {{ skill_version }}  
**ASVS version**: 5.0.0  
**Prepared by**: AI agent. Coordinator: {{ coordinator_model }}. Workers: {{ worker_models }} ({{ model_provenance }}). Mode: {{ execution_mode }}.  
**Reviewed and finalized by**: _____________________

<!-- model_provenance: "reported by host" or "as requested; host did not report the model used". -->
<!-- execution_mode: "two-model" or "one-model (only one model was available for workers; no second independent pass)". -->

## Technology stack

| Component | Path | Language | Framework | Database | Authentication | Key security libraries |
|---|---|---|---|---|---|---|
| {{ component }} | {{ component_path }} | {{ language }} | {{ framework }} | {{ database }} | {{ auth_method }} | {{ key_libraries }} |

---

## Introduction

This audit checks the application against the **OWASP Application Security Verification Standard (ASVS) 5.0**, Level 1. Level 1 is the baseline every application should meet.

It is a static review: the source code and configuration tracked in git were read, at the commit above plus any uncommitted changes noted there. {{ dependency_audit_statement }} The application was not run or tested live. Every failure in this report was checked against the code before it was included.

<!-- dependency_audit_statement: "The package manager's dependency audit was run on <date>; its results depend on the advisories known that day." or "The dependency audit could not run: <reason>." -->

For more on ASVS, see the [OWASP ASVS project page](https://owasp.org/www-project-application-security-verification-standard/).

## 🔒 Confidentiality statement

> **STRICTLY CONFIDENTIAL**
>
> This document contains detailed findings regarding the security posture of the target application. It may include information about vulnerabilities, architectural gaps, and potential exploitation vectors.
>
> **Access to this report is restricted to authorized stakeholders only.** Unauthorized distribution, copying, or public disclosure of this material is strictly prohibited and may compromise the security of the application.

---

## Summary

{{ executive_summary }}
<!-- 3–6 sentences: overall posture, the most serious risks, what to fix first. -->

**Results for the 70 Level 1 items**

- ❌ FAIL: {{ count_fail }} (🔴 Critical {{ fail_critical }} · 🟠 High {{ fail_high }} · 🟡 Medium {{ fail_medium }} · 🟢 Low {{ fail_low }})
- ✅ PASS: {{ count_pass }}
- ⚠️ NEEDS_REVIEW: {{ count_needs_review }}
- ⚪ N/A: {{ count_na }}
- Total: {{ count_total }} of 70
- **Compliance score**: {{ compliance_score }}%, up to {{ compliance_score_max }}% if every NEEDS_REVIEW item passes

<!-- compliance_score = PASS / (70 - N/A) * 100, rounded to one decimal. compliance_score_max = (PASS + NEEDS_REVIEW) / (70 - N/A) * 100. -->

**Other findings**: {{ count_other }} (🔴 {{ other_critical }} · 🟠 {{ other_high }} · 🟡 {{ other_medium }} · 🟢 {{ other_low }})

**Verification**: {{ count_candidates }} candidate failure locations checked, {{ count_rejected }} rejected as false positives.

**Dependency audit**: {{ dependency_audit_summary }}
<!-- Command(s) run and counts per severity, e.g. "npm audit --omit=dev: 0 critical, 2 high, 5 moderate, 1 low". Or why it could not run. -->

## Findings

<!-- One block per owning FAIL item, in item order. Other affected FAIL items reference the owner in their verification and evidence rows instead of duplicating its finding. Locations sorted by path, then line. -->

### #{{ item_number }} {{ req_id }} {{ section_name }}: {{ finding_title }}

- **Severity**: {{ severity_icon }} {{ severity_level }}
- **Chapter**: {{ chapter_id }} {{ chapter_name }}
- **Requirement**: {{ req_description }}
- **Description**: {{ finding_description }}
<!-- What is wrong, why it matters, and the reason for any severity change. -->
- **Locations**:

  | Location | Code | Why it fails | Severity |
  |---|---|---|---|
  | `{{ location }}` | `{{ quote }}` | {{ reason }} | {{ location_severity }} |

- **Remediation**: {{ remediation_steps }}

  ```{{ code_language }}
  {{ corrected_code_example }}
  ```
<!-- Include the code block only when a code change fixes the issue; omit it for dependency, documentation and configuration-only fixes. -->

---

## Other findings

<!-- Security issues outside the 70 items, verified the same way. Sorted by severity, then path. Write "None found." when empty. -->

### O{{ other_number }}: {{ other_title }}

- **Severity**: {{ severity_icon }} {{ severity_level }}
- **Description**: {{ other_description }}
- **Locations**:

  | Location | Code | Why it is a problem |
  |---|---|---|
  | `{{ location }}` | `{{ quote }}` | {{ reason }} |

- **Remediation**: {{ remediation_steps }}

---

## Needs review

<!-- One row per NEEDS_REVIEW item, in item order. Write "None." when empty. -->

| Item | Reason | Question to answer | Searched |
|---|---|---|---|
| #{{ item_number }} {{ req_id }} | `{{ review_reason }}` | {{ review_question }} | {{ searched_summary }} |

## Verification summary

<!-- Exactly 70 rows, in item order. Evidence column:
     PASS: `path:line` (or framework entry) and what it shows, at most 15 words.
     FAIL: "See finding #<owner>" and the number of locations.
     N/A: "N/A - <condition absent>; searched <terms>".
     NEEDS_REVIEW: the reason code. -->

| Item | Chapter / Section | Requirement | Status | Evidence |
|:---|:---|:---|:---|:---|
| #{{ item_number }} {{ req_id }} | {{ chapter_name }}<br>{{ section_name }} | {{ req_description }} | {{ status_icon }} {{ status_text }} | {{ evidence_short }} |

## Evidence appendix

<!-- One block per item, all 70, in item order, then the other-findings checklist block. Repeat the Evidence line for every evidence entry and the Searched line for every search. For FAIL items, the Evidence lines may say "See finding #n". This is what makes the report reproducible: a reviewer can re-run every search and re-read every cited line. -->

### #{{ item_number }} {{ req_id }}: {{ status_text }}

- Evidence: `{{ location }}` `{{ quote }}`: {{ reason }}
- Searched: `{{ search_command }}`: {{ hits }} hits, {{ first_party_hits }} first-party

### Other-findings checklist

- Searched: `{{ search_command }}`: {{ hits }} hits, {{ first_party_hits }} first-party

## Checked and rejected

<!-- Every candidate failure location rejected during verification, one line each: item, location, reason. Write "None." when empty. -->

- #{{ item_number }} `{{ location }}`: {{ rejection_reason }}

---

## Conclusion

{{ conclusion_text }}
<!-- Overall posture, the main risks, and the recommended order of work. -->

**Signed:**  
Date: {{ report_date }}  
Name: __________________  
Signature:
