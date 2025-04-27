"""Main CLI entry point for ChainData."""

import argparse
from typing import Optional

from ..core.logger import logger
from ..core.config import config
from .commands import (
    chain_commands,
    defi_commands,
    price_commands,
    pool_commands,
    display_commands,
)

def setup_parser() -> argparse.ArgumentParser:
    """Setup the argument parser."""
    parser = argparse.ArgumentParser(
        description="ChainData - A comprehensive blockchain data aggregator and analysis tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Global arguments
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file",
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        help="Path to cache directory",
    )

    # Create subparsers for different command groups
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Chain commands
    chain_parser = subparsers.add_parser("chain", help="Chain-related commands")
    chain_subparsers = chain_parser.add_subparsers(dest="subcommand")
    chain_commands.setup_chain_parser(chain_subparsers)

    # DeFi commands
    defi_parser = subparsers.add_parser("defi", help="DeFi-related commands")
    defi_subparsers = defi_parser.add_subparsers(dest="subcommand")
    defi_commands.setup_defi_parser(defi_subparsers)

    # Price commands
    price_parser = subparsers.add_parser("price", help="Price-related commands")
    price_subparsers = price_parser.add_subparsers(dest="subcommand")
    price_commands.setup_price_parser(price_subparsers)

    # Pool commands
    pool_parser = subparsers.add_parser("pool", help="Pool-related commands")
    pool_subparsers = pool_parser.add_subparsers(dest="subcommand")
    pool_commands.setup_pool_parser(pool_subparsers)

    # Display commands
    display_parser = subparsers.add_parser("display", help="Display-related commands")
    display_subparsers = display_parser.add_subparsers(dest="subcommand")
    display_commands.setup_display_parser(display_subparsers)

    return parser

def main(args: Optional[argparse.Namespace] = None) -> int:
    """Main entry point for the CLI."""
    parser = setup_parser()
    args = args or parser.parse_args()

    # Update config from command line arguments
    if args.debug:
        config.debug = True
        logger.setLevel("DEBUG")
    if args.config:
        config.load_from_file(args.config)
    if args.cache_dir:
        config.cache.directory = args.cache_dir

    try:
        if not args.command:
            parser.print_help()
            return 0

        # Execute the appropriate command
        if args.command == "chain":
            return chain_commands.execute_chain_command(args)
        elif args.command == "defi":
            return defi_commands.execute_defi_command(args)
        elif args.command == "price":
            return price_commands.execute_price_command(args)
        elif args.command == "pool":
            return pool_commands.execute_pool_command(args)
        elif args.command == "display":
            return display_commands.execute_display_command(args)
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1

    except Exception as e:
        logger.error(f"Error executing command: {e}")
        if config.debug:
            logger.exception("Detailed error traceback:")
        return 1

if __name__ == "__main__":
    exit(main()) 