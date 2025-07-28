"""Flask application entry point for the Mortgage Calculator web app."""
import importlib
import logging
import os
import sys
import traceback
from datetime import datetime, timedelta

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_wtf.csrf import CSRFProtect

# Set up Python path to handle both direct running and module imports
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)
# Set MortgageCalc module for absolute imports
sys.modules["MortgageCalc"] = sys.modules["__main__"]

# Add current directory to path to ensure imports work properly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import admin_routes  # noqa: E402
import beta_routes  # noqa: E402
import health_check  # noqa: E402
from calculator import MortgageCalculator  # noqa: E402
from config_factory import get_config  # noqa: E402
from config_manager import ConfigManager  # noqa: E402

# Now that paths are set up, we can safely import local modules
from constants import TRANSACTION_TYPE  # noqa: E402
from error_handling import ValidationError, handle_errors, validate_request_data  # noqa: E402

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

        # Get and log the version number
        from VERSION import VERSION as app_version

        logger.info(f"Application version: {app_version}.")
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

logger.debug("Flask app initialization completed")

# Log at the top level to confirm app.py is loaded and what template folder is used
logger.info(f"[TOP-LEVEL] app.py loaded. Flask template_folder: {app.template_folder}")


# Load configuration based on environment
app_config = get_config()
logger.debug("Configuration loading completed")

# Ensure proper MIME types for static files
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0  # During development
logger.debug("MIME type configuration completed")


# Add proper MIME type handling for static files
@app.route("/static/<path:filename>")
def serve_static(filename):
    """Serve static files from the static directory."""
    return send_from_directory(app.static_folder, filename)


# Apply configuration from the selected environment
app.config.from_object(app_config)
# SECURITY: Fail fast if SECRET_KEY is not set - never use default fallback
secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    raise RuntimeError(
        "SECRET_KEY environment variable must be set. Never use default keys in production!"
    )
app.secret_key = secret_key
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
    # Strict-Transport-Security (HSTS) - Enable in production with HTTPS
    if app.config.get("SESSION_COOKIE_SECURE") or os.getenv("FLASK_ENV") == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

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

# Initialize error handling (temporarily disabled for debugging)
# error_handler = ErrorHandler(app)


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


