"""
Authentication routes for the multi-tenant mortgage calculator.

Handles user login, logout, and registration with Flask-Login integration.
"""

import logging
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Organization, UserRole

logger = logging.getLogger(__name__)

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login route."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember_me = request.form.get('remember_me', False)
        
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('auth/login.html')
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated.', 'error')
                return render_template('auth/login.html')
            
            # Log the user in
            login_user(user, remember=bool(remember_me))
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            
            logger.info(f"User {username} logged in successfully")
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            # Redirect based on user role
            if user.is_super_admin():
                return redirect(url_for('admin.super_admin_dashboard'))
            elif user.is_org_admin():
                return redirect(url_for('admin.org_admin_dashboard'))
            else:
                return redirect(url_for('index'))
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            flash('Invalid username or password.', 'error')
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout route."""
    username = current_user.username
    logout_user()
    
    # Clear any existing admin session (for backward compatibility)
    session.pop('admin_logged_in', None)
    
    logger.info(f"User {username} logged out")
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route (for organizations that allow self-registration)."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # Check if registration is enabled
    from models import SystemSettings
    registration_enabled = SystemSettings.query.filter_by(key='allow_registration').first()
    if not registration_enabled or not registration_enabled.get_typed_value():
        flash('Registration is currently disabled.', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        organization_name = request.form.get('organization_name', '').strip()
        
        # Validation
        errors = []
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters long.')
        if not email or '@' not in email:
            errors.append('Valid email address is required.')
        if not password or len(password) < 8:
            errors.append('Password must be at least 8 characters long.')
        if password != password_confirm:
            errors.append('Passwords do not match.')
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            errors.append('Username already exists.')
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')
        
        try:
            # Create or find organization
            organization = None
            if organization_name:
                organization = Organization.query.filter_by(name=organization_name.lower().replace(' ', '_')).first()
                if not organization:
                    # Create new organization
                    organization = Organization(
                        name=organization_name.lower().replace(' ', '_'),
                        display_name=organization_name,
                        is_active=True
                    )
                    db.session.add(organization)
                    db.session.flush()  # Get the ID without committing
            else:
                # Use default organization
                organization = Organization.query.filter_by(name='default').first()
                if not organization:
                    # This should not happen if setup was done correctly
                    flash('System error: Default organization not found.', 'error')
                    return render_template('auth/register.html')
            
            # Create user
            user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=UserRole.USER,  # New users are regular users by default
                organization_id=organization.id,
                is_active=True
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"New user registered: {username} in organization {organization.display_name}")
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during registration: {e}")
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('auth/register.html')


@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page."""
    return render_template('auth/profile.html', user=current_user)


@auth_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile."""
    try:
        current_user.first_name = request.form.get('first_name', '').strip()
        current_user.last_name = request.form.get('last_name', '').strip()
        current_user.email = request.form.get('email', '').strip()
        
        # Check if email is already used by another user
        if current_user.email:
            existing_user = User.query.filter(
                User.email == current_user.email,
                User.id != current_user.id
            ).first()
            if existing_user:
                flash('Email address is already in use.', 'error')
                return redirect(url_for('auth.profile'))
        
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        logger.info(f"User {current_user.username} updated profile")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating profile for {current_user.username}: {e}")
        flash('Error updating profile. Please try again.', 'error')
    
    return redirect(url_for('auth.profile'))


@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password."""
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    if not current_user.check_password(current_password):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('auth.profile'))
    
    if len(new_password) < 8:
        flash('New password must be at least 8 characters long.', 'error')
        return redirect(url_for('auth.profile'))
    
    if new_password != confirm_password:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('auth.profile'))
    
    try:
        current_user.set_password(new_password)
        db.session.commit()
        flash('Password changed successfully.', 'success')
        logger.info(f"User {current_user.username} changed password")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error changing password for {current_user.username}: {e}")
        flash('Error changing password. Please try again.', 'error')
    
    return redirect(url_for('auth.profile'))