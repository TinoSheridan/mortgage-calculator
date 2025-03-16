import unittest
import os
import json
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from admin_routes import admin_bp
from config_manager import ConfigManager

class TestBase(unittest.TestCase):
    """Base test class with common setup"""
    
    def setUp(self):
        """Set up test environment before each test"""
        self.app = Flask(__name__, 
                        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'))
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        self.app.secret_key = 'test_key'
        
        # Initialize CSRF protection
        csrf = CSRFProtect()
        csrf.init_app(self.app)
        
        # Set up test config directory
        self.test_config_dir = os.path.join(os.path.dirname(__file__), 'test_config')
        if not os.path.exists(self.test_config_dir):
            os.makedirs(self.test_config_dir)
        
        # Create test configuration files
        self.create_test_configs()
        
        # Initialize ConfigManager
        self.config_manager = ConfigManager()
        self.config_manager.config_dir = self.test_config_dir
        self.config_manager.history_file = os.path.join(self.test_config_dir, 'history.json')
        self.config_manager.load_config()
        self.app.config_manager = self.config_manager
        
        # Register blueprints
        self.app.register_blueprint(admin_bp)
        
        # Create test client
        self.client = self.app.test_client()
        
    def tearDown(self):
        """Clean up test environment after each test"""
        # Remove test config directory and all its contents
        if os.path.exists(self.test_config_dir):
            for root, dirs, files in os.walk(self.test_config_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(self.test_config_dir)
    
    def create_test_configs(self):
        """Create test configuration files"""
        # Create test mortgage config
        mortgage_config = {
            'rates': {
                '30_year_fixed': 3.5,
                '15_year_fixed': 2.75
            },
            'terms': [15, 30],
            'admin': {
                'username': 'admin',
                'password': 'admin123'
            }
        }
        
        # Create test PMI rates
        pmi_rates = {
            'conventional': {
                'down_payment_tiers': {
                    '3_to_5': 1.05,
                    '5_to_10': 0.8,
                    '10_to_15': 0.6,
                    '15_to_20': 0.4
                }
            }
        }
        
        # Create test closing costs
        closing_costs = {
            'appraisal_fee': {
                'amount': 500,
                'is_percentage': False,
                'description': 'Fee for property appraisal'
            }
        }
        
        # Create empty history file
        history = {
            'calculations': [],
            'changes': []
        }
        
        # Write test configs to files
        configs = {
            'mortgage_config.json': mortgage_config,
            'pmi_rates.json': pmi_rates,
            'closing_costs.json': closing_costs,
            'history.json': history
        }
        
        for filename, data in configs.items():
            with open(os.path.join(self.test_config_dir, filename), 'w') as f:
                json.dump(data, f)

class TestAdminRoutes(TestBase):
    """Test admin routes"""
    
    def test_dashboard_data(self):
        """Test dashboard data API"""
        # Add some test calculations
        self.config_manager.add_calculation({
            'loan_amount': 300000,
            'down_payment': 60000,
            'interest_rate': 3.5,
            'loan_term': 30
        })
        
        # Add some test changes
        self.config_manager.add_change(
            description="Test change",
            details="Added test data",
            user="admin"
        )
        
        # Test dashboard data endpoint
        response = self.client.get('/admin/dashboard')
        self.assertEqual(response.status_code, 200)
    
    def test_fee_management(self):
        """Test fee management endpoints"""
        # Test adding a new fee
        new_fee = {
            'fee_type': 'inspection_fee',
            'amount': 400,
            'is_percentage': False,
            'description': 'Property inspection fee'
        }
        
        response = self.client.post('/admin/fees',
                                  json=new_fee,
                                  content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # Test editing a fee
        edit_fee = {
            'amount': 450,
            'description': 'Updated inspection fee'
        }
        
        response = self.client.post('/admin/fees/edit/inspection_fee',
                                  json=edit_fee,
                                  content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # Test deleting a fee
        response = self.client.post('/admin/fees/delete/inspection_fee')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
