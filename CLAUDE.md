# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Structure

This is a hybrid repository containing two main components:

1. **Python Event Monitor** (`/`): A comprehensive blockchain event monitoring system for Registry and Taiyi contracts
2. **LingLong Solidity Contracts** (`/linglong/`): A proposer commitment framework for Ethereum with EigenLayer and Symbiotic integrations

## Common Development Commands

### Python Event Monitor
```bash
# Install dependencies
pip install -e .

# Run the monitor with environment variables
python -m registry_monitor.cli.main monitor

# Fetch historical events
python -m registry_monitor.cli.main history <from_block> [to_block] [max_events]

# Test configuration
python -m registry_monitor.cli.main test
```

### Solidity Contracts (LingLong)
```bash
# Install dependencies
cd linglong && forge install

# Run tests
forge test

# Format code
forge fmt

# Build contracts
forge build

# Run specific test
forge test --match-test testFunctionName

# Generate gas reports
forge test --gas-report
```

## Architecture Overview

### Python Event Monitor Architecture

**Core Components:**
- `registry_monitor/core/`: Web3 client, contract interfaces, event processing
- `registry_monitor/monitor/`: Event monitoring with auto-reconnection
- `registry_monitor/notifications/`: Multi-channel notification system (Console, Slack)
- `registry_monitor/data/`: Event fetching and storage abstractions
- `registry_monitor/config/`: Network configurations and contract ABIs

**Contract Support:**
- Registry contracts (traditional with slashing events)
- TaiyiRegistryCoordinator (EigenLayer/Symbiotic operator management)
- TaiyiEscrow (deposit/withdrawal/payment events)
- TaiyiCore (core service events)
- EigenLayerMiddleware (restaking protocol events)

**Key Patterns:**
- Modular contract interface system with pluggable contract types
- Event processor with contract-specific formatting
- Auto-reconnection on network failures
- Real-time and historical event fetching

### LingLong Solidity Architecture

**Core System:**
- `src/taiyi/`: Core Taiyi contracts (TaiyiCore, TaiyiEscrow, parameter managers)
- `src/operator-registries/`: Unified operator registration system
- `src/eigenlayer-avs/`: EigenLayer middleware integration
- `src/symbiotic-network/`: Symbiotic protocol middleware
- `src/slasher/`: LinglongSlasher for cross-protocol slashing
- `src/libs/`: Shared libraries (cryptography, protocol mappings, utilities)

**Key Design Patterns:**
- OpenZeppelin upgradeable proxy pattern throughout
- Multi-protocol restaking support (EigenLayer + Symbiotic)
- Operator subset management with ID encoding
- BLS signature integration with SP1 zkVM proofs
- Comprehensive slashing and rewards system

## Environment Configuration

### Required Environment Variables
```bash
NETWORK=holesky                    # Target network
REGISTRY_CONTRACT_ADDRESS=0x...    # Registry contract
RPC_URL=https://...               # Custom RPC endpoint
```

### Optional Environment Variables
```bash
TAIYI_COORDINATOR_CONTRACT_ADDRESS=0x...           # TaiyiRegistryCoordinator
TAIYI_ESCROW_CONTRACT_ADDRESS=0x...    # TaiyiEscrow
SLACK_BOT_TOKEN=xoxb-...              # Slack notifications
SLACK_CHANNEL=C...                    # Slack channel ID
SHOW_HISTORY=true                     # Show historical events
FROM_BLOCK=12345                      # Starting block
USE_RECONNECTION=true                 # Auto-reconnection
```

## Development Guidelines

### Solidity Development
- Use Solidity 0.8.27 with Prague EVM version (for BLS precompiles)
- Follow upgradeable proxy patterns for all contracts
- Extensive testing with Foundry (unit, integration, fuzz testing)
- FFI enabled for cryptographic operations (G2 operations, BLS)
- Complex multi-protocol integration testing required

### Python Development
- Python 3.10+ required
- Uses web3.py for blockchain interactions
- Async/await patterns throughout
- Modular architecture with dependency injection
- Environment-based configuration

## Testing Patterns

### Solidity Tests
- Located in `linglong/test/`
- Uses Foundry with extensive mocking
- Upgradeable proxy deployment patterns in tests
- Cross-protocol integration testing (EigenLayer, Symbiotic)
- Event emission testing and access control validation

### Python Tests
- No dedicated test suite currently exists
- Testing happens through CLI commands (`test` command)
- Real-time validation against live networks

## Integration Points

The repository integrates with:
- **EigenLayer**: Operator registration, delegation, slashing
- **Symbiotic**: Alternative restaking protocol
- **SP1 zkVM**: Zero-knowledge proof verification
- **BLS cryptography**: Signature aggregation and verification
- **Ethereum networks**: Mainnet, Holesky, custom devnets

## Contract Deployment

Deployment configurations are stored in:
- `linglong/script/configs/`: Network-specific deployment parameters
- `linglong/script/output/`: Deployed contract addresses by network
- Scripts use Forge's deployment system with proxy patterns