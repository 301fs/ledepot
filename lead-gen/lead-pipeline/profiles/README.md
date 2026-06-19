# Campaign Profiles — schema

A **profile** is one file that fully defines a campaign. It's the layer you edit
to pivot: change the niche, the geography, the offer, or the scoring without
touching any skill code. The scraper and the qualifier both read the same
profile, so the two stages stay in sync.

Profiles are YAML (preferred) or JSON. Save them in this folder; pass the path
to the scraper and qualifier (the `lead-pipeline` skill does this for you).

## Top-level fields

| Field | Meaning |
|---|---|
| `name` | Short id, also used to name output files. |
| `description` | One line for humans. |
| `offer` | Which **need-signal detector set** the qualifier uses. Determines what "need" means. See below. |
| `sourcing` | Everything `lead-scraper` needs (provider, niches, locations, limits). |
| `pitch` | One sentence describing what you'll build — used in outreach framing. |
| `qualification` | Everything `lead-qualifier` needs (points, thresholds, tiers, weights). |

## `offer` types and their need signals

`offer` selects which detectors run against each business. The **points** for each
signal come from `qualification.need_points` in the profile, so you tune severity
per campaign; the **detection logic** lives in the qualifier's code.

- **`website`** (fully wired): `no_website`, `social_only`, `no_https`,
  `builder_subdomain`, `site_exists_unverified`, `modern_site`.
- **`automation`** (worked example to extend): `no_online_booking`, `phone_only`,
  `social_only`, `manual_ops_site`, `modern_site`. Detecting "manual operations"
  from Maps data is weaker than detecting a missing website — treat these as hints
  and verify before tiering.
- **`database`** / others: add a detector set in the qualifier code, then list its
  signal ids under `need_points`. The structure is built to extend this way:
  **adding a new *type* of signal = a small code addition; everything else is config.**

Only the signal ids relevant to your `offer` need points; unknown ids are ignored.

## `sourcing`

| Field | Meaning |
|---|---|
| `provider` | `outscraper` or `apify`. |
| `niches` | List of search terms. Each is crossed with each location → `"<niche> in <location>"`. |
| `locations` | Towns/cities, e.g. `Stamford CT`. |
| `limit_per_query` | Max places per query. |
| `language`, `region` | Passed to the provider. |
| `enrich_emails` | Ask the provider to also return emails (small extra cost). |

## `qualification`

- `need_points` — points per signal id (see offer types).
- `ability.review_buckets` — list of `[min_reviews, points]`; the highest bucket whose
  threshold the business meets wins.
- `ability.rating_*` — rating multiplier applied to the review points.
- `ability.price_*` — a small bump for higher price levels.
- `reach.*` — points by which contact channels were found (email vs phone vs both).
- `tiers` — `disqualify_max_need`, then `A`/`B`/`C` thresholds, evaluated in order.
- `weights` — per-dimension multipliers if you want to lean a campaign toward, say,
  need over reach.

## How to pivot

- **New niche, same offer:** edit `niches` (and maybe `locations`). Done.
- **New geography:** edit `locations`.
- **New service (e.g. automation):** set `offer: automation`, adjust `need_points`
  to that offer's signal ids, tweak the `pitch`. If the offer type isn't wired yet,
  add its detector set in the qualifier (one function) first.
- **Tougher/looser qualification:** edit thresholds in `tiers`, `review_buckets`, or `weights`.
