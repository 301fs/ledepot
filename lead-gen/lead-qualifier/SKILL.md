---
name: lead-qualifier
description: Score and qualify a list of local businesses into ranked, tiered prospects for a done-for-you tech-services business (websites, automation, database work) targeting non-technical owners in the NYC tri-state area. Use this skill whenever the user has a list/CSV of businesses (e.g. scraped from Google Maps by lead-scraper) and wants to rank them, decide who to approach, filter to the good ones, or "qualify these leads." Driven by a campaign profile so the niche, offer, and scoring can change without code edits. Trigger on phrasings like "qualify these leads," "score this scraped CSV," "who's worth reaching out to," or "rank these salons." For the full source→qualify→outreach flow, see the lead-pipeline skill; for getting the raw list, see lead-scraper.
---

# Lead Qualifier

This skill turns a raw list of local businesses into a **ranked, tiered list of qualified prospects**. It is the middle stage of the funnel: `lead-scraper` produces the raw CSV, this skill scores it, and outreach acts on the tiers. It reads the **same campaign profile** the scraper used, so qualification always matches what was targeted.

## The business model this serves

The user sells **done-for-you tech work** (websites first, then workflow automation, database management, etc.) to **non-technical local business owners** in the **NYC tri-state area (NY, NJ, CT)**. The outreach motion is: build a **demo** for a prospect, **cold-email it**, and **call after 2 days** if they don't reply.

That model dictates what a "good lead" is. A good lead is a business where **all three** are true at once:

1. **Need** — there's a visible gap that *this campaign's offer* fixes (for a website offer: no/bad website; for an automation offer: manual operations). The profile's `offer` decides what "need" means.
2. **Ability to pay** — proof of steady customers and cash flow (reviews, rating, price level).
3. **Reachability** — at least one working channel (email and/or phone) so the demo-email-then-call play can run.

Miss any one and it's not a lead. Scoring **multiplies** the three dimensions rather than adding them, so a zero anywhere zeroes the prospect — that's deliberate (see the rubric for why).

## Profile-driven by design

Everything tunable lives in a **campaign profile** (`../lead-pipeline/profiles/*.yaml`), not in this skill's code:

- `offer` selects which **need detectors** run (the detection logic per offer is in `scripts/score_leads.py`; the points are in the profile).
- `need_points`, `ability`, `reach`, `tiers`, and `weights` tune the scoring.

This is what lets the user pivot — new niche, new geography, or new offer — by editing one file. **Adding a brand-new *type* of need signal** (e.g. a `database` offer) means adding one detector function in `scripts/score_leads.py` and listing its signal ids in the profile; everything else is config. See `../lead-pipeline/profiles/README.md` for the schema.

## Workflow

1. **Get the profile and the raw CSV.** The profile is the campaign file; the CSV is `lead-scraper`'s output (or any export — the scorer sniffs common Outscraper/Apify/Apollo column names).
2. **Run the scorer:**
   ```bash
   python3 scripts/score_leads.py raw_leads.csv --profile ../lead-pipeline/profiles/<campaign>.yaml -o scored.csv
   ```
   (Profiles are YAML — needs PyYAML: `pip install pyyaml --break-system-packages`. JSON profiles work with no dependency.)
3. **Read the printed summary** — it reports the profile/offer, the A/B/C/disqualified counts, and the top prospects. If the scorer warns it couldn't map a column or scored something conservatively, note it.
4. **Spot-check the top 5 and bottom 5 by hand** before trusting the ranking on an unfamiliar export. Automated signals are directional. In particular, when a need signal is "site exists — load it to confirm," actually open the site rather than assuming from the URL.
5. **Hand off** the scored CSV: Tier A → demo + email track; Tier B → phone-first track.

## Tiers the scorer assigns

- **Tier A (hot)** — high need + can pay + **email found** → build a demo and email first.
- **Tier B (warm)** — high need + can pay but **no email** → phone-first track using the Google number.
- **Tier C (nurture)** — fits but weak on one dimension → revisit later.
- **Disqualified** — low need (already served), no reachable contact, or no proven customers.

The A/B split is deliberately about **email**, because the primary play (demo email) needs it. Don't promote a no-email lead into A on raw score alone — route it to the phone track.

## Output format

Always deliver:

1. **A scored CSV** sorted by tier then composite score, columns: `business_name, category, tier, composite_score, need_signal, ability_signal, contact_channel, email, phone, website, address` (plus the per-dimension scores).
2. **A short written summary**: how many scored, the tier counts, and the top few names with a one-line reason each. Keep it tight — the user wants the list, not an essay.

## Guardrails

- **Respect the all-three rule.** Don't surface a flashy "terrible website" lead that has no reviews and no contact — the multiply-not-add scoring exists to prevent exactly that; don't override it without saying why.
- **Don't fabricate contact data.** If no email was found, mark it missing and route to the phone track. Never invent an email.
- **Verify "bad site" claims** by loading the site when that signal drives tiering.
- **Keep parameters in the profile.** If you find yourself wanting to change a threshold or a niche, edit the profile, not the code. Only touch the code to add a new *kind* of detector.

## Reference files

- `references/qualification-rubric.md` — the scoring dimensions and the reasoning behind the defaults (which the profile overrides).
- `references/target-niches-tristate.md` — ranked tri-state niches with example search queries.
- `scripts/score_leads.py` — the scoring engine (also holds the per-offer need detectors).
