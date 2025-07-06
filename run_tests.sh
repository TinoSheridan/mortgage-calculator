#!/bin/bash

# Test runner script for mortgage calculator
# This script runs different test suites based on the argument provided

set -e  # Exit on any error

echo "🧪 Mortgage Calculator Test Suite"
echo "================================="

# Set required environment variables for testing
export SECRET_KEY="test-secret-key-for-testing-only"

case "${1:-all}" in
    "core")
        echo "🎯 Running core calculation tests..."
        python3 -m pytest tests/test_core_calculations.py -v
        ;;
    "security")
        echo "🔒 Running security tests..."
        python3 -m pytest tests/test_security.py::TestResponseHeaders -v
        python3 -m pytest tests/test_security.py::TestCSRFProtection::test_calculate_endpoint_requires_csrf_token -v
        ;;
    "api")
        echo "🌐 Running API integration tests..."
        python3 -m pytest tests/test_api_integration.py::TestCalculateEndpoint -v
        ;;
    "critical")
        echo "⚡ Running critical functionality tests..."
        python3 -m pytest tests/test_core_calculations.py::TestCoreCalculations::test_refinance_calculation -v
        python3 -m pytest tests/test_api_integration.py::TestCalculateEndpoint::test_high_ltv_conventional_loan -v
        echo "✅ Critical bug fix verified: High LTV loans are no longer blocked"
        ;;
    "smoke")
        echo "💨 Running smoke tests..."
        python3 -m pytest tests/test_core_calculations.py::TestCoreCalculations::test_basic_conventional_loan -v
        python3 -m pytest tests/test_api_integration.py::TestCalculateEndpoint::test_successful_purchase_calculation -v
        python3 -m pytest tests/test_security.py::TestResponseHeaders::test_security_headers_present -v
        ;;
    "all")
        echo "🚀 Running all tests..."
        python3 -m pytest tests/ --tb=short
        ;;
    *)
        echo "Usage: $0 [core|security|api|critical|smoke|all]"
        echo ""
        echo "Test suites:"
        echo "  core     - Core mortgage calculation tests"
        echo "  security - Security and CSRF protection tests"
        echo "  api      - API endpoint integration tests"
        echo "  critical - Critical bug fix verification"
        echo "  smoke    - Quick smoke tests"
        echo "  all      - All tests (default)"
        exit 1
        ;;
esac

echo ""
echo "✅ Test run completed!"