"""Chain-related commands."""

import argparse
from typing import Any, Dict, List, Optional

from ...core.logger import logger
from ...api.chainlist import chainlist_api
from ...models.chain import Chain, ChainSearchResult

def setup_chain_parser(subparsers: argparse._SubParsersAction) -> None:
    """Setup chain-related command parsers."""
    # List chains
    list_parser = subparsers.add_parser("list", help="List available chains")
    list_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format",
    )
    list_parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Force refresh of chain data",
    )

    # Search chains
    search_parser = subparsers.add_parser("search", help="Search for chains")
    search_parser.add_argument(
        "query",
        type=str,
        help="Search query (chain name, ID, or short name)",
    )
    search_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format",
    )

    # Get chain info
    info_parser = subparsers.add_parser("info", help="Get chain information")
    info_parser.add_argument(
        "identifier",
        type=str,
        help="Chain identifier (name, ID, or short name)",
    )
    info_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format",
    )

    # Get RPCs
    rpc_parser = subparsers.add_parser("rpcs", help="Get chain RPCs")
    rpc_parser.add_argument(
        "identifier",
        type=str,
        help="Chain identifier (name, ID, or short name)",
    )
    rpc_parser.add_argument(
        "--type",
        choices=["http", "wss"],
        default="http",
        help="RPC type",
    )
    rpc_parser.add_argument(
        "--no-tracking",
        action="store_true",
        help="Exclude RPCs with tracking",
    )
    rpc_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format",
    )

def execute_chain_command(args: argparse.Namespace) -> int:
    """Execute chain-related commands."""
    try:
        if args.subcommand == "list":
            return handle_list_command(args)
        elif args.subcommand == "search":
            return handle_search_command(args)
        elif args.subcommand == "info":
            return handle_info_command(args)
        elif args.subcommand == "rpcs":
            return handle_rpcs_command(args)
        else:
            logger.error(f"Unknown chain subcommand: {args.subcommand}")
            return 1
    except Exception as e:
        logger.error(f"Error executing chain command: {e}")
        return 1

def handle_list_command(args: argparse.Namespace) -> int:
    """Handle list chains command."""
    chains = chainlist_api.get_all_blockchain_data(force_refresh=args.force_refresh)
    if args.format == "json":
        print(ChainListResponse(data=chains, last_updated=datetime.now(), version=__version__).json())
    else:
        # Format as table
        print("\nAvailable Chains:")
        print(f"{'ID':<8} {'Name':<30} {'Short Name':<15}")
        print("-" * 55)
        for chain in sorted(chains, key=lambda x: x.chainId):
            print(f"{chain.chainId:<8} {chain.name:<30} {chain.shortName or 'N/A':<15}")
    return 0

def handle_search_command(args: argparse.Namespace) -> int:
    """Handle search chains command."""
    results = chainlist_api.search_chains(args.query)
    if args.format == "json":
        print(ChainSearchResult(chains=results, total=len(results), page=1, page_size=len(results)).json())
    else:
        if not results:
            print("No chains found matching the query.")
            return 0
        print("\nSearch Results:")
        print(f"{'ID':<8} {'Name':<30} {'Short Name':<15}")
        print("-" * 55)
        for chain in results:
            print(f"{chain.chainId:<8} {chain.name:<30} {chain.shortName or 'N/A':<15}")
    return 0

def handle_info_command(args: argparse.Namespace) -> int:
    """Handle get chain info command."""
    chain = chainlist_api.get_chain_data(args.identifier)
    if not chain:
        logger.error(f"Chain not found: {args.identifier}")
        return 1

    if args.format == "json":
        print(chain.json(indent=2))
    else:
        print("\nChain Information:")
        print(f"ID: {chain.chainId}")
        print(f"Name: {chain.name}")
        print(f"Short Name: {chain.shortName}")
        print(f"Network: {chain.network}")
        print(f"Native Currency: {chain.nativeCurrency.name} ({chain.nativeCurrency.symbol})")
        print("\nRPCs:")
        for rpc in chain.rpc:
            print(f"- {rpc.url} (Tracking: {rpc.tracking or 'None'})")
        print("\nExplorers:")
        for explorer in chain.explorers:
            print(f"- {explorer.name}: {explorer.url}")
    return 0

def handle_rpcs_command(args: argparse.Namespace) -> int:
    """Handle get RPCs command."""
    rpcs = chainlist_api.get_rpcs(
        args.identifier,
        rpc_type=args.type,
        no_tracking=args.no_tracking
    )
    if not rpcs:
        logger.error(f"No RPCs found for chain: {args.identifier}")
        return 1

    if args.format == "json":
        print(json.dumps(rpcs, indent=2))
    else:
        print(f"\n{args.type.upper()} RPCs for {args.identifier}:")
        for rpc in rpcs:
            print(f"- {rpc}")
    return 0 