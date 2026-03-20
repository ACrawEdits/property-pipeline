from dataclasses import dataclass


@dataclass
class GeoContext:
    api_params: dict
    local_county_filter: str | None
    label: str


def resolve_geo(
    zipcode: str | None = None,
    city: str | None = None,
    state: str | None = None,
    county: str | None = None,
) -> GeoContext:
    zipcode = zipcode.strip() if zipcode else None
    city = city.strip() if city else None
    state = state.strip().upper() if state else None
    county = county.strip() if county else None

    if not any([zipcode, city, state, county]):
        raise ValueError(
            "At least one of --zip, --city, --state, or --county must be provided."
        )

    if zipcode:
        return GeoContext(
            api_params={"zipCode": zipcode},
            local_county_filter=None,
            label=zipcode,
        )

    if city and state:
        return GeoContext(
            api_params={"city": city, "state": state},
            local_county_filter=None,
            label=f"{city}, {state}",
        )

    if county and state:
        # RentCast doesn't filter by county — pull full state, filter locally
        return GeoContext(
            api_params={"state": state},
            local_county_filter=county,
            label=f"{county} County, {state}",
        )

    if state:
        return GeoContext(
            api_params={"state": state},
            local_county_filter=None,
            label=state,
        )

    # county without state
    raise ValueError(
        "--county requires --state to narrow the API query. "
        "Provide both or use --zip / --city+state instead."
    )
