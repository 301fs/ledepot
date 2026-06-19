# Research Playbook — salons-tristate-website

**Offer:** website
**Market hypothesis:** Nail & hair salons in the NYC tri-state are appointment- and
image-driven but under-invested in their own web presence — many are Instagram-only
or rely on a booking-platform page (Booksy/Vagaro/Fresha) rather than a branded site.
Established ones have steady clientele and can afford a $1.5–4k build.
**Last updated:** 2026-06-19 · **Run #:** 1

---

## 1. Research questions for this campaign
- [x] How common is "no real website" among salons? ✅ ~30–40% of hair salons have no website.
- [x] What do salons use instead? ✅ Instagram heavily (78% of clients check social before booking) + booking platforms (Booksy 13M+ users, Vagaro, Fresha).
- [x] Can they pay? ✅ Realistic local-service site budget $1,500–8,000 (freelance); established salons clear this.
- [x] Which tri-state towns balance density and ability to pay? ✅ Commuter belt for volume; Ridgewood/Scarsdale/Greenwich tier for income.
- [ ] Actual email-find rate for salons on Maps? ⚠️ Unknown until first scrape — salons skew phone/IG, so expect a **B-heavy** split.
- [ ] Are affluent-town salons already modern (and thus DQ'd)? ❓ Verify in scrape; may trim those towns.

## 2. Findings by profile field
| Field | Finding | Source |
|---|---|---|
| offer fit | Strong: 30–40% no website; social/booking-page reliance widespread | KOR Digital; Booksy |
| niches | "nail salon" + "hair salon" cover it; consider adding "blow dry bar", "barber" | — |
| locations | Commuter belt (Hoboken, JC, White Plains, New Rochelle, Yonkers, Stamford, Norwalk) + affluent (Ridgewood NJ, Scarsdale NY, Greenwich CT) | BestNeighborhood; GOBankingRates |
| need signals | social-only and booking-platform-only are the money signals for salons | Booksy IG guide |
| ability | Steady-clientele salons can spend $1.5–4k; affluent-town owners more | Lounge Lizard; Northwest |
| pitch | "Own branded site vs. just an IG/Booksy link" resonates | — |

## 3. Need-signal calibration (key section)
**The salon-specific insight:** a salon's "website" field on Google Maps is often a
**Booksy / Vagaro / Fresha** booking page, *not* their own site. Treat those as
"no real website" (high need) — the owner has a booking tool but no branded web
presence to send clients to. → Added those domains to the qualifier's
`BUILDER_HOSTS` so they fire the `builder_subdomain` signal (points 7).

**Clear qualifiers (high need):** Instagram-only salons; salons whose only link is a
Booksy/Vagaro page; salons with an old http:// template site.
**Clear non-qualifiers (low need):** salons with a modern branded site that already
has integrated booking and looks good on mobile.

**Signal ranking for salons:** `no_website` (10) ≈ `social_only` (9) > `no_https` (8)
> `builder_subdomain` incl. booking pages (7) > `site_exists_unverified` (5).

## 4. Ability-to-pay benchmarks
- Typical healthy-salon review counts (to confirm in scrape): expect ~30–250 for established shops.
- Realistic budget for the offer: **$1,500–4,000** (freelance tier) — source: small-business website cost guides 2025.
- → `review_buckets` left at defaults (0/1/10/50/200 → 0/3/6/8/10); revisit after first scrape shows the real distribution.

## 5. Query phrasings to use
- Works (expected): `nail salon in <town>`, `hair salon in <town>`.
- Consider adding: `blow dry bar in <town>`, `hair stylist in <town>` (catches solo operators).
- Avoid: generic `beauty` (drifts to supply stores, cosmetics counters, med spas).

## 6. Reachability & channel notes
- Salons skew **phone + Instagram**; email is often absent on Maps → **expect a B-heavy (call-first) split**. Don't over-weight reach in scoring.
- Decision-maker: owner/operator (often the lead stylist). Personal, on-site.
- Best channel: the demo-email play still works where email exists; otherwise lead with a call referencing their Instagram.

## 7. Recommended scoring adjustments (vs. template defaults)
| Setting | Default | This campaign | Why |
|---|---|---|---|
| BUILDER_HOSTS (code) | wix/weebly/etc. | + Booksy/Vagaro/Fresha/Square/GlossGenius/StyleSeat/Schedulicity/Setmore | salon "sites" are often booking pages |
| locations | generic tri-state | commuter belt + 3 affluent towns | balance volume and ability to pay |
| pitch | generic | "own site vs. IG/Booksy link" | salon-specific pain |
| weights.reach | 1.0 | keep 1.0 for now, but **watch** — may lower if email is very rare | salons are phone/IG-first |

## 8. Competition & timing
- Many web agencies target salons (it's a popular niche) — differentiate with a *built demo* of their actual salon, not a generic pitch.
- Timing: salons are busiest Thu–Sat; reach owners Tue–Wed mornings.

## 9. Open questions / refine next run
- Measure real email-find rate after first scrape → decide whether to lower reach weight.
- Check whether affluent-town salons are mostly DQ'd (already modern); if so, trim those towns.
- Test adding "blow dry bar" / "hair stylist" niches for solo operators.

## 10. Changelog
- **Run 2 (2026-06-19) — live Maps scrape (7 salons, Hoboken nail + Yonkers hair):**
  - **Confirmed the booking-page signal live:** Gotham Nails' "website" is a Zoca page (gothamnailshoboken.zoca.com); Hair Dimension West uses Phorest. Added `zoca.com` + `phorest.com` to the qualifier's BUILDER_HOSTS.
  - **Email confirmed rare:** 0 of 7 salons exposed an email on Maps → 0 Tier A, 3 Tier B. The B-heavy (call-first) prediction held exactly.
  - **Saturation insight:** sourcing yield only 42.9% — 4/7 already have their own site (esp. affluent Hoboken: 3/4 nail salons had own domains). Yonkers smaller hair salons (Frances's, Sanela's) had NO website → the real Tier B leads.
  - **Action for next run:** weight locations toward less-saturated/less-affluent areas and smaller independent salons; the affluent towns (Hoboken, Ridgewood, Scarsdale, Greenwich) likely yield more DQs. Re-verify the 4 "site exists" DQs by loading the sites — if outdated, they re-enter as leads.
- **Run 1 (2026-06-19):** Initial live research. Established offer fit (~30–40% no site), booking-platform-page insight (added to BUILDER_HOSTS), affluent+commuter town mix, $1.5–4k budget, B-heavy split expectation. Sources: KOR Digital, Booksy, BestNeighborhood.org, GOBankingRates, Lounge Lizard, Northwest Registered Agent.
