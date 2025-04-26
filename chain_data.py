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

# Initialize colorama
init()

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

CACHE_FILE = 'blockchain_data_cache.json'
CACHE_EXPIRY_SECONDS = 3600  # 1 hour

def print_error(message):
    print(f"{Fore.RED}Error: {message}{Style.RESET_ALL}")

def print_success(message):
    print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")

def print_info(message):
    print(f"{Fore.CYAN}{message}{Style.RESET_ALL}")

def print_warning(message):
    print(f"{Fore.YELLOW}Warning: {message}{Style.RESET_ALL}")

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
            if time.time() - last_updated < CACHE_EXPIRY_SECONDS:
                print_success("Using cached data")
                return cache.get('data', [])
        except Exception as e:
            print_error(f"Error reading cache: {e}")
            pass  # If cache is corrupted, fetch fresh
    
    # Fetch fresh data
    print_info("Fetching fresh data...")
    url = "https://chainlist.org/rpcs.json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        print_success(f"Fetched {len(data)} chains from API")
        
        # Save to cache
        with open(CACHE_FILE, 'w') as f:
            json.dump({'last_updated': time.time(), 'data': data}, f)
        return data
    except requests.exceptions.RequestException as e:
        print_error(f"Failed to fetch data: {e}")
        return []

# Initialize blockchain data
blockchain_data = get_all_blockchain_data()

