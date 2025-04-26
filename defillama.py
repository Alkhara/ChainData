import requests
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import json
from functools import lru_cache

class DefiLlamaAPI:
    BASE_URL = "https://api.llama.fi"
    
    def __init__(self):
        self.session = requests.Session()
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a request to the DefiLlama API"""
        url = f"{self.BASE_URL}{endpoint}"
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
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
    
    def get_top_protocols(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top protocols by TVL"""
        all_protocols = self.get_all_protocols()
        return sorted(
            all_protocols,
            key=lambda x: x.get("tvl", 0),
            reverse=True
        )[:limit]
    
    def get_chain_protocols(self, chain: str) -> List[Dict[str, Any]]:
        """Get all protocols on a specific chain"""
        all_protocols = self.get_all_protocols()
        return [
            protocol for protocol in all_protocols
            if chain.lower() in [c.lower() for c in protocol.get("chains", [])]
        ] 