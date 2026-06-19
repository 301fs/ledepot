# Profile → Research Map

This is the reusable knowledge of **what a campaign profile needs to know, and how
to learn it.** For each field in a profile, it gives the question to answer, what a
good answer looks like, and where to look. Use it as scaffolding — not a rigid
checklist. The whole point is to reason about what *this* campaign actually needs:
a website campaign for salons and an automation campaign for law offices need very
different evidence, even though they fill the same profile shape.

For each item below: **Question → what good looks like → where to look.**

---

## `offer` — is there a real tech gap this niche has?

- **Question:** Does this niche, in this area, actually have the problem the offer fixes? (For a website offer: do many of them lack a decent site? For automation: do they run manual booking/intake?)
- **Good answer:** Concrete evidence that the gap is common — e.g. "scanning 20 nail salons on Maps, ~60% had no website or Instagram-only." A weak/absent gap means pick a different offer or niche.
- **Where:** Spot-scan Google Maps results for the niche; industry articles on the niche's tech adoption; the niche's subreddit/forums complaining about a tool or its absence.

## `sourcing.niches` — the right category terms

- **Question:** How is this business categorized on Google Maps, and what adjacent terms surface the same owners? ("nail salon" vs "manicure" vs "nail technician"; "hair salon" vs "barber" vs "blow dry bar".)
- **Good answer:** A short list of 2–5 search terms that together cover the niche without drifting into a different buyer.
- **Where:** Type candidate terms into Google Maps and see what comes back; Google's "People also search for"; the niche's trade association naming.

## `sourcing.locations` — where to sweep

- **Question:** Which tri-state towns have (a) enough of this niche, (b) owners who can pay, and (c) aren't already saturated by competitors selling the same thing?
- **Good answer:** A ranked list of towns/cities with a one-line reason each (density + income). Higher-income areas (e.g. Fairfield County CT, Westchester NY) raise ability-to-pay.
- **Where:** Census/median-income lookups by town; Maps density scan; chamber-of-commerce directories for counts.

## `sourcing.limit_per_query`, `language`, `region`

- Mostly defaults (50, en, US). Raise the limit only if a niche is dense in a town and you want full coverage; remember cost scales with it.

## `need_points` / which need signals matter

- **Question:** For *this* niche and offer, what does "need" actually look like, and how common is each signal? (Do they lean on Instagram? Is online booking standard or rare? Do sites tend to be old templates?)
- **Good answer:** The signal ids ranked by how strongly they indicate a winnable deal here, plus calibration examples — 2–3 real businesses that clearly qualify and 1–2 that clearly don't, so the points are grounded.
- **Where:** Manually inspect 15–25 real listings for the niche; note site presence/quality, booking links, socials. This hands-on scan is the single most valuable research step — it's how the abstract rubric gets tuned to reality.

## `ability` — review and price benchmarks for the niche

- **Question:** What's a *normal* review count and price level for a healthy business in this niche/area, and what can they realistically spend?
- **Good answer:** Rough distributions ("most established salons here have 50–250 reviews; budget for a site is ~$1.5–4k"), used to set sensible `review_buckets` and price expectations so the bar isn't accidentally too high or low.
- **Where:** Maps review-count scan across the niche; industry reports on typical marketing spend for the niche; competitor agency pricing pages.

## `tiers` / `weights` — calibrate the bar to the niche

- **Question:** Given how reachable and moneyed this niche is, where should the cutoffs sit, and should any dimension lean heavier?
- **Good answer:** Evidence-based tweaks — e.g. "emails are rare for salons (most are phone/IG only), so expect a B-heavy split; don't over-weight reach." Or "law offices almost all have email and money, so Need should dominate."
- **Where:** Falls out of the need/ability scans above plus reachability observations (what share had a findable email).

## `pitch` — the pain point that lands

- **Question:** What specific outcome does this niche care about that the offer delivers? (Salons: "clients book without calling." Restaurants: "own ordering, skip the delivery-app fees.")
- **Good answer:** One concrete sentence in the owner's language, not generic "modern website."
- **Where:** The niche's own complaints (forums, reviews of their tools), competitor messaging that targets them.

---

## Cross-cutting research worth doing once per campaign

- **Decision-maker:** Is it the owner, a manager, a franchise HQ? Changes who you contact and how.
- **Competition:** Are other agencies already blanketing this niche? If so, sharpen the angle or shift niche.
- **Seasonality / timing:** Some niches buy at predictable times (e.g. tax prep before spring, landscaping before summer).
- **Channel fit:** Does this niche read email, answer the phone, or live on Instagram? Confirms the demo-email-then-call motion fits, or suggests a tweak.

When a question needs deep, multi-source digging rather than a quick scan, hand it to the **deep-research** skill and fold its findings back into the playbook.
