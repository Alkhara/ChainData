import requests
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import json
import os
from functools import lru_cache
import time
from config import config

class DefiLlamaAPI:
    def __init__(self):
        self.session = requests.Session()
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Ensure the cache directory exists"""
        cache_dir = os.path.join(
            config.get('cache.directory'),
            config.get('cache.defillama_subdir')
        )
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def _get_cache_path(self, endpoint: str) -> str:
        """Get the cache file path for an endpoint"""
        # Convert endpoint to a valid filename
        filename = endpoint.replace('/', '_').strip('_')
        cache_dir = os.path.join(
            config.get('cache.directory'),
            config.get('cache.defillama_subdir')
        )
        return os.path.join(cache_dir, f"{filename}.json")
    
    def _load_from_cache(self, cache_path: str) -> Optional[Dict[str, Any]]:
        """Load data from cache if it exists and is not expired"""
        if not config.get('cache.enabled'):
            return None
            
        if not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
            
            # Check if cache is expired
            if time.time() - cache_data.get('timestamp', 0) > config.get('cache.expiry_seconds'):
                return None
            
            return cache_data.get('data')
        except (json.JSONDecodeError, KeyError):
            return None
    
    def _save_to_cache(self, cache_path: str, data: Dict[str, Any]):
        """Save data to cache with timestamp"""
        if not config.get('cache.enabled'):
            return
            
        try:
            with open(cache_path, 'w') as f:
                json.dump({
                    'timestamp': time.time(),
                    'data': data
                }, f)
        except Exception as e:
            print(f"Warning: Failed to save cache: {e}")
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a request to the DefiLlama API with caching"""
        cache_path = self._get_cache_path(endpoint)
        
        # Try to load from cache first
        cached_data = self._load_from_cache(cache_path)
        if cached_data is not None:
            return cached_data
        
        # If not in cache or expired, make the request
        url = f"{config.get('api.defillama_base_url')}{endpoint}"
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Save to cache
            self._save_to_cache(cache_path, data)
            return data
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {url}: {e}")
            return {}
    
    @lru_cache(maxsize=128)
    def get_all_protocols(self) -> List[Dict[str, Any]]:
        """Get list of all protocols with their TVL"""
        return self._make_request("/protocols")
    
    @lru_cache(maxsize=128)
    def get_protocol_tvl(self, protocol: str) -> Dict[str, Any]:
        """Get historical TVL of a protocol and breakdowns by token and chain"""
        return self._make_request(f"/protocol/{protocol}")
    
    @lru_cache(maxsize=128)
    def get_current_tvl(self, protocol: str) -> float:
        """Get current TVL of a protocol"""
        response = self._make_request(f"/tvl/{protocol}")
        return float(response) if response else 0.0
    
    @lru_cache(maxsize=128)
    def get_historical_chain_tvl(self, chain: Optional[str] = None) -> Dict[str, Any]:
        """Get historical TVL of DeFi on all chains or a specific chain"""
        endpoint = "/v2/historicalChainTvl"
        if chain:
            endpoint = f"{endpoint}/{chain}"
        return self._make_request(endpoint)
    
    @lru_cache(maxsize=128)
    def get_all_chains_tvl(self) -> Dict[str, Any]:
        """Get current TVL of all chains"""
        return self._make_request("/v2/chains")
    
    def get_protocol_info(self, protocol: str) -> Dict[str, Any]:
        """Get comprehensive protocol information including TVL history"""
        tvl_history = self.get_protocol_tvl(protocol)
        current_tvl = self.get_current_tvl(protocol)
        
        return {
            "name": protocol,
            "current_tvl": current_tvl,
            "tvl_history": tvl_history
        }
    
    def search_protocols(self, query: str) -> List[Dict[str, Any]]:
        """Search for protocols by name"""
        query = query.lower()
        all_protocols = self.get_all_protocols()
        return [
            protocol for protocol in all_protocols
            if query in protocol.get("name", "").lower() or
               query in protocol.get("slug", "").lower()
        ]
    
    def get_top_protocols(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get top protocols by TVL"""
        all_protocols = self.get_all_protocols()
        if limit is None:
            limit = config.get('display.max_protocols')
        # Sort by TVL, treating None as 0
        return sorted(
            all_protocols,
            key=lambda x: x.get("tvl", 0) or 0,  # Convert None to 0
            reverse=True
        )[:limit]
    
    def get_chain_protocols(self, chain: str) -> List[Dict[str, Any]]:
        """Get all protocols on a specific chain"""
        all_protocols = self.get_all_protocols()
        return [
            protocol for protocol in all_protocols
            if chain.lower() in [c.lower() for c in protocol.get("chains", [])]
        ] 