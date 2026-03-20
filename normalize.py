from datetime import datetime, timezone


def _extract_hoa_fee(raw: dict) -> float | None:
    hoa = raw.get("hoa")
    if isinstance(hoa, dict):
        return hoa.get("fee")
    return raw.get("hoaFee")


def normalize_property(raw: dict) -> dict:
    hoa_fee = _extract_hoa_fee(raw)
    prop = {
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
        "hoa_fee":           hoa_fee,
        "hoa_source":        "RentCast" if hoa_fee is not None else "Missing",
        "days_on_market":    raw.get("daysOnMarket"),
        "latitude":          raw.get("latitude"),
        "longitude":         raw.get("longitude"),
        "source":            "RentCast",
        "fetched_at":        datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "dscr_flag":         None,  # populated after normalization
    }
    return {**prop, **investor_flag(prop)}


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

    hoa_fee = prop.get("hoa_fee")
    if hoa_fee is None or hoa_fee == 0:
        return "N/A - HOA missing"

    monthly_debt = price * 0.006  # ~7.25% 30yr at 20% down
    denominator = monthly_debt + hoa_fee
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


BOARDER_VIABLE_TYPES = {"single family", "condo", "townhouse"}


def investor_flag(prop: dict) -> dict:
    list_price = prop.get("list_price") or 0
    bedrooms = prop.get("bedrooms") or 0
    property_type = (prop.get("property_type") or "").strip().lower()

    down_payment_est = list_price * 0.05
    down_payment_feasible = down_payment_est <= 50000

    if list_price <= 250000:
        target_price_range = "In range"
    elif list_price <= 400000:
        target_price_range = "Above range"
    else:
        target_price_range = "Out of range"

    boarder_strategy_viable = property_type in BOARDER_VIABLE_TYPES and bedrooms >= 2

    in_range = target_price_range == "In range"
    failures = sum([not down_payment_feasible, not in_range, not boarder_strategy_viable])

    match failures:
        case 0:
            flag = "STRONG"
        case 1 if down_payment_feasible and boarder_strategy_viable:
            flag = "POSSIBLE"  # only the price range condition failed
        case 1:
            flag = "REVIEW"
        case _:
            flag = "SKIP"

    return {
        "down_payment_est":       down_payment_est,
        "down_payment_feasible":  down_payment_feasible,
        "target_price_range":     target_price_range,
        "boarder_strategy_viable": boarder_strategy_viable,
        "investor_flag":          flag,
    }
