# Lead Sourcing & Qualification Strategy

**Business:** Done-for-you tech services (websites, workflow automation, database management, etc.) for non-technical business owners.
**Market:** NYC tri-state local businesses (NY, NJ, CT).
**Budget:** < $100/mo for tooling.
**Motion:** Source → qualify → build a demo website → cold email the demo → call after 2 days if no reply.

---

## 1. Who we are actually targeting (the ICP)

The ideal customer is a business that (a) **visibly needs tech help**, (b) **can clearly afford a few thousand dollars**, and (c) **is reachable**. All three must be true. A business with a terrible website but no money, or a perfect prospect with no findable contact, is not a lead.

Concretely, the best-fit prospect looks like:

- **Owner-operated local business**, roughly 1–25 employees, that the owner runs hands-on.
- **A weak or missing digital presence**: no website, a broken/outdated one, or "Facebook page only."
- **Manual operations**: booking by phone, paper intake, no online ordering, no CRM.
- **Proof they have customers and cash flow**: steady reviews, multiple years in business, mid-to-higher price point.
- **An identifiable owner and a way to reach them** (email and/or phone).

The "zero tech skill" owner is a feature, not a bug: they can't fix the problem themselves, they don't have an in-house person, and a working demo lands harder because they literally can't picture it until they see it.

### Best-fit niches in the tri-state (low-tech, real money)

Prioritize trades and service businesses where the owner is busy doing the work, not sitting at a computer. Highest-signal categories: home services (HVAC, plumbing, electricians, roofing, landscaping, pest control), auto (independent repair shops, body shops, detailers), health & wellness (dentists, chiropractors, physical therapy, med spas, optometrists), food (independent restaurants, caterers, bakeries, delis), personal care (salons, barbers, nail/spa), professional services (law offices, accountants, insurance brokers, real estate teams), and specialty retail. Full ranked list with reasoning is in `references/target-niches-tristate.md`.

---

## 2. Where leads come from (sourcing)

The core engine is **Google Maps / Google Business Profile data**, because it is the single richest public source of local businesses *and* it exposes the exact signals we qualify on: whether a website exists, the website URL (to inspect quality), category, review count, rating, phone, address, and price level.

### Primary source — Google Maps scraping (pay-per-use, cheapest at our scale)

Don't use the official Google Places API for this — it's ~$32–40 per 1,000 records, caps results per query, and returns **no email**. Instead use a pay-per-use Maps scraper:

- **Outscraper** or an **Apify** Google Maps scraper — roughly **$1.50–$3 per ~500 businesses**, plus a small add-on for email/social extraction. At a few hundred leads a week this stays well under $100/mo. These bypass the per-query cap and return the website field we need.
- Query pattern: `<niche> in <town/zip>` across a list of tri-state towns and ZIPs (e.g., "plumber in Hoboken NJ", "dentist in White Plains NY", "auto repair in Stamford CT").

### Enrichment — finding the email + owner

Google Maps usually gives the phone but not always an email. Fill the gap with:

- **Email/social extraction** from the scraper (pulls emails off the business's own website/socials when one exists).
- **Hunter.io** free tier (50 lookups/mo) or **Apollo.io** (free plan / ~$49 mo if scaled) for domain-based email lookup and to find the owner's name.
- For "no website" prospects, the contact is usually the **phone number from Google** plus the public Facebook page — these go straight to the phone-first track.

### Secondary / supplementary sources (free, lower volume)

Yelp, the local Chamber of Commerce directories, Instagram/Facebook local business listings, and town-specific business directories. Useful to cross-check and to catch businesses that are "social-only." Treat these as supplements, not the main engine.

### Suggested low-budget stack (fits < $100/mo)

A Maps scraper with email add-on (~$20–40/mo at our volume) + Hunter free tier + one cold-email sending tool with built-in warmup such as **Instantly** (~$47/mo) covers sourcing, enrichment, and deliverability. That leaves headroom for occasional Apollo credits. Detailed tool notes and current pricing are in `references/sourcing-tools.md`.

---

## 3. How we qualify (the scoring model)

Every scraped business is scored on three independent dimensions, then multiplied. Multiplying (not adding) enforces the rule that a lead must clear *all three* — a zero on any dimension kills the lead.

### Dimension A — Need (does the tech problem visibly exist?)

The bigger and more obvious the gap, the warmer the lead, because the demo will be dramatic.

- **No website at all** → highest need.
- **Social-only** (Facebook/Instagram but no real site) → very high.
- **Website exists but is bad**: not mobile-friendly, no HTTPS/SSL, broken pages, outdated (old copyright year, "© 2016"), no online booking/ordering, slow, or clearly a free template → high to medium.
- **Modern, functional site with booking/e-commerce** → low need (deprioritize or pitch a different service like automation).

### Dimension B — Ability to pay (will the money be there?)

We want businesses with proven, steady demand — they have customers, so they have budget.

- **Review volume** (a steady stream of reviews signals real customer flow).
- **Rating** (a solid rating means the business is healthy, not failing).
- **Longevity / establishment** (years in business, multiple locations).
- **Price level** (higher-ticket services = more to spend; med spas and law offices outspend a corner deli).

### Dimension C — Reachability (can we actually run the play?)

The outreach motion is demo-email-then-call, so a lead must be contactable on at least one channel.

- **Email found** → enables the demo-email track (primary).
- **Phone present** → enables the call track (we have this from Google almost always).
- **Owner name identified** → personalization, higher reply rate.

### Scoring output

`references/qualification-rubric.md` defines the exact point values, and `scripts/score_leads.py` computes the composite score from a scraped CSV and outputs a **ranked, tiered list**:

- **Tier A (hot):** high need + strong ability to pay + email found → build a demo and email first.
- **Tier B (warm):** high need + ability to pay but **no email** → phone-first track.
- **Tier C (nurture):** decent fit but weaker on one dimension → batch later.
- **Disqualified:** modern site already, or no reachable contact, or clearly defunct/too small.

---

## 4. How it connects to outreach (the full funnel)

1. **Source** a niche × town batch from Google Maps (scraper).
2. **Enrich** emails/owner names.
3. **Score & tier** with the rubric → ranked CSV.
4. **Tier A:** build a quick demo website for the business, then cold-email the demo (short, under 80 words, one link). If no reply in 2 days → **call**.
5. **Tier B:** call-first using the Google phone number, lead with the offer to "show you what your new site could look like."
6. **Track** every lead's status (sourced → qualified → demo built → emailed → called → replied → booked) so nothing falls through.

Cold email mechanics that protect deliverability at this budget: send from a **separate domain** (not your main one), warm it up for 2–4 weeks via the sending tool's network, keep volume low and ramped (5–10/day rising over weeks), keep copy short with a single link to the demo. Details in `references/sourcing-tools.md`.

---

This strategy is operationalized as a reusable skill in the `lead-qualifier/` folder so the same sourcing-and-scoring process runs the same way every time.
