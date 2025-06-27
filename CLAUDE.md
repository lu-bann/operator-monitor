# CLAUDE.md

This file provides comprehensive guidance to Claude Code (claude.ai/code) when working with this blockchain monitoring and validator management repository.

## Project Overview

This repository contains two main Python components for blockchain monitoring and validator management:

1. **Registry Event Monitor** (`registry_monitor/`): Advanced Python-based blockchain event monitoring system
2. **Operator Status Tools** (`operator-status/`): Helix validator delegation checking and status tools

## Development Commands

### Python Environment Setup
```bash
# Install all dependencies (consolidated in main pyproject.toml)
pip install -e .

# Verify installation
python -c "import registry_monitor; print('Registry Monitor installed')"
```

### Registry Event Monitor
```bash
# Run live event monitoring
python -m registry_monitor.cli.main monitor

# Fetch historical events for analysis
python -m registry_monitor.cli.main history <from_block> [to_block] [max_events]

# Test configuration and connectivity
python -m registry_monitor.cli.main test

# Examples with specific configurations
NETWORK=holesky REGISTRY_CONTRACT_ADDRESS=0x... python -m registry_monitor.cli.main monitor
```

### Operator Status Tools
```bash
# Check single validator delegation status
cd operator-status && python main.py check 0x8a1d7b8dd64e0aafe7ea7b6c95065c9364cf99d38470db679bdf5c9bed34755c947c6c3cdb2f4a66dd4d31aae7e23d7a

# Batch process validators from file
cd operator-status && python main.py batch validators.txt --output results.json

# List all validators with delegation data in Redis
cd operator-status && python main.py list-validators

# Query validator registration status from PostgreSQL
cd operator-status && python main.py validator-info 0x8a1d... --postgres-host localhost --postgres-port 5434

# JSON output for programmatic use
cd operator-status && python main.py check 0x8a1d... --format json
```

## Architecture Overview

### Registry Event Monitor Architecture

**Core Philosophy**: Modular, extensible event monitoring with pluggable contract support and notification systems.

**Module Structure**:
- `registry_monitor/core/`: Blockchain interaction and contract interfaces
  - `web3_client.py`: Web3 connection management with retry logic
  - `contract_interface.py`: Multi-contract interface system (Registry, Taiyi, EigenLayer)
  - `event_processor.py`: Event parsing, formatting, and enrichment
- `registry_monitor/monitor/`: Real-time monitoring engine
  - `event_monitor.py`: Async event monitoring with filter management
  - `reconnection_handler.py`: Automatic reconnection on network failures
- `registry_monitor/notifications/`: Multi-channel notification system
  - `console_notifier.py`: Rich terminal output with formatting
  - `slack_notifier.py`: Slack integration for team notifications
  - `notification_manager.py`: Orchestrates multiple notification channels
- `registry_monitor/data/`: Event data management
  - `event_fetcher.py`: Historical and real-time event retrieval
  - `event_store.py`: In-memory and persistent storage abstractions
- `registry_monitor/config/`: Configuration and network management
  - `settings.py`: Environment-based configuration
  - `networks.py`: Multi-network support (Mainnet, Holesky, testnets)
  - `contract_abi.py`: ABI definitions for supported contracts
- `registry_monitor/cli/`: Command-line interface
  - `main.py`: Main CLI entry point with command routing
  - `commands.py`: Individual command implementations

**Supported Contract Types**:
- **Registry Contracts**: Traditional operator registration with slashing events
- **TaiyiRegistryCoordinator**: EigenLayer/Symbiotic operator management and coordination
- **TaiyiEscrow**: Deposit, withdrawal, and payment processing
- **TaiyiCore**: Core service lifecycle and configuration events
- **EigenLayerMiddleware**: Restaking protocol integration and rewards
- **EigenLayerAllocationManager**: Operator allocation and distribution management

**Key Design Patterns**:
- **Event-driven Architecture**: Async/await throughout for non-blocking operations
- **Pluggable Contracts**: Easy addition of new contract types via interface system
- **Resilient Monitoring**: Auto-reconnection, error recovery, and graceful degradation
- **Rich Notifications**: Structured event formatting with contextual information

### Operator Status Tools Architecture

**Purpose**: Comprehensive validation of Helix relay validator delegation rights through multi-database queries.

**Core Components**:
- `main.py`: Typer-based CLI with rich formatting and progress indicators
- `redis_client.py`: Redis connection wrapper for delegation message cache access
- `database.py`: PostgreSQL client for validator registration and status queries
- `delegation_parser.py`: BLS delegation message parsing and validation logic
- `validator_info.py`: Validator registration status service
- `models.py`: Pydantic data models with validation and serialization
- `config.py`: Multi-source configuration management (env vars, files, CLI args)

**Data Flow**:
1. **Redis Query**: Retrieve delegation messages using pattern `delegations:{validator_pubkey}`
2. **Message Parsing**: Validate BLS signatures and delegation/revocation actions
3. **State Calculation**: Determine active delegations (delegations minus revocations)
4. **PostgreSQL Lookup**: Cross-reference with validator registration status
5. **Result Formatting**: Output in table or JSON format with rich context

**Data Models**:
- `SignedDelegation`: BLS-signed delegation messages with action validation
- `DelegationQueryResult`: Aggregated delegation status with active delegatee tracking
- `ValidatorInfo`: Registration status and validator metadata
- `DelegationMessage`: Core delegation data structure matching Helix relay format

## Environment Configuration

### Required Environment Variables
```bash
# Network and RPC Configuration
NETWORK=holesky                           # Target network (mainnet, holesky, sepolia)
RPC_URL=https://ethereum-holesky.publicnode.com  # Custom RPC endpoint

# Registry Monitor Configuration
REGISTRY_CONTRACT_ADDRESS=0x...           # Main registry contract address
```

