#!/usr/bin/env python3
"""
scrape.py — source local businesses from Google Maps into a normalized CSV.

Reads a campaign profile's `sourcing` section, builds "<niche> in <location>"
queries, calls the configured provider (Outscraper or Apify), and writes ONE
normalized CSV that lead-qualifier can score directly. The normalized schema is
the contract between the two skills — keep it stable.

Usage:
    export OUTSCRAPER_API_KEY=...        # or APIFY_API_TOKEN=... for apify
    python3 scrape.py --profile ../../lead-pipeline/profiles/<campaign>.yaml -o raw_leads.csv

Dry run (print the queries it WOULD send, hit no API, spend nothing):
    python3 scrape.py --profile <campaign>.yaml --dry-run

Providers:
  outscraper -> needs `pip install outscraper`, env OUTSCRAPER_API_KEY
  apify      -> needs `pip install apify-client`, env APIFY_API_TOKEN

Profiles are YAML (needs PyYAML) or JSON.
"""

import argparse
import csv
import json
import os
import sys

# Normalized CSV columns — the contract with lead-qualifier.
# The first block is what qualification scores on; the second block is content the
# website-build step (site-brief) reuses (hours, geo, the owner's own blurb, badges).
# Nested content too rich for a CSV cell (full review text, photo URLs, service menus)
# is preserved in the parallel <output>.full.json instead.
NORMALIZED_FIELDS = [
    # qualification fields
    "name", "category", "website", "phone", "email", "reviews", "rating",
    "price", "booking", "facebook", "instagram", "address", "city", "state",
    # website-build content fields
    "hours", "latitude", "longitude", "plus_code", "description", "attributes",
    "photo_count", "place_id", "query",
]


def load_profile(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text)
    except ImportError:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            sys.exit("Profile is YAML but PyYAML isn't installed. "
                     "pip install pyyaml --break-system-packages  (or use a JSON profile)")


def build_queries(sourcing):
    niches = sourcing.get("niches", [])
    locations = sourcing.get("locations", [])
    if not niches or not locations:
        sys.exit("Profile sourcing needs both `niches` and `locations`.")
    return [f"{n} in {loc}" for n in niches for loc in locations]


def first(d, *keys, default=""):
    """Return the first present, non-empty value among keys (case-insensitive)."""
    lower = {k.lower(): v for k, v in d.items()}
    for k in keys:
        v = lower.get(k.lower())
        if v not in (None, "", []):
            return v
    return default


def flatten(v):
    """Make a value safe for a CSV cell: dicts/lists -> compact JSON string."""
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)
    return v


def normalize_record(rec, query):
    """Map a provider record (Outscraper or Apify) to the flat CSV schema.
    The full record is kept separately (full.json) so nested content survives."""
    return {
        # --- qualification fields ---
        "name":      first(rec, "name", "title"),
        "category":  first(rec, "type", "category", "categoryName", "categories"),
        "website":   first(rec, "site", "website", "url", "domain"),
        "phone":     first(rec, "phone", "phone_1", "phoneUnformatted", "telephone"),
        "email":     first(rec, "email_1", "email", "emails"),
        "reviews":   first(rec, "reviews", "reviewsCount", "reviews_count", "user_ratings_total", default=""),
        "rating":    first(rec, "rating", "totalScore", "stars", default=""),
        "price":     first(rec, "price_level", "price", "priceRange", "categoryPrice"),
        "booking":   first(rec, "booking_appointment_link", "reserve_table_link", "order_link", "bookingLinks"),
        "facebook":  first(rec, "facebook", "fb"),
        "instagram": first(rec, "instagram", "ig"),
        "address":   first(rec, "full_address", "address"),
        "city":      first(rec, "city", "borough"),
        "state":     first(rec, "us_state", "state"),
        # --- website-build content fields ---
        "hours":       flatten(first(rec, "working_hours", "hours", "openingHours", "opening_hours")),
        "latitude":    first(rec, "latitude", "lat"),
        "longitude":   first(rec, "longitude", "lng", "lon"),
        "plus_code":   first(rec, "plus_code", "plusCode"),
        "description": first(rec, "description", "about_owner", "from_the_owner", "ownerDescription"),
        "attributes":  flatten(first(rec, "about", "attributes", "additional_info", "additionalInfo")),
        "photo_count": first(rec, "photos_count", "photosCount", "imagesCount", default=""),
        "place_id":    first(rec, "place_id", "placeId", "google_id", "fid"),
        "query":     query,
    }


# --- providers --------------------------------------------------------------

