"""Configuration factory for the mortgage calculator application."""
import os
import sys
import importlib.util
from security_config import SecurityConfig

# Define a base testing configuration class that inherits from SecurityConfig
class TestingConfig(SecurityConfig):
    """Testing environment configuration."""
    # Flask settings
    DEBUG = True
    TESTING = True
    
    # Database settings (using SQLite for testing)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Relaxed security settings for testing
    SESSION_COOKIE_SECURE = False  # Allow HTTP for testing
    REMEMBER_COOKIE_SECURE = False
    PREFERRED_URL_SCHEME = 'http'
    
    # Logging configuration
    LOG_FORMAT = '%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
    LOG_FILE = 'logs/testing.log'
    LOG_LEVEL = 'DEBUG'
    LOG_BACKUP_COUNT = 3
    LOG_MAX_BYTES = 5242880  # 5MB
    
    # Beta testing specific settings
    BETA_ENABLED = True
    FEEDBACK_COLLECTION_ENABLED = True
    ANALYTICS_ENABLED = True

# Create a development config that inherits from testing
class DevelopmentConfig(TestingConfig):
    """Development environment configuration."""
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dev.db'
    BETA_ENABLED = False
    LOG_FILE = 'logs/development.log'

# Import the production config if it exists
production_config_path = os.path.join(os.path.dirname(__file__), 'config', 'production.py')
if os.path.exists(production_config_path):
    spec = importlib.util.spec_from_file_location("production_config", production_config_path)
    production_config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(production_config)
    ProductionConfig = production_config.ProductionConfig
else:
    # Fallback if production config file doesn't exist
    class ProductionConfig(SecurityConfig):
        """Production environment configuration."""
        DEBUG = False
        TESTING = False
        BETA_ENABLED = False

# Configuration dictionary mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get the configuration based on environment variable."""
    env = os.environ.get('FLASK_ENV', 'default')
    return config.get(env, config['default'])
