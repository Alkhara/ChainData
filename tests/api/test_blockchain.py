from unittest.mock import MagicMock, patch

import pytest

from src.api.chainlist import ChainlistAPI


@pytest.fixture
def chainlist_api():
    return ChainlistAPI()


@pytest.fixture
def mock_response():
    mock = MagicMock()
    mock.json.return_value = {
        "chains": [
            {
                "name": "Ethereum",
                "chain": "ETH",
                "network": "mainnet",
                "rpc": ["https://mainnet.infura.io/v3/"],
                "faucets": [],
                "nativeCurrency": {"name": "Ether", "symbol": "ETH", "decimals": 18},
                "infoURL": "https://ethereum.org",
                "shortName": "eth",
                "chainId": 1,
                "networkId": 1,
                "slip44": 60,
                "ens": {"registry": "0x00000000000C2E074eC69A0dFb2997BA6C7d2e1e"},
            }
        ]
    }
    return mock


def test_get_chains(chainlist_api, mock_response):
    with patch("requests.get", return_value=mock_response):
        result = chainlist_api.get_chains()
        assert len(result) == 1
        assert result[0]["name"] == "Ethereum"
        assert result[0]["chain"] == "ETH"
        assert result[0]["chainId"] == 1


def test_get_chain_by_id(chainlist_api, mock_response):
    with patch("requests.get", return_value=mock_response):
        result = chainlist_api.get_chain_by_id(1)
        assert result["name"] == "Ethereum"
        assert result["chain"] == "ETH"
        assert result["chainId"] == 1


def test_get_chain_rpcs(chainlist_api, mock_response):
    with patch("requests.get", return_value=mock_response):
        result = chainlist_api.get_chain_rpcs(1)
        assert len(result) == 1
        assert result[0] == "https://mainnet.infura.io/v3/"


def test_get_chain_native_currency(chainlist_api, mock_response):
    with patch("requests.get", return_value=mock_response):
        result = chainlist_api.get_chain_native_currency(1)
        assert result["name"] == "Ether"
        assert result["symbol"] == "ETH"
        assert result["decimals"] == 18
