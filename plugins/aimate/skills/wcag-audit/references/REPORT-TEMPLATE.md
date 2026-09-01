# [[project_name]] · WCAG 2.2 Level AA · Static Source Audit

**Initial draft author:** AI Agent ([[model_name]])

**Independent review:** [[independent_review]]

**Report date:** [[report_date]]

**Skill version:** 1.6.0

**WCAG version:** 2.2

**Git commit:** [[git_commit_hash]]

## Scope and evidence boundary

**Target:** [[target_path]]

**Included scope:** [[included_scope]]

**Excluded scope:** [[excluded_scope]]

**Technology stack:** [[technology_stack]]

**Source limitations:** [[source_limitations]]

> This report is a static source-code audit against the 55 WCAG 2.2 Level A and AA success criteria. It is an audit finding, not a certification or WCAG conformance claim. Source review cannot establish rendered behavior, full-page and complete-process coverage, accessibility-supported behavior, or compatibility with assistive technologies. All NEEDS_REVIEW items require the stated browser, keyboard, content, and/or assistive-technology testing before any conformance claim is considered.

## Summary

[[executive_summary]]

| Verdict | Count |
|---|---:|
| ✅ PASS | [[count_pass]] |
| ⚪ N/A | [[count_na]] |
| ⚠️ NEEDS_REVIEW | [[count_needs_review]] |
| ❌ FAIL | [[count_fail]] |
| **Total** | **55** |

### Confirmed FAIL severity

| Severity | Count |
|---|---:|
| Critical | [[count_critical]] |
| Serious | [[count_serious]] |
| Moderate | [[count_moderate]] |
| Minor | [[count_minor]] |

Checklist completion is reported as verdict counts, not as a compliance percentage.

## Conformance criteria ledger

<!-- Exactly 55 body rows in canonical CSV order. -->

| SC | Name | Level | Verdict | Evidence |
|---|---|:---:|---|---|
| [[sc_id]] | [[name]] | [[level]] | [[verdict]] | [[evidence_short]] |

## Detailed findings and required review

<!-- Repeat in CSV order for every FAIL and NEEDS_REVIEW criterion. -->

### [[verdict]] [[sc_id]] — [[name]]

- **WCAG level:** [[level]]
- **Severity / review priority:** [[Critical_Serious_Moderate_or_Minor]]
- **Affected or unresolved instances:** [[instance_count]]
- **Coverage:** [[coverage_manifest]]
- **Representative evidence:**
  [[representative_evidence]]
- **Impact or uncertainty:** [[impact_or_uncertainty]]
- **Remediation or exact manual verification:**
  [[remediation_or_manual_check]]

## Supplemental observations

<!-- Optional non-verdict notes, disputed external claims, and advisory improvements. Do not duplicate or override ledger verdicts here. -->

[[supplemental_observations]]

## Regulatory context

WCAG is a technical accessibility standard, not a legal-compliance certification. Related regimes reference different WCAG versions and may add requirements:

- The [US Revised Section 508 Standards](https://www.section508.gov/develop/applicability-conformance/) incorporate WCAG 2.0 Level A and AA success criteria and conformance requirements.
- [EN 301 549 v3.2.1](https://commission.europa.eu/accessibility-statement_en) maps web requirements to WCAG 2.1 Level AA and contains additional ICT accessibility requirements.
- The European Accessibility Act and disability-rights laws such as the ADA may create obligations depending on the organization, product, service, jurisdiction, and current implementing rules.

This audit does not determine whether any law, procurement standard, or contractual obligation applies, and it does not assert compliance with one.

## Recommended next verification

[[next_verification_steps]]

## Conclusion

[[conclusion]]
