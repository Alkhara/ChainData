import argparse
from typing import Optional
from ..api.defillama import defillama_api
from ..api.blockchain import blockchain_api
from ..utils.display import (
    print_error, print_success, print_info, print_warning,
    format_protocol_info, format_chain_list, format_protocol_list
)
from ..core.config import config
from .interactive import InteractiveMode

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Chain Data CLI')
    
    # Add interactive mode flag
    parser.add_argument('-i', '--interactive', action='store_true',
                       help='Start in interactive mode')
    
    # Protocol commands
    protocol_group = parser.add_argument_group('Protocol Commands')
    protocol_group.add_argument('--protocol', type=str, help='Protocol name to query')
    protocol_group.add_argument('--function', type=str, choices=['info', 'tvl', 'chains'], 
                              help='Function to execute for the protocol')
    
    # Chain commands
    chain_group = parser.add_argument_group('Chain Commands')
    chain_group.add_argument('--chain', type=str, help='Chain name or ID to query')
    chain_group.add_argument('--limit', type=int, help='Limit number of results')
    chain_group.add_argument('--format', type=str, choices=['table', 'json'], default='table',
                            help='Output format (table or json)')
    
    # Cache commands
    cache_group = parser.add_argument_group('Cache Commands')
    cache_group.add_argument('--refresh', action='store_true', help='Force refresh cache')
    
    return parser.parse_args()

def handle_protocol_command(args):
    """Handle protocol-related commands"""
    if not args.protocol:
        print_error("Protocol name is required")
        return
    
    if args.function == 'info':
        protocol_data = defillama_api.get_protocol_info(args.protocol)
        if protocol_data:
            format_protocol_info(protocol_data)
        else:
            print_error(f"Protocol '{args.protocol}' not found")
    
    elif args.function == 'tvl':
        tvl = defillama_api.get_current_tvl(args.protocol)
        if tvl is not None:
            print_success(f"Current TVL for {args.protocol}: ${tvl:,.2f}")
        else:
            print_error(f"Could not fetch TVL for {args.protocol}")
    
    elif args.function == 'chains':
        chains = defillama_api.get_protocol_chains(args.protocol)
        if chains:
            format_chain_list(chains, args.format)
        else:
            print_error(f"No chains found for {args.protocol}")
    
    else:
        print_error("Function is required for protocol commands")

def handle_chain_command(args):
    """Handle chain-related commands"""
    if not args.chain:
        print_error("Chain name or ID is required")
        return
    
    # Try to get chain data
    chain_data = blockchain_api.get_chain_data(args.chain)
    if not chain_data:
        print_error(f"Chain '{args.chain}' not found")
        return
    
    # Get protocols on this chain
    protocols = defillama_api.get_chain_protocols(chain_data['name'], args.limit)
    if protocols:
        format_protocol_list(protocols, args.format)
    else:
        print_warning(f"No protocols found on {chain_data['name']}")

def main():
    """Main entry point"""
    args = parse_args()
    
    # Start interactive mode if requested
    if args.interactive:
        interactive = InteractiveMode()
        interactive.run()
        return
    
    # Initialize data if needed
    if args.refresh:
        blockchain_api.get_all_blockchain_data(force_refresh=True)
    else:
        blockchain_api.get_all_blockchain_data()
    
    # Handle commands
    if args.protocol:
        handle_protocol_command(args)
    elif args.chain:
        handle_chain_command(args)
    else:
        print_error("No command specified. Use --help for usage information or --interactive for interactive mode.")

if __name__ == '__main__':
    main() 