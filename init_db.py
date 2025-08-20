#!/usr/bin/env python3
"""
Database initialization script for the multi-tenant mortgage calculator.

This script:
1. Creates all database tables
2. Sets up initial super admin
3. Creates default organization  
4. Migrates existing file-based configuration to database
5. Sets up default system settings

Usage:
    python init_db.py [--reset] [--migrate-config]
    
Options:
    --reset: Drop all tables and recreate (WARNING: destroys all data)
    --migrate-config: Migrate file-based configs to database
"""

import os
import sys
import argparse
from datetime import datetime, timezone

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models import db, init_db, create_super_admin, User, Organization, UserRole
import database
from config_service import config_service


def create_app():
    """Create Flask app for database operations."""
    app = Flask(__name__)
    
    # Configure app
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'init-key')
    
    # Initialize database
    database.init_app(app)
    
    return app


def reset_database(app):
    """Drop all tables and recreate them. WARNING: This destroys all data!"""
    with app.app_context():
        print("⚠️  WARNING: This will delete ALL database data!")
        response = input("Type 'CONFIRM' to proceed: ")
        if response != 'CONFIRM':
            print("Operation cancelled.")
            return False
        
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()
        print("✅ Database reset completed")
        return True


def setup_initial_data(app):
    """Set up initial data including super admin and default organization."""
    with app.app_context():
        print("\n📋 Setting up initial data...")
        
        # Initialize database with default settings
        try:
            init_db()
            print("✅ System settings initialized")
        except Exception as e:
            print(f"❌ Error initializing system settings: {e}")
            return False
        
        # Check if super admin already exists
        super_admin = User.query.filter_by(role=UserRole.SUPER_ADMIN).first()
        if super_admin:
            print(f"ℹ️  Super admin already exists: {super_admin.username}")
        else:
            print("\n👤 Creating initial super admin...")
            
            # Get super admin credentials from environment or prompt
            admin_username = os.getenv('INITIAL_ADMIN_USERNAME')
            admin_email = os.getenv('INITIAL_ADMIN_EMAIL')
            admin_password = os.getenv('INITIAL_ADMIN_PASSWORD')
            
            if not admin_username:
                admin_username = input("Enter super admin username (default: superadmin): ").strip() or 'superadmin'
            
            if not admin_email:
                admin_email = input("Enter super admin email (default: admin@mortgagecalc.com): ").strip() or 'admin@mortgagecalc.com'
            
            if not admin_password:
                import getpass
                admin_password = getpass.getpass("Enter super admin password (default: ChangeMe123!): ") or 'ChangeMe123!'
            
            try:
                super_admin = create_super_admin(
                    username=admin_username,
                    email=admin_email,
                    password=admin_password,
                    first_name='Super',
                    last_name='Admin'
                )
                print(f"✅ Super admin created: {admin_username}")
                print(f"   Email: {admin_email}")
                print("   ⚠️  Please change the password after first login!")
                
            except Exception as e:
                print(f"❌ Error creating super admin: {e}")
                return False
        
        # Create default organization if it doesn't exist
        default_org = Organization.query.filter_by(name='default').first()
        if default_org:
            print(f"ℹ️  Default organization already exists: {default_org.display_name}")
        else:
            print("\n🏢 Creating default organization...")
            try:
                default_org = Organization(
                    name='default',
                    display_name='Default Organization',
                    subdomain='default',
                    is_active=True,
                    config_overrides={}
                )
                db.session.add(default_org)
                db.session.commit()
                print("✅ Default organization created")
                
            except Exception as e:
                print(f"❌ Error creating default organization: {e}")
                db.session.rollback()
                return False
        
        return True


def migrate_file_config(app):
    """Migrate existing file-based configuration to database."""
    with app.app_context():
        print("\n📁 Migrating file-based configuration...")
        
        success = database.migrate_from_file_config()
        if success:
            print("✅ Configuration migration completed")
        else:
            print("❌ Configuration migration failed")
        
        return success


def show_status(app):
    """Show current database status."""
    with app.app_context():
        print("\n📊 Database Status:")
        print("=" * 50)
        
        try:
            # Check database connection
            connected = database.check_database_connection()
            print(f"Database Connected: {'✅ Yes' if connected else '❌ No'}")
            
            if connected:
                # Get database info
                db_info = database.get_database_info()
                print(f"Database Type: {db_info.get('database_type', 'Unknown')}")
                print(f"Connection URL: {db_info.get('connection_url', 'Unknown')}")
                print(f"Tables: {db_info.get('table_count', 0)}")
                
                # User counts
                print(f"Users: {db_info.get('user_count', 0)}")
                print(f"Organizations: {db_info.get('organization_count', 0)}")
                
                # Super admin info
                super_admin = User.query.filter_by(role=UserRole.SUPER_ADMIN).first()
                if super_admin:
                    print(f"Super Admin: {super_admin.username} ({super_admin.email})")
                else:
                    print("Super Admin: Not found")
                
                # Default organization
                default_org = Organization.query.filter_by(name='default').first()
                if default_org:
                    print(f"Default Org: {default_org.display_name}")
                    user_count = User.query.filter_by(organization_id=default_org.id).count()
                    print(f"Default Org Users: {user_count}")
                else:
                    print("Default Org: Not found")
                
        except Exception as e:
            print(f"❌ Error getting database status: {e}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Initialize mortgage calculator database')
    parser.add_argument('--reset', action='store_true', 
                       help='Drop all tables and recreate (destroys all data)')
    parser.add_argument('--migrate-config', action='store_true',
                       help='Migrate file-based configs to database')
    parser.add_argument('--status', action='store_true',
                       help='Show database status')
    
    args = parser.parse_args()
    
    print("🏦 Mortgage Calculator Database Initialization")
    print("=" * 50)
    
    # Create Flask app
    app = create_app()
    
    try:
        # Show status if requested
        if args.status:
            show_status(app)
            return
        
        # Reset database if requested
        if args.reset:
            if not reset_database(app):
                return
        
        # Create tables if they don't exist
        with app.app_context():
            print("🔧 Creating database tables...")
            success = database.create_tables()
            if not success:
                print("❌ Failed to create database tables")
                return
        
        # Set up initial data
        if not setup_initial_data(app):
            print("❌ Failed to set up initial data")
            return
        
        # Migrate configuration if requested
        if args.migrate_config:
            if not migrate_file_config(app):
                print("❌ Configuration migration failed")
                return
        
        # Show final status
        show_status(app)
        
        print("\n🎉 Database initialization completed successfully!")
        print("\nNext steps:")
        print("1. Start the Flask application")
        print("2. Visit /auth/login to log in with the super admin account")
        print("3. Create organizations and users as needed")
        print("4. Configure application settings in the admin panel")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()