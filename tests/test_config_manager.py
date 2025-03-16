import unittest
import os
import json
import shutil
from datetime import datetime, timedelta
from config_manager import ConfigManager

class TestConfigManager(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test"""
        # Create test directory
        self.test_dir = os.path.join(os.path.dirname(__file__), 'test_config')
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)
        
        # Initialize config manager with test directory
        self.config_manager = ConfigManager()
        self.config_manager.config_dir = self.test_dir
        self.config_manager.history_file = os.path.join(self.test_dir, 'history.json')
        
        # Create test configurations
        self.create_test_configs()
        
        # Initialize empty history
        history_data = {
            'calculations': [],
            'changes': []
        }
        with open(self.config_manager.history_file, 'w') as f:
            json.dump(history_data, f, indent=4)
        
        # Load configuration and history
        self.config_manager.load_config()
        self.config_manager.load_history()

    def tearDown(self):
        """Clean up test environment after each test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def create_test_configs(self):
        """Create test configuration files"""
        configs = {
            'mortgage_config.json': {
                'loan_types': {'conventional': {}, 'fha': {}},
                'limits': {'min_loan': 50000, 'max_loan': 1000000},
                'prepaid_items': {'taxes': True, 'insurance': True}
            },
            'pmi_rates.json': {
                'conventional': {
                    '0-60': 0.4,
                    '61-80': 0.3,
                    '81-95': 0.5
                }
            },
            'county_rates.json': {
                'los_angeles': {'rate': 3.5, 'pmi': 0.5},
                'san_francisco': {'rate': 3.75, 'pmi': 0.55}
            },
            'closing_costs.json': {
                'appraisal': {'amount': 500, 'is_percentage': 'fixed'},
                'origination': {'amount': 1.0, 'is_percentage': 'percentage'}
            },
            'compliance_text.json': {
                'disclaimer': 'Test disclaimer',
                'privacy_policy': 'Test privacy policy'
            },
            'output_templates.json': {
                'standard': {'name': 'Standard Report'},
                'detailed': {'name': 'Detailed Report'}
            }
        }
        
        for filename, content in configs.items():
            with open(os.path.join(self.test_dir, filename), 'w') as f:
                json.dump(content, f)
    
    def test_load_config(self):
        """Test loading configuration files"""
        self.config_manager.load_config()
        
        # Verify all configs are loaded
        self.assertIn('loan_types', self.config_manager.config)
        self.assertIn('county_rates', self.config_manager.config)
        self.assertIn('compliance_text', self.config_manager.config)
        self.assertIn('output_templates', self.config_manager.config)
        self.assertIn('pmi_rates', self.config_manager.config)
        self.assertIn('closing_costs', self.config_manager.config)
        
        # Verify specific values
        self.assertEqual(len(self.config_manager.config['loan_types']), 2)
        self.assertEqual(len(self.config_manager.config['county_rates']), 2)
    
    def test_save_config(self):
        """Test saving configuration changes"""
        self.config_manager.load_config()
        
        # Make changes to config
        self.config_manager.config['county_rates']['new_york'] = {'rate': 3.8, 'pmi': 0.6}
        
        # Save changes
        self.config_manager.save_config(self.config_manager.config)
        
        # Reload config and verify changes
        self.config_manager.load_config()
        self.assertIn('new_york', self.config_manager.config['county_rates'])
        self.assertEqual(self.config_manager.config['county_rates']['new_york']['rate'], 3.8)
    
    def test_calculation_history(self):
        """Test calculation history tracking"""
        test_calc = {'loan_amount': 300000, 'rate': 3.5}
        
        # Add calculations
        for _ in range(5):
            self.config_manager.add_calculation(test_calc)
        
        # Verify history
        history = self.config_manager.get_calculation_history()
        self.assertEqual(len(history), 5)
        self.assertIn('timestamp', history[0])
        self.assertIn('data', history[0])
        
        # Verify max history limit
        for _ in range(100):
            self.config_manager.add_calculation(test_calc)
        
        history = self.config_manager.get_calculation_history()
        self.assertEqual(len(history), self.config_manager.max_history_items)
    
    def test_change_tracking(self):
        """Test configuration change tracking"""
        # Add 60 changes (more than max_recent_changes)
        for i in range(60):
            self.config_manager.add_change(
                description=f"Change {i}",
                details="Test change",
                user="admin"
            )
        
        # Get recent changes
        changes = self.config_manager.get_recent_changes()
        
        # Verify we get exactly max_recent_changes
        self.assertEqual(len(changes), self.config_manager.max_recent_changes)
        
        # Verify changes are the most recent ones
        for i, change in enumerate(changes):
            expected_desc = f"Change {60 - self.config_manager.max_recent_changes + i}"
            self.assertEqual(change['description'], expected_desc)
    
    def test_backup_functionality(self):
        """Test configuration backup system"""
        self.config_manager.load_config()
        
        # Create multiple backups with delays to ensure different timestamps
        for i in range(15):
            # Make some changes to trigger backup
            self.config_manager.config['county_rates'][f'county_{i}'] = {'rate': 3.5 + i/10}
            success = self.config_manager.backup_config()
            self.assertTrue(success)
        
        # Verify backup directory exists
        backup_dir = os.path.join(self.test_dir, 'backups')
        self.assertTrue(os.path.exists(backup_dir))
        
        # Verify backup rotation (should keep only last 10)
        backup_files = sorted([f for f in os.listdir(backup_dir) if f.endswith('.json')])
        self.assertEqual(len(backup_files), 10)
        
        # Verify backup contents
        with open(os.path.join(backup_dir, backup_files[-1]), 'r') as f:
            backup_data = json.load(f)
            self.assertIn('county_14', backup_data['county_rates'])
    
    def test_system_health(self):
        """Test system health monitoring"""
        self.config_manager.load_config()
        
        # Create a backup
        self.config_manager.backup_config()
        
        # Test backup time
        backup_time = self.config_manager.get_last_backup_time()
        self.assertNotEqual(backup_time, "No backups found")
        
        # Add some calculations and changes
        self.config_manager.add_calculation({'loan_amount': 300000})
        self.config_manager.add_change('Test change', 'Added test data', 'admin')
        
        # Get system health
        health = self.config_manager.get_system_health()
        
        # Verify health data
        self.assertIn('config_files', health)
        self.assertIn('last_backup', health)
        self.assertIn('calculation_count', health)
        self.assertIn('recent_changes', health)
        
        # Verify specific values
        self.assertEqual(health['calculation_count'], 1)
        self.assertGreaterEqual(len(health['recent_changes']), 1)
        self.assertNotEqual(health['last_backup'], "No backups found")

if __name__ == '__main__':
    unittest.main()
