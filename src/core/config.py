import os
from typing import Dict, Any

# Default configuration
DEFAULT_CONFIG: Dict[str, Any] = {
    'cache': {
        'directory': os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'cache'),
        'blockchain_subdir': 'blockchain',
        'defillama_subdir': 'defillama',
        'expiry_seconds': 3600,  # 1 hour
        'blockchain_expiry_seconds': 86400,  # 24 hours
    },
    'display': {
        'max_history_entries': 5,
        'date_format': '%Y-%m-%d %H:%M:%S',
    }
}

class Config:
    def __init__(self):
        self._config = DEFAULT_CONFIG.copy()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value using dot notation"""
        keys = key.split('.')
        current = self._config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value

# Create a global config instance
config = Config() 