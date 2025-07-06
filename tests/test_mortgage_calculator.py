"""
Comprehensive unit tests for the MortgageCalculator class.

These tests cover core financial calculations including:
- Monthly payment calculations
- LTV calculations
- PMI calculations  
- Closing costs
- Various loan types (Conventional, FHA, VA, USDA)
- Edge cases and error handling
"""

import pytest
import sys
import os
from decimal import Decimal
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the calculator
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculator import MortgageCalculator


class TestMortgageCalculatorBasics:
    """Test basic mortgage calculator functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calc = MortgageCalculator()
        self.standard_params = {
            'purchase_price': 300000,
            'down_payment_percentage': 20,
            'annual_rate': 5.5,
            'loan_term': 30,
            'annual_tax_rate': 1.2,
            'annual_insurance_rate': 0.8,
            'loan_type': 'conventional'
        }
    
    def test_basic_monthly_payment_calculation(self):
        """Test basic monthly payment calculation accuracy."""
        # Known calculation: $240K loan at 5.5% for 30 years = $1362.69
        loan_amount = 240000  # $300K - 20% down
        monthly_rate = 0.055 / 12
        num_payments = 30 * 12
        
        expected_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
        
        result = self.calc.calculate_all(**self.standard_params)
        
        # Allow for small rounding differences
        assert abs(result['monthly_breakdown']['principal_interest'] - expected_payment) < 1.0
        assert result['monthly_breakdown']['principal_interest'] == pytest.approx(1362.69, rel=0.01)
    
    def test_ltv_calculation(self):
        """Test LTV calculation accuracy."""
        result = self.calc.calculate_all(**self.standard_params)
        
        expected_ltv = 80.0  # 20% down = 80% LTV
        assert result['loan_details']['ltv_ratio'] == expected_ltv
    
    def test_down_payment_calculation(self):
        """Test down payment calculation."""
        result = self.calc.calculate_all(**self.standard_params)
        
        expected_down_payment = 300000 * 0.20
        assert result['loan_details']['down_payment'] == expected_down_payment
    
    def test_loan_amount_calculation(self):
        """Test loan amount calculation."""
        result = self.calc.calculate_all(**self.standard_params)
        
        expected_loan_amount = 300000 - (300000 * 0.20)  # Purchase price - down payment
        assert result['loan_details']['loan_amount'] == expected_loan_amount
    
    def test_property_tax_calculation(self):
        """Test monthly property tax calculation."""
        result = self.calc.calculate_all(**self.standard_params)
        
        expected_monthly_tax = (300000 * 0.012) / 12  # 1.2% annually / 12 months
        assert result['monthly_breakdown']['property_tax'] == expected_monthly_tax
    
    def test_insurance_calculation(self):
        """Test monthly insurance calculation."""
        result = self.calc.calculate_all(**self.standard_params)
        
        expected_monthly_insurance = (300000 * 0.008) / 12  # 0.8% annually / 12 months
        assert result['monthly_breakdown']['insurance'] == expected_monthly_insurance


class TestLoanTypes:
    """Test different loan types and their specific calculations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calc = MortgageCalculator()
        self.base_params = {
            'purchase_price': 300000,
            'down_payment_percentage': 10,  # Higher LTV to trigger PMI
            'annual_rate': 5.5,
            'loan_term': 30,
            'annual_tax_rate': 1.2,
            'annual_insurance_rate': 0.8,
        }
    
    def test_conventional_loan_with_pmi(self):
        """Test conventional loan PMI calculation when LTV > 80%."""
        params = {**self.base_params, 'loan_type': 'conventional'}
        result = self.calc.calculate_all(**params)
        
        # 10% down = 90% LTV, should have PMI
        assert result['loan_details']['ltv_ratio'] == 90.0
        assert result['monthly_breakdown']['pmi'] > 0
    
    def test_conventional_loan_no_pmi(self):
        """Test conventional loan without PMI when LTV <= 80%."""
        params = {**self.base_params, 'loan_type': 'conventional', 'down_payment_percentage': 20}
        result = self.calc.calculate_all(**params)
        
        # 20% down = 80% LTV, should not have PMI
        assert result['loan_details']['ltv_ratio'] == 80.0
        assert result['monthly_breakdown']['pmi'] == 0
    
    def test_fha_loan_mip_calculation(self):
        """Test FHA loan MIP calculation."""
        params = {**self.base_params, 'loan_type': 'fha'}
        result = self.calc.calculate_all(**params)
        
        # FHA loans have MIP regardless of LTV
        assert result['monthly_payment']['mortgage_insurance'] > 0
        
        # Should have upfront MIP added to loan amount
        base_loan = 300000 * 0.9  # 10% down
        assert result['loan_details']['loan_amount'] > base_loan
    
    def test_va_loan_no_mip(self):
        """Test VA loan has no mortgage insurance."""
        params = {
            **self.base_params, 
            'loan_type': 'va',
            'va_service_type': 'active',
            'va_usage': 'first',
            'va_disability_exempt': False
        }
        result = self.calc.calculate_all(**params)
        
        # VA loans don't have mortgage insurance
        assert result['monthly_payment']['mortgage_insurance'] == 0
    
    def test_usda_loan_guarantee_fee(self):
        """Test USDA loan guarantee fee calculation."""
        params = {**self.base_params, 'loan_type': 'usda'}
        result = self.calc.calculate_all(**params)
        
        # USDA loans have guarantee fees similar to FHA MIP
        assert result['monthly_payment']['mortgage_insurance'] > 0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calc = MortgageCalculator()
    
    def test_zero_down_payment(self):
        """Test calculation with zero down payment."""
        params = {
            'purchase_price': 300000,
            'down_payment_percentage': 0,
            'annual_rate': 5.5,
            'loan_term': 30,
            'annual_tax_rate': 1.2,
            'annual_insurance_rate': 0.8,
            'loan_type': 'va'  # VA allows 0% down
        }
        
        result = self.calc.calculate_all(**params)
        assert result['loan_details']['ltv'] == 100.0
        assert result['loan_details']['down_payment'] == 0
    
    def test_very_high_interest_rate(self):
        """Test calculation with high interest rate."""
        params = {
            'purchase_price': 300000,
            'down_payment_percentage': 20,
            'annual_rate': 15.0,  # High rate
            'loan_term': 30,
            'annual_tax_rate': 1.2,
            'annual_insurance_rate': 0.8,
            'loan_type': 'conventional'
        }
        
        result = self.calc.calculate_all(**params)
        # Should still calculate without error
        assert result['monthly_payment']['principal_and_interest'] > 0
        assert result['monthly_payment']['total'] > 0
    
    def test_short_loan_term(self):
        """Test calculation with short loan term."""
        params = {
            'purchase_price': 300000,
            'down_payment_percentage': 20,
            'annual_rate': 5.5,
            'loan_term': 15,  # 15-year loan
            'annual_tax_rate': 1.2,
            'annual_insurance_rate': 0.8,
            'loan_type': 'conventional'
        }
        
        result = self.calc.calculate_all(**params)
        # 15-year loan should have higher monthly payment but lower total interest
        assert result['monthly_payment']['principal_and_interest'] > 1703.26  # More than 30-year
    
    def test_invalid_loan_type(self):
        """Test error handling for invalid loan type."""
        params = {
            'purchase_price': 300000,
            'down_payment_percentage': 20,
            'annual_rate': 5.5,
            'loan_term': 30,
            'annual_tax_rate': 1.2,
            'annual_insurance_rate': 0.8,
            'loan_type': 'invalid_type'
        }
        
        # Should either handle gracefully or raise appropriate error
        try:
            result = self.calc.calculate_all(**params)
            # If no error, should default to conventional
            assert 'monthly_payment' in result
        except ValueError as e:
            # If error raised, should be descriptive
            assert 'loan_type' in str(e).lower()


