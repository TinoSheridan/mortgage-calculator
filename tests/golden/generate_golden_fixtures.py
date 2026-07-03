"""Generate golden regression fixtures for the mortgage calculator.

Run from the repo root:  python tests/golden/generate_golden_fixtures.py

Freezes time so refinance scenarios (which call date.today()) are deterministic.
Only regenerate fixtures when a calculation change is INTENTIONAL — the whole
point of these fixtures is to catch unintentional changes.
"""

import json
import os
import sys
from datetime import date

from freezegun import freeze_time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

FROZEN_TODAY = "2026-07-01"

PURCHASE_SCENARIOS = {
    "purchase_conventional_20down": dict(
        purchase_price=450000,
        down_payment_percentage=20,
        annual_rate=6.5,
        loan_term=30,
        annual_tax_rate=1.0,
        annual_insurance_rate=0.35,
        loan_type="conventional",
        closing_date=date(2026, 9, 15),
    ),
    "purchase_conventional_5down_pmi": dict(
        purchase_price=350000,
        down_payment_percentage=5,
        annual_rate=6.75,
        loan_term=30,
        annual_tax_rate=1.0,
        annual_insurance_rate=0.35,
        loan_type="conventional",
        closing_date=date(2026, 9, 15),
    ),
    "purchase_conventional_3down_credits": dict(
        purchase_price=300000,
        down_payment_percentage=3,
        annual_rate=7.0,
        loan_term=30,
        annual_tax_rate=1.0,
        annual_insurance_rate=0.35,
        loan_type="conventional",
        seller_credit=5000,
        lender_credit=1000,
        closing_date=date(2026, 9, 15),
    ),
    "purchase_fha_min_down": dict(
        purchase_price=320000,
        down_payment_percentage=3.5,
        annual_rate=6.25,
        loan_term=30,
        annual_tax_rate=1.0,
        annual_insurance_rate=0.35,
        loan_type="fha",
        closing_date=date(2026, 9, 15),
    ),
    "purchase_fha_5down_low_ltv_mip": dict(
        purchase_price=320000,
        down_payment_percentage=5,
        annual_rate=6.25,
        loan_term=30,
        annual_tax_rate=1.0,
        annual_insurance_rate=0.35,
        loan_type="fha",
        closing_date=date(2026, 9, 15),
    ),
    "purchase_va_active_first_0down": dict(
        purchase_price=400000,
        down_payment_percentage=0,
        annual_rate=6.0,
        loan_term=30,
        annual_tax_rate=1.0,
        annual_insurance_rate=0.35,
        loan_type="va",
        va_service_type="active",
        va_usage="first",
        va_disability_exempt=False,
        closing_date=date(2026, 9, 15),
    ),
    "purchase_va_reserves_subsequent_5down": dict(
        purchase_price=380000,
        down_payment_percentage=5,
        annual_rate=6.125,
        loan_term=30,
        annual_tax_rate=1.0,
        annual_insurance_rate=0.35,
        loan_type="va",
        va_service_type="reserves",
        va_usage="subsequent",
        va_disability_exempt=False,
        closing_date=date(2026, 9, 15),
    ),
    "purchase_va_disability_exempt": dict(
        purchase_price=400000,
        down_payment_percentage=0,
        annual_rate=6.0,
        loan_term=30,
        annual_tax_rate=1.0,
        annual_insurance_rate=0.35,
        loan_type="va",
        va_service_type="active",
        va_usage="first",
        va_disability_exempt=True,
        closing_date=date(2026, 9, 15),
    ),
    "purchase_usda_0down": dict(
        purchase_price=280000,
        down_payment_percentage=0,
        annual_rate=6.375,
        loan_term=30,
        annual_tax_rate=1.0,
        annual_insurance_rate=0.35,
        loan_type="usda",
        closing_date=date(2026, 9, 15),
    ),
    "purchase_conventional_15yr_points": dict(
        purchase_price=500000,
        down_payment_percentage=25,
        annual_rate=5.875,
        loan_term=15,
        annual_tax_rate=1.0,
        annual_insurance_rate=0.35,
        loan_type="conventional",
        discount_points=1.0,
        closing_date=date(2026, 9, 15),
    ),
    "purchase_conv_actual_amounts_no_owners_title": dict(
        purchase_price=450000,
        down_payment_percentage=20,
        annual_rate=6.5,
        loan_term=30,
        loan_type="conventional",
        include_owners_title=False,
        tax_method="amount",
        annual_tax_amount=4200.0,
        insurance_method="amount",
        annual_insurance_amount=1800.0,
        closing_date=date(2026, 9, 15),
    ),
}

