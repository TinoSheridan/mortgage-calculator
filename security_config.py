"""Security configuration for the mortgage calculator application."""
import os
from datetime import timedelta

class SecurityConfig:
    # Basic security settings
    CSRF_ENABLED = True
    CSRF_TIME_LIMIT = 3600  # 1 hour
    CSRF_SSL_STRICT = True
    
    # Session settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    SESSION_REFRESH_EACH_REQUEST = True
    
    # Password policy
    MIN_PASSWORD_LENGTH = 12
    PASSWORD_REQUIRE_UPPER = True
    PASSWORD_REQUIRE_LOWER = True
    PASSWORD_REQUIRE_DIGIT = True
    PASSWORD_REQUIRE_SPECIAL = True
    
    # Rate limiting
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_TIME = 300  # 5 minutes
    
    # Content Security Policy
    CSP = {
        'default-src': "'self'",
        'script-src': [
            "'self'",
            "'unsafe-inline'",
            "https://cdn.jsdelivr.net"
        ],
        'style-src': [
            "'self'",
            "'unsafe-inline'",
            "https://cdn.jsdelivr.net"
        ],
        'img-src': [
            "'self'",
            "data:",
            "https:"
        ],
        'font-src': [
            "'self'",
            "https://cdn.jsdelivr.net"
        ],
        'connect-src': "'self'"
    }
    
    # Security headers
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-same-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
    }
    
    # CORS settings
    CORS_ORIGINS = [
        "http://localhost:8013",
        "https://localhost:8013"
    ]
    CORS_METHODS = ["GET", "POST"]
    CORS_HEADERS = ["Content-Type", "Authorization"]
    CORS_SUPPORTS_CREDENTIALS = True
    
    @staticmethod
    def init_app(app):
        """Initialize security settings for the application."""
        # Apply all security settings to the app
        for key, value in SecurityConfig.__dict__.items():
            if key.isupper():
                app.config[key] = value
        
        # Set up CORS
        from flask_cors import CORS
        CORS(app, resources={
            r"/*": {
                "origins": SecurityConfig.CORS_ORIGINS,
                "methods": SecurityConfig.CORS_METHODS,
                "allow_headers": SecurityConfig.CORS_HEADERS,
                "supports_credentials": SecurityConfig.CORS_SUPPORTS_CREDENTIALS
            }
        })
        
        # Add security headers
        @app.after_request
        def add_security_headers(response):
            for header, value in SecurityConfig.SECURITY_HEADERS.items():
                response.headers[header] = value
            
            # Add Content Security Policy
            csp_directives = []
            for key, value in SecurityConfig.CSP.items():
                if isinstance(value, list):
                    value = ' '.join(value)
                csp_directives.append(f"{key} {value}")
            response.headers['Content-Security-Policy'] = '; '.join(csp_directives)
            
            return response
