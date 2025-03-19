from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_from_directory
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from datetime import timedelta
from dotenv import load_dotenv
from functools import wraps
import os
import json
import logging
from calculator import MortgageCalculator
from config_manager import ConfigManager
from forms import LoginForm
from admin_routes import admin_bp, load_closing_costs, save_closing_costs
from chat_routes import chat_bp
from datetime import datetime
from config_factory import get_config
from beta_routes import beta_bp

# Configure logging early
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Application module loading")

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Load configuration based on environment
app_config = get_config()

# Ensure proper MIME types for static files
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # During development
# Add proper MIME type handling for static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

# Apply configuration from the selected environment
app.config.from_object(app_config)
app.secret_key = os.getenv('SECRET_KEY', 'default-secret-key')
app.config['WTF_CSRF_ENABLED'] = True
CORS(app)

# Log app initialization with config details
app.logger.info(f"Flask app initialized with config: {app.config.get('ENV', 'unknown')}")

# Initialize app with environment-specific settings
if hasattr(app_config, 'init_app'):
    app_config.init_app(app)

# Make config settings available to templates
@app.context_processor
def inject_config():
    return {'config': app.config}

# Add response header to prevent caching
@app.after_request
def add_header(response):
    # Security and caching headers
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    
    # Add Content Security Policy that allows both cdn.jsdelivr.net and cdnjs.cloudflare.com
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com"
    
    # Explicitly set MIME types for static files if needed
    if 'Content-Type' not in response.headers and request.path.startswith('/static/'):
        file_ext = os.path.splitext(request.path)[1].lower()
        if file_ext == '.css':
            response.headers['Content-Type'] = 'text/css'
        elif file_ext == '.js':
            response.headers['Content-Type'] = 'text/javascript'
    
    return response

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Configure logging
app.permanent_session_lifetime = timedelta(days=5)

# Log application version on startup
try:
    from VERSION import VERSION, LAST_UPDATED
    app.logger.info(f"Starting Mortgage Calculator version {VERSION} (last updated: {LAST_UPDATED})")
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
app.config_manager = config_manager

# Main calculator route
@app.route('/')
def index():
    """Render the main calculator page."""
    app.logger.info("Index route accessed")
    try:
        # Get configuration limits
        limits = config.get('limits', {})
        
        # Default parameters
        params = {
            'purchase_price': 400000,
            'down_payment_percentage': 20,
            'annual_rate': 6.5,
            'loan_term': 30,
            'annual_tax_rate': 1.0,
            'annual_insurance_rate': 0.35,
            'credit_score': 740,
            'loan_type': 'conventional',
            'hoa_fee': 0,
            'seller_credit': 0,
            'lender_credit': 0,
            'discount_points': 0
        }
        
        return render_template('index.html', 
                            params=params, 
                            limits=limits,
                            version=getattr(app, 'version', 'Unknown'))
    except Exception as e:
        app.logger.error(f"Error in index route: {str(e)}")
        return f"Error rendering calculator: {str(e)}", 500

# Catch-all route to diagnose 404 issues
@app.route('/<path:path>')
def catch_all(path):
    """Catch-all route to log missing endpoints."""
    app.logger.warning(f"404 Not Found: {path}")
    return f"Page not found: /{path}. Try accessing the root URL instead.", 404