REFINANCE_SCENARIOS = {
    "refi_conventional_rate_term": dict(
        appraised_value=500000,
        original_loan_balance=400000,
        original_interest_rate=7.5,
        original_loan_term=30,
        original_closing_date="2023-06-01",
        new_interest_rate=6.25,
        new_loan_term=30,
        new_closing_date="2026-08-15",
        annual_taxes=4800.0,
        annual_insurance=1900.0,
        use_manual_balance=True,
        manual_current_balance=385000.0,
        loan_type="conventional",
        refinance_type="rate_term",
    ),
    "refi_conventional_cash_out": dict(
        appraised_value=550000,
        original_loan_balance=300000,
        original_interest_rate=6.5,
        original_loan_term=30,
        original_closing_date="2020-03-01",
        new_interest_rate=6.75,
        new_loan_term=30,
        new_closing_date="2026-08-15",
        annual_taxes=5200.0,
        annual_insurance=2100.0,
        use_manual_balance=True,
        manual_current_balance=270000.0,
        loan_type="conventional",
        refinance_type="cash_out",
        cash_option="cash_back",
        cash_back_amount=40000.0,
    ),
    "refi_fha_streamline": dict(
        appraised_value=400000,
        original_loan_balance=350000,
        original_interest_rate=7.0,
        original_loan_term=30,
        original_closing_date="2024-01-01",
        new_interest_rate=6.0,
        new_loan_term=30,
        new_closing_date="2026-08-15",
        annual_taxes=3800.0,
        annual_insurance=1600.0,
        use_manual_balance=True,
        manual_current_balance=340000.0,
        loan_type="fha",
        refinance_type="streamline",
    ),
    "refi_va_irrrl": dict(
        appraised_value=450000,
        original_loan_balance=380000,
        original_interest_rate=6.875,
        original_loan_term=30,
        original_closing_date="2023-10-01",
        new_interest_rate=5.99,
        new_loan_term=30,
        new_closing_date="2026-08-15",
        annual_taxes=4300.0,
        annual_insurance=1750.0,
        use_manual_balance=True,
        manual_current_balance=368000.0,
        loan_type="va",
        refinance_type="streamline",
    ),
}


def _serialize_inputs(params):
    out = {}
    for k, v in params.items():
        out[k] = v.isoformat() if isinstance(v, date) else v
    return out


def main():
    """Run every scenario and write the fixture file next to this script."""
    with freeze_time(FROZEN_TODAY):
        from calculator import MortgageCalculator

        calc = MortgageCalculator()
        fixtures = {
            "_meta": {
                "frozen_today": FROZEN_TODAY,
                "note": "Golden regression fixtures. Regenerate ONLY for intentional calculation changes.",
            }
        }

        for name, params in PURCHASE_SCENARIOS.items():
            result = calc.calculate_all(**params)
            fixtures[name] = {
                "kind": "purchase",
                "inputs": _serialize_inputs(params),
                "expected": json.loads(json.dumps(result, default=str)),
            }
            print(
                f"{name}: monthly={result['monthly_breakdown']['total']} cash={result['total_cash_needed']}"
            )

        for name, params in REFINANCE_SCENARIOS.items():
            result = calc.calculate_refinance(**params)
            fixtures[name] = {
                "kind": "refinance",
                "inputs": _serialize_inputs(params),
                "expected": json.loads(json.dumps(result, default=str)),
            }
            print(f"{name}: ok")

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "golden_scenarios.json")
    with open(out_path, "w") as f:
        json.dump(fixtures, f, indent=2, sort_keys=True)
    print(f"\nWrote {len(fixtures) - 1} scenarios to {out_path}")


if __name__ == "__main__":
    main()
