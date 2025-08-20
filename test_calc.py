#!/usr/bin/env python3
"""
Quick test script to verify the calculation logic works without CSRF
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from calculator import MortgageCalculator

def test_calculation():
    """Test a basic mortgage calculation"""
    try:
        calc = MortgageCalculator()
        
        result = calc.calculate_all(
            purchase_price=400000,
            down_payment_percentage=20,
            annual_rate=6.5,
            loan_term=30,
            loan_type="conventional",
            annual_tax_rate=1.0,
            annual_insurance_rate=0.35,
            monthly_hoa_fee=0,
            seller_credit=0,
            lender_credit=0,
            discount_points=0
        )
        
        print("✅ Calculation successful!")
        print(f"Monthly payment: ${result['monthly_breakdown']['total']:,.2f}")
        print(f"Loan amount: ${result['loan_details']['loan_amount']:,.2f}")
        print(f"Down payment: ${result['loan_details']['down_payment']:,.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Calculation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_calculation()
    sys.exit(0 if success else 1)