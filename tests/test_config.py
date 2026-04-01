"""
Tests for configuration module
"""

import unittest
import tempfile
import json
import os
from pathlib import Path
from acrcloud_cli.config import Config


class TestConfig(unittest.TestCase):
    """Test configuration management"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name) / 'test_config.json'
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.temp_dir.cleanup()
    
    def test_default_config(self):
        """Test default configuration values"""
        config = Config(config_path=self.config_path)
        self.assertEqual(config.get('base_url'), 'https://api-v2.acrcloud.com/api')
        self.assertIsNone(config.get('access_token'))
    
    def test_set_and_get(self):
        """Test setting and getting configuration values"""
        config = Config(config_path=self.config_path)
        config.set('access_token', 'test_token')
        self.assertEqual(config.get('access_token'), 'test_token')
    
    def test_persistence(self):
        """Test configuration persistence"""
        config1 = Config(config_path=self.config_path)
        config1.set('access_token', 'persistent_token')
        
        # Create new config instance with same path
        config2 = Config(config_path=self.config_path)
        self.assertEqual(config2.get('access_token'), 'persistent_token')
    
    def test_delete(self):
        """Test deleting configuration values"""
        config = Config(config_path=self.config_path)
        config.set('temp_key', 'temp_value')
        self.assertEqual(config.get('temp_key'), 'temp_value')
        
        config.delete('temp_key')
        self.assertIsNone(config.get('temp_key'))
    
    def test_list(self):
        """Test listing all configuration values"""
        config = Config(config_path=self.config_path)
        config.set('key1', 'value1')
        config.set('key2', 'value2')
        
        all_config = config.list()
        self.assertIn('key1', all_config)
        self.assertIn('key2', all_config)
        self.assertEqual(all_config['key1'], 'value1')
        self.assertEqual(all_config['key2'], 'value2')


if __name__ == '__main__':
    unittest.main()
