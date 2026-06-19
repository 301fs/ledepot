# Profiler Performance Metrics

A campaign profile (produced by `campaign-researcher`) is a set of *predictions*:
these niches/towns are worth scraping, and this scoring correctly ranks who to
approach. This skill grades those predictions against what actually happened, so
the profiler can be tuned and improve over time.

The central question is **calibration**: do higher tiers actually convert better?
A profiler that sorts leads into A/B/C is only useful if A really does beat B
beats C. If they convert the same, the scoring is noise — no matter how
sophisticated it looks.

Everything below is computed by `scripts/score_campaign.py` and is deliberately
transparent so you can argue with it.

---

## Inputs

- **scored.csv** — the qualifier's output: one row per lead with at least `business_name` and `tier`.
- **outcomes.csv** — what happened to each lead (you log this as outreach runs). See `scripts/outcomes_template.csv`. Joined to scored.csv on normalized business name.

With only scored.csv (no outcomes yet), the skill reports **structural** metrics
(sourcing yield) and tells you calibration needs logged results. Calibration
needs real outcomes — there's no shortcut.

## The metrics

### Sourcing yield (structural, 0–1)
`(A + B + C) / total_scored` — the share of scraped businesses that weren't
disqualified. Low yield means the scrape pulled a lot of off-target or
unreachable businesses → the niche terms or locations in the profile are likely
wrong. This is the one quality signal available before any outreach.

### Per-tier outcome rates
For each tier, among **contacted** leads: `reply_rate`, `book_rate`, `win_rate`
(= the count with that outcome / number contacted). Rates, not raw counts, so
tiers of different sizes compare fairly. The **primary metric** defaults to
`book_rate` (a booked call is the real goal of outreach) but can be set to
`replied` or `won`.

### Tier discrimination (0–50) — the core of the score
Does the primary rate fall monotonically A ≥ B ≥ C, and by how much?
- **Spread** = rate(A) − rate(C), normalized: a 30-point spread (0.30) scores full marks.
- **Monotonicity bonus**: +10 if A ≥ B ≥ C with at least one strict step.
A big, monotonic spread means the profiler genuinely ranks leads. An inversion
(e.g. B converts better than A) is the loudest signal something's miscalibrated.

### Tier A precision (0–25)
The primary rate of Tier A directly. Tier A is where you spend demo-building
effort first, so it should convert. 25% book rate scores full marks (tunable).

### Profiler score (0–100)
`discrimination (0–50) + tierA_precision (0–25) + sourcing_yield×25`.
A single, transparent number to track run over run. It rewards a profiler that
(a) ranks leads correctly, (b) makes a top tier that actually pays off, and
(c) sources relevant businesses. It is a heuristic, not gospel — read it
alongside the per-tier table.

### Research-prediction accuracy (optional, reported separately)
If the campaign's playbook predicted things (expected tier split, expected email
rate), pass them with `--predictions` and the skill reports predicted vs. actual.
This grades the *research*, not just the scoring — e.g. "playbook expected
B-heavy; actual was A-heavy" tells the researcher its reachability read was off.

## Reading the result → improving the profiler

The script prints recommendations derived from the numbers. How to act on each:

| Symptom | Likely cause | Fix in the profile / researcher |
|---|---|---|
| Tier inversion (B or C beats A) | need signals or weights mis-ranked | revisit `need_points` ranking and `tiers.A` cutoffs; re-do the Maps calibration scan |
| A precision low, but monotonic | A cutoff too loose | raise `tiers.A.min_need`/`min_ability` |
| Low sourcing yield | wrong niche terms / towns | fix `sourcing.niches` / `locations` |
| Email rate ≪ predicted | reachability read wrong | lower reach weight; expect B-heavy; update playbook |
| Score flat across runs | research not learning | check the playbook is actually being refined each run |

These map directly to fields the `campaign-researcher` controls, which is how the
loop closes: evaluate → write findings into the campaign's playbook changelog →
next research run produces a better-calibrated profile.

## History & trend

Each run appends a row to a history CSV (`--history`). Comparing the profiler
score across runs/campaigns is how you see the profiler **get better over time** —
and catch regressions. A rising score with stable or growing outcome volume is
the goal.

## Honest caveats

- **Small samples lie.** Ten contacted leads can't tell you A beats C reliably. The script flags low-volume verdicts as low-confidence; don't over-steer on them.
- **Outreach quality is a confound.** A bad email can sink Tier A regardless of the profile. When diagnosing, separate "wrong leads" (a profiler problem) from "right leads, bad pitch" (an outreach problem).
- **The score is a compass, not a verdict.** Use it to spot what to investigate, then look at the actual leads.
