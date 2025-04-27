import json
import os
from typing import Any, Dict


class Config:
    # Default settings
    DEFAULTS = {
        "cache": {
            "enabled": True,
            "expiry_seconds": 3600,  # 1 hour
            "directory": "cache",
            "defillama_subdir": "defillama",
            "blockchain_subdir": "blockchain",
        },
        "api": {
            "defillama_base_url": "https://api.llama.fi",
            "coins_base_url": "https://coins.llama.fi",
            "stablecoins_base_url": "https://stablecoins.llama.fi",
            "yields_base_url": "https://yields.llama.fi",
        },
        "display": {
            "max_protocols": 10,
            "max_history_entries": 5,
            "date_format": "%Y-%m-%d",
        },
    }

    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.settings = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    user_config = json.load(f)
                    return self._merge_configs(self.DEFAULTS, user_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Error loading config file: {e}. Using defaults.")
        return self.DEFAULTS.copy()

    def _merge_configs(
        self, defaults: Dict[str, Any], user_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge user configuration with defaults"""
        merged = defaults.copy()
        for key, value in user_config.items():
            if (
                key in merged
                and isinstance(merged[key], dict)
                and isinstance(value, dict)
            ):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        return merged

    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.settings, f, indent=4)
        except IOError as e:
            print(f"Warning: Error saving config file: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        keys = key.split(".")
        value = self.settings
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any):
        """Set a configuration value"""
        keys = key.split(".")
        current = self.settings
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
        self.save_config()


# Create a global config instance
config = Config()
