"""
Test script to debug VA funding fee calculation for subsequent use
"""

import logging
import json
from calculator import MortgageCalculator
from config_manager import ConfigManager

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_va_funding_fee():
    """Test VA funding fee calculation for different scenarios"""
    config_manager = ConfigManager()
    calculator = MortgageCalculator()
    
    # Test parameters
    loan_amount = 300000
    
    # Test cases
    test_cases = [
        {
            "down_payment_percentage": 0,
            "service_type": "active",
            "loan_usage": "first",
            "disability_exempt": False,
            "expected_rate": 2.3
        },
        {
            "down_payment_percentage": 0,
            "service_type": "active", 
            "loan_usage": "subsequent",
            "disability_exempt": False,
            "expected_rate": 3.6
        },
        {
            "down_payment_percentage": 0,
            "service_type": "reserves",
            "loan_usage": "first",
            "disability_exempt": False,
            "expected_rate": 2.3
        },
        {
            "down_payment_percentage": 0,
            "service_type": "reserves",
            "loan_usage": "subsequent",
            "disability_exempt": False,
            "expected_rate": 3.6
        },
        {
            "down_payment_percentage": 8,
            "service_type": "active",
            "loan_usage": "first",
            "disability_exempt": False,
            "expected_rate": 1.65
        },
        {
            "down_payment_percentage": 8,
            "service_type": "active",
            "loan_usage": "subsequent",
            "disability_exempt": False,
            "expected_rate": 1.65
        },
        {
            "down_payment_percentage": 15,
            "service_type": "active",
            "loan_usage": "first",
            "disability_exempt": False,
            "expected_rate": 1.4
        },
        {
            "down_payment_percentage": 0,
            "service_type": "active",
            "loan_usage": "first",
            "disability_exempt": True,
            "expected_rate": 0
        }
    ]
    
    print("VA Funding Fee Config:")
    print(json.dumps(calculator.config.get('loan_types', {}).get('va', {}).get('funding_fee_rates', {}), indent=2))
    print("\nTesting VA funding fee calculation:")
    print("-" * 80)
    
    for i, case in enumerate(test_cases):
        try:
            # Calculate funding fee
            fee = calculator.calculate_va_funding_fee(
                loan_amount=loan_amount,
                down_payment_percentage=case["down_payment_percentage"],
                service_type=case["service_type"],
                loan_usage=case["loan_usage"],
                disability_exempt=case["disability_exempt"]
            )
            
            # Calculate rate
            rate = round((fee / loan_amount) * 100, 2)
            
            # Check if the rate matches expected rate
            if abs(rate - case["expected_rate"]) < 0.01:
                result = "✓ PASS"
            else:
                result = "✗ FAIL"
                
            print(f"{result} Case {i+1}: {case['service_type']}, {case['loan_usage']}, " +
                  f"down={case['down_payment_percentage']}%, exempt={case['disability_exempt']}, " +
                  f"actual_rate={rate}%, expected_rate={case['expected_rate']}%, fee=${fee:.2f}")
            
        except Exception as e:
            print(f"✗ ERROR Case {i+1}: {case['service_type']}, {case['loan_usage']}, " +
                  f"down={case['down_payment_percentage']}%, exempt={case['disability_exempt']}")
            print(f"   Error: {str(e)}")
    
if __name__ == "__main__":
    test_va_funding_fee()
