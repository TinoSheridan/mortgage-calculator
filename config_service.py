"""
Configuration service for multi-tenant configuration inheritance.

This service handles the hierarchical configuration system:
Global Defaults → Organization Overrides → User Customizations

The system ensures that:
1. Version control updates only affect global defaults
2. User customizations are preserved across updates
3. Organizations can set defaults for their users
4. Individual users can override any setting
"""

import logging
from typing import Dict, Any, Optional, Union
from flask import g, session
from models import db, GlobalConfiguration, Organization, UserConfiguration, User

logger = logging.getLogger(__name__)


class ConfigService:
    """Service for managing hierarchical configuration inheritance."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._cache = {}  # Simple in-memory cache for performance
        self._cache_timeout = 300  # 5 minutes
        
    def get_config(self, config_type: str, user_id: Optional[int] = None, organization_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get configuration with full inheritance hierarchy.
        
        Args:
            config_type: Type of configuration (e.g., 'closing_costs', 'pmi_rates')
            user_id: User ID for user-specific customizations
            organization_id: Organization ID for org-specific overrides
            
        Returns:
            Dict containing merged configuration data
        """
        try:
            # Start with global defaults
            config = self._get_global_config(config_type)
            
            # Apply organization overrides if applicable
            if organization_id:
                org_overrides = self._get_organization_config(config_type, organization_id)
                config = self._merge_configs(config, org_overrides)
            
            # Apply user customizations if applicable
            if user_id:
                user_overrides = self._get_user_config(config_type, user_id, organization_id)
                config = self._merge_configs(config, user_overrides)
            
            self.logger.debug(f"Retrieved config {config_type} for user {user_id}, org {organization_id}")
            return config
            
        except Exception as e:
            self.logger.error(f"Error getting config {config_type}: {e}")
            return {}
    
    def get_config_for_current_user(self, config_type: str) -> Dict[str, Any]:
        """
        Get configuration for the currently logged-in user.
        Uses Flask's session/g to determine current user context.
        """
        try:
            # Try to get user from Flask-Login current_user
            from flask_login import current_user
            if hasattr(current_user, 'id') and current_user.is_authenticated:
                return self.get_config(
                    config_type, 
                    user_id=current_user.id,
                    organization_id=getattr(current_user, 'organization_id', None)
                )
            
            # Fallback to session-based admin system (for backward compatibility)
            if session.get('admin_logged_in'):
                # For now, admin users get global config
                return self._get_global_config(config_type)
            
            # Return global config for anonymous users
            return self._get_global_config(config_type)
            
        except Exception as e:
            self.logger.error(f"Error getting config for current user: {e}")
            return self._get_global_config(config_type)
    
    def _get_global_config(self, config_type: str) -> Dict[str, Any]:
        """Get global default configuration."""
        try:
            global_config = GlobalConfiguration.query.filter_by(config_type=config_type).first()
            if global_config and global_config.config_data:
                return global_config.config_data
            
            # Fallback to file-based config if not in database yet
            return self._get_fallback_file_config(config_type)
            
        except Exception as e:
            self.logger.error(f"Error getting global config {config_type}: {e}")
            return self._get_fallback_file_config(config_type)
    
    def _get_organization_config(self, config_type: str, organization_id: int) -> Dict[str, Any]:
        """Get organization-specific configuration overrides."""
        try:
            organization = Organization.query.get(organization_id)
            if organization and organization.config_overrides:
                return organization.config_overrides.get(config_type, {})
            return {}
        except Exception as e:
            self.logger.error(f"Error getting org config for {organization_id}: {e}")
            return {}
    
    def _get_user_config(self, config_type: str, user_id: int, organization_id: Optional[int] = None) -> Dict[str, Any]:
        """Get user-specific configuration customizations."""
        try:
            user_config = UserConfiguration.query.filter_by(
                user_id=user_id,
                config_type=config_type,
                is_active=True
            ).first()
            
            if user_config and user_config.config_data:
                return user_config.config_data
            return {}
        except Exception as e:
            self.logger.error(f"Error getting user config for {user_id}: {e}")
            return {}
    
    def _merge_configs(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge configuration dictionaries.
        Override config takes precedence over base config.
        """
        if not override_config:
            return base_config
        
        if not base_config:
            return override_config
        
        result = base_config.copy()
        
        for key, value in override_config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = self._merge_configs(result[key], value)
            else:
                # Override with new value
                result[key] = value
        
        return result
    
    def _get_fallback_file_config(self, config_type: str) -> Dict[str, Any]:
        """
        Fallback to file-based configuration for backward compatibility.
        This allows the system to work during migration period.
        """
        try:
            import os
            import json
            
            file_mapping = {
                'closing_costs': 'config/closing_costs.json',
                'pmi_rates': 'config/pmi_rates.json',
                'mortgage_config': 'config/mortgage_config.json',
                'compliance_text': 'config/compliance_text.json',
                'output_templates': 'config/output_templates.json'
            }
            
            if config_type not in file_mapping:
                self.logger.warning(f"Unknown config type: {config_type}")
                return {}
            
            file_path = os.path.join(os.path.dirname(__file__), file_mapping[config_type])
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return json.load(f)
            
            self.logger.warning(f"Config file not found: {file_path}")
            return {}
            
        except Exception as e:
            self.logger.error(f"Error loading fallback config {config_type}: {e}")
            return {}
    
    def set_global_config(self, config_type: str, config_data: Dict[str, Any], version: str = None, description: str = None, created_by_id: int = None) -> bool:
        """
        Set or update global configuration.
        This should only be called by super admins.
        """
        try:
            global_config = GlobalConfiguration.query.filter_by(config_type=config_type).first()
            
            if global_config:
                # Update existing
                global_config.config_data = config_data
                if version:
                    global_config.version = version
                if description:
                    global_config.description = description
            else:
                # Create new
                global_config = GlobalConfiguration(
                    config_type=config_type,
                    config_data=config_data,
                    version=version or '2.7.0',
                    description=description or f'Global {config_type} configuration',
                    created_by=created_by_id
                )
                db.session.add(global_config)
            
            db.session.commit()
            self.logger.info(f"Updated global config {config_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting global config {config_type}: {e}")
            db.session.rollback()
            return False
    
    def set_organization_config(self, organization_id: int, config_type: str, config_data: Dict[str, Any]) -> bool:
        """
        Set organization-specific configuration overrides.
        This should only be called by super admins or organization admins.
        """
        try:
            organization = Organization.query.get(organization_id)
            if not organization:
                self.logger.error(f"Organization {organization_id} not found")
                return False
            
            if not organization.config_overrides:
                organization.config_overrides = {}
            
            organization.config_overrides[config_type] = config_data
            db.session.commit()
            
            self.logger.info(f"Updated org config {config_type} for org {organization_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting org config: {e}")
            db.session.rollback()
            return False
    
    def set_user_config(self, user_id: int, config_type: str, config_data: Dict[str, Any], description: str = None) -> bool:
        """
        Set user-specific configuration customizations.
        """
        try:
            user = User.query.get(user_id)
            if not user:
                self.logger.error(f"User {user_id} not found")
                return False
            
            # Find or create user configuration
            user_config = UserConfiguration.query.filter_by(
                user_id=user_id,
                config_type=config_type
            ).first()
            
            if user_config:
                user_config.config_data = config_data
                if description:
                    user_config.description = description
                user_config.is_active = True
            else:
                user_config = UserConfiguration(
                    user_id=user_id,
                    organization_id=user.organization_id,
                    config_type=config_type,
                    config_data=config_data,
                    description=description or f'Custom {config_type} for {user.username}',
                    is_active=True
                )
                db.session.add(user_config)
            
            db.session.commit()
            self.logger.info(f"Updated user config {config_type} for user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting user config: {e}")
            db.session.rollback()
            return False
    
    def reset_user_config(self, user_id: int, config_type: str) -> bool:
        """
        Reset user configuration to use organization/global defaults.
        """
        try:
            user_config = UserConfiguration.query.filter_by(
                user_id=user_id,
                config_type=config_type
            ).first()
            
            if user_config:
                user_config.is_active = False
                db.session.commit()
                self.logger.info(f"Reset user config {config_type} for user {user_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error resetting user config: {e}")
            db.session.rollback()
            return False
    
    def get_config_inheritance_info(self, config_type: str, user_id: Optional[int] = None, organization_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get detailed information about configuration inheritance for debugging/display.
        Shows what values come from which level (global/org/user).
        """
        try:
            info = {
                'config_type': config_type,
                'global_config': self._get_global_config(config_type),
                'organization_config': {},
                'user_config': {},
                'final_config': {},
                'inheritance_chain': []
            }
            
            if organization_id:
                info['organization_config'] = self._get_organization_config(config_type, organization_id)
                info['inheritance_chain'].append('organization')
            
            if user_id:
                info['user_config'] = self._get_user_config(config_type, user_id, organization_id)
                if info['user_config']:
                    info['inheritance_chain'].append('user')
            
            info['final_config'] = self.get_config(config_type, user_id, organization_id)
            info['inheritance_chain'].insert(0, 'global')
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting inheritance info: {e}")
            return {'error': str(e)}


# Global instance
config_service = ConfigService()


def get_config_for_calculator(config_type: str) -> Dict[str, Any]:
    """
    Convenience function to get configuration for the current calculator context.
    This is the main function that the calculator components should use.
    """
    return config_service.get_config_for_current_user(config_type)