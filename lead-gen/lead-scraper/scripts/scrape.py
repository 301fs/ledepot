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

# Normalized output columns — the contract with lead-qualifier.
NORMALIZED_FIELDS = [
    "name", "category", "website", "phone", "email", "reviews", "rating",
    "price", "booking", "facebook", "instagram", "address", "city", "state", "query",
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


def normalize_record(rec, query):
    """Map a provider record (Outscraper or Apify) to the normalized schema."""
    return {
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

    rows = []
    # Outscraper returns a list aligned to the queries list; each item is a list of places.
    results = client.google_maps_search(queries, **kwargs)
    for qi, places in enumerate(results):
        q = queries[qi] if qi < len(queries) else ""
        for place in places:
            rows.append(normalize_record(place, place.get("query", q)))
    return rows


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
    rows = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        rows.append(normalize_record(item, item.get("searchString", "")))
    return rows


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
    rows = runner(queries, sourcing)

    # de-dup on name+address
    seen, deduped = set(), []
    for r in rows:
        key = (r["name"].lower().strip(), r["address"].lower().strip())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        wri = csv.DictWriter(f, fieldnames=NORMALIZED_FIELDS)
        wri.writeheader()
        wri.writerows(deduped)

    with_email = sum(1 for r in deduped if r["email"])
    print(f"\nWrote {len(deduped)} unique businesses ({len(rows) - len(deduped)} dupes dropped) -> {args.output}")
    print(f"  {with_email} have an email ({round(100 * with_email / max(1, len(deduped)))}%).")
    print(f"\nNext: python3 ../lead-qualifier/scripts/score_leads.py {args.output} "
          f"--profile {args.profile} -o scored.csv")


if __name__ == "__main__":
    main()
