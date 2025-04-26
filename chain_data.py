import sys
import json
import requests
import os
import time
from datetime import datetime
import argparse

# print a cool welcome message in ascii art saying ChainData
print("""

 ░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░░▒▓█▓▒░▒▓███████▓▒░░▒▓███████▓▒░ ░▒▓██████▓▒░▒▓████████▓▒░▒▓██████▓▒░  
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░      ░▒▓████████▓▒░▒▓████████▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓████████▓▒░ ░▒▓█▓▒░  ░▒▓████████▓▒░ 
░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░ 
 ░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░ 
                                                                                                              
                                                                                                              

""")


CACHE_FILE = 'blockchain_data_cache.json'
CACHE_EXPIRY_SECONDS = 3600  # 1 hour

def get_all_blockchain_data(force_refresh=False):
    # Check if cache exists and is fresh
    if not force_refresh and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                cache = json.load(f)
            last_updated = cache.get('last_updated', 0)
            if last_updated:
                last_updated_str = datetime.fromtimestamp(last_updated).strftime('%Y-%m-%d %H:%M:%S')
                print(f"Data last updated: {last_updated_str}")
            if time.time() - last_updated < CACHE_EXPIRY_SECONDS:
                print("Using cached data")
                return cache.get('data', [])
        except Exception as e:
            print(f"Error reading cache: {e}")
            pass  # If cache is corrupted, fetch fresh
    
    # Fetch fresh data
    print("Fetching fresh data")
    url = "https://chainlist.org/rpcs.json"
    response = requests.get(url)
    data = response.json()
    print(f"Fetched {len(data)} chains from API")
    
    # Save to cache
    with open(CACHE_FILE, 'w') as f:
        json.dump({'last_updated': time.time(), 'data': data}, f)
    return data

# Initialize blockchain data
blockchain_data = get_all_blockchain_data()

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
    identifier_group.add_argument('--chain-id', type=int, help='Chain ID')
    identifier_group.add_argument('--name', type=str, help='Chain name')
    
    # Add function argument
    parser.add_argument('--function', type=str, required=False, choices=[
        'http-rpcs', 'wss-rpcs', 'explorer', 'eips', 
        'native-currency', 'tvl', 'chain-data', 'explorer-link'
    ], help='Function to call')
    
    # Add optional arguments
    parser.add_argument('--no-tracking', action='store_true', help='Only return RPCs with no tracking')
    parser.add_argument('--explorer-type', type=str, help='Specific explorer type to return')
    parser.add_argument('--address', type=str, help='Address to get explorer link for')
    parser.add_argument('--list-functions', action='store_true', help='List all available functions')
    
    args = parser.parse_args()
    
    if args.list_functions:
        list_available_functions()
        return
    
    if not args.function:
        print("Error: --function is required. Use --list-functions to see available options.")
        return
    
    if not (args.chain_id or args.name):
        print("Error: Either --chain-id or --name must be provided.")
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
        print("Network: ", chain_id_to_name(identifier))
    else:
        print("Network: ", identifier)

    print(f"Function: {args.function}")
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()





























