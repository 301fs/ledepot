---
name: campaign-researcher
description: Research a market and produce a ready-to-run lead-gen campaign profile (niches, locations, offer, need signals, scoring) plus a reusable research playbook. Use this skill whenever the user wants to start a new campaign, target a new niche or area, or isn't sure how to fill in a profile — e.g. "research a campaign for dentists in Westchester," "should I target restaurants or salons?", "build me a profile for HVAC companies in NJ," or "figure out who to go after." It self-determines what it needs to learn, researches it (web + a hands-on Google Maps scan), and writes a profile the lead-pipeline can run. For running the resulting campaign, see lead-pipeline; for scraping/scoring, see lead-scraper and lead-qualifier.
---

# Campaign Researcher

This skill is the **front of the funnel**: it turns a rough idea ("I want to target nail salons in the tri-state with websites") into a **fully-evidenced campaign profile** the rest of the pipeline can run, and a **research playbook** that gets sharper every time you revisit the campaign.

Two jobs, and they matter equally:

1. **Research what's needed to define the profile.** Every field in a profile is a claim about the world (these are the right niches; these towns can pay; this is what "need" looks like here). This skill goes and checks those claims instead of guessing.
2. **Learn how to research *this specific* campaign.** Different campaigns need different evidence. The skill works out the right research questions for the campaign in front of it, then records that approach — questions, sources, calibration examples, recommended settings — in a per-campaign **playbook** it refines on later runs. That's the "learning": research compounds instead of restarting.

## The business model (context)

Done-for-you tech work (websites first, then automation, database) sold to **non-technical local business owners** in the **NYC tri-state area (NY/NJ/CT)**. Outreach motion: demo → email → call after 2 days. A good lead has **need × ability to pay × reachability** all present (see `lead-qualifier`).

## Workflow

Think of it as: form a plan → research → synthesize → validate → persist. Reason throughout about what *this* campaign actually requires — don't run a fixed checklist.

### 1. Scope the campaign
Get (or infer, then confirm) the **offer** and the **rough market**. If the user is unsure of the niche or offer, that's fine — comparing a couple of candidates is itself a research output. Resolve only what you must to start; the research will sharpen the rest.

### 2. Decide what you need to learn (the self-directed part)
Before searching, write down — briefly — what's **uncertain** about this campaign and what evidence would resolve it. Use `references/profile-research-map.md` as scaffolding (it maps each profile field to a research question and where to look), but tailor it: a website campaign for salons leans on "do they even have a site / are they Instagram-only?"; an automation campaign for clinics leans on "what do they do manually?". The questions you choose *are* the campaign-specific research method you're learning.

### 3. Research
Work the questions, cheapest-first, and **use the strongest research engine available** rather than raw web search when you can:

- **Hands-on local-business scan (do this — it's the highest-value step).** Look at 15–25 real listings for the niche in a couple of target towns: site present? quality? online booking? socials? review counts? findable email? This grounds the need signals and ability benchmarks in reality. The fastest way to gather this is the installed plugins: **`nimble:local-places`** / **`nimble:market-finder`** return real local businesses with reviews/social/scoring, and **`brightdata-plugin:scrape`/`search`** pull live page data. Fall back to a manual Google Maps look only if neither is available.
- **Market/competition research** → prefer **`brightdata-plugin:live-research`** or **`brightdata-plugin:competitive-intel`** (multi-source, cited) and **`nimble:company-deep-dive`/`competitor-intel`** for niche tech-adoption, typical budgets/spend, town income/density, competitor agencies, and seasonality. Use plain `WebSearch` / `web_fetch` only when no research plugin is installed.
- **Deep multi-source digs** → the **deep-research** or **`brightdata-plugin:live-research`** skill, folded back into the playbook.

Capture findings *with sources* as you go — you'll cite them in the playbook.

### 4. Synthesize the profile
Translate findings into a profile by copying `../lead-pipeline/profiles/_template.yaml` and filling it from evidence:
- `niches`, `locations` (ranked by density + ability to pay), `offer`, `pitch` (in the owner's language).
- `need_points` ranked by how strongly each signal predicts a winnable deal *here*, grounded in your calibration examples.
- `ability.review_buckets` / price settings tuned to the niche's normal range, so the bar isn't accidentally too high or low.
- `tiers` / `weights` adjusted for the niche's reachability (e.g. email-rare niches will run B-heavy — don't over-weight reach).

Note every non-default setting's reason; those reasons go in the playbook.

### 5. Validate
Run the validator before handing the profile downstream:
```bash
python3 scripts/validate_profile.py ../lead-pipeline/profiles/<campaign>.yaml
```
Fix anything it flags (missing fields, empty `need_points`, unsorted review buckets, out-of-range weights).

### 6. Persist the playbook (the learning)
Write `references/research-playbook-template.md`'s structure to `../lead-pipeline/profiles/<campaign>.research.md`, filled in. On a **re-run** of an existing campaign, read the existing playbook first and *refine* it — update findings, add to the changelog, adjust settings with reasons — rather than starting over. Over time this file becomes the campaign's institutional memory.

## Output

1. A validated **profile** at `../lead-pipeline/profiles/<campaign>.yaml`.
2. A **research playbook** at `../lead-pipeline/profiles/<campaign>.research.md` (findings + sources + the campaign-specific research method + recommended settings + changelog).
3. A **short summary** to the user: the recommended niche(s)/towns, the 2–3 most important findings, the expected tier split, and anything still uncertain. Then offer to run it via `lead-pipeline`.

## Guardrails

- **Evidence over vibes.** Don't fill a field you haven't checked. If you must assume, say so in the playbook and mark it to verify.
- **The Maps scan is not optional** for a real campaign — it's what makes the need signals true. Web search alone tends to give generic niche claims, not what *these* businesses in *these* towns actually look like.
- **Cite sources** so settings can be re-justified later, and so the next run can tell what's stale.
- **Recommend, don't overfit.** A handful of listings is directional. Prefer ranges and clearly-reasoned defaults over false precision; flag where more data would help.
- **Respect the search/fetch restrictions** in the environment; if a page can't be fetched, find another source rather than working around it.

## Reference files

- `references/profile-research-map.md` — what to research for each profile field, and where to look (the reusable scaffolding).
- `references/research-playbook-template.md` — the structure of the per-campaign learned playbook.
- `scripts/validate_profile.py` — checks a produced profile is well-formed and sane.
- Related: `lead-pipeline` (run the campaign), `lead-scraper`, `lead-qualifier`. Research engines to prefer when installed: `brightdata-plugin:live-research` / `competitive-intel`, `nimble:local-places` / `market-finder` / `company-deep-dive`, and the `deep-research` skill for heavy digs.
