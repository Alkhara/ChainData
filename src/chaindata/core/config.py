"""Configuration management for ChainData."""

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from dotenv import load_dotenv

from .config_schema import Config

# Load environment variables
load_dotenv()

class ConfigManager:
    """Configuration manager for ChainData."""

    def __init__(self):
        """Initialize configuration manager."""
        self._config = Config()
        self._load_default_config()
        self._load_env_vars()
        self._load_config_file()

    def _load_default_config(self) -> None:
        """Load default configuration."""
        self._config = Config()

    def _load_env_vars(self) -> None:
        """Load configuration from environment variables."""
        # Chainlist config
        if os.getenv("CHAINDATA_CHAINLIST_BASE_URL"):
            self._config.chainlist.base_url = os.getenv("CHAINDATA_CHAINLIST_BASE_URL")
        if os.getenv("CHAINDATA_CHAINLIST_TIMEOUT"):
            self._config.chainlist.timeout = int(os.getenv("CHAINDATA_CHAINLIST_TIMEOUT"))
        if os.getenv("CHAINDATA_CHAINLIST_RETRY_ATTEMPTS"):
            self._config.chainlist.retry_attempts = int(os.getenv("CHAINDATA_CHAINLIST_RETRY_ATTEMPTS"))

        # DefiLlama config
        if os.getenv("CHAINDATA_DEFILLAMA_BASE_URL"):
            self._config.defillama.base_url = os.getenv("CHAINDATA_DEFILLAMA_BASE_URL")
        if os.getenv("CHAINDATA_DEFILLAMA_TIMEOUT"):
            self._config.defillama.timeout = int(os.getenv("CHAINDATA_DEFILLAMA_TIMEOUT"))

        # Cache config
        if os.getenv("CHAINDATA_CACHE_DIRECTORY"):
            self._config.cache.directory = os.getenv("CHAINDATA_CACHE_DIRECTORY")
        if os.getenv("CHAINDATA_CACHE_EXPIRY_SECONDS"):
            self._config.cache.expiry_seconds = int(os.getenv("CHAINDATA_CACHE_EXPIRY_SECONDS"))

        # Display config
        if os.getenv("CHAINDATA_DISPLAY_DATE_FORMAT"):
            self._config.display.date_format = os.getenv("CHAINDATA_DISPLAY_DATE_FORMAT")
        if os.getenv("CHAINDATA_DISPLAY_NUMBER_FORMAT"):
            self._config.display.number_format = os.getenv("CHAINDATA_DISPLAY_NUMBER_FORMAT")

        # Debug and logging
        if os.getenv("CHAINDATA_DEBUG"):
            self._config.debug = os.getenv("CHAINDATA_DEBUG").lower() == "true"
        if os.getenv("CHAINDATA_LOG_LEVEL"):
            self._config.log_level = os.getenv("CHAINDATA_LOG_LEVEL").upper()

    def _load_config_file(self, config_path: Optional[str] = None) -> None:
        """Load configuration from file."""
        if config_path is None:
            config_path = os.getenv("CHAINDATA_CONFIG_FILE", "config.json")

        if not os.path.exists(config_path):
            return

        try:
            with open(config_path, "r") as f:
                config_data = json.load(f)
            self._config = Config(**config_data)
        except Exception as e:
            print(f"Error loading config file: {e}")

    def load_from_file(self, config_path: str) -> None:
        """Load configuration from a specific file."""
        self._load_config_file(config_path)

    def save_to_file(self, config_path: Optional[str] = None) -> None:
        """Save configuration to file."""
        if config_path is None:
            config_path = os.getenv("CHAINDATA_CONFIG_FILE", "config.json")

        try:
            with open(config_path, "w") as f:
                json.dump(self._config.dict(), f, indent=2)
        except Exception as e:
            print(f"Error saving config file: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        keys = key.split(".")
        value = self._config.dict()
        for k in keys:
            if k not in value:
                return default
            value = value[k]
        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value by key."""
        keys = key.split(".")
        config_dict = self._config.dict()
        current = config_dict
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
        self._config = Config(**config_dict)

    @property
    def config(self) -> Config:
        """Get the current configuration."""
        return self._config

# Create global config instance
config = ConfigManager() 