# ChainData

A powerful command-line tool for retrieving blockchain and DeFi data, including chain information, RPC endpoints, and Total Value Locked (TVL) metrics.

## Features

- Chain Information
  - Get chain data by ID or name
  - List all available chains
  - Search for chains
  - Get RPC endpoints (HTTP and WSS)
  - Get explorer links
  - Get native currency information
  - Get EIP support information

- DeFi Data (via DefiLlama API)
  - Get protocol TVL data
  - Get chain TVL data
  - Search for protocols
  - Get top protocols by TVL
  - Get protocols on specific chains

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ChainData.git
cd ChainData
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Chain Information

List all available chains:
```bash
python chain_data.py -l
```

Search for chains:
```bash
python chain_data.py -s "eth"
```

Get chain data by ID:
```bash
python chain_data.py -c 1 -f chain-data
```

Get chain data by name:
```bash
python chain_data.py -n "Ethereum" -f chain-data
```

Get HTTP RPCs:
```bash
python chain_data.py -c 1 -f http-rpcs
```

Get WSS RPCs:
```bash
python chain_data.py -c 1 -f wss-rpcs
```

Get explorer links:
```bash
python chain_data.py -c 1 -f explorer-link -a "0x123..."
```

### DeFi Data (DefiLlama)

Get protocol TVL:
```bash
python chain_data.py --protocol aave
```

Get top protocols by TVL:
```bash
python chain_data.py --top-protocols 10
```

Get all protocols on a specific chain:
```bash
python chain_data.py --chain-protocols ethereum
```

Search for protocols:
```bash
python chain_data.py -f search-protocols -s "uni"
```

Get chain TVL:
```bash
python chain_data.py -f chain-tvl --chain-protocols ethereum
```

## Command Line Arguments

### Chain Information Arguments
- `-c, --chain-id`: Chain ID
- `-n, --name`: Chain name
- `-s, --search`: Search for chains
- `-l, --list`: List all available chains
- `-f, --function`: Function to execute
  - `http-rpcs`: Get HTTP RPCs
  - `wss-rpcs`: Get WSS RPCs
  - `explorer`: Get explorer links
  - `eips`: Get EIP support
  - `native-currency`: Get native currency info
  - `tvl`: Get TVL data
  - `chain-data`: Get chain data
  - `explorer-link`: Get explorer link for address

### DefiLlama Arguments
- `--protocol`: Protocol name for TVL data
- `--top-protocols`: Get top N protocols by TVL
- `--chain-protocols`: Get all protocols on a specific chain
- `-f, --function` (additional options):
  - `protocol-tvl`: Get protocol TVL data
  - `chain-tvl`: Get chain TVL data
  - `search-protocols`: Search for protocols

### Additional Options
- `-o, --format`: Output format (table or json)
- `-t, --no-tracking`: Exclude tracking RPCs
- `-e, --explorer-type`: Specific explorer type
- `-a, --address`: Address for explorer link
- `-r, --force-refresh`: Force refresh cache

## Data Sources

- Chain Information: Chainlist.org
- DeFi Data: DefiLlama API (https://api.llama.fi)

## Caching

The tool implements caching for:
- Chain data (1 hour expiry)
- DefiLlama API responses (using LRU cache)

## Error Handling

The tool includes comprehensive error handling for:
- API request failures
- Invalid inputs
- Network issues
- Cache errors

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 