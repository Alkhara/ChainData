import json
from datetime import datetime
from typing import Any, Dict, List

from tabulate import tabulate

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
    chains = protocol_data.get("chains", [])
    if chains:
        print_info("\nChains:")
        for chain in chains:
            print(f"  - {chain}")

    # Format TVL history
    tvl_history = protocol_data.get("tvl_history", [])
    if tvl_history:
        print_info("\nRecent TVL History:")
        history = sorted(tvl_history, key=lambda x: x["date"], reverse=True)[:5]
        table = []
        for entry in history:
            date = datetime.fromtimestamp(entry["date"]).strftime("%Y-%m-%d")
            tvl = entry.get("tvl", 0)
            table.append([date, f"${tvl:,.2f}"])
        print(tabulate(table, headers=["Date", "TVL"], tablefmt="grid"))


def format_chain_list(chains: List[str], format_type: str = "table"):
    """Format chain list for display"""
    if format_type == "json":
        print(json.dumps(chains, indent=2))
    else:
        print_info("\nChains:")
        for chain in chains:
            print(f"  - {chain}")


def format_protocol_list(protocols: List[Dict[str, Any]], format_type: str = "table"):
    """Format protocol list for display"""
    if format_type == "json":
        print(json.dumps(protocols, indent=2))
    else:
        table = []
        for protocol in protocols:
            name = protocol.get("name", "N/A")
            tvl = protocol.get("tvl", 0)
            chains = protocol.get("chains", [])
            table.append([name, f"${tvl:,.2f}", len(chains)])

        print(tabulate(table, headers=["Protocol", "TVL", "Chains"], tablefmt="grid"))


def format_chain_data(data: List[Dict[str, Any]], fmt: str = "table") -> None:
    """Format chain data as either JSON or table"""
    if fmt == "json":
        print(json.dumps(data, indent=2))
        return

    headers = ["Chain", "Name", "Chain ID", "Token Symbol"]
    rows = [
        [
            chain["chain"],
            chain["name"],
            chain.get("chainId", "N/A"),
            chain.get("nativeCurrency", {}).get("symbol", "N/A"),
        ]
        for chain in data
    ]

    print(tabulate(rows, headers=headers, tablefmt="grid"))


def format_chain_info(chain_data: Dict[str, Any], fmt: str = "table") -> None:
    """Format chain information for display"""
    if fmt == "json":
        print(json.dumps(chain_data, indent=2))
        return

    # Format as table
    headers = ["Property", "Value"]
    rows = [
        ["Chain", chain_data.get("chain", "N/A")],
        ["Name", chain_data.get("name", "N/A")],
        ["Chain ID", chain_data.get("chainId", "N/A")],
        ["Token Symbol", chain_data.get("nativeCurrency", {}).get("symbol", "N/A")],
        ["Block Explorer", chain_data.get("explorers", [{}])[0].get("url", "N/A")],
        ["RPC Count", len(chain_data.get("rpc", []))],
    ]

    print(tabulate(rows, headers=headers, tablefmt="grid"))


def format_rpc_data(data: Dict[str, Any], fmt: str = "table") -> None:
    """Format RPC endpoint data as either JSON or table"""
    if fmt == "json":
        print(json.dumps(data, indent=2))
        return

    # Extract RPC URLs from the data
    rpcs = data.get("rpc", [])
    if not rpcs:
        print_warning("No RPC endpoints found")
        return

    headers = ["RPC URL", "Tracking"]
    rows = []
    for rpc in rpcs:
        url = rpc.get("url", "N/A")
        tracking = "Yes" if rpc.get("tracking") != "none" else "No"
        rows.append([url, tracking])

    print(tabulate(rows, headers=headers, tablefmt="grid"))


def format_price_data(data: Dict[str, Any], fmt: str = "table") -> None:
    """Format price data as either JSON or table"""
    if fmt == "json":
        print(json.dumps(data, indent=2))
        return

    headers = ["Coin", "Price (USD)", "Timestamp"]
    rows = [
        [coin, f"${price['price']:.4f}", price["timestamp"]]
        for coin, price in data.items()
    ]

    print(tabulate(rows, headers=headers, tablefmt="grid"))


def format_price_history(
    data: Dict[str, List[Dict[str, Any]]], fmt: str = "table"
) -> None:
    """Format price history data as either JSON or table"""
    if fmt == "json":
        print(json.dumps(data, indent=2))
        return

    headers = ["Date", "Price (USD)", "Market Cap", "Volume"]
    rows = [
        [
            entry["date"],
            f"${entry['price']:.4f}",
            f"${entry.get('marketCap', 0):,.0f}",
            f"${entry.get('volume', 0):,.0f}",
        ]
        for entry in data["prices"]
    ]

    print(tabulate(rows, headers=headers, tablefmt="grid"))


