import sys
from typing import Optional, List, Dict, Any
from ..api.defillama import defillama_api
from ..api.blockchain import blockchain_api
from ..utils.display import (
    print_error, print_success, print_info, print_warning,
    format_protocol_info, format_chain_list, format_protocol_list
)
from ..core.config import config
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from prompt_toolkit.history import FileHistory
import os

class InteractiveMode:
    def __init__(self):
        self.session = PromptSession(
            history=FileHistory(os.path.expanduser('~/.chaindata_history')),
            style=Style.from_dict({
                'prompt': 'cyan bold',
                'completion-menu.completion': 'bg:#008888 #ffffff',
                'completion-menu.completion.current': 'bg:#00aaaa #000000',
            })
        )
        self.commands = {
            'help': self.show_help,
            'exit': self.exit,
            'list': self.list_chains,
            'search': self.search,
            'protocol': self.show_protocol,
            'chain': self.show_chain,
            'tvl': self.show_tvl,
            'prices': self.show_prices,
            'stablecoins': self.show_stablecoins,
            'yields': self.show_yields,
            'dex': self.show_dex,
            'fees': self.show_fees,
        }
        self.completer = WordCompleter(list(self.commands.keys()))

    def show_help(self, args: List[str]) -> None:
        """Show help information"""
        print_info("\nAvailable commands:")
        print_info("  help                 - Show this help message")
        print_info("  exit                 - Exit the program")
        print_info("  list                 - List all available chains")
        print_info("  search <query>       - Search for chains or protocols")
        print_info("  protocol <name>      - Show protocol information")
        print_info("  chain <id/name>      - Show chain information")
        print_info("  tvl <protocol>       - Show TVL for a protocol")
        print_info("  prices <tokens>      - Show token prices")
        print_info("  stablecoins          - Show stablecoin information")
        print_info("  yields               - Show yield information")
        print_info("  dex <chain>          - Show DEX information")
        print_info("  fees <chain>         - Show fee information")

    def exit(self, args: List[str]) -> None:
        """Exit the program"""
        print_info("Goodbye!")
        sys.exit(0)

    def list_chains(self, args: List[str]) -> None:
        """List all available chains"""
        format_chain_list(blockchain_api.get_all_blockchain_data())

    def search(self, args: List[str]) -> None:
        """Search for chains or protocols"""
        if not args:
            print_error("Please provide a search query")
            return
        
        query = ' '.join(args)
        print_info(f"\nSearching for '{query}'...")
        
        # Search chains
        chains = blockchain_api.search_chains(query)
        if chains:
            print_info("\nMatching chains:")
            format_chain_list(chains)
        
        # Search protocols
        protocols = defillama_api.search_protocols(query)
        if protocols:
            print_info("\nMatching protocols:")
            format_protocol_list(protocols)
        
        if not chains and not protocols:
            print_warning(f"No results found for '{query}'")

    def show_protocol(self, args: List[str]) -> None:
        """Show protocol information"""
        if not args:
            print_error("Please provide a protocol name")
            return
        
        protocol = ' '.join(args)
        protocol_data = defillama_api.get_protocol_info(protocol)
        if protocol_data:
            format_protocol_info(protocol_data)
        else:
            print_error(f"Protocol '{protocol}' not found")

    def show_chain(self, args: List[str]) -> None:
        """Show chain information"""
        if not args:
            print_error("Please provide a chain ID or name")
            return
        
        identifier = ' '.join(args)
        try:
            # Try as ID first
            chain_id = int(identifier)
            chain_data = blockchain_api.get_chain_data_by_id(chain_id)
        except ValueError:
            # Try as name
            chain_data = blockchain_api.get_chain_data_by_name(identifier)
        
        if chain_data:
            print_info(f"\nChain Information:")
            print_info(f"ID: {chain_data['chainId']}")
            print_info(f"Name: {chain_data['name']}")
            print_info(f"Short Name: {chain_data.get('shortName', 'N/A')}")
            print_info(f"Native Currency: {chain_data['nativeCurrency']['symbol']}")
            
            # Show RPCs
            print_info("\nRPC Endpoints:")
            for rpc in chain_data['rpc']:
                print_info(f"- {rpc['url']}")
            
            # Show Explorers
            print_info("\nBlock Explorers:")
            for explorer in chain_data['explorers']:
                print_info(f"- {explorer['name']}: {explorer['url']}")
        else:
            print_error(f"Chain '{identifier}' not found")

    def show_tvl(self, args: List[str]) -> None:
        """Show TVL information"""
        if not args:
            print_error("Please provide a protocol name")
            return
        
        protocol = ' '.join(args)
        tvl = defillama_api.get_current_tvl(protocol)
        if tvl is not None:
            print_success(f"Current TVL for {protocol}: ${tvl:,.2f}")
        else:
            print_error(f"Could not fetch TVL for {protocol}")

    def show_prices(self, args: List[str]) -> None:
        """Show token prices"""
        if not args:
            print_error("Please provide token addresses")
            return
        
        tokens = args
        prices = defillama_api.get_current_prices(tokens)
        if prices:
            print_info("\nCurrent Prices:")
            for token, data in prices.items():
                print_info(f"{token}: ${data['price']:,.6f}")
        else:
            print_error("Could not fetch prices")

    def show_stablecoins(self, args: List[str]) -> None:
        """Show stablecoin information"""
        stablecoins = defillama_api.get_stablecoins()
        if stablecoins:
            print_info("\nStablecoins:")
            for stablecoin in stablecoins:
                print_info(f"{stablecoin['name']}: ${stablecoin.get('tvl', 0):,.2f}")
        else:
            print_error("Could not fetch stablecoin data")

    def show_yields(self, args: List[str]) -> None:
        """Show yield information"""
        pools = defillama_api.get_pools()
        if pools:
            print_info("\nTop Pools by APY:")
            for pool in sorted(pools, key=lambda x: x.get('apy', 0), reverse=True)[:10]:
                print_info(f"{pool['name']}: {pool.get('apy', 0):.2f}% APY")
        else:
            print_error("Could not fetch yield data")

    def show_dex(self, args: List[str]) -> None:
        """Show DEX information"""
        chain = args[0] if args else None
        if chain:
            dex_data = defillama_api.get_chain_dex_overview(chain)
        else:
            dex_data = defillama_api.get_dex_overview()
        
        if dex_data:
            print_info("\nDEX Overview:")
            for dex in dex_data.get('protocols', [])[:10]:
                print_info(f"{dex['name']}: ${dex.get('tvl', 0):,.2f} TVL")
        else:
            print_error("Could not fetch DEX data")

    def show_fees(self, args: List[str]) -> None:
        """Show fee information"""
        chain = args[0] if args else None
        if chain:
            fees_data = defillama_api.get_chain_fees_overview(chain)
        else:
            fees_data = defillama_api.get_fees_overview()
        
        if fees_data:
            print_info("\nFees Overview:")
            for protocol in fees_data.get('protocols', [])[:10]:
                print_info(f"{protocol['name']}: ${protocol.get('fees', 0):,.2f} fees")
        else:
            print_error("Could not fetch fee data")

    def run(self) -> None:
        """Run the interactive mode"""
        print_info("\nWelcome to ChainData Interactive Mode!")
        print_info("Type 'help' for available commands or 'exit' to quit")
        
        while True:
            try:
                text = self.session.prompt('chaindata> ', completer=self.completer)
                if not text.strip():
                    continue
                
                parts = text.split()
                command = parts[0].lower()
                args = parts[1:]
                
                if command in self.commands:
                    self.commands[command](args)
                else:
                    print_error(f"Unknown command: {command}")
                    print_info("Type 'help' for available commands")
            
            except KeyboardInterrupt:
                continue
            except EOFError:
                self.exit([])
            except Exception as e:
                print_error(f"Error: {str(e)}")

def main():
    interactive = InteractiveMode()
    interactive.run()

if __name__ == '__main__':
    main() 