#!/usr/bin/env python3
"""
Property data pipeline — RentCast → normalized Excel output.

Usage examples:
    python pipeline.py --zip 20175
    python pipeline.py --city Leesburg --state VA --limit 200 --enrich
    python pipeline.py --county Loudoun --state VA --limit 500
    python pipeline.py --state TX --limit 100
"""

import argparse
import os
import sys
from datetime import date
from collections import Counter

from config import DEFAULT_LIMIT, OUTPUT_WORKBOOK
from geo import resolve_geo
from fetcher import fetch_listings, fetch_rental_estimate
from normalize import normalize_property, normalize_rental_estimate, dscr_flag
from writer import write_to_excel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch rental property listings from RentCast and export to Excel."
    )
    parser.add_argument("--zip",    dest="zipcode", help="ZIP code")
    parser.add_argument("--city",   help="City name")
    parser.add_argument("--state",  help="Two-letter state code")
    parser.add_argument("--county", help="County name (requires --state)")
    parser.add_argument("--limit",  type=int, default=DEFAULT_LIMIT, help=f"Max records (default {DEFAULT_LIMIT})")
    parser.add_argument("--enrich", action="store_true", help="Fetch individual AVM rent estimates per property")
    parser.add_argument("--output", default=None, help="Output .xlsx path (default: MODELS/CHSSNotCheckersRealty v4.xlsx)")
    return parser.parse_args()


def main():
    if not os.environ.get("RENTCAST_API_KEY"):
        print("ERROR: RENTCAST_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    args = parse_args()

    # 1. Resolve geography
    try:
        geo = resolve_geo(
            zipcode=args.zipcode,
            city=args.city,
            state=args.state,
            county=args.county,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"[pipeline] Geo: {geo.label}")
    if geo.local_county_filter:
        print(f"[pipeline] County filter will be applied locally after fetching state data.")

    # 2. Fetch listings
    print(f"[pipeline] Fetching up to {args.limit} listings...")
    raw_listings = fetch_listings(geo, args.limit)
    print(f"[pipeline] Fetched {len(raw_listings)} listings.")

    if not raw_listings:
        print("[pipeline] No listings found. Exiting.")
        sys.exit(0)

    # 3. Normalize
    properties = [normalize_property(r) for r in raw_listings]

    # 4. Enrich with AVM rent estimates if requested
    if args.enrich:
        print(f"[pipeline] Enriching {len(properties)} properties with AVM rent estimates...")
        for i, prop in enumerate(properties):
            address = prop.get("address")
            if not address:
                continue
            estimate = fetch_rental_estimate(
                address=address,
                property_type=prop.get("property_type"),
                bedrooms=prop.get("bedrooms"),
                bathrooms=prop.get("bathrooms"),
            )
            if estimate:
                properties[i] = normalize_rental_estimate(estimate, prop)
            if (i + 1) % 10 == 0:
                print(f"[pipeline]   enriched {i + 1}/{len(properties)}")

    # 5. Compute DSCR flags
    for prop in properties:
        prop["dscr_flag"] = dscr_flag(prop)

    # 6. Write to Excel
    output_path = args.output or OUTPUT_WORKBOOK
    print(f"[pipeline] Writing to {output_path}...")
    written_path = write_to_excel(properties, geo, output_path)

    # 7. Summary
    def _dscr_bucket(flag: str | None) -> str:
        if flag in ("PASS", "MARGINAL", "FAIL"):
            return flag
        if flag and str(flag).startswith("N/A"):
            return "N/A"
        return "N/A"

    buckets = Counter(_dscr_bucket(p["dscr_flag"]) for p in properties)
    print(f"\n{'='*50}")
    print(f"  Records written : {len(properties)}")
    print(f"  DSCR PASS       : {buckets.get('PASS', 0)}")
    print(f"  DSCR MARGINAL   : {buckets.get('MARGINAL', 0)}")
    print(f"  DSCR FAIL       : {buckets.get('FAIL', 0)}")
    print(f"  DSCR N/A        : {buckets.get('N/A', 0)}")
    print(f"  Output          : {written_path}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
