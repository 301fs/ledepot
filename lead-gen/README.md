# Lead generation workflow

A profile-driven funnel for a done-for-you tech-services business (websites,
automation, database work) targeting non-technical local business owners in the
NYC tri-state area (NY / NJ / CT).

```
campaign-researcher → profile → lead-scraper → lead-qualifier → site-brief → website → outreach → outcomes
        ▲                            │  (raw_leads.full.json: content for the site) ▲                  │
        │                            └──────────────────────────────────────────────┘                  │
        └────────────────────────────  campaign-evaluator grades & feeds back  ◀───────────────────────┘
```

**Core idea:** *what* you target lives in a campaign **profile** (config); *how*
you scrape and score lives in the **skills** (machinery). Pivoting to a new niche,
geography, or offer is a new profile — not a code change.

## Structure

- **`campaign-researcher/`** — researches a market and writes an evidence-backed profile + a reusable research playbook (the front of the funnel; start here for a new campaign).
  - `scripts/validate_profile.py`, `references/profile-research-map.md`, `references/research-playbook-template.md`.
- **`lead-pipeline/`** — orchestrator skill + the campaign profiles.
  - `SKILL.md` — runs the end-to-end flow.
  - `profiles/` — one file per campaign (`salons-tristate-website.yaml`, `_template.yaml`) + schema `README.md`.
- **`lead-scraper/`** — sources businesses from Google Maps (Outscraper/Apify) into a normalized CSV.
  - `scripts/scrape.py` (supports `--dry-run`), `references/sourcing-tools.md`.
- **`lead-qualifier/`** — scores the CSV into ranked A/B/C tiers, driven by the profile.
  - `scripts/score_leads.py`, `references/qualification-rubric.md`, `references/target-niches-tristate.md`.
- **`site-brief/`** — turns each qualified lead + its scraped content into a build-ready website brief (JSON + Markdown): contact, testimonials, badges, site plan, and gaps to fill. The bridge from lead to demo site.
  - `scripts/build_brief.py`, `references/brief-schema.md`.
- **`campaign-evaluator/`** — grades whether the tiers actually converted (calibration), scores the profiler 0–100, tracks the trend, and feeds fixes back into the researcher's playbooks (closes the loop).
  - `scripts/score_campaign.py`, `scripts/outcomes_template.csv`, `references/metrics.md`.
- **`lead-sourcing-and-qualification-strategy.md`** — the written strategy behind it all.

## Quick start

```bash
pip install pyyaml outscraper --break-system-packages
export OUTSCRAPER_API_KEY=...

# 1. preview scope/cost (no spend)
python3 lead-scraper/scripts/scrape.py --profile lead-pipeline/profiles/salons-tristate-website.yaml --dry-run

# 2. source
python3 lead-scraper/scripts/scrape.py --profile lead-pipeline/profiles/salons-tristate-website.yaml -o raw_leads.csv

# 3. qualify
python3 lead-qualifier/scripts/score_leads.py raw_leads.csv \
    --profile lead-pipeline/profiles/salons-tristate-website.yaml -o scored.csv
```

Then work the tiers: **A** → build a demo + email first; **B** → phone-first; **C** → nurture.

## Pivoting

- New niche/area → edit `niches`/`locations` in the profile.
- New offer (e.g. automation) → set `offer:` + adjust `need_points`/`pitch`; wire a new detector in `score_leads.py` only if the offer type is brand new.
- Tougher/looser bar → edit `tiers`/`weights` in the profile.
