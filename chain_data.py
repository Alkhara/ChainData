import sys
import json
import requests
import os
import time
from datetime import datetime
import argparse
from tqdm import tqdm
from colorama import init, Fore, Style
import re
from functools import lru_cache
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, List, Optional, Union, Any
from src.api.defillama import DefiLlamaAPI
from config import config

# Initialize colorama
init()

# Initialize DefiLlama API
defillama = DefiLlamaAPI()

# print a cool welcome message in ascii art saying ChainData
print(f"{Fore.CYAN}")

print("""

 ░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░░▒▓█▓▒░▒▓███████▓▒░░▒▓███████▓▒░ ░▒▓██████▓▒░▒▓████████▓▒░▒▓██████▓▒░  
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░      ░▒▓████████▓▒░▒▓████████▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓████████▓▒░ ░▒▓█▓▒░  ░▒▓████████▓▒░ 
░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░ 
 ░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░ 
                                                                                                              
                                                                                                              

""")

print(f"{Style.RESET_ALL}")

CACHE_FILE = os.path.join(config.get('cache.directory'), config.get('cache.blockchain_subdir'), 'blockchain_data_cache.json')

def print_error(message):
    print(f"{Fore.RED}Error: {message}{Style.RESET_ALL}")

def print_success(message):
    print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")

def print_info(message):
    print(f"{Fore.CYAN}{message}{Style.RESET_ALL}")

def print_warning(message):
    print(f"{Fore.YELLOW}Warning: {message}{Style.RESET_ALL}")

# Initialize data structures
blockchain_data = []
chain_by_id = {}
chain_by_name = {}
chain_by_short_name = {}

def initialize_data_structures(data):
    """Initialize optimized data structures for lookups"""
    global blockchain_data, chain_by_id, chain_by_name, chain_by_short_name
    blockchain_data = data
    chain_by_id = {chain['chainId']: chain for chain in data}
    chain_by_name = {chain['name'].lower(): chain for chain in data}
    chain_by_short_name = {chain.get('shortName', '').lower(): chain for chain in data if chain.get('shortName')}

def create_session():
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

def get_all_blockchain_data(force_refresh=False):
    # Check if cache exists and is fresh
    if not force_refresh and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                cache = json.load(f)
            last_updated = cache.get('last_updated', 0)
            if last_updated:
                last_updated_str = datetime.fromtimestamp(last_updated).strftime('%Y-%m-%d %H:%M:%S')
                print_info(f"Data last updated: {last_updated_str}")
            if time.time() - last_updated < config.get('cache.expiry_seconds'):
                print_success("Using cached data")
                data = cache.get('data', [])
                initialize_data_structures(data)
                return data
        except Exception as e:
            print_error(f"Error reading cache: {e}")
            pass  # If cache is corrupted, fetch fresh
    
    # Fetch fresh data
    print_info("Fetching fresh data...")
    url = "https://chainlist.org/rpcs.json"
    try:
        session = create_session()
        response = session.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        print_success(f"Fetched {len(data)} chains from API")
        
        # Save to cache
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, 'w') as f:
            json.dump({'last_updated': time.time(), 'data': data}, f)
        
        initialize_data_structures(data)
        return data
    except requests.exceptions.RequestException as e:
        print_error(f"Failed to fetch data: {e}")
        return []

# Initialize blockchain data
blockchain_data = get_all_blockchain_data()

@lru_cache(maxsize=128)
def get_chain_data_by_id(chain_id):
    """Get chain data by ID with caching"""
    return chain_by_id.get(chain_id)

@lru_cache(maxsize=128)
def get_chain_data_by_name(chain_name):
    """Get chain data by name with caching"""
    return chain_by_name.get(chain_name.lower())

def search_chains(query):
    """Search for chains by name or ID with optimized lookups"""
    query = query.lower()
    results = []
    
    # Check chain ID
    try:
        chain_id = int(query)
        if chain_id in chain_by_id:
            results.append(chain_by_id[chain_id])
    except ValueError:
        pass
    
    # Check chain names
    for chain in blockchain_data:
        if (query in chain['name'].lower() or 
            query in chain.get('shortName', '').lower()):
            results.append(chain)
    
    return results

