# Qualification Rubric

The composite score is **Need × Ability-to-pay × Reachability**. Each dimension is scored 0–10. Multiplying enforces the rule that a lead must clear all three: a zero on any dimension zeroes the lead. Max composite is 1000; the script normalizes the display to 0–100.

Treat these numbers as a tuned starting point, not physics. They're calibrated for low-tech tri-state local businesses where the first offer is a website. If you shift niche or offer, retune (e.g. for an automation-first offer, "manual operations" should weigh heavier than "no website").

---

## Dimension A — Need (0–10)

How visible and severe is the tech gap? Bigger gap = more dramatic demo = warmer lead.

| Signal | Points |
|---|---|
| No website at all (Google listing only) | 10 |
| Social-only (Facebook/Instagram, no real website) | 9 |
| Website exists but **not mobile-friendly** | 8 |
| Website **not HTTPS** (http only / no SSL) | 8 |
| Site clearly outdated (old copyright year, broken pages, free-template look) | 7 |
| Site works but **no online booking/ordering** in a niche that needs it | 5 |
| Modern, functional site **with** booking/e-commerce | 1 |

Take the **highest** applicable signal, not the sum. Record which signal fired as the `need_signal` so the user knows the hook. If multiple low-medium signals stack (e.g. outdated AND no booking), bump up by 1.

## Dimension B — Ability to pay (0–10)

Proof of steady customers and cash flow. Built from review volume, rating, longevity, and price level.

| Component | Scoring |
|---|---|
| Review count | 0 reviews → 0; 1–9 → 3; 10–49 → 6; 50–199 → 8; 200+ → 10 |
| Rating modifier | rating ≥ 4.0 → ×1.0; 3.0–3.9 → ×0.85; < 3.0 or unrated → ×0.7 |
| Price level (if available, $–$$$$) | $$ or higher adds +1 (capped at 10); high-ticket niches inherently score well |
| Longevity / multiple locations | +1 if clearly established (cap 10) |

Compute review-count points, apply the rating multiplier, then add the modifiers. A business with **zero reviews scores near zero here** — no proven customers means no proven budget, and that's intentional. Record a short `ability_signal` like "127 reviews, 4.6★".

## Dimension C — Reachability (0–10)

Can the demo-email-then-call motion actually run?

| Signal | Points |
|---|---|
| Email found **and** phone present **and** owner name known | 10 |
| Email found and phone present | 9 |
| Email found only | 7 |
| Phone only (no email) | 6 |
| No email and no phone | 0 |

Phone is almost always present from Google, so most rows land at 6+. The presence/absence of **email** is what splits Tier A from Tier B. Record `contact_channel` = "email+phone", "phone", or "none".

---

## Tier cutoffs

After computing the composite (normalized 0–100):

- **Tier A (hot):** Need ≥ 7 **and** Ability ≥ 6 **and** email found. Build a demo, email first.
- **Tier B (warm):** Need ≥ 7 **and** Ability ≥ 6 **and** no email (phone present). Call-first track.
- **Tier C (nurture):** composite ≥ 30 but doesn't meet A or B (usually weaker on one dimension). Revisit later.
- **Disqualified:** Need ≤ 2 (already has a modern site), **or** Reachability = 0, **or** Ability = 0 (no proven customers / looks defunct).

The Tier A vs B split is deliberately about email, because that's the channel the primary play (demo email) needs. Don't let a high raw score promote a no-email lead into Tier A — route it to the phone track instead.

## Why multiply instead of add

Adding lets one huge strength hide a fatal weakness — a business with a hilariously bad website (Need 10) but zero reviews and no contact would float to the top of an additive list and waste a demo build. Multiplying makes any single near-zero drag the whole score down, which matches reality: you need the problem **and** the money **and** the way in.
