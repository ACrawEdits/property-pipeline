from datetime import datetime, timezone


def normalize_property(raw: dict) -> dict:
    return {
        "address":           raw.get("formattedAddress") or raw.get("address"),
        "city":              raw.get("city"),
        "state":             raw.get("state"),
        "zip":               raw.get("zipCode"),
        "county":            raw.get("county"),
        "property_type":     raw.get("propertyType"),
        "bedrooms":          raw.get("bedrooms"),
        "bathrooms":         raw.get("bathrooms"),
        "sqft":              raw.get("squareFootage"),
        "year_built":        raw.get("yearBuilt"),
        "list_price":        raw.get("price") or raw.get("listPrice"),
        "rent_estimate":     raw.get("rentEstimate"),
        "rent_estimate_low": raw.get("rentEstimateLow"),
        "rent_estimate_high":raw.get("rentEstimateHigh"),
        "hoa_fee":           raw.get("hoa", {}).get("fee") if isinstance(raw.get("hoa"), dict) else raw.get("hoaFee"),
        "days_on_market":    raw.get("daysOnMarket"),
        "latitude":          raw.get("latitude"),
        "longitude":         raw.get("longitude"),
        "source":            "RentCast",
        "fetched_at":        datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "dscr_flag":         None,  # populated after normalization
    }


def normalize_rental_estimate(raw: dict, prop: dict) -> dict:
    updated = prop.copy()
    if raw:
        updated["rent_estimate"]      = raw.get("rent") or raw.get("rentEstimate") or prop.get("rent_estimate")
        updated["rent_estimate_low"]  = raw.get("rentRangeLow") or raw.get("rentEstimateLow") or prop.get("rent_estimate_low")
        updated["rent_estimate_high"] = raw.get("rentRangeHigh") or raw.get("rentEstimateHigh") or prop.get("rent_estimate_high")
    return updated


def dscr_flag(prop: dict) -> str:
    rent = prop.get("rent_estimate")
    price = prop.get("list_price")

    if not rent or not price or rent <= 0 or price <= 0:
        return "N/A"

    monthly_debt = price * 0.006  # ~7.25% 30yr at 20% down
    hoa = prop.get("hoa_fee") or 0

    denominator = monthly_debt + hoa
    if denominator <= 0:
        return "N/A"

    dscr = (rent * 0.75) / denominator

    match True:
        case _ if dscr >= 1.1:
            return "PASS"
        case _ if dscr >= 0.9:
            return "MARGINAL"
        case _:
            return "FAIL"
