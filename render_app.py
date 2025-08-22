"""Simplified Flask API for Render deployment.

This version has no database dependencies and focuses on core calculator functionality.
"""

import logging
import os
import sys
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS

from calculator import MortgageCalculator

# Set up Python path
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

# Initialize Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "render-api-key")

# Enable CORS for GitHub Pages
CORS(
    app,
    origins=[
        "https://tinosheridan.github.io",  # GitHub Pages URL
        "http://localhost:3000",  # For local development
        "http://127.0.0.1:3000",  # For local development
        "http://localhost:5000",  # Local Flask development
        "http://127.0.0.1:5000",  # Local Flask development
    ],
    supports_credentials=True,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize calculator with default configuration
calculator = MortgageCalculator()


@app.route("/")
def api_info():
    """Return API information endpoint."""
    return jsonify(
        {
            "name": "Mortgage Calculator API",
            "version": "2.8.1",
            "description": "Simplified mortgage calculator API for GitHub Pages frontend",
            "platform": "Render",
            "endpoints": {
                "calculator": {
                    "POST /api/calculate": "Calculate mortgage payment",
                    "POST /api/refinance": "Calculate refinance options",
                },
                "health": {
                    "GET /health": "Health check endpoint",
                },
            },
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/api/calculate", methods=["POST"])
def api_calculate():
    """Calculate mortgage payments via API endpoint."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Extract calculation parameters
        purchase_price = float(data.get("purchase_price", 0))
        down_payment_percentage = float(data.get("down_payment_percentage", 20))
        annual_rate = float(data.get("annual_rate", 6.5))
        loan_term = int(data.get("loan_term", 30))
        loan_type = data.get("loan_type", "conventional").lower()

        # Property details
        annual_tax_rate = float(data.get("annual_tax_rate", 1.2))
        annual_insurance_rate = float(data.get("annual_insurance_rate", 0.35))
        monthly_hoa_fee = float(data.get("monthly_hoa_fee", 0))

        # Credits and fees
        seller_credit = float(data.get("seller_credit", 0))
        lender_credit = float(data.get("lender_credit", 0))
        discount_points = float(data.get("discount_points", 0))

        # Perform calculation
        result = calculator.calculate_all(
            purchase_price=purchase_price,
            down_payment_percentage=down_payment_percentage,
            annual_rate=annual_rate,
            loan_term=loan_term,
            loan_type=loan_type,
            annual_tax_rate=annual_tax_rate,
            annual_insurance_rate=annual_insurance_rate,
            monthly_hoa_fee=monthly_hoa_fee,
            seller_credit=seller_credit,
            lender_credit=lender_credit,
            discount_points=discount_points,
        )

        return jsonify(
            {
                "success": True,
                "result": result,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Calculation error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/refinance", methods=["POST"])
def api_refinance():
    """Calculate refinance options via API endpoint."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Extract refinance parameters
        home_value = float(data.get("home_value", 0))
        current_loan_balance = float(data.get("current_loan_balance", 0))
        new_interest_rate = float(data.get("new_interest_rate", 6.5))
        new_loan_term = int(data.get("new_loan_term", 30))
        loan_type = data.get("loan_type", "conventional").lower()

        # Refinance options
        cash_out_amount = float(data.get("cash_out_amount", 0))
        target_ltv = float(data.get("target_ltv", 80)) if data.get("target_ltv") else None

        # Property details
        annual_tax_rate = float(data.get("annual_tax_rate", 1.2))
        annual_insurance_rate = float(data.get("annual_insurance_rate", 0.35))
        monthly_hoa_fee = float(data.get("monthly_hoa_fee", 0))

        # Perform refinance calculation
        result = calculator.calculate_refinance(
            home_value=home_value,
            current_loan_balance=current_loan_balance,
            new_interest_rate=new_interest_rate,
            new_loan_term=new_loan_term,
            loan_type=loan_type,
            cash_out_amount=cash_out_amount,
            target_ltv=target_ltv,
            annual_tax_rate=annual_tax_rate,
            annual_insurance_rate=annual_insurance_rate,
            monthly_hoa_fee=monthly_hoa_fee,
        )

        return jsonify(
            {
                "success": True,
                "result": result,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Refinance calculation error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/health")
def health_check():
    """Health check endpoint."""
    try:
        return jsonify(
            {
                "status": "healthy",
                "version": "2.8.1",
                "platform": "Render",
                "calculator_available": True,
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        return (
            jsonify(
                {"status": "unhealthy", "error": str(e), "timestamp": datetime.now().isoformat()}
            ),
            500,
        )


if __name__ == "__main__":
    # Run the API
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