def search_chains(query):
    """Search for chains by name or ID"""
    results = []
    query = query.lower()
    for chain in blockchain_data:
        if (query in chain['name'].lower() or 
            str(chain['chainId']) == query or
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

## Get Specific Blockchain Data

# Get a specific Chain by ID
def get_chain_data_by_id(chain_id):
    for chain in blockchain_data:
        if chain['chainId'] == chain_id:
            return chain
    return None

# Get a specific Chain by Name
def get_chain_data_by_name(chain_name):
    for chain in blockchain_data:
        if chain['name'].lower() == chain_name.lower():
            return chain
    return None 

def get_chain_data(identifier):
    """Get chain data by ID or name"""
    if isinstance(identifier, int):
        return get_chain_data_by_id(identifier)
    return get_chain_data_by_name(identifier)

## Get RPCs for a specific Chain

# Get HTTP RPCs for a specific Chain
def get_http_rpcs(identifier, no_tracking=False):
    """Get HTTP RPCs by ID or name"""
    chain_data = get_chain_data(identifier)
    http_rpcs = []
    if chain_data:
        for rpc in chain_data['rpc']:
            if 'https' in rpc['url']:
                if not no_tracking or (no_tracking and rpc.get('tracking') == 'none'):
                    http_rpcs.append(rpc['url'])
    return http_rpcs

# Get HTTP RPCs for a specific Chain by Name
def get_http_rpcs_by_name(chain_name, no_tracking=False):
    chain_data = get_chain_data_by_name(chain_name)
    http_rpcs = []
    if chain_data:
        for rpc in chain_data['rpc']:
            if 'https' in rpc['url']:
                if not no_tracking or (no_tracking and rpc.get('tracking') == 'none'):
                    http_rpcs.append(rpc['url'])
    return http_rpcs

# Get WSS RPCs for a specific Chain by ID
def get_wss_rpcs(identifier, no_tracking=False):
    """Get WSS RPCs by ID or name"""
    chain_data = get_chain_data(identifier)
    wss_rpcs = []
    if chain_data:
        for rpc in chain_data['rpc']:
            if 'wss' in rpc['url']:
                if not no_tracking or (no_tracking and rpc.get('tracking') == 'none'):
                    wss_rpcs.append(rpc['url'])
    return wss_rpcs 

# Get WSS RPCs for a specific Chain by Name
def get_wss_rpcs_by_name(chain_name, no_tracking=False):
    chain_data = get_chain_data_by_name(chain_name)
    wss_rpcs = []
    if chain_data:
        for rpc in chain_data['rpc']:   
            if 'wss' in rpc['url']:
                if not no_tracking or (no_tracking and rpc.get('tracking') == 'none'):
                    wss_rpcs.append(rpc['url'])
    return wss_rpcs

## Get Explorer for a specific Chain

# Get Explorer for a specific Chain by ID
def get_explorer(identifier, explorer_type=None):
    """Get explorer by ID or name"""
    chain_data = get_chain_data(identifier)
    explorers = []
    if chain_data:
        for explorer in chain_data['explorers']:
            if not explorer_type or explorer['name'] == explorer_type:
                explorers.append(explorer['url'])
    return explorers

# Get Explorer for a specific Chain by Name
def get_explorer_by_name(chain_name, explorer_type=None):
    chain_data = get_chain_data_by_name(chain_name)
    explorers = []
    if chain_data:
        for explorer in chain_data['explorers']:
            if not explorer_type or explorer['name'] == explorer_type:
                explorers.append(explorer['url'])
    return explorers

## Get EIPs for a specific Chain
def get_eips(identifier):
    """Get EIPs by ID or name"""
    chain_data = get_chain_data(identifier)
    eips = []
    if chain_data:
        for eip in chain_data['features']:
            eips.extend(eip.values())
    return eips

## Get EIPs for a specific Chain by Name
def get_eips_by_name(chain_name):
    chain_data = get_chain_data_by_name(chain_name)
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

def get_native_currency_by_name(chain_name):
    chain_data = get_chain_data_by_name(chain_name)
    if chain_data:
        return chain_data['nativeCurrency']
    return None 


def get_tvl(identifier):
    """Get TVL by ID or name"""
    chain_data = get_chain_data(identifier)
    if chain_data:
        return chain_data['tvl']
    return None  

def get_tvl_by_name(chain_name):
    chain_data = get_chain_data_by_name(chain_name)
    if chain_data:
        return chain_data['tvl']
    return None  


## Helper Functions

def list_available_functions():
    functions = {
        'http-rpcs': 'Get HTTP RPC endpoints for a chain',
        'wss-rpcs': 'Get WebSocket RPC endpoints for a chain',
        'explorer': 'Get blockchain explorer URLs',
        'eips': 'Get supported EIPs for a chain',
        'native-currency': 'Get native currency information',
        'tvl': 'Get Total Value Locked information',
        'chain-data': 'Get complete chain data',
        'explorer-link': 'Get explorer link for an address'
    }
    
    print("\nAvailable Functions:")
    print("------------------")
    for func, desc in functions.items():
        print(f"{func:<15} - {desc}")
    print("\nExample Usage:")
    print("python chains.py --chain-id 1 --function http-rpcs")
    print("python chains.py --name 'ethereum mainnet' --function explorer --explorer-type etherscan")
    print("python chains.py --chain-id 1 --function explorer-link --address 0x123...")

def chain_id_to_name(chain_id):
    for chain in blockchain_data:
        if chain['chainId'] == chain_id:
            return chain['name']
    return None

def get_explorer_link(chain_id, address):
    for chain in blockchain_data:
        if chain['chainId'] == chain_id:
            for explorer in chain['explorers']:
                if explorer['name'] == 'etherscan':
                    return explorer['url'] + '/address/' + address
    return None



def main():
    parser = argparse.ArgumentParser(description='ChainData - Get blockchain information')
    
    # Add mutually exclusive group for chain identifier
    identifier_group = parser.add_mutually_exclusive_group(required=False)
    identifier_group.add_argument('-c', '--chain-id', type=int, help='Chain ID')
    identifier_group.add_argument('-n', '--name', type=str, help='Chain name')
    identifier_group.add_argument('-s', '--search', type=str, help='Search for chains')
    identifier_group.add_argument('-l', '--list', action='store_true', help='List all available chains')
    
    # Add function argument
    parser.add_argument('-f', '--function', type=str, required=False, choices=[
        'http-rpcs', 'wss-rpcs', 'explorer', 'eips', 
        'native-currency', 'tvl', 'chain-data', 'explorer-link'
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
        global blockchain_data
        blockchain_data = get_all_blockchain_data(force_refresh=True)
    
    if args.list:
        list_chains(format=args.format)
        return
    
    if args.search:
        results = search_chains(args.search)
        if results:
            print(f"\n{Fore.CYAN}Search Results:{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'ID':<8} {'Name':<30} {'Short Name':<15}{Style.RESET_ALL}")
            print("-" * 55)
            for chain in results:
                print(f"{chain['chainId']:<8} {chain['name']:<30} {chain.get('shortName', 'N/A'):<15}")
        else:
            print_warning(f"No chains found matching '{args.search}'")
        return
    
    if not args.function:
        print_error("Error: --function is required. Use --list-functions to see available options.")
        return
    
    if not (args.chain_id or args.name):
        print_error("Error: Either --chain-id or --name must be provided.")
        return
    
    # Determine identifier
    identifier = args.chain_id if args.chain_id is not None else args.name
    
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
        print_info(f"Network: {chain_id_to_name(identifier)}")
    else:
        print_info(f"Network: {identifier}")

    print_info(f"Function: {args.function}")
    if isinstance(result, (list, dict)):
        print(json.dumps(result, indent=2))
    else:
        print(result)

if __name__ == '__main__':
    main()





























