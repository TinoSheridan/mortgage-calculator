#!/usr/bin/env python3
"""Test script for verifying all endpoints work correctly."""

import json
import requests
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:3333"

def test_endpoint(method: str, url: str, data: Dict[str, Any] = None, description: str = "") -> bool:
    """Test a single endpoint and return success status."""
    try:
        print(f"Testing {method} {url} - {description}")
        
        if method.upper() == "GET":
            response = requests.get(url, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            print(f"  ❌ Unsupported method: {method}")
            return False
        
        if response.status_code in [200, 201]:
            print(f"  ✅ Success: {response.status_code}")
            return True
        else:
            print(f"  ❌ Failed: {response.status_code}")
            if response.text:
                print(f"     Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Request failed: {str(e)}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {str(e)}")
        return False

def test_health_endpoint():
    """Test health endpoint."""
    print("\n=== Testing Health Endpoint ===")
    return test_endpoint("GET", f"{BASE_URL}/health", description="Health check")

def test_index_endpoint():
    """Test main index endpoint."""
    print("\n=== Testing Index Endpoint ===")
    return test_endpoint("GET", f"{BASE_URL}/", description="Main calculator page")

def test_calculate_endpoint():
    """Test calculation endpoint with valid data."""
    print("\n=== Testing Calculate Endpoint ===")
    
    # Test with valid data
    valid_data = {
        "purchase_price": 400000,
        "down_payment_percentage": 20,
        "annual_rate": 6.5,
        "loan_term": 30,
        "annual_tax_rate": 1.3,
        "annual_insurance_rate": 1.1,
        "loan_type": "conventional",
        "monthly_hoa_fee": 0,
        "seller_credit": 0,
        "lender_credit": 0,
        "discount_points": 0,
        "include_owners_title": True
    }
    
    success = test_endpoint("POST", f"{BASE_URL}/calculate", valid_data, "Valid calculation")
    
    if success:
        # Get the actual response to verify structure
        try:
            response = requests.post(f"{BASE_URL}/calculate", json=valid_data, timeout=10)
            result = response.json()
            
            required_keys = ["success", "monthly_payment", "loan_amount", "closing_costs"]
            missing_keys = [key for key in required_keys if key not in result]
            
            if missing_keys:
                print(f"  ⚠️  Missing response keys: {missing_keys}")
                return False
            else:
                print(f"  ✅ Response structure valid")
                print(f"     Monthly payment: ${result.get('monthly_payment', 0):,.2f}")
                print(f"     Loan amount: ${result.get('loan_amount', 0):,.2f}")
                
        except Exception as e:
            print(f"  ⚠️  Could not verify response structure: {str(e)}")
    
    return success

def test_refinance_endpoint():
    """Test refinance endpoint with valid data."""
    print("\n=== Testing Refinance Endpoint ===")
    
    valid_data = {
        "appraised_value": 450000,
        "original_loan_balance": 320000,
        "original_interest_rate": 7.5,
        "original_loan_term": 30,
        "original_closing_date": "2020-01-01",
        "new_interest_rate": 6.0,
        "new_loan_term": 30,
        "extra_monthly_payment": 0,
        "new_discount_points": 0
    }
    
    success = test_endpoint("POST", f"{BASE_URL}/refinance", valid_data, "Valid refinance calculation")
    
    if success:
        # Get the actual response to verify structure
        try:
            response = requests.post(f"{BASE_URL}/refinance", json=valid_data, timeout=10)
            result = response.json()
            
            if result.get("success") and "result" in result:
                refinance_result = result["result"]
                print(f"  ✅ Refinance response structure valid")
                print(f"     Current balance: ${refinance_result.get('current_balance', 0):,.2f}")
                print(f"     New monthly payment: ${refinance_result.get('new_monthly_payment', 0):,.2f}")
                print(f"     Monthly savings: ${refinance_result.get('monthly_savings', 0):,.2f}")
            else:
                print(f"  ⚠️  Unexpected refinance response structure")
                return False
                
        except Exception as e:
            print(f"  ⚠️  Could not verify refinance response: {str(e)}")
    
    return success

def test_max_seller_contribution():
    """Test max seller contribution endpoint."""
    print("\n=== Testing Max Seller Contribution Endpoint ===")
    
    valid_data = {
        "loan_type": "conventional",
        "purchase_price": 400000,
        "down_payment_amount": 80000
    }
    
    return test_endpoint("POST", f"{BASE_URL}/api/max_seller_contribution", valid_data, "Max seller contribution")

def test_validation_errors():
    """Test validation error handling."""
    print("\n=== Testing Validation Error Handling ===")
    
    # Test with missing required field
    invalid_data = {
        "down_payment_percentage": 20,
        "annual_rate": 6.5
        # Missing purchase_price
    }
    
    try:
        response = requests.post(f"{BASE_URL}/calculate", json=invalid_data, timeout=10)
        
        if response.status_code == 400:
            result = response.json()
            if "error" in result and not result.get("success", True):
                print(f"  ✅ Validation error handled correctly: {result['error']}")
                return True
            else:
                print(f"  ❌ Unexpected validation response structure")
                return False
        else:
            print(f"  ❌ Expected 400 status code, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error testing validation: {str(e)}")
        return False

def test_invalid_endpoint():
    """Test invalid endpoint handling."""
    print("\n=== Testing Invalid Endpoint Handling ===")
    
    try:
        response = requests.get(f"{BASE_URL}/nonexistent-endpoint", timeout=10)
        
        if response.status_code == 404:
            print(f"  ✅ 404 error handled correctly")
            return True
        else:
            print(f"  ❌ Expected 404 status code, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error testing 404: {str(e)}")
        return False

def main():
    """Run all endpoint tests."""
    print("🧪 Testing Refactored Mortgage Calculator Endpoints")
    print("=" * 60)
    
    tests = [
        test_health_endpoint,
        test_index_endpoint,
        test_calculate_endpoint,
        test_refinance_endpoint,
        test_max_seller_contribution,
        test_validation_errors,
        test_invalid_endpoint
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Test failed with exception: {str(e)}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {test.__name__}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! The refactored application is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the logs above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())