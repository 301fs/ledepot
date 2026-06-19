#!/usr/bin/env python3
"""
score_campaign.py — grade how well a campaign profile (the profiler's output)
performed, so the profiler can improve over time.

It joins the qualifier's scored.csv (predictions: a tier per lead) with an
outcomes.csv (what actually happened) and measures CALIBRATION: do higher tiers
convert better? It prints a scorecard, a single profiler score (0-100), concrete
improvement recommendations, and appends the run to a history file so you can see
the profiler get better (or worse) across runs.

Usage:
    python3 score_campaign.py scored.csv \
        --outcomes outcomes.csv \
        --campaign salons-tristate-website \
        --metric booked \
        --history scorecard-history.csv

    # structural-only (no outcomes logged yet):
    python3 score_campaign.py scored.csv --campaign salons-tristate-website

    # see the trend across past runs:
    python3 score_campaign.py --history scorecard-history.csv --show-history

See ../references/metrics.md for the definitions and the formula.
"""

import argparse
import csv
import os
import re
import sys
from datetime import datetime

TIERS = ["A", "B", "C"]
METRIC_COL = {"booked": "booked_call", "replied": "replied", "won": "won"}

# tunable thresholds (documented in metrics.md)
SPREAD_FULL = 0.30      # a 30pp A-vs-C spread earns full discrimination spread points
PRECISION_FULL = 0.25   # a 25% Tier-A primary rate earns full precision points
LOW_VOLUME = 15         # fewer contacted than this => low-confidence verdict


