---
name: site-brief
description: Turn a qualified lead and its scraped Google Maps data into a build-ready website brief (JSON + Markdown) for creating that business's demo site. Use this skill whenever the user wants to prep or build a website for a prospect, package a lead's info for a site, generate a content brief, or move a qualified lead toward a demo — e.g. "make a website brief for these salons," "what do we have to build their site," "prep the Tier A leads for site building," or "get Frances's Hair Studio ready for a demo." It reads the qualifier's scored.csv plus the scraper's full.json and writes one brief per lead with contact, location, testimonials, badges, services, hours, a suggested site plan, and an explicit list of what's still missing. This is the bridge from the lead funnel (campaign-researcher → lead-scraper → lead-qualifier) to the website build.
---

# Site Brief

This skill is the **bridge from lead to website**. The funnel's whole point is to go
scrape → qualify → *build the prospect a site*; this step packages everything the
scrape already captured about a qualified business into a brief a builder can work
from — and is honest about what's still missing.

It exists because the scrape contains far more than qualification needs. The same
pull that told us a salon has no website also captured its phone, address, hours,
rating, real review quotes, trust badges, and the owner's own description — exactly
the raw material for *their* demo site. Throwing that away after scoring would mean
re-gathering it later. The brief keeps it and shapes it.

## Inputs

- **scored.csv** — the qualifier's output (tier per lead). Determines who gets a brief.
- **<output>.full.json** — the scraper's rich record per business (hours, reviews,
  photos, badges, owner blurb). Optional but strongly recommended; without it the
  brief falls back to the flat CSV and will have more gaps.

## Workflow

1. **Pick the tiers to build for.** Default is `A,B` — the leads you'll actually
   pitch. Tier A first (you email them a demo), then B (phone-first).

2. **Run the builder:**
   ```bash
   python3 scripts/build_brief.py \
       --scored scored.csv \
       --full   raw_leads.full.json \
       --tiers  A,B \
       --offer  website \
       --out    briefs/
   ```
   It writes `briefs/<business>.json` and `briefs/<business>.md` per lead and reports
   how many were enriched from full.json vs. flat CSV only.

3. **Read each brief and act on the gaps.** Every brief ends with `gaps_to_fill` —
   the things a real site needs that Maps can't give (high-res photos, full service
   menu + prices, hours if absent, owner email, logo/brand, domain). These become the
   questions you ask the owner on the call. Don't ship a site with the gaps unfilled.

4. **Hand off to the build.** Give the `.json` to a site generator (it's structured
   for that) or the `.md` to whoever builds the page. The `site_plan` section
   suggests pages, home-page sections, a primary CTA, and a tone derived from the
   business's own badges.

## What a good brief captures

- **Identity & pitch:** name, category, a tagline, and the owner's own words (gold for hero copy).
- **Contact & map:** phone, email (if any), address, a ready Google Maps link from lat/lng.
- **Current presence:** existing site/booking link/socials — and whether the "site" is really a Booksy/Vagaro/Zoca booking page (i.e. they need a real one).
- **Social proof:** rating, review count, real testimonial quotes, and trust badges (women-owned, LGBTQ+ friendly, etc.) to feature.
- **Buildable content:** services/specialties, hours, photo URLs where available.
- **A starting site plan** and the **gaps** to close.

## Guardrails

- **Be honest about gaps.** The brief must not imply the scrape is enough to ship. Surface what's missing so the owner conversation fills it. A confident-but-empty brief is worse than an honest one.
- **Don't fabricate content.** Use only what was actually scraped. If there are no testimonials or no hours, say so — don't invent quotes, services, or prices.
- **Quote reviews verbatim and attribute them.** Testimonials are real customers' words; keep them accurate and credit the author where captured.
- **Richer scrape = richer brief.** If briefs come out thin, the fix is upstream: have `lead-scraper` pull reviews and photos (small extra cost), not padding here.
- **Tier order.** Build A before B; A leads get a demo emailed, so their briefs are used first.

## Reference files

- `references/brief-schema.md` — the full JSON structure, where each field comes from, and how to get richer content at scrape time.
- `scripts/build_brief.py` — the brief builder (scored.csv + full.json → JSON + MD per lead).
- Upstream: `lead-scraper` (captures the content), `lead-qualifier` (decides who's worth a brief). Downstream: the website build itself.
