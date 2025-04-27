from unittest.mock import MagicMock, patch

import pytest

from src.api.defillama import DefiLlamaAPI


@pytest.fixture
def defillama_api():
    return DefiLlamaAPI()


@pytest.fixture
def mock_protocols_response():
    return [
        {
            "name": "Protocol1",
            "tvl": 1000000000,
            "chains": ["Ethereum", "BSC"],
            "oracles": ["chainlink"],
            "change_1h": 1.5,
            "change_1d": -2.3,
            "change_7d": 5.7,
        },
        {
            "name": "Protocol2",
            "tvl": 500000000,
            "chains": ["Ethereum"],
            "oracles": ["pyth"],
            "change_1h": -0.5,
            "change_1d": 1.2,
            "change_7d": -3.1,
        },
    ]


@pytest.fixture
def mock_dex_response():
    return {
        "total24h": 1000000,
        "total7d": 7000000,
        "total30d": 30000000,
        "protocols": [
            {
                "name": "Uniswap",
                "total24h": 500000,
                "total7d": 3500000,
                "total30d": 15000000,
                "change_1d": 2.5,
                "change_7d": -1.8,
                "change_1m": 5.2,
            },
            {
                "name": "PancakeSwap",
                "total24h": 300000,
                "total7d": 2100000,
                "total30d": 9000000,
                "change_1d": -1.2,
                "change_7d": 3.4,
                "change_1m": -2.1,
            },
        ],
    }


@pytest.fixture
def mock_prices_response():
    return {
        "coins": {
            "coingecko:ethereum": {
                "price": 2000.50,
                "symbol": "ETH",
                "timestamp": 1625097600,
                "confidence": 0.99,
            },
            "coingecko:bitcoin": {
                "price": 35000.75,
                "symbol": "BTC",
                "timestamp": 1625097600,
                "confidence": 0.99,
            },
        }
    }


def test_get_all_protocols(defillama_api, mock_protocols_response):
    with patch.object(
        defillama_api, "_make_request", return_value=mock_protocols_response
    ):
        result = defillama_api.get_all_protocols()
        assert len(result) == 2
        assert result[0]["name"] == "Protocol1"
        assert result[0]["tvl"] == 1000000000
        assert "Ethereum" in result[0]["chains"]


def test_get_top_protocols(defillama_api, mock_protocols_response):
    with patch.object(
        defillama_api, "_make_request", return_value=mock_protocols_response
    ):
        result = defillama_api.get_top_protocols(limit=1)
        assert len(result) == 1
        assert result[0]["name"] == "Protocol1"  # Should be highest TVL
        assert result[0]["tvl"] == 1000000000


def test_search_protocols(defillama_api, mock_protocols_response):
    with patch.object(
        defillama_api, "_make_request", return_value=mock_protocols_response
    ):
        result = defillama_api.search_protocols("Protocol1")
        assert len(result) == 1
        assert result[0]["name"] == "Protocol1"


def test_get_chain_protocols(defillama_api, mock_protocols_response):
    with patch.object(
        defillama_api, "_make_request", return_value=mock_protocols_response
    ):
        result = defillama_api.get_chain_protocols("Ethereum")
        assert len(result) == 2  # Both protocols are on Ethereum
        assert all("Ethereum" in p["chains"] for p in result)


def test_get_dex_overview(defillama_api, mock_dex_response):
    with patch.object(defillama_api, "_make_request", return_value=mock_dex_response):
        result = defillama_api.get_dex_overview()
        assert result["total24h"] == 1000000
        assert len(result["protocols"]) == 2
        assert result["protocols"][0]["name"] == "Uniswap"


def test_get_chain_dex_overview(defillama_api, mock_dex_response):
    with patch.object(defillama_api, "_make_request", return_value=mock_dex_response):
        result = defillama_api.get_chain_dex_overview("ethereum")
        assert result["total24h"] == 1000000
        assert len(result["protocols"]) == 2


def test_get_current_prices(defillama_api, mock_prices_response):
    with patch.object(
        defillama_api, "_make_request", return_value=mock_prices_response
    ):
        result = defillama_api.get_current_prices(
            ["coingecko:ethereum", "coingecko:bitcoin"]
        )
        assert "coins" in result
        assert result["coins"]["coingecko:ethereum"]["price"] == 2000.50
        assert result["coins"]["coingecko:bitcoin"]["price"] == 35000.75


def test_get_historical_prices(defillama_api, mock_prices_response):
    with patch.object(
        defillama_api, "_make_request", return_value=mock_prices_response
    ):
        result = defillama_api.get_historical_prices(["coingecko:ethereum"], 1625097600)
        assert "coins" in result
        assert result["coins"]["coingecko:ethereum"]["price"] == 2000.50


def test_sanitize_cache_key(defillama_api):
    url = "https://api.llama.fi/protocols"
    params = {"chain": "ethereum", "limit": 10}
    key = defillama_api._sanitize_cache_key(url, params)
    assert isinstance(key, str)
    assert len(key) == 32  # MD5 hash length


def test_create_session(defillama_api):
    session = defillama_api._create_session()
    assert session.adapters["https://"].max_retries.total == 3
    assert session.adapters["https://"].max_retries.backoff_factor == 1
    assert set(session.adapters["https://"].max_retries.status_forcelist) == {
        429,
        500,
        502,
        503,
        504,
    }


@pytest.mark.parametrize(
    "protocol,expected_tvl",
    [
        ("Protocol1", 1000000000),
        ("Protocol2", 500000000),
    ],
)
def test_get_protocol_info(
    defillama_api, mock_protocols_response, protocol, expected_tvl
):
    with patch.object(defillama_api, "_make_request") as mock_request:
        # Mock both protocol TVL and current TVL responses
        mock_request.side_effect = [
            {"tvl": expected_tvl},  # protocol_tvl response
            expected_tvl,  # current_tvl response
        ]

        result = defillama_api.get_protocol_info(protocol)
        assert result["name"] == protocol
        assert result["current_tvl"] == expected_tvl
        assert "tvl_history" in result
