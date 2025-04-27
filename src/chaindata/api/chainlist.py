"""Chainlist API integration."""

import asyncio
from typing import Dict, List, Optional, Union

from ..core.config import config
from ..core.logger import logger
from ..models.chain import Chain, ChainListResponse, ChainSearchResult
from ..utils.http import AsyncHTTPClient
from .base import BaseAPI

class ChainlistAPI(BaseAPI):
    """Chainlist API client."""

    def __init__(self):
        """Initialize Chainlist API client."""
        super().__init__(config.chainlist.base_url)
        self.http_client = AsyncHTTPClient(
            base_url=config.chainlist.base_url,
            timeout=config.chainlist.timeout,
            retry_attempts=config.chainlist.retry_attempts,
            retry_backoff=config.chainlist.retry_backoff,
            rate_limit=config.chainlist.rate_limit,
        )
        self._chains: List[Chain] = []
        self._chain_by_id: Dict[int, Chain] = {}
        self._chain_by_name: Dict[str, Chain] = {}
        self._chain_by_short_name: Dict[str, Chain] = {}

    async def initialize(self) -> None:
        """Initialize API client."""
        await self.http_client._initialize()

    async def close(self) -> None:
        """Close API client."""
        await self.http_client.close()

    def _sanitize_cache_key(self, url: str, params: Optional[Dict] = None) -> str:
        """Create a safe cache key from URL and parameters."""
        key = url
        if params:
            key += "?" + "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        return key

    def validate_response(self, response: Dict) -> bool:
        """Validate API response format."""
        return isinstance(response, dict) and "data" in response

    def handle_error(self, error: Exception) -> None:
        """Handle API errors."""
        logger.error(f"Chainlist API error: {error}")

    def _update_chain_mappings(self, chains: List[Chain]) -> None:
        """Update chain lookup mappings."""
        self._chains = chains
        self._chain_by_id = {chain.chainId: chain for chain in chains}
        self._chain_by_name = {chain.name.lower(): chain for chain in chains}
        self._chain_by_short_name = {
            chain.shortName.lower(): chain
            for chain in chains
            if chain.shortName
        }

    async def get_all_blockchain_data(self, force_refresh: bool = False) -> List[Chain]:
        """Get all blockchain data."""
        cache_key = "all_chains"
        if not force_refresh:
            cached_data = chainlist_cache.load_from_cache(cache_key)
            if cached_data:
                self._update_chain_mappings(cached_data.data)
                return cached_data.data

        try:
            response = await self.http_client.get(config.chainlist.rpc_endpoint)
            if not self.validate_response(response):
                raise ValueError("Invalid response format")

            chains = [Chain(**chain_data) for chain_data in response["data"]]
            self._update_chain_mappings(chains)

            # Save to cache
            chainlist_cache.save_to_cache(
                cache_key,
                ChainListResponse(
                    data=chains,
                    last_updated=datetime.now(),
                    version=__version__,
                ),
            )

            return chains
        except Exception as e:
            self.handle_error(e)
            return []

    async def get_chain_data_by_id(self, chain_id: int) -> Optional[Chain]:
        """Get chain data by ID."""
        if not self._chains:
            await self.get_all_blockchain_data()
        return self._chain_by_id.get(chain_id)

    async def get_chain_data_by_name(self, chain_name: str) -> Optional[Chain]:
        """Get chain data by name."""
        if not self._chains:
            await self.get_all_blockchain_data()
        return self._chain_by_name.get(chain_name.lower())

    async def get_chain_data_by_short_name(self, short_name: str) -> Optional[Chain]:
        """Get chain data by short name."""
        if not self._chains:
            await self.get_all_blockchain_data()
        return self._chain_by_short_name.get(short_name.lower())

    async def get_chain_data(self, identifier: Union[int, str]) -> Optional[Chain]:
        """Get chain data by ID or name."""
        if isinstance(identifier, int):
            return await self.get_chain_data_by_id(identifier)
        return await self.get_chain_data_by_name(identifier)

    async def search_chains(self, query: str) -> List[Chain]:
        """Search for chains by name or ID."""
        if not self._chains:
            await self.get_all_blockchain_data()

        query = query.lower()
        results = []

        # Check chain ID
        try:
            chain_id = int(query)
            if chain_id in self._chain_by_id:
                results.append(self._chain_by_id[chain_id])
        except ValueError:
            pass

        # Check chain names
        for chain in self._chains:
            if (
                query in chain.name.lower()
                or (chain.shortName and query in chain.shortName.lower())
            ):
                results.append(chain)

        return results

    async def get_rpcs(
        self,
        identifier: Union[int, str],
        rpc_type: str = "http",
        no_tracking: bool = False,
    ) -> List[str]:
        """Get RPCs by type."""
        chain = await self.get_chain_data(identifier)
        if not chain:
            return []

        rpcs = []
        for rpc in chain.rpc:
            url = rpc.url.lower()
            tracking = rpc.tracking.lower() if rpc.tracking else "none"

            # Check RPC type
            if rpc_type == "http" and not url.startswith("https://"):
                continue
            if rpc_type == "wss" and not url.startswith("wss://"):
                continue

            # Check tracking status
            if no_tracking and tracking != "none":
                continue

            rpcs.append(rpc.url)

        return rpcs

    async def get_explorer(
        self,
        identifier: Union[int, str],
        explorer_type: Optional[str] = None,
    ) -> List[str]:
        """Get explorer by ID or name."""
        chain = await self.get_chain_data(identifier)
        if not chain:
            return []

        explorers = []
        for explorer in chain.explorers:
            if not explorer_type or explorer.name == explorer_type:
                explorers.append(explorer.url)
        return explorers

    async def get_eips(self, identifier: Union[int, str]) -> List[str]:
        """Get EIPs by ID or name."""
        chain = await self.get_chain_data(identifier)
        if not chain:
            return []

        eips = []
        for feature in chain.features or []:
            eips.extend(feature.values())
        return eips

    async def get_native_currency(
        self,
        identifier: Union[int, str],
    ) -> Optional[Dict[str, Any]]:
        """Get native currency by ID or name."""
        chain = await self.get_chain_data(identifier)
        if not chain:
            return None
        return chain.nativeCurrency.dict()

    async def get_tvl(self, identifier: Union[int, str]) -> Optional[float]:
        """Get TVL by ID or name."""
        chain = await self.get_chain_data(identifier)
        if not chain:
            return None
        return chain.tvl

    async def get_explorer_link(
        self,
        chain_id: int,
        address: str,
    ) -> Optional[str]:
        """Get explorer link for an address."""
        chain = await self.get_chain_data_by_id(chain_id)
        if not chain:
            return None

        for explorer in chain.explorers:
            if explorer.name == "etherscan":
                return f"{explorer.url}/address/{address}"
        return None

# Create global instance
chainlist_api = ChainlistAPI() 