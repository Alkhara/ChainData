"""Async HTTP client for API calls."""

import asyncio
from typing import Any, Dict, Optional, Union
from urllib.parse import urljoin

import aiohttp
from aiohttp import ClientSession, ClientTimeout
from aiohttp.typedefs import StrOrURL

from ..core.config import config
from ..core.logger import logger

class AsyncHTTPClient:
    """Async HTTP client with retry logic and rate limiting."""

    def __init__(
        self,
        base_url: str,
        timeout: int = 10,
        retry_attempts: int = 3,
        retry_backoff: float = 1.0,
        rate_limit: Optional[int] = None,
    ):
        """Initialize async HTTP client."""
        self.base_url = base_url
        self.timeout = ClientTimeout(total=timeout)
        self.retry_attempts = retry_attempts
        self.retry_backoff = retry_backoff
        self.rate_limit = rate_limit
        self._session: Optional[ClientSession] = None
        self._semaphore: Optional[asyncio.Semaphore] = None

    async def __aenter__(self) -> "AsyncHTTPClient":
        """Enter async context."""
        await self._initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context."""
        await self.close()

    async def _initialize(self) -> None:
        """Initialize client session and semaphore."""
        if self._session is None:
            self._session = ClientSession(
                timeout=self.timeout,
                headers={"User-Agent": "ChainData/1.0"},
            )
        if self.rate_limit and self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.rate_limit)

    async def close(self) -> None:
        """Close client session."""
        if self._session:
            await self._session.close()
            self._session = None

    async def _make_request(
        self,
        method: str,
        url: StrOrURL,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic."""
        if not self._session:
            await self._initialize()

        for attempt in range(self.retry_attempts):
            try:
                if self._semaphore:
                    async with self._semaphore:
                        async with self._session.request(method, url, **kwargs) as response:
                            response.raise_for_status()
                            return await response.json()
                else:
                    async with self._session.request(method, url, **kwargs) as response:
                        response.raise_for_status()
                        return await response.json()
            except aiohttp.ClientError as e:
                if attempt == self.retry_attempts - 1:
                    raise
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.retry_attempts}): {e}")
                await asyncio.sleep(self.retry_backoff * (attempt + 1))

    def _build_url(self, path: str) -> str:
        """Build full URL from path."""
        return urljoin(self.base_url, path)

    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make GET request."""
        url = self._build_url(path)
        return await self._make_request("GET", url, params=params, headers=headers)

    async def post(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make POST request."""
        url = self._build_url(path)
        return await self._make_request("POST", url, data=data, json=json, headers=headers)

    async def put(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make PUT request."""
        url = self._build_url(path)
        return await self._make_request("PUT", url, data=data, json=json, headers=headers)

    async def delete(
        self,
        path: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make DELETE request."""
        url = self._build_url(path)
        return await self._make_request("DELETE", url, headers=headers) 