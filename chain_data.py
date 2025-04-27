import argparse
import json
import os
import re
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional, Union

import requests
from colorama import Fore, Style, init
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from urllib3.util.retry import Retry

from src.api.chainlist import chainlist_api  # Import the global instance
from src.api.defillama import DefiLlamaAPI
from src.core.config import config
from src.utils.display import (
    format_chain_data,
    format_chain_info,
    format_dex_data,
    format_options_data,
    format_pool_chart,
    format_pool_data,
    format_price_chart,
    format_price_data,
    format_price_history,
    format_rpc_data,
    print_error,
    print_info,
    print_success,
    print_warning,
)
from src.api.etherscan import etherscan_api
from src.models.etherscan import Transaction, TokenTransfer, ContractSource

# Initialize colorama
init()

# Initialize APIs
defillama_api = DefiLlamaAPI()

# print a cool welcome message in ascii art saying ChainData
print(f"{Fore.CYAN}")

print(
    """

 ░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░░▒▓█▓▒░▒▓███████▓▒░░▒▓███████▓▒░ ░▒▓██████▓▒░▒▓████████▓▒░▒▓██████▓▒░  
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░      ░▒▓████████▓▒░▒▓████████▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓████████▓▒░ ░▒▓█▓▒░  ░▒▓████████▓▒░ 
░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░ 
 ░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░ 
                                                                                                              
                                                                                                              

"""
)

print(f"{Style.RESET_ALL}")

CACHE_FILE = os.path.join(
    config.get("cache.directory"),
    config.get("cache.blockchain_subdir"),
    "blockchain_data_cache.json",
)


def initialize_data_structures(data):
    """Initialize optimized data structures for lookups"""
    global blockchain_data, chain_by_id, chain_by_name, chain_by_short_name
    blockchain_data = data
    chain_by_id = {chain["chainId"]: chain for chain in data}
    chain_by_name = {chain["name"].lower(): chain for chain in data}
    chain_by_short_name = {
        chain.get("shortName", "").lower(): chain
        for chain in data
        if chain.get("shortName")
    }


def create_session():
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


def get_all_blockchain_data(force_refresh=False):
    # Check if cache exists and is fresh
    if not force_refresh and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cache = json.load(f)
            last_updated = cache.get("last_updated", 0)
            if last_updated:
                last_updated_str = datetime.fromtimestamp(last_updated).strftime(
                    config.get("display.date_format")
                )
                print_info(f"Data last updated: {last_updated_str}")
            if time.time() - last_updated < config.get("cache.expiry_seconds"):
                print_success("Using cached data")
                data = cache.get("data", [])
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
        with open(CACHE_FILE, "w") as f:
            json.dump({"last_updated": time.time(), "data": data}, f)

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
        if (
            query in chain["name"].lower()
            or query in chain.get("shortName", "").lower()
        ):
            results.append(chain)

    return results


def list_chains(format="table"):
    """List all available chains"""
    if format == "table":
        print(f"\n{Fore.CYAN}Available Chains:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'ID':<8} {'Name':<30} {'Short Name':<15}{Style.RESET_ALL}")
        print("-" * 55)
        for chain in sorted(blockchain_data, key=lambda x: x["chainId"]):
            print(
                f"{chain['chainId']:<8} {chain['name']:<30} {chain.get('shortName', 'N/A'):<15}"
            )
    elif format == "json":
        print(json.dumps(blockchain_data, indent=2))


def get_chain_data(identifier):
    """Get chain data by ID or name"""
    if isinstance(identifier, int):
        return get_chain_data_by_id(identifier)
    return get_chain_data_by_name(identifier)


def get_rpcs(identifier, rpc_type, no_tracking=False):
    """Unified function to get RPCs by type"""
    return chainlist_api.get_rpcs(identifier, rpc_type, no_tracking)


def get_http_rpcs(identifier, no_tracking=False):
    """Get HTTP RPCs by ID or name with parallel processing"""
    return get_rpcs(identifier, "https", no_tracking)


def get_wss_rpcs(identifier, no_tracking=False):
    """Get WSS RPCs by ID or name with parallel processing"""
    return get_rpcs(identifier, "wss", no_tracking)


def get_explorer(identifier, explorer_type=None):
    """Get explorer by ID or name"""
    chain_data = get_chain_data(identifier)
    explorers = []
    if chain_data:
        for explorer in chain_data["explorers"]:
            if not explorer_type or explorer["name"] == explorer_type:
                explorers.append(explorer["url"])
    return explorers


def get_eips(identifier):
    """Get EIPs by ID or name"""
    chain_data = get_chain_data(identifier)
    eips = []
    if chain_data:
        for eip in chain_data["features"]:
            eips.extend(eip.values())
    return eips


def get_native_currency(identifier):
    """Get native currency by ID or name"""
    chain_data = get_chain_data(identifier)
    if chain_data:
        return chain_data["nativeCurrency"]
    return None


def get_tvl(identifier):
    """Get TVL by ID or name"""
    chain_data = get_chain_data(identifier)
    if chain_data:
        return chain_data["tvl"]
    return None


