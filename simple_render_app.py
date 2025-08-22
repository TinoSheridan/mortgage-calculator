"""Ultra-simple Flask API for Render deployment.

Minimal calculator without complex dependencies.
"""

import logging
import os
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "render-api-key")

# Enable CORS
CORS(
    app,
    origins=[
        "https://tinosheridan.github.io",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
    ],
    supports_credentials=True,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_monthly_payment(loan_amount, annual_rate, loan_term_years):
    """Calculate monthly mortgage payment."""
    monthly_rate = annual_rate / 100 / 12
    num_payments = loan_term_years * 12

    if monthly_rate == 0:
        return loan_amount / num_payments

    payment = (
        loan_amount
        * (monthly_rate * (1 + monthly_rate) ** num_payments)
        / ((1 + monthly_rate) ** num_payments - 1)
    )
    return payment


@app.route("/")
def api_info():
    """Return API information endpoint."""
    return jsonify(
        {
            "name": "Simple Mortgage Calculator API",
            "version": "3.0.0",
            "description": "Minimal mortgage calculator API for GitHub Pages",
            "platform": "Render",
            "endpoints": {
                "calculator": {
                    "POST /api/calculate": "Calculate mortgage payment",
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

        # Extract basic parameters
        purchase_price = float(data.get("purchase_price", 0))
        down_payment_percentage = float(data.get("down_payment_percentage", 20))
        annual_rate = float(data.get("annual_rate", 6.5))
        loan_term = int(data.get("loan_term", 30))

        # Calculate loan amount
        down_payment = purchase_price * (down_payment_percentage / 100)
        loan_amount = purchase_price - down_payment

        # Calculate monthly payment
        monthly_payment = calculate_monthly_payment(loan_amount, annual_rate, loan_term)

        # Calculate basic taxes and insurance
        annual_tax_rate = float(data.get("annual_tax_rate", 1.2))
        annual_insurance_rate = float(data.get("annual_insurance_rate", 0.35))
        monthly_hoa_fee = float(data.get("monthly_hoa_fee", 0))

        monthly_taxes = purchase_price * (annual_tax_rate / 100) / 12
        monthly_insurance = purchase_price * (annual_insurance_rate / 100) / 12
        total_monthly_payment = (
            monthly_payment + monthly_taxes + monthly_insurance + monthly_hoa_fee
        )

        result = {
            "purchase_price": purchase_price,
            "down_payment": down_payment,
            "loan_amount": loan_amount,
            "monthly_payment": round(monthly_payment, 2),
            "monthly_taxes": round(monthly_taxes, 2),
            "monthly_insurance": round(monthly_insurance, 2),
            "monthly_hoa_fee": monthly_hoa_fee,
            "total_monthly_payment": round(total_monthly_payment, 2),
            "annual_rate": annual_rate,
            "loan_term": loan_term,
        }

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


@app.route("/health")
def health_check():
    """Health check endpoint."""
    return jsonify(
        {
            "status": "healthy",
            "version": "3.0.0",
            "platform": "Render",
            "timestamp": datetime.now().isoformat(),
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
