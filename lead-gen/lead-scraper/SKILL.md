---
name: lead-scraper
description: Source local businesses into a clean, normalized CSV (+ full.json) for lead generation, driven by a campaign profile. Use this skill whenever the user wants to scrape, pull, or build a raw list of businesses to prospect — e.g. "scrape nail salons in NJ," "pull restaurants in Westchester," "get me a list of HVAC companies in Connecticut," or "source leads for the salon campaign." It uses the best available web-data engine — Nimble or Bright Data when installed, otherwise the built-in Outscraper/Apify script — and outputs files that lead-qualifier scores and site-brief builds from. For the full source→qualify→outreach flow see lead-pipeline.
---

# Lead Scraper

This skill is the **first stage** of the lead funnel: it sources local businesses and writes a normalized CSV (plus a `full.json` of rich content) that `lead-qualifier` scores and `site-brief` builds websites from. It does **not** decide who's a good lead — it collects the raw data the campaign profile asks for. Keeping sourcing separate means you can re-scrape without re-qualifying and swap the engine without touching the rest of the funnel.

## Engine: prefer the installed web-data plugins

The *engine* that actually fetches businesses is pluggable, and the funnel is better when it rides on a robust, maintained scraper rather than a raw API script. Use the best one available, in this order:

1. **Nimble (preferred for local-business discovery).** If the `nimble` plugin is installed and authenticated, use its purpose-built skills — they do exactly this stage's job and handle scale, geo, reviews, and social:
   - **`nimble:market-finder`** — "find all <niche> in <geography>" → a prospect list (best fit for a campaign sweep across many towns).
   - **`nimble:local-places`** — discover + enrich + score local businesses in an area, returning reviews, social presence, and a map (great for richer per-place content).
   - **`nimble:nimble-web-expert`** — fetch/scrape any specific URLs or run ad-hoc extraction for enrichment.
2. **Bright Data (strong general scraper / platform data).** If `brightdata-plugin` is installed: `brightdata-plugin:search` to discover, `brightdata-plugin:scrape` for clean page data, and `brightdata-plugin:data-feeds` for structured profiles from 40+ platforms (handles bot detection/CAPTCHAs). Good for enriching a lead's socials or pulling reviews at scale.
3. **Built-in fallback script.** If neither plugin is available, use `scripts/scrape.py` (Outscraper/Apify API). It still works and is the no-plugin path.

Whichever engine runs, **normalize its output into this skill's schema** (below) so the downstream skills never care which engine was used. That normalization is the one job this skill always owns.

## What it reads and produces

- **Input:** a campaign profile's `sourcing` section (`../lead-pipeline/profiles/*.yaml`) — niches, locations, per-query limit, and whether to enrich emails. (`provider` may now also be `nimble` or `brightdata`.)
- **Output (the contract with the rest of the funnel):**
  - `raw_leads.csv` — flat fields the qualifier scores on plus website-build fields (hours, geo, description, attributes): `name, category, website, phone, email, reviews, rating, price, booking, facebook, instagram, address, city, state, hours, latitude, longitude, plus_code, description, attributes, photo_count, place_id, query`.
  - `raw_leads.full.json` — the full per-business records (nested reviews, photos, services) that `site-brief` turns into website content.

## Workflow

1. **Pick the profile** (the campaign). Fresh start → fill one from `../lead-pipeline/profiles/_template.yaml`, especially `niches` and `locations`.

2. **Source with the best available engine.**
   - **Nimble/Bright Data path (preferred):** invoke the relevant plugin skill above for each `<niche> in <location>` the profile defines (e.g. hand `nimble:market-finder` the niche + town list). Then **normalize** the returned businesses into `raw_leads.csv` + `raw_leads.full.json` using this skill's schema. Confirm scope with the user before a large sweep.
   - **Fallback script path:** dry-run first, then run, as below.
     ```bash
     python3 scripts/scrape.py --profile ../lead-pipeline/profiles/<campaign>.yaml --dry-run   # preview, no spend
     export OUTSCRAPER_API_KEY=...        # or APIFY_API_TOKEN=...
     python3 scripts/scrape.py --profile ../lead-pipeline/profiles/<campaign>.yaml -o raw_leads.csv
     ```

3. **Hand off to the qualifier** with the same profile:
   ```bash
   python3 ../lead-qualifier/scripts/score_leads.py raw_leads.csv \
       --profile ../lead-pipeline/profiles/<campaign>.yaml -o scored.csv
   ```

## Cost control

- The bill scales with **niches × locations × limit_per_query**. The dry-run prints the worst-case place count — sanity-check it against your budget before running. A few hundred places is cents to low dollars; tens of thousands adds up.
- Start with a **small batch** (a couple of towns) to confirm the data and your scoring before sweeping the whole tri-state.
- `enrich_emails` adds a small per-record cost but is what fills the email column that splits Tier A from Tier B — usually worth it.

## Guardrails

- **Dry-run before every real run**, especially after editing a profile — it's the cheapest way to catch a fat-fingered location list or an oversized limit.
- **Only collect public business-listing data** at reasonable volume. This is standard B2B prospecting; keep it that way.
- **Don't hand-edit the normalized schema** in a way that breaks the qualifier's column expectations — if you add a field, add it to `NORMALIZED_FIELDS` and the qualifier's column sniffing together.
- **Keep targeting in the profile**, not in the script. Changing who you scrape should mean editing the profile.

## Reference files

- `references/sourcing-tools.md` — engines (Nimble, Bright Data, Outscraper/Apify), pricing, the budget stack, enrichment, and cold-email deliverability setup.
- `scripts/scrape.py` — the fallback scraper (Outscraper + Apify, with `--dry-run`) used when the Nimble/Bright Data plugins aren't available.