def list_chains(format='table'):
    """List all available chains"""
    if format == 'table':
        print(f"\n{Fore.CYAN}Available Chains:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'ID':<8} {'Name':<30} {'Short Name':<15}{Style.RESET_ALL}")
        print("-" * 55)
        for chain in sorted(blockchain_data, key=lambda x: x['chainId']):
            print(f"{chain['chainId']:<8} {chain['name']:<30} {chain.get('shortName', 'N/A'):<15}")
    elif format == 'json':
        print(json.dumps(blockchain_data, indent=2))

def get_chain_data(identifier):
    """Get chain data by ID or name"""
    if isinstance(identifier, int):
        return get_chain_data_by_id(identifier)
    return get_chain_data_by_name(identifier)

def get_rpcs_parallel(chain_data, rpc_type, no_tracking=False):
    """Get RPCs in parallel using thread pool"""
    rpcs = []
    if not chain_data:
        return rpcs
    
    def process_rpc(rpc):
        if rpc_type in rpc['url']:
            if not no_tracking or (no_tracking and rpc.get('tracking') == 'none'):
                return rpc['url']
        return None
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_rpc, rpc) for rpc in chain_data['rpc']]
        for future in as_completed(futures):
            result = future.result()
            if result:
                rpcs.append(result)
    
    return rpcs

def get_rpcs(identifier, rpc_type, no_tracking=False):
    """Unified function to get RPCs by type"""
    chain_data = get_chain_data(identifier)
    return get_rpcs_parallel(chain_data, rpc_type, no_tracking)

def get_http_rpcs(identifier, no_tracking=False):
    """Get HTTP RPCs by ID or name with parallel processing"""
    return get_rpcs(identifier, 'https', no_tracking)

def get_wss_rpcs(identifier, no_tracking=False):
    """Get WSS RPCs by ID or name with parallel processing"""
    return get_rpcs(identifier, 'wss', no_tracking)

def get_explorer(identifier, explorer_type=None):
    """Get explorer by ID or name"""
    chain_data = get_chain_data(identifier)
    explorers = []
    if chain_data:
        for explorer in chain_data['explorers']:
            if not explorer_type or explorer['name'] == explorer_type:
                explorers.append(explorer['url'])
    return explorers

def get_eips(identifier):
    """Get EIPs by ID or name"""
    chain_data = get_chain_data(identifier)
    eips = []
    if chain_data:
        for eip in chain_data['features']:
            eips.extend(eip.values())
    return eips

def get_native_currency(identifier):
    """Get native currency by ID or name"""
    chain_data = get_chain_data(identifier)
    if chain_data:
        return chain_data['nativeCurrency']
    return None

def get_tvl(identifier):
    """Get TVL by ID or name"""
    chain_data = get_chain_data(identifier)
    if chain_data:
        return chain_data['tvl']
    return None

def chain_id_to_name(chain_id):
    """Convert chain ID to chain name"""
    chain = get_chain_data_by_id(chain_id)
    return chain['name'] if chain else None

def get_explorer_link(chain_id, address):
    """Get explorer link for an address"""
    chain_data = get_chain_data_by_id(chain_id)
    if chain_data:
        for explorer in chain_data['explorers']:
            if explorer['name'] == 'etherscan':
                return explorer['url'] + '/address/' + address
    return None

def cleanup_resources():
    """Clean up resources and clear caches"""
    global blockchain_data, chain_by_id, chain_by_name, chain_by_short_name
    blockchain_data = []
    chain_by_id.clear()
    chain_by_name.clear()
    chain_by_short_name.clear()
    # Only clear cache if the functions have been decorated
    if hasattr(get_chain_data_by_id, 'cache_clear'):
        get_chain_data_by_id.cache_clear()
    if hasattr(get_chain_data_by_name, 'cache_clear'):
        get_chain_data_by_name.cache_clear()

def get_protocol_tvl(protocol: str) -> Dict:
    """Get TVL data for a protocol"""
    return defillama.get_protocol_info(protocol)

def get_chain_tvl(chain: str, limit: Optional[int] = None) -> Dict:
    """Get chain TVL"""
    if limit is None:
        limit = config.get('display.max_tvl_history')
    result = defillama.get_chain_tvl(chain)
    if limit and isinstance(result, dict):
        return {k: v[:limit] if isinstance(v, list) else v for k, v in result.items()}
    return result

