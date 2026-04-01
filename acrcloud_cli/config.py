"""
Configuration management for ACRCloud CLI
"""

import json
import os
from pathlib import Path


class Config:
    """Manage ACRCloud CLI configuration"""
    
    DEFAULT_CONFIG = {
        'base_url': 'https://api-v2.acrcloud.com/api',
        'access_token': None
    }
    
    def __init__(self, config_path=None):
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Default config location: ~/.acrcloud/config.json
            self.config_path = Path.home() / '.acrcloud' / 'config.json'
        
        self._config = self._load()
    
    def _load(self):
        """Load configuration from file"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    return {**self.DEFAULT_CONFIG, **json.load(f)}
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config file: {e}")
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()
    
    def save(self):
        """Save configuration to file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self._config, f, indent=2)
    
    def get(self, key, default=None):
        """Get configuration value"""
        return self._config.get(key, default)
    
    def set(self, key, value):
        """Set configuration value"""
        self._config[key] = value
        self.save()
    
    def delete(self, key):
        """Delete configuration key"""
        if key in self._config:
            del self._config[key]
            self.save()
    
    def list(self):
        """List all configuration"""
        return self._config.copy()
