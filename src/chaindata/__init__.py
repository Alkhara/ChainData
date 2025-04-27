"""ChainData - A comprehensive blockchain data aggregator and analysis tool."""

from importlib.metadata import version

__version__ = version("chaindata")

from .core.config import config
from .core.logger import logger
from .api.chainlist import ChainlistAPI
from .api.defillama import DefiLlamaAPI

# Initialize APIs
chainlist_api = ChainlistAPI()
defillama_api = DefiLlamaAPI()

__all__ = [
    "config",
    "logger",
    "chainlist_api",
    "defillama_api",
] 