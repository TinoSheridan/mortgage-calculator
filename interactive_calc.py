from typing import Any, Dict

from calculator import MortgageCalculator


def get_float_input(prompt: str, default: float) -> float:
    """Get float input with default value."""
    try:
        value = input(f"{prompt} [{default}]: ")
        return float(value) if value.strip() else default
    except ValueError:
        return default


def get_int_input(prompt: str, default: int) -> int:
    """Get integer input with default value."""
    try:
        value = input(f"{prompt} [{default}]: ")
        return int(value) if value.strip() else default
    except ValueError:
        return default


def get_str_input(prompt: str, default: str) -> str:
    """Get string input with default value."""
    value = input(f"{prompt} [{default}]: ")
    return value.strip() if value.strip() else default


def interactive_calculator():
    calc = MortgageCalculator()

    while True:
        print("\n=== Interactive Mortgage Calculator ===")
        print("Press Enter to use default values, or enter new values.")

        # Get loan parameters with defaults
        params = {
            "purchase_price": get_float_input("Purchase Price ($)", 400000),
            "down_payment": get_float_input("Down Payment ($)", 80000),
            "annual_rate": get_float_input("Annual Interest Rate (%)", 6.5),
            "loan_term": get_int_input("Loan Term (years)", 30),
            "annual_tax_rate": get_float_input("Annual Property Tax Rate (%)", 1.2),
            "annual_insurance_rate": get_float_input("Annual Insurance Rate (%)", 0.5),
            "credit_score": get_int_input("Credit Score", 750),
            "loan_type": get_str_input(
                "Loan Type (conventional/fha/va/usda)", "conventional"
            ),
            "hoa_fee": get_float_input("Monthly HOA Fee ($)", 0),
            "seller_credit": get_float_input("Seller Credit ($)", 0),
            "lender_credit": get_float_input("Lender Credit ($)", 0),
            "discount_points": get_float_input("Discount Points", 0),
        }

        # Get VA-specific parameters if loan type is VA
        if params["loan_type"].lower() == "va":
            print("\n=== VA Loan Parameters ===")
            va_service_type = get_str_input(
                "Service Type (active/reserves)", "active"
            ).lower()
            va_usage = get_str_input("Loan Usage (first/subsequent)", "first").lower()

            # Get disability exempt status (yes/no)
            disability_exempt_input = get_str_input(
                "Disability Exempt (yes/no)", "no"
            ).lower()
            va_disability_exempt = (
                True if disability_exempt_input in ("yes", "y", "true") else False
            )

            # Add VA parameters to the params dictionary
            params["va_service_type"] = va_service_type
            params["va_usage"] = va_usage
            params["va_disability_exempt"] = va_disability_exempt

            print(
                f"\nVA Loan Parameters: Service Type={va_service_type}, Usage={va_usage}, Disability Exempt={va_disability_exempt}"
            )

        try:
            # Calculate and display results
            result = calc.calculate_all(**params)

            print("\n=== Results ===")
            print(f"\nLoan Details:")
            print(f"Purchase Price: ${result['loan_details']['purchase_price']:,.2f}")
            print(f"Down Payment: ${result['loan_details']['down_payment']:,.2f}")
            print(
                f"Base Loan Amount: ${result['loan_details']['purchase_price'] - result['loan_details']['down_payment']:,.2f}"
            )

            # FHA loans include upfront MIP in the total loan amount
            if params["loan_type"].lower() == "fha":
                print(
                    f"Upfront MIP: ${result['loan_details']['loan_amount'] - (result['loan_details']['purchase_price'] - result['loan_details']['down_payment']):,.2f}"
                )

            print(f"Total Loan Amount: ${result['loan_details']['loan_amount']:,.2f}")
            print(f"Interest Rate: {result['loan_details']['annual_rate']}%")
            print(f"Loan Term: {result['loan_details']['loan_term']} years")
            print(f"LTV: {result['loan_details']['ltv']}%")

            print(f"\nMonthly Payments:")
            print(
                f"Principal & Interest: ${result['monthly_payment']['principal_and_interest']:,.2f}"
            )
            print(f"Property Tax: ${result['monthly_payment']['property_tax']:,.2f}")
            print(f"Insurance: ${result['monthly_payment']['home_insurance']:,.2f}")
            print(
                f"Mortgage Insurance: ${result['monthly_payment']['mortgage_insurance']:,.2f}"
            )
            print(f"HOA: ${result['monthly_payment']['hoa_fee']:,.2f}")
            print(f"Total Monthly Payment: ${result['monthly_payment']['total']:,.2f}")

            print(f"\nCash Required:")
            print(f"Closing Costs: ${result['closing_costs']['total']:,.2f}")
            print(f"Prepaid Items: ${result['prepaid_items']['total']:,.2f}")
            print(f"Credits: ${result['credits']['total']:,.2f}")
            print(f"Total Cash Needed: ${result['total_cash_needed']:,.2f}")

            # VA loans show funding fee information
            if (
                params["loan_type"].lower() == "va"
                and "funding_fee" in result["loan_details"]
            ):
                print(f"VA Funding Fee: ${result['loan_details']['funding_fee']:,.2f}")

        except Exception as e:
            print(f"\nError: {str(e)}")

        # Ask to continue
        again = input("\nCalculate another? (y/n) [y]: ").lower()
        if again == "n":
            break


if __name__ == "__main__":
    interactive_calculator()
