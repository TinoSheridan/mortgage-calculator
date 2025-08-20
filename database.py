"""
Database configuration and utilities for the multi-tenant mortgage calculator.

This module handles database connectivity, initialization, and migration utilities.
"""

import os
import logging
from flask import Flask
from flask_migrate import Migrate
from models import db, init_db, create_super_admin, UserRole

logger = logging.getLogger(__name__)

# Flask-Migrate instance
migrate = Migrate()


def init_app(app: Flask):
    """Initialize database with Flask app."""
    # Configure database
    app.config['SQLALCHEMY_DATABASE_URI'] = get_database_url()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    logger.info(f"Database initialized with URI: {get_database_url(masked=True)}")


def get_database_url(masked: bool = False) -> str:
    """
    Get database connection URL from environment variables.
    
    Priority:
    1. DATABASE_URL (for Heroku/Render deployment)
    2. Individual components (DB_HOST, DB_NAME, etc.)
    3. SQLite fallback for development
    """
    
    # Check for full database URL first (common in cloud deployments)
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Handle postgres:// vs postgresql:// (some platforms use the old format)
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        if masked:
            # Mask password for logging
            import re
            masked_url = re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', database_url)
            return masked_url
        return database_url
    
    # Build URL from individual components
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'mortgage_calculator')
    
    if db_password:
        url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        if masked:
            return f"postgresql://{db_user}:***@{db_host}:{db_port}/{db_name}"
        return url
    
    # SQLite fallback for development (no PostgreSQL available)
    sqlite_path = os.getenv('SQLITE_PATH', 'mortgage_calculator.db')
    sqlite_url = f"sqlite:///{sqlite_path}"
    
    if not masked:
        logger.warning("Using SQLite fallback - not recommended for production multi-tenant use")
    
    return sqlite_url


def create_tables():
    """Create all database tables."""
    try:
        db.create_all()
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        return False


def setup_initial_data():
    """Set up initial data including super admin and default organization."""
    try:
        # Initialize database with default settings
        init_db()
        
        # Check if we need to create initial super admin
        from models import User, Organization
        
        super_admin = User.query.filter_by(role=UserRole.SUPER_ADMIN).first()
        if not super_admin:
            logger.info("Creating initial super admin...")
            
            # Get super admin credentials from environment or use defaults
            admin_username = os.getenv('INITIAL_ADMIN_USERNAME', 'superadmin')
            admin_email = os.getenv('INITIAL_ADMIN_EMAIL', 'admin@mortgagecalc.com')
            admin_password = os.getenv('INITIAL_ADMIN_PASSWORD', 'ChangeMe123!')
            
            super_admin = create_super_admin(
                username=admin_username,
                email=admin_email,
                password=admin_password,
                first_name='Super',
                last_name='Admin'
            )
            logger.info(f"Super admin created: {admin_username}")
        
        # Create default organization if none exists
        default_org = Organization.query.first()
        if not default_org:
            logger.info("Creating default organization...")
            default_org = Organization(
                name='default',
                display_name='Default Organization',
                subdomain='default',
                config_overrides={}
            )
            db.session.add(default_org)
            db.session.commit()
            logger.info("Default organization created")
        
        return True
        
    except Exception as e:
        logger.error(f"Error setting up initial data: {e}")
        db.session.rollback()
        return False


def migrate_from_file_config():
    """
    Migrate existing file-based configuration to database.
    This preserves current settings while moving to the new system.
    """
    try:
        from models import GlobalConfiguration
        import json
        
        # Map of file paths to config types
        config_files = {
            'config/closing_costs.json': 'closing_costs',
            'config/pmi_rates.json': 'pmi_rates', 
            'config/mortgage_config.json': 'mortgage_config',
            'config/compliance_text.json': 'compliance_text',
            'config/output_templates.json': 'output_templates'
        }
        
        migrated_count = 0
        
        for file_path, config_type in config_files.items():
            # Check if this config already exists in database
            existing = GlobalConfiguration.query.filter_by(config_type=config_type).first()
            if existing:
                logger.info(f"Skipping {config_type} - already exists in database")
                continue
            
            # Try to load the file
            full_path = os.path.join(os.path.dirname(__file__), file_path)
            if not os.path.exists(full_path):
                logger.warning(f"Config file not found: {full_path}")
                continue
            
            try:
                with open(full_path, 'r') as f:
                    config_data = json.load(f)
                
                # Create global configuration entry
                global_config = GlobalConfiguration(
                    config_type=config_type,
                    config_data=config_data,
                    version='2.7.0',  # Current version
                    description=f'Migrated from {file_path}'
                )
                
                db.session.add(global_config)
                migrated_count += 1
                logger.info(f"Migrated {config_type} from {file_path}")
                
            except Exception as file_error:
                logger.error(f"Error reading {file_path}: {file_error}")
                continue
        
        if migrated_count > 0:
            db.session.commit()
            logger.info(f"Successfully migrated {migrated_count} configuration files to database")
        else:
            logger.info("No configuration files needed migration")
        
        return True
        
    except Exception as e:
        logger.error(f"Error migrating file configuration: {e}")
        db.session.rollback()
        return False


def check_database_connection() -> bool:
    """Check if database connection is working."""
    try:
        # Try a simple query
        db.session.execute(db.text('SELECT 1'))
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


def get_database_info() -> dict:
    """Get database connection information for diagnostics."""
    try:
        url = get_database_url(masked=True)
        
        # Determine database type
        db_type = "Unknown"
        if url.startswith('postgresql://'):
            db_type = "PostgreSQL"
        elif url.startswith('sqlite://'):
            db_type = "SQLite"
        elif url.startswith('mysql://'):
            db_type = "MySQL"
        
        # Get table count
        result = db.session.execute(db.text("""
            SELECT COUNT(*) as table_count 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """))
        table_count = result.scalar()
        
        # Get user count
        from models import User
        user_count = User.query.count()
        
        # Get organization count  
        from models import Organization
        org_count = Organization.query.count()
        
        return {
            'database_type': db_type,
            'connection_url': url,
            'table_count': table_count,
            'user_count': user_count,
            'organization_count': org_count,
            'connected': True
        }
        
    except Exception as e:
        return {
            'connected': False,
            'error': str(e),
            'database_type': 'Unknown',
            'connection_url': get_database_url(masked=True)
        }