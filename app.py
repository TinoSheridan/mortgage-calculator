"""Flask application entry point for the Mortgage Calculator web app."""
import importlib
import logging
import os
import sys
from datetime import datetime, timedelta

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_wtf.csrf import CSRFProtect

from admin_routes import admin_bp
from beta_routes import beta_bp
from calculator import MortgageCalculator
from chat_routes import chat_bp
from config_factory import get_config
from config_manager import ConfigManager
from health_check import health_bp

# Configure logging early
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Application module loading")


def force_reload_version():
    """Force reload the VERSION module to get the latest version info."""
    try:
        # Clear any cached version module
        if "VERSION" in sys.modules:
            logger.info("Reloading VERSION module to ensure correct version")
            importlib.reload(sys.modules["VERSION"])
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
app.config[
    "CACHE_BUSTER"
] = f"{current_version}.{cache_timestamp}"  # Create cache buster string

# Load configuration based on environment
app_config = get_config()

# Ensure proper MIME types for static files
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0  # During development


# Add proper MIME type handling for static files
@app.route("/static/<path:filename>")
def serve_static(filename):
    """Serve static files from the static directory."""
    return send_from_directory(app.static_folder, filename)


# Apply configuration from the selected environment
app.config.from_object(app_config)
app.secret_key = os.getenv("SECRET_KEY", "default-secret-key")
app.config["WTF_CSRF_ENABLED"] = True  # Re-enabled CSRF protection
app.config["SESSION_TYPE"] = "filesystem"  # Use filesystem sessions for persistence
app.config["SESSION_PERMANENT"] = True  # Make sessions permanent by default
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)  # Longer session lifetime
app.config["SESSION_USE_SIGNER"] = True  # Add a signer for security
app.config["SESSION_FILE_DIR"] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "flask_session"
)
os.makedirs(app.config["SESSION_FILE_DIR"], exist_ok=True)


# Add response header to prevent caching
@app.after_request
def add_header(response):
    """Add CORS and security headers to the response."""
    # Skip adding headers for static files to avoid conflicts
    if request.path.startswith("/static/") or request.path.startswith("/favicon.ico"):
        logger.debug(f"Skipping headers for static path: {request.path}")
        return response

    # Security Headers
    # Strict-Transport-Security (HSTS) - Only enable if using HTTPS
    # if app.config.get('SESSION_COOKIE_SECURE'):
    #     response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    # Content Security Policy (CSP)
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src-elem 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "  # Allow Font Awesome
        "img-src 'self' data: https:; "
        "font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "  # Allow Font Awesome
        "connect-src 'self'"
    )
    response.headers["Content-Security-Policy"] = csp_policy
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers[
        "X-Frame-Options"
    ] = "DENY"  # Changed from SAMEORIGIN for better security unless framing needed
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers[
        "Referrer-Policy"
    ] = "strict-origin-when-cross-origin"  # Recommended modern policy

    # Cache-Control Headers
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"  # For HTTP/1.0 compatibility
    response.headers["Expires"] = "0"  # Proxies

    # Conditionally add CORS header for API routes
    if request.path.startswith("/api/"):
        response.headers[
            "Access-Control-Allow-Origin"
        ] = "*"  # Adjust as needed for specific origins

    return response


# Initialize CSRF protection after CORS initialization
csrf = CSRFProtect(app)


