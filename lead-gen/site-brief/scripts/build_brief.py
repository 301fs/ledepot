#!/usr/bin/env python3
"""
build_brief.py — turn qualified leads + their scraped content into per-lead
WEBSITE BRIEFS (JSON + Markdown) ready for the site-build step.

It joins the qualifier's scored.csv (tier per lead) with the scraper's
<output>.full.json (rich content: hours, reviews, photos, the owner's blurb,
trust badges) and, for the tiers you choose, writes one brief per business:
everything a builder needs to draft that salon's site — plus an explicit list of
what's still MISSING and must be collected before the site is real.

Usage:
    python3 build_brief.py \
        --scored scored.csv \
        --full   raw_leads.full.json \
        --tiers  A,B \
        --offer  website \
        --out    briefs/

If --full is absent it falls back to the flat scored.csv columns (less content).
Each lead produces briefs/<slug>.json and briefs/<slug>.md.
"""

import argparse
import csv
import json
import os
import re
import sys


def norm(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "lead").lower()).strip("-") or "lead"


def first(d, *keys, default=""):
    if not isinstance(d, dict):
        return default
    low = {k.lower(): v for k, v in d.items()}
    for k in keys:
        v = low.get(k.lower())
        if v not in (None, "", [], {}):
            return v
    return default


# --- content extractors (defensive: provider shapes vary) -------------------

def extract_testimonials(rec, limit=4):
    out = []
    data = first(rec, "reviews_data", "reviews", "testimonials", default=[])
    if isinstance(data, list):
        for r in data:
            if isinstance(r, dict):
                text = first(r, "review_text", "text", "snippet", "review")
                if not text:
                    continue
                out.append({
                    "text": text.strip(),
                    "author": first(r, "author_title", "author", "reviewer_name", "name"),
                    "rating": first(r, "review_rating", "rating", "stars", default=""),
                })
            elif isinstance(r, str) and r.strip():
                out.append({"text": r.strip(), "author": "", "rating": ""})
    return out[:limit]


def extract_services(rec):
    svc = first(rec, "services", "service_options", default=[])
    if isinstance(svc, list) and svc:
        return [s if isinstance(s, str) else first(s, "name", "title") for s in svc]
    # fall back to review topic tags if present (e.g. "gel manicure", "blowout")
    tags = first(rec, "reviews_tags", "review_tags", "popular_for", default=[])
    if isinstance(tags, list) and tags:
        return [t if isinstance(t, str) else first(t, "title", "keyword") for t in tags][:8]
    return []


def extract_hours(rec):
    h = first(rec, "working_hours", "hours", "opening_hours", default="")
    if isinstance(h, dict):
        return {str(k): str(v) for k, v in h.items()}
    if isinstance(h, str) and h.strip():
        try:
            j = json.loads(h)
            return j if isinstance(j, dict) else {"raw": h}
        except (json.JSONDecodeError, ValueError):
            return {"raw": h}
    return {}


def extract_badges(rec):
    out = []
    about = first(rec, "about", "attributes", "additional_info", default=None)
    if isinstance(about, str):
        try:
            about = json.loads(about)
        except (json.JSONDecodeError, ValueError):
            return [about] if about else []
    if isinstance(about, dict):
        for group, vals in about.items():
            if isinstance(vals, dict):
                out += [k for k, v in vals.items() if v]
            elif isinstance(vals, list):
                out += [str(v) for v in vals]
    elif isinstance(about, list):
        out += [str(v) for v in about]
    return out[:8]


def extract_photos(rec, limit=12):
    ph = first(rec, "photos", "images", "photos_data", default=[])
    urls = []
    if isinstance(ph, list):
        for p in ph:
            if isinstance(p, str):
                urls.append(p)
            elif isinstance(p, dict):
                u = first(p, "photo_url", "url", "image", "src")
                if u:
                    urls.append(u)
    return urls[:limit]


# --- brief assembly ---------------------------------------------------------

PAGE_PLANS = {
    "website": ["Home", "Services", "Gallery", "Reviews", "Book / Contact"],
    "automation": ["Home", "Services", "Online Booking", "Contact"],
    "database": ["Home", "Services", "Client Portal", "Contact"],
}