def chain_id_to_name(chain_id):
    """Convert chain ID to chain name"""
    chain = get_chain_data_by_id(chain_id)
    return chain["name"] if chain else None


def get_explorer_link(chain_id, address):
    """Get explorer link for an address"""
    chain_data = get_chain_data_by_id(chain_id)
    if chain_data:
        for explorer in chain_data["explorers"]:
            if explorer["name"] == "etherscan":
                return explorer["url"] + "/address/" + address
    return None


def cleanup_resources():
    """Clean up resources and clear caches"""
    global blockchain_data, chain_by_id, chain_by_name, chain_by_short_name
    blockchain_data = []
    chain_by_id.clear()
    chain_by_name.clear()
    chain_by_short_name.clear()
    # Only clear cache if the functions have been decorated
    if hasattr(get_chain_data_by_id, "cache_clear"):
        get_chain_data_by_id.cache_clear()
    if hasattr(get_chain_data_by_name, "cache_clear"):
        get_chain_data_by_name.cache_clear()


def get_protocol_tvl(protocol: str) -> Dict:
    """Get TVL data for a protocol"""
    return defillama_api.get_protocol_info(protocol)


def get_chain_tvl(chain: str, limit: Optional[int] = None) -> Dict:
    """Get chain TVL"""
    if limit is None:
        limit = config.get("display.max_tvl_history")
    result = defillama_api.get_chain_tvl(chain)
    if limit and isinstance(result, dict):
        return {k: v[:limit] if isinstance(v, list) else v for k, v in result.items()}
    return result


def search_protocols(query: str) -> List[Dict]:
    """Search for DeFi protocols"""
    return defillama_api.search_protocols(query)


def get_top_protocols(limit: Optional[int] = None) -> List[Dict]:
    """Get top protocols by TVL"""
    if limit is None:
        limit = config.get("display.max_protocols")
    return defillama_api.get_top_protocols(limit)


