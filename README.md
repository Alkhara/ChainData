# ChainData

A comprehensive CLI tool for blockchain and DeFi data analysis.

## Quick Start

1. Clone the repository and navigate to the directory:
```bash
git clone https://github.com/yourusername/ChainData.git
cd ChainData
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Try these example commands:
```bash
# Get help and see all available commands
python chain_data.py --help

# List all available chains
python chain_data.py chainlist list

# Search for a chain (works with names or chain IDs)
python chain_data.py chainlist search ethereum
python chain_data.py chainlist search 1  # Ethereum mainnet

# Get detailed chain information
python chain_data.py chainlist info ethereum

# Search for DeFi protocols
python chain_data.py defillama protocols --search aave

# Get top protocols by TVL (Total Value Locked)
python chain_data.py defillama protocols --limit 10

# Get output in JSON format (available for most commands)
python chain_data.py chainlist list --format json
```

Note: The tool caches data to reduce API calls. Use appropriate flags to force refresh when needed.

## Features

### Chain Information (via Chainlist)
- List all chains
- Search chains by name or ID
- Get detailed chain information
- Get RPC endpoints (HTTP and WebSocket)
- Filter RPCs by type (http/wss)
- Exclude tracking RPCs

### DeFi Data (via DefiLlama)
- Protocol TVL and historical data
- Chain-specific TVL
- Protocol search and filtering
- Top protocols by TVL
- Oracle filtering
- Chain display options

### DEX and Trading Data
- DEX volume overview
- Chain-specific DEX data
- 24h/7d/30d volume metrics
- Volume change percentages
- Options protocol data
- Fees and revenue data

### Price and Token Data
- Current token prices
- Historical price data
- Price charts
- Multiple token support
- Coingecko integration

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/chaindata.git
cd chaindata
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Command Reference

### Chainlist Commands

```bash
# List all chains
python chain_data.py chainlist list
python chain_data.py chainlist list --format json

# Search for chains
python chain_data.py chainlist search ethereum
python chain_data.py chainlist search "binance smart chain"

# Get chain information
python chain_data.py chainlist info ethereum
python chain_data.py chainlist info 1  # Using chain ID

# Get RPC endpoints
python chain_data.py chainlist rpcs ethereum --type http
python chain_data.py chainlist rpcs ethereum --type wss
python chain_data.py chainlist rpcs ethereum --type http --no-tracking
```

### DeFi Protocol Commands

```bash
# Get all protocols
python chain_data.py defillama protocols

# Get top protocols with limit
python chain_data.py defillama protocols --limit 10

# Search for protocols
python chain_data.py defillama protocols --search "aave"

# Filter by chain
python chain_data.py defillama protocols --chain ethereum

# Filter by oracle and show chains
python chain_data.py defillama protocols --oracle chainlink --show-chains

# Combine filters
python chain_data.py defillama protocols --chain ethereum --limit 5 --oracle chainlink
```

### DEX Commands

```bash
# Get DEX overview
python chain_data.py defillama dex

# Filter by chain
python chain_data.py defillama dex --chain ethereum

# Limit results and set minimum volume
python chain_data.py defillama dex --limit 10 --min-volume 1000000

# Get options protocol data
python chain_data.py defillama options
python chain_data.py defillama options --chain ethereum
```

### Price Commands

```bash
# Get current prices
python chain_data.py defillama prices BTC ETH LINK

# Get historical prices
python chain_data.py defillama prices BTC ETH --historical --timestamp 1625097600

# Common token symbols are automatically mapped:
# BTC -> coingecko:bitcoin
# ETH -> coingecko:ethereum
# LINK -> coingecko:chainlink
# etc.
```

### Yield Pool Commands

```bash
# Get all yield pools
python chain_data.py defillama pools

# Filter pools by TVL and APY
python chain_data.py defillama pools --min-tvl 1000000 --min-apy 5

# Limit results
python chain_data.py defillama pools --limit 20
```

## Output Formats

Most commands support multiple output formats:
- `--format table`: Human-readable table format (default)
- `--format json`: JSON format for programmatic use

## Data Caching

The tool implements intelligent caching to reduce API calls:
- Chain data is cached locally
- Cache expiry is configurable
- Force refresh with appropriate flags

## Error Handling

The tool provides clear error messages for:
- Invalid commands or arguments
- API request failures
- Rate limiting
- Network issues
- Invalid data formats

## Configuration

Configuration options can be found in `src/core/config.py`:
- Cache settings
- API endpoints
- Display options
- Rate limiting
- Timeout values 

## Development

### Code Style and Linting

This project uses several tools to maintain code quality:

1. **Flake8** for code linting:
```bash
# Run flake8 on the codebase
flake8 .
```

Flake8 is configured with the following settings:
- Max line length: 88 characters (matches Black)
- Ignores E203 (whitespace before ':')
- Excludes common directories (.git, __pycache__, etc.)
- Special rules for __init__.py and test files

2. **Black** for code formatting:
```bash
# Format code with Black
black .
```

3. **isort** for import sorting:
```bash
# Sort imports
isort .
```

To ensure your code meets the project's standards, run these tools before committing:
```bash
# Run all code quality checks
black .
isort .
flake8 .
```

### Testing

Run the test suite with pytest:
```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=src tests/
``` 