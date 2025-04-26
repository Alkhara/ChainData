from typing import List, Dict, Any
import json
from tabulate import tabulate
from datetime import datetime
from ..core.config import config

def print_error(message: str):
    """Print error message in red"""
    print(f"\033[91mError: {message}\033[0m")

def print_success(message: str):
    """Print success message in green"""
    print(f"\033[92m{message}\033[0m")

def print_info(message: str):
    """Print info message in blue"""
    print(f"\033[94m{message}\033[0m")

def print_warning(message: str):
    """Print warning message in yellow"""
    print(f"\033[93mWarning: {message}\033[0m")

def format_protocol_info(protocol_data: Dict[str, Any]):
    """Format protocol information for display"""
    print_success(f"\nProtocol: {protocol_data['name']}")
    print_info(f"Category: {protocol_data.get('category', 'N/A')}")
    print_info(f"Current TVL: ${protocol_data.get('tvl', 0):,.2f}")
    
    # Format chains
    chains = protocol_data.get('chains', [])
    if chains:
        print_info("\nChains:")
        for chain in chains:
            print(f"  - {chain}")
    
    # Format TVL history
    tvl_history = protocol_data.get('tvl_history', [])
    if tvl_history:
        print_info("\nRecent TVL History:")
        history = sorted(tvl_history, key=lambda x: x['date'], reverse=True)[:5]
        table = []
        for entry in history:
            date = datetime.fromtimestamp(entry['date']).strftime('%Y-%m-%d')
            tvl = entry.get('tvl', 0)
            table.append([date, f"${tvl:,.2f}"])
        print(tabulate(table, headers=['Date', 'TVL'], tablefmt='grid'))

def format_chain_list(chains: List[str], format_type: str = 'table'):
    """Format chain list for display"""
    if format_type == 'json':
        print(json.dumps(chains, indent=2))
    else:
        print_info("\nChains:")
        for chain in chains:
            print(f"  - {chain}")

def format_protocol_list(protocols: List[Dict[str, Any]], format_type: str = 'table'):
    """Format protocol list for display"""
    if format_type == 'json':
        print(json.dumps(protocols, indent=2))
    else:
        table = []
        for protocol in protocols:
            name = protocol.get('name', 'N/A')
            tvl = protocol.get('tvl', 0)
            chains = protocol.get('chains', [])
            table.append([name, f"${tvl:,.2f}", len(chains)])
        
        print(tabulate(table, headers=['Protocol', 'TVL', 'Chains'], tablefmt='grid')) 