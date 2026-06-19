# Sourcing, Enrichment & Sending Tools

Budget target: **under $100/mo total.** Pricing below was accurate as of mid-2026 — re-check current pricing before committing, since these tools change plans often.

## Sourcing — get the raw business list

**Use a pay-per-use Google Maps scraper. Do NOT use the official Google Places API for prospecting.**

- **Outscraper** or an **Apify Google Maps scraper** — roughly **$1.50–$3 per ~500 businesses**, with an email/social-extraction add-on for a bit more. Bypasses the per-query result cap and returns the website field and (often) an email. At a few hundred leads/week this stays well under budget.
- **Why not the official Places API:** ~$32–40 per 1,000 records, caps results per query (~120), and returns **no email or social data** — Google tiers that data out. Far more expensive and missing the field you most need.

Typical export columns to expect (names vary by tool): `name`, `site`/`website`, `phone`, `full_address`, `city`, `state`, `category`/`type`, `reviews`/`review_count`, `rating`, `price_level`, `email`, `facebook`, `instagram`. The scoring script sniffs for these.

## Enrichment — find emails & owner names the scraper missed

- **Hunter.io** — free tier ~50 lookups/mo; paid starts ~$49/mo (2,000 credits) and bundles a verifier and a basic sender. Best for domain-based lookups when a prospect has a website.
- **Apollo.io** — large B2B database (275M+ contacts); free plan exists (limited credits/exports, ~250 sends/day fair-use), paid from ~$49–59/mo. Better for finding the owner's name and B2B/professional-services contacts; weaker for tiny local shops.
- For **no-website** prospects there's usually no email to find — use the **Google phone number** and route to the phone-first track.

## Sending — cold email with deliverability built in

- **Instantly** — paid from ~$47/mo; includes unlimited sending mailboxes and an automated warmup network on every plan. Good single-tool choice for our volume.
- **Smartlead** — similar, oriented toward agencies/multiple clients.
- Both handle domain warmup automatically by spreading volume across warmed mailboxes.

## Deliverability setup (don't skip — this is what makes cold email work)

1. **Send from a separate domain**, not your primary business domain, so a spam complaint can't poison your main email. (e.g. buy a `.co`/`.net` lookalike for outreach.)
2. **Authenticate it:** SPF, DKIM, and DMARC records are mandatory in 2026 — without them you go straight to spam.
3. **Warm up 2–4 weeks** before real sends, via the sending tool's warmup network.
4. **Ramp volume:** start 5–10 emails/day and increase gradually over 4–6 weeks. Sudden spikes trigger spam filters.
5. **Copy:** keep it under ~80 words, conversational, **one link only** (the demo). Multiple links raise spam scores. Personalize the first line with the owner's name or business specifics.

## A budget stack that fits under $100/mo

| Purpose | Tool | Approx cost |
|---|---|---|
| Source businesses | Outscraper / Apify Maps scraper (pay-per-use, w/ email add-on) | ~$20–40/mo at our volume |
| Enrich emails/owners | Hunter.io free tier (+ occasional Apollo free credits) | $0 |
| Send + warmup | Instantly | ~$47/mo |
| **Total** | | **~$67–87/mo** |

Leaves a little headroom. If volume grows, the scraper line scales first (it's per-use), so watch that one.

---
*Sources for pricing/benchmarks (mid-2026): Outscraper & Apify Google Maps scraper listings; Hunter.io and Apollo.io pricing pages; Instantly/Smartlead cold-email guides and the Instantly 2026 Cold Email Benchmark. Re-verify before purchasing.*
