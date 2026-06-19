#!/usr/bin/env python3
"""
score_leads.py — profile-driven lead qualifier.

Scores each business on Need x Ability-to-pay x Reachability (each 0-10) and
multiplies them, so a near-zero on any one dimension kills the lead. All the
tunable parts — which need signals matter, their points, ability thresholds,
tier cutoffs, weights — come from a CAMPAIGN PROFILE (see
../../lead-pipeline/profiles/). The detection *logic* per offer lives here;
the *parameters* live in the profile. That split is what lets you pivot niche,
geography, or offer by editing config instead of code.

Usage:
    python3 score_leads.py raw_leads.csv --profile path/to/profile.yaml -o scored.csv

If --profile is omitted, built-in "website" defaults are used (handy for a quick
look, but real campaigns should pass a profile).

Profiles may be YAML (needs PyYAML: pip install pyyaml) or JSON.
"""

import argparse
import csv
import json
import re
import sys
from datetime import datetime

# ---------------------------------------------------------------------------
# Profile loading
# ---------------------------------------------------------------------------

DEFAULT_PROFILE = {
    "offer": "website",
    "qualification": {
        "need_points": {
            "no_website": 10, "social_only": 9, "no_https": 8,
            "builder_subdomain": 7, "site_exists_unverified": 5, "modern_site": 1,
        },
        "ability": {
            "review_buckets": [[0, 0], [1, 3], [10, 6], [50, 8], [200, 10]],
            "rating_full_at": 4.0, "rating_mid_at": 3.0,
            "rating_full_mult": 1.0, "rating_mid_mult": 0.85, "rating_low_mult": 0.7,
            "price_bump_levels": ["$$", "$$$", "$$$$"], "price_bump": 1,
        },
        "reach": {
            "email_phone_owner": 10, "email_phone": 9,
            "email_only": 7, "phone_only": 6, "none": 0,
        },
        "tiers": {
            "disqualify_max_need": 2,
            "A": {"min_need": 7, "min_ability": 6, "requires_email": True},
            "B": {"min_need": 7, "min_ability": 6, "requires_email": False},
            "C": {"min_composite": 30},
        },
        "weights": {"need": 1.0, "ability": 1.0, "reach": 1.0},
    },
}


def load_profile(path):
    if not path:
        return DEFAULT_PROFILE
    with open(path, encoding="utf-8") as f:
        text = f.read()
    # Try YAML first, then JSON.
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text)
    except ImportError:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            sys.exit("Profile looks like YAML but PyYAML isn't installed. "
                     "Run: pip install pyyaml --break-system-packages  (or save the profile as JSON)")
    except Exception as e:  # yaml parse error
        sys.exit(f"Could not parse profile: {e}")


# ---------------------------------------------------------------------------
# Column sniffing (tolerant of Outscraper / Apify / Apollo header variants)
# ---------------------------------------------------------------------------

COLUMN_HINTS = {
    "name":      ["name", "title", "business"],
    "website":   ["site", "website", "url", "web", "domain"],
    "phone":     ["phone", "telephone", "tel", "contact_number"],
    "email":     ["email", "e-mail", "email_1", "mail"],
    "reviews":   ["reviews", "review_count", "reviews_count", "num_reviews",
                  "user_ratings_total", "reviewscount"],
    "rating":    ["rating", "totalscore", "stars", "avg_rating", "score"],
    "category":  ["category", "type", "categories", "industry"],
    "price":     ["price", "price_level", "price_range"],
    "address":   ["full_address", "address", "location", "street"],
    "city":      ["city", "town"],
    "owner":     ["owner", "contact_name", "first_name", "person"],
    "facebook":  ["facebook", "fb"],
    "instagram": ["instagram", "insta", "ig"],
    "booking":   ["booking", "booking_appointment_link", "reserve", "order_link"],
}


def build_column_map(headers):
    cmap, used = {}, set()
    lower = {h: h.lower().strip() for h in headers}
    for concept, hints in COLUMN_HINTS.items():
        chosen = None
        for h, hl in lower.items():
            if h in used:
                continue
            if hl in hints:
                chosen = h
                break
        if not chosen:
            for h, hl in lower.items():
                if h in used:
                    continue
                if any(hint in hl for hint in hints):
                    chosen = h
                    break
        if chosen:
            cmap[concept] = chosen
            used.add(chosen)
    return cmap


def get(row, cmap, concept, default=""):
    col = cmap.get(concept)
    return (row.get(col) or "").strip() if col else default


def to_int(s):
    m = re.search(r"\d[\d,]*", str(s)) if s is not None else None
    return int(m.group(0).replace(",", "")) if m else None


def to_float(s):
    m = re.search(r"\d+(\.\d+)?", str(s)) if s is not None else None
    return float(m.group(0)) if m else None