def format_price_chart(
    data: Dict[str, List[Dict[str, Any]]], fmt: str = "table"
) -> None:
    """Format price chart data as either JSON or table"""
    if fmt == "json":
        print(json.dumps(data, indent=2))
        return

    # For table format, we'll show a simplified version
    headers = ["Date", "Price (USD)", "% Change"]
    rows = []
    prev_price = None

    for entry in data["prices"]:
        curr_price = entry["price"]
        pct_change = "-"
        if prev_price:
            pct_change = f"{((curr_price - prev_price) / prev_price) * 100:.2f}%"
        rows.append([entry["date"], f"${curr_price:.4f}", pct_change])
        prev_price = curr_price

    print(tabulate(rows, headers=headers, tablefmt="grid"))


def format_pool_data(data: List[Dict[str, Any]], fmt: str = "table") -> None:
    """Format pool data as either JSON or table"""
    if fmt == "json":
        print(json.dumps(data, indent=2))
        return

    headers = ["Project", "Chain", "Symbol", "APY", "TVL (USD)", "Pool ID"]
    rows = [
        [
            pool["project"],
            pool["chain"],
            pool["symbol"],
            f"{pool['apy']:.2f}%",
            f"${pool['tvlUsd']:,.2f}",
            pool["pool"],
        ]
        for pool in data
    ]

    print(tabulate(rows, headers=headers, tablefmt="grid"))


def format_pool_chart(
    data: Dict[str, List[Dict[str, Any]]], fmt: str = "table"
) -> None:
    """Format pool chart data as either JSON or table"""
    if fmt == "json":
        print(json.dumps(data, indent=2))
        return

    headers = ["Date", "TVL (USD)", "APY", "% Change TVL"]
    rows = []
    prev_tvl = None

    for entry in data["data"]:
        curr_tvl = entry["tvl"]
        pct_change = "-"
        if prev_tvl:
            pct_change = f"{((curr_tvl - prev_tvl) / prev_tvl) * 100:.2f}%"
        rows.append(
            [entry["date"], f"${curr_tvl:,.2f}", f"{entry['apy']:.2f}%", pct_change]
        )
        prev_tvl = curr_tvl

    print(tabulate(rows, headers=headers, tablefmt="grid"))


def format_dex_data(data: Dict[str, Any], fmt: str = "table") -> None:
    """Format DEX data as either JSON or table"""
    if fmt == "json":
        print(json.dumps(data, indent=2))
        return

    headers = ["DEX", "Chain", "24h Volume", "7d Volume", "TVL"]
    rows = [
        [
            dex["name"],
            dex.get("chain", "All"),
            f"${dex['volume24h']:,.2f}",
            f"${dex['volume7d']:,.2f}",
            f"${dex['tvl']:,.2f}",
        ]
        for dex in data["dexes"]
    ]

    print(tabulate(rows, headers=headers, tablefmt="grid"))


def format_options_data(data: Dict[str, Any], fmt: str = "table") -> None:
    """Format options data as either JSON or table"""
    if fmt == "json":
        print(json.dumps(data, indent=2))
        return

    headers = ["Protocol", "Chain", "Total Value", "Volume 24h", "Fees 24h"]
    rows = [
        [
            protocol["name"],
            protocol.get("chain", "All"),
            f"${protocol['totalValue']:,.2f}",
            f"${protocol.get('volume24h', 0):,.2f}",
            f"${protocol.get('fees24h', 0):,.2f}",
        ]
        for protocol in data["protocols"]
    ]

    print(tabulate(rows, headers=headers, tablefmt="grid"))


def format_chart_data(
    data: Dict[str, List[Dict[str, Any]]], fmt: str = "table"
) -> None:
    """Format chart data as either JSON or table"""
    if fmt == "json":
        print(json.dumps(data, indent=2))
        return

    headers = ["Date", "Value", "% Change"]
    rows = []
    prev_value = None

    for entry in data["data"]:
        curr_value = entry["value"]
        pct_change = "-"
        if prev_value:
            pct_change = f"{((curr_value - prev_value) / prev_value) * 100:.2f}%"
        rows.append([entry["date"], f"${curr_value:,.2f}", pct_change])
        prev_value = curr_value

    print(tabulate(rows, headers=headers, tablefmt="grid"))