class TestRefinanceCalculations:
    """Test refinance-specific calculations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calc = MortgageCalculator()
        self.refinance_params = {
            'purchase_price': 300000,  # Current home value
            'current_loan_balance': 200000,
            'annual_rate': 4.5,  # New rate
            'loan_term': 30,
            'annual_tax_rate': 1.2,
            'annual_insurance_rate': 0.8,
            'loan_type': 'conventional',
            'transaction_type': 'refinance'
        }
    
    def test_refinance_ltv_calculation(self):
        """Test LTV calculation for refinance."""
        result = self.calc.calculate_all(**self.refinance_params)
        
        # LTV should be based on current loan balance vs home value
        expected_ltv = (200000 / 300000) * 100
        assert result['loan_details']['ltv'] == pytest.approx(expected_ltv, rel=0.01)
    
    def test_refinance_over_80_ltv(self):
        """Test that refinance with LTV > 80% is allowed (previous bug)."""
        # This tests the fix for the critical bug where refinances were blocked
        high_ltv_params = {
            **self.refinance_params,
            'current_loan_balance': 250000  # 83.33% LTV
        }
        
        result = self.calc.calculate_all(**high_ltv_params)
        
        # Should not raise an error and should calculate PMI
        assert result['loan_details']['ltv'] > 80
        assert result['monthly_payment']['mortgage_insurance'] > 0
        assert 'error' not in result


class TestValidationAndSecurity:
    """Test input validation and security measures."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calc = MortgageCalculator()
    
    def test_negative_purchase_price(self):
        """Test handling of negative purchase price."""
        params = {
            'purchase_price': -100000,  # Invalid
            'down_payment_percentage': 20,
            'annual_rate': 5.5,
            'loan_term': 30,
            'annual_tax_rate': 1.2,
            'annual_insurance_rate': 0.8,
            'loan_type': 'conventional'
        }
        
        with pytest.raises(ValueError):
            self.calc.calculate_all(**params)
    
    def test_invalid_down_payment_percentage(self):
        """Test handling of invalid down payment percentage."""
        params = {
            'purchase_price': 300000,
            'down_payment_percentage': 150,  # Invalid - over 100%
            'annual_rate': 5.5,
            'loan_term': 30,
            'annual_tax_rate': 1.2,
            'annual_insurance_rate': 0.8,
            'loan_type': 'conventional'
        }
        
        with pytest.raises(ValueError):
            self.calc.calculate_all(**params)
    
    def test_zero_interest_rate(self):
        """Test handling of zero interest rate."""
        params = {
            'purchase_price': 300000,
            'down_payment_percentage': 20,
            'annual_rate': 0,  # Zero interest
            'loan_term': 30,
            'annual_tax_rate': 1.2,
            'annual_insurance_rate': 0.8,
            'loan_type': 'conventional'
        }
        
        result = self.calc.calculate_all(**params)
        # Should handle zero interest rate (payment = principal only)
        expected_payment = 240000 / (30 * 12)  # Principal only
        assert result['monthly_payment']['principal_and_interest'] == pytest.approx(expected_payment, rel=0.01)