BUILDER_HOSTS = ["wixsite.com", "weebly.com", "godaddysites.com", "business.site",
                 "blogspot.", "wordpress.com", "squarespace.com/site", "wix.com"]


def has_site(website):
    return bool(website) and website.lower() not in ("n/a", "none", "-", "null")


# ---------------------------------------------------------------------------
# Need detectors per offer.
# Each returns a dict {signal_id: human_label} of signals that FIRED for the row.
# The scorer then picks the firing signal with the highest points (from profile).
# ---------------------------------------------------------------------------

def need_signals_website(row, cmap):
    website = get(row, cmap, "website")
    social = bool(get(row, cmap, "facebook") or get(row, cmap, "instagram"))
    fired = {}
    if not has_site(website):
        if social:
            fired["social_only"] = "social-only (no real website)"
        else:
            fired["no_website"] = "no website (Google listing only)"
        return fired
    url = website.lower()
    fired["site_exists_unverified"] = "site exists — load it to confirm quality"
    if url.startswith("http://"):
        fired["no_https"] = "no HTTPS/SSL (http only)"
    if any(b in url for b in BUILDER_HOSTS):
        fired["builder_subdomain"] = "free-template/builder subdomain"
    return fired


def need_signals_automation(row, cmap):
    """Worked example. Detecting 'manual operations' from Maps data is weak;
    treat these as hints and verify before relying on them for tiering."""
    website = get(row, cmap, "website")
    social = bool(get(row, cmap, "facebook") or get(row, cmap, "instagram"))
    booking = get(row, cmap, "booking")
    fired = {}
    if not has_site(website) and social:
        fired["social_only"] = "social-only (manual/DM-driven)"
    if not booking:
        fired["no_online_booking"] = "no online booking link found"
    if not has_site(website):
        fired["phone_only"] = "no website — likely phone-only intake"
    elif booking:
        fired["modern_site"] = "has site + booking (lower automation need)"
    else:
        fired["manual_ops_site"] = "site exists but no booking/ordering"
    return fired


NEED_DETECTORS = {
    "website": need_signals_website,
    "automation": need_signals_automation,
    # Add new offers here: "database": need_signals_database, ...
}


def score_need(row, cmap, profile, notes):
    offer = profile.get("offer", "website")
    detector = NEED_DETECTORS.get(offer)
    if not detector:
        notes.append(f"need: offer '{offer}' has no detector — add one in NEED_DETECTORS")
        return 0, f"no detector for offer '{offer}'"
    points = profile["qualification"].get("need_points", {})
    fired = detector(row, cmap)
    # pick the firing signal with the highest configured points
    best_id, best_pts, best_label = None, -1, ""
    for sid, label in fired.items():
        pts = points.get(sid, 0)
        if pts > best_pts:
            best_id, best_pts, best_label = sid, pts, label
    if best_id is None:
        return 0, "no need signal fired"
    if offer == "website" and best_id == "site_exists_unverified":
        notes.append("need: site present — load it to confirm quality before tiering")
    return best_pts, best_label


def score_ability(row, cmap, profile, notes):
    cfg = profile["qualification"]["ability"]
    reviews = to_int(get(row, cmap, "reviews"))
    rating = to_float(get(row, cmap, "rating"))
    price = get(row, cmap, "price")

    if reviews is None:
        notes.append("ability: no review column — scored as 0 reviews")
        reviews = 0

    base = 0
    for min_r, pts in sorted(cfg["review_buckets"], key=lambda x: x[0]):
        if reviews >= min_r:
            base = pts
    if rating is None:
        mult = cfg["rating_low_mult"]
    elif rating >= cfg["rating_full_at"]:
        mult = cfg["rating_full_mult"]
    elif rating >= cfg["rating_mid_at"]:
        mult = cfg["rating_mid_mult"]
    else:
        mult = cfg["rating_low_mult"]

    pts = base * mult
    if price and any(lvl in price for lvl in cfg.get("price_bump_levels", [])):
        pts += cfg.get("price_bump", 0)
    pts = max(0.0, min(10.0, pts))

    bits = [f"{reviews} reviews"]
    if rating is not None:
        bits.append(f"{rating:g}★")
    if price:
        bits.append(price)
    return round(pts, 1), ", ".join(bits)


def score_reach(row, cmap, profile):
    cfg = profile["qualification"]["reach"]
    email = get(row, cmap, "email")
    phone = get(row, cmap, "phone")
    owner = get(row, cmap, "owner")
    has_email = bool(email) and "@" in email
    has_phone = bool(phone) and any(c.isdigit() for c in phone)
    if has_email and has_phone and owner:
        return cfg["email_phone_owner"], "email+phone", has_email
    if has_email and has_phone:
        return cfg["email_phone"], "email+phone", has_email
    if has_email:
        return cfg["email_only"], "email", has_email
    if has_phone:
        return cfg["phone_only"], "phone", has_email
    return cfg["none"], "none", has_email


