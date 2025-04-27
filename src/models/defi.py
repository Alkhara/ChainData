from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class Protocol(BaseModel):
    id: str
    name: str
    address: Optional[str] = None
    symbol: Optional[str] = None
    url: str
    description: Optional[str] = None
    chain: str
    logo: Optional[str] = None
    audits: Optional[List[str]] = None
    audit_note: Optional[str] = None
    gecko_id: Optional[str] = None
    cmcId: Optional[str] = None
    category: str
    chains: List[str]
    module: str
    twitter: Optional[str] = None
    language: Optional[str] = None
    parentProtocol: Optional[str] = None
    tvl: Optional[float] = None
    chainTvls: Optional[Dict[str, float]] = None
    change_1h: Optional[float] = None
    change_1d: Optional[float] = None
    change_7d: Optional[float] = None
    mcap: Optional[float] = None
    fdv: Optional[float] = None
    staking: Optional[float] = None
    pool2: Optional[float] = None
    borrowed: Optional[float] = None
    minted: Optional[float] = None
    treasury: Optional[float] = None
    vesting: Optional[float] = None
    lending: Optional[float] = None
    borrowed: Optional[float] = None
    stablecoins: Optional[float] = None
    pool2: Optional[float] = None
    other: Optional[float] = None
    last_updated: Optional[datetime] = None

class Pool(BaseModel):
    pool: str
    chain: str
    project: str
    symbol: str
    tvlUsd: float
    apy: Optional[float] = None
    apyBase: Optional[float] = None
    apyReward: Optional[float] = None
    rewardTokens: Optional[List[str]] = None
    underlyingTokens: Optional[List[str]] = None
    poolMeta: Optional[str] = None
    url: Optional[str] = None
    volumeUsd1d: Optional[float] = None
    volumeUsd7d: Optional[float] = None
    apyPct1D: Optional[float] = None
    apyPct7D: Optional[float] = None
    apyPct30D: Optional[float] = None
    stablecoin: Optional[bool] = None
    ilRisk: Optional[str] = None
    exposure: Optional[str] = None
    predictions: Optional[Dict] = None
    poolMeta: Optional[str] = None
    mu: Optional[float] = None
    sigma: Optional[float] = None
    count: Optional[int] = None
    outlier: Optional[bool] = None
    last_updated: Optional[datetime] = None

class PriceData(BaseModel):
    price: float
    timestamp: datetime
    confidence: Optional[float] = None
    source: Optional[str] = None
    volume24h: Optional[float] = None
    marketCap: Optional[float] = None
    change24h: Optional[float] = None
    change7d: Optional[float] = None
    change30d: Optional[float] = None
    high24h: Optional[float] = None
    low24h: Optional[float] = None

class TVLData(BaseModel):
    date: datetime
    totalLiquidityUSD: float
    chains: Optional[Dict[str, float]] = None
    protocols: Optional[Dict[str, float]] = None
    staking: Optional[float] = None
    pool2: Optional[float] = None
    borrowed: Optional[float] = None
    minted: Optional[float] = None
    treasury: Optional[float] = None
    vesting: Optional[float] = None
    lending: Optional[float] = None
    borrowed: Optional[float] = None
    stablecoins: Optional[float] = None
    pool2: Optional[float] = None
    other: Optional[float] = None 