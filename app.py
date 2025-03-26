import json
import logging
import os
import importlib
import sys
from datetime import datetime, timedelta
from functools import wraps
import time

from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect

from admin_routes import admin_bp, load_closing_costs, save_closing_costs
from beta_routes import beta_bp
from calculator import MortgageCalculator
from chat_routes import chat_bp
from config_factory import get_config
from config_manager import ConfigManager
from forms import LoginForm
from health_check import health_bp

# Configure logging early
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Application module loading")

def force_reload_version():
    """
    Force reload VERSION module to get the correct version
    This prevents issues with cached versions across different Python installations
    """
    try:
        # Clear any cached version module
        if 'VERSION' in sys.modules:
            logger.info("Reloading VERSION module to ensure correct version")
            importlib.reload(sys.modules['VERSION'])
        else:
            logger.info("Importing VERSION module for the first time")
            import VERSION
    
        # Get and log the version number
        from VERSION import VERSION as app_version
        logger.info(f"Application version: {app_version}")
        return app_version
    except Exception as e:
        logger.error(f"Error loading version information: {str(e)}")
        return "unknown"

# Force reload VERSION to ensure we have the correct version
current_version = force_reload_version()

# Create timestamp for cache busting
cache_timestamp = int(datetime.now().timestamp())

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.version = current_version  # Store version in app object for template access
app.config["VERSION"] = current_version  # Also store in config
app.config["CACHE_BUSTER"] = f"{current_version}.{cache_timestamp}"  # Create cache buster string

# Load configuration based on environment
app_config = get_config()

# Ensure proper MIME types for static files
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0  # During development


# Add proper MIME type handling for static files
@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)


# Apply configuration from the selected environment
app.config.from_object(app_config)
app.secret_key = os.getenv("SECRET_KEY", "default-secret-key")
app.config["WTF_CSRF_ENABLED"] = False  # Temporarily disable CSRF for debugging
CORS(app)

# Log app initialization with config details
app.logger.info(
    f"Flask app initialized with config: {app.config.get('ENV', 'unknown')}"
)

# Initialize app with environment-specific settings
if hasattr(app_config, "init_app"):
    app_config.init_app(app)


# Make config settings available to templates
@app.context_processor
def inject_config():
    return {
        "app_version": app.version,
        "cache_buster": app.config["CACHE_BUSTER"],
        "config": app.config
    }


# Add response header to prevent caching
@app.after_request
def add_header(response):
    # Force browser to clear cache with stronger headers
    timestamp = int(time.time())
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0, post-check=0, pre-check=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["X-Cache-Bust"] = str(timestamp)
    
    # Add clear Site-Data header on main page to force cache reset
    if request.path == "/":
        response.headers["Clear-Site-Data"] = '"cache", "cookies", "storage"'

    # Add Content Security Policy that allows both cdn.jsdelivr.net and cdnjs.cloudflare.com
    if request.path.startswith("/admin"):
        # Apply stricter CSP for admin routes
        response.headers[
            "Content-Security-Policy"
        ] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src-elem 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com data:; img-src 'self' data: blob:; connect-src 'self'"
    else:
        # Regular CSP for user-facing routes
        response.headers[
            "Content-Security-Policy"
        ] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src-elem 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com data:; img-src 'self' data: blob:; connect-src 'self'"
    
    # Set proper referrer policy
    response.headers["Referrer-Policy"] = "same-origin"

    # Explicitly set MIME types for static files if needed
    if request.path.startswith("/static/"):
        file_ext = os.path.splitext(request.path)[1].lower()
        if file_ext == ".css":
            response.headers["Content-Type"] = "text/css"
        elif file_ext == ".js":
            response.headers["Content-Type"] = "application/javascript"

    return response


# Initialize CSRF protection
csrf = CSRFProtect(app)