def assign_tier(need, ability, reach, has_email, composite_100, profile):
    t = profile["qualification"]["tiers"]
    if need <= t.get("disqualify_max_need", 2):
        return "Disqualified", "low need (likely already served)"
    if reach == 0:
        return "Disqualified", "no reachable contact"
    if ability == 0:
        return "Disqualified", "no proven customers / possibly defunct"
    A, B, C = t.get("A", {}), t.get("B", {}), t.get("C", {})
    if (need >= A.get("min_need", 7) and ability >= A.get("min_ability", 6)
            and (has_email if A.get("requires_email", True) else True)):
        return "A", "hot — build demo, email first"
    if need >= B.get("min_need", 7) and ability >= B.get("min_ability", 6):
        return "B", "warm — phone-first track"
    if composite_100 >= C.get("min_composite", 30):
        return "C", "nurture — revisit later"
    return "Disqualified", "weak across dimensions"


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Profile-driven lead qualifier.")
    ap.add_argument("input", help="raw leads CSV (from lead-scraper)")
    ap.add_argument("--profile", default=None, help="campaign profile (.yaml/.json)")
    ap.add_argument("-o", "--output", default=None, help="output CSV path")
    args = ap.parse_args()

    profile = load_profile(args.profile)
    if "qualification" not in profile:
        sys.exit("Profile is missing a 'qualification' section.")
    out_path = args.output or args.input.rsplit(".", 1)[0] + "_scored.csv"
    w = profile["qualification"].get("weights", {"need": 1, "ability": 1, "reach": 1})

    with open(args.input, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        cmap = build_column_map(reader.fieldnames or [])
        rows = list(reader)
    if not rows:
        sys.exit("No rows in input.")

    missing = [c for c in ("name", "website", "phone", "reviews", "rating") if c not in cmap]
    if missing:
        print(f"Note: couldn't confidently map: {', '.join(missing)} — scored conservatively.\n")

    scored = []
    for row in rows:
        notes = []
        need, need_sig = score_need(row, cmap, profile, notes)
        ability, ability_sig = score_ability(row, cmap, profile, notes)
        reach, channel, has_email = score_reach(row, cmap, profile)

        composite = (need * w.get("need", 1)) * (ability * w.get("ability", 1)) * (reach * w.get("reach", 1))
        composite_100 = round(composite / 10.0, 1)
        tier, reason = assign_tier(need, ability, reach, has_email, composite_100, profile)

        scored.append({
            "business_name": get(row, cmap, "name"),
            "category": get(row, cmap, "category"),
            "tier": tier,
            "composite_score": composite_100,
            "need_score": need, "need_signal": need_sig,
            "ability_score": ability, "ability_signal": ability_sig,
            "reach_score": reach, "contact_channel": channel,
            "tier_reason": reason,
            "email": get(row, cmap, "email"),
            "phone": get(row, cmap, "phone"),
            "website": get(row, cmap, "website"),
            "address": get(row, cmap, "address") or get(row, cmap, "city"),
        })

    rank = {"A": 0, "B": 1, "C": 2, "Disqualified": 3}
    scored.sort(key=lambda r: (rank.get(r["tier"], 9), -r["composite_score"]))

    fields = ["business_name", "category", "tier", "composite_score", "need_score",
              "need_signal", "ability_score", "ability_signal", "reach_score",
              "contact_channel", "tier_reason", "email", "phone", "website", "address"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        wri = csv.DictWriter(f, fieldnames=fields)
        wri.writeheader()
        wri.writerows(scored)

    counts = {"A": 0, "B": 0, "C": 0, "Disqualified": 0}
    for r in scored:
        counts[r["tier"]] = counts.get(r["tier"], 0) + 1

    print(f"Profile: {profile.get('name', '(built-in defaults)')}  |  offer: {profile.get('offer')}")
    print(f"Scored {len(scored)} businesses  ->  {out_path}\n")
    print(f"  Tier A (hot, email-first): {counts['A']}")
    print(f"  Tier B (warm, call-first): {counts['B']}")
    print(f"  Tier C (nurture):          {counts['C']}")
    print(f"  Disqualified:              {counts['Disqualified']}\n")
    top = [r for r in scored if r["tier"] in ("A", "B")][:5]
    if top:
        print("Top prospects:")
        for r in top:
            print(f"  [{r['tier']}] {r['business_name']} ({r['composite_score']}) — "
                  f"{r['need_signal']}; {r['ability_signal']}; {r['contact_channel']}")
    print(f"\nGenerated {datetime.now():%Y-%m-%d %H:%M}. "
          f"Spot-check the top 5 and bottom 5 by hand before outreach.")


if __name__ == "__main__":
    main()