def get_chain_protocols(
    chain: str, limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Get all protocols on a specific chain, optionally limited to top N by TVL"""
    if limit is None:
        limit = config.get("display.max_protocols")
    protocols = defillama_api.get_chain_protocols(chain)
    if limit:
        # Sort by TVL and take top N
        protocols = sorted(protocols, key=lambda x: x.get("tvl", 0) or 0, reverse=True)[
            :limit
        ]
    return protocols


def print_protocol_info(protocol_data: Dict[str, Any]):
    """Print formatted protocol information"""
    print(f"\n{Fore.CYAN}Protocol: {protocol_data['name']}{Style.RESET_ALL}")
    print(f"Current TVL: ${protocol_data['current_tvl']:,.2f}")

    if "tvl_history" in protocol_data and isinstance(
        protocol_data["tvl_history"], dict
    ):
        print(f"\n{Fore.CYAN}TVL History (Most Recent First):{Style.RESET_ALL}")
        # Get the TVL history and sort by date in descending order
        history = protocol_data["tvl_history"].get("tvl", [])
        if history:
            # Sort by date in descending order
            sorted_history = sorted(history, key=lambda x: x["date"], reverse=True)
            # Take the first N entries (most recent)
            for entry in sorted_history[: config.get("display.max_history_entries")]:
                date = datetime.fromtimestamp(entry["date"]).strftime(
                    config.get("display.date_format")
                )
                print(f"{date}: ${entry['totalLiquidityUSD']:,.2f}")
        else:
            print_warning("No TVL history data available")
    else:
        print_warning("No TVL history data available")


def get_pools(
    limit: Optional[int] = None,
    min_tvl: Optional[float] = None,
    min_apy: Optional[float] = None,
) -> List[Dict]:
    """Get yield pools with optional filtering"""
    pools = defillama_api.get_pools()

    # Apply filters
    if min_tvl is not None:
        pools = [p for p in pools if p.get("tvlUsd", 0) >= min_tvl]
    if min_apy is not None:
        pools = [p for p in pools if p.get("apy", 0) >= min_apy]

    # Sort by APY in descending order
    pools = sorted(pools, key=lambda x: x.get("apy", 0) or 0, reverse=True)

    # Apply limit
    if limit is not None:
        pools = pools[:limit]

    return pools


def get_stablecoins(limit: Optional[int] = None) -> List[Dict]:
    """Get stablecoins"""
    if limit is None:
        limit = config.get("display.max_stablecoins")
    stablecoins = defillama_api.get_stablecoins()
    if isinstance(stablecoins, list):
        return stablecoins[:limit]
    elif isinstance(stablecoins, dict):
        return list(stablecoins.values())[:limit]
    return stablecoins


def get_dex_overview(limit: Optional[int] = None) -> List[Dict]:
    """Get DEX overview"""
    return defillama_api.get_dex_overview(limit)


def get_options_overview(limit: Optional[int] = None) -> List[Dict]:
    """Get options overview"""
    return defillama_api.get_options_overview(limit)


def get_fees_overview(limit: Optional[int] = None) -> List[Dict]:
    """Get fees overview"""
    if limit is None:
        limit = config.get("display.max_fees")
    fees = defillama_api.get_fees_overview()
    if isinstance(fees, list):
        return fees[:limit]
    elif isinstance(fees, dict):
        return list(fees.values())[:limit]
    return fees


def get_current_prices(coins: List[str], limit: Optional[int] = None) -> Dict:
    """Get current prices"""
    if limit is None:
        limit = config.get("display.max_prices")
    result = defillama_api.get_current_prices(coins)
    if limit and isinstance(result, dict):
        return dict(list(result.items())[:limit])
    return result


def get_historical_prices(
    coins: List[str], timestamp: int, limit: Optional[int] = None
) -> Dict:
    """Get historical prices"""
    if limit is None:
        limit = config.get("display.max_price_history")
    result = defillama_api.get_historical_prices(coins, timestamp)
    if limit and isinstance(result, dict):
        return dict(list(result.items())[:limit])
    return result


def get_price_chart(coins: List[str], period: str, limit: Optional[int] = None) -> Dict:
    """Get price chart"""
    if limit is None:
        limit = config.get("display.max_price_history")
    result = defillama_api.get_price_chart(coins, period)
    if limit and isinstance(result, dict):
        return {k: v[:limit] if isinstance(v, list) else v for k, v in result.items()}
    return result


def get_volume_history(protocol: str, limit: Optional[int] = None) -> Dict:
    """Get volume history"""
    if limit is None:
        limit = config.get("display.max_volume_history")
    result = defillama_api.get_volume_history(protocol)
    if limit and isinstance(result, dict):
        return {k: v[:limit] if isinstance(v, list) else v for k, v in result.items()}
    return result


def get_fee_history(protocol: str, limit: Optional[int] = None) -> Dict:
    """Get fee history"""
    if limit is None:
        limit = config.get("display.max_fee_history")
    result = defillama_api.get_fee_history(protocol)
    if limit and isinstance(result, dict):
        return {k: v[:limit] if isinstance(v, list) else v for k, v in result.items()}
    return result


def format_chain_data(
    data, output_format="text", oracle_filter=None, show_chains=False, limit=None
):
    """Format protocol data for display.

    Args:
        data: List of protocol data from DefiLlama
        output_format: Output format ('text' or 'json')
        oracle_filter: Filter protocols by oracle (e.g., 'chainlink')
        show_chains: Whether to display supported chains
        limit: Maximum number of protocols to display
    """
    if output_format == "json":
        return json.dumps(data, indent=2)

    # Filter by oracle if specified
    if oracle_filter:
        data = [
            p
            for p in data
            if oracle_filter.lower() in [o.lower() for o in p.get("oracles", [])]
        ]

    # Sort by TVL
    data.sort(key=lambda x: float(x.get("tvl", 0)), reverse=True)

    # Apply limit if specified
    if limit is not None:
        data = data[:limit]

    # Format header
    header = f"{'Name':<30} {'TVL':>15} {'1h Change':>12} {'24h Change':>12} {'7d Change':>12}"
    if show_chains:
        header += " Chains"

    lines = [header, "-" * len(header)]

    # Format each protocol
    for protocol in data:
        name = protocol.get("name", "Unknown")[:30]
        tvl = format_number(float(protocol.get("tvl", 0)))
        change_1h = format_percentage(protocol.get("change_1h", 0))
        change_1d = format_percentage(protocol.get("change_1d", 0))
        change_7d = format_percentage(protocol.get("change_7d", 0))

        line = f"{name:<30} {tvl:>15} {change_1h:>12} {change_1d:>12} {change_7d:>12}"

        if show_chains:
            chains = protocol.get("chains", [])
            if chains:
                line += f" {', '.join(chains)}"

        lines.append(line)

    return "\n".join(lines)


def format_number(value):
    """Format large numbers with K/M/B suffixes."""
    if value >= 1_000_000_000:
        return f"${value/1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"${value/1_000_000:.2f}M"
    elif value >= 1_000:
        return f"${value/1_000:.2f}K"
    else:
        return f"${value:.2f}"


def format_percentage(value):
    """Format percentage with color based on value."""
    if not value:
        return "0.00%"

    value = float(value)
    if value > 0:
        return f"\033[32m+{value:.2f}%\033[0m"  # Green for positive
    elif value < 0:
        return f"\033[31m{value:.2f}%\033[0m"  # Red for negative
    return "0.00%"


def format_price_data(
    price_data: Union[Dict[str, float], List[Dict[str, Any]]], format: str = "table"
) -> str:
    """Format price data for display"""
    if format == "json":
        return json.dumps(price_data, indent=2)

    result = []
    result.append(f"\n{Fore.CYAN}Current Prices:{Style.RESET_ALL}")
    result.append(f"{Fore.CYAN}{'Token':<15} {'Price (USD)':<20}{Style.RESET_ALL}")
    result.append("-" * 35)

    def clean_token_name(token: str) -> str:
        """Clean token name for display by removing prefix and formatting"""
        if ":" in token:
            prefix, name = token.split(":", 1)
            if prefix == "coingecko":
                # Capitalize first letter of each word, replace hyphens with spaces
                return name.replace("-", " ").title()
            return f"{prefix}:{name}"  # Keep original format for non-coingecko tokens
        return token.title()

    if isinstance(price_data, dict):
        # Handle nested structure from DefiLlama API
        for coin, data in price_data.items():
            # The API returns data in the format: {"coins": {"LINK": {"price": 123.45, ...}}}
            if coin == "coins" and isinstance(data, dict):
                for token, token_data in data.items():
                    if isinstance(token_data, dict):
                        price = token_data.get("price", 0)
                        display_name = clean_token_name(token)
                        result.append(
                            f"{Fore.WHITE}{display_name:<15}{Style.RESET_ALL} ${price:,.4f}"
                        )
            # Direct price data format
            elif isinstance(data, dict) and "price" in data:
                price = data["price"]
                display_name = clean_token_name(coin)
                result.append(
                    f"{Fore.WHITE}{display_name:<15}{Style.RESET_ALL} ${price:,.4f}"
                )
            elif isinstance(data, (int, float)):
                display_name = clean_token_name(coin)
                result.append(
                    f"{Fore.WHITE}{display_name:<15}{Style.RESET_ALL} ${float(data):,.4f}"
                )
    else:
        # Historical or chart data
        for entry in price_data:
            timestamp = datetime.fromtimestamp(entry["timestamp"]).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            price = entry.get("price", 0)
            result.append(f"{timestamp}: ${price:,.4f}")

    return "\n".join(result)


def format_chart_data(chart_data: List[Dict[str, Any]], format: str = "table") -> str:
    """Format historical chart data for display"""
    if format == "json":
        return json.dumps(chart_data, indent=2)

    result = []
    result.append("\nHistorical Data:")
    for entry in chart_data:
        timestamp = datetime.fromtimestamp(entry["timestamp"]).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        values = []
        for key, value in entry.items():
            if key != "timestamp":
                if isinstance(value, float):
                    values.append(f"{key}: ${value:,.2f}")
                else:
                    values.append(f"{key}: {value}")
        result.append(f"{timestamp}: {', '.join(values)}")

    return "\n".join(result)


def format_pool_data(pool_data: List[Dict[str, Any]], format: str = "table") -> str:
    """Format pool data for display"""
    if format == "json":
        return json.dumps(pool_data, indent=2)

    result = []
    result.append("\nYield Pools Information:")
    result.append(
        f"{Fore.CYAN}Project              Chain           Symbol      APY          TVL (USD){Style.RESET_ALL}"
    )
    result.append(f"{Fore.BLUE}{'-' * 75}{Style.RESET_ALL}")

    for pool in pool_data:
        # Format APY with color based on value
        apy = pool.get("apy", 0)
        apy_color = Fore.GREEN if apy >= 10 else Fore.YELLOW if apy >= 5 else Fore.RED
        apy_str = f"{apy_color}{apy:.2f}%{Style.RESET_ALL}"

        # Format TVL with thousands separator and color
        tvl = pool.get("tvlUsd", 0)
        tvl_str = f"${tvl:,.2f}"

        # Format each column with proper spacing
        project = pool.get("project", "N/A")[:18]
        chain = pool.get("chain", "N/A")[:12]
        symbol = pool.get("symbol", "N/A")[:10]

        # Build the row with proper spacing and alignment
        row = (
            f"{Fore.WHITE}{project:<18}{Style.RESET_ALL} | "
            f"{Fore.WHITE}{chain:<12}{Style.RESET_ALL} | "
            f"{Fore.CYAN}{symbol:<10}{Style.RESET_ALL} | "
            f"{apy_str:<12} | "
            f"{Fore.CYAN}{tvl_str}{Style.RESET_ALL}"
        )

        result.append(row)

    return "\n".join(result)


def format_dex_data(
    dex_data: Union[Dict[str, Any], List[Dict[str, Any]]],
    format: str = "table",
    limit: int = 20,
    min_volume: Optional[float] = None,
) -> str:
    """Format DEX data for display"""
    if format == "json":
        return json.dumps(dex_data, indent=2)

    result = []

    # Extract and sort DEX data
    dexes = []
    total_volume_24h = 0
    total_volume_7d = 0
    total_volume_30d = 0

    # Process DEX data - handle both list and dict responses
    if isinstance(dex_data, list):
        dex_list = dex_data
    else:
        dex_list = dex_data.get("protocols", [])

    # Process each DEX
    for dex in dex_list:
        if isinstance(dex, dict):
            # Get volume data from the correct fields
            volume_24h = float(dex.get("total24h", 0))
            volume_7d = float(dex.get("total7d", 0))
            volume_30d = float(dex.get("total30d", 0))
            total_volume_24h += volume_24h
            total_volume_7d += volume_7d
            total_volume_30d += volume_30d

            if min_volume is None or volume_24h >= min_volume:
                dexes.append(
                    {
                        "name": dex.get("name", "Unknown"),
                        "volume_24h": volume_24h,
                        "change_24h": dex.get("change_1d", 0),
                        "volume_7d": volume_7d,
                        "change_7d": dex.get("change_7d", 0),
                        "volume_30d": volume_30d,
                        "change_30d": dex.get("change_1m", 0),
                    }
                )

    # Sort by 24h volume
    dexes.sort(key=lambda x: x["volume_24h"], reverse=True)

    # Take top N results
    dexes = dexes[:limit]

    # Format the output
    result.append(f"\n{Fore.CYAN}DEX Volume Overview:{Style.RESET_ALL}")
    result.append(f"Total 24h Volume: ${total_volume_24h:,.2f}")
    result.append(f"Total 7d Volume: ${total_volume_7d:,.2f}")
    result.append(f"Total 30d Volume: ${total_volume_30d:,.2f}")
    result.append("")

    # Header with exact spacing from screenshot
    result.append(
        f"{Fore.CYAN}{'DEX':<20} {'24h Volume':>20} {'24h Change':>11}   {'7d Volume':>20} {'7d Change':>11}   {'30d Volume':>20} {'30d Change':>11}{Style.RESET_ALL}"
    )
    result.append("-" * 120)

    def format_volume(value: float) -> str:
        """Format volume to fit in 20 chars by using K/M/B for large numbers"""
        if value >= 1_000_000_000:  # Billions
            return f"${value/1_000_000_000:.2f}B"
        elif value >= 1_000_000:  # Millions
            return f"${value/1_000_000:.2f}M"
        elif value >= 1_000:  # Thousands
            return f"${value/1_000:.2f}K"
        else:
            return f"${value:.2f}"

    # Data rows
    for dex in dexes:
        name = dex["name"][:19]  # Truncate long names

        # Format volumes with exact spacing
        volume_24h = format_volume(dex["volume_24h"]).rjust(20)
        volume_7d = format_volume(dex["volume_7d"]).rjust(20)
        volume_30d = format_volume(dex["volume_30d"]).rjust(20)

        # Color code the change percentages
        def format_change(change):
            if isinstance(change, (int, float)):
                color = Fore.GREEN if change >= 0 else Fore.RED
                return f"{color}{change:+.2f}%{Style.RESET_ALL}"
            return "N/A"

        change_24h_str = format_change(dex["change_24h"])
        change_7d_str = format_change(dex["change_7d"])
        change_30d_str = format_change(dex["change_30d"])

        # Build the row with exact spacing from screenshot
        row = (
            f"{Fore.WHITE}{name:<20}{Style.RESET_ALL} "  # DEX name (left-aligned, 20 chars)
            f"{volume_24h} "  # 24h volume (right-aligned, 20 chars)
            f"{change_24h_str:>11}   "  # 24h change (right-aligned, 11 chars + 3 spaces)
            f"{volume_7d} "  # 7d volume (right-aligned, 20 chars)
            f"{change_7d_str:>11}   "  # 7d change (right-aligned, 11 chars + 3 spaces)
            f"{volume_30d} "  # 30d volume (right-aligned, 20 chars)
            f"{change_30d_str:>11}"  # 30d change (right-aligned, 11 chars)
        )

        result.append(row)

    return "\n".join(result)


def format_options_data(
    options_data: Union[Dict[str, Any], List[Dict[str, Any]]], format: str = "table"
) -> str:
    """Format options data for display"""
    if format == "json":
        return json.dumps(options_data, indent=2)

    result = []

    # Extract total volumes
    total_24h = float(options_data.get("total24h", 0))
    total_7d = float(options_data.get("total7d", 0))
    total_30d = float(options_data.get("total30d", 0))

    # Format the output header
    result.append(f"\n{Fore.CYAN}Options Volume Overview:{Style.RESET_ALL}")
    result.append(f"Total 24h Volume: ${total_24h:,.2f}")
    result.append(f"Total 7d Volume: ${total_7d:,.2f}")
    result.append(f"Total 30d Volume: ${total_30d:,.2f}")
    result.append("")

    # Header with exact spacing (matching DEX format)
    result.append(
        f"{Fore.CYAN}{'Protocol':<20} {'24h Volume':>20} {'24h Change':>11}   {'7d Volume':>20} {'7d Change':>11}   {'30d Volume':>20} {'30d Change':>11}{Style.RESET_ALL}"
    )
    result.append("-" * 120)

    def format_volume(value: float) -> str:
        """Format volume to fit in 20 chars by using K/M/B for large numbers"""
        if value >= 1_000_000_000:  # Billions
            return f"${value/1_000_000_000:.2f}B"
        elif value >= 1_000_000:  # Millions
            return f"${value/1_000_000:.2f}M"
        elif value >= 1_000:  # Thousands
            return f"${value/1_000:.2f}K"
        else:
            return f"${value:.2f}"

    # Process protocols and sort by 24h volume
    protocols = options_data.get("protocols", [])
    protocols.sort(key=lambda x: float(x.get("total24h", 0)), reverse=True)

    for protocol in protocols:
        name = protocol.get("name", "Unknown")[:19]  # Truncate long names

        # Get volume data
        volume_24h = float(protocol.get("total24h", 0))
        volume_7d = float(protocol.get("total7d", 0))
        volume_30d = float(protocol.get("total30d", 0))

        # Format volumes with exact spacing
        volume_24h_str = format_volume(volume_24h).rjust(20)
        volume_7d_str = format_volume(volume_7d).rjust(20)
        volume_30d_str = format_volume(volume_30d).rjust(20)

        # Format changes
        def format_change(change):
            if isinstance(change, (int, float)):
                color = Fore.GREEN if change >= 0 else Fore.RED
                return f"{color}{change:+.2f}%{Style.RESET_ALL}"
            return "N/A"

        change_24h = format_change(protocol.get("change_1d", 0))
        change_7d = format_change(protocol.get("change_7d", 0))
        change_30d = format_change(protocol.get("change_1m", 0))

        # Build the row with exact spacing
        row = (
            f"{Fore.WHITE}{name:<20}{Style.RESET_ALL} "  # Protocol name (left-aligned, 20 chars)
            f"{volume_24h_str} "  # 24h volume (right-aligned, 20 chars)
            f"{change_24h:>11}   "  # 24h change (right-aligned, 11 chars + 3 spaces)
            f"{volume_7d_str} "  # 7d volume (right-aligned, 20 chars)
            f"{change_7d:>11}   "  # 7d change (right-aligned, 11 chars + 3 spaces)
            f"{volume_30d_str} "  # 30d volume (right-aligned, 20 chars)
            f"{change_30d:>11}"  # 30d change (right-aligned, 11 chars)
        )

        result.append(row)

    return "\n".join(result)


def get_token_identifier(token: str) -> str:
    """Convert token symbol or identifier to DefiLlama format"""
    # If it's already in chain:address format, return as is
    if ":" in token:
        return token

    # Common token mappings for better UX
    token_mappings = {
        "BTC": "coingecko:bitcoin",
        "ETH": "coingecko:ethereum",
        "LINK": "coingecko:chainlink",
        "USDT": "coingecko:tether",
        "USDC": "coingecko:usd-coin",
        "BNB": "coingecko:binancecoin",
        "SOL": "coingecko:solana",
        "ADA": "coingecko:cardano",
        "DOT": "coingecko:polkadot",
        "MATIC": "coingecko:matic-network",
        "AVAX": "coingecko:avalanche-2",
        "UNI": "coingecko:uniswap",
        "AAVE": "coingecko:aave",
        "DAI": "coingecko:dai",
    }

    # Convert to uppercase for matching
    token_upper = token.upper()

    # If we have a direct mapping, use it
    if token_upper in token_mappings:
        return token_mappings[token_upper]

    # Otherwise, try to make a reasonable coingecko ID
    # Convert token to lowercase as most coingecko IDs are lowercase
    return f"coingecko:{token.lower()}"


def format_transaction_data(transactions: List[Transaction], format: str = "table") -> str:
    """Format transaction data for display."""
    if format == "table":
        print(f"\n{Fore.CYAN}Transactions:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'Hash':<66} {'From':<42} {'To':<42} {'Value (ETH)':<15} {'Time':<20}{Style.RESET_ALL}")
        print("-" * 185)
        for tx in transactions:
            value_eth = float(tx.value) / 1e18
            time_str = datetime.fromtimestamp(int(tx.timeStamp)).strftime(config.get("display.date_format"))
            print(f"{tx.hash:<66} {tx.from_address:<42} {tx.to_address:<42} {value_eth:,.6f} {time_str:<20}")
        return ""
    elif format == "json":
        return json.dumps([tx.dict() for tx in transactions], indent=2)


def format_token_transfer_data(transfers: List[TokenTransfer], format: str = "table") -> str:
    """Format token transfer data for display."""
    if format == "table":
        print(f"\n{Fore.CYAN}Token Transfers:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'Hash':<66} {'Token':<20} {'From':<42} {'To':<42} {'Value':<20} {'Time':<20}{Style.RESET_ALL}")
        print("-" * 210)
        for transfer in transfers:
            value = float(transfer.value) / (10 ** int(transfer.tokenDecimal))
            time_str = datetime.fromtimestamp(int(transfer.timeStamp)).strftime(config.get("display.date_format"))
            print(f"{transfer.hash:<66} {transfer.tokenSymbol:<20} {transfer.from_address:<42} {transfer.to_address:<42} {value:,.6f} {time_str:<20}")
        return ""
    elif format == "json":
        return json.dumps([transfer.dict() for transfer in transfers], indent=2)


def format_contract_source(contract: ContractSource, format: str = "table") -> str:
    """Format contract source code for display."""
    if format == "table":
        print(f"\n{Fore.CYAN}Contract Information:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'Name':<20} {'Compiler':<20} {'Optimization':<15} {'License':<15}{Style.RESET_ALL}")
        print("-" * 70)
        print(f"{contract.ContractName:<20} {contract.CompilerVersion:<20} {contract.OptimizationUsed:<15} {contract.LicenseType:<15}")
        print(f"\n{Fore.CYAN}Source Code:{Style.RESET_ALL}")
        print(contract.SourceCode)
        return ""
    elif format == "json":
        return json.dumps(contract.dict(), indent=2)


def setup_parser():
    """Set up the argument parser."""
    parser = argparse.ArgumentParser(description="ChainData - Blockchain Data Aggregator")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Chainlist commands
    chainlist_parser = subparsers.add_parser(
        "chainlist", help="Interact with Chainlist API"
    )
    chainlist_subparsers = chainlist_parser.add_subparsers(
        dest="subcommand", help="Chainlist subcommand"
    )

    # Chainlist search command
    search_parser = chainlist_subparsers.add_parser("search", help="Search for chains")
    search_parser.add_argument("query", help="Search query (chain name or ID)")
    search_parser.add_argument(
        "--format", choices=["table", "json"], default="table", help="Output format"
    )

    # Chainlist list command
    list_parser = chainlist_subparsers.add_parser("list", help="List all chains")
    list_parser.add_argument(
        "--format", choices=["table", "json"], default="table", help="Output format"
    )

    # Chainlist info command
    info_parser = chainlist_subparsers.add_parser("info", help="Get chain information")
    info_parser.add_argument("chain", help="Chain name or ID")
    info_parser.add_argument(
        "--format", choices=["table", "json"], default="table", help="Output format"
    )

    # Chainlist rpcs command
    rpcs_parser = chainlist_subparsers.add_parser("rpcs", help="Get RPC endpoints")
    rpcs_parser.add_argument("chain", help="Chain name or ID")
    rpcs_parser.add_argument(
        "--type", choices=["http", "wss"], default="http", help="RPC type"
    )
    rpcs_parser.add_argument(
        "--no-tracking", action="store_true", help="Exclude tracking RPCs"
    )
    rpcs_parser.add_argument(
        "--format", choices=["table", "json"], default="table", help="Output format"
    )

    # DefiLlama commands
    defillama_parser = subparsers.add_parser(
        "defillama", help="Interact with DefiLlama API"
    )
    defillama_subparsers = defillama_parser.add_subparsers(
        dest="subcommand", help="DefiLlama subcommand"
    )

    # DefiLlama prices command
    prices_parser = defillama_subparsers.add_parser("prices", help="Get coin prices")
    prices_parser.add_argument("coins", nargs="+", help="List of coin symbols")
    prices_parser.add_argument(
        "--historical", action="store_true", help="Get historical prices"
    )
    prices_parser.add_argument(
        "--timestamp", type=int, help="Timestamp for historical prices"
    )
    prices_parser.add_argument(
        "--format", choices=["table", "json"], default="table", help="Output format"
    )

    # DefiLlama pools command
    pools_parser = defillama_subparsers.add_parser("pools", help="Get yield pools")
    pools_parser.add_argument("--min-tvl", type=float, help="Minimum TVL in USD")
    pools_parser.add_argument("--min-apy", type=float, help="Minimum APY percentage")
    pools_parser.add_argument("--limit", type=int, help="Limit number of results")
    pools_parser.add_argument(
        "--format", choices=["table", "json"], default="table", help="Output format"
    )

    # DefiLlama dex command
    dex_parser = defillama_subparsers.add_parser(
        "dex", help="Get DEX volume information"
    )
    dex_parser.add_argument(
        "--chain",
        help="Filter by chain name (e.g., ethereum, bsc, arbitrum). Shows all chains if not specified.",
    )
    dex_parser.add_argument(
        "--limit", type=int, default=20, help="Limit number of results (default: 20)"
    )
    dex_parser.add_argument(
        "--min-volume", type=float, help="Minimum 24h volume in USD"
    )
    dex_parser.add_argument(
        "--format", choices=["table", "json"], default="table", help="Output format"
    )

    # DefiLlama options command
    options_parser = defillama_subparsers.add_parser(
        "options", help="Get options information"
    )
    options_parser.add_argument("--chain", help="Filter by chain")
    options_parser.add_argument(
        "--format", choices=["table", "json"], default="table", help="Output format"
    )

    # DefiLlama protocols command
    protocols_parser = defillama_subparsers.add_parser(
        "protocols", help="Get protocol information"
    )
    protocols_parser.add_argument("--chain", help="Filter by chain")
    protocols_parser.add_argument("--search", help="Search query")
    protocols_parser.add_argument("--limit", type=int, help="Limit number of results")
    protocols_parser.add_argument(
        "--format", choices=["table", "json"], default="table", help="Output format"
    )
    protocols_parser.add_argument("--oracle", help="Filter by oracle (e.g., chainlink)")
    protocols_parser.add_argument(
        "--show-chains",
        action="store_true",
        help="Show supported chains for each protocol",
    )

    # Etherscan commands
    etherscan_parser = subparsers.add_parser("etherscan", help="Etherscan-related commands")
    etherscan_subparsers = etherscan_parser.add_subparsers(dest="subcommand", help="Etherscan subcommands")

    # Transactions command
    transactions_parser = etherscan_subparsers.add_parser("transactions", help="Get transactions for an address")
    transactions_parser.add_argument("address", help="Ethereum address")
    transactions_parser.add_argument("--start-block", type=int, help="Start block number")
    transactions_parser.add_argument("--end-block", type=int, help="End block number")
    transactions_parser.add_argument("--page", type=int, default=1, help="Page number")
    transactions_parser.add_argument("--offset", type=int, default=10, help="Number of results per page")
    transactions_parser.add_argument("--format", choices=["table", "json"], default="table", help="Output format")

    # Token transfers command
    transfers_parser = etherscan_subparsers.add_parser("transfers", help="Get token transfers for an address")
    transfers_parser.add_argument("address", help="Ethereum address")
    transfers_parser.add_argument("--contract", help="Token contract address")
    transfers_parser.add_argument("--page", type=int, default=1, help="Page number")
    transfers_parser.add_argument("--offset", type=int, default=10, help="Number of results per page")
    transfers_parser.add_argument("--format", choices=["table", "json"], default="table", help="Output format")

    # Contract source command
    contract_parser = etherscan_subparsers.add_parser("contract", help="Get contract source code")
    contract_parser.add_argument("address", help="Contract address")
    contract_parser.add_argument("--format", choices=["table", "json"], default="table", help="Output format")

    return parser


def main():
    """Main entry point."""
    parser = setup_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Get the etherscan subparser for help display
    etherscan_parser = parser._subparsers._group_actions[0].choices.get('etherscan')

    try:
        if args.command == "chainlist":
            # Initialize chainlist data if not already done
            if not chainlist_api.blockchain_data:
                chainlist_api.get_all_blockchain_data()

            if not args.subcommand:
                parser.parse_args(["chainlist", "--help"])
                return 1

            if args.subcommand == "search":
                results = chainlist_api.search_chains(args.query)
                print(format_chain_info(results, args.format))

            elif args.subcommand == "list":
                results = chainlist_api.get_all_blockchain_data()
                print(format_chain_info(results, args.format))

            elif args.subcommand == "info":
                # Try to convert to int if possible
                try:
                    chain_id = int(args.chain)
                    info = chainlist_api.get_chain_data_by_id(chain_id)
                except ValueError:
                    info = chainlist_api.get_chain_data_by_name(args.chain)

                if not info:
                    print_error(f"Chain not found: {args.chain}")
                    return 1
                print(format_chain_info(info, args.format))

            elif args.subcommand == "rpcs":
                # Try to convert to int if possible
                try:
                    chain_id = int(args.chain)
                    chain_data = chainlist_api.get_chain_data_by_id(chain_id)
                except ValueError:
                    chain_data = chainlist_api.get_chain_data_by_name(args.chain)

                if not chain_data:
                    print_error(f"Chain not found: {args.chain}")
                    return 1

                rpc_type = "https" if args.type == "http" else "wss"
                rpcs = chainlist_api.get_rpcs(chain_data, rpc_type, args.no_tracking)

                # Format the RPCs for display
                if args.format == "json":
                    print(json.dumps({"rpc": rpcs}, indent=2))
                else:
                    print("\nRPC Endpoints:")
                    for rpc in rpcs:
                        print(f"- {rpc}")

        elif args.command == "defillama":
            if not args.subcommand:
                parser.parse_args(["defillama", "--help"])
                return 1

            if args.subcommand == "prices":
                if args.historical:
                    if not args.timestamp:
                        print_error("Timestamp required for historical prices")
                        return 1
                    token_ids = [get_token_identifier(token) for token in args.coins]
                    prices = defillama_api.get_historical_prices(
                        token_ids, args.timestamp
                    )
                else:
                    # Convert tokens to DefiLlama format
                    token_ids = [get_token_identifier(token) for token in args.coins]
                    print_info(f"Fetching prices for: {', '.join(token_ids)}")
                    prices = defillama_api.get_current_prices(token_ids)
                print(format_price_data(prices, args.format))

            elif args.subcommand == "pools":
                pools = get_pools(args.limit, args.min_tvl, args.min_apy)
                print(format_pool_data(pools, args.format))

            elif args.subcommand == "dex":
                if args.chain:
                    dex_data = defillama_api.get_chain_dex_overview(args.chain)
                else:
                    dex_data = defillama_api.get_dex_overview()
                print(
                    format_dex_data(dex_data, args.format, args.limit, args.min_volume)
                )

            elif args.subcommand == "options":
                if args.chain:
                    options_data = defillama_api.get_chain_options_overview(args.chain)
                else:
                    options_data = defillama_api.get_options_overview()
                print(format_options_data(options_data, args.format))

            elif args.subcommand == "protocols":
                if args.search:
                    results = defillama_api.search_protocols(args.search)
                elif args.chain:
                    results = defillama_api.get_chain_protocols(args.chain)
                else:
                    results = defillama_api.get_top_protocols(args.limit)

                # Apply oracle filtering and chain display options
                print(
                    format_chain_data(
                        results, args.format, args.oracle, args.show_chains, args.limit
                    )
                )

        elif args.command == "etherscan":
            if args.subcommand == "transactions":
                transactions = etherscan_api.get_transactions(
                    args.address,
                    args.start_block,
                    args.end_block,
                    args.page,
                    args.offset
                )
                print(format_transaction_data(transactions, args.format))
            elif args.subcommand == "transfers":
                transfers = etherscan_api.get_token_transfers(
                    args.address,
                    args.contract,
                    args.page,
                    args.offset
                )
                print(format_token_transfer_data(transfers, args.format))
            elif args.subcommand == "contract":
                contract = etherscan_api.get_contract_source(args.address)
                if contract:
                    print(format_contract_source(contract, args.format))
                else:
                    print_error("Contract not found")
            else:
                etherscan_parser.print_help()

        return 0

    except Exception as e:
        print_error(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
