from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime

class NativeCurrency(BaseModel):
    name: str
    symbol: str
    decimals: int
    address: Optional[str] = None

class Explorer(BaseModel):
    name: str
    url: str
    standard: Optional[str] = None
    icon: Optional[str] = None

class RPC(BaseModel):
    url: str
    tracking: Optional[str] = None
    tracking_details: Optional[Dict] = None
    is_public: bool = True

class Chain(BaseModel):
    chainId: int
    name: str
    shortName: Optional[str] = None
    chain: str
    network: str
    networkId: int
    nativeCurrency: NativeCurrency
    rpc: List[RPC]
    explorers: List[Explorer]
    infoURL: Optional[str] = None
    icon: Optional[str] = None
    features: Optional[List[Dict]] = None
    parent: Optional[Dict] = None
    status: Optional[str] = None
    redFlags: Optional[List[str]] = None
    slip44: Optional[int] = None
    ens: Optional[Dict] = None
    faucets: Optional[List[str]] = None
    testnet: bool = False
    slug: Optional[str] = None
    tvl: Optional[float] = None
    last_updated: Optional[datetime] = None

    @validator("rpc")
    def validate_rpcs(cls, v):
        if not v:
            raise ValueError("At least one RPC must be provided")
        return v

    @validator("explorers")
    def validate_explorers(cls, v):
        if not v:
            raise ValueError("At least one explorer must be provided")
        return v

class ChainSearchResult(BaseModel):
    chains: List[Chain]
    total: int
    page: int
    page_size: int

class ChainListResponse(BaseModel):
    data: List[Chain]
    last_updated: datetime
    version: str 