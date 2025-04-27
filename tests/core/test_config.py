import pytest

from src.core.config import config


def test_config_loading():
    assert config is not None
    assert hasattr(config, "api_keys")
    assert hasattr(config, "endpoints")
    assert hasattr(config, "cache_settings")


def test_api_keys():
    assert isinstance(config.api_keys, dict)
    assert "defillama" in config.api_keys
    assert "etherscan" in config.api_keys


def test_endpoints():
    assert isinstance(config.endpoints, dict)
    assert "defillama" in config.endpoints
    assert "etherscan" in config.endpoints


def test_cache_settings():
    assert isinstance(config.cache_settings, dict)
    assert "enabled" in config.cache_settings
    assert "ttl" in config.cache_settings
    assert isinstance(config.cache_settings["ttl"], int)
    assert config.cache_settings["ttl"] > 0
