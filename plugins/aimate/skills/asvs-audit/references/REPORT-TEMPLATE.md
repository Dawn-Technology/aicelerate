# Dawn Technology · OWASP ASVS 5.0 Level 1 · Security Audit Report

**Initial Draft author**: AI Agent ({{ model_name }})  
**Reviewed & Finalized by**: _____________________
**Report Date**: {{ report_date }}  
**Skill Version**: 2.1.0  
**ASVS Version**: 5.0.0  

## Application details

**App Version**: {{ app_version }}  
**Git Commit**: {{ git_commit_hash }}  

## Technology Stack

**Language** | {{ language }}  
**Framework** | {{ framework }}  
**Database** | {{ database }}  
**Key Libraries** | {{ key_libraries }}  

---

## Introduction

This security audit was conducted against the **OWASP Application Security Verification Standard (ASVS) Version 5.0**. The ASVS provides a basis for testing web application technical security controls and also provides developers with a list of requirements for secure development.

Level 1 is the minimum level that all applications should strive for. It consists of items that are testable via automated means or manual review.

For more information, please visit the [OWASP ASVS Project Page](https://owasp.org/www-project-application-security-verification-standard/).

## 🔒 Confidentiality Statement

> **STRICTLY CONFIDENTIAL**
>
> This document contains detailed findings regarding the security posture of the target application. It may include information about vulnerabilities, architectural gaps, and potential exploitation vectors.
>
> **Access to this report is restricted to authorized stakeholders only.** Unauthorized distribution, copying, or public disclosure of this material is strictly prohibited and may compromise the security of the application.

---

## Summary

{{ executive_summary }}
<!-- Fill: executive summary — strengths + critical weaknesses -->

**Coverage Statistics**:

- Total Level 1 Items: 70
- Items Verified: {{ items_verified_count }} (Must be 70)
- **Result Breakdown**:
  - 🔴 Critical: {{ count_critical }}
  - 🟠 High: {{ count_high }}
  - 🟡 Medium: {{ count_medium }}
  - 🟢 Low: {{ count_low }}
  - ✅ PASS: {{ count_pass }}
  - ⚠️ NEEDS_REVIEW: {{ count_needs_review }}
- **Compliance Score**: {{ compliance_score }}% <!-- Calculated as PASS / (Total Items - N/A Items - NEEDS_REVIEW Items) * 100 -->
- **Completeness Check**: {{ total_reported }} / {{ total_from_csv }} (Should be 100%)
- **Review Debt**: {{ count_needs_review }} items require manual verification

## Findings

<!-- Loop: one block per FAIL finding, CSV order -->
### #{{ internal_num }} - {{ req_id }} - {{ section_name }}

- **Chapter**: {{ chapter_name }}
- **Section**: {{ section_name }}
- **ASVS ID**: {{ req_id }}
- **Internal Item #**: {{ internal_num }}
- **Requirement**: {{ req_description }}
- **Severity**: {{ severity_icon }} {{ severity_level }}
- **Location**: `{{ location }}`
- **Evidence**: `{{ evidence_details }}`
- **Description**: {{ finding_description }}
- **Remediation**:
  {{ remediation_steps }}

  ```{{ code_language }}
  {{ corrected_code_example }}
  ```

---
<!-- End loop -->

## Verification Summary

<!-- All 70 items, sorted by internal_num -->

| Item | Chapter / Section | Requirement | Status | Evidence |
|:---|:---|:---|:---|:---|
| #{{ internal_num }} {{ req_id }} | {{ chapter_name }}<br>{{ section_name }} | {{ req_description }} | {{ status_icon }} {{ status_text }} | {{ evidence_short }} |
<!-- Repeat for all 70. Status: ✅ PASS | ⚪ N/A | ⚠️ NEEDS_REVIEW | ❌ FAIL -->

---

## Conclusion

{{ conclusion_text }}
<!-- Fill: overall posture, key risks, next steps -->

**Signed:**  
Date: {{ report_date }}  
Name: __________________
Signature:  

---