# Exempt specific routes from CSRF protection
# Note: Be careful with CSRF exemptions as they can introduce security vulnerabilities
# Only exempt endpoints that absolutely require it (e.g., API endpoints used by third-party services)
@app.after_request
def csrf_exempt_admin_routes(response):
    # Exclude specific admin endpoints from CSRF protection for AJAX requests
    if (
        request.path.startswith("/admin/closing-costs/")
        or request.path == "/admin/pmi-rates/update"
    ):
        if request.method in ["POST", "PUT", "DELETE"]:
            response.headers.pop("X-Frame-Options", None)
            response.headers.pop("Content-Security-Policy", None)
            response.headers.pop("X-Content-Type-Options", None)
            return response
    return response


# Exempt specific endpoints from CSRF protection (we'll handle it manually with X-CSRFToken header)
@csrf.exempt
@app.route("/calculate", methods=["POST"])
def calculate():
    """Main calculation endpoint that returns complete mortgage details."""
    try:
        data = request.get_json()
        app.logger.info(f"Received calculation request with data: {data}")

        # Extract parameters
        purchase_price = float(data.get("purchase_price", 0))
        down_payment_percentage = float(data.get("down_payment_percentage", 0))
        annual_rate = float(data.get("annual_rate", 0))
        loan_term = int(data.get("loan_term", 30))
        annual_tax_rate = float(data.get("annual_tax_rate", 0))
        annual_insurance_rate = float(data.get("annual_insurance_rate", 0))
        loan_type = data.get("loan_type", "conventional")
        monthly_hoa_fee = float(data.get("monthly_hoa_fee", 0))
        seller_credit = float(data.get("seller_credit", 0))
        lender_credit = float(data.get("lender_credit", 0))
        discount_points = float(data.get("discount_points", 0))

        # Get optional closing date
        closing_date_str = data.get("closing_date")
        closing_date = None
        if closing_date_str:
            try:
                # Parse ISO format date string (YYYY-MM-DD)
                closing_date = datetime.strptime(closing_date_str, "%Y-%m-%d").date()
                app.logger.info(f"Using closing date: {closing_date}")
            except Exception as e:
                app.logger.warning(
                    f"Could not parse closing date '{closing_date_str}': {e}"
                )

        # Extract specific parameters for different loan types
        va_params = {}
        if loan_type.lower() == "va":
            app.logger.info(
                f"Processing VA loan with parameters: service_type={data.get('va_service_type')}, "
                f"usage={data.get('va_usage')}, "
                f"disability_exempt={data.get('va_disability_exempt')}"
            )

            va_params = {
                "va_service_type": data.get("va_service_type", "active"),
                "va_usage": data.get("va_usage", "first"),
                "va_disability_exempt": data.get("va_disability_exempt", False),
            }

        # Create a fresh calculator instance with latest config
        calculator = MortgageCalculator()
        # Force reload of configuration to ensure latest changes are used
        calculator.config_manager.load_config()
        calculator.config = calculator.config_manager.get_config()
        app.logger.info("Using freshly loaded configuration for main calculation")

        # Convert down payment percentage to amount
        down_payment_amount = purchase_price * (down_payment_percentage / 100)

        # Calculate results
        result = calculator.calculate_all(
            purchase_price=purchase_price,
            down_payment=down_payment_amount,
            annual_rate=annual_rate,
            loan_term=loan_term,
            annual_tax_rate=annual_tax_rate,
            annual_insurance_rate=annual_insurance_rate,
            loan_type=loan_type,
            hoa_fee=monthly_hoa_fee,
            seller_credit=seller_credit,
            lender_credit=lender_credit,
            discount_points=discount_points,
            closing_date=closing_date,
            **va_params,
        )

        # Calculate maximum seller contribution based on loan type and LTV
        max_seller_contribution = calculate_max_seller_contribution(
            loan_type=loan_type,
            purchase_price=purchase_price,
            down_payment_amount=down_payment_amount,
            occupancy=data.get("occupancy", "primary_residence"),
        )

        # Add max seller contribution to result
        if "loan_details" not in result:
            result["loan_details"] = {}
        result["loan_details"]["max_seller_contribution"] = max_seller_contribution

        # Special handling for VA loans - check prepaids and discount points against 4% limit
        if loan_type.lower() == "va":
            # Get prepaids total from result
            prepaids_total = 0
            if "prepaids" in result and "total" in result["prepaids"]:
                prepaids_total = result["prepaids"]["total"]

            # Get discount points from input
            discount_points_amount = 0
            if "discount_points" in result.get("closing_costs", {}):
                discount_points_amount = result["closing_costs"]["discount_points"]

            # Calculate VA concession limit (4% of purchase price)
            va_concession_limit = 0.04 * purchase_price
            result["loan_details"]["va_concession_limit"] = va_concession_limit

            # Calculate potential concessions (prepaids + discount points that would be covered by seller)
            potential_concessions = min(
                prepaids_total + discount_points_amount, seller_credit
            )
            result["loan_details"]["potential_concessions"] = potential_concessions

            # Check if concessions exceed limit
            if potential_concessions > va_concession_limit:
                result["loan_details"]["seller_credit_exceeds_max"] = True
                result["loan_details"]["va_concessions_exceed_limit"] = True
            else:
                result["loan_details"]["seller_credit_exceeds_max"] = False
                result["loan_details"]["va_concessions_exceed_limit"] = False
        else:
            # For non-VA loans, check total seller credit against max contribution
            if seller_credit > max_seller_contribution:
                result["loan_details"]["seller_credit_exceeds_max"] = True
            else:
                result["loan_details"]["seller_credit_exceeds_max"] = False

        # Format the response for the frontend
        formatted_result = {
            "success": True,
            "monthly_payment": result["monthly_payment"]["total"],
            "loan_amount": result["loan_details"]["loan_amount"],
            "down_payment": result["loan_details"]["down_payment"],
            "monthly_mortgage": result["monthly_payment"]["principal_and_interest"],
            "monthly_tax": result["monthly_payment"]["property_tax"],
            "monthly_insurance": result["monthly_payment"]["home_insurance"],
            "monthly_pmi": result["monthly_payment"]["mortgage_insurance"],
            "monthly_hoa": result["monthly_payment"]["hoa_fee"],
            "closing_costs": result["closing_costs"],
            "prepaids": result["prepaid_items"],
            "monthly_breakdown": {
                "principal_interest": result["monthly_payment"][
                    "principal_and_interest"
                ],
                "property_tax": result["monthly_payment"]["property_tax"],
                "home_insurance": result["monthly_payment"]["home_insurance"],
                "mortgage_insurance": result["monthly_payment"]["mortgage_insurance"],
                "hoa_fee": result["monthly_payment"]["hoa_fee"],
                "total": result["monthly_payment"]["total"],
            },
            "loan_details": result["loan_details"],
            "credits": {
                "seller_credit": seller_credit,
                "lender_credit": lender_credit,
                "total": seller_credit + lender_credit,
            },
            # Calculate total cash needed if not in the result, making sure to subtract credits
            "total_cash_needed": result.get(
                "cash_to_close",
                result["loan_details"]["down_payment"]
                + result["closing_costs"].get("total", 0)
                + result["prepaid_items"].get("total", 0)
                - (seller_credit + lender_credit),
            ),
        }

        return jsonify(formatted_result)
    except ValueError as e:
        app.logger.error(f"Value error in calculate: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app.logger.error(f"Error in calculate: {e}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


def calculate_max_seller_contribution(
    loan_type, purchase_price, down_payment_amount, occupancy="primary_residence"
):
    """
    Calculate the maximum allowed seller contribution based on loan type, LTV ratio, and occupancy.

    Args:
        loan_type (str): Type of loan ('conventional', 'fha', 'va', 'usda')
        purchase_price (float): Purchase price of the property
        down_payment_amount (float): Down payment amount
        occupancy (str): Property occupancy type (primary_residence, second_home, investment_property)

    Returns:
        float: Maximum allowed seller contribution amount in dollars
    """
    # Load seller contributions configuration
    seller_contributions_file = os.path.join(
        app.config.get("CONFIG_DIR", "config"), "seller_contributions.json"
    )
    seller_contributions = {}

    try:
        if os.path.exists(seller_contributions_file):
            with open(seller_contributions_file, "r") as f:
                seller_contributions = json.load(f)
    except Exception as e:
        app.logger.error(f"Error loading seller contributions: {e}")
        # Default to conservative limits if file can't be loaded
        return 0.03 * purchase_price

    # Calculate LTV ratio
    loan_amount = purchase_price - down_payment_amount
    ltv_ratio = (loan_amount / purchase_price) * 100

    # Special handling for VA loans - sellers can pay all closing costs, but concessions
    # (prepaids and discount points) are limited to 4% of purchase price
    if loan_type.lower() == "va":
        # For VA loans, use a very high number instead of infinity to avoid JSON serialization issues
        return 999999999.0  # Large value instead of infinity for JSON compatibility

    # Determine max contribution percentage based on loan type and LTV
    max_contribution_pct = 0

    # Handle conventional loans with different occupancy types
    if loan_type.lower() == "conventional":
        # Map occupancy parameter to config structure
        if occupancy == "primary":
            occupancy = "primary_residence"
        elif occupancy == "second":
            occupancy = "second_home"
        elif occupancy == "investment":
            occupancy = "investment_property"

        # Get contribution limits for this occupancy type
        occupancy_limits = seller_contributions.get("conventional", {}).get(
            occupancy, []
        )

        app.logger.debug(f"Checking occupancy limits: {occupancy_limits}")
        app.logger.debug(f"Current LTV ratio: {ltv_ratio:.2f}%")

        # Find the applicable limit based on LTV
        for limit in occupancy_limits:
            ltv_range = limit.get("ltv_range", "")
            app.logger.debug(f"Checking LTV range: {ltv_range}")

            # Handle "Any LTV" case
            if ltv_range.lower() == "any ltv":
                max_contribution_pct = limit.get("max_contribution", 0)
                app.logger.debug(f"Matched 'Any LTV' range, max: {max_contribution_pct}%")
                break

            # Parse LTV range and check if current LTV falls within it
            if "≤" in ltv_range:
                # Less than or equal to
                threshold = float(ltv_range.replace("≤", "").replace("%", "").strip())
                app.logger.debug(f"Checking if {ltv_ratio:.2f}% ≤ {threshold}%")
                if ltv_ratio <= threshold:
                    max_contribution_pct = limit.get("max_contribution", 0)
                    app.logger.debug(f"Matched ≤ range, max: {max_contribution_pct}%")
                    break
            elif ">" in ltv_range:
                # Greater than
                threshold = float(ltv_range.replace(">", "").replace("%", "").strip())
                app.logger.debug(f"Checking if {ltv_ratio:.2f}% > {threshold}%")
                if ltv_ratio > threshold:
                    max_contribution_pct = limit.get("max_contribution", 0)
                    app.logger.debug(f"Matched > range, max: {max_contribution_pct}%")
                    break
            elif "-" in ltv_range:
                # Range between two values
                parts = ltv_range.replace("%", "").split("-")
                lower = float(parts[0].strip())
                upper = float(parts[1].strip())
                app.logger.debug(f"Checking if {lower}% ≤ {ltv_ratio:.2f}% ≤ {upper}%")
                if lower <= ltv_ratio <= upper:
                    max_contribution_pct = limit.get("max_contribution", 0)
                    app.logger.debug(f"Matched range {lower}%-{upper}%, max: {max_contribution_pct}%")
                    break
    else:
        # For FHA, USDA, use the all_types category
        limits = seller_contributions.get(loan_type.lower(), {}).get("all_types", [])
        if limits:
            # These typically have a single limit regardless of LTV
            max_contribution_pct = limits[0].get("max_contribution", 0)

    # Calculate maximum dollar amount
    max_contribution_amount = (max_contribution_pct / 100) * purchase_price

    app.logger.debug(
        f"Max seller contribution for {loan_type} loan with {occupancy} and {ltv_ratio:.2f}% LTV: "
        f"{max_contribution_pct:.1f}% = ${max_contribution_amount:.2f}"
    )

    return max_contribution_amount


# Add a route to calculate maximum seller contribution
@app.route('/calculate-max-seller-contribution', methods=['POST'])
def max_seller_contribution_api():
    """API endpoint to calculate the maximum allowed seller contribution"""
    try:
        # Parse input from JSON request
        data = request.get_json()
        app.logger.info(f"Max seller contribution request received: {data}")
        
        # Extract parameters
        loan_type = data.get('loan_type', 'conventional')
        purchase_price = float(data.get('purchase_price', 0))
        down_payment_amount = float(data.get('down_payment_amount', 0))
        occupancy = data.get('occupancy', 'primary_residence')
        
        app.logger.info(f"Calculating max seller contribution for: loan_type={loan_type}, purchase_price={purchase_price}, down_payment={down_payment_amount}, occupancy={occupancy}")
        
        # Calculate maximum seller contribution
        max_contribution = calculate_max_seller_contribution(
            loan_type, purchase_price, down_payment_amount, occupancy
        )
        
        app.logger.info(f"Max seller contribution calculated: {max_contribution}")
        
        # Return result as JSON
        return jsonify({
            'max_contribution': max_contribution,
            'status': 'success'
        })
    
    except Exception as e:
        app.logger.error(f"Error calculating max seller contribution: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 400


# Configure logging
app.permanent_session_lifetime = timedelta(days=5)

# Log application version on startup
try:
    from VERSION import LAST_UPDATED, VERSION

    app.logger.info(
        f"Starting Mortgage Calculator version {VERSION} (last updated: {LAST_UPDATED})"
    )
except ImportError:
    app.logger.warning("VERSION module not found, version tracking not enabled")

# Load calculator configuration
calculator = MortgageCalculator()
config_manager = ConfigManager()
config_manager.load_config()  # Load the config
config = config_manager.get_config()  # Get the loaded config

# Register admin blueprint
app.register_blueprint(admin_bp)
# Register chat blueprint
app.register_blueprint(chat_bp)
# Register beta testing blueprint
app.register_blueprint(beta_bp)
# Register health check blueprint
app.register_blueprint(health_bp)
app.config_manager = config_manager


# Main calculator route
@app.route("/", methods=["GET", "POST"])
def index():
    """Render the main calculator page."""
    app.logger.info(f"Index route accessed with method: {request.method}")

    # If it's a POST request, redirect to calculate endpoint
    if request.method == "POST":
        app.logger.warning(
            "POST request received at root route - redirecting to /calculate"
        )
        return (
            jsonify(
                {
                    "error": "Direct form submission to root URL is not supported",
                    "message": "Please use the /calculate endpoint with proper JSON data",
                }
            ),
            400,
        )

    try:
        # Get configuration limits
        limits = config.get("limits", {})

        # Default parameters
        params = {
            "purchase_price": 400000,
            "down_payment_percentage": 20,
            "annual_rate": 6.5,
            "loan_term": 30,
            "annual_tax_rate": 1.0,
            "annual_insurance_rate": 0.35,
            "loan_type": "conventional",
            "hoa_fee": 0,
            "seller_credit": 0,
            "lender_credit": 0,
            "discount_points": 0,
        }

        return render_template(
            "index.html",
            params=params,
            limits=limits,
            version=app.version,
            cache_buster=app.config["CACHE_BUSTER"]
        )
    except Exception as e:
        app.logger.error(f"Error in index route: {str(e)}")
        return f"Error rendering calculator: {str(e)}", 500


# Catch-all route to diagnose 404 issues
@app.route("/<path:path>")
def catch_all(path):
    """Catch-all route to log missing endpoints."""
    app.logger.warning(f"404 Not Found: {path}")
    return f"Page not found: /{path}. Try accessing the root URL instead.", 404


# Health check endpoint for monitoring
@app.route("/health")
def health_check():
    """Get health and version information about the application."""
    try:
        from VERSION import FEATURES, LAST_UPDATED, VERSION
    except ImportError:
        VERSION = "unknown"
        LAST_UPDATED = "unknown"
        FEATURES = []

    return jsonify(
        {
            "status": "healthy",
            "version": VERSION,
            "features": FEATURES,
            "last_updated": LAST_UPDATED,
            "environment": os.environ.get("FLASK_ENV", "development"),
            "timestamp": datetime.now().isoformat(),
        }
    )


# Main entry point
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run the Mortgage Calculator Flask app"
    )
    parser.add_argument("--port", type=int, default=8080, help="Port to run the app on")
    parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="Host to run the app on"
    )
    args = parser.parse_args()

    app.run(host=args.host, port=args.port, debug=True)
