"""
Fetches data from the RentCast API.

Note on --limit for county-scoped pulls:
  County filtering is applied locally after fetching from the state endpoint,
  because RentCast has no county query parameter. This means --limit caps the
  pre-filter state result set. For large states (TX, CA, FL) this can be a
  large payload before the county filter is applied.
"""

import sys
import time
import requests

from config import RENTCAST_BASE_URL, HEADERS, PAGE_SIZE
from geo import GeoContext


def fetch_listings(geo_context: GeoContext, limit: int) -> list[dict]:
    all_listings: list[dict] = []
    offset = 0

    while len(all_listings) < limit:
        page_size = min(PAGE_SIZE, limit - len(all_listings))
        params = {**geo_context.api_params, "limit": page_size, "offset": offset, "status": "Active"}

        try:
            response = _get_with_backoff(f"{RENTCAST_BASE_URL}/listings/rental/long-term", params)
        except Exception as exc:
            print(f"[fetcher] listings request failed: {exc}", file=sys.stderr)
            break

        batch = response if isinstance(response, list) else response.get("data", [])
        if not batch:
            break

        all_listings.extend(batch)
        offset += len(batch)

        if len(batch) < page_size:
            break  # last page

        time.sleep(0.5)

    if geo_context.local_county_filter:
        all_listings = apply_county_filter(all_listings, geo_context.local_county_filter)

    return all_listings


def fetch_rental_estimate(
    address: str,
    property_type: str | None = None,
    bedrooms: int | None = None,
    bathrooms: float | None = None,
) -> dict | None:
    params: dict = {"address": address}
    if property_type:
        params["propertyType"] = property_type
    if bedrooms is not None:
        params["bedrooms"] = bedrooms
    if bathrooms is not None:
        params["bathrooms"] = bathrooms

    try:
        return _get_with_backoff(f"{RENTCAST_BASE_URL}/avm/rent/long-term", params)
    except Exception as exc:
        print(f"[fetcher] rent estimate failed for {address!r}: {exc}", file=sys.stderr)
        return None


def fetch_property_details(address: str) -> dict | None:
    try:
        result = _get_with_backoff(f"{RENTCAST_BASE_URL}/properties", {"address": address})
        if isinstance(result, list):
            return result[0] if result else None
        return result or None
    except Exception as exc:
        print(f"[fetcher] property details failed for {address!r}: {exc}", file=sys.stderr)
        return None


def apply_county_filter(listings: list[dict], county_name: str) -> list[dict]:
    def _normalize(name: str) -> str:
        return name.lower().removesuffix(" county").strip()

    target = _normalize(county_name)
    filtered = [
        p for p in listings
        if _normalize(p.get("county", "") or "") == target
    ]

    if not filtered:
        print(
            f"[fetcher] WARNING: county filter '{county_name}' matched 0 of "
            f"{len(listings)} listings — returning unfiltered results.",
            file=sys.stderr,
        )
        return listings

    return filtered


def _get_with_backoff(url: str, params: dict, max_retries: int = 4) -> dict | list:
    delay = 2.0
    for attempt in range(max_retries):
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)

        if response.status_code == 429:
            wait = delay * (2 ** attempt)
            print(f"[fetcher] 429 rate limit — waiting {wait:.0f}s (attempt {attempt + 1})", file=sys.stderr)
            time.sleep(wait)
            continue

        response.raise_for_status()
        return response.json()

    raise RuntimeError(f"Max retries exceeded for {url}")
