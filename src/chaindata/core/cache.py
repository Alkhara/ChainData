"""Cache management for ChainData."""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, TypeVar, Generic

from pydantic import BaseModel

from .config import config
from .logger import logger

T = TypeVar("T", bound=BaseModel)

class CacheManager(Generic[T]):
    """Generic cache manager for different types of data."""

    def __init__(self, subdir: str, model_class: type[T]):
        """Initialize cache manager."""
        self.cache_dir = Path(config.cache.directory) / subdir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.model_class = model_class
        self.expiry = timedelta(seconds=config.cache.expiry_seconds)

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for a key."""
        return self.cache_dir / f"{key}.json"

    def _is_expired(self, cache_path: Path) -> bool:
        """Check if cache is expired."""
        if not cache_path.exists():
            return True
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        return datetime.now() - mtime > self.expiry

    def load_from_cache(self, key: str) -> Optional[T]:
        """Load data from cache."""
        cache_path = self._get_cache_path(key)
        if not cache_path.exists() or self._is_expired(cache_path):
            return None

        try:
            with open(cache_path, "r") as f:
                data = json.load(f)
            return self.model_class(**data)
        except Exception as e:
            logger.warning(f"Error loading from cache: {e}")
            return None

    def save_to_cache(self, key: str, data: T) -> None:
        """Save data to cache."""
        cache_path = self._get_cache_path(key)
        try:
            with open(cache_path, "w") as f:
                json.dump(data.dict(), f, indent=2)
        except Exception as e:
            logger.warning(f"Error saving to cache: {e}")

    def clear_cache(self) -> None:
        """Clear all cached data."""
        try:
            for file in self.cache_dir.glob("*.json"):
                file.unlink()
        except Exception as e:
            logger.warning(f"Error clearing cache: {e}")

    def get_cache_size(self) -> int:
        """Get total size of cache in bytes."""
        try:
            return sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))
        except Exception as e:
            logger.warning(f"Error getting cache size: {e}")
            return 0

# Create specific cache managers
from ..models.chain import ChainListResponse
from ..models.defi import Protocol, Pool, PriceData, TVLData

chainlist_cache = CacheManager("blockchain", ChainListResponse)
protocol_cache = CacheManager("protocols", Protocol)
pool_cache = CacheManager("pools", Pool)
price_cache = CacheManager("prices", PriceData)
tvl_cache = CacheManager("tvl", TVLData) 