---
name: lead-qualifier
description: Source and qualify local-business leads for a done-for-you tech-services business (websites, automation, database work) targeting non-technical owners in the NYC tri-state area. Use this skill whenever the user wants to find leads, build a prospect list, scrape local businesses (e.g. from Google Maps), score or rank prospects, decide who to reach out to, or set up the top of their sales funnel — even if they don't say the word "lead." Trigger on phrasings like "find me businesses that need a website," "who should I cold email," "build a prospect list for plumbers in NJ," "qualify these leads," or "score this scraped CSV."
---

# Lead Qualifier

This skill turns a raw list of local businesses into a **ranked, tiered list of qualified prospects** ready for demo-and-outreach. It is built for one specific business model, and every decision in it serves that model — understand the model first and the rules will make sense.

## The business model this serves

The user sells **done-for-you tech work** (websites first, then workflow automation, database management, etc.) to **non-technical local business owners** in the **NYC tri-state area (NY, NJ, CT)**. The outreach motion is: build a **demo website** for a prospect, **cold-email the demo**, and **call after 2 days** if they don't reply.

That model dictates what a "good lead" is. A good lead is a business where **all three** of these are true at once:

1. **Need** — there's a visible tech gap (no website, a bad website, or manual operations) so a demo will land hard.
2. **Ability to pay** — proof of steady customers and cash flow (reviews, longevity, price level), so they can actually buy.
3. **Reachability** — at least one working channel (email and/or phone), so the demo-email-then-call play can run.

Miss any one and it's not a lead. That's why scoring **multiplies** the three dimensions rather than adding them — a zero anywhere zeroes the whole prospect.

## Workflow

Follow these steps in order. Steps 1–2 produce raw data; step 3 is the core qualification; step 4 hands off to outreach.

### Step 1 — Define the batch (niche × geography)

Pick one niche and a set of tri-state towns/ZIPs to target. Don't boil the ocean — one niche at a time keeps the demo and the pitch sharp. If the user hasn't named a niche, recommend from `references/target-niches-tristate.md` (ranked by how low-tech-yet-moneyed each category tends to be). Build search queries in the pattern `<niche> in <town/state>`, e.g. "plumber in Hoboken NJ", "dentist in White Plains NY", "auto repair in Stamford CT".

### Step 2 — Source the raw list

Pull businesses from **Google Maps**, the richest public source for local businesses — it exposes exactly the fields we score on (website-or-not, URL, category, review count, rating, phone, price level, address).

- Preferred at this budget: a **pay-per-use Maps scraper** (Outscraper or an Apify Google Maps scraper) with the **email/social extraction add-on**. Avoid the official Google Places API — it's far pricier per record, caps results, and returns no email.
- If the user already has a scraped CSV/export, skip straight to step 3.
- For enrichment (emails, owner names) when the scraper misses them, use Hunter.io (free tier) or Apollo. See `references/sourcing-tools.md` for current tools, pricing, and the cold-email deliverability setup.

The export should be a CSV. Normalize columns to whatever the scraper gives; the scoring script auto-detects common column names (name, site/website, phone, reviews, rating, category, etc.).

### Step 3 — Score and tier (the core of the skill)

Run the scoring script on the CSV. It computes a composite score from Need × Ability-to-pay × Reachability and outputs a ranked, tiered CSV plus a short summary.

```bash
python3 scripts/score_leads.py <input.csv> -o <scored_output.csv>
```

The script is column-tolerant (it sniffs for common header names from Outscraper/Apify/Apollo exports). If a column it wants is missing, it scores conservatively and notes the assumption — read its printed summary. Before trusting the ranking on an unfamiliar export, **open the output and spot-check the top 5 and bottom 5 by hand** — automated signals are directional, not gospel, and a quick human glance catches mislabeled categories or dead businesses.

The full point values and the logic behind each are in `references/qualification-rubric.md`. Read that file when you need to explain a score, tune the weights for a different niche, or add a new signal. Do **not** restate the rubric from memory — read it, because the numbers are tuned and change over time.

Tiers the script assigns:

- **Tier A (hot)** — high need + can pay + **email found** → build a demo website and email it first.
- **Tier B (warm)** — high need + can pay but **no email** → phone-first track using the Google number.
- **Tier C (nurture)** — fits but weak on one dimension → revisit in a later batch.
- **Disqualified** — already has a modern site, no reachable contact, or looks defunct/too small.

### Step 4 — Hand off to outreach

Output a clean CSV the user can work from, with the tier, the composite score, the specific need signal that triggered (e.g. "no website", "not mobile-friendly", "© 2016 footer"), and the best contact channel. Tier A rows go to the website-demo + cold-email track; Tier B rows go to the call-first track. Suggest tracking each lead's status (sourced → qualified → demo built → emailed → called → replied → booked) so nothing slips; if the user has Notion or a sheet connected, offer to set that tracker up.

## Output format

Always deliver:

1. **A scored CSV** (one row per business) sorted by composite score descending, with columns: `business_name, category, tier, composite_score, need_signal, ability_signal, contact_channel, email, phone, website, address`.
2. **A short written summary** stating how many businesses were scored, the Tier A/B/C/disqualified counts, and the top few names with a one-line reason each. Keep it tight — the user wants the list, not an essay.

## Guardrails

- **Respect the all-three rule.** Resist the temptation to surface a flashy "terrible website" lead that has no reviews and no contact — it wastes the user's outreach time. The multiply-not-add scoring exists to enforce this; don't override it without saying why.
- **Don't fabricate contact data.** If no email was found, mark it missing and route to the phone track. Never guess an email address that wasn't actually discovered.
- **Verify before asserting a site is "bad."** When the website-quality signal matters for tiering, actually load the site (fetch it / open it in the browser) rather than assuming from the URL — a site can look outdated in a directory but be fine, or vice versa.
- **Stay within the budget.** Prefer pay-per-use scraping and free enrichment tiers; flag before recommending anything that pushes past ~$100/mo.
- **Scraping etiquette.** Only collect public business-listing data, at reasonable volume. This is standard B2B prospecting; keep it that way.

## Reference files

- `references/target-niches-tristate.md` — ranked tri-state niches with why each is a good fit and example search queries.
- `references/qualification-rubric.md` — exact scoring values for Need, Ability-to-pay, Reachability, and the tier cutoffs.
- `references/sourcing-tools.md` — current sourcing/enrichment/sending tools, pricing, and cold-email deliverability setup.
- `scripts/score_leads.py` — the scoring engine.
