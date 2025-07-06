from typing import Any, Dict

from calculator import MortgageCalculator


def calculate_and_print(calc: MortgageCalculator, params: Dict[str, Any], scenario_name: str):
    """Calculate and print mortgage details for a given scenario."""
    print(f"\n=== {scenario_name} ===")
    try:
        result = calc.calculate_all(**params)

        print(f"\nLoan Details:")
        print(f"Purchase Price: ${result['loan_details']['purchase_price']:,.2f}")
        print(f"Down Payment: ${result['loan_details']['down_payment']:,.2f}")
        print(
            f"Base Loan Amount: ${result['loan_details']['purchase_price'] - result['loan_details']['down_payment']:,.2f}"
        )

        # FHA loans include upfront MIP in the total loan amount
        if params.get("loan_type", "conventional").lower() == "fha":
            print(
                f"Upfront MIP: ${result['loan_details']['loan_amount'] - (result['loan_details']['purchase_price'] - result['loan_details']['down_payment']):,.2f}"
            )

        print(f"Total Loan Amount: ${result['loan_details']['loan_amount']:,.2f}")
        print(f"Interest Rate: {result['loan_details']['annual_rate']}%")
        print(f"Loan Term: {result['loan_details']['loan_term']} years")
        print(f"LTV: {result['loan_details']['ltv']}%")

        print(f"\nMonthly Payments:")
        print(f"Principal & Interest: ${result['monthly_payment']['principal_and_interest']:,.2f}")
        print(f"Property Tax: ${result['monthly_payment']['property_tax']:,.2f}")
        print(f"Insurance: ${result['monthly_payment']['home_insurance']:,.2f}")
        print(f"Mortgage Insurance: ${result['monthly_payment']['mortgage_insurance']:,.2f}")
        print(f"HOA: ${result['monthly_payment']['hoa_fee']:,.2f}")
        print(f"Total Monthly Payment: ${result['monthly_payment']['total']:,.2f}")

        print("\nClosing Costs and Cash Required:")
        print(f"Total Closing Costs: ${result['closing_costs']['total']:,.2f}")
        print(f"Total Prepaid Items: ${result['prepaid_items']['total']:,.2f}")
        print(f"Total Credits: ${result['credits']['total']:,.2f}")
        print(f"Total Cash Needed: ${result['total_cash_needed']:,.2f}")

        print("\nCalculation successful!")
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


def test_mortgage_scenarios():
    # Initialize calculator
    calc = MortgageCalculator()

    # Scenario 1: Conventional loan with 20% down
    conventional_20_down = {
        "purchase_price": 400000,  # $400,000 home
        "down_payment": 80000,  # 20% down
        "annual_rate": 6.5,  # 6.5% rate
        "loan_term": 30,  # 30-year
        "annual_tax_rate": 1.2,  # 1.2% tax
        "annual_insurance_rate": 0.5,  # 0.5% insurance
        "credit_score": 750,  # Good credit
        "loan_type": "conventional",
        "hoa_fee": 200,
        "seller_credit": 0,
        "lender_credit": 0,
        "discount_points": 0,
    }
    calculate_and_print(calc, conventional_20_down, "Conventional Loan - 20% Down")

    # Scenario 2: FHA loan with 3.5% down
    fha_min_down = {
        "purchase_price": 350000,  # $350,000 home
        "down_payment": 12250,  # 3.5% down
        "annual_rate": 7.0,  # 7.0% rate
        "loan_term": 30,  # 30-year
        "annual_tax_rate": 1.2,  # 1.2% tax
        "annual_insurance_rate": 0.5,  # 0.5% insurance
        "credit_score": 680,  # Fair credit
        "loan_type": "fha",
        "hoa_fee": 0,
        "seller_credit": 5000,  # $5,000 seller credit
        "lender_credit": 0,
        "discount_points": 0,
    }
    calculate_and_print(calc, fha_min_down, "FHA Loan - 3.5% Down")

    # Scenario 3: Conventional loan with 10% down and points
    conventional_points = {
        "purchase_price": 500000,  # $500,000 home
        "down_payment": 50000,  # 10% down
        "annual_rate": 6.0,  # 6.0% rate (lower due to points)
        "loan_term": 30,  # 30-year
        "annual_tax_rate": 1.2,  # 1.2% tax
        "annual_insurance_rate": 0.5,  # 0.5% insurance
        "credit_score": 720,  # Good credit
        "loan_type": "conventional",
        "hoa_fee": 300,
        "seller_credit": 0,
        "lender_credit": 2500,  # $2,500 lender credit
        "discount_points": 2.0,  # 2 points to lower rate
    }
    calculate_and_print(calc, conventional_points, "Conventional Loan - 10% Down with Points")

    # Scenario 4: Test validation - Should fail (purchase price too low)
    invalid_price = {
        "purchase_price": 40000,  # Too low
        "down_payment": 8000,
        "annual_rate": 6.5,
        "loan_term": 30,
        "annual_tax_rate": 1.2,
        "annual_insurance_rate": 0.5,
        "credit_score": 750,
        "loan_type": "conventional",
        "hoa_fee": 0,
        "seller_credit": 0,
        "lender_credit": 0,
        "discount_points": 0,
    }
    calculate_and_print(calc, invalid_price, "Invalid Scenario - Low Purchase Price")

    # Scenario 5: 15-year conventional with 25% down
    fifteen_year = {
        "purchase_price": 450000,  # $450,000 home
        "down_payment": 112500,  # 25% down
        "annual_rate": 5.75,  # 5.75% rate
        "loan_term": 15,  # 15-year
        "annual_tax_rate": 1.2,  # 1.2% tax
        "annual_insurance_rate": 0.5,  # 0.5% insurance
        "credit_score": 780,  # Excellent credit
        "loan_type": "conventional",
        "hoa_fee": 150,
        "seller_credit": 2500,
        "lender_credit": 1500,
        "discount_points": 0,
    }
    calculate_and_print(calc, fifteen_year, "15-Year Conventional - 25% Down")


if __name__ == "__main__":
    test_mortgage_scenarios()
