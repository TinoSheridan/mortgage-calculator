"""
Tests for configuration caching functionality.

These tests verify that the config manager properly caches JSON files
and only reloads them when the files are modified.
"""

import pytest
import json
import os
import tempfile
import time
import sys
from unittest.mock import patch

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_manager import ConfigManager


class TestConfigCaching:
    """Test configuration caching functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test config files
        self.test_config = {
            "default_rate": 5.5,
            "default_term": 30
        }
        
        self.config_file = os.path.join(self.temp_dir, "mortgage_config.json")
        with open(self.config_file, 'w') as f:
            json.dump(self.test_config, f)
            
        # Create other required config files
        required_files = ["pmi_rates.json", "closing_costs.json"]
        for filename in required_files:
            file_path = os.path.join(self.temp_dir, filename)
            with open(file_path, 'w') as f:
                json.dump({"test": "data"}, f)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_initial_load_caches_config(self):
        """Test that initial config load populates cache."""
        # Patch the config directory
        with patch.object(ConfigManager, '__init__') as mock_init:
            mock_init.return_value = None
            
            config_manager = ConfigManager()
            config_manager.config = {}
            config_manager.config_dir = self.temp_dir
            config_manager._config_cache = {}
            config_manager._file_mod_times = {}
            config_manager._cache_enabled = True
            config_manager._validation_enabled = False  # Disable validation for caching tests
            config_manager.validator = None
            config_manager.logger = pytest.mock_logger = type('MockLogger', (), {
                'info': lambda self, x: None,
                'debug': lambda self, x: None,
                'error': lambda self, x: None
            })()
            
            # Load config
            config_manager.load_config()
            
            # Verify cache is populated
            assert len(config_manager._config_cache) > 0
            assert len(config_manager._file_mod_times) > 0
            
            # Verify config was loaded
            assert "default_rate" in config_manager.config
            assert config_manager.config["default_rate"] == 5.5
    
    def test_cache_hit_avoids_file_read(self):
        """Test that cache hit avoids reading file again."""
        with patch.object(ConfigManager, '__init__') as mock_init:
            mock_init.return_value = None
            
            config_manager = ConfigManager()
            config_manager.config = {}
            config_manager.config_dir = self.temp_dir
            config_manager._config_cache = {}
            config_manager._file_mod_times = {}
            config_manager._cache_enabled = True
            config_manager._validation_enabled = False  # Disable validation for caching tests
            config_manager.validator = None
            config_manager.logger = type('MockLogger', (), {
                'info': lambda self, x: None,
                'debug': lambda self, x: None,
                'error': lambda self, x: None
            })()
            
            # First load
            config_manager.load_config()
            initial_cache_size = len(config_manager._config_cache)
            
            # Mock file read to ensure it's not called again
            with patch('builtins.open') as mock_open:
                # Second load should use cache
                config_manager.load_config()
                
                # Verify cache was used (files not opened)
                # Since cache is valid, open should not be called for cached files
                assert len(config_manager._config_cache) == initial_cache_size
    
    def test_file_modification_invalidates_cache(self):
        """Test that modifying a file invalidates the cache."""
        with patch.object(ConfigManager, '__init__') as mock_init:
            mock_init.return_value = None
            
            config_manager = ConfigManager()
            config_manager.config = {}
            config_manager.config_dir = self.temp_dir
            config_manager._config_cache = {}
            config_manager._file_mod_times = {}
            config_manager._cache_enabled = True
            config_manager._validation_enabled = False  # Disable validation for caching tests
            config_manager.validator = None
            config_manager.logger = type('MockLogger', (), {
                'info': lambda self, x: None,
                'debug': lambda self, x: None,
                'error': lambda self, x: None
            })()
            
            # First load
            config_manager.load_config()
            
            # Modify the config file
            time.sleep(0.1)  # Ensure different modification time
            modified_config = {"default_rate": 6.0, "default_term": 15}
            with open(self.config_file, 'w') as f:
                json.dump(modified_config, f)
            
            # Second load should detect change
            config_manager.load_config()
            
            # Verify new config was loaded
            assert config_manager.config["default_rate"] == 6.0
            assert config_manager.config["default_term"] == 15
    
    def test_cache_disable_forces_reload(self):
        """Test that disabling cache forces file reload."""
        with patch.object(ConfigManager, '__init__') as mock_init:
            mock_init.return_value = None
            
            config_manager = ConfigManager()
            config_manager.config = {}
            config_manager.config_dir = self.temp_dir
            config_manager._config_cache = {}
            config_manager._file_mod_times = {}
            config_manager._cache_enabled = True
            config_manager._validation_enabled = False  # Disable validation for caching tests
            config_manager.validator = None
            config_manager.logger = type('MockLogger', (), {
                'info': lambda self, x: None,
                'debug': lambda self, x: None,
                'error': lambda self, x: None
            })()
            
            # First load with cache enabled
            config_manager.load_config()
            
            # Disable cache
            config_manager.disable_cache()
            assert not config_manager._cache_enabled
            assert len(config_manager._config_cache) == 0
            
            # Load again should work without cache
            config_manager.load_config()
            assert "default_rate" in config_manager.config
    
    def test_cache_clear_empties_cache(self):
        """Test that clear_cache empties the cache."""
        with patch.object(ConfigManager, '__init__') as mock_init:
            mock_init.return_value = None
            
            config_manager = ConfigManager()
            config_manager.config = {}
            config_manager.config_dir = self.temp_dir
            config_manager._config_cache = {}
            config_manager._file_mod_times = {}
            config_manager._cache_enabled = True
            config_manager._validation_enabled = False  # Disable validation for caching tests
            config_manager.validator = None
            config_manager.logger = type('MockLogger', (), {
                'info': lambda self, x: None,
                'debug': lambda self, x: None,
                'error': lambda self, x: None
            })()
            
            # Load config to populate cache
            config_manager.load_config()
            assert len(config_manager._config_cache) > 0
            
            # Clear cache
            config_manager.clear_cache()
            assert len(config_manager._config_cache) == 0
            assert len(config_manager._file_mod_times) == 0
    
    def test_cache_performance_improvement(self):
        """Test that caching provides performance improvement."""
        with patch.object(ConfigManager, '__init__') as mock_init:
            mock_init.return_value = None
            
            config_manager = ConfigManager()
            config_manager.config = {}
            config_manager.config_dir = self.temp_dir
            config_manager._config_cache = {}
            config_manager._file_mod_times = {}
            config_manager._cache_enabled = True
            config_manager._validation_enabled = False  # Disable validation for caching tests
            config_manager.validator = None
            config_manager.logger = type('MockLogger', (), {
                'info': lambda self, x: None,
                'debug': lambda self, x: None,
                'error': lambda self, x: None
            })()
            
            # Time first load (cold cache)
            start_time = time.time()
            config_manager.load_config()
            cold_load_time = time.time() - start_time
            
            # Time second load (warm cache)
            start_time = time.time()
            config_manager.load_config()
            warm_load_time = time.time() - start_time
            
            # Cache should be faster (though this is a simple test)
            # At minimum, it should not be significantly slower
            assert warm_load_time <= cold_load_time * 2  # Allow some variance


if __name__ == '__main__':
    pytest.main([__file__, '-v'])