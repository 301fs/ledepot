---
name: lead-pipeline
description: Run the end-to-end lead generation funnel for a done-for-you tech-services business targeting non-technical local business owners in the NYC tri-state area — source businesses, qualify them into tiers, and hand off to outreach. Use this skill whenever the user wants to run a whole lead campaign, "find and qualify leads," start prospecting a niche, or asks how the scrape→qualify→outreach flow fits together. This is the orchestrator and the entry point; it drives the lead-scraper and lead-qualifier skills off a single campaign profile. Trigger on phrasings like "run the salon campaign," "find me qualified leads for hair salons in NJ," "start a new prospecting campaign," or "set up lead gen for restaurants."
---

# Lead Pipeline (orchestrator)

This is the **entry point and conductor** for the lead funnel. It doesn't do the scraping or scoring itself — it owns the **campaign profile** and runs the specialist skills in order, so the whole flow stays consistent end to end.

```
profile  →  lead-scraper  →  raw_leads.csv  →  lead-qualifier  →  scored.csv  →  outreach
```

The design principle: **what you target lives in the profile (config); how you scrape and score lives in the skills (machinery).** That's what makes pivoting cheap — a new niche, geography, or offer is a new profile, not a code change.

## The business model

The user sells **done-for-you tech work** (websites first, then automation, database management) to **non-technical local business owners** in the **NYC tri-state area (NY, NJ, CT)**. Outreach motion: build a **demo**, **cold-email it**, **call after 2 days** if no reply.

## The pieces

- **Campaign profile** (`profiles/*.yaml`) — one file fully defines a campaign: niche, geography, provider, offer, qualifiers, weights. Start from `profiles/_template.yaml`; schema in `profiles/README.md`. The current live campaign is `profiles/salons-tristate-website.yaml` (nail & hair salons, tri-state, website offer).
- **lead-scraper** skill — sources businesses from Google Maps into a normalized CSV.
- **lead-qualifier** skill — scores that CSV into ranked A/B/C tiers.
- **Outreach** — separate, triggered by tier (this is where a website-demo builder skill plugs in later).

## Workflow

1. **Choose or create the profile.** If running an existing campaign, pick its file in `profiles/`. If starting a **new** campaign — or the user isn't sure of the niche/towns/scoring — use the **campaign-researcher** skill: it researches the market and writes an evidence-backed profile (plus a research playbook) for you, rather than you hand-guessing the fields. For a quick manual start, copy `_template.yaml`, fill in at least `name`, `offer`, `sourcing.niches`, `sourcing.locations`, and validate it (`python3 ../campaign-researcher/scripts/validate_profile.py profiles/<campaign>.yaml`). Confirm the choices with the user before spending anything.

2. **Source** — invoke the **lead-scraper** skill. Always dry-run first to preview scope/cost:
   ```bash
   python3 ../lead-scraper/scripts/scrape.py --profile profiles/<campaign>.yaml --dry-run
   # then the real run, once credentials are set:
   python3 ../lead-scraper/scripts/scrape.py --profile profiles/<campaign>.yaml -o raw_leads.csv
   ```

3. **Qualify** — invoke the **lead-qualifier** skill with the *same profile*:
   ```bash
   python3 ../lead-qualifier/scripts/score_leads.py raw_leads.csv \
       --profile profiles/<campaign>.yaml -o scored.csv
   ```

4. **Review & hand off.** Read the qualifier's summary, spot-check the top and bottom of `scored.csv`, then route: **Tier A** → build a demo and email first; **Tier B** → phone-first using the Google number; **Tier C** → nurture later.

5. **Track status & log outcomes** so nothing slips *and the loop can close*: `sourced → qualified → demo built → emailed → called → replied → booked`. Record per-lead outcomes in an outcomes ledger (`../campaign-evaluator/scripts/outcomes_template.csv`) — these are what the evaluator needs. If the user has Notion or a sheet connected, offer to stand up that tracker.

6. **Evaluate & improve** (after outreach has run). Use the **campaign-evaluator** skill to grade whether the tiers actually converted and feed fixes back into the profile/playbook:
   ```bash
   python3 ../campaign-evaluator/scripts/score_campaign.py scored.csv \
       --outcomes outcomes.csv --campaign <campaign> --history scorecard-history.csv
   ```
   This is what makes the profiler improve over time rather than repeating the same targeting.

## How to pivot (the whole point of this structure)

- **Same offer, new niche/area:** edit `niches` / `locations` in the profile. Re-run scrape + qualify.
- **New offer (e.g. automation instead of websites):** set `offer: automation` in the profile, adjust `need_points` to that offer's signal ids and the `pitch`. If that offer type isn't wired in the qualifier yet, add one detector function there first (see `lead-qualifier`), then it's config from then on.
- **Tougher/looser bar:** edit `tiers`, `review_buckets`, or `weights` in the profile.

A pivot should almost never require touching scraper or qualifier code — if it does, that's a signal the profile schema should absorb the new knob.

## Guardrails

- **Confirm scope and cost before scraping** — run the dry-run and check the place-count estimate against budget.
- **One profile drives both stages.** Never scrape with one profile and score with another — the qualifier's need detectors assume the offer the scraper targeted.
- **Spot-check before outreach.** Automated tiers are directional; eyeball the top A's (and a few disqualified) before building demos or dialing.

## Related

- `profiles/README.md` — full profile schema and the available `offer` types.
- `lead-scraper` skill — sourcing stage.
- `lead-qualifier` skill — scoring stage and the per-offer need detectors.
