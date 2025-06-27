# Transaction Calldata Decoding Enhancement

## Overview

The operator monitor has been enhanced with transaction calldata decoding capabilities for `OperatorRegistered` events from Registry contracts. When such events are detected and the transaction originated from the EigenLayerMiddleware contract's `registerValidators` function, the monitor will decode and display the validator registration details.

## Features

### Enhanced Event Display

When an `OperatorRegistered` event is detected that was triggered by a `registerValidators` function call from EigenLayerMiddleware, the event display will include additional transaction analysis:

```
📋 Transaction Analysis:
   🔍 Function: registerValidators()
   📊 Validators Registered: 3
   🔑 Validator Public Keys:
     - Validator #1: 0x1234abcd...5678efgh
     - Validator #2: 0x9876dcba...4321hgfe
     - Validator #3: 0x5555aaaa...9999ffff
   ✅ Triggered by EigenLayerMiddleware
```

### Decoded Information

For each validator registration, the system extracts:
- **BLS Public Keys**: The validator's BLS G1 point public key (x, y coordinates)
- **BLS Signatures**: The validator's BLS G2 point signature 
- **Registration Count**: Total number of validators being registered
- **Transaction Source**: Verification that the call came from EigenLayerMiddleware

## Configuration

### Environment Variables

#### Required
- `EIGENLAYER_MIDDLEWARE_CONTRACT_ADDRESS`: The address of the EigenLayerMiddleware contract to monitor for `registerValidators` calls

#### Optional  
- `ENABLE_CALLDATA_DECODING`: Enable/disable calldata decoding (default: `true`)
  - Set to `false` to disable transaction analysis for performance reasons

### Example Configuration

```bash
# .env file
NETWORK=holesky
REGISTRY_CONTRACT_ADDRESS=0x1234567890123456789012345678901234567890
EIGENLAYER_MIDDLEWARE_CONTRACT_ADDRESS=0xabcdefabcdefabcdefabcdefabcdefabcdefabcd
ENABLE_CALLDATA_DECODING=true
RPC_URL=https://ethereum-holesky.publicnode.com
```

## How It Works

### Detection Flow

1. **Event Monitoring**: The monitor detects `OperatorRegistered` events from Registry contracts
2. **Transaction Fetching**: When enabled, the system fetches the full transaction details
3. **Address Validation**: Checks if the transaction was sent to the configured EigenLayerMiddleware address
4. **Calldata Decoding**: Decodes the transaction input data using the `registerValidators` function ABI
5. **Analysis Display**: Formats and displays the decoded validator registration information

### Function Signature

The decoder specifically looks for transactions calling:
```solidity
function registerValidators(IRegistry.SignedRegistration[] calldata registrations) 
    external payable returns (bytes32)
```

Where each `SignedRegistration` contains:
```solidity
struct SignedRegistration {
    BLS.G1Point pubkey;    // BLS public key (x, y coordinates)
    BLS.G2Point signature; // BLS signature (4 field elements)
}
```

## Architecture

### New Components

#### CalldataDecoder (`operator_monitor/core/calldata_decoder.py`)
- Handles ABI decoding of `registerValidators` function calls
- Formats BLS public keys for display
- Validates function signatures and transaction sources

#### Enhanced EventProcessor
- Integrated transaction analysis for Registry events
- Conditional calldata decoding based on configuration
- Graceful fallback when decoding fails

#### Extended Web3Client
- Added transaction fetching methods
- Transaction receipt retrieval for additional context

## Error Handling

The system includes comprehensive error handling:

- **Graceful Degradation**: If calldata decoding fails, events are still processed normally
- **Address Validation**: Only processes transactions from the correct EigenLayerMiddleware contract
- **Function Validation**: Ensures transaction actually calls `registerValidators`
- **Logging**: Detailed logging for debugging decoding issues

## Performance Considerations

### Transaction Fetching Overhead
- Each `OperatorRegistered` event triggers an additional RPC call to fetch transaction details
- Consider disabling via `ENABLE_CALLDATA_DECODING=false` for high-frequency monitoring

### Memory Usage
- Transaction data is not persisted, only used for immediate analysis
- No significant impact on long-running monitoring processes

## Usage Examples

### Basic Monitoring with Calldata Decoding
```bash
# Set environment variables
export NETWORK=holesky
export REGISTRY_CONTRACT_ADDRESS=0x1234...
export EIGENLAYER_MIDDLEWARE_CONTRACT_ADDRESS=0xabcd...
export ENABLE_CALLDATA_DECODING=true

# Run monitor
python -m operator_monitor.cli.main monitor
```

### Disable Calldata Decoding
```bash
export ENABLE_CALLDATA_DECODING=false
python -m operator_monitor.cli.main monitor
```

### Historical Event Analysis
```bash
# Analyze historical events with calldata decoding
python -m operator_monitor.cli.main history 1000000 latest 50
```

## Troubleshooting

### Common Issues

#### No Transaction Analysis Displayed
- Verify `EIGENLAYER_MIDDLEWARE_CONTRACT_ADDRESS` is set correctly
- Check that `ENABLE_CALLDATA_DECODING=true`
- Ensure the transaction actually calls `registerValidators`

#### RPC Errors
- High-frequency requests may hit RPC rate limits
- Consider using a dedicated RPC endpoint for monitoring
- Disable calldata decoding if RPC resources are limited

#### Decoding Failures
- Check logs for specific ABI decoding errors
- Verify the EigenLayerMiddleware ABI is up to date
- Ensure transaction input data is valid

### Debug Mode
Enable debug logging to see detailed decoding information:
```python
import logging
logging.getLogger('operator_monitor.core.calldata_decoder').setLevel(logging.DEBUG)
```

## Future Enhancements

Potential areas for expansion:
- Support for other middleware contract functions
- Enhanced BLS signature validation
- Historical transaction analysis tools
- Performance optimizations for high-frequency monitoring