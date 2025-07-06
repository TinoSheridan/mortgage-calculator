"""
Configuration file validator for mortgage calculator.

This module provides JSON schema validation for all configuration files
to ensure data integrity and prevent runtime errors.
"""

import json
import logging
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path

try:
    import jsonschema
    from jsonschema import validate, ValidationError as JsonSchemaValidationError
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

from config_schemas import CONFIG_SCHEMAS, REQUIRED_CONFIG_FILES, OPTIONAL_CONFIG_FILES
from error_handling import ConfigurationError


class ConfigValidator:
    """Validates configuration files against JSON schemas."""
    
    def __init__(self, config_dir: str):
        """Initialize the configuration validator.
        
        Args:
            config_dir: Path to the configuration directory
        """
        self.config_dir = Path(config_dir)
        self.logger = logging.getLogger(__name__)
        
        if not HAS_JSONSCHEMA:
            self.logger.warning(
                "jsonschema package not available. Configuration validation will be disabled. "
                "Install with: pip install jsonschema"
            )
    
    def validate_all_configs(self) -> Tuple[bool, List[str]]:
        """Validate all configuration files.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        if not HAS_JSONSCHEMA:
            self.logger.warning("Skipping validation - jsonschema not available")
            return True, []
        
        all_valid = True
        errors = []
        
        # Validate required files
        for filename in REQUIRED_CONFIG_FILES:
            file_path = self.config_dir / filename
            
            if not file_path.exists():
                all_valid = False
                error_msg = f"Required configuration file missing: {filename}"
                errors.append(error_msg)
                self.logger.error(error_msg)
                continue
            
            is_valid, file_errors = self.validate_config_file(filename)
            if not is_valid:
                all_valid = False
                errors.extend(file_errors)
        
        # Validate optional files (only if they exist)
        for filename in OPTIONAL_CONFIG_FILES:
            file_path = self.config_dir / filename
            
            if file_path.exists():
                is_valid, file_errors = self.validate_config_file(filename)
                if not is_valid:
                    all_valid = False
                    errors.extend(file_errors)
            else:
                self.logger.info(f"Optional configuration file not found: {filename}")
        
        if all_valid:
            self.logger.info("All configuration files validated successfully")
        else:
            self.logger.error(f"Configuration validation failed with {len(errors)} errors")
        
        return all_valid, errors
    
    def validate_config_file(self, filename: str) -> Tuple[bool, List[str]]:
        """Validate a single configuration file.
        
        Args:
            filename: Name of the configuration file
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        if not HAS_JSONSCHEMA:
            return True, []
        
        if filename not in CONFIG_SCHEMAS:
            self.logger.warning(f"No schema defined for {filename}")
            return True, []
        
        file_path = self.config_dir / filename
        
        try:
            # Load the configuration file
            with open(file_path, 'r') as f:
                config_data = json.load(f)
            
            # Get the schema for this file
            schema = CONFIG_SCHEMAS[filename]
            
            # Validate against the schema
            validate(instance=config_data, schema=schema)
            
            self.logger.debug(f"Configuration file {filename} is valid")
            return True, []
            
        except FileNotFoundError:
            error_msg = f"Configuration file not found: {filename}"
            self.logger.error(error_msg)
            return False, [error_msg]
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in {filename}: {str(e)}"
            self.logger.error(error_msg)
            return False, [error_msg]
            
        except JsonSchemaValidationError as e:
            error_msg = f"Schema validation failed for {filename}: {e.message}"
            if e.absolute_path:
                error_msg += f" at path: {'.'.join(str(p) for p in e.absolute_path)}"
            self.logger.error(error_msg)
            return False, [error_msg]
            
        except Exception as e:
            error_msg = f"Unexpected error validating {filename}: {str(e)}"
            self.logger.error(error_msg)
            return False, [error_msg]
    
    def validate_config_data(self, filename: str, config_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate configuration data against a schema.
        
        Args:
            filename: Name of the configuration file (to get the schema)
            config_data: The configuration data to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        if not HAS_JSONSCHEMA:
            return True, []
        
        if filename not in CONFIG_SCHEMAS:
            self.logger.warning(f"No schema defined for {filename}")
            return True, []
        
        try:
            schema = CONFIG_SCHEMAS[filename]
            validate(instance=config_data, schema=schema)
            return True, []
            
        except JsonSchemaValidationError as e:
            error_msg = f"Schema validation failed for {filename}: {e.message}"
            if e.absolute_path:
                error_msg += f" at path: {'.'.join(str(p) for p in e.absolute_path)}"
            return False, [error_msg]
            
        except Exception as e:
            error_msg = f"Unexpected error validating {filename} data: {str(e)}"
            return False, [error_msg]
    
    def get_validation_report(self) -> Dict[str, Any]:
        """Get a comprehensive validation report.
        
        Returns:
            Dictionary containing validation results for all files
        """
        report = {
            "validation_enabled": HAS_JSONSCHEMA,
            "timestamp": None,
            "files": {},
            "summary": {
                "total_files": 0,
                "valid_files": 0,
                "invalid_files": 0,
                "missing_required": 0,
                "total_errors": 0
            }
        }
        
        if not HAS_JSONSCHEMA:
            report["validation_enabled"] = False
            report["warning"] = "jsonschema package not available"
            return report
        
        from datetime import datetime
        report["timestamp"] = datetime.now().isoformat()
        
        all_files = REQUIRED_CONFIG_FILES + OPTIONAL_CONFIG_FILES
        
        for filename in all_files:
            file_path = self.config_dir / filename
            file_exists = file_path.exists()
            is_required = filename in REQUIRED_CONFIG_FILES
            
            file_report = {
                "exists": file_exists,
                "required": is_required,
                "valid": None,
                "errors": []
            }
            
            if file_exists:
                is_valid, errors = self.validate_config_file(filename)
                file_report["valid"] = is_valid
                file_report["errors"] = errors
                
                report["summary"]["total_files"] += 1
                if is_valid:
                    report["summary"]["valid_files"] += 1
                else:
                    report["summary"]["invalid_files"] += 1
                    report["summary"]["total_errors"] += len(errors)
                    
            elif is_required:
                file_report["valid"] = False
                file_report["errors"] = ["Required file is missing"]
                report["summary"]["missing_required"] += 1
                report["summary"]["total_errors"] += 1
            
            report["files"][filename] = file_report
        
        return report
    
    def install_jsonschema_instructions(self) -> str:
        """Get instructions for installing jsonschema dependency.
        
        Returns:
            Installation instructions string
        """
        return """
JSON Schema validation requires the 'jsonschema' package.

To install it, run one of these commands:

    pip install jsonschema
    pip3 install jsonschema
    python -m pip install jsonschema
    python3 -m pip install jsonschema

Or add 'jsonschema>=4.0.0' to your requirements.txt file.

Configuration validation will be disabled until this package is installed.
"""


def validate_config_on_startup(config_dir: str) -> None:
    """Validate configuration files on application startup.
    
    Args:
        config_dir: Path to configuration directory
        
    Raises:
        ConfigurationError: If required files are invalid
    """
    validator = ConfigValidator(config_dir)
    
    if not HAS_JSONSCHEMA:
        logging.getLogger(__name__).warning(
            "Configuration validation disabled - jsonschema package not installed"
        )
        return
    
    is_valid, errors = validator.validate_all_configs()
    
    if not is_valid:
        error_message = f"Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
        raise ConfigurationError(error_message, config_section="startup_validation")


# Convenience function for integration
def create_validator(config_dir: str) -> ConfigValidator:
    """Create a configuration validator instance.
    
    Args:
        config_dir: Path to configuration directory
        
    Returns:
        ConfigValidator instance
    """
    return ConfigValidator(config_dir)