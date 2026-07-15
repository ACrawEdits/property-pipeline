import os

from dataclasses import dataclass

# --- DSCR pre-screen assumptions (edit as rates move) ---
DSCR_RATE               = 0.0725   # 30yr fixed assumption
DSCR_TERM_MONTHS        = 360
DSCR_LTV                = 0.80     # 20% down
DSCR_TAX_RATE_ANNUAL    = 0.0080   # Loudoun approx; becomes a per-county table later
DSCR_INSURANCE_MONTHLY  = 75.0
DSCR_RENT_HAIRCUT       = 0.75     # conventional-style haircut, not DSCR-lender math
DSCR_PASS_THRESHOLD     = 1.10
DSCR_MARGINAL_THRESHOLD = 0.90


def monthly_piti_factor(rate=DSCR_RATE, term_months=DSCR_TERM_MONTHS,
                        ltv=DSCR_LTV, tax_rate_annual=DSCR_TAX_RATE_ANNUAL) -> float:
    """Monthly P&I + taxes per dollar of list price. Insurance and HOA added separately."""
    r = rate / 12
    pmt_per_loan_dollar = r * (1 + r) ** term_months / ((1 + r) ** term_months - 1)
    return pmt_per_loan_dollar * ltv + tax_rate_annual / 12


@dataclass
class InvestorProfile:
    down_payment_pct: float = 0.05
    down_payment_ceiling: float = 50_000
    in_range_max_price: float = 250_000
    stretch_max_price: float = 400_000
    boarder_min_bedrooms: int = 2
    boarder_viable_types: frozenset = frozenset({"single family", "condo", "townhouse"})

DEFAULT_PROFILE = InvestorProfile()

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
    "down_payment_est",
    "down_payment_feasible",
    "target_price_range",
    "boarder_strategy_viable",
    "investor_flag",
]

# Columns that represent hardcoded user inputs (styled blue in Excel)
INPUT_COLUMNS = {"list_price", "hoa_fee"}

SOURCE_WORKBOOK = "MODELS/CHSSNotCheckersRealty v3.xlsx"
OUTPUT_WORKBOOK = "MODELS/CHSSNotCheckersRealty v4.xlsx"
