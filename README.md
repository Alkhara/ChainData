# ChainData

A comprehensive CLI tool for blockchain and DeFi data analysis.

## Quick Start

```bash
# Install
pip install -e .

# List all available chains
python chain_data.py --list

# Search for a chain
python chain_data.py --search "ethereum"

# Get chain data by ID
python chain_data.py --chain-id 1

# Get protocol information
python chain_data.py --protocol aave

# Get top protocols by TVL
python chain_data.py --top-protocols 10
```

## Features

### Blockchain Data
- Chain information and metadata
- RPC endpoints (HTTP and WebSocket)
- Block explorers
- EIP support
- Native currency details
- TVL (Total Value Locked) data

### DeFi Data (via DefiLlama API)
- Protocol TVL and historical data
- Chain-specific TVL
- Protocol search and information
- Top protocols by TVL
- Chain-specific protocols

#### Coins and Prices
- Current token prices
- Historical price data
- Batch historical prices
- Price charts
- Price percentage changes
- First price records

#### Stablecoins
- List all stablecoins
- Historical market cap data
- Chain-specific stablecoin data
- Individual stablecoin information
- Current stablecoin prices

#### Yields
- Pool data and APY
- Historical APY/TVL charts

#### Volumes
- DEX overview and metrics
- Chain-specific DEX data
- Individual DEX statistics
- Options DEX data

#### Fees and Revenue
- Protocol fees overview
- Chain-specific fees
- Individual protocol fee data

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/chaindata.git
cd chaindata
```

2. Install dependencies:
```bash
pip install -e .
```

## Usage Examples

### Chain Information

```bash
# List all chains in a table format
python chain_data.py --list --format table

# Search for chains with "eth" in their name
python chain_data.py --search "eth"

# Get detailed chain information
python chain_data.py --chain-id 1 --format json

# Get RPC endpoints for a chain
python chain_data.py --chain-id 1 --function http-rpcs
python chain_data.py --chain-id 1 --function wss-rpcs

# Get block explorers
python chain_data.py --chain-id 1 --function explorer

# Get EIP support
python chain_data.py --chain-id 1 --function eips
```

### DeFi Data

```bash
# Get protocol information
python chain_data.py --protocol aave

# Get top 10 protocols by TVL
python chain_data.py --top-protocols 10

# Get protocols on Ethereum
python chain_data.py --chain-protocols ethereum --limit 5

# Search for protocols
python chain_data.py --function search-protocols --search "lending"

# Get historical TVL data
python chain_data.py --protocol aave --function tvl-history
```

### Token Data

```bash
# Get current prices
python chain_data.py --function get-current-prices --coins "ethereum:0x...","bsc:0x..."

# Get historical prices
python chain_data.py --function get-historical-prices --coins "ethereum:0x..." --timestamp 1648680149

# Get price charts
python chain_data.py --function get-price-chart --coins "ethereum:0x..." --period "7d"
```

### Stablecoins

```bash
# List all stablecoins
python chain_data.py --function get-stablecoins

# Get stablecoin market cap data
python chain_data.py --function get-stablecoin-charts

# Get chain-specific stablecoin data
python chain_data.py --function get-chain-stablecoin-charts --chain ethereum
```

### Yields and APY

```bash
# Get pool data
python chain_data.py --function get-pools

# Get pool APY/TVL chart
python chain_data.py --function get-pool-chart --pool-id "pool-id"
```

### DEX Data

```bash
# Get DEX overview
python chain_data.py --function get-dex-overview

# Get chain-specific DEX data
python chain_data.py --function get-chain-dex-overview --chain ethereum

# Get options DEX data
python chain_data.py --function get-options-overview
```

### Fees and Revenue

```bash
# Get protocol fees overview
python chain_data.py --function get-fees-overview

# Get chain-specific fees
python chain_data.py --function get-chain-fees-overview --chain ethereum
```

## Command Line Arguments

### Chain Commands
- `--list`: List all available chains
- `--search`: Search for chains by name or ID
- `--chain-id`: Get chain data by ID
- `--name`: Get chain data by name
- `--function`: Specify the function to execute
- `--format`: Output format (table or json)

### Protocol Commands
- `--protocol`: Get protocol information
- `--top-protocols`: Get top N protocols by TVL
- `--chain-protocols`: Get protocols on a specific chain
- `--limit`: Limit the number of protocols shown
- `--search`: Search term for protocols

### Cache Commands
- `--refresh`: Force refresh the cache

## Data Sources

- Chain data: Chainlist.org
- DeFi data: DefiLlama API
  - TVL data
  - Protocol information
  - Chain-specific data
  - Coins and prices
  - Stablecoins
  - Yields
  - Volumes
  - Fees and revenue

## Caching

The application implements caching to improve performance and reduce API calls:
- Chain data is cached for 24 hours
- DefiLlama data is cached for 1 hour
- Cache can be force refreshed with `--refresh` flag

## Error Handling

The application includes comprehensive error handling:
- Invalid chain IDs or names
- API rate limits
- Network errors
- Invalid protocol names
- Missing required arguments

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 