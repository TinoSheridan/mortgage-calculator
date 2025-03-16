import os
import json
import logging
from datetime import datetime

class ConfigManager:
    def __init__(self):
        """Initialize ConfigManager."""
        self.config = {}
        self.logger = logging.getLogger(__name__)
        self.config_dir = os.path.join(os.path.dirname(__file__), 'config')
        self.history_file = os.path.join(self.config_dir, 'history.json')
        self.max_history_items = 100
        self.max_recent_changes = 50
        self.calculation_history = []
        self.recent_changes = []

        # Load configuration and history
        self.load_config()
        self.load_history()

    def load_config(self):
        """Load all configuration files"""
        try:
            # Load mortgage configuration
            mortgage_config_path = os.path.join(self.config_dir, 'mortgage_config.json')
            self.logger.info(f"Loading mortgage config from: {mortgage_config_path}")
            with open(mortgage_config_path, 'r') as f:
                self.config.update(json.load(f))
                self.logger.info("Loaded mortgage configuration")

            # Load PMI rates
            pmi_rates_path = os.path.join(self.config_dir, 'pmi_rates.json')
            self.logger.info(f"Loading PMI rates from: {pmi_rates_path}")
            with open(pmi_rates_path, 'r') as f:
                self.config['pmi_rates'] = json.load(f)
                self.logger.info("Loaded PMI rates")

            # Load closing costs
            closing_costs_path = os.path.join(self.config_dir, 'closing_costs.json')
            self.logger.info(f"Loading closing costs from: {closing_costs_path}")
            with open(closing_costs_path, 'r') as f:
                self.config['closing_costs'] = json.load(f)
                self.logger.info("Loaded closing costs")

            # Load county rates (optional)
            county_rates_path = os.path.join(self.config_dir, 'county_rates.json')
            if os.path.exists(county_rates_path):
                self.logger.info(f"Loading county rates from: {county_rates_path}")
                with open(county_rates_path, 'r') as f:
                    self.config['county_rates'] = json.load(f)
                    self.logger.info("Loaded county rates")
            else:
                self.config['county_rates'] = {}
                self.logger.info("No county rates file found, using empty configuration")

            # Load compliance text (optional)
            compliance_path = os.path.join(self.config_dir, 'compliance_text.json')
            if os.path.exists(compliance_path):
                self.logger.info(f"Loading compliance text from: {compliance_path}")
                with open(compliance_path, 'r') as f:
                    self.config['compliance_text'] = json.load(f)
                    self.logger.info("Loaded compliance text")
            else:
                self.config['compliance_text'] = {}
                self.logger.info("No compliance text file found, using empty configuration")

            # Load output templates (optional)
            templates_path = os.path.join(self.config_dir, 'output_templates.json')
            if os.path.exists(templates_path):
                self.logger.info(f"Loading output templates from: {templates_path}")
                with open(templates_path, 'r') as f:
                    self.config['output_templates'] = json.load(f)
                    self.logger.info("Loaded output templates")
            else:
                self.config['output_templates'] = {}
                self.logger.info("No output templates file found, using empty configuration")

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
                with open(self.history_file, 'r') as f:
                    history_data = json.load(f)
                    self.calculation_history = history_data.get('calculations', [])
                    self.recent_changes = history_data.get('changes', [])
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
                'calculations': self.calculation_history[-self.max_history_items:] if self.calculation_history else [],
                'changes': self.recent_changes[-self.max_recent_changes:] if self.recent_changes else []
            }
            
            with open(self.history_file, 'w') as f:
                json.dump(history_data, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving history: {e}")

    def add_calculation(self, calculation_data):
        """Add a new calculation to history."""
        calculation = {
            'timestamp': datetime.now().isoformat(),
            'data': calculation_data
        }
        self.calculation_history.append(calculation)
        if len(self.calculation_history) > self.max_history_items:
            self.calculation_history = self.calculation_history[-self.max_history_items:]
        self.save_history()

    def get_calculation_history(self):
        """Get the calculation history."""
        return self.calculation_history

    def add_change(self, description, details, user):
        """Add a new configuration change to history."""
        try:
            # Initialize history if not loaded
            if not hasattr(self, 'recent_changes'):
                self.recent_changes = []
                
            change = {
                'timestamp': datetime.now().isoformat(),
                'description': description,
                'details': details,
                'user': user
            }
            self.recent_changes.append(change)
            
            # Don't truncate the changes list here - let save_history handle it
            self.save_history()
        except Exception as e:
            self.logger.error(f"Error adding change to history: {e}")

    def get_recent_changes(self):
        """Get the recent configuration changes."""
        if not hasattr(self, 'recent_changes'):
            self.load_history()
        return self.recent_changes[-self.max_recent_changes:] if self.recent_changes else []

    def get_last_backup_time(self):
        """Get the timestamp of the last configuration backup."""
        try:
            backup_dir = os.path.join(self.config_dir, 'backups')
            if not os.path.exists(backup_dir):
                return "No backups found"
            
            backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.json')]
            if not backup_files:
                return "No backups found"
            
            latest_backup = max(backup_files, key=lambda x: os.path.getctime(os.path.join(backup_dir, x)))
            backup_time = datetime.fromtimestamp(os.path.getctime(os.path.join(backup_dir, latest_backup)))
            return backup_time.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            self.logger.error(f"Error getting last backup time: {e}")
            return "Error checking backup time"

    def backup_config(self):
        """Create a backup of all configuration files."""
        try:
            backup_dir = os.path.join(self.config_dir, 'backups')
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # Create 10 backups in quick succession for testing
            for i in range(10):
                timestamp = datetime.now().strftime(f"%Y%m%d_%H%M%S_{i}")
                backup_file = os.path.join(backup_dir, f'config_backup_{timestamp}.json')
                
                with open(backup_file, 'w') as f:
                    json.dump(self.config, f, indent=4)
                
                self.add_change(
                    description="Configuration Backup",
                    details=f"Created backup: config_backup_{timestamp}.json",
                    user="system"
                )
            
            # Clean up old backups (keep last 10)
            backup_files = sorted([f for f in os.listdir(backup_dir) if f.endswith('.json')],
                                key=lambda x: os.path.getctime(os.path.join(backup_dir, x)))
            for old_backup in backup_files[:-10]:
                os.remove(os.path.join(backup_dir, old_backup))
                
            return True
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return False

    def get_config(self):
        """Get the complete configuration"""
        return self.config

    def get_loan_type_config(self, loan_type):
        """Get configuration for a specific loan type"""
        return self.config.get('loan_types', {}).get(loan_type.lower(), {})

    def save_config(self, config=None):
        """Save configuration to files"""
        try:
            if config:
                self.config.update(config)
            
            # Create config directory if it doesn't exist
            os.makedirs(self.config_dir, exist_ok=True)
            
            # Track which sections are modified
            modified_sections = []
            
            # Save mortgage configuration
            mortgage_config_path = os.path.join(self.config_dir, 'mortgage_config.json')
            self.logger.info(f"Saving mortgage config to: {mortgage_config_path}")
            with open(mortgage_config_path, 'w') as f:
                mortgage_config = {k: v for k, v in self.config.items() 
                                 if k not in ['pmi_rates', 'closing_costs', 'county_rates', 'compliance_text', 'output_templates']}
                json.dump(mortgage_config, f, indent=4)
                self.logger.info("Saved mortgage configuration")
                modified_sections.append('mortgage_config')
            
            # Save PMI rates
            pmi_rates_path = os.path.join(self.config_dir, 'pmi_rates.json')
            self.logger.info(f"Saving PMI rates to: {pmi_rates_path}")
            with open(pmi_rates_path, 'w') as f:
                json.dump(self.config.get('pmi_rates', {}), f, indent=4)
                self.logger.info("Saved PMI rates")
                modified_sections.append('pmi_rates')
            
            # Save closing costs
            closing_costs_path = os.path.join(self.config_dir, 'closing_costs.json')
            self.logger.info(f"Saving closing costs to: {closing_costs_path}")
            with open(closing_costs_path, 'w') as f:
                json.dump(self.config.get('closing_costs', {}), f, indent=4)
                self.logger.info("Saved closing costs")
                modified_sections.append('closing_costs')
            
            # Save county rates
            county_rates_path = os.path.join(self.config_dir, 'county_rates.json')
            self.logger.info(f"Saving county rates to: {county_rates_path}")
            with open(county_rates_path, 'w') as f:
                json.dump(self.config.get('county_rates', {}), f, indent=4)
                self.logger.info("Saved county rates")
                modified_sections.append('county_rates')
            
            # Save compliance text
            compliance_path = os.path.join(self.config_dir, 'compliance_text.json')
            self.logger.info(f"Saving compliance text to: {compliance_path}")
            with open(compliance_path, 'w') as f:
                json.dump(self.config.get('compliance_text', {}), f, indent=4)
                self.logger.info("Saved compliance text")
                modified_sections.append('compliance_text')
            
            # Save output templates
            templates_path = os.path.join(self.config_dir, 'output_templates.json')
            self.logger.info(f"Saving output templates to: {templates_path}")
            with open(templates_path, 'w') as f:
                json.dump(self.config.get('output_templates', {}), f, indent=4)
                self.logger.info("Saved output templates")
                modified_sections.append('output_templates')
            
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
                'mortgage_config': os.path.exists(os.path.join(self.config_dir, 'mortgage_config.json')),
                'pmi_rates': os.path.exists(os.path.join(self.config_dir, 'pmi_rates.json')),
                'closing_costs': os.path.exists(os.path.join(self.config_dir, 'closing_costs.json')),
                'county_rates': os.path.exists(os.path.join(self.config_dir, 'county_rates.json')),
                'compliance_text': os.path.exists(os.path.join(self.config_dir, 'compliance_text.json')),
                'output_templates': os.path.exists(os.path.join(self.config_dir, 'output_templates.json'))
            }
            
            # Get backup information
            last_backup = self.get_last_backup_time()
            backup_dir = os.path.join(self.config_dir, 'backups')
            total_backups = len([f for f in os.listdir(backup_dir)
                               if f.endswith('.json')]) if os.path.exists(backup_dir) else 0
            
            # Get calculation and change statistics
            calculation_count = len(self.calculation_history)
            recent_changes = self.recent_changes[-5:]  # Last 5 changes
            
            return {
                'config_files': config_files,
                'last_backup': last_backup,
                'total_backups': total_backups,
                'calculation_count': calculation_count,
                'recent_changes': recent_changes,
                'status': 'healthy' if all(config_files.values()) else 'warning'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system health: {e}")
            return {
                'config_files': {},
                'last_backup': 'Error checking backup time',
                'total_backups': 0,
                'calculation_count': 0,
                'recent_changes': [],
                'status': 'error'
            }
