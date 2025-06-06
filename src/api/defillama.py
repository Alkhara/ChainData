import hashlib
import json
import os
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional, Union

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..core.cache import defillama_cache
from ..core.config import config


class DefiLlamaAPI:
    def __init__(self):
        self.base_url = "https://api.llama.fi"
        self.coins_url = "https://coins.llama.fi"
        self.stablecoins_url = "https://stablecoins.llama.fi"
        self.yields_url = "https://yields.llama.fi"
        self.session = self._create_session()

    def _create_session(self):
        """Create a requests session with retry logic"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _sanitize_cache_key(self, url: str, params: Optional[Dict] = None) -> str:
        """Create a safe cache key from URL and parameters"""
        # Combine URL and params into a string
        key = url
        if params:
            key += "?" + "&".join(f"{k}={v}" for k, v in sorted(params.items()))

        # Create a hash of the key to use as the filename
        return hashlib.md5(key.encode()).hexdigest()

    def _make_request(self, url: str, params: Optional[Dict] = None) -> Dict:
        """Make a request to the API with caching"""
        cache_key = self._sanitize_cache_key(url, params)
        cached_data = defillama_cache.load_from_cache(cache_key)
        if cached_data:
            return cached_data

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            defillama_cache.save_to_cache(cache_key, data)
            return data
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {url}: {e}")
            return {}

    # Existing TVL methods...

    # Coins/Prices API
    def get_current_prices(
        self, coins: List[str], search_width: str = "6h"
    ) -> Dict[str, Dict]:
        """Get current prices for a list of coins"""
        url = f"{self.coins_url}/prices/current/{','.join(coins)}"
        return self._make_request(url, {"searchWidth": search_width})

    def get_historical_prices(
        self, coins: List[str], timestamp: int, search_width: str = "6h"
    ) -> Dict[str, Dict]:
        """Get historical prices for a list of coins at a specific timestamp"""
        url = f"{self.coins_url}/prices/historical/{timestamp}/{','.join(coins)}"
        return self._make_request(url, {"searchWidth": search_width})

    def get_batch_historical_prices(
        self, coins: Dict[str, List[int]], search_width: str = "6h"
    ) -> Dict[str, Dict]:
        """Get historical prices for multiple coins at multiple timestamps"""
        url = f"{self.coins_url}/batchHistorical"
        return self._make_request(
            url, {"coins": json.dumps(coins), "searchWidth": search_width}
        )

    def get_price_chart(
        self,
        coins: List[str],
        start: Optional[int] = None,
        end: Optional[int] = None,
        span: int = 0,
        period: str = "24h",
        search_width: str = "10%",
    ) -> Dict[str, Dict]:
        """Get price chart data for coins"""
        url = f"{self.coins_url}/chart/{','.join(coins)}"
        params = {
            "start": start,
            "end": end,
            "span": span,
            "period": period,
            "searchWidth": search_width,
        }
        return self._make_request(
            url, {k: v for k, v in params.items() if v is not None}
        )

    def get_price_percentage(
        self,
        coins: List[str],
        timestamp: Optional[int] = None,
        look_forward: bool = False,
        period: str = "24h",
    ) -> Dict[str, float]:
        """Get percentage change in price over time"""
        url = f"{self.coins_url}/percentage/{','.join(coins)}"
        params = {"timestamp": timestamp, "lookForward": look_forward, "period": period}
        return self._make_request(
            url, {k: v for k, v in params.items() if v is not None}
        )

    def get_first_price(self, coins: List[str]) -> Dict[str, Dict]:
        """Get earliest price record for coins"""
        url = f"{self.coins_url}/prices/first/{','.join(coins)}"
        return self._make_request(url)

    # Stablecoins API
    def get_stablecoins(self, include_prices: bool = True) -> List[Dict]:
        """Get list of all stablecoins"""
        url = f"{self.stablecoins_url}/stablecoins"
        return self._make_request(url, {"includePrices": include_prices})

    def get_stablecoin_charts(self, stablecoin_id: Optional[int] = None) -> Dict:
        """Get historical mcap sum of all stablecoins"""
        url = f"{self.stablecoins_url}/stablecoincharts/all"
        return self._make_request(
            url, {"stablecoin": stablecoin_id} if stablecoin_id else None
        )

    def get_chain_stablecoin_charts(
        self, chain: str, stablecoin_id: Optional[int] = None
    ) -> Dict:
        """Get historical mcap sum of stablecoins on a chain"""
        url = f"{self.stablecoins_url}/stablecoincharts/{chain}"
        return self._make_request(
            url, {"stablecoin": stablecoin_id} if stablecoin_id else None
        )

    def get_stablecoin_data(self, asset_id: int) -> Dict:
        """Get historical mcap and chain distribution of a stablecoin"""
        url = f"{self.stablecoins_url}/stablecoin/{asset_id}"
        return self._make_request(url)

    def get_stablecoin_chains(self) -> Dict:
        """Get current mcap sum of stablecoins on each chain"""
        url = f"{self.stablecoins_url}/stablecoinchains"
        return self._make_request(url)

    def get_stablecoin_prices(self) -> Dict:
        """Get historical prices of all stablecoins"""
        url = f"{self.stablecoins_url}/stablecoinprices"
        return self._make_request(url)

    # Yields API
    def get_pools(self) -> List[Dict]:
        """Get latest data for all pools"""
        url = f"{self.yields_url}/pools"
        response = self._make_request(url)
        # The API returns a dictionary with pools under the 'data' key
        if isinstance(response, dict) and "data" in response:
            return response["data"]
        return response

    def get_pool_chart(self, pool_id: str) -> Dict:
        """Get historical APY and TVL of a pool"""
        url = f"{self.yields_url}/chart/{pool_id}"
        return self._make_request(url)

    # Volumes API
    def get_dex_overview(
        self, exclude_total_chart: bool = True, exclude_breakdown: bool = True
    ) -> Dict:
        """Get overview of all DEXs"""
        url = f"{self.base_url}/overview/dexs"
        return self._make_request(
            url,
            {
                "excludeTotalDataChart": exclude_total_chart,
                "excludeTotalDataChartBreakdown": exclude_breakdown,
            },
        )

    def get_chain_dex_overview(
        self,
        chain: str,
        exclude_total_chart: bool = True,
        exclude_breakdown: bool = True,
    ) -> Dict:
        """Get overview of DEXs on a specific chain"""
        url = f"{self.base_url}/overview/dexs/{chain}"
        return self._make_request(
            url,
            {
                "excludeTotalDataChart": exclude_total_chart,
                "excludeTotalDataChartBreakdown": exclude_breakdown,
            },
        )

    def get_dex_summary(
        self,
        protocol: str,
        exclude_total_chart: bool = True,
        exclude_breakdown: bool = True,
    ) -> Dict:
        """Get summary of a specific DEX"""
        url = f"{self.base_url}/summary/dexs/{protocol}"
        return self._make_request(
            url,
            {
                "excludeTotalDataChart": exclude_total_chart,
                "excludeTotalDataChartBreakdown": exclude_breakdown,
            },
        )

    # Options Volumes API
    def get_options_overview(
        self,
        exclude_total_chart: bool = False,
        exclude_breakdown: bool = False,
        data_type: str = "dailyNotionalVolume",
    ) -> Dict:
        """Get overview of all options DEXs"""
        url = f"{self.base_url}/overview/options"
        return self._make_request(
            url,
            {
                "excludeTotalDataChart": exclude_total_chart,
                "excludeTotalDataChartBreakdown": exclude_breakdown,
                "dataType": data_type,
            },
        )

    def get_chain_options_overview(
        self,
        chain: str,
        exclude_total_chart: bool = False,
        exclude_breakdown: bool = False,
        data_type: str = "dailyNotionalVolume",
    ) -> Dict:
        """Get overview of options DEXs on a specific chain"""
        url = f"{self.base_url}/overview/options/{chain}"
        return self._make_request(
            url,
            {
                "excludeTotalDataChart": exclude_total_chart,
                "excludeTotalDataChartBreakdown": exclude_breakdown,
                "dataType": data_type,
            },
        )

    def get_options_summary(
        self, protocol: str, data_type: str = "dailyNotionalVolume"
    ) -> Dict:
        """Get summary of a specific options DEX"""
        url = f"{self.base_url}/summary/options/{protocol}"
        return self._make_request(url, {"dataType": data_type})

    # Fees and Revenue API
    def get_fees_overview(
        self,
        exclude_total_chart: bool = False,
        exclude_breakdown: bool = False,
        data_type: str = "dailyFees",
    ) -> Dict:
        """Get overview of all protocol fees"""
        url = f"{self.base_url}/overview/fees"
        return self._make_request(
            url,
            {
                "excludeTotalDataChart": exclude_total_chart,
                "excludeTotalDataChartBreakdown": exclude_breakdown,
                "dataType": data_type,
            },
        )

    def get_chain_fees_overview(
        self,
        chain: str,
        exclude_total_chart: bool = False,
        exclude_breakdown: bool = False,
        data_type: str = "dailyFees",
    ) -> Dict:
        """Get overview of protocol fees on a specific chain"""
        url = f"{self.base_url}/overview/fees/{chain}"
        return self._make_request(
            url,
            {
                "excludeTotalDataChart": exclude_total_chart,
                "excludeTotalDataChartBreakdown": exclude_breakdown,
                "dataType": data_type,
            },
        )

    def get_fees_summary(self, protocol: str, data_type: str = "dailyFees") -> Dict:
        """Get summary of fees for a specific protocol"""
        url = f"{self.base_url}/summary/fees/{protocol}"
        return self._make_request(url, {"dataType": data_type})

    # TVL API
    def get_all_protocols(self) -> List[Dict]:
        """Get list of all protocols with their TVL"""
        url = f"{self.base_url}/protocols"
        return self._make_request(url)

    def get_protocol_tvl(self, protocol: str) -> Dict:
        """Get historical TVL of a protocol"""
        url = f"{self.base_url}/protocol/{protocol}"
        return self._make_request(url)

    def get_current_tvl(self, protocol: str) -> float:
        """Get current TVL of a protocol"""
        url = f"{self.base_url}/tvl/{protocol}"
        response = self._make_request(url)
        return float(response) if response else 0.0

    def get_historical_chain_tvl(self, chain: Optional[str] = None) -> Dict:
        """Get historical TVL of DeFi on all chains or a specific chain"""
        url = f"{self.base_url}/v2/historicalChainTvl"
        if chain:
            url = f"{url}/{chain}"
        return self._make_request(url)

    def get_all_chains_tvl(self) -> Dict:
        """Get current TVL of all chains"""
        url = f"{self.base_url}/v2/chains"
        return self._make_request(url)

    def get_protocol_info(self, protocol: str) -> Dict:
        """Get comprehensive protocol information including TVL history"""
        tvl_history = self.get_protocol_tvl(protocol)
        current_tvl = self.get_current_tvl(protocol)

        return {
            "name": protocol,
            "current_tvl": current_tvl,
            "tvl_history": tvl_history,
        }

    def search_protocols(self, query: str) -> List[Dict]:
        """Search for protocols by name"""
        query = query.lower()
        all_protocols = self.get_all_protocols()
        return [
            protocol
            for protocol in all_protocols
            if query in protocol.get("name", "").lower()
            or query in protocol.get("slug", "").lower()
        ]

    def get_top_protocols(self, limit: Optional[int] = None) -> List[Dict]:
        """Get top protocols by TVL"""
        all_protocols = self.get_all_protocols()
        if limit is None:
            limit = config.get("display.max_protocols")
        # Sort by TVL, treating None as 0
        return sorted(
            all_protocols,
            key=lambda x: x.get("tvl", 0) or 0,  # Convert None to 0
            reverse=True,
        )[:limit]

    def get_chain_protocols(self, chain: str) -> List[Dict]:
        """Get all protocols on a specific chain"""
        all_protocols = self.get_all_protocols()
        return [
            protocol
            for protocol in all_protocols
            if chain.lower() in [c.lower() for c in protocol.get("chains", [])]
        ]


# Create a global instance
defillama_api = DefiLlamaAPI()
