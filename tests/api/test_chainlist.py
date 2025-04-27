from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from src.api.chainlist import ChainlistAPI


@pytest.fixture
def mock_cache():
    """Mock the blockchain cache"""
    with patch("src.api.chainlist.blockchain_cache") as mock:
        mock.load_from_cache.return_value = None
        mock.save_to_cache.return_value = None
        yield mock


@pytest.fixture
def chainlist_api(mock_cache):
    """Create a fresh ChainlistAPI instance for each test"""
    return ChainlistAPI()


@pytest.fixture
def mock_blockchain_data() -> List[Dict[str, Any]]:
    return [
        {
            "name": "Ethereum",
            "chainId": 1,
            "shortName": "eth",
            "networkType": "mainnet",
            "status": "active",
            "tvl": 1000000000,
            "nativeCurrency": {"name": "Ether", "symbol": "ETH", "decimals": 18},
            "rpc": [
                {
                    "url": "https://mainnet.infura.io/v3/",
                    "tracking": "none",
                    "type": "https",
                },
                {
                    "url": "https://eth-mainnet.public.blastapi.io",
                    "tracking": "limited",
                    "type": "https",
                },
            ],
            "explorers": [
                {"name": "etherscan", "url": "https://etherscan.io"},
                {"name": "blockscout", "url": "https://blockscout.com/eth/mainnet"},
            ],
            "features": [{"eip1559": True}, {"eip155": True}],
        },
        {
            "name": "Arbitrum One",
            "chainId": 42161,
            "shortName": "arb1",
            "networkType": "L2",
            "status": "active",
            "tvl": 500000000,
            "nativeCurrency": {"name": "Ether", "symbol": "ETH", "decimals": 18},
            "rpc": [
                {
                    "url": "https://arb1.arbitrum.io/rpc",
                    "tracking": "none",
                    "type": "https",
                },
                {
                    "url": "https://arb-mainnet.g.alchemy.com/v2/",
                    "tracking": "limited",
                    "type": "https",
                },
            ],
            "explorers": [
                {"name": "arbiscan", "url": "https://arbiscan.io"},
                {"name": "arbitrum", "url": "https://explorer.arbitrum.io"},
            ],
            "features": [{"eip1559": True}, {"eip155": True}],
        },
    ]


@pytest.fixture
def mock_response(mock_blockchain_data):
    mock = MagicMock()
    mock.json.return_value = mock_blockchain_data
    mock.raise_for_status.return_value = None
    return mock


def test_initialize_data_structures(chainlist_api, mock_blockchain_data):
    chainlist_api.initialize_data_structures(mock_blockchain_data)
    assert len(chainlist_api.blockchain_data) == 2
    assert chainlist_api.chain_by_id[1]["name"] == "Ethereum"
    assert chainlist_api.chain_by_name["ethereum"]["chainId"] == 1
    assert chainlist_api.chain_by_short_name["eth"]["name"] == "Ethereum"


def test_get_all_blockchain_data(chainlist_api, mock_response, mock_cache):
    with patch("requests.Session.get", return_value=mock_response):
        # Configure mock cache to return None first time (forcing fresh fetch)
        mock_cache.load_from_cache.return_value = None
        result = chainlist_api.get_all_blockchain_data()
        assert len(result) == 2
        assert result[0]["name"] == "Ethereum"
        assert result[1]["name"] == "Arbitrum One"

        # Verify cache was called
        mock_cache.save_to_cache.assert_called_once()

        # Test cache hit
        mock_cache.load_from_cache.return_value = result
        cached_result = chainlist_api.get_all_blockchain_data()
        assert cached_result == result


def test_get_chain_data_by_id(chainlist_api, mock_blockchain_data):
    chainlist_api.initialize_data_structures(mock_blockchain_data)
    result = chainlist_api.get_chain_data_by_id(1)
    assert result["name"] == "Ethereum"
    assert result["chainId"] == 1


def test_get_chain_data_by_name(chainlist_api, mock_blockchain_data):
    chainlist_api.initialize_data_structures(mock_blockchain_data)
    result = chainlist_api.get_chain_data_by_name("Ethereum")
    assert result["name"] == "Ethereum"
    assert result["chainId"] == 1


def test_search_chains(chainlist_api, mock_blockchain_data):
    chainlist_api.initialize_data_structures(mock_blockchain_data)

    # Test search by exact name
    results = chainlist_api.search_chains("Ethereum")
    assert len(results) == 1
    assert results[0]["name"] == "Ethereum"

    # Test search by short name
    results = chainlist_api.search_chains("eth")
    assert len(results) == 1
    assert results[0]["shortName"] == "eth"

    # Test search by chain ID
    results = chainlist_api.search_chains("1")
    assert len(results) == 1
    assert results[0]["chainId"] == 1

    # Test search by partial name
    results = chainlist_api.search_chains("Arbitrum")
    assert len(results) == 1
    assert results[0]["name"] == "Arbitrum One"

    # Test search with no matches
    results = chainlist_api.search_chains("nonexistent")
    assert len(results) == 0


def test_get_rpcs(chainlist_api, mock_blockchain_data):
    chainlist_api.initialize_data_structures(mock_blockchain_data)

    # Test HTTP RPCs
    rpcs = chainlist_api.get_rpcs(1, "https")
    assert len(rpcs) == 2
    assert "https://mainnet.infura.io/v3/" in rpcs

    # Test WSS RPCs
    rpcs = chainlist_api.get_rpcs(1, "wss")
    assert len(rpcs) == 0  # No WSS RPCs in mock data

    # Test no tracking RPCs
    rpcs = chainlist_api.get_rpcs(1, "https", no_tracking=True)
    assert len(rpcs) == 1
    assert rpcs[0] == "https://mainnet.infura.io/v3/"


def test_get_explorer(chainlist_api, mock_blockchain_data):
    chainlist_api.initialize_data_structures(mock_blockchain_data)

    # Test all explorers
    explorers = chainlist_api.get_explorer(1)
    assert len(explorers) == 2
    assert "https://etherscan.io" in explorers

    # Test specific explorer type
    explorers = chainlist_api.get_explorer(1, "etherscan")
    assert len(explorers) == 1
    assert explorers[0] == "https://etherscan.io"


def test_get_eips(chainlist_api, mock_blockchain_data):
    chainlist_api.initialize_data_structures(mock_blockchain_data)
    eips = chainlist_api.get_eips(1)
    assert len(eips) == 2
    assert True in eips  # eip1559 is True
    assert True in eips  # eip155 is True


def test_get_native_currency(chainlist_api, mock_blockchain_data):
    chainlist_api.initialize_data_structures(mock_blockchain_data)
    currency = chainlist_api.get_native_currency(1)
    assert currency["name"] == "Ether"
    assert currency["symbol"] == "ETH"
    assert currency["decimals"] == 18


def test_get_tvl(chainlist_api, mock_blockchain_data):
    chainlist_api.initialize_data_structures(mock_blockchain_data)
    tvl = chainlist_api.get_tvl(1)
    assert tvl == 1000000000  # Expected TVL for Ethereum


def test_get_explorer_link(chainlist_api, mock_blockchain_data):
    chainlist_api.initialize_data_structures(mock_blockchain_data)
    address = "0x1234567890123456789012345678901234567890"
    link = chainlist_api.get_explorer_link(1, address)
    assert (
        link
        == "https://etherscan.io/address/0x1234567890123456789012345678901234567890"
    )
