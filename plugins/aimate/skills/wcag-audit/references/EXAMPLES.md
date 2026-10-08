# Evaluator Output Examples

Illustrative only — never copy conclusions without the source premise. One object per SC in `verdicts`.

```json
{
  "meta": {"model": "<evaluator model id>"},
  "verdicts": [
    {"sc_id": "1.1.1", "verdict": "FAIL", "severity": "Serious",
     "evidence": "templates/card.twig:12 <img src=\"{{ teaser }}\"> has no alt; image is the only content of a linked teaser",
     "instances": ["templates/card.twig:12 <img> missing alt", "src/Hero.jsx:30 <img> missing alt"],
     "total": "2",
     "remediation": "Add alt describing the linked destination; use alt=\"\" only for decorative images."},
    {"sc_id": "1.2.2", "verdict": "N/A",
     "evidence": "N/A - inventory features.video.count=0, caption_track=0; no player library in package.json"},
    {"sc_id": "1.4.3", "verdict": "NEEDS_REVIEW", "priority": "Serious",
     "evidence": "styles/tokens.scss:14 --brand-500 used as button background; contrast depends on rendered colours",
     "verify": "Measure text contrast of .btn-primary (default/hover/disabled) in a browser; ≥4.5:1 normal text, ≥3:1 large."},
    {"sc_id": "3.1.1", "verdict": "PASS",
     "evidence": "public/index.html:2 <html lang=\"en\">; single document shell (inventory: 1 file with <html)"}
  ]
}
```

## Rendered FAIL finding (produced by `report.py build`)

```markdown
### 1.1.1 Non-text Content (Level A) — ❌ FAIL — Serious

- **Evidence:** templates/card.twig:12 <img src="{{ teaser }}"> has no alt; image is the only content of a linked teaser
- **Representative instances (2 shown, total 2):**
  - `templates/card.twig:12 <img> missing alt`
  - `src/Hero.jsx:30 <img> missing alt`
- **Remediation:** Add alt describing the linked destination; use alt="" only for decorative images.
```
