---
name: campaign-evaluator
description: Grade how well a lead-gen campaign profile performed and feed the findings back so the profiler improves over time. Use this skill whenever the user wants to measure campaign results, check if their lead scoring actually works, see which tier is converting, compare campaigns, or "how good is my targeting." It joins the qualifier's scored leads with logged outreach outcomes, measures whether higher tiers really convert better (calibration), scores the profiler 0-100, tracks the trend across runs, and recommends concrete profile fixes. Trigger on phrasings like "how did the salon campaign do," "is my lead scoring any good," "which tier converts best," "score this campaign's results," or "did targeting improve." Pairs with campaign-researcher (which it feeds) and lead-qualifier (whose output it grades).
---

# Campaign Evaluator

This skill closes the loop. `campaign-researcher` makes a profile, `lead-scraper`
and `lead-qualifier` run it, outreach happens — and then this skill **grades the
profile against what actually happened**, so the next profile is better. Without
it, the profiler never learns whether its tiers mean anything.

The one question it answers: **does the scoring actually rank leads correctly?**
A profile that sorts businesses into Tier A/B/C is only valuable if A really does
convert better than B better than C. This skill measures that (calibration),
turns it into a single tracked score, and tells you what to change.

## What it needs

- **scored.csv** — the qualifier's output (a `tier` per lead).
- **outcomes.csv** — what happened to each lead, which the user logs as they do
  outreach. Use `scripts/outcomes_template.csv` as the starting point; the columns
  are `contacted, channel_used, replied, demo_built, booked_call, won, deal_value`.
  Joined to scored.csv on business name.

If outcomes haven't been logged yet, the skill still reports **sourcing yield**
(did the scrape pull relevant businesses?) and tells the user to start logging —
calibration genuinely can't be known without real results.

## Workflow

1. **Make sure outcomes are being logged.** If the user has no outcomes file, give
   them `scripts/outcomes_template.csv` and explain the columns — this is the
   feedback data the whole loop depends on. Even a few weeks of logged replies and
   booked calls is enough to start.

2. **Run the scorecard:**
   ```bash
   python3 scripts/score_campaign.py scored.csv \
       --outcomes outcomes.csv \
       --campaign <name> \
       --metric booked \
       --history scorecard-history.csv
   ```
   `--metric` picks the success measure (`booked` is the default and usually the
   right one; `replied` is an earlier signal, `won` a later one). `--history`
   appends the run so the trend accumulates.

3. **Read the scorecard with the user.** Walk through the per-tier table and the
   profiler score (0-100 = discrimination + Tier A precision + sourcing yield; see
   `references/metrics.md` for the formula). The headline is whether tiers are
   **monotonic** (A ≥ B ≥ C). An inversion is the loudest signal something's wrong.

4. **Act on the recommendations — this is where the profiler improves.** The script
   prints specific fixes tied to profile fields (e.g. "tiers aren't monotonic →
   revisit need_points ranking"; "low sourcing yield → fix niches/locations"). Map
   each to the campaign's profile and, importantly, **write the finding into the
   campaign's research playbook changelog** (`<campaign>.research.md` in
   `campaign-researcher`). That's the mechanism by which the next research run
   produces a better-calibrated profile instead of repeating the mistake.

5. **Track the trend.** `--show-history` prints the profiler score across runs and
   the delta per campaign. A rising score with steady or growing outcome volume
   means the profiler is genuinely getting better; a drop flags a regression to
   investigate.

## How this makes the profiler better over time

```
researcher → profile → scrape → qualify → OUTREACH (log outcomes)
     ▲                                              │
     └──────────  evaluator grades & recommends  ◀──┘
```

Each cycle, the evaluator converts real outcomes into specific, field-level
corrections that flow back into the researcher's playbook. Over several campaigns
the playbooks accumulate hard-won calibration ("for salons, emails are rare so
expect B-heavy; the builder-subdomain signal predicted the best deals"), and new
profiles start from that evidence rather than from defaults.

## Guardrails

- **Don't over-steer on small samples.** The script flags low-volume verdicts as
  low-confidence; with a dozen contacted leads, treat the score as a hint, not a
  mandate. Gather more before re-tuning.
- **Separate a profiling problem from an outreach problem.** Tier A can underperform
  because the leads were wrong (fix the profile) *or* because the email was weak
  (fix outreach). Look at the actual leads before blaming the scoring.
- **Be honest about confounds.** Channel, timing, and pitch all move outcomes. The
  score is a compass for where to look, not a final verdict.
- **Keep the loop closed.** A scorecard nobody acts on is wasted. Always end by
  recording the takeaway in the campaign's playbook so it changes the next run.

## Reference files

- `references/metrics.md` — every metric defined, the profiler-score formula, the symptom→fix table, and the honest caveats.
- `scripts/score_campaign.py` — the scorecard engine (run, history, trend).
- `scripts/outcomes_template.csv` — the outcomes ledger to copy and fill.
- Related: `campaign-researcher` (receives the feedback), `lead-qualifier` (produces what's graded), `lead-pipeline` (the run this evaluates).
