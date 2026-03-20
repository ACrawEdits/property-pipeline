import os

RENTCAST_API_KEY = os.environ.get("RENTCAST_API_KEY", "")
RENTCAST_BASE_URL = "https://api.rentcast.io/v1"

HEADERS = {
    "Accept": "application/json",
    "X-Api-Key": RENTCAST_API_KEY,
}

DEFAULT_LIMIT = 100
PAGE_SIZE = 500  # RentCast max per page

# Ordered field schema shared by normalize.py and writer.py
FIELDS = [
    "address",
    "city",
    "state",
    "zip",
    "county",
    "property_type",
    "bedrooms",
    "bathrooms",
    "sqft",
    "year_built",
    "list_price",
    "rent_estimate",
    "rent_estimate_low",
    "rent_estimate_high",
    "hoa_fee",
    "hoa_source",
    "days_on_market",
    "latitude",
    "longitude",
    "source",
    "fetched_at",
    "dscr_flag",
]

# Columns that represent hardcoded user inputs (styled blue in Excel)
INPUT_COLUMNS = {"list_price", "hoa_fee"}

SOURCE_WORKBOOK = "MODELS/CHSSNotCheckersRealty v3.xlsx"
OUTPUT_WORKBOOK = "MODELS/CHSSNotCheckersRealty v4.xlsx"