### Optional Environment Variables
```bash
# Extended Contract Addresses
TAIYI_COORDINATOR_CONTRACT_ADDRESS=0x...  # TaiyiRegistryCoordinator
TAIYI_ESCROW_CONTRACT_ADDRESS=0x...       # TaiyiEscrow contract
TAIYI_CORE_CONTRACT_ADDRESS=0x...         # TaiyiCore contract
EIGENLAYER_MIDDLEWARE_CONTRACT_ADDRESS=0x...  # EigenLayer middleware

# Notification Configuration
SLACK_BOT_TOKEN=xoxb-...                  # Slack bot token for notifications
SLACK_CHANNEL=C...                        # Slack channel ID for alerts

# Monitoring Behavior
SHOW_HISTORY=true                         # Display historical events on startup
FROM_BLOCK=12345                          # Starting block for event monitoring
USE_RECONNECTION=true                     # Enable automatic reconnection
CHECK_INTERVAL_SECONDS=10                 # Event polling interval

# Operator Status Tool Configuration
REDIS_URL=redis://localhost:6379         # Redis connection for delegation data
POSTGRES_HOST=localhost                   # PostgreSQL host for validator data
POSTGRES_PORT=5434                        # PostgreSQL port
POSTGRES_DB=helix_mev_relayer            # Database name
POSTGRES_USER=postgres                    # Database user
POSTGRES_PASSWORD=postgres                # Database password
```

## Development Guidelines

### Python Development Standards
- **Python Version**: 3.10+ required for modern type hints and async features
- **Type Hints**: Comprehensive typing throughout, using `typing` and `pydantic`
- **Async/Await**: Non-blocking operations for blockchain interactions
- **Error Handling**: Graceful degradation with comprehensive logging
- **Testing Strategy**: Integration testing with live networks via CLI test commands
- **Code Style**: Black formatting, isort imports, mypy type checking

### Code Organization Principles
- **Modular Design**: Clear separation of concerns with well-defined interfaces
- **Configuration Management**: Environment-based config with sensible defaults
- **Extensibility**: Plugin-style architecture for new contract types and notifiers
- **Documentation**: Comprehensive docstrings and inline comments
- **Error Recovery**: Robust error handling with automatic retry mechanisms

## Testing Strategies

### Python Component Testing
```bash
# Registry Monitor integration tests
python -m registry_monitor.cli.main test

# Test specific network configurations
NETWORK=holesky python -m registry_monitor.cli.main test

# Operator status tool validation
cd operator-status && python main.py check 0x... --verbose
```

### End-to-End Integration Testing
- **Live Network Testing**: Monitor and operator tools against live testnets
- **Contract Interaction**: Verify event monitoring captures contract deployments
- **Multi-Protocol Testing**: Validate EigenLayer and Symbiotic integrations
- **Performance Testing**: High-frequency event monitoring under load

## Integration Points and External Dependencies

### Blockchain Networks
- **Ethereum Mainnet**: Production operator monitoring and slashing enforcement
- **Holesky Testnet**: Primary testing and development environment
- **Sepolia Testnet**: Secondary testing for contract deployments
- **Custom Devnets**: Local development and testing

### External Protocol Integrations
- **EigenLayer**: Native AVS integration with operator management and slashing
- **Symbiotic**: Alternative restaking protocol with unified operator interface
- **Helix MEV Relay**: Validator delegation message parsing and status checking

### Database and Caching Systems
- **Redis**: High-performance delegation message caching and retrieval
- **PostgreSQL**: Persistent validator registration and status data
- **In-Memory Stores**: Event caching for real-time monitoring performance

### Notification and Alerting
- **Slack Integration**: Real-time team notifications for critical events
- **Console Output**: Rich terminal display with color coding and progress indicators
- **Structured Logging**: Comprehensive logging for debugging and audit trails

## Deployment and Operations

### Production Monitoring Setup
```bash
# Set up monitoring service
NETWORK=mainnet \
REGISTRY_CONTRACT_ADDRESS=0x... \
SLACK_BOT_TOKEN=... \
python -m registry_monitor.cli.main monitor

# Background service with systemd
sudo systemctl enable registry-monitor
sudo systemctl start registry-monitor
```

### Operational Monitoring
- **Event Volume**: Monitor event processing rates and blockchain sync status
- **Error Rates**: Track reconnection events and processing failures
- **Resource Usage**: Memory and CPU utilization for long-running monitors
- **Notification Delivery**: Verify Slack and console notification reliability

## Security Considerations

### Python Application Security
- **API Key Management**: Secure handling of Slack tokens and RPC credentials
- **Database Security**: Connection encryption and credential protection
- **Input Validation**: Comprehensive validation of blockchain addresses and parameters
- **Error Information**: Careful error handling to prevent information disclosure

## Troubleshooting Guide

### Common Issues

**Registry Monitor Connection Problems**:
```bash
# Check network connectivity
python -m registry_monitor.cli.main test

# Verify contract addresses
echo $REGISTRY_CONTRACT_ADDRESS

# Test with alternative RPC
RPC_URL=https://alternative-rpc.com python -m registry_monitor.cli.main test
```

**Operator Status Database Issues**:
```bash
# Test Redis connection
cd operator-status && python -c "import redis; r=redis.Redis(); print(r.ping())"

# Test PostgreSQL connection
cd operator-status && python main.py validator-info 0x000... --verbose
```

### Performance Optimization
- **Event Filtering**: Use specific block ranges for historical queries
- **Batch Processing**: Group multiple validator checks for efficiency
- **Connection Pooling**: Optimize database connections for high throughput
- **Caching Strategy**: Implement intelligent caching for frequently accessed data