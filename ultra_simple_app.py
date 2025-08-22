"""Ultra-simple calculator app for Render deployment."""

import os
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS

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

        # Extract basic parameters with defaults
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
            "down_payment": round(down_payment, 2),
            "loan_amount": round(loan_amount, 2),
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
        cash_out_amount = float(data.get("cash_out_amount", 0))

        # Calculate new loan amount
        new_loan_amount = current_loan_balance + cash_out_amount

        # Calculate new monthly payment
        new_monthly_payment = calculate_monthly_payment(
            new_loan_amount, new_interest_rate, new_loan_term
        )

        # Calculate LTV
        ltv_ratio = (new_loan_amount / home_value) * 100 if home_value > 0 else 0

        # Calculate basic taxes and insurance
        annual_tax_rate = float(data.get("annual_tax_rate", 1.2))
        annual_insurance_rate = float(data.get("annual_insurance_rate", 0.35))
        monthly_hoa_fee = float(data.get("monthly_hoa_fee", 0))

        monthly_taxes = home_value * (annual_tax_rate / 100) / 12
        monthly_insurance = home_value * (annual_insurance_rate / 100) / 12
        total_monthly_payment = (
            new_monthly_payment + monthly_taxes + monthly_insurance + monthly_hoa_fee
        )

        result = {
            "home_value": home_value,
            "current_loan_balance": current_loan_balance,
            "cash_out_amount": cash_out_amount,
            "new_loan_amount": round(new_loan_amount, 2),
            "new_monthly_payment": round(new_monthly_payment, 2),
            "monthly_taxes": round(monthly_taxes, 2),
            "monthly_insurance": round(monthly_insurance, 2),
            "monthly_hoa_fee": monthly_hoa_fee,
            "total_monthly_payment": round(total_monthly_payment, 2),
            "ltv_ratio": round(ltv_ratio, 2),
            "new_interest_rate": new_interest_rate,
            "new_loan_term": new_loan_term,
        }

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
