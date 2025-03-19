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
logging.basicConfig(level=logging.INFO)
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