def search_protocols(query: str) -> List[Dict]:
    """Search for DeFi protocols"""
    results = defillama.search_protocols(query)
    max_results = config.get('display.max_search_results')
    return results[:max_results] if max_results else results

def get_top_protocols(limit: Optional[int] = None) -> List[Dict]:
    """Get top protocols by TVL"""
    if limit is None:
        limit = config.get('display.max_protocols')
    return defillama.get_top_protocols(limit)

def get_chain_protocols(chain: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get all protocols on a specific chain, optionally limited to top N by TVL"""
    if limit is None:
        limit = config.get('display.max_protocols')
    protocols = defillama.get_chain_protocols(chain)
    if limit:
        # Sort by TVL and take top N
        protocols = sorted(
            protocols,
            key=lambda x: x.get("tvl", 0) or 0,
            reverse=True
        )[:limit]
    return protocols

def print_protocol_info(protocol_data: Dict[str, Any]):
    """Print formatted protocol information"""
    print(f"\n{Fore.CYAN}Protocol: {protocol_data['name']}{Style.RESET_ALL}")
    print(f"Current TVL: ${protocol_data['current_tvl']:,.2f}")
    
    if 'tvl_history' in protocol_data and isinstance(protocol_data['tvl_history'], dict):
        print(f"\n{Fore.CYAN}TVL History (Most Recent First):{Style.RESET_ALL}")
        # Get the TVL history and sort by date in descending order
        history = protocol_data['tvl_history'].get('tvl', [])
        if history:
            # Sort by date in descending order
            sorted_history = sorted(history, key=lambda x: x['date'], reverse=True)
            # Take the first N entries (most recent)
            for entry in sorted_history[:config.get('display.max_history_entries')]:
                date = datetime.fromtimestamp(entry['date']).strftime(config.get('display.date_format'))
                print(f"{date}: ${entry['totalLiquidityUSD']:,.2f}")
        else:
            print_warning("No TVL history data available")
    else:
        print_warning("No TVL history data available")

def get_pools(limit: Optional[int] = None, min_tvl: Optional[float] = None, min_apy: Optional[float] = None) -> List[Dict]:
    """Get yield pools with optional filtering"""
    if limit is None:
        limit = config.get('display.max_pools')
    pools = defillama.get_pools()
    if isinstance(pools, list):
        # Apply filters
        if min_tvl is not None:
            pools = [p for p in pools if p.get('tvlUsd', 0) >= min_tvl]
        if min_apy is not None:
            pools = [p for p in pools if p.get('apy', 0) >= min_apy]
        
        # Sort by APY in descending order
        pools = sorted(pools, key=lambda x: x.get('apy', 0) or 0, reverse=True)
        
        # Format the results as a table
        if pools:
            print("\nYield Pools:")
            print("-" * 100)
            # Left-align text columns, right-align numeric columns
            headers = [
                f"{'Project':<25}",
                f"{'Chain':<12}",
                f"{'Symbol':<20}",
                f"{'APY':>15}",
                f"{'TVL (USD)':>15}"
            ]
            print("".join(headers))
            print("-" * 100)
            
            for pool in pools[:limit]:
                project = pool.get('project', 'N/A')[:24]  # Truncate long names
                chain = pool.get('chain', 'N/A')[:11]
                symbol = pool.get('symbol', 'N/A')[:19]
                apy = f"{pool.get('apy', 0):,.2f}%"
                tvl = f"${pool.get('tvlUsd', 0):,.2f}"
                
                # Format each column with proper alignment
                columns = [
                    f"{project:<25}",
                    f"{chain:<12}",
                    f"{symbol:<20}",
                    f"{apy:>15}",
                    f"{tvl:>15}"
                ]
                print("".join(columns))
            
            print("-" * 100)
            print(f"Showing {min(len(pools), limit)} of {len(pools)} pools")
            if min_tvl is not None:
                print(f"Minimum TVL: ${min_tvl:,.2f}")
            if min_apy is not None:
                print(f"Minimum APY: {min_apy:.2f}%")
        
        return pools[:limit]
    return pools

def get_stablecoins(limit: Optional[int] = None) -> List[Dict]:
    """Get stablecoins"""
    if limit is None:
        limit = config.get('display.max_stablecoins')
    stablecoins = defillama.get_stablecoins()
    if isinstance(stablecoins, list):
        return stablecoins[:limit]
    elif isinstance(stablecoins, dict):
        return list(stablecoins.values())[:limit]
    return stablecoins

def get_dex_overview(limit: Optional[int] = None) -> List[Dict]:
    """Get DEX overview"""
    if limit is None:
        limit = config.get('display.max_dexes')
    dexs = defillama.get_dex_overview()
    if isinstance(dexs, list):
        return dexs[:limit]
    elif isinstance(dexs, dict):
        return list(dexs.values())[:limit]
    return dexs

def get_options_overview(limit: Optional[int] = None) -> List[Dict]:
    """Get options overview"""
    if limit is None:
        limit = config.get('display.max_options')
    options = defillama.get_options_overview()
    if isinstance(options, list):
        return options[:limit]
    elif isinstance(options, dict):
        return list(options.values())[:limit]
    return options

def get_fees_overview(limit: Optional[int] = None) -> List[Dict]:
    """Get fees overview"""
    if limit is None:
        limit = config.get('display.max_fees')
    fees = defillama.get_fees_overview()
    if isinstance(fees, list):
        return fees[:limit]
    elif isinstance(fees, dict):
        return list(fees.values())[:limit]
    return fees

def get_current_prices(coins: List[str], limit: Optional[int] = None) -> Dict:
    """Get current prices"""
    if limit is None:
        limit = config.get('display.max_prices')
    result = defillama.get_current_prices(coins)
    if limit and isinstance(result, dict):
        return dict(list(result.items())[:limit])
    return result

def get_historical_prices(coins: List[str], timestamp: int, limit: Optional[int] = None) -> Dict:
    """Get historical prices"""
    if limit is None:
        limit = config.get('display.max_price_history')
    result = defillama.get_historical_prices(coins, timestamp)
    if limit and isinstance(result, dict):
        return dict(list(result.items())[:limit])
    return result

def get_price_chart(coins: List[str], period: str, limit: Optional[int] = None) -> Dict:
    """Get price chart"""
    if limit is None:
        limit = config.get('display.max_price_history')
    result = defillama.get_price_chart(coins, period)
    if limit and isinstance(result, dict):
        return {k: v[:limit] if isinstance(v, list) else v for k, v in result.items()}
    return result

def get_volume_history(protocol: str, limit: Optional[int] = None) -> Dict:
    """Get volume history"""
    if limit is None:
        limit = config.get('display.max_volume_history')
    result = defillama.get_volume_history(protocol)
    if limit and isinstance(result, dict):
        return {k: v[:limit] if isinstance(v, list) else v for k, v in result.items()}
    return result

def get_fee_history(protocol: str, limit: Optional[int] = None) -> Dict:
    """Get fee history"""
    if limit is None:
        limit = config.get('display.max_fee_history')
    result = defillama.get_fee_history(protocol)
    if limit and isinstance(result, dict):
        return {k: v[:limit] if isinstance(v, list) else v for k, v in result.items()}
    return result

def main():
    try:
        parser = argparse.ArgumentParser(description='ChainData - Get blockchain information')
        
        # Add mutually exclusive group for chain identifier
        identifier_group = parser.add_mutually_exclusive_group(required=False)
        identifier_group.add_argument('-c', '--chain-id', type=int, help='Chain ID')
        identifier_group.add_argument('-n', '--name', type=str, help='Chain name')
        identifier_group.add_argument('-s', '--search', type=str, help='Search for chains')
        identifier_group.add_argument('-l', '--list', action='store_true', help='List all available chains')
        
        # Add DefiLlama specific arguments
        parser.add_argument('--protocol', type=str, help='Protocol name for TVL data')
        parser.add_argument('--top-protocols', type=int, help='Get top N protocols by TVL')
        parser.add_argument('--chain-protocols', type=str, help='Get all protocols on a specific chain')
        parser.add_argument('--limit', type=int, help='Limit the number of protocols shown')
        parser.add_argument('--target-chain', type=str, help='Target chain for chain-specific operations')
        parser.add_argument('--pool-id', type=str, help='Pool ID for yield/APY data')
        parser.add_argument('--coins', type=str, help='Comma-separated list of coins for price data')
        parser.add_argument('--timestamp', type=int, help='Timestamp for historical data')
        parser.add_argument('--period', type=str, help='Time period for charts (e.g., 24h, 7d)')
        parser.add_argument('--data-type', type=str, choices=['dailyFees', 'dailyRevenue', 'dailyNotionalVolume', 'dailyPremiumVolume'],
                          help='Data type for fees/volumes')
        
        # Add filter arguments for get-pools
        parser.add_argument('--min-tvl', type=str, help='Minimum TVL in USD for yield pools')
        parser.add_argument('--min-apy', type=str, help='Minimum APY percentage for yield pools')
        
        # Add function argument
        parser.add_argument('-f', '--function', type=str, required=False, choices=[
            # Chain functions
            'http-rpcs', 'wss-rpcs', 'explorer', 'eips', 
            'native-currency', 'tvl', 'chain-data', 'explorer-link',
            
            # TVL functions
            'protocol-tvl', 'chain-tvl', 'search-protocols',
            
            # Stablecoin functions
            'get-stablecoins', 'get-stablecoin-charts', 'get-chain-stablecoin-charts',
            'get-stablecoin-data', 'get-stablecoin-chains', 'get-stablecoin-prices',
            
            # Yield/APY functions
            'get-pools', 'get-pool-chart',
            
            # DEX functions
            'get-dex-overview', 'get-chain-dex-overview', 'get-dex-summary',
            'get-options-overview', 'get-chain-options-overview', 'get-options-summary',
            
            # Fee/Revenue functions
            'get-fees-overview', 'get-chain-fees-overview', 'get-fees-summary',
            
            # Price functions
            'get-current-prices', 'get-historical-prices', 'get-batch-historical-prices',
            'get-price-chart', 'get-price-percentage', 'get-first-price'
        ], help='Function to execute')
        
        # Add format argument
        parser.add_argument('-o', '--format', type=str, choices=['table', 'json'], default='table',
                           help='Output format (table or json)')
        
        # Add other arguments
        parser.add_argument('-t', '--no-tracking', action='store_true', help='Exclude tracking RPCs')
        parser.add_argument('-e', '--explorer-type', type=str, help='Specific explorer type')
        parser.add_argument('-a', '--address', type=str, help='Address for explorer link')
        parser.add_argument('-r', '--force-refresh', action='store_true', help='Force refresh cache')
        
        args = parser.parse_args()
        
        if args.force_refresh:
            cleanup_resources()
            global blockchain_data
            blockchain_data = get_all_blockchain_data(force_refresh=True)
        
        # Handle DefiLlama specific commands first
        if args.function == 'search-protocols':
            if not args.search:
                print_error("Error: --search is required for protocol search")
                return
            results = search_protocols(args.search)
            if results:
                print(f"\n{Fore.CYAN}Search Results:{Style.RESET_ALL}")
                for protocol in results:
                    tvl = protocol.get('tvl', 0) or 0
                    print(f"{protocol['name']}: ${tvl:,.2f}")
            else:
                print_warning(f"No protocols found matching '{args.search}'")
            return
        
        if args.protocol:
            protocol_data = get_protocol_tvl(args.protocol)
            print_protocol_info(protocol_data)
            return
        
        if args.top_protocols:
            top_protocols = get_top_protocols(args.top_protocols)
            print(f"\n{Fore.CYAN}Top {args.top_protocols} Protocols by TVL:{Style.RESET_ALL}")
            for i, protocol in enumerate(top_protocols, 1):
                print(f"{i}. {protocol['name']}: ${protocol.get('tvl', 0):,.2f}")
            return
        
        if args.chain_protocols:
            chain_protocols = get_chain_protocols(args.chain_protocols, args.limit)
            limit_text = f" (Top {args.limit})" if args.limit else ""
            print(f"\n{Fore.CYAN}Protocols on {args.chain_protocols}{limit_text}:{Style.RESET_ALL}")
            for i, protocol in enumerate(chain_protocols, 1):
                print(f"{i}. {protocol['name']}: ${protocol.get('tvl', 0):,.2f}")
            return

        # Handle yield/APY functions
        if args.function == 'get-pools':
            # Parse filter arguments
            min_tvl = None
            min_apy = None
            if args.min_tvl:
                try:
                    min_tvl = float(args.min_tvl)
                except ValueError:
                    print_error("Error: --min-tvl must be a number")
                    return
            if args.min_apy:
                try:
                    min_apy = float(args.min_apy)
                except ValueError:
                    print_error("Error: --min-apy must be a number")
                    return
            
            result = get_pools(limit=args.limit, min_tvl=min_tvl, min_apy=min_apy)
            if args.format == 'json':
                print(json.dumps(result, indent=2))
            return

        if args.function == 'get-pool-chart':
            if not args.pool_id:
                print_error("Error: --pool-id is required for pool chart")
                return
            result = defillama.get_pool_chart(args.pool_id)
            print(json.dumps(result, indent=2))
            return

        # Handle stablecoin functions
        if args.function == 'get-stablecoins':
            result = get_stablecoins()
            print(json.dumps(result, indent=2))
            return

        if args.function == 'get-stablecoin-charts':
            result = defillama.get_stablecoin_charts()
            print(json.dumps(result, indent=2))
            return

        if args.function == 'get-chain-stablecoin-charts':
            if not args.target_chain:
                print_error("Error: --target-chain is required for chain-specific stablecoin charts")
                return
            result = defillama.get_chain_stablecoin_charts(args.target_chain)
            print(json.dumps(result, indent=2))
            return

        # Handle price functions
        if args.function == 'get-current-prices':
            if not args.coins:
                print_error("Error: --coins is required for current prices")
                return
            coins = args.coins.split(',')
            result = get_current_prices(coins)
            print(json.dumps(result, indent=2))
            return

        if args.function == 'get-historical-prices':
            if not args.coins or not args.timestamp:
                print_error("Error: --coins and --timestamp are required for historical prices")
                return
            coins = args.coins.split(',')
            result = get_historical_prices(coins, args.timestamp)
            print(json.dumps(result, indent=2))
            return

        # Handle DEX functions
        if args.function == 'get-dex-overview':
            result = get_dex_overview()
            print(json.dumps(result, indent=2))
            return

        if args.function == 'get-chain-dex-overview':
            if not args.target_chain:
                print_error("Error: --target-chain is required for chain-specific DEX overview")
                return
            result = defillama.get_chain_dex_overview(args.target_chain)
            print(json.dumps(result, indent=2))
            return

        # Handle fee/revenue functions
        if args.function == 'get-fees-overview':
            result = get_fees_overview()
            print(json.dumps(result, indent=2))
            return

        if args.function == 'get-chain-fees-overview':
            if not args.target_chain:
                print_error("Error: --target-chain is required for chain-specific fees overview")
                return
            result = defillama.get_chain_fees_overview(args.target_chain, data_type=args.data_type)
            print(json.dumps(result, indent=2))
            return

        # Handle chain-specific functions
        if not args.function:
            print_error("Error: --function is required for chain-specific operations. Use --list-functions to see available options.")
            return
        
        if not (args.chain_id or args.name):
            print_error("Error: Either --chain-id or --name must be provided for chain-specific operations.")
            return
        
        # Determine identifier
        identifier = args.chain_id if args.chain_id is not None else args.name
        
        # Validate chain ID if provided
        if isinstance(identifier, int):
            chain_data = get_chain_data_by_id(identifier)
            if not chain_data:
                print_error(f"Chain ID {identifier} not found.")
                print_info("Available chains:")
                list_chains(format='table')
                print("\nPlease try again with a valid chain ID.")
                return
        
        # Call appropriate function
        if args.function == 'http-rpcs':
            result = get_http_rpcs(identifier, args.no_tracking)
        elif args.function == 'wss-rpcs':
            result = get_wss_rpcs(identifier, args.no_tracking)
        elif args.function == 'explorer':
            result = get_explorer(identifier, args.explorer_type)
        elif args.function == 'eips':
            result = get_eips(identifier)
        elif args.function == 'native-currency':
            result = get_native_currency(identifier)
        elif args.function == 'tvl':
            result = get_tvl(identifier)
        elif args.function == 'chain-data':
            result = get_chain_data(identifier)
        elif args.function == 'explorer-link':
            result = get_explorer_link(identifier, args.address)
        
        # Print result
        if isinstance(identifier, int):
            chain_name = chain_id_to_name(identifier)
            print_info(f"Network: {chain_name if chain_name else 'Unknown'}")
        else:
            print_info(f"Network: {identifier}")

        print_info(f"Function: {args.function}")
        if isinstance(result, (list, dict)):
            print(json.dumps(result, indent=2))
        else:
            print(result)
    finally:
        cleanup_resources()

if __name__ == '__main__':
    main()





























