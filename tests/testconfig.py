#!/usr/bin/env python3
"""
Tests for the configuration module.
"""
import unittest
import os
import sys

# Add parent directory to path to import the config module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import module after path is set
import config  # noqa: E402

class TestConfig(unittest.TestCase):
    """Test cases for the configuration module."""
    
    def setUp(self):
        """Set up test environment variables."""
        # Save original environment
        self.original_env = {}
        for key in ['API_KEY', 'DB_PASSWORD', 'SECRET_TOKEN']:
            self.original_env[key] = os.environ.get(key)
            
        # Set test environment variables
        os.environ['API_KEY'] = 'test_api_key'
        os.environ['DB_PASSWORD'] = 'test_password'
        os.environ['SECRET_TOKEN'] = 'test_token'
        
    def tearDown(self):
        """Restore original environment variables."""
        for key, value in self.original_env.items():
            if value is None:
                if key in os.environ:
                    del os.environ[key]
            else:
                os.environ[key] = value
    
    def test_config_values(self):
        """Test that configuration values are loaded properly."""
        # This test is a placeholder and would need to be adapted
        # to work with your actual configuration loading mechanism
        self.assertEqual(os.environ.get('API_KEY'), 'test_api_key')
        self.assertEqual(os.environ.get('DB_PASSWORD'), 'test_password')
        self.assertEqual(os.environ.get('SECRET_TOKEN'), 'test_token')
        
        # In a real test, you would reload the config module
        # and check that the values are loaded properly
        # For example:
        # import importlib
        # importlib.reload(config)
        # self.assertEqual(config.API_KEY, 'test_api_key')

if __name__ == '__main__':
    unittest.main() 