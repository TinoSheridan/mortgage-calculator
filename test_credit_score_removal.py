#!/usr/bin/env python3
"""
Test script to verify that the credit score removal changes work correctly
"""

from calculator import MortgageCalculator

def test_mortgage_calculation():
    """Test mortgage calculation with credit score dependencies removed"""
    # Create a calculator instance
    calculator = MortgageCalculator()
    
    # Calculate mortgage details with various loan types
    test_scenarios = [
        {
            'name': 'Conventional Loan',
            'params': {
                'purchase_price': 400000,
                'down_payment': 80000,
                'annual_rate': 7.0,
                'loan_term': 30,
                'annual_tax_rate': 1.2,
                'annual_insurance_rate': 0.35,
                'loan_type': 'conventional'
            }
        },
        {
            'name': 'FHA Loan',
            'params': {
                'purchase_price': 350000,
                'down_payment': 12250, # 3.5%
                'annual_rate': 7.1,
                'loan_term': 30,
                'annual_tax_rate': 1.2,
                'annual_insurance_rate': 0.35,
                'loan_type': 'fha'
            }
        },
        {
            'name': 'VA Loan',
            'params': {
                'purchase_price': 380000,
                'down_payment': 0,
                'annual_rate': 6.8,
                'loan_term': 30,
                'annual_tax_rate': 1.2,
                'annual_insurance_rate': 0.35,
                'loan_type': 'va',
                'va_service_type': 'active',
                'va_usage': 'first',
                'va_disability_exempt': False
            }
        }
    ]
    
    # Run tests
    for scenario in test_scenarios:
        print(f"\n--- Testing {scenario['name']} ---")
        try:
            results = calculator.calculate_all(**scenario['params'])
            
            # Print key results
            print(f"Loan amount: ${results['loan_details']['loan_amount']:.2f}")
            print(f"Monthly P&I: ${results['monthly_payment']['principal_and_interest']:.2f}")
            print(f"Monthly PMI/MIP: ${results['monthly_payment']['mortgage_insurance']:.2f}")
            print(f"Total Monthly Payment: ${results['monthly_payment']['total']:.2f}")
            print("Test passed successfully!")
        except Exception as e:
            print(f"Error calculating mortgage: {e}")
            print("Test failed!")

if __name__ == "__main__":
    test_mortgage_calculation()
