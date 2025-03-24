"""Production configuration for the mortgage calculator application."""
import os
from datetime import timedelta
from security_config import SecurityConfig

class ProductionConfig(SecurityConfig):
    # Flask settings
    DEBUG = False
    TESTING = False
    
    # Database settings (if needed in future)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = 5
    SQLALCHEMY_POOL_TIMEOUT = 10
    SQLALCHEMY_MAX_OVERFLOW = 2
    
    # SSL/TLS settings
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = 'https'
    
    # Logging configuration
    LOG_FORMAT = '%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
    LOG_FILE = '/var/log/mortgage_calc/app.log'
    LOG_LEVEL = 'INFO'
    LOG_BACKUP_COUNT = 7
    LOG_MAX_BYTES = 10485760  # 10MB
    
    # Redis for rate limiting and session storage (if needed)
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # Additional security settings
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    SESSION_REFRESH_EACH_REQUEST = True
    
    # SSL cert paths (for production HTTPS)
    SSL_CERT_PATH = '/etc/ssl/certs/mortgage_calc.crt'
    SSL_KEY_PATH = '/etc/ssl/private/mortgage_calc.key'
    
    # Allowed hosts
    ALLOWED_HOSTS = ['mortgagecalc.example.com']  # Update with your domain
    
    # Backup configuration
    BACKUP_ENABLED = True
    BACKUP_DIR = '/var/backups/mortgage_calc'
    BACKUP_RETENTION_DAYS = 30
    
    # Monitoring settings
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    PROMETHEUS_ENABLED = True
    
    @classmethod
    def init_app(cls, app):
        """Initialize production settings."""
        super().init_app(app)
        
        # Configure logging
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Ensure log directory exists
        os.makedirs(os.path.dirname(cls.LOG_FILE), exist_ok=True)
        
        file_handler = RotatingFileHandler(
            cls.LOG_FILE,
            maxBytes=cls.LOG_MAX_BYTES,
            backupCount=cls.LOG_BACKUP_COUNT
        )
        file_handler.setFormatter(logging.Formatter(cls.LOG_FORMAT))
        file_handler.setLevel(cls.LOG_LEVEL)
        
        # Add handlers
        app.logger.addHandler(file_handler)
        app.logger.setLevel(cls.LOG_LEVEL)
        
        # Configure Sentry for error tracking
        if cls.SENTRY_DSN:
            import sentry_sdk
            from sentry_sdk.integrations.flask import FlaskIntegration
            
            sentry_sdk.init(
                dsn=cls.SENTRY_DSN,
                integrations=[FlaskIntegration()],
                traces_sample_rate=1.0
            )
        
        # Configure Prometheus monitoring
        if cls.PROMETHEUS_ENABLED:
            from prometheus_flask_exporter import PrometheusMetrics
            PrometheusMetrics(app)
