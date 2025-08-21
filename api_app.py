"""
API-only Flask application for GitHub Pages deployment.

This is a pure API version of the mortgage calculator that serves JSON responses
and can be deployed to Railway/Vercel while the frontend runs on GitHub Pages.
"""

import logging
import os
import sys
from datetime import datetime, timedelta

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

# Set up Python path
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

# Load environment variables
load_dotenv()

from flask_login import LoginManager, current_user, login_required

import auth_routes

# Import our modules
import database
from calculator import MortgageCalculator
from config_service import config_service
from models import Organization, User, UserRole, db

# Initialize Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "api-secret-key")

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

# Initialize database
database.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Register auth blueprint
app.register_blueprint(auth_routes.auth_bp)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize calculator
calculator = MortgageCalculator()


@app.route("/")
def api_info():
    """API information endpoint."""
    return jsonify(
        {
            "name": "Mortgage Calculator API",
            "version": "2.8.0",
            "description": "Multi-tenant mortgage calculator API for GitHub Pages frontend",
            "endpoints": {
                "auth": {
                    "POST /auth/api/login": "User login (returns JWT token)",
                    "POST /auth/api/register": "User registration",
                    "POST /auth/api/logout": "User logout",
                    "GET /auth/api/profile": "Get user profile",
                },
                "calculator": {
                    "POST /api/calculate": "Calculate mortgage payment",
                    "POST /api/refinance": "Calculate refinance options",
                },
                "config": {
                    "GET /api/config/<type>": "Get configuration (closing_costs, pmi_rates, etc.)",
                    "POST /api/config/<type>": "Update user configuration",
                },
                "admin": {
                    "GET /api/admin/users": "List users (admin only)",
                    "POST /api/admin/users": "Create user (admin only)",
                },
            },
            "database_connected": database.check_database_connection(),
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/api/calculate", methods=["POST"])
def api_calculate():
    """API endpoint for mortgage calculations."""
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

        # Get user-specific configuration if logged in
        user_id = None
        organization_id = None
        if current_user and current_user.is_authenticated:
            user_id = current_user.id
            organization_id = current_user.organization_id

        # Load configuration with inheritance
        config_data = config_service.get_config("mortgage_config", user_id, organization_id)
        closing_costs_config = config_service.get_config("closing_costs", user_id, organization_id)

        # Update calculator configuration
        calculator.config = config_data

        # Debug logging to verify method exists
        logger.info(
            f"Calculator methods available: {[method for method in dir(calculator) if 'calculate' in method]}"
        )

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
                "user_id": user_id,
                "organization_id": organization_id,
            }
        )

    except Exception as e:
        logger.error(f"Calculation error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/refinance", methods=["POST"])
def api_refinance():
    """API endpoint for refinance calculations."""
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

        # Get user-specific configuration if logged in
        user_id = None
        organization_id = None
        if current_user and current_user.is_authenticated:
            user_id = current_user.id
            organization_id = current_user.organization_id

        # Load configuration with inheritance
        config_data = config_service.get_config("mortgage_config", user_id, organization_id)

        # Update calculator configuration
        calculator.config = config_data

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
                "user_id": user_id,
                "organization_id": organization_id,
            }
        )

    except Exception as e:
        logger.error(f"Refinance calculation error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/config/<config_type>", methods=["GET"])
def api_get_config(config_type):
    """Get configuration with user inheritance."""
    try:
        # Get user context if logged in
        user_id = None
        organization_id = None
        if current_user and current_user.is_authenticated:
            user_id = current_user.id
            organization_id = current_user.organization_id

        # Get configuration with inheritance
        config_data = config_service.get_config(config_type, user_id, organization_id)

        # Get inheritance info for debugging
        inheritance_info = config_service.get_config_inheritance_info(
            config_type, user_id, organization_id
        )

        return jsonify(
            {
                "success": True,
                "config_type": config_type,
                "config_data": config_data,
                "inheritance_info": inheritance_info,
                "user_id": user_id,
                "organization_id": organization_id,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Config retrieval error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/config/<config_type>", methods=["POST"])
@login_required
def api_set_config(config_type):
    """Set user-specific configuration."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No configuration data provided"}), 400

        config_data = data.get("config_data")
        description = data.get("description", f"Custom {config_type} configuration")

        if not config_data:
            return jsonify({"error": "config_data is required"}), 400

        # Set user configuration
        success = config_service.set_user_config(
            user_id=current_user.id,
            config_type=config_type,
            config_data=config_data,
            description=description,
        )

        if success:
            return jsonify(
                {
                    "success": True,
                    "message": f"Configuration {config_type} updated successfully",
                    "timestamp": datetime.now().isoformat(),
                }
            )
        else:
            return jsonify({"success": False, "error": "Failed to update configuration"}), 500

    except Exception as e:
        logger.error(f"Config update error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/auth/login", methods=["POST"])
def api_login():
    """API login endpoint that returns JWT token."""
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400

        # Find user
        user = User.query.filter((User.username == username) | (User.email == username)).first()

        if user and user.check_password(password) and user.is_active:
            # For API, we'll use session-based auth (can be upgraded to JWT later)
            from flask_login import login_user

            login_user(user)

            user.last_login = datetime.now()
            db.session.commit()

            return jsonify(
                {
                    "success": True,
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "full_name": user.get_full_name(),
                        "role": user.role.value,
                        "organization_id": user.organization_id,
                        "organization_name": user.organization.display_name
                        if user.organization
                        else None,
                    },
                    "message": "Login successful",
                }
            )
        else:
            return jsonify({"error": "Invalid credentials"}), 401

    except Exception as e:
        logger.error(f"API login error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/auth/profile", methods=["GET"])
@login_required
def api_profile():
    """Get current user profile."""
    return jsonify(
        {
            "success": True,
            "user": {
                "id": current_user.id,
                "username": current_user.username,
                "email": current_user.email,
                "full_name": current_user.get_full_name(),
                "role": current_user.role.value,
                "organization_id": current_user.organization_id,
                "organization_name": current_user.organization.display_name
                if current_user.organization
                else None,
                "last_login": current_user.last_login.isoformat()
                if current_user.last_login
                else None,
            },
        }
    )


@app.route("/api/auth/logout", methods=["POST"])
@login_required
def api_logout():
    """API logout endpoint."""
    from flask_login import logout_user

    logout_user()
    return jsonify({"success": True, "message": "Logged out successfully"})


@app.route("/health")
def health_check():
    """Health check endpoint."""
    try:
        db_connected = database.check_database_connection()
        db_info = database.get_database_info()

        return jsonify(
            {
                "status": "healthy",
                "version": "2.8.0",
                "database_connected": db_connected,
                "database_info": db_info,
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
    # Initialize database on startup
    with app.app_context():
        database.create_tables()
        database.setup_initial_data()

    # Run the API
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_ENV") == "development")
