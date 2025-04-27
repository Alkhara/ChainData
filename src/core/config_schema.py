from typing import Dict, Optional
from pydantic import BaseModel, Field, validator
from pathlib import Path

class CacheConfig(BaseModel):
    directory: str = Field(default="cache")
    expiry_seconds: int = Field(default=3600)
    blockchain_subdir: str = Field(default="blockchain")
    defillama_subdir: str = Field(default="defillama")

    @validator("directory")
    def validate_directory(cls, v):
        path = Path(v)
        if not path.exists():
            path.mkdir(parents=True)
        return str(path)

class APIConfig(BaseModel):
    base_url: str
    timeout: int = Field(default=10)
    retry_attempts: int = Field(default=3)
    retry_backoff: float = Field(default=1.0)
    rate_limit: Optional[int] = None

class ChainlistConfig(APIConfig):
    base_url: str = Field(default="https://chainlist.org")
    rpc_endpoint: str = Field(default="/rpcs.json")

class DefiLlamaConfig(APIConfig):
    base_url: str = Field(default="https://api.llama.fi")
    coins_url: str = Field(default="https://coins.llama.fi")
    stablecoins_url: str = Field(default="https://stablecoins.llama.fi")
    yields_url: str = Field(default="https://yields.llama.fi")

class DisplayConfig(BaseModel):
    date_format: str = Field(default="%Y-%m-%d %H:%M:%S")
    number_format: str = Field(default=",.2f")
    percentage_format: str = Field(default=".2%")
    table_width: int = Field(default=80)

class Config(BaseModel):
    cache: CacheConfig = Field(default_factory=CacheConfig)
    chainlist: ChainlistConfig = Field(default_factory=ChainlistConfig)
    defillama: DefiLlamaConfig = Field(default_factory=DefiLlamaConfig)
    display: DisplayConfig = Field(default_factory=DisplayConfig)
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    class Config:
        env_prefix = "CHAINDATA_"
        case_sensitive = False 