"""Display formatters for ChainData."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from tabulate import tabulate
from colorama import Fore, Style

from ..core.config import config
from ..core.logger import logger
from ..models.chain import Chain, ChainSearchResult
from ..models.defi import Protocol, Pool, PriceData, TVLData

def format_date(date: datetime) -> str:
    """Format date according to config."""
    return date.strftime(config.display.date_format)

def format_number(value: Union[int, float]) -> str:
    """Format number according to config."""
    if isinstance(value, int):
        return f"{value:,}"
    return f"{value:{config.display.number_format}}"

def format_percentage(value: float) -> str:
    """Format percentage according to config."""
    return f"{value:{config.display.percentage_format}}"

def format_chain_data(chain: Chain, format: str = "table") -> str:
    """Format chain data for display."""
    if format == "json":
        return chain.json(indent=2)

    data = [
        ["ID", chain.chainId],
        ["Name", chain.name],
        ["Short Name", chain.shortName or "N/A"],
        ["Network", chain.network],
        ["Native Currency", f"{chain.nativeCurrency.name} ({chain.nativeCurrency.symbol})"],
        ["Decimals", chain.nativeCurrency.decimals],
        ["Testnet", "Yes" if chain.testnet else "No"],
    ]

    if chain.tvl is not None:
        data.append(["TVL", f"${format_number(chain.tvl)}"])

    return tabulate(data, tablefmt="grid")

def format_chain_list(chains: List[Chain], format: str = "table") -> str:
    """Format list of chains for display."""
    if format == "json":
        return ChainListResponse(
            data=chains,
            last_updated=datetime.now(),
            version=__version__
        ).json(indent=2)

    headers = ["ID", "Name", "Short Name", "Network", "TVL"]
    rows = []
    for chain in sorted(chains, key=lambda x: x.chainId):
        row = [
            chain.chainId,
            chain.name,
            chain.shortName or "N/A",
            chain.network,
            f"${format_number(chain.tvl)}" if chain.tvl is not None else "N/A"
        ]
        rows.append(row)

    return tabulate(rows, headers=headers, tablefmt="grid")

def format_protocol_data(protocol: Protocol, format: str = "table") -> str:
    """Format protocol data for display."""
    if format == "json":
        return protocol.json(indent=2)

    data = [
        ["ID", protocol.id],
        ["Name", protocol.name],
        ["Category", protocol.category],
        ["Chain", protocol.chain],
        ["TVL", f"${format_number(protocol.tvl)}" if protocol.tvl else "N/A"],
    ]

    if protocol.change_1d is not None:
        data.append(["24h Change", format_percentage(protocol.change_1d)])

    return tabulate(data, tablefmt="grid")

def format_pool_data(pool: Pool, format: str = "table") -> str:
    """Format pool data for display."""
    if format == "json":
        return pool.json(indent=2)

    data = [
        ["Pool", pool.pool],
        ["Chain", pool.chain],
        ["Project", pool.project],
        ["Symbol", pool.symbol],
        ["TVL", f"${format_number(pool.tvlUsd)}"],
    ]

    if pool.apy is not None:
        data.append(["APY", format_percentage(pool.apy)])

    return tabulate(data, tablefmt="grid")

def format_price_data(price: PriceData, format: str = "table") -> str:
    """Format price data for display."""
    if format == "json":
        return price.json(indent=2)

    data = [
        ["Price", f"${format_number(price.price)}"],
        ["Timestamp", format_date(price.timestamp)],
    ]

    if price.change24h is not None:
        data.append(["24h Change", format_percentage(price.change24h)])

    if price.volume24h is not None:
        data.append(["24h Volume", f"${format_number(price.volume24h)}"])

    return tabulate(data, tablefmt="grid")

def format_tvl_data(tvl: TVLData, format: str = "table") -> str:
    """Format TVL data for display."""
    if format == "json":
        return tvl.json(indent=2)

    data = [
        ["Date", format_date(tvl.date)],
        ["Total TVL", f"${format_number(tvl.totalLiquidityUSD)}"],
    ]

    if tvl.chains:
        data.append(["Chains", len(tvl.chains)])

    if tvl.protocols:
        data.append(["Protocols", len(tvl.protocols)])

    return tabulate(data, tablefmt="grid")

def format_error(message: str) -> str:
    """Format error message."""
    return f"{Fore.RED}Error: {message}{Style.RESET_ALL}"

def format_warning(message: str) -> str:
    """Format warning message."""
    return f"{Fore.YELLOW}Warning: {message}{Style.RESET_ALL}"

def format_success(message: str) -> str:
    """Format success message."""
    return f"{Fore.GREEN}{message}{Style.RESET_ALL}"

def format_info(message: str) -> str:
    """Format info message."""
    return f"{Fore.CYAN}{message}{Style.RESET_ALL}" 