# CSRF protection enabled - token must be provided in X-CSRFToken header
@app.route("/calculate", methods=["POST"])
@validate_request_data(
    required_fields=[
        "purchase_price",
        "down_payment_percentage",
        "annual_rate",
        "loan_term",
        "annual_tax_rate",
        "annual_insurance_rate",
        "loan_type",
    ]
)
@handle_errors
def calculate():
    """Perform the main calculation and return complete mortgage details."""
    app.logger.info(f"Calculate route accessed with method: {request.method}")
    data = request.get_json()
    app.logger.info(f"Received calculation request with data: {data}")

    # Extract and validate basic loan parameters
    try:
        purchase_price = float(data.get("purchase_price"))
        if purchase_price <= 0:
            raise ValidationError(
                "Purchase price must be greater than 0",
                field="purchase_price",
                value=purchase_price,
            )

        down_payment_percentage = float(data.get("down_payment_percentage"))
        if not (0 <= down_payment_percentage <= 100):
            raise ValidationError(
                "Down payment percentage must be between 0 and 100",
                field="down_payment_percentage",
                value=down_payment_percentage,
            )

        annual_rate = float(data.get("annual_rate"))
        if not (0 <= annual_rate <= 30):
            raise ValidationError(
                "Interest rate must be between 0 and 30", field="annual_rate", value=annual_rate
            )

        loan_term = int(data.get("loan_term"))
        if not (1 <= loan_term <= 50):
            raise ValidationError(
                "Loan term must be between 1 and 50 years", field="loan_term", value=loan_term
            )

        annual_tax_rate = float(data.get("annual_tax_rate"))
        if annual_tax_rate < 0:
            raise ValidationError(
                "Property tax rate cannot be negative",
                field="annual_tax_rate",
                value=annual_tax_rate,
            )

        annual_insurance_rate = float(data.get("annual_insurance_rate"))
        if annual_insurance_rate < 0:
            raise ValidationError(
                "Insurance rate cannot be negative",
                field="annual_insurance_rate",
                value=annual_insurance_rate,
            )

        # Handle tax and insurance method overrides
        tax_method = data.get("tax_method", "percentage")
        insurance_method = data.get("insurance_method", "percentage")
        annual_tax_amount = float(data.get("annual_tax_amount", 0))
        annual_insurance_amount = float(data.get("annual_insurance_amount", 0))

        if tax_method == "amount" and annual_tax_amount < 0:
            raise ValidationError(
                "Annual tax amount cannot be negative",
                field="annual_tax_amount",
                value=annual_tax_amount,
            )
        if insurance_method == "amount" and annual_insurance_amount < 0:
            raise ValidationError(
                "Annual insurance amount cannot be negative",
                field="annual_insurance_amount",
                value=annual_insurance_amount,
            )

    except (ValueError, TypeError) as e:
        raise ValidationError(f"Invalid numeric value provided: {str(e)}")

    # Parse loan_type from request
    loan_type = request.json.get("loan_type", "conventional").lower()
    app.logger.info(f"Request for loan_type: {loan_type}")

    # Use shared utility to parse transaction type (default to PURCHASE for this route)
    transaction_type_enum = parse_transaction_type(data, TRANSACTION_TYPE.PURCHASE)
    app.logger.info(f"Using transaction type: {transaction_type_enum}")

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

            app.logger.info(f"Attempting to parse closing date: '{closing_date_str}'")

            # Handle different possible date formats
            if "-" in closing_date_str:
                # ISO format: YYYY-MM-DD
                closing_date = datetime.strptime(closing_date_str, "%Y-%m-%d").date()
            elif "/" in closing_date_str:
                # US format: MM/DD/YYYY
                closing_date = datetime.strptime(closing_date_str, "%m/%d/%Y").date()
            else:
                app.logger.warning(f"Unknown date format: {closing_date_str}")

            app.logger.info(f"Successfully parsed closing date: {closing_date}")
        except Exception as e:
            app.logger.error(f"Could not parse closing date '{closing_date_str}': {str(e)}")
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
        f"Calculating with the following parameters: \n"
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
        transaction_type=TRANSACTION_TYPE.PURCHASE,  # Explicitly use enum for transaction type
        # Tax and insurance method overrides
        tax_method=tax_method,
        insurance_method=insurance_method,
        annual_tax_amount=annual_tax_amount,
        annual_insurance_amount=annual_insurance_amount,
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
        "loan_details": {
            "purchase_price": result["loan_details"].get("purchase_price"),
            "down_payment": result["loan_details"].get("down_payment"),
            "down_payment_percentage": result["loan_details"].get("down_payment_percentage"),
            "loan_amount": result["loan_details"].get("loan_amount"),
            "original_loan_amount": result["loan_details"].get("original_loan_amount"),
            "financed_fees": result["loan_details"].get("financed_fees"),
            "loan_term_years": result["loan_details"].get("loan_term_years"),
            "interest_rate": result["loan_details"].get("interest_rate"),
            "loan_type": result["loan_details"].get("loan_type"),
            "ltv_ratio": result["loan_details"].get("ltv_ratio"),
            "transaction_type": TRANSACTION_TYPE.PURCHASE.value,  # Add transaction type to response
            "max_seller_contribution": result["loan_details"].get("max_seller_contribution"),
            "seller_credit_exceeds_max": result["loan_details"].get("seller_credit_exceeds_max"),
        },
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


# API endpoint to calculate the maximum allowed seller contribution
# CSRF protection enabled - token must be provided in X-CSRFToken header
@app.route("/api/max_seller_contribution", methods=["POST"])
def max_seller_contribution_api():
    """Calculate the maximum allowed seller contribution."""
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


# --- Shared utility function for mortgage calculations ---
def parse_transaction_type(request_data, default_type=TRANSACTION_TYPE.PURCHASE):
    """
    Parse transaction_type from request data and convert to enum.

    Args:
        request_data: The JSON data from the request
        default_type: Default transaction type to use if not specified

    Returns:
        TRANSACTION_TYPE enum value
    """
    transaction_type = request_data.get("transaction_type", "").lower()
    if not transaction_type:
        transaction_type = default_type.value

    # Map the transaction_type string to enum value
    try:
        transaction_type_enum = TRANSACTION_TYPE(transaction_type)
        app.logger.info(f"Mapped transaction_type to enum: {transaction_type_enum}")
        return transaction_type_enum
    except ValueError:
        app.logger.warning(
            f"Invalid transaction_type: {transaction_type}, defaulting to {default_type}"
        )
        return default_type


# --- Add refinance calculation API endpoint ---