def map_url(lat, lng, name, address):
    if lat and lng:
        return f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"
    q = (name + " " + address).strip().replace(" ", "+")
    return f"https://www.google.com/maps/search/?api=1&query={q}" if q else ""


def make_tagline(rec, scored_row):
    name = first(rec, "name", "title") or scored_row.get("business_name", "")
    city = first(rec, "city", "borough") or ""
    cat = (first(rec, "type", "category") or scored_row.get("category", "") or "salon").lower()
    loc = f" in {city}" if city else ""
    return f"{name} — {cat}{loc}".strip()


def build_brief(scored_row, rec, offer):
    name = scored_row.get("business_name") or first(rec, "name", "title")
    address = first(rec, "full_address", "address") or scored_row.get("address", "")
    lat, lng = first(rec, "latitude", "lat"), first(rec, "longitude", "lng", "lon")
    testimonials = extract_testimonials(rec)
    services = extract_services(rec)
    hours = extract_hours(rec)
    badges = extract_badges(rec)
    photos = extract_photos(rec)
    owner_blurb = first(rec, "description", "from_the_owner", "about_owner", "ownerDescription")
    current_site = first(rec, "site", "website") or scored_row.get("website", "")
    booking = first(rec, "booking_appointment_link", "booking", "reserve_table_link")
    email = first(rec, "email_1", "email") or scored_row.get("email", "")

    # gaps: what a real site needs that the scrape can't provide
    gaps = []
    if not photos:
        gaps.append("High-resolution photos (interior, work/portfolio, team) — scrape only has counts/thumbnails.")
    if not services or len(services) < 3:
        gaps.append("Full service menu with prices — confirm directly with the owner.")
    if not hours:
        gaps.append("Business hours — not captured; confirm with owner or Maps profile.")
    if not email:
        gaps.append("Owner email — none found; needed for the demo-email send (else phone-first).")
    gaps.append("Logo / brand colors — ask the owner or design simple defaults.")
    gaps.append("Domain name — register once they're interested.")

    return {
        "business": {
            "name": name,
            "category": first(rec, "type", "category") or scored_row.get("category", ""),
            "tagline": make_tagline(rec, scored_row),
            "owner_blurb": owner_blurb,
        },
        "lead": {
            "tier": scored_row.get("tier", ""),
            "composite_score": scored_row.get("composite_score", ""),
            "need_signal": scored_row.get("need_signal", ""),
            "query": first(rec, "_query") or scored_row.get("query", ""),
        },
        "contact": {
            "phone": first(rec, "phone", "phone_1") or scored_row.get("phone", ""),
            "email": email,
            "address": address,
            "city": first(rec, "city", "borough") or scored_row.get("city", ""),
            "state": first(rec, "us_state", "state") or scored_row.get("state", ""),
            "latitude": lat, "longitude": lng,
            "map_url": map_url(lat, lng, name, address),
        },
        "online_presence": {
            "current_website": current_site,
            "booking_link": booking,
            "facebook": first(rec, "facebook", "fb"),
            "instagram": first(rec, "instagram", "ig"),
        },
        "proof": {
            "rating": first(rec, "rating", "totalScore") or scored_row.get("rating", ""),
            "review_count": first(rec, "reviews", "reviews_count", "reviewsCount") or "",
            "testimonials": testimonials,
            "badges": badges,
        },
        "content": {
            "services": services,
            "hours": hours,
            "photo_urls": photos,
        },
        "site_plan": {
            "suggested_pages": PAGE_PLANS.get(offer, PAGE_PLANS["website"]),
            "home_sections": ["Hero (name + tagline + Book CTA)", "Services", "Testimonials",
                              "Gallery", "Location & hours", "Contact / booking"],
            "primary_cta": "Book an appointment" if offer == "website" else "Get started",
            "tone": "warm, local, trustworthy" + (" · " + ", ".join(badges) if badges else ""),
        },
        "gaps_to_fill": gaps,
    }


