"""Comprehensive error handling module for mortgage calculator."""

import logging
import traceback
from datetime import datetime
from typing import Any, Dict, Optional, Tuple
from flask import jsonify, request, current_app
from functools import wraps

logger = logging.getLogger(__name__)


class MortgageCalculatorError(Exception):
    """Base exception class for mortgage calculator errors."""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__.replace('Error', '').upper()
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        super().__init__(self.message)


class ValidationError(MortgageCalculatorError):
    """Exception for input validation errors."""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        self.field = field
        self.value = value
        details = {}
        if field:
            details['field'] = field
        if value is not None:
            details['invalid_value'] = str(value)
        
        super().__init__(message, 'VALIDATION_ERROR', details)


class CalculationError(MortgageCalculatorError):
    """Exception for calculation-related errors."""
    
    def __init__(self, message: str, calculation_type: str = None, parameters: Dict[str, Any] = None):
        self.calculation_type = calculation_type
        self.parameters = parameters or {}
        details = {'calculation_type': calculation_type} if calculation_type else {}
        
        super().__init__(message, 'CALCULATION_ERROR', details)


class ConfigurationError(MortgageCalculatorError):
    """Exception for configuration-related errors."""
    
    def __init__(self, message: str, config_section: str = None):
        self.config_section = config_section
        details = {'config_section': config_section} if config_section else {}
        
        super().__init__(message, 'CONFIGURATION_ERROR', details)


class BusinessLogicError(MortgageCalculatorError):
    """Exception for business logic violations."""
    
    def __init__(self, message: str, rule: str = None, context: Dict[str, Any] = None):
        self.rule = rule
        self.context = context or {}
        details = {'rule': rule, 'context': self.context} if rule else {}
        
        super().__init__(message, 'BUSINESS_LOGIC_ERROR', details)


class ExternalServiceError(MortgageCalculatorError):
    """Exception for external service failures."""
    
    def __init__(self, message: str, service: str = None, status_code: int = None):
        self.service = service
        self.status_code = status_code
        details = {}
        if service:
            details['service'] = service
        if status_code:
            details['status_code'] = status_code
        
        super().__init__(message, 'EXTERNAL_SERVICE_ERROR', details)


