#!/usr/bin/env python3
"""
Test script to verify VA funding fee calculation with different parameters.
"""
from calculator import MortgageCalculator


def test_va_funding_fee():
    calculator = MortgageCalculator()

    # Test parameters - we'll test multiple combinations
    test_cases = [
        {
            "name": "Active Duty - First Use - 0% Down",
            "loan_amount": 300000,
            "down_payment_percentage": 0,
            "service_type": "active",
            "loan_usage": "first",
            "disability_exempt": False,
            "expected_rate": 2.3,  # 2.3%
        },
        {
            "name": "Active Duty - Subsequent Use - 0% Down",
            "loan_amount": 300000,
            "down_payment_percentage": 0,
            "service_type": "active",
            "loan_usage": "subsequent",
            "disability_exempt": False,
            "expected_rate": 3.6,  # 3.6%
        },
        {
            "name": "Reserves - First Use - 0% Down",
            "loan_amount": 300000,
            "down_payment_percentage": 0,
            "service_type": "reserves",
            "loan_usage": "first",
            "disability_exempt": False,
            "expected_rate": 2.3,  # 2.3%
        },
        {
            "name": "Reserves - Subsequent Use - 0% Down",
            "loan_amount": 300000,
            "down_payment_percentage": 0,
            "service_type": "reserves",
            "loan_usage": "subsequent",
            "disability_exempt": False,
            "expected_rate": 3.6,  # 3.6%
        },
        {
            "name": "Active Duty - First Use - 5% Down",
            "loan_amount": 300000,
            "down_payment_percentage": 5,
            "service_type": "active",
            "loan_usage": "first",
            "disability_exempt": False,
            "expected_rate": 1.65,  # 1.65%
        },
        {
            "name": "Active Duty - Subsequent Use - 5% Down",
            "loan_amount": 300000,
            "down_payment_percentage": 5,
            "service_type": "active",
            "loan_usage": "subsequent",
            "disability_exempt": False,
            "expected_rate": 1.65,  # 1.65%
        },
        {
            "name": "Disability Exempt",
            "loan_amount": 300000,
            "down_payment_percentage": 0,
            "service_type": "active",
            "loan_usage": "first",
            "disability_exempt": True,
            "expected_rate": 0.0,  # 0%
        },
    ]

    # Run test cases
    for case in test_cases:
        print(f"\n----- Testing: {case['name']} -----")

        funding_fee = calculator.calculate_va_funding_fee(
            loan_amount=case["loan_amount"],
            down_payment_percentage=case["down_payment_percentage"],
            service_type=case["service_type"],
            loan_usage=case["loan_usage"],
            disability_exempt=case["disability_exempt"],
        )

        expected_fee = (case["loan_amount"] * case["expected_rate"]) / 100

        print(
            f"Params: service={case['service_type']}, usage={case['loan_usage']}, down={case['down_payment_percentage']}%"
        )
        print(f"Expected rate: {case['expected_rate']}%")
        print(f"Expected fee: ${expected_fee:,.2f}")
        print(f"Actual fee: ${funding_fee:,.2f}")

        if abs(funding_fee - expected_fee) < 0.01:
            print("✅ PASS: Funding fee matches expected value")
        else:
            print(
                f"❌ FAIL: Funding fee does not match. Difference: ${abs(funding_fee - expected_fee):,.2f}"
            )

    print("\nTest complete!")


if __name__ == "__main__":
    test_va_funding_fee()