def run_outscraper(queries, sourcing):
    try:
        from outscraper import OutscraperClient  # type: ignore
    except ImportError:
        sys.exit("Outscraper provider needs: pip install outscraper")
    key = os.environ.get("OUTSCRAPER_API_KEY")
    if not key:
        sys.exit("Set OUTSCRAPER_API_KEY in your environment.")
    client = OutscraperClient(api_key=key)

    enrich = ["domains_service", "emails_validator_service"] if sourcing.get("enrich_emails") else None
    kwargs = dict(
        limit=sourcing.get("limit_per_query", 50),
        language=sourcing.get("language", "en"),
        region=sourcing.get("region", "US"),
    )
    if enrich:
        kwargs["enrichment"] = enrich

    raw = []
    # Outscraper returns a list aligned to the queries list; each item is a list of places.
    results = client.google_maps_search(queries, **kwargs)
    for qi, places in enumerate(results):
        q = queries[qi] if qi < len(queries) else ""
        for place in places:
            place["_query"] = place.get("query", q)
            raw.append(place)
    return raw


def run_apify(queries, sourcing):
    try:
        from apify_client import ApifyClient  # type: ignore
    except ImportError:
        sys.exit("Apify provider needs: pip install apify-client")
    token = os.environ.get("APIFY_API_TOKEN")
    if not token:
        sys.exit("Set APIFY_API_TOKEN in your environment.")
    client = ApifyClient(token)
    run_input = {
        "searchStringsArray": queries,
        "maxCrawledPlacesPerSearch": sourcing.get("limit_per_query", 50),
        "language": sourcing.get("language", "en"),
        "scrapeContacts": bool(sourcing.get("enrich_emails")),
    }
    # compass/crawler-google-places is the widely used Maps actor; swap if you prefer another.
    actor = sourcing.get("apify_actor", "compass/crawler-google-places")
    run = client.actor(actor).call(run_input=run_input)
    raw = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        item["_query"] = item.get("searchString", "")
        raw.append(item)
    return raw


PROVIDERS = {"outscraper": run_outscraper, "apify": run_apify}


def main():
    ap = argparse.ArgumentParser(description="Source local businesses to a normalized CSV.")
    ap.add_argument("--profile", required=True, help="campaign profile (.yaml/.json)")
    ap.add_argument("-o", "--output", default="raw_leads.csv")
    ap.add_argument("--dry-run", action="store_true", help="print queries, call no API")
    args = ap.parse_args()

    profile = load_profile(args.profile)
    sourcing = profile.get("sourcing")
    if not sourcing:
        sys.exit("Profile has no `sourcing` section.")
    queries = build_queries(sourcing)
    provider = sourcing.get("provider", "outscraper").lower()

    print(f"Profile: {profile.get('name')}  |  provider: {provider}")
    print(f"{len(queries)} queries "
          f"({len(sourcing.get('niches', []))} niches x {len(sourcing.get('locations', []))} locations), "
          f"up to {sourcing.get('limit_per_query', 50)} each.")

    if args.dry_run:
        print("\n-- DRY RUN — queries that would be sent --")
        for q in queries:
            print("  ", q)
        est = len(queries) * sourcing.get("limit_per_query", 50)
        print(f"\nWould fetch up to ~{est} places. No API called, nothing spent.")
        return

    runner = PROVIDERS.get(provider)
    if not runner:
        sys.exit(f"Unknown provider '{provider}'. Use 'outscraper' or 'apify'.")

    print("\nCalling provider — this can take a few minutes for large sweeps...")
    raw_records = runner(queries, sourcing)

    # Normalize + de-dup on name+address, keeping the full raw record alongside.
    seen, flat_rows, full_records = set(), [], []
    for rec in raw_records:
        flat = normalize_record(rec, rec.get("_query", ""))
        key = (flat["name"].lower().strip(), flat["address"].lower().strip())
        if not flat["name"] or key in seen:
            continue
        seen.add(key)
        flat_rows.append(flat)
        full_records.append(rec)

    # 1) flat CSV for qualification
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        wri = csv.DictWriter(f, fieldnames=NORMALIZED_FIELDS)
        wri.writeheader()
        wri.writerows(flat_rows)

    # 2) full JSON for the website-build step (keeps nested reviews/photos/services)
    full_path = args.output.rsplit(".", 1)[0] + ".full.json"
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(full_records, f, ensure_ascii=False, indent=2)

    with_email = sum(1 for r in flat_rows if r["email"])
    print(f"\nWrote {len(flat_rows)} unique businesses "
          f"({len(raw_records) - len(flat_rows)} dupes/blanks dropped)")
    print(f"  flat CSV (for qualifying): {args.output}")
    print(f"  full JSON (for website build): {full_path}")
    print(f"  {with_email} have an email ({round(100 * with_email / max(1, len(flat_rows)))}%).")
    print(f"\nNext: python3 ../lead-qualifier/scripts/score_leads.py {args.output} "
          f"--profile {args.profile} -o scored.csv")


if __name__ == "__main__":
    main()
