import os
import json
import time
from typing import Dict, Any, Optional
from .config import config

class CacheManager:
    def __init__(self, subdir: str):
        self.cache_dir = os.path.join(config.get('cache.directory'), subdir)
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Ensure the cache directory exists"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def get_cache_path(self, key: str) -> str:
        """Get the cache file path for a key"""
        filename = key.replace('/', '_').strip('_')
        return os.path.join(self.cache_dir, f"{filename}.json")
    
    def load_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Load data from cache if it exists and is not expired"""
        if not config.get('cache.enabled'):
            return None
            
        cache_path = self.get_cache_path(key)
        if not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
            
            # Check if cache is expired
            if time.time() - cache_data.get('timestamp', 0) > config.get('cache.expiry_seconds'):
                return None
            
            return cache_data.get('data')
        except (json.JSONDecodeError, KeyError):
            return None
    
    def save_to_cache(self, key: str, data: Dict[str, Any]):
        """Save data to cache with timestamp"""
        if not config.get('cache.enabled'):
            return
            
        cache_path = self.get_cache_path(key)
        try:
            with open(cache_path, 'w') as f:
                json.dump({
                    'timestamp': time.time(),
                    'data': data
                }, f)
        except Exception as e:
            print(f"Warning: Failed to save cache: {e}")

# Create cache managers for different components
defillama_cache = CacheManager(config.get('cache.defillama_subdir'))
blockchain_cache = CacheManager(config.get('cache.blockchain_subdir')) 