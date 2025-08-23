"""Full-featured calculator app for Render deployment."""

import os
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS

from calculator import MortgageCalculator

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "test-key")

# Enable CORS for GitHub Pages integration
CORS(
    app,
    origins=[
        "https://tinosheridan.github.io",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    supports_credentials=True,
)

# Initialize the full mortgage calculator
calculator = MortgageCalculator()


@app.route("/")
def home():
    """Home endpoint."""
    return jsonify(
        {
            "name": "Mortgage Calculator API v3",
            "version": "3.1.0",
            "description": "Standalone mortgage and refinance calculator API",
            "platform": "Render",
            "status": "working",
            "endpoints": {
                "/health": "Health check",
                "/api/calculate": "POST - Calculate mortgage payment",
                "/api/refinance": "POST - Calculate refinance options",
            },
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify(
        {"status": "healthy", "version": "3.1.0", "timestamp": datetime.now().isoformat()}
    )


@app.route("/api/calculate", methods=["POST"])
def api_calculate():
    """Calculate mortgage payments via API endpoint."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Use the full calculator's calculate_all method
        result = calculator.calculate_all(
            purchase_price=float(data.get("purchase_price", 0)),
            down_payment_percentage=float(data.get("down_payment_percentage", 20)),
            annual_rate=float(data.get("annual_rate", 6.5)),
            loan_term=int(data.get("loan_term", 30)),
            loan_type=data.get("loan_type", "conventional"),
            annual_tax_rate=float(data.get("annual_tax_rate", 1.2)),
            annual_insurance_rate=float(data.get("annual_insurance_rate", 0.35)),
            monthly_hoa_fee=float(data.get("monthly_hoa_fee", 0)),
            seller_credit=float(data.get("seller_credit", 0)),
            lender_credit=float(data.get("lender_credit", 0)),
            discount_points=float(data.get("discount_points", 0)),
            include_owners_title=data.get("include_owners_title", False),
            va_service_type=data.get("va_service_type", "")
            if data.get("va_service_type")
            else None,
            va_usage=data.get("va_usage", "") if data.get("va_usage") else None,
            va_disability_exempt=data.get("va_disability_exempt", False),
        )

        return jsonify(
            {
                "success": True,
                "result": result,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/refinance", methods=["POST"])
def api_refinance():
    """Calculate refinance options via API endpoint."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Use the full calculator's calculate_refinance method
        result = calculator.calculate_refinance(
            home_value=float(data.get("home_value", 0)),
            current_loan_balance=float(data.get("current_loan_balance", 0)),
            new_interest_rate=float(data.get("new_interest_rate", 6.5)),
            new_loan_term=int(data.get("new_loan_term", 30)),
            loan_type=data.get("loan_type", "conventional"),
            cash_out_amount=float(data.get("cash_out_amount", 0)),
            target_ltv=float(data.get("target_ltv")) if data.get("target_ltv") else None,
            annual_tax_rate=float(data.get("annual_tax_rate", 1.2)),
            annual_insurance_rate=float(data.get("annual_insurance_rate", 0.35)),
            monthly_hoa_fee=float(data.get("monthly_hoa_fee", 0)),
        )

        return jsonify(
            {
                "success": True,
                "result": result,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
