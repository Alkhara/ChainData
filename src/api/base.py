from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class BaseAPI(ABC):
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic and connection pooling"""
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

    @abstractmethod
    def _sanitize_cache_key(self, url: str, params: Optional[Dict] = None) -> str:
        """Create a safe cache key from URL and parameters"""
        pass

    def _make_request(
        self, 
        url: str, 
        params: Optional[Dict] = None,
        method: str = "GET",
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict:
        """Make a request to the API with caching"""
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # TODO: Implement proper logging
            print(f"Error making request to {url}: {e}")
            return {}

    @abstractmethod
    def validate_response(self, response: Dict) -> bool:
        """Validate API response format"""
        pass

    @abstractmethod
    def handle_error(self, error: Exception) -> None:
        """Handle API errors consistently"""
        pass 