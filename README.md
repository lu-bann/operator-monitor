# Operator Monitor

A comprehensive monitoring system for blockchain operator and registry contracts, supporting both traditional Registry contracts and the new TaiyiRegistryCoordinator contracts.

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

### 3. TaiyiEscrow Contract
Escrow contract managing deposits, withdrawals and payments with events:
- `Deposited` - User deposits Ether
- `Withdrawn` - User withdraws Ether after lock period
- `PaymentMade` - Payment processed (pre or post execution)
- `RequestedWithdraw` - User requests withdrawal (starts lock period)

## Configuration

Configure your environment variables:

### Required Environment Variables
- `NETWORK` - Target blockchain network (mainnet, holesky, hoodi, devnet)
- `REGISTRY_CONTRACT_ADDRESS` - Registry contract address
- `RPC_URL` - Custom RPC endpoint (optional)
### Optional Environment Variables  
- `TAIYI_COORDINATOR_CONTRACT_ADDRESS` - TaiyiRegistryCoordinator contract address
- `TAIYI_ESCROW_CONTRACT_ADDRESS` - TaiyiEscrow contract address
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
export TAIYI_COORDINATOR_CONTRACT_ADDRESS=0xabcdefabcdefabcdefabcdefabcdefabcdefabcdef
export TAIYI_ESCROW_CONTRACT_ADDRESS=0x9876543210987654321098765432109876543210
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
TAIYI_COORDINATOR_CONTRACT_ADDRESS=0xabcdefabcdefabcdefabcdefabcdefabcdefabcdef
TAIYI_ESCROW_CONTRACT_ADDRESS=0x9876543210987654321098765432109876543210
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
export TAIYI_COORDINATOR_CONTRACT_ADDRESS=0xabcdefabcdefabcdefabcdefabcdefabcdefabcdef
export TAIYI_ESCROW_CONTRACT_ADDRESS=0x9876543210987654321098765432109876543210
export RPC_URL=https://eth.llamarpc.com

python -m operator_monitor.cli.main monitor
```

### Commands
- `monitor` - Start real-time event monitoring
- `history <from_block> [to_block] [max_events]` - Fetch historical events
- `test` - Test all connections and configurations

### Example with Slack Notifications
```bash
export NETWORK=mainnet
export REGISTRY_CONTRACT_ADDRESS=0x1234567890123456789012345678901234567890
export TAIYI_COORDINATOR_CONTRACT_ADDRESS=0xabcdefabcdefabcdefabcdefabcdefabcdefabcdef
export TAIYI_ESCROW_CONTRACT_ADDRESS=0x9876543210987654321098765432109876543210
export SLACK_BOT_TOKEN=xoxb-your-bot-token
export SLACK_CHANNEL=C091L7Q0ZJN
export SHOW_HISTORY=true
export FROM_BLOCK=18000000

python -m operator_monitor.cli.main monitor
```

### Programmatic Usage
```python
import asyncio
from operator_monitor.cli.main import RegistryMonitorCLI

async def main():
    cli = RegistryMonitorCLI()
    
    # Add additional TaiyiRegistryCoordinator contracts
    cli.add_taiyi_contract("0x...", "secondary_taiyi")
    
    # Add additional TaiyiEscrow contracts
    cli.add_taiyi_escrow_contract("0x...", "secondary_escrow")
    
    # Start monitoring
    await cli.run_monitor_command()

asyncio.run(main())
```