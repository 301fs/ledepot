#!/usr/bin/env python3
"""
score_leads.py — qualify and tier local-business leads for a website-first
done-for-you tech offer (NYC tri-state).

Scoring = Need x Ability-to-pay x Reachability (each 0-10), multiplied so a
zero on any one dimension kills the lead. See ../references/qualification-rubric.md
for the full logic and how to tune it.

Input: a CSV exported from a Google Maps scraper (Outscraper / Apify) or similar.
The column names don't have to match exactly — the script sniffs for common
header variants. Missing columns are scored conservatively (and noted).

Usage:
    python3 score_leads.py input.csv [-o scored_output.csv]

Output: a CSV sorted by composite score (desc) with tier, the firing signals,
and the best contact channel, plus a printed summary.
"""

import argparse
import csv
import re
import sys
from datetime import datetime

# ---- column sniffing -------------------------------------------------------
# map a normalized concept -> list of header substrings that might represent it
COLUMN_HINTS = {
    "name":        ["name", "business", "title"],
    "website":     ["site", "website", "url", "web"],
    "phone":       ["phone", "telephone", "tel", "contact_number"],
    "email":       ["email", "e-mail", "mail"],
    "reviews":     ["review", "reviews_count", "review_count", "num_reviews", "user_ratings_total"],
    "rating":      ["rating", "stars", "score", "avg_rating"],
    "category":    ["category", "type", "categories", "industry"],
    "price":       ["price", "price_level", "price_range"],
    "address":     ["address", "full_address", "location", "street"],
    "city":        ["city", "town"],
    "state":       ["state", "region"],
    "owner":       ["owner", "contact_name", "first_name", "person"],
    "facebook":    ["facebook", "fb"],
    "instagram":   ["instagram", "ig", "insta"],
}


def build_column_map(headers):
    """Return {concept: actual_header} best-guess mapping."""
    cmap = {}
    lower = {h: h.lower().strip() for h in headers}
    for concept, hints in COLUMN_HINTS.items():
        best = None
        for h, hl in lower.items():
            if h in cmap.values():
                continue
            # exact-ish match wins
            if hl in hints:
                best = h
                break
        if not best:
            for h, hl in lower.items():
                if h in cmap.values():
                    continue
                if any(hint in hl for hint in hints):
                    best = h
                    break
        if best:
            cmap[concept] = best
    return cmap


def get(row, cmap, concept, default=""):
    col = cmap.get(concept)
    if not col:
        return default
    return (row.get(col) or "").strip()


def to_int(s):
    if s is None:
        return None
    m = re.search(r"\d[\d,]*", str(s))
    return int(m.group(0).replace(",", "")) if m else None


def to_float(s):
    if s is None:
        return None
    m = re.search(r"\d+(\.\d+)?", str(s))
    return float(m.group(0)) if m else None


# ---- dimension scorers -----------------------------------------------------

def score_need(row, cmap, notes):
    """0-10. Highest applicable signal. Returns (points, signal_label)."""
    website = get(row, cmap, "website")
    fb = get(row, cmap, "facebook")
    ig = get(row, cmap, "instagram")
    has_site = bool(website) and website.lower() not in ("n/a", "none", "-", "null")
    has_social = bool(fb or ig)

    if not has_site and not has_social:
        return 10, "no website (Google listing only)"
    if not has_site and has_social:
        return 9, "social-only (no real website)"

    # A website exists. We can only infer quality from the URL string here;
    # SKILL.md instructs the operator to actually load the site when this
    # signal drives tiering. Cheap heuristics below:
    url = website.lower()
    pts, signal = 5, "site exists, quality unverified"
    if url.startswith("http://"):
        pts, signal = 8, "no HTTPS/SSL (http only)"
    # free-host / builder subdomains often indicate a weak template site
    weak_hosts = ["wixsite.com", "weebly.com", "godaddysites.com",
                  "business.site", "blogspot.", "wordpress.com", "squarespace.com/site"]
    if any(w in url for w in weak_hosts):
        pts, signal = max(pts, 7), "free-template/builder subdomain"
    # Google "business.site" pages are a strong tell of zero real web investment
    if "business.site" in url:
        pts, signal = 8, "google business.site page (no real website)"

    notes.append("need: site present — load it to confirm quality before tiering")
    return pts, signal


def score_ability(row, cmap, notes):
    """0-10 from reviews, rating, price, longevity. Returns (points, label)."""
    reviews = to_int(get(row, cmap, "reviews"))
    rating = to_float(get(row, cmap, "rating"))
    price = get(row, cmap, "price")

    if reviews is None:
        notes.append("ability: no review-count column — scored conservatively")
        reviews = 0

    if reviews == 0:
        base = 0
    elif reviews < 10:
        base = 3
    elif reviews < 50:
        base = 6
    elif reviews < 200:
        base = 8
    else:
        base = 10

    if rating is None:
        mult = 0.85  # unknown rating: mild penalty
    elif rating >= 4.0:
        mult = 1.0
    elif rating >= 3.0:
        mult = 0.85
    else:
        mult = 0.7

    pts = base * mult

    # price level bump
    if price and ("$$" in price or "$$$" in price or "$$$$" in price):
        pts += 1

    pts = max(0, min(10, pts))
    label_bits = []
    label_bits.append(f"{reviews} reviews")
    if rating is not None:
        label_bits.append(f"{rating:g}★")
    if price:
        label_bits.append(price)
    return round(pts, 1), ", ".join(label_bits)


