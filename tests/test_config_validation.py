"""
Tests for configuration validation functionality.

These tests verify that the config validator properly validates JSON files
according to the defined schemas and prevents invalid configurations.
"""

import pytest
import json
import os
import tempfile
import sys
from unittest.mock import patch

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_validator import ConfigValidator, validate_config_on_startup
from config_schemas import MORTGAGE_CONFIG_SCHEMA, CLOSING_COSTS_SCHEMA, PMI_RATES_SCHEMA
from error_handling import ConfigurationError


class TestConfigValidation:
    """Test configuration validation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.validator = ConfigValidator(self.temp_dir)
        
        # Create valid test configurations
        self.valid_mortgage_config = {
            "loan_types": {
                "conventional": {
                    "min_down_payment": 3,
                    "max_ltv": 97,
                    "description": "Traditional mortgage loan"
                },
                "fha": {
                    "min_down_payment": 3.5,
                    "max_ltv": 96.5,
                    "upfront_mip_rate": 1.75,
                    "annual_mip_rate": 0.85,
                    "description": "FHA-insured mortgage loan"
                },
                "va": {
                    "min_down_payment": 0,
                    "max_ltv": 100,
                    "funding_fee_rates": {
                        "funding_fee": {
                            "active": {
                                "less_than_5": {"first": 2.3, "subsequent": 3.6},
                                "5_to_10": {"first": 1.65, "subsequent": 1.65},
                                "10_or_more": {"first": 1.4, "subsequent": 1.4}
                            },
                            "reserves": {
                                "less_than_5": {"first": 2.3, "subsequent": 3.6},
                                "5_to_10": {"first": 1.65, "subsequent": 1.65},
                                "10_or_more": {"first": 1.4, "subsequent": 1.4}
                            }
                        }
                    },
                    "description": "VA-guaranteed mortgage loan"
                },
                "usda": {
                    "min_down_payment": 0,
                    "max_ltv": 100,
                    "upfront_fee_rate": 1.0,
                    "annual_fee_rate": 0.35,
                    "description": "USDA Rural Development loan"
                }
            },
            "limits": {
                "max_interest_rate": 15.0,
                "max_loan_term": 30,
                "min_purchase_price": 50000,
                "max_purchase_price": 2000000
            },
            "prepaid_items": {
                "months_insurance_prepaid": 12.0,
                "months_tax_prepaid": 12.0
            },
            "title_insurance": {
                "simultaneous_issuance_fee": 150.0,
                "total_rates_tiers": [
                    {"up_to": 100000, "rate_percentage": 0.625},
                    {"up_to": None, "rate_percentage": 0.425}
                ],
                "lender_rates_simultaneous_tiers": [
                    {"up_to": 100000, "rate_percentage": 0.325},
                    {"up_to": None, "rate_percentage": 0.225}
                ]
            }
        }
        
        self.valid_closing_costs = {
            "appraisal_fee": {
                "type": "fixed",
                "value": 675.0,
                "calculation_base": "fixed",
                "description": "Fee for professional property appraisal",
                "applies_to": ["Purchase", "Refinance"]
            },
            "title_insurance": {
                "type": "percentage",
                "value": 0.3,
                "calculation_base": "purchase_price",
                "description": "Insurance protecting against property title issues",
                "applies_to": ["Purchase"]
            }
        }
        
        self.valid_pmi_rates = {
            "conventional": {
                "ltv_ranges": {
                    "80.01-85.00": 0.3,
                    "85.01-90.00": 0.49
                },
                "credit_score_adjustments": {}
            },
            "fha": {
                "upfront_mip_rate": 1.75,
                "annual_mip": {
                    "long_term": {
                        "standard_amount": {
                            "low_ltv": 0.5,
                            "high_ltv": 0.55
                        }
                    },
                    "short_term": {
                        "standard_amount": {
                            "low_ltv": 0.15,
                            "high_ltv": 0.4
                        }
                    }
                }
            }
        }
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_config_file(self, filename: str, data: dict):
        """Create a configuration file with the given data."""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return file_path
    
    def test_valid_mortgage_config_passes_validation(self):
        """Test that a valid mortgage configuration passes validation."""
        self.create_config_file("mortgage_config.json", self.valid_mortgage_config)
        
        is_valid, errors = self.validator.validate_config_file("mortgage_config.json")
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_invalid_mortgage_config_fails_validation(self):
        """Test that an invalid mortgage configuration fails validation."""
        invalid_config = self.valid_mortgage_config.copy()
        # Remove required field
        del invalid_config["loan_types"]["conventional"]["min_down_payment"]
        
        self.create_config_file("mortgage_config.json", invalid_config)
        
        is_valid, errors = self.validator.validate_config_file("mortgage_config.json")
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("min_down_payment" in error for error in errors)
    
    def test_valid_closing_costs_passes_validation(self):
        """Test that a valid closing costs configuration passes validation."""
        self.create_config_file("closing_costs.json", self.valid_closing_costs)
        
        is_valid, errors = self.validator.validate_config_file("closing_costs.json")
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_invalid_closing_costs_fails_validation(self):
        """Test that an invalid closing costs configuration fails validation."""
        invalid_config = {
            "appraisal_fee": {
                "type": "invalid_type",  # Invalid enum value
                "value": 675.0,
                "calculation_base": "fixed",
                "description": "Fee for professional property appraisal",
                "applies_to": ["Purchase"]
            }
        }
        
        self.create_config_file("closing_costs.json", invalid_config)
        
        is_valid, errors = self.validator.validate_config_file("closing_costs.json")
        
        assert is_valid is False
        assert len(errors) > 0
    
    def test_valid_pmi_rates_passes_validation(self):
        """Test that a valid PMI rates configuration passes validation."""
        self.create_config_file("pmi_rates.json", self.valid_pmi_rates)
        
        is_valid, errors = self.validator.validate_config_file("pmi_rates.json")
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_missing_required_file_fails_validation(self):
        """Test that missing required files fail validation."""
        # Only create optional files
        self.create_config_file("county_rates.json", {})
        
        is_valid, errors = self.validator.validate_all_configs()
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("mortgage_config.json" in error for error in errors)
    
    def test_malformed_json_fails_validation(self):
        """Test that malformed JSON files fail validation."""
        file_path = os.path.join(self.temp_dir, "mortgage_config.json")
        with open(file_path, 'w') as f:
            f.write("{ invalid json }")
        
        is_valid, errors = self.validator.validate_config_file("mortgage_config.json")
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("JSON" in error for error in errors)
    
    def test_validation_report_structure(self):
        """Test that validation report has the correct structure."""
        # Create some valid and invalid files
        self.create_config_file("mortgage_config.json", self.valid_mortgage_config)
        self.create_config_file("closing_costs.json", {"invalid": "structure"})
        
        report = self.validator.get_validation_report()
        
        assert "validation_enabled" in report
        assert "timestamp" in report
        assert "files" in report
        assert "summary" in report
        
        assert "total_files" in report["summary"]
        assert "valid_files" in report["summary"]
        assert "invalid_files" in report["summary"]
        
        # Check that files are reported correctly
        assert "mortgage_config.json" in report["files"]
        assert "closing_costs.json" in report["files"]
        
        # Check that mortgage config is valid and closing costs is invalid
        assert report["files"]["mortgage_config.json"]["valid"] is True
        assert report["files"]["closing_costs.json"]["valid"] is False
    
    def test_config_data_validation(self):
        """Test validation of configuration data without files."""
        # Test valid data
        is_valid, errors = self.validator.validate_config_data(
            "mortgage_config.json", 
            self.valid_mortgage_config
        )
        assert is_valid is True
        assert len(errors) == 0
        
        # Test invalid data
        invalid_data = {"invalid": "structure"}
        is_valid, errors = self.validator.validate_config_data(
            "mortgage_config.json", 
            invalid_data
        )
        assert is_valid is False
        assert len(errors) > 0
    
    def test_validation_with_edge_cases(self):
        """Test validation with edge cases and boundary values."""
        # Test with boundary values
        edge_case_config = self.valid_mortgage_config.copy()
        edge_case_config["limits"]["max_interest_rate"] = 50  # Maximum allowed
        edge_case_config["limits"]["max_loan_term"] = 5  # Minimum allowed
        
        is_valid, errors = self.validator.validate_config_data(
            "mortgage_config.json", 
            edge_case_config
        )
        assert is_valid is True
        
        # Test with values outside boundaries
        invalid_config = self.valid_mortgage_config.copy()
        invalid_config["limits"]["max_interest_rate"] = 100  # Too high
        
        is_valid, errors = self.validator.validate_config_data(
            "mortgage_config.json", 
            invalid_config
        )
        assert is_valid is False
        assert len(errors) > 0
    
    def test_startup_validation_success(self):
        """Test that startup validation succeeds with valid configs."""
        # Create all required files
        self.create_config_file("mortgage_config.json", self.valid_mortgage_config)
        self.create_config_file("closing_costs.json", self.valid_closing_costs)
        self.create_config_file("pmi_rates.json", self.valid_pmi_rates)
        
        # Should not raise any exception
        try:
            validate_config_on_startup(self.temp_dir)
        except ConfigurationError:
            pytest.fail("validate_config_on_startup raised ConfigurationError unexpectedly")
    
    def test_startup_validation_failure(self):
        """Test that startup validation fails with invalid configs."""
        # Create invalid mortgage config
        invalid_config = {"invalid": "structure"}
        self.create_config_file("mortgage_config.json", invalid_config)
        
        # Should raise ConfigurationError
        with pytest.raises(ConfigurationError):
            validate_config_on_startup(self.temp_dir)
    
    def test_optional_files_validation(self):
        """Test that optional files are validated when present."""
        # Create required files
        self.create_config_file("mortgage_config.json", self.valid_mortgage_config)
        self.create_config_file("closing_costs.json", self.valid_closing_costs)
        self.create_config_file("pmi_rates.json", self.valid_pmi_rates)
        
        # Create optional file with valid structure
        self.create_config_file("county_rates.json", {
            "Fulton County": {
                "property_tax_rate": 1.3,
                "insurance_rate": 0.35,
                "description": "Fulton County, GA rates"
            }
        })
        
        is_valid, errors = self.validator.validate_all_configs()
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validation_performance(self):
        """Test that validation completes in reasonable time."""
        import time
        
        # Create all required files
        self.create_config_file("mortgage_config.json", self.valid_mortgage_config)
        self.create_config_file("closing_costs.json", self.valid_closing_costs)
        self.create_config_file("pmi_rates.json", self.valid_pmi_rates)
        
        start_time = time.time()
        is_valid, errors = self.validator.validate_all_configs()
        duration = time.time() - start_time
        
        assert is_valid is True
        assert duration < 1.0  # Should complete in less than 1 second


if __name__ == '__main__':
    pytest.main([__file__, '-v'])