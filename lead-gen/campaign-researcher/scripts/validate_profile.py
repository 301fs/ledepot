#!/usr/bin/env python3
"""
validate_profile.py — check a campaign profile is well-formed and sane before it
feeds the pipeline. Catches the mistakes that would otherwise surface as a silent
mis-scrape or mis-score: missing sections, empty need_points, unsorted review
buckets, out-of-range weights, an offer with no points, etc.

Usage:
    python3 validate_profile.py path/to/profile.yaml

Exit code 0 = valid (warnings allowed), 1 = errors found.
Profiles may be YAML (needs PyYAML) or JSON.
"""

import json
import sys

KNOWN_OFFERS = {"website", "automation", "database"}  # extend as detectors are added


def load(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text)
    except ImportError:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            sys.exit("Profile is YAML but PyYAML isn't installed "
                     "(pip install pyyaml --break-system-packages), or save as JSON.")


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python3 validate_profile.py path/to/profile.yaml")
    p = load(sys.argv[1]) or {}
    errors, warnings = [], []

    # top-level
    for key in ("name", "offer", "sourcing", "qualification"):
        if key not in p:
            errors.append(f"missing top-level `{key}`")

    offer = p.get("offer")
    if offer and offer not in KNOWN_OFFERS:
        warnings.append(f"offer '{offer}' isn't in KNOWN_OFFERS {sorted(KNOWN_OFFERS)} "
                        f"— make sure lead-qualifier has a need detector for it")

    # sourcing
    s = p.get("sourcing", {}) or {}
    if not s.get("niches"):
        errors.append("sourcing.niches is empty")
    if not s.get("locations"):
        errors.append("sourcing.locations is empty")
    if s.get("provider") not in (None, "outscraper", "apify"):
        warnings.append(f"sourcing.provider '{s.get('provider')}' is unusual (expected outscraper/apify)")
    lim = s.get("limit_per_query", 50)
    if not isinstance(lim, int) or lim <= 0:
        errors.append("sourcing.limit_per_query must be a positive integer")
    elif lim > 200:
        warnings.append(f"sourcing.limit_per_query={lim} is high — cost scales with it")

    # qualification
    q = p.get("qualification", {}) or {}
    np_ = q.get("need_points", {}) or {}
    if not np_:
        errors.append("qualification.need_points is empty — nothing to score need on")
    else:
        for sid, pts in np_.items():
            if not isinstance(pts, (int, float)) or not (0 <= pts <= 10):
                errors.append(f"need_points.{sid}={pts} should be a number 0–10")

    ab = q.get("ability", {}) or {}
    buckets = ab.get("review_buckets")
    if not buckets:
        errors.append("qualification.ability.review_buckets is missing")
    else:
        mins = [b[0] for b in buckets]
        if mins != sorted(mins):
            warnings.append("review_buckets aren't sorted by min reviews — highest match wins, "
                            "so order won't break scoring, but sort them for readability")
        for b in buckets:
            if len(b) != 2 or not all(isinstance(x, (int, float)) for x in b):
                errors.append(f"review_buckets entry {b} should be [min_reviews, points]")

    for mk in ("rating_full_mult", "rating_mid_mult", "rating_low_mult"):
        v = ab.get(mk)
        if v is not None and not (0 <= v <= 1.5):
            warnings.append(f"ability.{mk}={v} is outside the usual 0–1.5 range")

    # tiers
    tiers = q.get("tiers", {}) or {}
    for t in ("A", "B"):
        td = tiers.get(t)
        if not td:
            errors.append(f"qualification.tiers.{t} is missing")
        else:
            for f in ("min_need", "min_ability"):
                if f not in td:
                    errors.append(f"tiers.{t}.{f} is missing")
    if "A" in tiers and not tiers["A"].get("requires_email"):
        warnings.append("tiers.A.requires_email is false/missing — A and B will only differ by score, "
                        "not by the email channel the demo-email play needs")

    # weights
    w = q.get("weights", {}) or {}
    for dim in ("need", "ability", "reach"):
        v = w.get(dim)
        if v is not None and (not isinstance(v, (int, float)) or v < 0):
            errors.append(f"weights.{dim}={v} should be a non-negative number")

    # report
    name = p.get("name", "(unnamed)")
    print(f"Profile: {name}  |  offer: {offer}")
    if not errors and not warnings:
        print("✅ Valid — no issues.")
    if warnings:
        print(f"\n⚠️  {len(warnings)} warning(s):")
        for w_ in warnings:
            print(f"   - {w_}")
    if errors:
        print(f"\n❌ {len(errors)} error(s):")
        for e in errors:
            print(f"   - {e}")
        print("\nFix the errors before running the pipeline.")
        sys.exit(1)
    print("\nOK to feed into lead-scraper / lead-qualifier.")


if __name__ == "__main__":
    main()
