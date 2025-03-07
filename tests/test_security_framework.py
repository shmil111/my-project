#!/usr/bin/env python3
"""
Integration tests for the modular security framework.
"""
import unittest
import os
import sys
import json
import logging
from unittest.mock import patch
from datetime import datetime, timedelta

# Adjust path to import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import security framework
import security

# Disable logging during tests
logging.disable(logging.CRITICAL)

class TestSecurityFramework(unittest.TestCase):
    """Test cases for the modular security framework."""
    
    def setUp(self):
        """Set up test environment."""
        # Initialize security module with test data directories
        self.test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
        os.makedirs(self.test_data_dir, exist_ok=True)
        
        # Create test directories
        test_directories = [
            'credentials',
            'credential_history',
            'intel',
            'iocs',
            'taxii_configs',
            'threat_rules',
            'logs'
        ]
        
        for directory in test_directories:
            dir_path = os.path.join(self.test_data_dir, directory)
            os.makedirs(dir_path, exist_ok=True)
    
    def tearDown(self):
        """Clean up after tests."""
        # In a real test, would clean up test data
        pass
    
    def test_utils_module(self):
        """Test utility functions from the security framework."""
        # Test generate_request_id
        request_id = security.generate_request_id()
        self.assertIsNotNone(request_id)
        self.assertIsInstance(request_id, str)
        
        # Test mask_credential
        masked = security.mask_credential("abcdefg12345")
        self.assertIsNotNone(masked)
        self.assertIsInstance(masked, str)
        self.assertNotEqual(masked, "abcdefg12345")  # Should be masked
        
        # Test generate_secure_credential
        credential = security.generate_secure_credential(length=16, complexity='medium')
        self.assertIsNotNone(credential)
        self.assertIsInstance(credential, str)
        self.assertEqual(len(credential), 16)
    
    def test_credential_verification(self):
        """Test credential verification functions."""
        # Mock config for testing
        with patch('config.API_KEY', 'test_api_key'):
            # Test verify_api_key
            result = security.verify_api_key('test_api_key')
            self.assertTrue(result)
            
            result = security.verify_api_key('wrong_api_key')
            self.assertFalse(result)
    
    def test_intel_module(self):
        """Test intelligence module functions."""
        # Test categorize_intelligence
        intel_data = {
            'type': 'indicator',
            'value': 'test.example.com',
        }
        
        categorized = security.categorize_intelligence(intel_data, 'test', 'medium')
        self.assertIsNotNone(categorized)
        self.assertIn('metadata', categorized)
        self.assertEqual(categorized['metadata']['source_type'], 'test')
        self.assertEqual(categorized['metadata']['priority_level'], 'medium')
    
    def test_threat_detection(self):
        """Test threat detection functionality."""
        # Create a threat detector
        detector = security.ThreatDetector()
        
        # Test IOC type identification
        ioc_type = security.identify_ioc_type('192.168.1.1')
        self.assertEqual(ioc_type, 'ip')
        
        ioc_type = security.identify_ioc_type('example.com')
        self.assertEqual(ioc_type, 'domain')
        
        ioc_type = security.identify_ioc_type('https://example.com')
        self.assertEqual(ioc_type, 'url')
    
    def test_extract_iocs(self):
        """Test extracting IOCs from text."""
        # Test with text containing IOCs
        text = """
        This is a test containing IP 192.168.1.1 and domain example.com.
        It also has a URL https://example.org/test and an email user@example.net.
        """
        
        iocs = security.extract_iocs(text)
        self.assertIsNotNone(iocs)
        self.assertIsInstance(iocs, list)
        
        # Should extract IP, domain, URL, and email
        ioc_types = [ioc['type'] for ioc in iocs]
        self.assertIn('ip', ioc_types)
        self.assertIn('domain', ioc_types)
        self.assertIn('url', ioc_types)
        self.assertIn('email', ioc_types)
        
        # Verify values
        ip_iocs = [ioc for ioc in iocs if ioc['type'] == 'ip']
        self.assertEqual(ip_iocs[0]['value'], '192.168.1.1')
        
        domain_iocs = [ioc for ioc in iocs if ioc['type'] == 'domain']
        self.assertEqual(domain_iocs[0]['value'], 'example.com')

if __name__ == '__main__':
    unittest.main() 