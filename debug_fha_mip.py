from calculator import MortgageCalculator


def debug_fha_mip():
    """Debug FHA MIP calculation issues"""
    calc = MortgageCalculator()

    # Test parameters
    params = {
        "purchase_price": 400000,
        "down_payment": 60000,
        "annual_rate": 6.5,
        "loan_term": 30,
        "annual_tax_rate": 1.2,
        "annual_insurance_rate": 0.5,
        "credit_score": 750,
        "loan_type": "fha",
        "hoa_fee": 100,
    }

    # Calculate values manually
    base_loan = params["purchase_price"] - params["down_payment"]

    # Get MIP rates from config
    mip_rates = calc.config.get("pmi_rates", {}).get("fha", {})
    upfront_mip_rate = mip_rates.get("upfront_mip_rate", 1.75) / 100

    # Calculate upfront MIP
    upfront_mip = base_loan * upfront_mip_rate

    # Total loan amount (base + upfront MIP)
    total_loan = base_loan + upfront_mip

    # Get annual MIP rate for this loan
    annual_mip_rate = (
        mip_rates.get("annual_mip", {})
        .get("long_term", {})
        .get("standard_amount", {})
        .get("low_ltv", 0.5)
    )

    # Calculate monthly MIP
    monthly_mip = (total_loan * annual_mip_rate) / 12

    # Get result from calculator
    result = calc.calculate_all(**params)
    calc_monthly_mip = result["monthly_payment"]["mortgage_insurance"]

    # Print results
    print("=== FHA MIP Debug ===")
    print(f"Base loan amount: ${base_loan:,.2f}")
    print(f"Upfront MIP rate: {upfront_mip_rate*100:.2f}%")
    print(f"Upfront MIP: ${upfront_mip:,.2f}")
    print(f"Total loan amount: ${total_loan:,.2f}")
    print(f"Annual MIP rate: {annual_mip_rate*100:.2f}%")
    print(f"Monthly MIP (calculated manually): ${monthly_mip:,.2f}")
    print(f"Monthly MIP (from calculator): ${calc_monthly_mip:,.2f}")
    print(f"Difference: ${calc_monthly_mip - monthly_mip:,.2f}")

    # Check full result structure
    print("\nFull monthly payment structure:")
    for key, value in result["monthly_payment"].items():
        print(f"  {key}: ${value:,.2f}")


if __name__ == "__main__":
    debug_fha_mip()
