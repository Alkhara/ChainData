"""DeFi models for DeFiLlama API."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Protocol(BaseModel):
    """Protocol model."""

    id: str = Field(..., description="Protocol ID")
    name: str = Field(..., description="Protocol name")
    url: str = Field(..., description="Protocol URL")
    description: str = Field(..., description="Protocol description")
    logo: str = Field(..., description="Protocol logo URL")
    chains: List[str] = Field(..., description="List of chains the protocol is on")
    tvl: float = Field(..., description="Total Value Locked in USD")
    change_1d: Optional[float] = Field(None, description="24h TVL change")
    change_7d: Optional[float] = Field(None, description="7d TVL change")
    change_30d: Optional[float] = Field(None, description="30d TVL change")
    mcap: Optional[float] = Field(None, description="Market cap in USD")
    fdv: Optional[float] = Field(None, description="Fully diluted valuation in USD")
    staking: Optional[float] = Field(None, description="Staking TVL in USD")
    borrowed: Optional[float] = Field(None, description="Borrowed amount in USD")
    category: str = Field(..., description="Protocol category")
    slug: str = Field(..., description="Protocol slug")
    tvl_rank: Optional[int] = Field(None, description="TVL rank")
    chain_tvls: Dict[str, float] = Field(..., description="TVL per chain")


class Pool(BaseModel):
    """Pool model."""

    id: str = Field(..., description="Pool ID")
    name: str = Field(..., description="Pool name")
    chain: str = Field(..., description="Chain name")
    project: str = Field(..., description="Project name")
    symbol: str = Field(..., description="Pool symbol")
    tvl: float = Field(..., description="Total Value Locked in USD")
    apy: Optional[float] = Field(None, description="Annual Percentage Yield")
    apy_7d: Optional[float] = Field(None, description="7d APY")
    apy_30d: Optional[float] = Field(None, description="30d APY")
    apy_1y: Optional[float] = Field(None, description="1y APY")
    apy_base: Optional[float] = Field(None, description="Base APY")
    apy_reward: Optional[float] = Field(None, description="Reward APY")
    reward_tokens: List[str] = Field(..., description="List of reward tokens")
    underlying_tokens: List[str] = Field(..., description="List of underlying tokens")
    url: str = Field(..., description="Pool URL")
    category: str = Field(..., description="Pool category")
    pool_meta: Optional[str] = Field(None, description="Pool metadata")


class PriceData(BaseModel):
    """Price data model."""

    price: float = Field(..., description="Token price in USD")
    timestamp: datetime = Field(..., description="Price timestamp")
    change_24h: Optional[float] = Field(None, description="24h price change")
    change_7d: Optional[float] = Field(None, description="7d price change")
    change_30d: Optional[float] = Field(None, description="30d price change")
    volume_24h: Optional[float] = Field(None, description="24h volume in USD")
    market_cap: Optional[float] = Field(None, description="Market cap in USD")
    fdv: Optional[float] = Field(None, description="Fully diluted valuation in USD")
    liquidity: Optional[float] = Field(None, description="Liquidity in USD")


class TVLData(BaseModel):
    """TVL data model."""

    date: datetime = Field(..., description="TVL date")
    total_tvl: float = Field(..., description="Total TVL in USD")
    chain_count: Optional[int] = Field(None, description="Number of chains")
    protocol_count: Optional[int] = Field(None, description="Number of protocols")
    chain_tvls: Dict[str, float] = Field(..., description="TVL per chain")
    protocol_tvls: Dict[str, float] = Field(..., description="TVL per protocol")
    category_tvls: Dict[str, float] = Field(..., description="TVL per category") 