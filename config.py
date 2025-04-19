import os
from datetime import timedelta


class Config:
    # Basic Flask config
    SECRET_KEY = os.environ.get("SECRET_KEY") or "your-secret-key-here"

    # Security headers
    SECURITY_HEADERS = {
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "SAMEORIGIN",
        "X-XSS-Protection": "1; mode=block",
    }

    # Session config
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Application specific config
    MAX_LOAN_AMOUNT = 10000000  # $10M maximum loan
    MIN_LOAN_AMOUNT = 1000  # $1K minimum loan
    MAX_INTEREST_RATE = 25.0  # 25% maximum interest rate
    MAX_LOAN_TERM = 40  # 40 years maximum term


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    DEBUG = False
    # In production, ensure to set a proper SECRET_KEY
    # and configure any additional production settings


# Select config based on environment
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
