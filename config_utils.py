"""Configuration utilities for environment variable management."""

import os
import logging
import logging.handlers
from typing import Any, Dict, Optional, Union
from datetime import timedelta

logger = logging.getLogger(__name__)


class EnvironmentConfig:
    """Utility class for managing environment-based configuration."""
    
    @staticmethod
    def get_bool(key: str, default: bool = False) -> bool:
        """Get a boolean value from environment variables."""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    @staticmethod
    def get_int(key: str, default: int = 0) -> int:
        """Get an integer value from environment variables."""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            logger.warning(f"Invalid integer value for {key}, using default: {default}")
            return default
    
    @staticmethod
    def get_float(key: str, default: float = 0.0) -> float:
        """Get a float value from environment variables."""
        try:
            return float(os.getenv(key, str(default)))
        except ValueError:
            logger.warning(f"Invalid float value for {key}, using default: {default}")
            return default
    
    @staticmethod
    def get_string(key: str, default: str = "") -> str:
        """Get a string value from environment variables."""
        return os.getenv(key, default)
    
    @staticmethod
    def get_list(key: str, separator: str = ",", default: Optional[list] = None) -> list:
        """Get a list value from environment variables."""
        if default is None:
            default = []
        
        value = os.getenv(key)
        if not value:
            return default
        
        return [item.strip() for item in value.split(separator) if item.strip()]
    
    @classmethod
    def get_flask_config(cls) -> Dict[str, Any]:
        """Get Flask-specific configuration from environment variables."""
        config = {
            # Basic Flask settings
            'SECRET_KEY': cls.get_string('SECRET_KEY', 'dev-secret-key-change-in-production'),
            'FLASK_ENV': cls.get_string('FLASK_ENV', 'development'),
            'DEBUG': cls.get_bool('ENABLE_DEBUG_MODE', False),
            
            # Session configuration
            'WTF_CSRF_ENABLED': cls.get_bool('WTF_CSRF_ENABLED', True),
            'SESSION_TYPE': cls.get_string('SESSION_TYPE', 'filesystem'),
            'SESSION_PERMANENT': cls.get_bool('SESSION_PERMANENT', True),
            'SESSION_USE_SIGNER': cls.get_bool('SESSION_USE_SIGNER', True),
            'PERMANENT_SESSION_LIFETIME': timedelta(
                days=cls.get_int('SESSION_LIFETIME_DAYS', 7)
            ),
            
            # File upload settings (for future use)
            'MAX_CONTENT_LENGTH': cls.get_int('MAX_CONTENT_LENGTH', 16 * 1024 * 1024),  # 16MB
            'UPLOAD_FOLDER': cls.get_string('UPLOAD_FOLDER', 'uploads'),
            
            # Cache settings
            'SEND_FILE_MAX_AGE_DEFAULT': 0 if cls.get_string('FLASK_ENV') == 'development' else 43200,
        }
        
        # Conditional configuration based on environment
        if cls.get_string('FLASK_ENV') == 'production':
            config.update({
                'SESSION_COOKIE_SECURE': True,
                'SESSION_COOKIE_HTTPONLY': True,
                'SESSION_COOKIE_SAMESITE': 'Lax',
            })
        
        return config
    
    @classmethod
    def get_security_headers(cls) -> Dict[str, str]:
        """Get security headers configuration."""
        return {
            'Content-Security-Policy': cls.get_string(
                'CONTENT_SECURITY_POLICY',
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self'"
            ),
            'X-Frame-Options': cls.get_string('X_FRAME_OPTIONS', 'DENY'),
            'X-Content-Type-Options': cls.get_string('X_CONTENT_TYPE_OPTIONS', 'nosniff'),
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': cls.get_string('REFERRER_POLICY', 'strict-origin-when-cross-origin'),
        }
    
    @classmethod
    def get_logging_config(cls) -> Dict[str, Any]:
        """Get logging configuration."""
        return {
            'level': cls.get_string('LOG_LEVEL', 'INFO').upper(),
            'format': cls.get_string(
                'LOG_FORMAT', 
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ),
            'filename': cls.get_string('LOG_FILE', 'logs/app.log'),
            'max_bytes': cls.get_int('LOG_MAX_BYTES', 10 * 1024 * 1024),  # 10MB
            'backup_count': cls.get_int('LOG_BACKUP_COUNT', 5),
        }
    
    @classmethod
    def get_calculation_limits(cls) -> Dict[str, Dict[str, Union[int, float]]]:
        """Get calculation limits configuration."""
        return {
            'purchase_price': {
                'min': cls.get_int('MIN_PURCHASE_PRICE', 10000),
                'max': cls.get_int('MAX_PURCHASE_PRICE', 50000000)
            },
            'loan_term': {
                'min': cls.get_int('MIN_LOAN_TERM', 1),
                'max': cls.get_int('MAX_LOAN_TERM', 50)
            },
            'interest_rate': {
                'min': cls.get_float('MIN_INTEREST_RATE', 0.0),
                'max': cls.get_float('MAX_INTEREST_RATE', 30.0)
            }
        }
    
    @classmethod
    def get_application_info(cls) -> Dict[str, str]:
        """Get application information."""
        return {
            'name': cls.get_string('APP_NAME', 'Enhanced Mortgage Calculator'),
            'version': cls.get_string('APP_VERSION', '2.0.1'),
            'environment': cls.get_string('FLASK_ENV', 'development'),
        }
    
    @classmethod
    def get_feature_flags(cls) -> Dict[str, bool]:
        """Get feature flag configuration."""
        return {
            'beta_enabled': cls.get_bool('BETA_ENABLED', False),
            'feedback_collection_enabled': cls.get_bool('FEEDBACK_COLLECTION_ENABLED', False),
            'analytics_enabled': cls.get_bool('ANALYTICS_ENABLED', False),
            'profiling_enabled': cls.get_bool('ENABLE_PROFILING', False),
            'backup_enabled': cls.get_bool('BACKUP_ENABLED', True),
        }
    
    @classmethod
    def validate_configuration(cls) -> Dict[str, Any]:
        """Validate the current configuration and return status."""
        issues = []
        warnings = []
        
        # Check for production settings
        if cls.get_string('FLASK_ENV') == 'production':
            secret_key = cls.get_string('SECRET_KEY')
            if secret_key in ['dev-secret-key-change-in-production', 'your-secret-key-here-change-in-production']:
                issues.append("SECRET_KEY is using default value in production")
            
            if not cls.get_bool('WTF_CSRF_ENABLED'):
                warnings.append("CSRF protection is disabled in production")
        
        # Check logging configuration
        log_file = cls.get_string('LOG_FILE')
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
            except OSError:
                issues.append(f"Cannot create log directory: {log_dir}")
        
        # Check calculation limits
        limits = cls.get_calculation_limits()
        for limit_type, limit_values in limits.items():
            if limit_values['min'] >= limit_values['max']:
                issues.append(f"Invalid {limit_type} limits: min >= max")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'summary': f"Configuration validation: {len(issues)} issues, {len(warnings)} warnings"
        }


def setup_logging_from_env() -> None:
    """Set up logging based on environment configuration."""
    config = EnvironmentConfig.get_logging_config()
    
    # Create log directory if it doesn't exist
    log_file = config['filename']
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # Convert string level to logging constant
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    log_level = level_map.get(config['level'], logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=config['format'],
        handlers=[
            logging.StreamHandler(),  # Console output
            logging.handlers.RotatingFileHandler(
                config['filename'],
                maxBytes=config['max_bytes'],
                backupCount=config['backup_count']
            ) if log_file else logging.NullHandler()
        ]
    )
    
    logger.info(f"Logging configured: level={config['level']}, file={config['filename']}")


# Module-level configuration validation on import
if __name__ != '__main__':
    validation_result = EnvironmentConfig.validate_configuration()
    if not validation_result['valid']:
        logger.warning(f"Configuration issues detected: {validation_result['summary']}")
        for issue in validation_result['issues']:
            logger.error(f"Config issue: {issue}")
        for warning in validation_result['warnings']:
            logger.warning(f"Config warning: {warning}")