def score_reach(row, cmap, notes):
    """0-10. Returns (points, channel_label)."""
    email = get(row, cmap, "email")
    phone = get(row, cmap, "phone")
    owner = get(row, cmap, "owner")
    has_email = bool(email) and "@" in email
    has_phone = bool(phone) and any(ch.isdigit() for ch in phone)

    if has_email and has_phone and owner:
        return 10, "email+phone"
    if has_email and has_phone:
        return 9, "email+phone"
    if has_email:
        return 7, "email"
    if has_phone:
        return 6, "phone"
    return 0, "none"


def assign_tier(need, ability, reach, has_email, composite_100):
    if need <= 2:
        return "Disqualified", "already has a modern site"
    if reach == 0:
        return "Disqualified", "no reachable contact"
    if ability == 0:
        return "Disqualified", "no proven customers / possibly defunct"
    if need >= 7 and ability >= 6 and has_email:
        return "A", "hot — build demo, email first"
    if need >= 7 and ability >= 6 and not has_email:
        return "B", "warm — phone-first track"
    if composite_100 >= 30:
        return "C", "nurture — revisit later"
    return "Disqualified", "weak across dimensions"


# ---- main ------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Score & tier local-business leads.")
    ap.add_argument("input", help="input CSV from a Maps scraper")
    ap.add_argument("-o", "--output", default=None, help="output CSV path")
    args = ap.parse_args()

    out_path = args.output or args.input.rsplit(".", 1)[0] + "_scored.csv"

    with open(args.input, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        cmap = build_column_map(headers)
        rows = list(reader)

    if not rows:
        print("No rows found in input.", file=sys.stderr)
        sys.exit(1)

    missing = [c for c in ("name", "website", "phone", "reviews", "rating") if c not in cmap]
    if missing:
        print(f"Note: could not confidently map columns for: {', '.join(missing)}. "
              f"Scored conservatively where data was unavailable.\n")

    scored = []
    for row in rows:
        notes = []
        need, need_sig = score_need(row, cmap, notes)
        ability, ability_sig = score_ability(row, cmap, notes)
        reach, channel = score_reach(row, cmap, notes)

        composite = need * ability * reach           # 0..1000
        composite_100 = round(composite / 10.0, 1)   # 0..100

        email = get(row, cmap, "email")
        has_email = bool(email) and "@" in email
        tier, tier_reason = assign_tier(need, ability, reach, has_email, composite_100)

        scored.append({
            "business_name": get(row, cmap, "name"),
            "category": get(row, cmap, "category"),
            "tier": tier,
            "composite_score": composite_100,
            "need_score": need,
            "need_signal": need_sig,
            "ability_score": ability,
            "ability_signal": ability_sig,
            "reach_score": reach,
            "contact_channel": channel,
            "tier_reason": tier_reason,
            "email": email,
            "phone": get(row, cmap, "phone"),
            "website": get(row, cmap, "website"),
            "address": get(row, cmap, "address") or get(row, cmap, "city"),
        })

    # sort: Tier order then composite desc
    tier_rank = {"A": 0, "B": 1, "C": 2, "Disqualified": 3}
    scored.sort(key=lambda r: (tier_rank.get(r["tier"], 9), -r["composite_score"]))

    fields = ["business_name", "category", "tier", "composite_score",
              "need_score", "need_signal", "ability_score", "ability_signal",
              "reach_score", "contact_channel", "tier_reason",
              "email", "phone", "website", "address"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in scored:
            w.writerow(r)

    # summary
    counts = {"A": 0, "B": 0, "C": 0, "Disqualified": 0}
    for r in scored:
        counts[r["tier"]] = counts.get(r["tier"], 0) + 1

    print(f"Scored {len(scored)} businesses  →  {out_path}\n")
    print(f"  Tier A (hot, email-first): {counts['A']}")
    print(f"  Tier B (warm, call-first): {counts['B']}")
    print(f"  Tier C (nurture):          {counts['C']}")
    print(f"  Disqualified:              {counts['Disqualified']}\n")

    top = [r for r in scored if r["tier"] in ("A", "B")][:5]
    if top:
        print("Top prospects:")
        for r in top:
            print(f"  [{r['tier']}] {r['business_name']}  "
                  f"({r['composite_score']}) — {r['need_signal']}; "
                  f"{r['ability_signal']}; {r['contact_channel']}")
    print(f"\nGenerated {datetime.now():%Y-%m-%d %H:%M}. "
          f"Spot-check the top 5 and bottom 5 by hand before outreach.")


if __name__ == "__main__":
    main()
