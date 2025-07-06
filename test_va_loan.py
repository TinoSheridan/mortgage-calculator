#!/usr/bin/env python
"""
Test script for VA loan parameters
This script tests the VA loan parameter handling in the MortgageCalculator class.
"""
import json
import logging

from calculator import MortgageCalculator

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_va_loan_parameters():
    """Test VA loan parameter handling with different scenarios."""
    logger.info("Starting VA loan parameter test")

    # Test scenarios
    scenarios = [
        {
            "name": "VA loan - active duty, first use, 10% down",
            "params": {
                "purchase_price": 400000,
                "down_payment": 40000,  # 10%
                "annual_rate": 5.5,
                "loan_term": 30,
                "annual_tax_rate": 1.2,
                "annual_insurance_rate": 0.5,
                "credit_score": 720,
                "loan_type": "va",
                "va_service_type": "active",
                "va_usage": "first",
                "va_disability_exempt": False,
            },
        },
        {
            "name": "VA loan - reserves, subsequent use, 5% down",
            "params": {
                "purchase_price": 350000,
                "down_payment": 17500,  # 5%
                "annual_rate": 6.0,
                "loan_term": 30,
                "annual_tax_rate": 1.2,
                "annual_insurance_rate": 0.5,
                "credit_score": 700,
                "loan_type": "va",
                "va_service_type": "reserves",
                "va_usage": "subsequent",
                "va_disability_exempt": False,
            },
        },
        {
            "name": "VA loan - disability exempt",
            "params": {
                "purchase_price": 500000,
                "down_payment": 25000,  # 5%
                "annual_rate": 5.75,
                "loan_term": 30,
                "annual_tax_rate": 1.2,
                "annual_insurance_rate": 0.5,
                "credit_score": 750,
                "loan_type": "va",
                "va_service_type": "active",
                "va_usage": "first",
                "va_disability_exempt": True,
            },
        },
    ]

    calculator = MortgageCalculator()

    for scenario in scenarios:
        logger.info(f"Testing: {scenario['name']}")
        try:
            # Extract parameters
            params = scenario["params"]

            # Calculate
            result = calculator.calculate_all(
                purchase_price=params["purchase_price"],
                down_payment=params["down_payment"],
                annual_rate=params["annual_rate"],
                loan_term=params["loan_term"],
                annual_tax_rate=params["annual_tax_rate"],
                annual_insurance_rate=params["annual_insurance_rate"],
                credit_score=params["credit_score"],
                loan_type=params["loan_type"],
                va_service_type=params.get("va_service_type"),
                va_usage=params.get("va_usage"),
                va_disability_exempt=params.get("va_disability_exempt", False),
            )

            # Check for mortgage_insurance key
            monthly_payment = result.get("monthly_payment", {})
            if "mortgage_insurance" not in monthly_payment:
                logger.error("Key 'mortgage_insurance' missing from monthly payment")
            else:
                logger.info(f"Mortgage insurance amount: ${monthly_payment['mortgage_insurance']}")

            # Check funding fee if applicable
            loan_details = result.get("loan_details", {})
            if "funding_fee" in loan_details:
                logger.info(f"VA funding fee: ${loan_details['funding_fee']}")

            # Print summary
            logger.info(
                f"Test result: "
                f"Loan amount=${loan_details.get('loan_amount', 0):,.2f}, "
                f"Monthly payment=${monthly_payment.get('total', 0):,.2f}"
            )

            print(f"\n--- {scenario['name']} ---")
            print(f"Purchase price: ${params['purchase_price']:,.2f}")
            print(
                f"Down payment: ${params['down_payment']:,.2f} ({params['down_payment']/params['purchase_price']*100:.1f}%)"
            )
            print(f"VA service type: {params.get('va_service_type', 'N/A')}")
            print(f"VA usage: {params.get('va_usage', 'N/A')}")
            print(f"Disability exempt: {params.get('va_disability_exempt', False)}")
            print(f"Base loan amount: ${loan_details.get('base_loan_amount', 0):,.2f}")
            print(f"VA funding fee: ${loan_details.get('funding_fee', 0):,.2f}")
            print(f"Final loan amount: ${loan_details.get('loan_amount', 0):,.2f}")
            print(f"Monthly payment: ${monthly_payment.get('total', 0):,.2f}")
            print(f"Mortgage insurance: ${monthly_payment.get('mortgage_insurance', 0):,.2f}")

        except Exception as e:
            logger.error(f"Test failed: {e}")
            print(f"\n--- {scenario['name']} ---")
            print(f"ERROR: {e}")


if __name__ == "__main__":
    test_va_loan_parameters()
