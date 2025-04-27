import pytest

from src.utils.display import (
    format_chain_data,
    format_chart_data,
    format_dex_data,
    format_options_data,
    format_pool_data,
    format_price_data,
)


def test_format_chain_data():
    chain_data = {
        "id": "ethereum",
        "name": "Ethereum",
        "tvl": 1000000000,
        "nativeCurrency": {"symbol": "ETH", "name": "Ether"},
    }
    result = format_chain_data(chain_data)
    assert "Ethereum" in result
    assert "ETH" in result
    assert "1,000,000,000" in result


def test_format_price_data():
    price_data = {"ethereum": {"usd": 2000.0, "usd_24h_change": 5.0}}
    result = format_price_data(price_data)
    assert "Ethereum" in result
    assert "2,000.00" in result
    assert "5.00%" in result


def test_format_chart_data():
    chart_data = [
        {"timestamp": 1620000000, "value": 2000.0},
        {"timestamp": 1620086400, "value": 2100.0},
    ]
    result = format_chart_data(chart_data)
    assert "2,000.00" in result
    assert "2,100.00" in result


def test_format_pool_data():
    pool_data = [
        {"name": "Uniswap V2", "tvl": 1000000, "apy": 0.05, "volume24h": 500000}
    ]
    result = format_pool_data(pool_data)
    assert "Uniswap V2" in result
    assert "1,000,000" in result
    assert "5.00%" in result
    assert "500,000" in result


def test_format_dex_data():
    dex_data = {
        "name": "Uniswap",
        "tvl": 2000000000,
        "volume24h": 100000000,
        "pairs": 1000,
    }
    result = format_dex_data(dex_data)
    assert "Uniswap" in result
    assert "2,000,000,000" in result
    assert "100,000,000" in result
    assert "1,000" in result


def test_format_options_data():
    options_data = [
        {
            "name": "ETH Call",
            "strike": 2000,
            "expiry": "2023-12-31",
            "volume24h": 1000000,
        }
    ]
    result = format_options_data(options_data)
    assert "ETH Call" in result
    assert "2,000" in result
    assert "2023-12-31" in result
    assert "1,000,000" in result
