from dataclasses import dataclass, field
from enum import Enum


class FinancingStrategy(str, Enum):
    OWNER_OCC_CONVENTIONAL = "owner_occ_conventional"
    FHA_MULTIUNIT          = "fha_multiunit"
    DSCR                   = "dscr"
    ADU_INCOME             = "adu_income"


@dataclass
class IncomeSource:
    type: str
    monthly_amount: float
    lender_treatment_pct: float = 1.0


def _credit_tier(score: int | None) -> str:
    if score is None:
        return "unknown"
    if score >= 760:
        return "excellent"
    if score >= 720:
        return "strong"
    if score >= 680:
        return "good"
    if score >= 640:
        return "fair"
    return "needs_work"


@dataclass
class InvestorProfile:
    down_payment_ceiling: float = 50_000
    down_payment_pct: float = 0.05
    cash_reserves: float = 0.0
    closing_cost_est: float = 8_000

    income_sources: list[IncomeSource] = field(default_factory=list)
    monthly_debt_obligations: float = 0.0
    credit_score: int | None = None
    max_dti: float = 0.45

    primary_strategy: FinancingStrategy = FinancingStrategy.OWNER_OCC_CONVENTIONAL
    eligible_products: list[FinancingStrategy] = field(default_factory=lambda: [FinancingStrategy.OWNER_OCC_CONVENTIONAL])
    occupancy_intent: str = "owner_occ"
    first_time_buyer: bool = False

    target_markets: list[str] = field(default_factory=list)
    in_range_max_price: float = 250_000
    stretch_max_price: float = 400_000
    property_types: frozenset = frozenset({"single family", "condo", "townhouse"})
    min_bedrooms: int = 2
    min_bathrooms: float = 1.0

    boarder_strategy: bool = True
    adu_interest: bool = False
    ltr_intent: bool = True
    str_intent: bool = False

    min_dscr: float = 1.10
    marginal_dscr: float = 0.90
    min_cap_rate: float | None = None
    min_coc: float | None = None
    max_monthly_negative_cashflow: float = 0.0

    dscr_rate: float = 0.0725
    dscr_term_months: int = 360
    dscr_ltv: float = 0.80
    dscr_tax_rate_annual: float = 0.0080
    dscr_insurance_monthly: float = 75.0
    dscr_rent_haircut: float = 0.75

    @property
    def credit_tier(self) -> str:
        return _credit_tier(self.credit_score)

    @property
    def total_monthly_income(self) -> float:
        return sum(s.monthly_amount * s.lender_treatment_pct for s in self.income_sources)

    def monthly_piti_factor(self) -> float:
        r = self.dscr_rate / 12
        n = self.dscr_term_months
        pmt_per_loan_dollar = r * (1 + r) ** n / ((1 + r) ** n - 1)
        return pmt_per_loan_dollar * self.dscr_ltv + self.dscr_tax_rate_annual / 12


DEFAULT_PROFILE = InvestorProfile()