# Exempt specific routes from CSRF protection
# Note: Be careful with CSRF exemptions as they can introduce security vulnerabilities
# Only exempt endpoints that absolutely require it (e.g., API endpoints used by third-party services)
@app.after_request
def csrf_exempt_admin_routes(response):
    """Exclude specific admin endpoints from CSRF protection for AJAX requests."""
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
        app.logger.info(f"Calculate route accessed with method: {request.method}")
        data = request.get_json()
        app.logger.info(f"Received calculation request with data: {data}")

        # Extract basic loan parameters
        purchase_price = float(data.get("purchase_price"))
        down_payment_percentage = float(data.get("down_payment_percentage"))
        annual_rate = float(data.get("annual_rate"))
        loan_term = int(data.get("loan_term"))
        annual_tax_rate = float(data.get("annual_tax_rate"))
        annual_insurance_rate = float(data.get("annual_insurance_rate"))
        loan_type = data.get("loan_type", "conventional")
        monthly_hoa_fee = float(data.get("monthly_hoa_fee", 0))
        seller_credit = float(data.get("seller_credit", 0))
        lender_credit = float(data.get("lender_credit", 0))
        discount_points = float(data.get("discount_points", 0))

        # Get title insurance preferences
        include_owners_title_val = data.get("include_owners_title", "true")
        # Convert string "true"/"false" to Python boolean - handle various formats
        if isinstance(include_owners_title_val, bool):
            include_owners_title = include_owners_title_val
        else:
            include_owners_title = str(include_owners_title_val).lower() in [
                "true",
                "yes",
                "1",
            ]

        app.logger.info(
            f"Include owner's title insurance: {include_owners_title} (from value: {include_owners_title_val})"
        )

        # Get optional closing date
        closing_date_str = data.get("closing_date")
        closing_date = None
        if closing_date_str:
            try:
                # Parse ISO format date string (YYYY-MM-DD)
                from datetime import datetime

                app.logger.info(
                    f"Attempting to parse closing date: '{closing_date_str}'"
                )

                # Handle different possible date formats
                if "-" in closing_date_str:
                    # ISO format: YYYY-MM-DD
                    closing_date = datetime.strptime(
                        closing_date_str, "%Y-%m-%d"
                    ).date()
                elif "/" in closing_date_str:
                    # US format: MM/DD/YYYY
                    closing_date = datetime.strptime(
                        closing_date_str, "%m/%d/%Y"
                    ).date()
                else:
                    app.logger.warning(f"Unknown date format: {closing_date_str}")

                app.logger.info(f"Successfully parsed closing date: {closing_date}")
            except Exception as e:
                app.logger.error(
                    f"Could not parse closing date '{closing_date_str}': {str(e)}"
                )
                # Don't set closing date if parsing fails
                closing_date = None

        # Extract specific parameters for different loan types
        va_params = {}
        if loan_type.lower() == "va":
            app.logger.info(
                f"Processing VA loan with parameters: service_type={data.get('va_service_type')}, "
                f"usage={data.get('va_usage')}, "
                f"disability_exempt={data.get('va_disability_exempt')}"
            )

            # Get VA disability exempt value and convert from string to boolean if needed
            va_disability_exempt_val = data.get("va_disability_exempt", False)
            if isinstance(va_disability_exempt_val, bool):
                va_disability_exempt = va_disability_exempt_val
            else:
                va_disability_exempt = str(va_disability_exempt_val).lower() in [
                    "true",
                    "yes",
                    "1",
                ]

            app.logger.info(
                f"VA disability exempt: {va_disability_exempt} (from value: {va_disability_exempt_val})"
            )

            va_params = {
                "va_service_type": data.get("va_service_type", "active"),
                "va_usage": data.get("va_usage", "first"),
                "va_disability_exempt": va_disability_exempt,
            }

        # Create a fresh calculator instance with latest config
        calculator_instance = MortgageCalculator()
        calculator_instance.config_manager.load_config()
        calculator_instance.config = calculator_instance.config_manager.get_config()
        app.logger.info("Using freshly loaded configuration for main calculation")

        # Log all parameters before calculation
        app.logger.info(
            f"Calculating with the following parameters:\n"
            f"Purchase price: ${purchase_price:,.2f}\n"
            f"Down payment: {down_payment_percentage}%\n"
            f"Interest rate: {annual_rate}%\n"
            f"Loan term: {loan_term} years\n"
            f"Loan type: {loan_type}\n"
            f"Property tax rate: {annual_tax_rate}%\n"
            f"Insurance rate: {annual_insurance_rate}%\n"
            f"HOA fee: ${monthly_hoa_fee}/mo\n"
            f"Closing date: {closing_date}\n"
            f"VA parameters: {va_params}\n"
            f"Include owner's title: {include_owners_title}\n"
            f"Seller credit: ${seller_credit}\n"
            f"Lender credit: ${lender_credit}\n"
            f"Discount points: {discount_points}%"
        )

        # Use calculator_instance to perform all calculations
        result = calculator_instance.calculate_all(
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
            closing_date=closing_date,  # Make sure this is passed
            include_owners_title=include_owners_title,
            discount_points=discount_points,  # Pass discount points
            **va_params,  # Pass VA-specific parameters if applicable
        )

        # Format the response for the frontend
        # Build the response
        formatted_result = {
            "success": True,
            "monthly_payment": result["monthly_breakdown"]["total"],
            "loan_amount": result["loan_details"]["loan_amount"],
            "down_payment": result["loan_details"]["down_payment"],
            "monthly_mortgage": result["monthly_breakdown"]["principal_interest"],
            "monthly_tax": result["monthly_breakdown"]["property_tax"],
            "monthly_insurance": result["monthly_breakdown"]["insurance"],
            "monthly_pmi": result["monthly_breakdown"]["pmi"],
            "monthly_hoa": result["monthly_breakdown"]["hoa"],
            "closing_costs": result["closing_costs"],
            "prepaids": result["prepaid_items"],
            "monthly_breakdown": {
                "principal_interest": result["monthly_breakdown"]["principal_interest"],
                "property_tax": result["monthly_breakdown"]["property_tax"],
                "home_insurance": result["monthly_breakdown"]["insurance"],
                "mortgage_insurance": result["monthly_breakdown"]["pmi"],
                "hoa_fee": result["monthly_breakdown"]["hoa"],
                "total": result["monthly_breakdown"]["total"],
            },
            "loan_details": result["loan_details"],
            "credits": {
                "seller_credit": seller_credit,
                "lender_credit": lender_credit,
                "total": round(seller_credit + lender_credit, 2),
            },
            # Calculate total cash needed if not in the result, making sure to subtract all credits
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
        # Add extensive error debugging
        import traceback

        app.logger.error(f"DEBUG: Exception type: {type(e).__name__}")
        app.logger.error(f"DEBUG: Exception traceback: {traceback.format_exc()}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


# API endpoint to calculate the maximum allowed seller contribution
@app.route("/api/max_seller_contribution", methods=["POST"])
@csrf.exempt
def max_seller_contribution_api():
    """API endpoint to calculate the maximum allowed seller contribution"""
    try:
        data = request.get_json()
        loan_type = data.get("loan_type")
        purchase_price = float(data.get("purchase_price"))
        down_payment_amount = float(data.get("down_payment_amount"))
        # Calculate LTV
        loan_amount = purchase_price - down_payment_amount
        ltv_ratio = (loan_amount / purchase_price) * 100
        # Use MortgageCalculator method
        calculator_instance = MortgageCalculator()
        max_contribution = calculator_instance._calculate_max_seller_contribution(
            loan_type, ltv_ratio, purchase_price
        )
        return jsonify({"max_seller_contribution": max_contribution})
    except Exception as e:
        app.logger.error(f"Error calculating max seller contribution: {str(e)}")
        return jsonify({"error": str(e)}), 400


# Configure logging
app.permanent_session_lifetime = timedelta(days=5)

# Log application version on startup
try:
    from VERSION import LAST_UPDATED

    app.logger.info(
        f"Starting Mortgage Calculator version {current_version} (last updated: {LAST_UPDATED})"
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

        # Explicitly fetch the latest version right before rendering
        latest_version = force_reload_version()
        # Update cache buster based on potentially reloaded version
        latest_cache_buster = f"{latest_version}.{int(datetime.now().timestamp())}"

        return render_template(
            "index.html",
            params=params,
            limits=limits,
            version=latest_version,  # Use the freshly loaded version
            cache_buster=latest_cache_buster,  # Use updated cache buster
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
        from VERSION import FEATURES, LAST_UPDATED

        return jsonify(
            {
                "status": "healthy",
                "version": current_version,
                "features": FEATURES,
                "last_updated": LAST_UPDATED,
                "environment": os.environ.get("FLASK_ENV", "development"),
                "timestamp": datetime.now().isoformat(),
            }
        )
    except ImportError:
        return jsonify(
            {
                "status": "healthy",
                "version": current_version,
                "features": [],
                "last_updated": "unknown",
                "environment": os.environ.get("FLASK_ENV", "development"),
                "timestamp": datetime.now().isoformat(),
            }
        )


# Main entry point
if __name__ == "__main__":
    app.logger.info("Starting development server")
    app.run(debug=True, host="0.0.0.0", port=3333)