@app.route("/refinance", methods=["POST"])
def refinance():
    """
    Perform a refinance analysis and return results (no prepaids, just loan, closing costs, and savings).
    """
    try:
        app.logger.info(f"Refinance route accessed with method: {request.method}")
        data = request.get_json()
        app.logger.info(f"Received refinance request with data: {data}")

        # Print each key/value for debugging
        for key, value in data.items():
            app.logger.info(f"Parameter: {key} = {repr(value)} (Type: {type(value).__name__})")

        # Create a complete set of validated parameters to pass to the calculator
        validated_params = {}

        try:
            # Function to safely convert values with detailed error logging
            def validate_param(key, default_value=0, converter=float, required=False):
                value = data.get(key)
                app.logger.info(f"Processing parameter {key}: {repr(value)}")

                # Handle empty strings and None values
                if value is None or value == "" or (isinstance(value, str) and value.strip() == ""):
                    if required:
                        app.logger.warning(f"Required parameter {key} is missing or empty")
                        raise ValueError(f"Required parameter {key} is missing or empty")
                    app.logger.info(f"Using default for {key}: {default_value}")
                    return default_value

                try:
                    converted = converter(value)
                    app.logger.info(f"Converted {key}: {converted}")
                    return converted
                except Exception as e:
                    app.logger.error(f"Error converting {key}={repr(value)}: {str(e)}")
                    if required:
                        raise ValueError(f"Invalid value for {key}: {repr(value)}. Error: {str(e)}")
                    return default_value

            # Validate all parameters
            validated_params["appraised_value"] = validate_param("appraised_value", required=True)
            validated_params["original_loan_balance"] = validate_param(
                "original_loan_balance", required=True
            )
            validated_params["original_interest_rate"] = validate_param(
                "original_interest_rate", required=True
            )
            validated_params["original_loan_term"] = validate_param("original_loan_term", 30, int)
            validated_params["use_manual_balance"] = data.get("use_manual_balance", False)
            validated_params["manual_current_balance"] = validate_param(
                "manual_current_balance", 0, float
            )
            cash_option_value = data.get("cash_option", "finance_all")
            # Handle empty string as default to finance_all
            validated_params["cash_option"] = (
                cash_option_value if cash_option_value else "finance_all"
            )
            validated_params["target_ltv_value"] = validate_param("target_ltv_value", 80, float)
            validated_params["cash_back_amount"] = validate_param("cash_back_amount", 0, float)

            # Handle date with special case
            original_closing_date = data.get("original_closing_date")
            if not original_closing_date:
                original_closing_date = datetime.now().strftime("%Y-%m-%d")
                app.logger.info(f"Using today as original_closing_date: {original_closing_date}")
            validated_params["original_closing_date"] = original_closing_date

            validated_params["new_interest_rate"] = validate_param(
                "new_interest_rate", required=True
            )
            validated_params["new_loan_term"] = validate_param("new_loan_term", 30, int)

            # We no longer need to validate closing_costs or new_loan_amount
            # These will be calculated automatically by the calculator

            # Prepaid calculation parameters
            validated_params["new_closing_date"] = data.get(
                "new_closing_date", datetime.now().strftime("%Y-%m-%d")
            )
            validated_params["annual_taxes"] = validate_param("annual_taxes", required=True)
            validated_params["annual_insurance"] = validate_param("annual_insurance", required=True)
            validated_params["monthly_hoa_fee"] = validate_param("monthly_hoa_fee", 0, float)
            validated_params["extra_monthly_savings"] = validate_param(
                "extra_monthly_savings", 0, float
            )
            validated_params["refinance_lender_credit"] = validate_param(
                "refinance_lender_credit", 0, float
            )
            validated_params["tax_escrow_months"] = validate_param("tax_escrow_months", 3, int)
            validated_params["insurance_escrow_months"] = validate_param(
                "insurance_escrow_months", 2, int
            )

            # Add tax and insurance method parameters
            validated_params["tax_method"] = data.get("tax_method", "percentage")
            validated_params["insurance_method"] = data.get("insurance_method", "percentage")

            # Zero cash to close mode
            validated_params["zero_cash_to_close"] = data.get("zero_cash_to_close", False)

            # Optional parameters
            validated_params["new_discount_points"] = validate_param("new_discount_points", 0)

            # New refinance parameters
            validated_params["loan_type"] = data.get("loan_type", "conventional").lower()
            validated_params["refinance_type"] = data.get("refinance_type", "rate_term").lower()

            # Validate loan type
            valid_loan_types = ["conventional", "fha", "va", "usda"]
            if validated_params["loan_type"] not in valid_loan_types:
                raise ValueError(
                    f"Invalid loan type: {validated_params['loan_type']}. Must be one of: {valid_loan_types}"
                )

            # Validate refinance type
            valid_refinance_types = ["rate_term", "cash_out", "streamline"]
            if validated_params["refinance_type"] not in valid_refinance_types:
                raise ValueError(
                    f"Invalid refinance type: {validated_params['refinance_type']}. Must be one of: {valid_refinance_types}"
                )

            # Handle streamline refinance special cases
            if validated_params["refinance_type"] == "streamline":
                # For streamline refinances, appraisal may not be required
                if validated_params["loan_type"] in ["usda", "fha", "va"]:
                    # If no appraised value provided for streamline, use original loan balance as proxy
                    if validated_params["appraised_value"] <= 0:
                        validated_params["appraised_value"] = (
                            validated_params["original_loan_balance"] * 1.2
                        )  # Assume 20% equity

            # Remove closing costs and total closing costs parameters
            # These will be calculated automatically by the calculator
            if "closing_costs" in validated_params:
                del validated_params["closing_costs"]
            if "total_closing_costs" in validated_params:
                del validated_params["total_closing_costs"]
            if "financed_closing_costs" in validated_params:
                del validated_params["financed_closing_costs"]

            # Final validation checks
            if validated_params["appraised_value"] <= 0:
                app.logger.error("Appraised value must be > 0")
                return (
                    jsonify(
                        {"success": False, "error": "Appraised value must be greater than zero"}
                    ),
                    400,
                )

            if validated_params["original_loan_balance"] <= 0:
                app.logger.error("Original loan balance must be > 0")
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Original loan balance must be greater than zero",
                        }
                    ),
                    400,
                )

            app.logger.info(f"Final validated parameters: {validated_params}")

        except ValueError as e:
            app.logger.error(f"Parameter validation error: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 400
        except Exception as e:
            app.logger.error(f"Unexpected validation error: {str(e)}")
            app.logger.error(traceback.format_exc())
            return jsonify({"success": False, "error": f"Validation error: {str(e)}"}), 400

        # Parse transaction type (default to REFINANCE for this route)
        transaction_type_enum = parse_transaction_type(data, TRANSACTION_TYPE.REFINANCE)
        app.logger.info(f"Using transaction type: {transaction_type_enum}")

        # Calculate refinance with validated parameters
        calculator_instance = MortgageCalculator()
        try:
            app.logger.info("Calling calculate_refinance with validated parameters")
            # The transaction_type is now explicitly passed from our utility function
            result = calculator_instance.calculate_refinance(
                **validated_params, transaction_type=transaction_type_enum
            )
            app.logger.info("Refinance calculation success")

            # Add transaction_type to result for consistent frontend handling
            if "loan_details" not in result:
                result["loan_details"] = {}
            result["loan_details"]["transaction_type"] = transaction_type_enum.value
        except Exception as calc_error:
            app.logger.error(f"Error in calculate_refinance: {str(calc_error)}")
            app.logger.error(traceback.format_exc())
            return (
                jsonify({"success": False, "error": f"Calculation error: {str(calc_error)}"}),
                400,
            )

        # The closing costs are now calculated by the calculator and included in the result
        # We don't need to add any additional structure as the calculator already provides
        # detailed closing costs in the closing_costs_details field
        app.logger.info(f"Closing costs details: {result.get('closing_costs_details', {})}")

        # For backward compatibility, ensure we have a structured closing_costs field
        if "closing_costs" not in result and "total_closing_costs" in result:
            result["closing_costs"] = {
                "total": result["total_closing_costs"],
                "financed_amount": result["financed_closing_costs"],
                "cash_to_close": result["cash_to_close"],
                # Add default line items based on the closing_costs_details
                "appraisal_fee": result.get("closing_costs_details", {}).get("appraisal_fee", 675),
                "credit_report_fee": result.get("closing_costs_details", {}).get(
                    "credit_report_fee", 249
                ),
                "processing_fee": result.get("closing_costs_details", {}).get(
                    "processing_fee", 575
                ),
                "underwriting_fee": result.get("closing_costs_details", {}).get(
                    "underwriting_fee", 675
                ),
                "title_fees": result.get("closing_costs_details", {}).get(
                    "lender_title_insurance", 825
                ),
                "recording_fee": result.get("closing_costs_details", {}).get("recording_fee", 60),
                "other_fees": result.get("closing_costs_details", {}).get("other_fees", 0),
            }

        # The new_loan_amount is calculated automatically by the calculator and included in the result
        app.logger.info(
            f"new_loan_amount in response: {result.get('new_loan_amount', 'not found')}"
        )

        # Log the full result for debugging
        app.logger.info(f"Final refinance result: {result}")

        app.logger.info("Refinance calculation complete. Returning result")
        return jsonify({"success": True, "result": result})
    except Exception as e:
        app.logger.error(f"Unhandled error in refinance endpoint: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 400


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
try:
    app.register_blueprint(admin_routes.admin_bp)
    logger.debug("Admin blueprint registered successfully")
    app.register_blueprint(beta_routes.beta_bp)
    logger.debug("Beta blueprint registered successfully")
    app.register_blueprint(health_check.health_bp)
    logger.debug("Health check blueprint registered successfully")
except Exception as e:
    logger.error(f"Exception during blueprint registration: {e}")

app.config_manager = config_manager

logger.debug("Starting route definitions")


# Main calculator route
@app.route("/", methods=["GET", "POST"])
def index():
    logger.debug("Index route accessed")
    app.logger.info(f"Index route accessed with method: {request.method}")

    # Print out the template folder and absolute path for index.html for debugging
    app.logger.info(f"Flask template_folder: {app.template_folder}")
    import os

    template_abs_path = os.path.abspath(
        os.path.join(app.template_folder or "templates", "index.html")
    )
    app.logger.warning(f"[DEBUG] Attempting to render template at: {template_abs_path}")
    app.logger.info(
        f"[DEBUG] Absolute path of index.html template being rendered: {template_abs_path}"
    )

    # If it's a POST request, redirect to calculate endpoint
    if request.method == "POST":
        app.logger.warning("POST request received at root route - redirecting to /calculate")
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


# Property Intelligence API endpoint
@app.route("/api/property-intel")
def property_intel():
    """API endpoint to analyze property for financing information."""
    address = request.args.get("address", "").strip()

    if not address:
        return jsonify({"success": False, "error": "Address parameter is required"}), 400

    try:
        app.logger.info(f"Property intel API called for address: {address}")

        # Try to import property_intel_api, fall back to embedded fallback if not available
        try:
            from property_intel_api import property_intel_api

            analysis = property_intel_api.analyze_property(address)
            app.logger.info(
                f"Property analysis completed. Source links available: {list(analysis.get('sourceLinks', {}).keys())}"
            )
        except ImportError as import_error:
            app.logger.warning(
                f"property_intel_api not available, using fallback: {str(import_error)}"
            )
            analysis = get_fallback_property_data(address)
        except Exception as api_error:
            app.logger.warning(f"property_intel_api failed, using fallback: {str(api_error)}")
            analysis = get_fallback_property_data(address)

        return jsonify({"success": True, "data": analysis, "timestamp": datetime.now().isoformat()})

    except Exception as e:
        app.logger.error(f"Critical error in property intel endpoint: {str(e)}")
        import traceback

        app.logger.error(f"Traceback: {traceback.format_exc()}")

        # Even if everything fails, return basic fallback data
        fallback_data = get_fallback_property_data(address)
        return jsonify(
            {"success": True, "data": fallback_data, "timestamp": datetime.now().isoformat()}
        )


def get_fallback_property_data(address):
    """Fallback property data when property_intel_api is not available"""
    # Generate basic source links for the address
    import urllib.parse

    encoded_address = urllib.parse.quote(address)

    return {
        "address": address,
        "timestamp": datetime.now().isoformat(),
        "sourceLinks": {
            "spokeo": f"https://www.spokeo.com/property-search/{address.replace(' ', '-').replace(',', '').lower()}",
            "qpublic": "https://qpublic.net",
            "countyAssessor": "https://www.google.com/search?q=county+assessor+" + encoded_address,
            "usda": "https://eligibility.sc.egov.usda.gov/eligibility/welcomeAction.do",
            "fema": f"https://msc.fema.gov/portal/search#{encoded_address}",
            "zillow": f"https://www.zillow.com/homes/{encoded_address}_rb/",
            "realtor": f"https://www.realtor.com/realestateandhomes-search/{encoded_address}",
            "propertyShark": f"https://www.propertyshark.com/mason/Property-Search/?searchtext={encoded_address}",
            "redfin": f"https://www.redfin.com/stingray/do/location-search?location={encoded_address}",
        },
        "tax": {
            "status": "Unknown",
            "annualTax": "Unknown",
            "taxRate": "Unknown",
            "lastAssessed": "Unknown",
            "assessedValue": "Unknown",
            "message": "Manual verification required - API unavailable",
            "needsManualVerification": True,
        },
        "propertyType": {
            "type": "Unknown",
            "confidence": "Unknown",
            "details": "Unknown",
            "message": "Manual verification required - API unavailable",
            "needsManualVerification": True,
        },
        "usda": {
            "eligible": "Unknown",
            "location": "Unknown",
            "message": "Check USDA eligibility map for this address",
            "needsManualVerification": True,
        },
        "flood": {
            "zone": "Unknown",
            "risk": "Unknown",
            "message": "Check FEMA flood maps for this address",
            "needsManualVerification": True,
        },
        "hoa": {
            "hasHOA": "Unknown",
            "fees": "Unknown",
            "message": "Manual verification required - API unavailable",
            "needsManualVerification": True,
        },
        "financing": {
            "options": "Unknown",
            "restrictions": "Unknown",
            "message": "Manual verification required - API unavailable",
            "needsManualVerification": True,
        },
    }


def get_fallback_market_data():
    """Fallback market data when market_data_api is not available"""
    return {
        "mortgage_rate_30y": {
            "current": 7.15,
            "previous": 7.08,
            "change": 0.07,
            "change_direction": "up",
            "date": "2025-07-18",
        },
        "treasury_10y": {
            "current": 4.23,
            "previous": 4.18,
            "change": 0.05,
            "change_direction": "up",
            "date": "2025-07-18",
        },
        "mbs_data": {
            "spread": 2.92,
            "description": "Mortgage-Treasury Spread: 2.92%",
            "date": "2025-07-18",
        },
        "news_headlines": [
            {
                "title": "View Current Mortgage Rates & Market Analysis",
                "link": "https://www.mortgagenewsdaily.com/mortgage-rates",
                "published": "2025-07-18T10:30:00Z",
                "source": "Mortgage News Daily",
            },
            {
                "title": "Browse Housing Wire - Industry News & Updates",
                "link": "https://www.housingwire.com/",
                "published": "2025-07-18T09:15:00Z",
                "source": "Housing Wire",
            },
        ],
        "rate_trend": "rising",
        "last_updated": datetime.now().isoformat(),
        "data_sources": ["Fallback Demo Data"],
    }


# Market data API endpoint for loan officer banner
@app.route("/api/market-data")
def market_data():
    """
    API endpoint to fetch real-time market data for loan officer banner
    Returns mortgage rates, treasury yields, and related news
    """
    try:
        app.logger.info("Market data API endpoint called")

        # Try to import market_data_api, fall back to embedded fallback if not available
        try:
            from market_data_api import market_data_api

            market_summary = market_data_api.get_market_summary()
            app.logger.info(
                f"Market data retrieved from API: {len(str(market_summary))} characters"
            )
        except ImportError as import_error:
            app.logger.warning(
                f"market_data_api not available, using fallback: {str(import_error)}"
            )
            market_summary = get_fallback_market_data()
        except Exception as api_error:
            app.logger.warning(f"market_data_api failed, using fallback: {str(api_error)}")
            market_summary = get_fallback_market_data()

        return jsonify(
            {"success": True, "data": market_summary, "timestamp": datetime.now().isoformat()}
        )

    except Exception as e:
        app.logger.error(f"Critical error in market data endpoint: {str(e)}")
        import traceback

        app.logger.error(f"Traceback: {traceback.format_exc()}")

        # Even if everything fails, return basic fallback data
        fallback_data = get_fallback_market_data()
        return jsonify(
            {"success": True, "data": fallback_data, "timestamp": datetime.now().isoformat()}
        )


# Catch-all route to diagnose 404 issues
@app.route("/<path:path>")
def catch_all(path):
    app.logger.warning(f"[CATCH_ALL] 404 Not Found: /{path} (catch_all route hit!)")
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


# Print all registered routes for debugging (after all routes are defined)
with app.app_context():
    logger.info("=== REGISTERED ROUTES ===")
    for rule in app.url_map.iter_rules():
        logger.info(f"Route: {rule} -> Endpoint: {rule.endpoint} Methods: {rule.methods}")
    logger.info("=========================")

# Main entry point
if __name__ == "__main__":
    app.logger.info("Starting development server")
    app.run(debug=True, host="0.0.0.0", port=3333)
