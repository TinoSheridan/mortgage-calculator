from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
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
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
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
