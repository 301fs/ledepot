---
name: lead-scraper
description: Source local businesses from Google Maps into a clean, normalized CSV for lead generation, driven by a campaign profile. Use this skill whenever the user wants to scrape, pull, or build a raw list of businesses to prospect — e.g. "scrape nail salons in NJ," "pull restaurants in Westchester from Google Maps," "get me a list of HVAC companies in Connecticut," or "source leads for the salon campaign." It runs the Outscraper or Apify API based on the profile's sourcing settings and outputs a CSV that lead-qualifier scores. For the full source→qualify→outreach flow see lead-pipeline; for scoring the output see lead-qualifier.
---

# Lead Scraper

This skill is the **first stage** of the lead funnel: it sources local businesses from Google Maps and writes a normalized CSV that `lead-qualifier` can score directly. It does **not** decide who's a good lead — it just collects the raw data the campaign profile asks for. Keeping sourcing separate means you can re-scrape without re-qualifying, swap the data source later, and reason about each stage on its own.

## What it reads and produces

- **Input:** a campaign profile's `sourcing` section (`../lead-pipeline/profiles/*.yaml`) — provider, niches, locations, per-query limit, language/region, and whether to enrich emails.
- **Output:** one CSV with a fixed normalized schema (the contract with the qualifier): `name, category, website, phone, email, reviews, rating, price, booking, facebook, instagram, address, city, state, query`.

The normalizer maps both Outscraper and Apify field names into this schema, so the qualifier never has to care which provider was used.

## Why Google Maps + a pay-per-use scraper

Google Maps is the richest public source of local businesses and exposes exactly the fields qualification needs (website-or-not, URL, category, reviews, rating, phone, price). Do **not** use the official Google Places API for this — it's far pricier per record, caps results, and returns no email. Use a pay-per-use scraper (Outscraper or Apify) instead. Pricing, the recommended budget stack, and cold-email deliverability setup are in `references/sourcing-tools.md`.

## Workflow

1. **Pick the profile** (the campaign). If the user is starting fresh, help them fill one from `../lead-pipeline/profiles/_template.yaml` — especially `niches` and `locations`.

2. **Always dry-run first** to preview the queries and the scope before spending anything:
   ```bash
   python3 scripts/scrape.py --profile ../lead-pipeline/profiles/<campaign>.yaml --dry-run
   ```
   This prints every `"<niche> in <location>"` query and the max places it would fetch — no API call, no spend. Confirm the niches/locations look right before the real run.

3. **Set the provider credential** (one of):
   ```bash
   export OUTSCRAPER_API_KEY=...     # provider: outscraper  (needs: pip install outscraper)
   export APIFY_API_TOKEN=...        # provider: apify       (needs: pip install apify-client)
   ```

4. **Run the scrape:**
   ```bash
   python3 scripts/scrape.py --profile ../lead-pipeline/profiles/<campaign>.yaml -o raw_leads.csv
   ```
   It de-dupes on name+address and reports how many businesses it got and what share have an email.

5. **Hand off to the qualifier** with the same profile:
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

- `references/sourcing-tools.md` — providers, current pricing, the budget stack, enrichment, and cold-email deliverability setup.
- `scripts/scrape.py` — the scraper (Outscraper + Apify, with `--dry-run`).
