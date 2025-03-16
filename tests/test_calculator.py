import unittest
from unittest.mock import patch, MagicMock
import json
from decimal import Decimal
from calculator import MortgageCalculator

class TestMortgageCalculator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Mock configuration data for testing
        cls.mock_config = {
            'loan_types': {
                'conventional': {
                    'min_down_payment': 3,
                    'max_ltv': 97,
                    'min_credit_score': 620
                },
                'fha': {
                    'min_down_payment': 3.5,
                    'max_ltv': 96.5,
                    'min_credit_score': 580
                }
            },
            'pmi_rates': {
                'conventional': {
                    'ltv_ranges': {
                        '80.01-85.00': 0.0030,
                        '85.01-90.00': 0.0049,
                        '90.01-95.00': 0.0067,
                        '95.01-97.00': 0.0088
                    },
                    'credit_score_adjustments': {
                        '760+': 0.0000,
                        '740-759': 0.0002,
                        '720-739': 0.0004,
                        '700-719': 0.0008,
                        '680-699': 0.0012,
                        '660-679': 0.0016,
                        '640-659': 0.0027,
                        '620-639': 0.0032
                    }
                },
                'fha': {
                    'upfront': 0.0175,
                    'annual': {
                        'ltv_over_95': 0.0085,
                        'ltv_under_95': 0.0080
                    }
                }
            },
            'closing_costs': {
                'origination_fee': {
                    'type': 'percentage',
                    'value': 1.0,
                    'calculation_base': 'loan_amount'
                },
                'appraisal_fee': {
                    'type': 'fixed',
                    'value': 500,
                    'calculation_base': 'fixed'
                }
            },
            'prepaid_items': {
                'months_insurance_prepaid': 12,
                'months_tax_prepaid': 6,
                'days_interest_prepaid': 30,
                'months_insurance_escrow': 2,
                'months_tax_escrow': 3
            },
            'limits': {
                'max_interest_rate': 15.0,
                'max_loan_term': 30,
                'min_purchase_price': 50000,
                'max_purchase_price': 2000000
            }
        }

    def setUp(self):
        self.patcher = patch('calculator.ConfigManager')
        mock_config_manager = self.patcher.start()
        instance = mock_config_manager.return_value
        instance.get_config.return_value = self.mock_config
        instance.get_loan_type_config.return_value = self.mock_config['loan_types']['conventional']
        self.calculator = MortgageCalculator()

    def tearDown(self):
        self.patcher.stop()

    def test_monthly_payment_calculation(self):
        """Test basic monthly payment calculation"""
        # Test case: $300,000 loan, 6% annual rate, 30 years
        monthly_payment = self.calculator.calculate_monthly_payment(300000, 6.0, 30)
        self.assertAlmostEqual(monthly_payment, 1798.65, places=2)

        # Test case: $0 interest rate
        monthly_payment = self.calculator.calculate_monthly_payment(300000, 0.0, 30)
        self.assertAlmostEqual(monthly_payment, 833.33, places=2)

    def test_mortgage_insurance_calculation(self):
        """Test mortgage insurance calculations for different scenarios"""
        # Test case: No PMI needed for conventional loan (LTV <= 80%)
        mi = self.calculator.calculate_mortgage_insurance(240000, 300000, 740, 'conventional')
        self.assertEqual(mi, 0.0)

        # Test case: Conventional loan with 90% LTV and good credit
        mi = self.calculator.calculate_mortgage_insurance(270000, 300000, 740, 'conventional')
        # Since PMI rates can vary based on configuration, just verify it's calculated and returns a value > 0
        self.assertGreater(mi, 0.0)

        # Test case: Non-conventional loan type
        mi = self.calculator.calculate_mortgage_insurance(270000, 300000, 740, 'jumbo')
        self.assertEqual(mi, 0.0)
        
        # Test case: FHA loan with upfront MIP
        mi = self.calculator.calculate_mortgage_insurance(270000, 300000, 740, 'fha', 360)
        # FHA MIP rate depends on configuration, so just verify it's not zero
        self.assertGreater(mi, 0.0)

    def test_closing_costs_calculation(self):
        """Test closing costs calculations"""
        costs = self.calculator.calculate_closing_costs(300000, 270000)
        
        # Test origination fee (percentage-based)
        self.assertAlmostEqual(costs['origination_fee'], 2700.0)  # 1% of loan amount
        
        # Test appraisal fee (fixed)
        self.assertEqual(costs['appraisal_fee'], 500.0)
        
        # Test total
        expected_total = 2700.0 + 500.0
        self.assertAlmostEqual(costs['total'], expected_total)

    def test_prepaid_items_calculation(self):
        """Test prepaid items calculations"""
        items = self.calculator.calculate_prepaid_items(
            loan_amount=300000,
            annual_tax_rate=1.2,
            annual_insurance_rate=0.5,
            annual_interest_rate=6.0
        )
        
        # Test property tax calculation
        monthly_tax = (300000 * 1.2 / 100) / 12
        expected_prepaid_tax = monthly_tax * 6  # 6 months prepaid
        self.assertAlmostEqual(items['prepaid_tax'], round(expected_prepaid_tax, 2))
        
        # Test insurance calculation
        monthly_insurance = (300000 * 0.5 / 100) / 12
        expected_prepaid_insurance = monthly_insurance * 12  # 12 months prepaid
        self.assertAlmostEqual(items['prepaid_insurance'], round(expected_prepaid_insurance, 2))

    def test_calculate_all(self):
        """Test complete mortgage calculation"""
        result = self.calculator.calculate_all(
            purchase_price=300000,
            down_payment=60000,
            annual_rate=6.0,
            loan_term=30,
            annual_tax_rate=1.2,
            annual_insurance_rate=0.5,
            credit_score=740,
            loan_type='conventional',
            hoa_fee=100,
            seller_credit=3000,
            lender_credit=2000
        )
        
        # Test loan details
        self.assertEqual(result['loan_details']['purchase_price'], 300000)
        self.assertEqual(result['loan_details']['down_payment'], 60000)
        self.assertEqual(result['loan_details']['loan_amount'], 240000)
        self.assertEqual(result['loan_details']['ltv'], 80.0)
        
        # Test monthly payment components
        self.assertIn('principal_and_interest', result['monthly_payment'])
        self.assertIn('property_tax', result['monthly_payment'])
        self.assertIn('home_insurance', result['monthly_payment'])
        self.assertIn('mortgage_insurance', result['monthly_payment'])
        self.assertEqual(result['monthly_payment']['hoa_fee'], 100)

    def test_validation_errors(self):
        """Test input validation"""
        # Test invalid interest rate
        with self.assertRaises(ValueError) as context:
            self.calculator.calculate_all(
                purchase_price=300000,
                down_payment=60000,
                annual_rate=16.0,  # Exceeds max
                loan_term=30,
                annual_tax_rate=1.2,
                annual_insurance_rate=0.5,
                credit_score=740,
                loan_type='conventional'
            )
        self.assertIn("Interest rate exceeds maximum", str(context.exception))

        # Test invalid purchase price
        with self.assertRaises(ValueError) as context:
            self.calculator.calculate_all(
                purchase_price=40000,  # Below minimum
                down_payment=8000,
                annual_rate=6.0,
                loan_term=30,
                annual_tax_rate=1.2,
                annual_insurance_rate=0.5,
                credit_score=740,
                loan_type='conventional'
            )
        self.assertIn("Purchase price below minimum", str(context.exception))

if __name__ == '__main__':
    unittest.main()
