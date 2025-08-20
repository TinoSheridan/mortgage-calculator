"""
Database models for the multi-tenant mortgage calculator system.

This module defines the database schema for users, organizations, and configurations
with proper inheritance hierarchy: Global -> Organization -> User customizations.
"""

from datetime import datetime, timezone
from enum import Enum
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, JSON, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
import bcrypt
import json

db = SQLAlchemy()


class UserRole(Enum):
    """User role enumeration for role-based access control."""
    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    USER = "user"


class Organization(db.Model):
    """
    Organization model for multi-tenant support.
    Each organization has its own configuration overrides.
    """
    __tablename__ = 'organizations'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(200), nullable=False)
    subdomain = Column(String(50), unique=True)  # For future subdomain support
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Configuration overrides (JSON stored as text for flexibility)
    config_overrides = Column(JSON)  # Organization-specific config overrides
    
    # Relationships
    users = relationship("User", back_populates="organization", lazy='dynamic')
    user_configurations = relationship("UserConfiguration", back_populates="organization")
    
    def __repr__(self):
        return f'<Organization {self.name}>'
    
    def get_config_override(self, config_key: str, default=None):
        """Get a specific configuration override for this organization."""
        if self.config_overrides and isinstance(self.config_overrides, dict):
            return self.config_overrides.get(config_key, default)
        return default
    
    def set_config_override(self, config_key: str, value):
        """Set a configuration override for this organization."""
        if not self.config_overrides:
            self.config_overrides = {}
        self.config_overrides[config_key] = value
        self.updated_at = datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    """
    User model with Flask-Login integration.
    Supports hierarchical roles: Super Admin -> Org Admin -> User.
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # User details
    first_name = Column(String(50))
    last_name = Column(String(50))
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    
    # Organization relationship (NULL for super admins)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=True)
    organization = relationship("Organization", back_populates="users")
    
    # Status and timestamps
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    configurations = relationship("UserConfiguration", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password: str):
        """Set password with bcrypt hashing."""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        self.updated_at = datetime.now(timezone.utc)
    
    def check_password(self, password: str) -> bool:
        """Check password against hash."""
        if not self.password_hash:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def get_full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def is_super_admin(self) -> bool:
        """Check if user is a super admin."""
        return self.role == UserRole.SUPER_ADMIN
    
    def is_org_admin(self) -> bool:
        """Check if user is an organization admin."""
        return self.role == UserRole.ORG_ADMIN
    
    def can_manage_organization(self, org_id: int) -> bool:
        """Check if user can manage a specific organization."""
        if self.is_super_admin():
            return True
        return self.is_org_admin() and self.organization_id == org_id
    
    def can_manage_user(self, target_user) -> bool:
        """Check if this user can manage another user."""
        if self.is_super_admin():
            return True
        if self.is_org_admin() and target_user.organization_id == self.organization_id:
            return target_user.role != UserRole.SUPER_ADMIN
        return False


class UserConfiguration(db.Model):
    """
    User-specific configuration overrides.
    These override both global defaults and organization settings.
    """
    __tablename__ = 'user_configurations'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False)
    
    # Configuration data
    config_type = Column(String(50), nullable=False)  # e.g., 'closing_costs', 'pmi_rates', 'mortgage_config'
    config_data = Column(JSON, nullable=False)  # The actual configuration JSON
    
    # Metadata
    description = Column(String(200))  # User description of customization
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="configurations")
    organization = relationship("Organization", back_populates="user_configurations")
    
    # Unique constraint: one config per type per user
    __table_args__ = (
        db.UniqueConstraint('user_id', 'config_type', name='unique_user_config_type'),
    )
    
    def __repr__(self):
        return f'<UserConfiguration {self.user.username}:{self.config_type}>'
    
    def get_config_value(self, key: str, default=None):
        """Get a specific value from the configuration data."""
        if isinstance(self.config_data, dict):
            return self.config_data.get(key, default)
        return default
    
    def set_config_value(self, key: str, value):
        """Set a specific value in the configuration data."""
        if not isinstance(self.config_data, dict):
            self.config_data = {}
        self.config_data[key] = value
        self.updated_at = datetime.now(timezone.utc)


class GlobalConfiguration(db.Model):
    """
    Global default configurations managed by super admins.
    These serve as the base for all organizations and users.
    """
    __tablename__ = 'global_configurations'

    id = Column(Integer, primary_key=True)
    config_type = Column(String(50), nullable=False, unique=True)  # e.g., 'closing_costs', 'pmi_rates'
    config_data = Column(JSON, nullable=False)
    version = Column(String(20), nullable=False)  # For version control
    
    # Metadata
    description = Column(Text)
    created_by = Column(Integer, ForeignKey('users.id'))  # Super admin who created it
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    created_by_user = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<GlobalConfiguration {self.config_type}:{self.version}>'
    
    def get_config_value(self, key: str, default=None):
        """Get a specific value from the global configuration."""
        if isinstance(self.config_data, dict):
            return self.config_data.get(key, default)
        return default


class AuditLog(db.Model):
    """
    Audit log for tracking configuration changes and administrative actions.
    """
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    organization_id = Column(Integer, ForeignKey('organizations.id'))  # NULL for super admin actions
    
    # Action details
    action_type = Column(String(50), nullable=False)  # e.g., 'CONFIG_UPDATE', 'USER_CREATE', 'LOGIN'
    entity_type = Column(String(50))  # e.g., 'User', 'Organization', 'Configuration'
    entity_id = Column(Integer)  # ID of the affected entity
    
    # Change details
    old_values = Column(JSON)  # Previous values (for updates)
    new_values = Column(JSON)  # New values (for updates)
    description = Column(Text)  # Human-readable description
    
    # Request context
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(Text)
    
    # Timestamp
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f'<AuditLog {self.action_type} by {self.user.username}>'


class SystemSettings(db.Model):
    """
    System-wide settings and metadata.
    """
    __tablename__ = 'system_settings'

    id = Column(Integer, primary_key=True)
    key = Column(String(100), nullable=False, unique=True)
    value = Column(Text)
    data_type = Column(String(20), default='string')  # string, integer, boolean, json
    description = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    def __repr__(self):
        return f'<SystemSettings {self.key}:{self.value}>'
    
    def get_typed_value(self):
        """Get the value converted to its proper type."""
        if self.data_type == 'integer':
            return int(self.value) if self.value else 0
        elif self.data_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes') if self.value else False
        elif self.data_type == 'json':
            return json.loads(self.value) if self.value else {}
        return self.value  # string


def create_super_admin(username: str, email: str, password: str, first_name: str = None, last_name: str = None) -> User:
    """
    Create a super admin user. This function should be used for initial setup.
    """
    # Check if super admin already exists
    existing_super_admin = User.query.filter_by(role=UserRole.SUPER_ADMIN).first()
    if existing_super_admin:
        raise ValueError("Super admin already exists. Only one super admin is allowed initially.")
    
    super_admin = User(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        role=UserRole.SUPER_ADMIN,
        organization_id=None  # Super admins don't belong to organizations
    )
    super_admin.set_password(password)
    
    db.session.add(super_admin)
    db.session.commit()
    
    return super_admin


def init_db():
    """Initialize database with default settings."""
    db.create_all()
    
    # Create default system settings
    default_settings = [
        ('app_version', '2.7.0', 'string', 'Current application version'),
        ('maintenance_mode', 'false', 'boolean', 'Whether the app is in maintenance mode'),
        ('max_organizations', '100', 'integer', 'Maximum number of organizations allowed'),
        ('default_organization_name', 'Default Organization', 'string', 'Name for the default organization'),
    ]
    
    for key, value, data_type, description in default_settings:
        existing = SystemSettings.query.filter_by(key=key).first()
        if not existing:
            setting = SystemSettings(
                key=key,
                value=value,
                data_type=data_type,
                description=description
            )
            db.session.add(setting)
    
    db.session.commit()
    print("Database initialized successfully!")