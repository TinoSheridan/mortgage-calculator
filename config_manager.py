import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

# Import validation components
try:
    from config_validator import ConfigValidator, validate_config_on_startup

    HAS_VALIDATION = True
except ImportError:
    HAS_VALIDATION = False


class ConfigManager:
    def __init__(self):
        """Initialize ConfigManager with caching and validation support."""
        self.config = {}
        self.logger = logging.getLogger(__name__)
        self.config_dir = os.path.join(os.path.dirname(__file__), "config")
        self.history_file = os.path.join(self.config_dir, "history.json")
        self.max_history_items = 100
        self.max_recent_changes = 50
        self.calculation_history = []
        self.recent_changes = []

        # Caching support
        self._config_cache: Dict[str, Any] = {}
        self._file_mod_times: Dict[str, float] = {}
        self._cache_enabled = True

        # Validation support
        self.validator = None
        self._validation_enabled = HAS_VALIDATION
        if HAS_VALIDATION:
            self.validator = ConfigValidator(self.config_dir)
            self.logger.info("Configuration validation enabled")
        else:
            self.logger.warning(
                "Configuration validation disabled - jsonschema package not available"
            )

        # Load configuration and history
        self.load_config()
        self.load_history()

    def _get_file_mod_time(self, file_path: str) -> float:
        """Get file modification time."""
        try:
            return os.path.getmtime(file_path)
        except OSError:
            return 0.0

    def _is_cache_valid(self, file_path: str) -> bool:
        """Check if cached data is still valid for a file."""
        if not self._cache_enabled or file_path not in self._config_cache:
            return False

        current_mod_time = self._get_file_mod_time(file_path)
        cached_mod_time = self._file_mod_times.get(file_path, 0.0)

        return current_mod_time == cached_mod_time

    def _load_json_file_cached(self, file_path: str, config_key: str) -> Optional[Dict[str, Any]]:
        """Load JSON file with caching support."""
        # Check if cache is valid
        if self._is_cache_valid(file_path):
            self.logger.debug(f"Using cached config for {config_key}")
            return self._config_cache[file_path]

        # Load from file
        try:
            if not os.path.exists(file_path):
                return None

            with open(file_path, "r") as f:
                data = json.load(f)

            # Cache the data
            if self._cache_enabled:
                self._config_cache[file_path] = data
                self._file_mod_times[file_path] = self._get_file_mod_time(file_path)
                self.logger.debug(f"Cached config for {config_key}")

            return data

        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Error loading {config_key} from {file_path}: {e}")
            return None

    def clear_cache(self):
        """Clear the configuration cache."""
        self._config_cache.clear()
        self._file_mod_times.clear()
        self.logger.info("Configuration cache cleared")

    def disable_cache(self):
        """Disable caching (useful for testing)."""
        self._cache_enabled = False
        self.clear_cache()

    def enable_cache(self):
        """Enable caching."""
        self._cache_enabled = True

    def validate_configuration(self) -> bool:
        """Validate all configuration files.

        Returns:
            True if all configurations are valid, False otherwise
        """
        if not self._validation_enabled:
            self.logger.warning("Configuration validation is disabled")
            return True

        is_valid, errors = self.validator.validate_all_configs()

        if not is_valid:
            self.logger.error("Configuration validation failed:")
            for error in errors:
                self.logger.error(f"  - {error}")

        return is_valid

    def get_validation_report(self) -> Dict[str, Any]:
        """Get a comprehensive validation report.

        Returns:
            Dictionary containing validation results
        """
        if not self._validation_enabled:
            return {"validation_enabled": False, "warning": "jsonschema package not available"}

        return self.validator.get_validation_report()

    def validate_config_data(self, filename: str, config_data: Dict[str, Any]) -> bool:
        """Validate configuration data before saving.

        Args:
            filename: Name of the configuration file
            config_data: Configuration data to validate

        Returns:
            True if valid, False otherwise
        """
        if not self._validation_enabled:
            return True

        is_valid, errors = self.validator.validate_config_data(filename, config_data)

        if not is_valid:
            self.logger.error(f"Validation failed for {filename}:")
            for error in errors:
                self.logger.error(f"  - {error}")

        return is_valid

    def load_config(self):
        """Load all configuration files with caching and validation support."""
        try:
            # Validate configurations first (if validation is enabled)
            if self._validation_enabled and self.validator:
                self.logger.info("Validating configuration files before loading...")
                is_valid, errors = self.validator.validate_all_configs()
                if not is_valid:
                    self.logger.warning(
                        "Configuration validation failed, but proceeding with load:"
                    )
                    for error in errors:
                        self.logger.warning(f"  - {error}")
                else:
                    self.logger.info("All configuration files passed validation")

            # Define configuration files to load
            config_files = [
                (
                    "mortgage_config.json",
                    "mortgage_config",
                    True,
                ),  # (filename, config_key, required)
                ("pmi_rates.json", "pmi_rates", True),
                ("closing_costs.json", "closing_costs", True),
                ("compliance_text.json", "compliance_text", False),
                ("output_templates.json", "output_templates", False),
            ]

            for filename, config_key, required in config_files:
                file_path = os.path.join(self.config_dir, filename)
                self.logger.info(f"Loading {config_key} from: {file_path}")

                # Load with caching
                data = self._load_json_file_cached(file_path, config_key)

                if data is not None:
                    if config_key == "mortgage_config":
                        # Merge mortgage config into main config
                        self.config.update(data)
                    else:
                        # Store as separate key
                        self.config[config_key] = data
                    self.logger.info(f"Loaded {config_key}")

                elif required:
                    # Required file is missing
                    raise FileNotFoundError(f"Required configuration file not found: {file_path}")
                else:
                    # Optional file is missing
                    self.config[config_key] = {}
                    self.logger.info(f"No {filename} file found, using empty configuration")

        except FileNotFoundError as e:
            self.logger.error(f"Configuration file not found: {e}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in configuration file: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            raise

    def load_history(self):
        """Load calculation history and recent changes from file."""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, "r") as f:
                    history_data = json.load(f)
                    self.calculation_history = history_data.get("calculations", [])
                    self.recent_changes = history_data.get("changes", [])
            else:
                # Create empty history file
                self.save_history()
        except Exception as e:
            self.logger.error(f"Error loading history: {e}")
            self.calculation_history = []
            self.recent_changes = []

    def save_history(self):
        """Save calculation history and recent changes to file."""
        try:
            # Ensure config directory exists
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)

            # Keep the most recent items up to the maximum limit
            history_data = {
                "calculations": self.calculation_history[-self.max_history_items :]
                if self.calculation_history
                else [],
                "changes": self.recent_changes[-self.max_recent_changes :]
                if self.recent_changes
                else [],
            }

            with open(self.history_file, "w") as f:
                json.dump(history_data, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving history: {e}")

    def add_calculation(self, calculation_data):
        """Add a new calculation to history."""
        calculation = {
            "timestamp": datetime.now().isoformat(),
            "data": calculation_data,
        }
        self.calculation_history.append(calculation)
        if len(self.calculation_history) > self.max_history_items:
            self.calculation_history = self.calculation_history[-self.max_history_items :]
        self.save_history()

    def get_calculation_history(self):
        """Get the calculation history."""
        return self.calculation_history

    def add_change(self, description, details, user):
        """Add a new configuration change to history."""
        try:
            # Initialize history if not loaded
            if not hasattr(self, "recent_changes"):
                self.recent_changes = []

            change = {
                "timestamp": datetime.now().isoformat(),
                "description": description,
                "details": details,
                "user": user,
            }
            self.recent_changes.append(change)

            # Don't truncate the changes list here - let save_history handle it
            self.save_history()
        except Exception as e:
            self.logger.error(f"Error adding change to history: {e}")

    def get_recent_changes(self):
        """Get the recent configuration changes."""
        if not hasattr(self, "recent_changes"):
            self.load_history()
        return self.recent_changes[-self.max_recent_changes :] if self.recent_changes else []

    def get_last_backup_time(self):
        """Get the timestamp of the last configuration backup."""
        try:
            backup_dir = os.path.join(self.config_dir, "backups")
            if not os.path.exists(backup_dir):
                return "No backups found"

            backup_files = [f for f in os.listdir(backup_dir) if f.endswith(".json")]
            if not backup_files:
                return "No backups found"

            latest_backup = max(
                backup_files,
                key=lambda x: os.path.getctime(os.path.join(backup_dir, x)),
            )
            backup_time = datetime.fromtimestamp(
                os.path.getctime(os.path.join(backup_dir, latest_backup))
            )
            return backup_time.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            self.logger.error(f"Error getting last backup time: {e}")
            return "Error checking backup time"

    def get_closing_costs(self):
        """Get the closing costs configuration.

        Returns:
            list: The closing costs configuration as a list of dictionaries
        """
        self.logger.debug("Getting closing costs configuration")
        closing_costs = self.config.get("closing_costs", [])

        # Ensure we're returning a list, not a string
        if isinstance(closing_costs, str):
            self.logger.error(f"Closing costs config is a string: '{closing_costs}'")
            # Try to parse it as JSON if it looks like JSON
            if closing_costs.strip().startswith("[") and closing_costs.strip().endswith("]"):
                try:
                    import json

                    parsed = json.loads(closing_costs)
                    self.logger.info("Successfully parsed closing costs string as JSON")
                    return parsed
                except Exception as e:
                    self.logger.error(f"Failed to parse closing costs string as JSON: {e}")
                    return []
            # Default to empty list if not valid JSON
            return []

        return closing_costs

    def get_config(self):
        """Get the complete configuration"""
        return self.config

    def get_loan_type_config(self, loan_type):
        """Get configuration for a specific loan type"""
        # Ensure loan_type is a string
        loan_type_str = str(loan_type).lower()

        # Get the loan_types dictionary safely
        loan_types = self.config.get("loan_types", {})

        # Check if loan_types is actually a dictionary
        if not isinstance(loan_types, dict):
            self.logger.error(f"loan_types is not a dictionary: {type(loan_types).__name__}")
            return {}

        # Get the specific loan type config safely
        loan_config = loan_types.get(loan_type_str, {})

        # Ensure we're returning a dictionary
        if not isinstance(loan_config, dict):
            self.logger.error(
                f"Config for loan type '{loan_type_str}' is not a dictionary: {type(loan_config).__name__}"
            )
            return {}

        return loan_config

    def save_config(self, config=None):
        """Save configuration to files with validation"""
        try:
            if config:
                self.config.update(config)

            # Validate configuration before saving (if validation is enabled)
            if self._validation_enabled and self.validator:
                self.logger.info("Validating configuration before saving...")

                # Validate mortgage config data
                mortgage_config = {
                    k: v
                    for k, v in self.config.items()
                    if k
                    not in ["pmi_rates", "closing_costs", "compliance_text", "output_templates"]
                }
                if not self.validate_config_data("mortgage_config.json", mortgage_config):
                    raise ValueError("Mortgage configuration validation failed")

                # Validate other configs
                if "pmi_rates" in self.config and not self.validate_config_data(
                    "pmi_rates.json", self.config["pmi_rates"]
                ):
                    raise ValueError("PMI rates configuration validation failed")

                if "closing_costs" in self.config and not self.validate_config_data(
                    "closing_costs.json", self.config["closing_costs"]
                ):
                    raise ValueError("Closing costs configuration validation failed")

            # Create config directory if it doesn't exist
            os.makedirs(self.config_dir, exist_ok=True)

            # Track which sections are modified
            modified_sections = []

            # Check file permissions before attempting to save
            pmi_rates_path = os.path.join(self.config_dir, "pmi_rates.json")
            if os.path.exists(pmi_rates_path):
                if not os.access(pmi_rates_path, os.W_OK):
                    self.logger.error(f"No write permission for file: {pmi_rates_path}")
                    raise PermissionError(
                        f"No write permission for PMI rates file: {pmi_rates_path}"
                    )

            # Save mortgage configuration
            mortgage_config_path = os.path.join(self.config_dir, "mortgage_config.json")
            self.logger.info(f"Saving mortgage config to: {mortgage_config_path}")
            try:
                with open(mortgage_config_path, "w") as f:
                    mortgage_config = {
                        k: v
                        for k, v in self.config.items()
                        if k
                        not in [
                            "pmi_rates",
                            "closing_costs",
                            "compliance_text",
                            "output_templates",
                        ]
                    }
                    json.dump(mortgage_config, f, indent=4)
                    self.logger.info("Saved mortgage configuration")
                    modified_sections.append("mortgage_config")
            except (IOError, PermissionError) as e:
                self.logger.error(f"Failed to save mortgage config: {e}")
                raise

            # Save PMI rates
            self.logger.info(f"Saving PMI rates to: {pmi_rates_path}")
            try:
                # Create a backup of the PMI rates file first
                if os.path.exists(pmi_rates_path):
                    backup_dir = os.path.join(self.config_dir, "backups")
                    os.makedirs(backup_dir, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_file = os.path.join(backup_dir, f"pmi_rates_backup_{timestamp}.json")
                    with open(pmi_rates_path, "r") as src, open(backup_file, "w") as dst:
                        dst.write(src.read())
                    self.logger.info(f"Created backup of PMI rates at {backup_file}")

                # Save the new PMI rates
                with open(pmi_rates_path, "w") as f:
                    pmi_data = self.config.get("pmi_rates", {})
                    self.logger.info(f"Writing PMI data: {pmi_data}")
                    json.dump(pmi_data, f, indent=4)
                    self.logger.info("Saved PMI rates successfully")
                    modified_sections.append("pmi_rates")
            except (IOError, PermissionError) as e:
                self.logger.error(f"Failed to save PMI rates: {e}")
                raise

            # Save closing costs
            closing_costs_path = os.path.join(self.config_dir, "closing_costs.json")
            self.logger.info(f"Saving closing costs to: {closing_costs_path}")
            try:
                with open(closing_costs_path, "w") as f:
                    json.dump(self.config.get("closing_costs", {}), f, indent=4)
                    self.logger.info("Saved closing costs")
                    modified_sections.append("closing_costs")
            except (IOError, PermissionError) as e:
                self.logger.error(f"Failed to save closing costs: {e}")
                raise

            # Save compliance text
            compliance_path = os.path.join(self.config_dir, "compliance_text.json")
            self.logger.info(f"Saving compliance text to: {compliance_path}")
            try:
                with open(compliance_path, "w") as f:
                    json.dump(self.config.get("compliance_text", {}), f, indent=4)
                    self.logger.info("Saved compliance text")
                    modified_sections.append("compliance_text")
            except (IOError, PermissionError) as e:
                self.logger.error(f"Failed to save compliance text: {e}")
                raise

            # Save output templates
            templates_path = os.path.join(self.config_dir, "output_templates.json")
            self.logger.info(f"Saving output templates to: {templates_path}")
            try:
                with open(templates_path, "w") as f:
                    json.dump(self.config.get("output_templates", {}), f, indent=4)
                    self.logger.info("Saved output templates")
                    modified_sections.append("output_templates")
            except (IOError, PermissionError) as e:
                self.logger.error(f"Failed to save output templates: {e}")
                raise

            # Track changes and create backup
            if modified_sections:
                change_description = "Updated configuration"
                change_details = f"Modified sections: {', '.join(modified_sections)}"
                self.add_change(change_description, change_details, "admin")
                self.backup_config()

            return True
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            raise

    def get_system_health(self):
        """Get system health information."""
        try:
            # Check config files
            config_files = {
                "mortgage_config": os.path.exists(
                    os.path.join(self.config_dir, "mortgage_config.json")
                ),
                "pmi_rates": os.path.exists(os.path.join(self.config_dir, "pmi_rates.json")),
                "closing_costs": os.path.exists(
                    os.path.join(self.config_dir, "closing_costs.json")
                ),
                "compliance_text": os.path.exists(
                    os.path.join(self.config_dir, "compliance_text.json")
                ),
                "output_templates": os.path.exists(
                    os.path.join(self.config_dir, "output_templates.json")
                ),
            }

            # Get backup information
            last_backup = self.get_last_backup_time()
            backup_dir = os.path.join(self.config_dir, "backups")
            total_backups = (
                len([f for f in os.listdir(backup_dir) if f.endswith(".json")])
                if os.path.exists(backup_dir)
                else 0
            )

            # Get calculation and change statistics
            calculation_count = len(self.calculation_history)
            recent_changes = self.recent_changes[-5:]  # Last 5 changes

            return {
                "config_files": config_files,
                "last_backup": last_backup,
                "total_backups": total_backups,
                "calculation_count": calculation_count,
                "recent_changes": recent_changes,
                "status": "healthy" if all(config_files.values()) else "warning",
            }

        except Exception as e:
            self.logger.error(f"Error getting system health: {e}")
            return {
                "config_files": {},
                "last_backup": "Error checking backup time",
                "total_backups": 0,
                "calculation_count": 0,
                "recent_changes": [],
                "status": "error",
            }

    def backup_config(self):
        """Create a backup of all configuration files."""
        try:
            backup_dir = os.path.join(self.config_dir, "backups")
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)

            # Create 10 backups in quick succession for testing
            for i in range(10):
                timestamp = datetime.now().strftime(f"%Y%m%d_%H%M%S_{i}")
                backup_file = os.path.join(backup_dir, f"config_backup_{timestamp}.json")

                with open(backup_file, "w") as f:
                    json.dump(self.config, f, indent=4)

                self.add_change(
                    description="Configuration Backup",
                    details=f"Created backup: config_backup_{timestamp}.json",
                    user="system",
                )

            # Clean up old backups (keep last 10)
            backup_files = sorted(
                [f for f in os.listdir(backup_dir) if f.endswith(".json")],
                key=lambda x: os.path.getctime(os.path.join(backup_dir, x)),
            )
            for old_backup in backup_files[:-10]:
                os.remove(os.path.join(backup_dir, old_backup))

            return True
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return False