def norm(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def truthy(v):
    return str(v).strip().lower() in ("1", "true", "yes", "y")


def fnum(v):
    try:
        return float(str(v).replace(",", ""))
    except (ValueError, AttributeError):
        return 0.0


def safe_div(a, b):
    return a / b if b else None


def pct(x):
    return "  –  " if x is None else f"{100*x:5.1f}%"


# ---------------------------------------------------------------------------

def build_rows(scored, outcomes):
    """Join on normalized business_name. Returns list of merged dicts."""
    omap = {norm(o.get("business_name", "")): o for o in outcomes}
    rows = []
    for s in scored:
        name = s.get("business_name", "")
        o = omap.get(norm(name), {})
        rows.append({
            "name": name,
            "tier": (s.get("tier") or "").strip(),
            "contacted": truthy(o.get("contacted")) if o else False,
            "replied": truthy(o.get("replied")) if o else False,
            "booked_call": truthy(o.get("booked_call")) if o else False,
            "won": truthy(o.get("won")) if o else False,
            "deal_value": fnum(o.get("deal_value")) if o else 0.0,
        })
    return rows


def tier_stats(rows, metric_col):
    stats = {}
    for t in TIERS:
        tr = [r for r in rows if r["tier"] == t]
        contacted = [r for r in tr if r["contacted"]]
        stats[t] = {
            "n": len(tr),
            "contacted": len(contacted),
            "reply_rate": safe_div(sum(r["replied"] for r in contacted), len(contacted)),
            "book_rate": safe_div(sum(r["booked_call"] for r in contacted), len(contacted)),
            "win_rate": safe_div(sum(r["won"] for r in contacted), len(contacted)),
            "primary": safe_div(sum(truthy(r[metric_col]) for r in contacted), len(contacted)),
            "revenue": sum(r["deal_value"] for r in contacted),
        }
    return stats


def compute_score(rows, stats, total_scored):
    """Returns (profiler_score, components dict, recommendations list)."""
    recs = []
    disqualified = sum(1 for r in rows if r["tier"] not in TIERS)
    qualified = total_scored - disqualified
    yield_ = safe_div(qualified, total_scored) or 0.0

    a, c = stats["A"]["primary"], stats["C"]["primary"]
    total_contacted = sum(stats[t]["contacted"] for t in TIERS)

    # discrimination (0-50)
    discrimination = 0.0
    comparable = [t for t in TIERS if stats[t]["primary"] is not None]
    if a is not None and c is not None and stats["A"]["contacted"] and stats["C"]["contacted"]:
        spread = a - c
        discrimination += max(0.0, min(spread / SPREAD_FULL, 1.0)) * 40
        seq = [stats[t]["primary"] for t in TIERS if stats[t]["primary"] is not None]
        monotonic = all(x >= y - 1e-9 for x, y in zip(seq, seq[1:])) and any(x > y + 1e-9 for x, y in zip(seq, seq[1:]))
        if monotonic:
            discrimination += 10
        else:
            recs.append("Tiers are NOT monotonic (a lower tier converts >= a higher one) — "
                        "the scoring mis-ranks leads. Revisit need_points ranking and tier cutoffs; "
                        "re-do the hands-on Maps calibration in campaign-researcher.")
        if spread <= 0:
            recs.append(f"Tier A's {METRIC_LABEL} rate ({pct(a).strip()}) is not above Tier C's "
                        f"({pct(c).strip()}) — the top tier isn't selecting better leads.")
    else:
        recs.append("Not enough outcome data across tiers to judge calibration — log outcomes for "
                    "Tier A and Tier C leads to measure whether the ranking works.")

    # Tier A precision (0-25)
    precision = 0.0
    if stats["A"]["primary"] is not None and stats["A"]["contacted"]:
        precision = max(0.0, min(stats["A"]["primary"] / PRECISION_FULL, 1.0)) * 25
        if stats["A"]["primary"] < PRECISION_FULL * 0.5:
            recs.append(f"Tier A {METRIC_LABEL} rate is low ({pct(stats['A']['primary']).strip()}). "
                        f"If tiers are otherwise monotonic, tighten tiers.A cutoffs; if not, the need "
                        f"signal driving A may be wrong for this niche.")

    # sourcing yield (0-25)
    yield_pts = yield_ * 25
    if yield_ < 0.5:
        recs.append(f"Sourcing yield is low ({pct(yield_).strip()} of scraped businesses qualified) — "
                    f"many off-target/unreachable results. Revisit sourcing.niches and locations.")

    score = round(discrimination + precision + yield_pts, 1)
    components = {
        "discrimination": round(discrimination, 1),
        "tierA_precision": round(precision, 1),
        "sourcing_yield_pts": round(yield_pts, 1),
        "sourcing_yield": yield_,
        "qualified": qualified, "disqualified": disqualified,
        "total_contacted": total_contacted,
    }
    if 0 < total_contacted < LOW_VOLUME:
        recs.append(f"Only {total_contacted} leads contacted — verdicts are LOW CONFIDENCE. "
                    f"Gather more outcomes before re-tuning the profile.")
    return score, components, recs


# ---------------------------------------------------------------------------

def show_history(path):
    if not os.path.exists(path):
        sys.exit(f"No history file at {path}.")
    rows = read_csv(path)
    print(f"Scorecard history ({len(rows)} runs)\n")
    print(f"  {'date':<12}{'campaign':<28}{'leads':>6}{'contacted':>10}{'primary':>9}{'score':>7}")
    for r in rows:
        print(f"  {r['date']:<12}{r['campaign'][:27]:<28}{r['n_leads']:>6}{r['contacted']:>10}"
              f"{r['primary_metric']:>9}{r['profiler_score']:>7}")
    by_campaign = {}
    for r in rows:
        by_campaign.setdefault(r["campaign"], []).append(r)
    print()
    for camp, rs in by_campaign.items():
        if len(rs) >= 2:
            d = float(rs[-1]["profiler_score"]) - float(rs[0]["profiler_score"])
            arrow = "↑" if d > 0 else ("↓" if d < 0 else "→")
            print(f"  {camp}: {rs[0]['profiler_score']} → {rs[-1]['profiler_score']} {arrow} ({d:+.1f} over {len(rs)} runs)")


def main():
    ap = argparse.ArgumentParser(description="Grade a campaign profile's performance.")
    ap.add_argument("scored", nargs="?", help="qualifier scored.csv")
    ap.add_argument("--outcomes", help="outcomes.csv (what happened per lead)")
    ap.add_argument("--campaign", default="(unnamed)", help="campaign name (for history)")
    ap.add_argument("--metric", choices=list(METRIC_COL), default="booked", help="primary success metric")
    ap.add_argument("--history", help="history CSV to append/read")
    ap.add_argument("--show-history", action="store_true", help="print the trend and exit")
    args = ap.parse_args()

    global METRIC_LABEL
    METRIC_LABEL = args.metric

    if args.show_history:
        return show_history(args.history or "scorecard-history.csv")
    if not args.scored:
        sys.exit("Provide scored.csv (or use --show-history).")

    metric_col = METRIC_COL[args.metric]
    scored = read_csv(args.scored)
    if not scored:
        sys.exit("scored.csv is empty.")
    outcomes = read_csv(args.outcomes) if args.outcomes else []
    rows = build_rows(scored, outcomes)
    stats = tier_stats(rows, metric_col)
    score, comp, recs = compute_score(rows, stats, len(scored))

    # ---- report ----
    print(f"Campaign: {args.campaign}   |   primary metric: {args.metric}   |   "
          f"{len(scored)} leads scored, {comp['total_contacted']} contacted")
    if not outcomes:
        print("(no outcomes file — structural metrics only; calibration needs logged results)\n")
    else:
        print()
    print(f"  {'tier':<6}{'leads':>6}{'contacted':>10}{'reply':>8}{'book':>8}{'win':>8}{'revenue':>10}")
    for t in TIERS:
        s = stats[t]
        print(f"  {t:<6}{s['n']:>6}{s['contacted']:>10}{pct(s['reply_rate']):>8}"
              f"{pct(s['book_rate']):>8}{pct(s['win_rate']):>8}{s['revenue']:>10,.0f}")
    dq = comp["disqualified"]
    print(f"  {'(DQ)':<6}{dq:>6}")

    print(f"\n  Sourcing yield: {pct(comp['sourcing_yield']).strip()} "
          f"({comp['qualified']}/{len(scored)} not disqualified)")
    print(f"\n  PROFILER SCORE: {score} / 100")
    print(f"    discrimination {comp['discrimination']}/50  +  "
          f"tierA precision {comp['tierA_precision']}/25  +  "
          f"sourcing yield {comp['sourcing_yield_pts']}/25")

    print("\n  Recommendations:")
    if recs:
        for r in recs:
            print(f"   - {r}")
    else:
        print("   - Well-calibrated: tiers are monotonic with good spread and yield. "
              "Keep the current profile; widen the batch.")

    # ---- history ----
    if args.history:
        head = ["date", "campaign", "n_leads", "contacted", "primary_metric",
                "A_rate", "B_rate", "C_rate", "sourcing_yield", "profiler_score"]
        newfile = not os.path.exists(args.history)
        with open(args.history, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if newfile:
                w.writerow(head)
            w.writerow([
                datetime.now().strftime("%Y-%m-%d"), args.campaign, len(scored),
                comp["total_contacted"], args.metric,
                "" if stats["A"]["primary"] is None else f"{stats['A']['primary']:.3f}",
                "" if stats["B"]["primary"] is None else f"{stats['B']['primary']:.3f}",
                "" if stats["C"]["primary"] is None else f"{stats['C']['primary']:.3f}",
                f"{comp['sourcing_yield']:.3f}", score,
            ])
        print(f"\n  Logged to {args.history}. Run with --show-history to see the trend.")
    print("\n  Next: write the key findings into the campaign's playbook changelog "
          "(campaign-researcher) so the next profile is better-calibrated.")


if __name__ == "__main__":
    METRIC_LABEL = "booked"
    main()
