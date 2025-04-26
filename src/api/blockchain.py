import requests
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from functools import lru_cache
from ..core.cache import blockchain_cache

class BlockchainAPI:
    def __init__(self):
        self.session = self._create_session()
        self.blockchain_data = []
        self.chain_by_id = {}
        self.chain_by_name = {}
        self.chain_by_short_name = {}
    
    def _create_session(self):
        """Create a requests session with retry logic and connection pooling"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def initialize_data_structures(self, data: List[Dict[str, Any]]):
        """Initialize optimized data structures for lookups"""
        self.blockchain_data = data
        self.chain_by_id = {chain['chainId']: chain for chain in data}
        self.chain_by_name = {chain['name'].lower(): chain for chain in data}
        self.chain_by_short_name = {chain.get('shortName', '').lower(): chain for chain in data if chain.get('shortName')}
    
    def get_all_blockchain_data(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Get all blockchain data with caching"""
        cache_key = 'blockchain_data'
        
        # Try to load from cache first
        if not force_refresh:
            cached_data = blockchain_cache.load_from_cache(cache_key)
            if cached_data is not None:
                self.initialize_data_structures(cached_data)
                return cached_data
        
        # Fetch fresh data
        url = "https://chainlist.org/rpcs.json"
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Save to cache
            blockchain_cache.save_to_cache(cache_key, data)
            self.initialize_data_structures(data)
            return data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching blockchain data: {e}")
            return []
    
    @lru_cache(maxsize=128)
    def get_chain_data_by_id(self, chain_id: int) -> Optional[Dict[str, Any]]:
        """Get chain data by ID with caching"""
        return self.chain_by_id.get(chain_id)
    
    @lru_cache(maxsize=128)
    def get_chain_data_by_name(self, chain_name: str) -> Optional[Dict[str, Any]]:
        """Get chain data by name with caching"""
        return self.chain_by_name.get(chain_name.lower())
    
    def search_chains(self, query: str) -> List[Dict[str, Any]]:
        """Search for chains by name or ID"""
        query = query.lower()
        results = []
        
        # Check chain ID
        try:
            chain_id = int(query)
            if chain_id in self.chain_by_id:
                results.append(self.chain_by_id[chain_id])
        except ValueError:
            pass
        
        # Check chain names
        for chain in self.blockchain_data:
            if (query in chain['name'].lower() or 
                query in chain.get('shortName', '').lower()):
                results.append(chain)
        
        return results
    
    def get_chain_data(self, identifier: Union[int, str]) -> Optional[Dict[str, Any]]:
        """Get chain data by ID or name"""
        if isinstance(identifier, int):
            return self.get_chain_data_by_id(identifier)
        return self.get_chain_data_by_name(identifier)
    
    def get_rpcs(self, identifier: Union[int, str], rpc_type: str, no_tracking: bool = False) -> List[str]:
        """Get RPCs by type"""
        chain_data = self.get_chain_data(identifier)
        if not chain_data:
            return []
        
        rpcs = []
        for rpc in chain_data['rpc']:
            if rpc_type in rpc['url']:
                if not no_tracking or (no_tracking and rpc.get('tracking') == 'none'):
                    rpcs.append(rpc['url'])
        return rpcs
    
    def get_explorer(self, identifier: Union[int, str], explorer_type: Optional[str] = None) -> List[str]:
        """Get explorer by ID or name"""
        chain_data = self.get_chain_data(identifier)
        explorers = []
        if chain_data:
            for explorer in chain_data['explorers']:
                if not explorer_type or explorer['name'] == explorer_type:
                    explorers.append(explorer['url'])
        return explorers
    
    def get_eips(self, identifier: Union[int, str]) -> List[str]:
        """Get EIPs by ID or name"""
        chain_data = self.get_chain_data(identifier)
        eips = []
        if chain_data:
            for eip in chain_data['features']:
                eips.extend(eip.values())
        return eips
    
    def get_native_currency(self, identifier: Union[int, str]) -> Optional[Dict[str, Any]]:
        """Get native currency by ID or name"""
        chain_data = self.get_chain_data(identifier)
        if chain_data:
            return chain_data['nativeCurrency']
        return None
    
    def get_tvl(self, identifier: Union[int, str]) -> Optional[float]:
        """Get TVL by ID or name"""
        chain_data = self.get_chain_data(identifier)
        if chain_data:
            return chain_data['tvl']
        return None
    
    def get_explorer_link(self, chain_id: int, address: str) -> Optional[str]:
        """Get explorer link for an address"""
        chain_data = self.get_chain_data_by_id(chain_id)
        if chain_data:
            for explorer in chain_data['explorers']:
                if explorer['name'] == 'etherscan':
                    return explorer['url'] + '/address/' + address
        return None

# Create a global instance
blockchain_api = BlockchainAPI() 