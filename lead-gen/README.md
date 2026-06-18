# ledepot

Lead sourcing, qualification, and outreach assets for a done-for-you tech-services business
(websites, workflow automation, database management) targeting non-technical local business
owners in the NYC tri-state area (NY / NJ / CT).

## Contents

- **`lead-sourcing-and-qualification-strategy.md`** — where leads come from and how they're qualified.
- **`lead-qualifier/`** — a reusable skill that operationalizes the strategy:
  - `SKILL.md` — the workflow (source → enrich → score → tier → hand off to outreach).
  - `references/qualification-rubric.md` — exact Need × Ability-to-pay × Reachability scoring.
  - `references/target-niches-tristate.md` — ranked tri-state niches with example search queries.
  - `references/sourcing-tools.md` — current tools, pricing, and cold-email deliverability setup.
  - `scripts/score_leads.py` — scores a scraped CSV and outputs a ranked, tiered prospect list.

## Quick start

```bash
python3 lead-qualifier/scripts/score_leads.py your_scraped_leads.csv -o scored.csv
```

The script auto-detects common column names from Outscraper / Apify / Apollo exports.
