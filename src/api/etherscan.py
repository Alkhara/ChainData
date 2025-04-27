"""Etherscan API client for ChainData."""

import os
from typing import List, Optional
from dotenv import load_dotenv

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..models.etherscan import Transaction, TokenTransfer, ContractSource
from ..core.config import config
from ..utils.display import print_error, print_info


class EtherscanAPI:
    """Etherscan API client."""

    def __init__(self):
        """Initialize the Etherscan API client."""
        self.base_url = "https://api.etherscan.io/api"
        
        # Load environment variables from .env file
        load_dotenv()
        
        # Try to get API key from environment variables
        self.api_key = os.getenv("ETHERSCAN_API_KEY")
        if not self.api_key:
            print_error("ETHERSCAN_API_KEY environment variable not set")
            print_info("Please set your Etherscan API key in the .env file or as an environment variable")
            raise ValueError("ETHERSCAN_API_KEY environment variable not set")
        
        self.session = self._create_session()

    def _create_session(self):
        """Create a requests session with retry logic."""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy, pool_connections=10, pool_maxsize=10
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _make_request(self, module: str, action: str, **params) -> dict:
        """Make a request to the Etherscan API."""
        params.update({
            "module": module,
            "action": action,
            "apikey": self.api_key
        })
        
        try:
            response = self.session.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] != "1":
                print_error(f"Etherscan API error: {data.get('message', 'Unknown error')}")
                return None
                
            return data["result"]
        except requests.exceptions.RequestException as e:
            print_error(f"Failed to fetch data from Etherscan: {e}")
            return None

    def get_transactions(
        self,
        address: str,
        start_block: Optional[int] = None,
        end_block: Optional[int] = None,
        page: int = 1,
        offset: int = 10,
        sort: str = "desc"
    ) -> List[Transaction]:
        """Get transactions for an address."""
        params = {
            "address": address,
            "page": page,
            "offset": offset,
            "sort": sort
        }
        
        if start_block:
            params["startblock"] = start_block
        if end_block:
            params["endblock"] = end_block
            
        data = self._make_request("account", "txlist", **params)
        if not data:
            return []
            
        return [Transaction(**tx) for tx in data]

    def get_token_transfers(
        self,
        address: str,
        contract_address: Optional[str] = None,
        page: int = 1,
        offset: int = 10,
        sort: str = "desc"
    ) -> List[TokenTransfer]:
        """Get token transfers for an address."""
        params = {
            "address": address,
            "page": page,
            "offset": offset,
            "sort": sort
        }
        
        if contract_address:
            params["contractaddress"] = contract_address
            
        data = self._make_request("account", "tokentx", **params)
        if not data:
            return []
            
        return [TokenTransfer(**transfer) for transfer in data]

    def get_contract_source(self, address: str) -> Optional[ContractSource]:
        """Get contract source code."""
        data = self._make_request("contract", "getsourcecode", address=address)
        if not data or not isinstance(data, list) or not data:
            return None
            
        return ContractSource(**data[0])


# Create global instance
etherscan_api = EtherscanAPI() 