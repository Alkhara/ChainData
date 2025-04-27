import json
import os
import time
from typing import Any, Optional

from ..core.config import config


class Cache:
    def __init__(self, subdir: str):
        self.cache_dir = os.path.join(config.get("cache.directory"), subdir)
        self.expiry_seconds = config.get("cache.expiry_seconds")
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, key: str) -> str:
        """Get the full path for a cache file"""
        return os.path.join(self.cache_dir, f"{key}.json")

    def load_from_cache(self, key: str) -> Optional[Any]:
        """Load data from cache if it exists and is not expired"""
        cache_path = self._get_cache_path(key)
        if not os.path.exists(cache_path):
            return None

        try:
            with open(cache_path, "r") as f:
                data = json.load(f)
                if time.time() - data.get("timestamp", 0) < self.expiry_seconds:
                    return data.get("data")
        except (json.JSONDecodeError, IOError):
            return None
        return None

    def save_to_cache(self, key: str, data: Any) -> None:
        """Save data to cache with timestamp"""
        cache_path = self._get_cache_path(key)
        try:
            with open(cache_path, "w") as f:
                json.dump({"timestamp": time.time(), "data": data}, f)
        except IOError as e:
            print(f"Error saving to cache: {e}")


# Create cache instances
defillama_cache = Cache("defillama")
blockchain_cache = Cache("blockchain")
