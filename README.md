# Registry Event Monitor

A comprehensive monitoring system for blockchain registry contracts, supporting both traditional Registry contracts and the new TaiyiRegistryCoordinator contracts.

## Features

- **Multi-Contract Support**: Monitor multiple contract types simultaneously
- **Real-time Event Monitoring**: Live monitoring of blockchain events
- **Historical Event Fetching**: Retrieve and process historical events
- **Multiple Notification Channels**: Console output and Slack notifications
- **Auto-reconnection**: Automatic reconnection on network failures
- **Modular Architecture**: Easy to add new contract types

## Supported Contracts

### 1. Registry Contract
Traditional registry contract with events:
- `OperatorRegistered`
- `OperatorSlashed`
- `OperatorUnregistered`
- `CollateralClaimed`
- `CollateralAdded`
- `OperatorOptedIn`
- `OperatorOptedOut`

### 2. TaiyiRegistryCoordinator Contract
Advanced registry coordinator for EigenLayer and Symbiotic protocols with events:
- `OperatorRegistered`
- `OperatorDeregistered`
- `OperatorStatusChanged`
- `LinglongSubsetCreated`
- `OperatorAddedToSubset`
- `OperatorRemovedFromSubset`
- `SocketRegistryUpdated`
- `PubkeyRegistryUpdated`
- `OperatorSocketUpdate`
- `RestakingMiddlewareUpdated`

## Configuration

Configure your environment variables:

### Required Environment Variables
- `NETWORK` - Target blockchain network (mainnet, holesky, hoodi, devnet)
- `REGISTRY_CONTRACT_ADDRESS` - Registry contract address
- `RPC_URL` - Custom RPC endpoint (optional)
### Optional Environment Variables  
- `TAIYI_CONTRACT_ADDRESS` - TaiyiRegistryCoordinator contract address
- `SLACK_BOT_TOKEN` - Slack bot token for notifications
- `SLACK_CHANNEL` - Slack channel ID for notifications
- `SHOW_HISTORY` - Show historical events on startup (true/false)
- `FROM_BLOCK` - Starting block for historical data
- `USE_RECONNECTION` - Enable auto-reconnection (true/false)
- `CHUNK_SIZE` - Block chunk size for historical fetching

### Example Configuration

```bash
# Basic configuration
export NETWORK=holesky
export REGISTRY_CONTRACT_ADDRESS=0x1234567890123456789012345678901234567890
export TAIYI_CONTRACT_ADDRESS=0xabcdefabcdefabcdefabcdefabcdefabcdefabcdef
export RPC_URL=https://holesky.infura.io/v3/YOUR_PROJECT_ID

# Slack notifications (optional)
export SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
export SLACK_CHANNEL=C1234567890

# Historical data
export SHOW_HISTORY=true
export FROM_BLOCK=12345
```

### Environment File

Create a `.env` file in the project root:

```bash
NETWORK=holesky
REGISTRY_CONTRACT_ADDRESS=0x1234567890123456789012345678901234567890
TAIYI_CONTRACT_ADDRESS=0xabcdefabcdefabcdefabcdefabcdefabcdefabcdef
RPC_URL=https://holesky.infura.io/v3/YOUR_PROJECT_ID
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_CHANNEL=C1234567890
SHOW_HISTORY=true
FROM_BLOCK=12345
```

## Usage

### Basic Monitoring
```bash
export NETWORK=mainnet
export REGISTRY_CONTRACT_ADDRESS=0x1234567890123456789012345678901234567890
export TAIYI_CONTRACT_ADDRESS=0xabcdefabcdefabcdefabcdefabcdefabcdefabcdef
export RPC_URL=https://eth.llamarpc.com

python -m registry_monitor.cli.main monitor
```

### Commands
- `monitor` - Start real-time event monitoring
- `history <from_block> [to_block] [max_events]` - Fetch historical events
- `test` - Test all connections and configurations

### Example with Slack Notifications
```bash
export NETWORK=mainnet
export REGISTRY_CONTRACT_ADDRESS=0x1234567890123456789012345678901234567890
export TAIYI_CONTRACT_ADDRESS=0xabcdefabcdefabcdefabcdefabcdefabcdefabcdef
export SLACK_BOT_TOKEN=xoxb-your-bot-token
export SLACK_CHANNEL=C091L7Q0ZJN
export SHOW_HISTORY=true
export FROM_BLOCK=18000000

python -m registry_monitor.cli.main monitor
```

### Programmatic Usage
```python
import asyncio
from registry_monitor.cli.main import RegistryMonitorCLI

async def main():
    cli = RegistryMonitorCLI()
    
    # Add additional TaiyiRegistryCoordinator contracts
    cli.add_taiyi_contract("0x...", "secondary_taiyi")
    
    # Start monitoring
    await cli.run_monitor_command()

asyncio.run(main())
```

## Event Processing

Events are processed through a standardized pipeline:

1. **Validation** - Events are validated for required fields
2. **Storage** - Events are stored in memory (configurable)
3. **Formatting** - Events are formatted for different output channels
4. **Notification** - Formatted events are sent through notification channels

Each contract type has specialized formatting logic that displays relevant information in a user-friendly format with emojis and proper formatting.

## Architecture

The monitor uses a modular architecture:

- **ContractRegistry** - Manages multiple contract types and configurations
- **EventProcessor** - Handles event formatting and validation
- **NotificationManager** - Manages multiple notification channels
- **EventMonitor** - Core monitoring engine
- **ReconnectionHandler** - Handles automatic reconnection

## Networks Supported

- **Mainnet** (Chain ID: 1)
- **Holesky** (Chain ID: 17000) 
- **Hoodi** (Chain ID: 560048)
- **Devnet** (Chain ID: 1337)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables (see above)

3. Run the monitor:
```bash
python -m registry_monitor.cli.main monitor
```

## Adding New Contract Types

To add support for a new contract type:

1. Create the contract ABI in `registry_monitor/config/contract_abi.py`
2. Create a contract interface class inheriting from `ContractInterface`
3. Add event formatting logic to `EventProcessor`
4. Register the contract type in the CLI

See `TaiyiRegistryCoordinatorContract` as an example implementation.
