# Website Brief — schema

A **brief** is the handoff packet from the lead funnel to the website build. It
collects everything the scrape captured about one qualified business, shaped into
what a site needs, plus an explicit list of what's still missing. One brief per
lead, emitted as JSON (for a generator) and Markdown (for a human).

## JSON structure

```jsonc
{
  "business":   { "name", "category", "tagline", "owner_blurb" },
  "lead":       { "tier", "composite_score", "need_signal", "query" },
  "contact":    { "phone", "email", "address", "city", "state",
                  "latitude", "longitude", "map_url" },
  "online_presence": { "current_website", "booking_link", "facebook", "instagram" },
  "proof":      { "rating", "review_count",
                  "testimonials": [ { "text", "author", "rating" } ],
                  "badges": [ "women-owned", "LGBTQ+ friendly", ... ] },
  "content":    { "services": [...], "hours": { ... }, "photo_urls": [...] },
  "site_plan":  { "suggested_pages", "home_sections", "primary_cta", "tone" },
  "gaps_to_fill": [ "High-res photos ...", "Service menu + prices ...", ... ]
}
```

## Where each field comes from

| Section | Source in the scrape |
|---|---|
| business.name/category/tagline | flat CSV + full.json |
| business.owner_blurb | `description` / "from the owner" text (full.json) |
| contact.* | phone/address/geo from the scrape; `map_url` derived from lat/lng or name+address |
| online_presence | `website`, `booking`, `facebook`, `instagram` |
| proof.testimonials | `reviews_data` review text (needs reviews pulled at scrape time) |
| proof.badges | `about` / attributes (e.g. women-owned, wheelchair accessible) |
| content.services | `services`, or review topic tags as a fallback |
| content.hours | `working_hours` |
| content.photo_urls | `photos` (URLs if the scrape pulled them) |

## `gaps_to_fill` — why it matters

The scrape gives you real, usable raw material (name, location, phone, rating,
testimonials, badges, the owner's own words) but **not** everything a finished site
needs. The brief is honest about the difference so nobody ships a half-empty page:

- **High-res photos** — Maps gives counts/thumbnails, not usable hero images.
- **Service menu + prices** — rarely complete on Maps; confirm with the owner.
- **Hours** — include if captured, else flag.
- **Owner email** — if missing, the demo-email play can't run (route to phone).
- **Logo / brand colors / domain** — never on Maps; collect on interest.

A good brief turns "we scraped them" into "here's their site, and here are the five
things to ask them for on the call."

## Getting richer content at scrape time

Testimonials, services, photos, and hours only appear in `full.json` if the scrape
pulled them. With Outscraper/Apify, enable reviews (e.g. a small `reviewsLimit` /
`maxReviews`) and photos in the actor input. More content per place costs a little
more but makes the briefs — and the demo sites — far stronger. The booking-platform
domains (Booksy/Vagaro/Fresha/Zoca/Phorest) in `online_presence.current_website`
are a strong tell that the business has no real site of its own — prime build targets.