def brief_to_md(b):
    L = []
    biz, c, p, cn, sp = b["business"], b["contact"], b["proof"], b["content"], b["site_plan"]
    L.append(f"# Website brief — {biz['name']}")
    L.append(f"*{biz['tagline']}*  ·  Tier {b['lead']['tier']} ({b['lead']['need_signal']})\n")
    if biz["owner_blurb"]:
        L.append(f"> {biz['owner_blurb']}\n")
    L.append("## Contact & location")
    L.append(f"- Phone: {c['phone'] or '—'}")
    L.append(f"- Email: {c['email'] or '— (none found; phone-first)'}")
    L.append(f"- Address: {c['address'] or '—'}")
    if c["map_url"]:
        L.append(f"- Map: {c['map_url']}")
    op = b["online_presence"]
    L.append("\n## Current online presence")
    L.append(f"- Website: {op['current_website'] or '— (none)'}")
    L.append(f"- Booking: {op['booking_link'] or '—'}")
    L.append(f"- Facebook: {op['facebook'] or '—'}  ·  Instagram: {op['instagram'] or '—'}")
    L.append("\n## Social proof")
    L.append(f"- Rating: {p['rating'] or '—'}  ·  Reviews: {p['review_count'] or '—'}")
    if p["badges"]:
        L.append(f"- Badges: {', '.join(p['badges'])}")
    if p["testimonials"]:
        L.append("- Testimonials (use on the site):")
        for t in p["testimonials"]:
            who = f" — {t['author']}" if t.get("author") else ""
            L.append(f"  - \"{t['text']}\"{who}")
    L.append("\n## Content captured")
    L.append(f"- Services/specialties: {', '.join(cn['services']) if cn['services'] else '— (collect from owner)'}")
    if cn["hours"]:
        L.append(f"- Hours: {json.dumps(cn['hours'], ensure_ascii=False)}")
    L.append(f"- Photos available: {len(cn['photo_urls'])}")
    L.append("\n## Suggested site")
    L.append(f"- Pages: {', '.join(sp['suggested_pages'])}")
    L.append(f"- Home sections: {', '.join(sp['home_sections'])}")
    L.append(f"- Primary CTA: {sp['primary_cta']}")
    L.append(f"- Tone: {sp['tone']}")
    L.append("\n## Gaps to fill before building")
    for g in b["gaps_to_fill"]:
        L.append(f"- [ ] {g}")
    return "\n".join(L) + "\n"


# --- main -------------------------------------------------------------------

def load_full(path):
    if not path or not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        recs = json.load(f)
    index = {}
    for r in recs:
        nm = norm(first(r, "name", "title"))
        if nm:
            index[nm] = r
    return index


def main():
    ap = argparse.ArgumentParser(description="Build per-lead website briefs.")
    ap.add_argument("--scored", required=True, help="qualifier scored.csv")
    ap.add_argument("--full", help="scraper <output>.full.json (rich content)")
    ap.add_argument("--tiers", default="A,B", help="comma list of tiers to build (default A,B)")
    ap.add_argument("--offer", default="website", help="offer type (page plan)")
    ap.add_argument("--out", default="briefs", help="output directory")
    args = ap.parse_args()

    tiers = {t.strip().upper() for t in args.tiers.split(",") if t.strip()}
    with open(args.scored, newline="", encoding="utf-8-sig") as f:
        scored = list(csv.DictReader(f))
    full_index = load_full(args.full)
    os.makedirs(args.out, exist_ok=True)

    built = 0
    for row in scored:
        if (row.get("tier") or "").strip().upper() not in tiers:
            continue
        rec = full_index.get(norm(row.get("business_name", "")), {})
        brief = build_brief(row, rec, args.offer)
        slug = slugify(row.get("business_name", ""))
        with open(os.path.join(args.out, slug + ".json"), "w", encoding="utf-8") as f:
            json.dump(brief, f, ensure_ascii=False, indent=2)
        with open(os.path.join(args.out, slug + ".md"), "w", encoding="utf-8") as f:
            f.write(brief_to_md(brief))
        built += 1
        print(f"  brief: {row.get('business_name')}  [{row.get('tier')}]  -> {slug}.json / .md")

    if not built:
        print(f"No leads in tiers {sorted(tiers)} found in {args.scored}.")
        return
    matched = sum(1 for row in scored
                  if (row.get('tier') or '').strip().upper() in tiers
                  and norm(row.get('business_name', '')) in full_index)
    print(f"\nBuilt {built} briefs in {args.out}/  "
          f"({matched} enriched from full.json, {built - matched} from flat CSV only).")
    print("Each brief lists gaps to fill before the site is build-ready. "
          "Hand the .json to a site generator or the .md to whoever builds it.")


if __name__ == "__main__":
    main()
