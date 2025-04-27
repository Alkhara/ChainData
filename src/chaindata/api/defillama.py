"""DeFiLlama API integration."""

from datetime import datetime
from typing import Dict, List, Optional, Union

from chaindata.api.base import BaseAPI
from chaindata.client import AsyncHTTPClient
from chaindata.models.defi import Protocol, Pool, PriceData, TVLData
from chaindata.utils.cache import cache_manager
from chaindata.utils.logging import get_logger

logger = get_logger(__name__)


class DefiLlamaAPI(BaseAPI):
    """DeFiLlama API client."""

    def __init__(self):
        """Initialize the DeFiLlama API client."""
        super().__init__()
        self.base_url = "https://api.llama.fi"
        self.client = AsyncHTTPClient()

    async def close(self):
        """Close the HTTP client."""
        await self.client.close()

    def _sanitize_cache_key(self, key: str) -> str:
        """Sanitize a cache key."""
        return f"defillama:{key}"

    async def _validate_response(self, response: Dict) -> bool:
        """Validate the API response."""
        return isinstance(response, dict) and "error" not in response

    async def _handle_error(self, error: Exception) -> None:
        """Handle API errors."""
        logger.error(f"DeFiLlama API error: {error}")
        raise error

    @cache_manager.cache(ttl=3600)
    async def get_protocols(self) -> List[Protocol]:
        """Get all protocols."""
        cache_key = self._sanitize_cache_key("protocols")
        try:
            response = await self.client.get(f"{self.base_url}/protocols")
            if not await self._validate_response(response):
                raise ValueError("Invalid response from DeFiLlama API")
            return [Protocol(**protocol) for protocol in response]
        except Exception as e:
            await self._handle_error(e)

    @cache_manager.cache(ttl=3600)
    async def get_protocol(self, protocol_id: str) -> Protocol:
        """Get a specific protocol."""
        cache_key = self._sanitize_cache_key(f"protocol:{protocol_id}")
        try:
            response = await self.client.get(f"{self.base_url}/protocol/{protocol_id}")
            if not await self._validate_response(response):
                raise ValueError("Invalid response from DeFiLlama API")
            return Protocol(**response)
        except Exception as e:
            await self._handle_error(e)

    @cache_manager.cache(ttl=3600)
    async def get_pools(self, chain: Optional[str] = None) -> List[Pool]:
        """Get all pools."""
        cache_key = self._sanitize_cache_key(f"pools:{chain or 'all'}")
        try:
            url = f"{self.base_url}/pools"
            if chain:
                url += f"?chain={chain}"
            response = await self.client.get(url)
            if not await self._validate_response(response):
                raise ValueError("Invalid response from DeFiLlama API")
            return [Pool(**pool) for pool in response]
        except Exception as e:
            await self._handle_error(e)

    @cache_manager.cache(ttl=300)
    async def get_price(self, token: str) -> PriceData:
        """Get token price."""
        cache_key = self._sanitize_cache_key(f"price:{token}")
        try:
            response = await self.client.get(f"{self.base_url}/prices/{token}")
            if not await self._validate_response(response):
                raise ValueError("Invalid response from DeFiLlama API")
            return PriceData(**response)
        except Exception as e:
            await self._handle_error(e)

    @cache_manager.cache(ttl=3600)
    async def get_tvl(self) -> TVLData:
        """Get TVL data."""
        cache_key = self._sanitize_cache_key("tvl")
        try:
            response = await self.client.get(f"{self.base_url}/tvl")
            if not await self._validate_response(response):
                raise ValueError("Invalid response from DeFiLlama API")
            return TVLData(**response)
        except Exception as e:
            await self._handle_error(e)


# Global instance
defillama = DefiLlamaAPI() 