class TestPrecisionAndAccuracy:
    """Test calculation precision and accuracy."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calc = MortgageCalculator()
    
    def test_decimal_precision(self):
        """Test that calculations maintain proper decimal precision."""
        params = {
            'purchase_price': 300000,
            'down_payment_percentage': 20,
            'annual_rate': 5.5,
            'loan_term': 30,
            'annual_tax_rate': 1.2,
            'annual_insurance_rate': 0.8,
            'loan_type': 'conventional'
        }
        
        result = self.calc.calculate_all(**params)
        
        # All monetary values should be rounded to 2 decimal places
        assert isinstance(result['monthly_payment']['principal_and_interest'], (int, float))
        assert round(result['monthly_payment']['principal_and_interest'], 2) == result['monthly_payment']['principal_and_interest']
    
    def test_consistent_results(self):
        """Test that identical inputs produce identical results."""
        params = {
            'purchase_price': 300000,
            'down_payment_percentage': 20,
            'annual_rate': 5.5,
            'loan_term': 30,
            'annual_tax_rate': 1.2,
            'annual_insurance_rate': 0.8,
            'loan_type': 'conventional'
        }
        
        result1 = self.calc.calculate_all(**params)
        result2 = self.calc.calculate_all(**params)
        
        # Results should be identical
        assert result1['monthly_payment']['total'] == result2['monthly_payment']['total']
        assert result1['loan_details']['ltv'] == result2['loan_details']['ltv']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])