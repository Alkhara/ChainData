# ChainData

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.6%2B-blue.svg)](https://www.python.org/downloads/)

A Python utility for retrieving and managing blockchain network information, including RPC endpoints, explorers, and chain-specific data.

## Features

- Fetch and cache blockchain data from Chainlist.org
- Retrieve HTTP and WebSocket RPC endpoints for any supported chain
- Get blockchain explorer URLs
- Access chain-specific information including:
  - Native currency details
  - Supported EIPs
  - Total Value Locked (TVL)
  - Complete chain data
- Automatic caching with configurable expiry
- Support for both chain ID and chain name lookups

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Alkhara/ChainData.git
cd ChainData
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Command Line Interface

The tool can be used via command line with various options. All options have both long and short forms:

| Short | Long | Description |
|-------|------|-------------|
| `-c` | `--chain-id` | Chain ID |
| `-n` | `--name` | Chain name |
| `-f` | `--function` | Function to execute |
| `-s` | `--search` | Search for chains |
| `-l` | `--list` | List all available chains |
| `-o` | `--format` | Output format (table/json) |
| `-t` | `--no-tracking` | Exclude tracking RPCs |
| `-e` | `--explorer-type` | Specific explorer type |
| `-a` | `--address` | Address for explorer link |
| `-r` | `--force-refresh` | Force refresh cache |

#### Examples

```bash
# Get HTTP RPCs for Ethereum Mainnet
python chain_data.py -c 1 -f http-rpcs
# or
python chain_data.py --chain-id 1 --function http-rpcs

# Get explorer URLs for a specific chain
python chain_data.py -n "ethereum mainnet" -f explorer
# or
python chain_data.py --name "ethereum mainnet" --function explorer

# Get WebSocket RPCs with no tracking
python chain_data.py -c 1 -f wss-rpcs -t
# or
python chain_data.py --chain-id 1 --function wss-rpcs --no-tracking

# Search for chains containing "eth"
python chain_data.py -s eth
# or
python chain_data.py --search eth

# List all chains in JSON format
python chain_data.py -l -o json
# or
python chain_data.py --list --format json

# Get native currency information
python chain_data.py -c 1 -f native-currency
# or
python chain_data.py --chain-id 1 --function native-currency

# Get supported EIPs
python chain_data.py -c 1 -f eips
# or
python chain_data.py --chain-id 1 --function eips

# Get TVL information
python chain_data.py -c 1 -f tvl
# or
python chain_data.py --chain-id 1 --function tvl

# Force refresh cache
python chain_data.py -r -c 1 -f http-rpcs
# or
python chain_data.py --force-refresh --chain-id 1 --function http-rpcs
```

### Python API

You can also use the functions directly in your Python code:

```python
from chain_data import get_http_rpcs, get_wss_rpcs, get_explorer, get_eips

# Get HTTP RPCs
http_rpcs = get_http_rpcs(1)  # Using chain ID
http_rpcs = get_http_rpcs("ethereum mainnet")  # Using chain name

# Get WebSocket RPCs
wss_rpcs = get_wss_rpcs(1, no_tracking=True)

# Get explorer URLs
explorers = get_explorer(1)

# Get supported EIPs
eips = get_eips(1)
```

## Data Caching

The tool implements a caching mechanism to reduce API calls:
- Cache is stored in `blockchain_data_cache.json`
- Cache expires after 1 hour by default
- Force refresh available with `-r` or `--force-refresh` option

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Data provided by [Chainlist.org](https://chainlist.org/) 