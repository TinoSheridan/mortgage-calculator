"""Refactored Flask application entry point for the Mortgage Calculator web app."""

import importlib
import logging
import os
import sys
import traceback
from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

# Set up Python path to handle both direct running and module imports
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

# Add current directory to path to ensure imports work properly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import new modules
from config_utils import EnvironmentConfig, setup_logging_from_env
from services import MortgageCalculationService, ConfigurationService
from validation import ValidationError
from constants import TRANSACTION_TYPE
from config_factory import get_config
from config_manager import ConfigManager
import admin_routes
import beta_routes
import chat_routes
import health_check

# Set up logging from environment
setup_logging_from_env()
logger = logging.getLogger(__name__)
logger.info("Application module loading")


class MortgageCalculatorApp:
    """Main application class for the Mortgage Calculator."""
    
    def __init__(self):
        """Initialize the application."""
        self.app = None
        self.calculation_service = None
        self.config_service = None
        self.config_manager = None
        self.current_version = None
        self._setup_application()
    
    def _setup_application(self) -> None:
        """Set up the Flask application and services."""
        # Load environment variables
        load_dotenv()
        
        # Get version information
        self.current_version = self._load_version_info()
        
        # Initialize Flask app
        self.app = Flask(__name__)
        self._configure_flask_app()
        
        # Initialize services
        self.config_manager = ConfigManager()
        self.calculation_service = MortgageCalculationService()
        self.config_service = ConfigurationService(self.config_manager)
        
        # Set up routes and middleware
        self._setup_middleware()
        self._register_blueprints()
        self._register_routes()
        
        logger.info(f"Mortgage Calculator v{self.current_version} initialized successfully")
    
    def _load_version_info(self) -> str:
        """Load version information from VERSION module."""
        try:
            # Clear any cached version module
            if "VERSION" in sys.modules:
                logger.info("Reloading VERSION module to ensure correct version")
                importlib.reload(sys.modules["VERSION"])
            
            from VERSION import VERSION as app_version
            logger.info(f"Application version: {app_version}")
            return app_version
        except Exception as e:
            logger.error(f"Error loading version information: {str(e)}")
            return "unknown"
    
    def _configure_flask_app(self) -> None:
        """Configure Flask application settings."""
        # Basic app configuration
        self.app.version = self.current_version
        self.app.config["VERSION"] = self.current_version
        self.app.config["CACHE_BUSTER"] = f"{self.current_version}.{int(datetime.now().timestamp())}"
        
        # Load environment-based configuration
        flask_config = EnvironmentConfig.get_flask_config()
        self.app.config.update(flask_config)
        
        # Load traditional config for backward compatibility
        app_config = get_config()
        self.app.config.from_object(app_config)
        
        # Session configuration
        session_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flask_session")
        os.makedirs(session_dir, exist_ok=True)
        self.app.config["SESSION_FILE_DIR"] = session_dir
        
        logger.info("Flask application configured")
    
    def _setup_middleware(self) -> None:
        """Set up middleware and request/response handlers."""
        # Initialize CSRF protection
        self.csrf = CSRFProtect(self.app)
        
        # Security headers middleware
        @self.app.after_request
        def add_security_headers(response):
            return self._add_security_headers(response)
        
        # CSRF exemptions for specific routes
        @self.app.after_request
        def handle_csrf_exemptions(response):
            return self._handle_csrf_exemptions(response)
        
        # Error handlers
        self._setup_error_handlers()
        
        logger.info("Middleware configured")
    
    def _add_security_headers(self, response):
        """Add security headers to responses."""
        # Skip headers for static files
        if request.path.startswith("/static/") or request.path.startswith("/favicon.ico"):
            return response
        
        # Get security headers from environment config
        security_headers = EnvironmentConfig.get_security_headers()
        
        for header, value in security_headers.items():
            response.headers[header] = value
        
        # Cache control headers
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        
        # CORS headers for API routes
        if request.path.startswith("/api/"):
            response.headers["Access-Control-Allow-Origin"] = "*"
        
        return response
    
    def _handle_csrf_exemptions(self, response):
        """Handle CSRF exemptions for specific admin routes."""
        csrf_exempt_paths = [
            "/admin/closing-costs/",
            "/admin/pmi-rates/update"
        ]
        
        if any(request.path.startswith(path) for path in csrf_exempt_paths):
            if request.method in ["POST", "PUT", "DELETE"]:
                # Remove some headers for AJAX requests
                headers_to_remove = ["X-Frame-Options", "Content-Security-Policy", "X-Content-Type-Options"]
                for header in headers_to_remove:
                    response.headers.pop(header, None)
        
        return response
    
    def _setup_error_handlers(self) -> None:
        """Set up error handlers for the application."""
        @self.app.errorhandler(ValidationError)
        def handle_validation_error(e):
            logger.warning(f"Validation error: {e.message}")
            return jsonify({
                "success": False,
                "error": e.message,
                "field": e.field,
                "type": "validation_error"
            }), 400
        
        @self.app.errorhandler(404)
        def handle_not_found(e):
            logger.warning(f"404 error for path: {request.path}")
            if request.path.startswith("/api/"):
                return jsonify({"error": "Endpoint not found"}), 404
            return render_template("404.html"), 404
        
        @self.app.errorhandler(500)
        def handle_internal_error(e):
            logger.error(f"Internal server error: {str(e)}")
            logger.error(traceback.format_exc())
            if request.path.startswith("/api/"):
                return jsonify({"error": "Internal server error"}), 500
            return render_template("500.html"), 500
    
    def _register_blueprints(self) -> None:
        """Register Flask blueprints."""
        try:
            self.app.register_blueprint(admin_routes.admin_bp)
            self.app.register_blueprint(beta_routes.beta_bp)
            self.app.register_blueprint(chat_routes.chat_bp)
            self.app.register_blueprint(health_check.health_bp)
            logger.info("Blueprints registered successfully")
        except Exception as e:
            logger.error(f"Error registering blueprints: {e}")
            raise
    
    def _register_routes(self) -> None:
        """Register application routes."""
        # Main routes
        self.app.add_url_rule("/", "index", self.index, methods=["GET", "POST"])
        self.app.add_url_rule("/health", "health_check", self.health_check, methods=["GET"])
        
        # API routes with CSRF exemption
        calculate_view = self.csrf.exempt(self.calculate)
        refinance_view = self.csrf.exempt(self.refinance) 
        max_seller_view = self.csrf.exempt(self.max_seller_contribution_api)
        
        self.app.add_url_rule("/calculate", "calculate", calculate_view, methods=["POST"])
        self.app.add_url_rule("/refinance", "refinance", refinance_view, methods=["POST"])
        self.app.add_url_rule("/api/max_seller_contribution", "max_seller_contribution", 
                             max_seller_view, methods=["POST"])
        
        # Static file route
        self.app.add_url_rule("/static/<path:filename>", "serve_static", self.serve_static)
        
        # Catch-all route
        self.app.add_url_rule("/<path:path>", "catch_all", self.catch_all)
        
        logger.info("Routes registered successfully")
    
    # Route handlers
    def index(self):
        """Main calculator route."""
        logger.info(f"Index route accessed with method: {request.method}")
        
        if request.method == "POST":
            logger.warning("POST request received at root route - redirecting to /calculate")
            return jsonify({
                "error": "Direct form submission to root URL is not supported",
                "message": "Please use the /calculate endpoint with proper JSON data",
            }), 400
        
        try:
            # Get default parameters from service
            params = self.config_service.get_default_parameters()
            
            # Get version info
            latest_version = self._load_version_info()
            latest_cache_buster = f"{latest_version}.{int(datetime.now().timestamp())}"
            
            return render_template(
                "index.html",
                params=params,
                limits=params.get("limits", {}),
                version=latest_version,
                cache_buster=latest_cache_buster,
            )
        except Exception as e:
            logger.error(f"Error in index route: {str(e)}")
            return f"Error rendering calculator: {str(e)}", 500
    
    def calculate(self):
        """Handle purchase mortgage calculations."""
        try:
            logger.info("Purchase calculation endpoint accessed")
            
            data = request.get_json()
            if not data:
                raise ValidationError("No JSON data provided")
            
            logger.info(f"Received calculation request: {list(data.keys())}")
            
            # Use service to handle calculation
            result = self.calculation_service.calculate_purchase_mortgage(data)
            
            logger.info("Purchase calculation completed successfully")
            return jsonify(result)
            
        except ValidationError as e:
            logger.warning(f"Validation error in calculate: {e.message}")
            return jsonify({
                "success": False,
                "error": e.message,
                "field": getattr(e, 'field', None)
            }), 400
        except Exception as e:
            logger.error(f"Error in calculate endpoint: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                "success": False,
                "error": f"Calculation failed: {str(e)}"
            }), 500
    
    def refinance(self):
        """Handle refinance mortgage calculations."""
        try:
            logger.info("Refinance calculation endpoint accessed")
            
            data = request.get_json()
            if not data:
                raise ValidationError("No JSON data provided")
            
            logger.info(f"Received refinance request: {list(data.keys())}")
            
            # Use service to handle calculation
            result = self.calculation_service.calculate_refinance_mortgage(data)
            
            logger.info("Refinance calculation completed successfully")
            return jsonify(result)
            
        except ValidationError as e:
            logger.warning(f"Validation error in refinance: {e.message}")
            return jsonify({
                "success": False,
                "error": e.message,
                "field": getattr(e, 'field', None)
            }), 400
        except Exception as e:
            logger.error(f"Error in refinance endpoint: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                "success": False,
                "error": f"Refinance calculation failed: {str(e)}"
            }), 500
    
    def max_seller_contribution_api(self):
        """Calculate maximum allowed seller contribution."""
        try:
            logger.info("Max seller contribution API accessed")
            
            data = request.get_json()
            if not data:
                raise ValidationError("No JSON data provided")
            
            result = self.calculation_service.calculate_max_seller_contribution(data)
            return jsonify(result)
            
        except ValidationError as e:
            logger.warning(f"Validation error in max seller contribution: {e.message}")
            return jsonify({"error": e.message}), 400
        except Exception as e:
            logger.error(f"Error in max seller contribution API: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    def health_check(self):
        """Health check endpoint."""
        try:
            app_info = EnvironmentConfig.get_application_info()
            feature_flags = EnvironmentConfig.get_feature_flags()
            
            return jsonify({
                "status": "healthy",
                "version": self.current_version,
                "environment": app_info["environment"],
                "features": feature_flags,
                "timestamp": datetime.now().isoformat(),
            })
        except Exception as e:
            logger.error(f"Error in health check: {str(e)}")
            return jsonify({
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }), 500
    
    def serve_static(self, filename):
        """Serve static files from the static directory."""
        return send_from_directory(self.app.static_folder, filename)
    
    def catch_all(self, path):
        """Catch-all route for unmatched paths."""
        logger.warning(f"404 Not Found: /{path}")
        return jsonify({"error": f"Page not found: /{path}"}), 404
    
    def get_app(self) -> Flask:
        """Get the Flask application instance."""
        return self.app


# Create application instance
mortgage_app = MortgageCalculatorApp()
app = mortgage_app.get_app()

# Add shared utility for transaction type parsing (backward compatibility)
def parse_transaction_type(request_data, default_type=TRANSACTION_TYPE.PURCHASE):
    """Parse transaction_type from request data and convert to enum."""
    transaction_type = request_data.get('transaction_type', '').lower()
    if not transaction_type:
        transaction_type = default_type.value
    
    try:
        transaction_type_enum = TRANSACTION_TYPE(transaction_type)
        logger.info(f"Mapped transaction_type to enum: {transaction_type_enum}")
        return transaction_type_enum
    except ValueError:
        logger.warning(f"Invalid transaction_type: {transaction_type}, defaulting to {default_type}")
        return default_type


# Store services in app context for access by blueprints
app.config_manager = mortgage_app.config_manager
app.calculation_service = mortgage_app.calculation_service
app.config_service = mortgage_app.config_service

# Log all registered routes for debugging
with app.app_context():
    logger.info("=== REGISTERED ROUTES ===")
    for rule in app.url_map.iter_rules():
        logger.info(f"Route: {rule} -> Endpoint: {rule.endpoint} Methods: {rule.methods}")
    logger.info("=========================")

# Main entry point
if __name__ == "__main__":
    logger.info("Starting development server")
    app.run(debug=EnvironmentConfig.get_bool('ENABLE_DEBUG_MODE', True), host="0.0.0.0", port=3333)