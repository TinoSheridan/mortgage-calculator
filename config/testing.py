"""Testing configuration for the mortgage calculator application."""
import os
from datetime import timedelta
from security_config import SecurityConfig

class TestingConfig(SecurityConfig):
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
    
    # Allowed beta testers (empty means anyone can access)
    BETA_TESTERS = []  # Add email addresses to restrict access
    
    # Beta testing feedback storage
    FEEDBACK_FILE = 'data/beta_feedback.json'
    
    @classmethod
    def init_app(cls, app):
        """Initialize testing settings."""
        super().init_app(app)
        
        # Configure logging
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Ensure log directory exists
        os.makedirs(os.path.dirname(cls.LOG_FILE), exist_ok=True)
        
        # Ensure feedback directory exists
        os.makedirs(os.path.dirname(cls.FEEDBACK_FILE), exist_ok=True)
        
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
        
        # Setup beta testing routes
        @app.route('/beta/feedback', methods=['POST'])
        def submit_feedback():
            from flask import request, jsonify
            import json
            from datetime import datetime
            
            feedback_data = request.form.to_dict()
            feedback_data['timestamp'] = datetime.now().isoformat()
            
            # Load existing feedback
            try:
                with open(cls.FEEDBACK_FILE, 'r') as f:
                    feedback_list = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                feedback_list = []
            
            # Add new feedback
            feedback_list.append(feedback_data)
            
            # Save feedback
            with open(cls.FEEDBACK_FILE, 'w') as f:
                json.dump(feedback_list, f, indent=2)
            
            return jsonify({'status': 'success'})
