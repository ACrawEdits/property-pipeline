from datetime import datetime, timezone

from config import (monthly_piti_factor, DSCR_INSURANCE_MONTHLY, DSCR_RENT_HAIRCUT,
                    DSCR_PASS_THRESHOLD, DSCR_MARGINAL_THRESHOLD,
                    DEFAULT_PROFILE, InvestorProfile)


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
    hoa_source = prop.get("hoa_source")
    if hoa_fee is None:
        return "N/A - HOA missing"
    if hoa_fee == 0 and hoa_source != "ATTOM":
        return "N/A - HOA unconfirmed $0"  # RentCast zero untrusted until ATTOM confirms

    pitia = price * monthly_piti_factor() + DSCR_INSURANCE_MONTHLY + hoa_fee
    dscr = (rent * DSCR_RENT_HAIRCUT) / pitia

    if dscr >= DSCR_PASS_THRESHOLD:
        return "PASS"
    if dscr >= DSCR_MARGINAL_THRESHOLD:
        return "MARGINAL"
    return "FAIL"


def investor_flag(prop: dict, profile: InvestorProfile = DEFAULT_PROFILE) -> dict:
    list_price = prop.get("list_price") or 0
    bedrooms = prop.get("bedrooms") or 0
    property_type = (prop.get("property_type") or "").strip().lower()

    down_payment_est = list_price * profile.down_payment_pct
    down_payment_feasible = down_payment_est <= profile.down_payment_ceiling

    if list_price <= profile.in_range_max_price:
        target_price_range = "In range"
    elif list_price <= profile.stretch_max_price:
        target_price_range = "Above range"
    else:
        target_price_range = "Out of range"

    boarder_strategy_viable = (property_type in profile.boarder_viable_types
                               and bedrooms >= profile.boarder_min_bedrooms)

    in_range = target_price_range == "In range"
    failures = sum([not down_payment_feasible, not in_range, not boarder_strategy_viable])

    if failures == 0:
        flag = "STRONG"
    elif failures == 1 and down_payment_feasible and boarder_strategy_viable:
        flag = "POSSIBLE"
    elif failures == 1:
        flag = "REVIEW"
    else:
        flag = "SKIP"

    return {
        "down_payment_est": down_payment_est,
        "down_payment_feasible": down_payment_feasible,
        "target_price_range": target_price_range,
        "boarder_strategy_viable": boarder_strategy_viable,
        "investor_flag": flag,
    }