class ErrorHandler:
    """Centralized error handler for the mortgage calculator application."""
    
    def __init__(self, app=None):
        """Initialize the error handler."""
        self.app = app
        self.error_counts = {}
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize error handler with Flask app."""
        self.app = app
        self._register_error_handlers()
    
    def _register_error_handlers(self):
        """Register error handlers with the Flask app."""
        @self.app.errorhandler(ValidationError)
        def handle_validation_error(error):
            return self._handle_validation_error(error)
        
        @self.app.errorhandler(CalculationError)
        def handle_calculation_error(error):
            return self._handle_calculation_error(error)
        
        @self.app.errorhandler(ConfigurationError)
        def handle_configuration_error(error):
            return self._handle_configuration_error(error)
        
        @self.app.errorhandler(BusinessLogicError)
        def handle_business_logic_error(error):
            return self._handle_business_logic_error(error)
        
        @self.app.errorhandler(ExternalServiceError)
        def handle_external_service_error(error):
            return self._handle_external_service_error(error)
        
        @self.app.errorhandler(404)
        def handle_not_found(error):
            return self._handle_not_found_error(error)
        
        @self.app.errorhandler(500)
        def handle_internal_error(error):
            return self._handle_internal_server_error(error)
        
        @self.app.errorhandler(Exception)
        def handle_unexpected_error(error):
            return self._handle_unexpected_error(error)
    
    def _handle_validation_error(self, error: ValidationError) -> Tuple[Dict[str, Any], int]:
        """Handle validation errors."""
        self._log_error("Validation error", error, level=logging.WARNING)
        
        response = {
            "success": False,
            "error": {
                "type": "validation_error",
                "message": error.message,
                "code": error.error_code,
                "timestamp": error.timestamp
            }
        }
        
        if error.field:
            response["error"]["field"] = error.field
        
        if error.details:
            response["error"]["details"] = error.details
        
        return jsonify(response), 400
    
    def _handle_calculation_error(self, error: CalculationError) -> Tuple[Dict[str, Any], int]:
        """Handle calculation errors."""
        self._log_error("Calculation error", error, level=logging.ERROR)
        
        response = {
            "success": False,
            "error": {
                "type": "calculation_error",
                "message": error.message,
                "code": error.error_code,
                "timestamp": error.timestamp
            }
        }
        
        if error.calculation_type:
            response["error"]["calculation_type"] = error.calculation_type
        
        return jsonify(response), 422
    
    def _handle_configuration_error(self, error: ConfigurationError) -> Tuple[Dict[str, Any], int]:
        """Handle configuration errors."""
        self._log_error("Configuration error", error, level=logging.ERROR)
        
        response = {
            "success": False,
            "error": {
                "type": "configuration_error",
                "message": "System configuration error. Please contact support.",
                "code": error.error_code,
                "timestamp": error.timestamp
            }
        }
        
        return jsonify(response), 500
    
    def _handle_business_logic_error(self, error: BusinessLogicError) -> Tuple[Dict[str, Any], int]:
        """Handle business logic errors."""
        self._log_error("Business logic error", error, level=logging.WARNING)
        
        response = {
            "success": False,
            "error": {
                "type": "business_logic_error",
                "message": error.message,
                "code": error.error_code,
                "timestamp": error.timestamp
            }
        }
        
        if error.rule:
            response["error"]["rule"] = error.rule
        
        return jsonify(response), 422
    
    def _handle_external_service_error(self, error: ExternalServiceError) -> Tuple[Dict[str, Any], int]:
        """Handle external service errors."""
        self._log_error("External service error", error, level=logging.ERROR)
        
        response = {
            "success": False,
            "error": {
                "type": "external_service_error",
                "message": "External service temporarily unavailable. Please try again later.",
                "code": error.error_code,
                "timestamp": error.timestamp
            }
        }
        
        return jsonify(response), 503
    
    def _handle_not_found_error(self, error) -> Tuple[Dict[str, Any], int]:
        """Handle 404 errors."""
        logger.warning(f"404 error for path: {request.path}")
        
        if self._is_api_request():
            return jsonify({
                "success": False,
                "error": {
                    "type": "not_found",
                    "message": f"Endpoint '{request.path}' not found",
                    "code": "NOT_FOUND",
                    "timestamp": datetime.now().isoformat()
                }
            }), 404
        
        # For HTML requests, could return a template
        return jsonify({"error": "Page not found"}), 404
    
    def _handle_internal_server_error(self, error) -> Tuple[Dict[str, Any], int]:
        """Handle 500 errors."""
        self._log_error("Internal server error", error, level=logging.ERROR, include_traceback=True)
        
        response = {
            "success": False,
            "error": {
                "type": "internal_server_error",
                "message": "An internal server error occurred. Please try again later.",
                "code": "INTERNAL_SERVER_ERROR",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Add error ID for tracking
        error_id = self._generate_error_id()
        response["error"]["error_id"] = error_id
        logger.error(f"Error ID: {error_id}")
        
        return jsonify(response), 500
    
    def _handle_unexpected_error(self, error: Exception) -> Tuple[Dict[str, Any], int]:
        """Handle unexpected errors."""
        self._log_error("Unexpected error", error, level=logging.CRITICAL, include_traceback=True)
        
        response = {
            "success": False,
            "error": {
                "type": "unexpected_error",
                "message": "An unexpected error occurred. Please contact support.",
                "code": "UNEXPECTED_ERROR",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Add error ID for tracking
        error_id = self._generate_error_id()
        response["error"]["error_id"] = error_id
        logger.critical(f"Unexpected error ID: {error_id}")
        
        return jsonify(response), 500
    
    def _log_error(self, error_type: str, error: Exception, level: int = logging.ERROR, 
                   include_traceback: bool = False) -> None:
        """Log error with appropriate level and context."""
        # Track error counts
        error_key = f"{error_type}:{type(error).__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Build log message
        log_message = f"{error_type}: {str(error)}"
        
        # Add request context if available
        if request:
            log_message += f" | Path: {request.path} | Method: {request.method}"
            if request.remote_addr:
                log_message += f" | IP: {request.remote_addr}"
        
        # Log the error
        logger.log(level, log_message)
        
        # Add traceback for severe errors
        if include_traceback or level >= logging.ERROR:
            logger.log(level, f"Traceback: {traceback.format_exc()}")
        
        # Log error details if available
        if hasattr(error, 'details') and error.details:
            logger.log(level, f"Error details: {error.details}")
    
    def _is_api_request(self) -> bool:
        """Check if the current request is an API request."""
        return (request.path.startswith('/api/') or 
                request.path in ['/calculate', '/refinance'] or
                request.is_json or
                'application/json' in request.headers.get('Accept', ''))
    
    def _generate_error_id(self) -> str:
        """Generate a unique error ID for tracking."""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        return {
            "error_counts": self.error_counts.copy(),
            "total_errors": sum(self.error_counts.values()),
            "timestamp": datetime.now().isoformat()
        }


def handle_errors(func):
    """Decorator to wrap functions with comprehensive error handling."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError:
            # Re-raise validation errors as they should be handled by Flask
            raise
        except CalculationError:
            # Re-raise calculation errors as they should be handled by Flask
            raise
        except Exception as e:
            # Convert unexpected exceptions to CalculationError
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            raise CalculationError(
                f"Error in {func.__name__}: {str(e)}",
                calculation_type=func.__name__
            )
    
    return wrapper


def validate_request_data(required_fields: list = None, optional_fields: list = None):
    """Decorator to validate request data."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                raise ValidationError("Request must contain JSON data")
            
            data = request.get_json()
            if not data:
                raise ValidationError("Request body cannot be empty")
            
            # Check required fields
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    raise ValidationError(
                        f"Missing required fields: {', '.join(missing_fields)}"
                    )
            
            # Log received fields for debugging
            logger.debug(f"Received fields in {func.__name__}: {list(data.keys())}")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def log_performance(func):
    """Decorator to log function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        
        try:
            result = func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"{func.__name__} completed in {duration:.3f}s")
            return result
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"{func.__name__} failed after {duration:.3f}s: {str(e)}")
            raise
    
    return wrapper