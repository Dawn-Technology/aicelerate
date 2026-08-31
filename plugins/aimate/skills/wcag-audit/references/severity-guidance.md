# Accessibility Severity and Review Priority

WCAG level and finding severity measure different things. Show the criterion's A/AA level separately. Assign severity from demonstrated user impact, reach, task criticality, and availability of a reasonable workaround.

## Confirmed FAIL severity

| Severity | Meaning | Typical examples |
|---|---|---|
| **Critical** | Blocks one or more disability groups from completing a core task, with no reasonable workaround | Keyboard trap in checkout; inaccessible authentication path; essential live content without captions |
| **Serious** | Substantially impairs access to important information or functionality | Informative image missing alt; unlabeled required input; insufficient text contrast; custom control unavailable to keyboard users |
| **Moderate** | Causes meaningful friction or confusion but a reasonable workaround exists | Vague heading or label; inconsistent navigation; error suggestion omitted where the error is otherwise identified |
| **Minor** | Limited, localized impact that does not materially block task completion | Overly verbose alternative text; minor heading-structure issue in non-core content |

## NEEDS_REVIEW priority

Use the same labels as review priority, not as confirmed defect severity:

- **Critical priority:** unresolved behavior could block a core task or create a trap.
- **Serious priority:** unresolved behavior affects common navigation, input, perception, or authentication.
- **Moderate priority:** unresolved behavior is localized or has a likely workaround.
- **Minor priority:** low-reach uncertainty with limited likely impact.

## Baselines and adjustments

These are starting points, not automatic severities:

| Criterion or pattern | Baseline |
|---|---|
| 2.1.2 keyboard trap in a core flow | Critical |
| 3.3.8 inaccessible sole authentication method | Critical |
| 1.1.1 missing alternative for informative content | Serious |
| 1.2.2 missing captions for meaningful prerecorded media | Serious |
| 1.4.3 insufficient text contrast | Serious |
| 2.1.1 custom control not keyboard operable | Serious |
| 2.4.7 focus indicator suppressed | Serious |
| 3.3.2 required input lacks a label | Serious |
| 2.4.6 vague heading or label with recoverable context | Moderate |
| 3.2.4 inconsistent identification with a clear workaround | Moderate |

Increase severity for core tasks, broad reuse in a shared component, no workaround, safety/financial consequences, or multiple affected disability groups. Decrease only with evidence of low reach and a reasonable accessible workaround. Document the reason for any material adjustment.

