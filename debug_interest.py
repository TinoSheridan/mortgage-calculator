#!/usr/bin/env python3
"""
Debug script to test prepaid interest calculation
"""
from datetime import datetime, date
from calendar import monthrange
from calculator import MortgageCalculator

def main():
    # Setup test parameters
    loan_amount = 300000
    annual_rate = 5.0
    closing_date_str = "2025-03-10"
    
    # Parse closing date
    closing_date = datetime.strptime(closing_date_str, '%Y-%m-%d').date()
    print(f"Closing date: {closing_date}")
    
    # Calculate daily interest
    daily_interest = (loan_amount * annual_rate / 100) / 360
    print(f"Daily interest: ${daily_interest:.2f}")
    
    # Calculate days to end of month
    _, last_day = monthrange(closing_date.year, closing_date.month)
    last_date = date(closing_date.year, closing_date.month, last_day)
    days = (last_date - closing_date).days + 1
    print(f"Days from {closing_date} to {last_date}: {days}")
    
    # Calculate expected prepaid interest
    expected_interest = daily_interest * days
    print(f"Expected prepaid interest: ${expected_interest:.2f}")
    
    # Use the calculator to compute prepaid interest
    calculator = MortgageCalculator()
    prepaid_items = calculator.calculate_prepaid_items(
        loan_amount=loan_amount,
        annual_tax_rate=1.0,  # Doesn't matter for interest calc
        annual_insurance_rate=0.5,  # Doesn't matter for interest calc
        annual_interest_rate=annual_rate,
        closing_date=closing_date
    )
    
    print(f"\nActual prepaid interest from calculator: ${prepaid_items['prepaid_interest']:.2f}")
    
    # Calculate difference
    difference = abs(prepaid_items['prepaid_interest'] - expected_interest)
    if difference < 0.01:
        print("\n✓ MATCHES: The calculated value matches the expected value!")
    else:
        print(f"\n✗ DOESN'T MATCH: There's a difference of ${difference:.2f}")
        
    # Print calculator config
    print("\nCalculator prepaid_items config:")
    print(calculator.config['prepaid_items'])

if __name__ == "__main__":
    main()