# Health check endpoint for monitoring
@app.route('/health')
def health_check():
    """Get health and version information about the application."""
    try:
        from VERSION import VERSION, LAST_UPDATED, FEATURES
    except ImportError:
        VERSION = "unknown"
        LAST_UPDATED = "unknown"
        FEATURES = []
    
    return jsonify({
        'status': 'healthy',
        'version': VERSION,
        'features': FEATURES,
        'last_updated': LAST_UPDATED,
        'environment': os.environ.get('FLASK_ENV', 'development'),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/calculate', methods=['POST'])
def calculate():
    """Main calculation endpoint that returns complete mortgage details."""
    try:
        data = request.get_json()
        app.logger.info(f"Received calculation request with data: {data}")
        
        # Extract parameters
        purchase_price = float(data.get('purchase_price', 0))
        down_payment_percentage = float(data.get('down_payment_percentage', 0))
        annual_rate = float(data.get('annual_rate', 0))
        loan_term = int(data.get('loan_term', 30))
        annual_tax_rate = float(data.get('annual_tax_rate', 0))
        annual_insurance_rate = float(data.get('annual_insurance_rate', 0))
        credit_score = int(data.get('credit_score', 740))
        loan_type = data.get('loan_type', 'conventional')
        monthly_hoa_fee = float(data.get('monthly_hoa_fee', 0))
        seller_credit = float(data.get('seller_credit', 0))
        lender_credit = float(data.get('lender_credit', 0))
        discount_points = float(data.get('discount_points', 0))
        
        # Get optional closing date
        closing_date_str = data.get('closing_date')
        closing_date = None
        if closing_date_str:
            try:
                # Parse ISO format date string (YYYY-MM-DD)
                closing_date = datetime.strptime(closing_date_str, '%Y-%m-%d').date()
                app.logger.info(f"Using closing date: {closing_date}")
            except Exception as e:
                app.logger.warning(f"Could not parse closing date '{closing_date_str}': {e}")
        
        # Extract specific parameters for different loan types
        va_params = {}
        if loan_type.lower() == 'va':
            app.logger.info(f"Processing VA loan with parameters: service_type={data.get('va_service_type')}, "
                            f"usage={data.get('va_usage')}, "
                            f"disability_exempt={data.get('va_disability_exempt')}")
            
            va_params = {
                'va_service_type': data.get('va_service_type', 'active'),
                'va_usage': data.get('va_usage', 'first'),
                'va_disability_exempt': data.get('va_disability_exempt', False)
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
            credit_score=credit_score,
            loan_type=loan_type,
            hoa_fee=monthly_hoa_fee,
            seller_credit=seller_credit,
            lender_credit=lender_credit,
            discount_points=discount_points,
            closing_date=closing_date,
            **va_params
        )
        
        # Calculate maximum seller contribution based on loan type and LTV
        max_seller_contribution = calculate_max_seller_contribution(
            loan_type=loan_type, 
            purchase_price=purchase_price, 
            down_payment_amount=down_payment_amount,
            occupancy=data.get('occupancy', 'primary_residence')
        )
        
        # Add max seller contribution to result
        if 'loan_details' not in result:
            result['loan_details'] = {}
        result['loan_details']['max_seller_contribution'] = max_seller_contribution
        
        # Special handling for VA loans - check prepaids and discount points against 4% limit
        if loan_type.lower() == 'va':
            # Get prepaids total from result
            prepaids_total = 0
            if 'prepaids' in result and 'total' in result['prepaids']:
                prepaids_total = result['prepaids']['total']
            
            # Get discount points from input
            discount_points_amount = 0
            if 'discount_points' in result.get('closing_costs', {}):
                discount_points_amount = result['closing_costs']['discount_points']
            
            # Calculate VA concession limit (4% of purchase price)
            va_concession_limit = 0.04 * purchase_price
            result['loan_details']['va_concession_limit'] = va_concession_limit
            
            # Calculate potential concessions (prepaids + discount points that would be covered by seller)
            potential_concessions = min(prepaids_total + discount_points_amount, seller_credit)
            result['loan_details']['potential_concessions'] = potential_concessions
            
            # Check if concessions exceed limit
            if potential_concessions > va_concession_limit:
                result['loan_details']['seller_credit_exceeds_max'] = True
                result['loan_details']['va_concessions_exceed_limit'] = True
            else:
                result['loan_details']['seller_credit_exceeds_max'] = False
                result['loan_details']['va_concessions_exceed_limit'] = False
        else:
            # For non-VA loans, check total seller credit against max contribution
            if seller_credit > max_seller_contribution:
                result['loan_details']['seller_credit_exceeds_max'] = True
            else:
                result['loan_details']['seller_credit_exceeds_max'] = False
        
        # Format the response for the frontend
        formatted_result = {
            'success': True,
            'monthly_payment': result['monthly_payment']['total'],
            'loan_amount': result['loan_details']['loan_amount'],
            'down_payment': result['loan_details']['down_payment'],
            'monthly_mortgage': result['monthly_payment']['principal_and_interest'],
            'monthly_tax': result['monthly_payment']['property_tax'],
            'monthly_insurance': result['monthly_payment']['home_insurance'],
            'monthly_pmi': result['monthly_payment']['mortgage_insurance'],
            'monthly_hoa': result['monthly_payment']['hoa_fee'],
            'closing_costs': result['closing_costs'],
            'prepaids': result['prepaid_items'],  
            'monthly_breakdown': {
                'principal_interest': result['monthly_payment']['principal_and_interest'],
                'property_tax': result['monthly_payment']['property_tax'],
                'home_insurance': result['monthly_payment']['home_insurance'],
                'mortgage_insurance': result['monthly_payment']['mortgage_insurance'],
                'hoa_fee': result['monthly_payment']['hoa_fee'],
                'total': result['monthly_payment']['total']
            },
            'loan_details': result['loan_details'],
            'credits': {
                'seller_credit': seller_credit,
                'lender_credit': lender_credit,
                'total': seller_credit + lender_credit
            },
            # Calculate total cash needed if not in the result, making sure to subtract credits
            'total_cash_needed': result.get('cash_to_close', 
                                          result['loan_details']['down_payment'] + 
                                          result['closing_costs'].get('total', 0) + 
                                          result['prepaid_items'].get('total', 0) - 
                                          (seller_credit + lender_credit))
        }
        
        return jsonify(formatted_result)
    except ValueError as e:
        app.logger.error(f"Value error in calculate: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app.logger.error(f"Error in calculate: {e}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

def calculate_max_seller_contribution(loan_type, purchase_price, down_payment_amount, occupancy='primary_residence'):
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
    seller_contributions_file = os.path.join(app.config.get('CONFIG_DIR', 'config'), 'seller_contributions.json')
    seller_contributions = {}
    
    try:
        if os.path.exists(seller_contributions_file):
            with open(seller_contributions_file, 'r') as f:
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
    if loan_type.lower() == 'va':
        # For VA loans, use a very high number instead of infinity to avoid JSON serialization issues
        return 999999999.0  # Large value instead of infinity for JSON compatibility
    
    # Determine max contribution percentage based on loan type and LTV
    max_contribution_pct = 0
    
    # Handle conventional loans with different occupancy types
    if loan_type.lower() == 'conventional':
        # Map occupancy parameter to config structure
        if occupancy == 'primary':
            occupancy = 'primary_residence'
        elif occupancy == 'second':
            occupancy = 'second_home'
        elif occupancy == 'investment':
            occupancy = 'investment_property'
        
        # Get contribution limits for this occupancy type
        occupancy_limits = seller_contributions.get('conventional', {}).get(occupancy, [])
        
        # Find the applicable limit based on LTV
        for limit in occupancy_limits:
            ltv_range = limit.get('ltv_range', '')
            
            # Parse LTV range and check if current LTV falls within it
            if '≤' in ltv_range and ltv_ratio <= float(ltv_range.replace('≤', '').replace('%', '').strip()):
                max_contribution_pct = limit.get('max_contribution', 0)
                break
            elif '>' in ltv_range and ltv_ratio > float(ltv_range.replace('>', '').replace('%', '').strip()):
                max_contribution_pct = limit.get('max_contribution', 0)
                break
            elif '-' in ltv_range:
                parts = ltv_range.replace('%', '').split('-')
                lower = float(parts[0].strip())
                upper = float(parts[1].strip())
                if lower <= ltv_ratio <= upper:
                    max_contribution_pct = limit.get('max_contribution', 0)
                    break
    else:
        # For FHA, USDA, use the all_types category
        limits = seller_contributions.get(loan_type.lower(), {}).get('all_types', [])
        if limits:
            # These typically have a single limit regardless of LTV
            max_contribution_pct = limits[0].get('max_contribution', 0)
    
    # Calculate maximum dollar amount
    max_contribution_amount = (max_contribution_pct / 100) * purchase_price
    
    app.logger.debug(f"Max seller contribution for {loan_type} loan with {occupancy} and {ltv_ratio:.2f}% LTV: "
                    f"{max_contribution_pct:.1f}% = ${max_contribution_amount:.2f}")
    
    return max_contribution_amount
