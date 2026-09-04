# [[project_name]] · WCAG 2.2 Level AA · Static Source Audit — [PARTIAL]

**Primary audit:** AI Agent ([[primary_model]])

**Evidence review:** AI Agent ([[reviewer_model]])

**Report date:** [[report_date]]

**Skill version:** 3.1.0

**WCAG version:** 2.2

**Git commit:** [[git_commit_hash]]

**Primary audit coverage:** [[COMPLETE_or_INCOMPLETE]] — [[primary_coverage_detail]]

**Evidence review coverage:** [[COMPLETE_or_INCOMPLETE]] — [[review_coverage_detail]]

## Why this report is partial

[[partial_reason_and_exact_remaining_scope]]

## Scope and evidence boundary

**Target:** [[target_path]]

**Included scope:** [[included_scope]]

**Excluded scope:** [[excluded_scope]]

**Technology stack:** [[technology_stack]]

**Source limitations:** [[source_limitations]]

> This is an interim static source-review artifact, not a completed WCAG audit, certification, or conformance claim. `⏳ NOT_EVALUATED` rows have no WCAG verdict. Completed NEEDS_REVIEW rows were evaluated but require the stated runtime, content, browser, or assistive-technology verification.

## Progress summary

| Progress | Count |
|---|---:|
| COMPLETE | [[count_complete]] |
| CONFIRMED_FAIL | [[count_confirmed_fail]] |
| INCOMPLETE | [[count_incomplete]] |
| **Total** | **55** |

| Completed-row verdict | Count |
|---|---:|
| ✅ PASS | [[count_pass]] |
| ⚪ N/A | [[count_na]] |
| ⚠️ NEEDS_REVIEW | [[count_needs_review]] |
| ❌ FAIL | [[count_fail]] |
| **Completed total** | **[[count_complete]]** |

Confirmed partial FAILs: **[[count_confirmed_fail]]**. These rows prove the aggregate FAIL verdict but do not claim a complete violation inventory.

## Progress ledger

<!-- Exactly 55 rows in canonical CSV order. -->

| SC | Name | Level | Progress | Verdict | Evidence or remaining work |
|---|---|:---:|---|---|---|
| [[sc_id]] | [[name]] | [[level]] | [[COMPLETE_CONFIRMED_FAIL_or_INCOMPLETE]] | [[verdict_or_NOT_EVALUATED]] | [[evidence_or_remaining_work]] |

## Confirmed findings

<!-- Repeat for COMPLETE FAIL and every CONFIRMED_FAIL row, in canonical order. -->

### [[verdict]] [[sc_id]] — [[name]]

- **WCAG level:** [[level]]
- **Severity / review priority:** [[Critical_Serious_Moderate_or_Minor]]
- **Affected or unresolved instances:** [[instance_count]]
- **Coverage:** [[bounded_coverage]]
- **Applicability and exceptions:** [[applicability_and_exceptions_resolved_or_unresolved]]
- **Representative evidence:**
  [[representative_evidence]]
- **Impact or uncertainty:** [[impact_or_uncertainty]]
- **Remediation or exact manual verification:**
  [[remediation_or_manual_check]]

## Manual verification plan

<!-- One row for each COMPLETE NEEDS_REVIEW criterion, in canonical order. -->

| SC | Priority | Unresolved boundary | Required verification |
|---|---|---|---|
| [[sc_id]] | [[Critical_Serious_Moderate_or_Minor]] | [[unresolved_boundary]] | [[exact_manual_verification]] |

## Recommended continuation

[[remaining_work_in_priority_order]]

## Conclusion

[[partial_conclusion]]
