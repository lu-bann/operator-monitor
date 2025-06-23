#!/usr/bin/env python3
"""
Example script for monitoring TaiyiRegistryCoordinator events

This script demonstrates how to monitor both the original Registry contract
and the new TaiyiRegistryCoordinator contract simultaneously.

Usage:
    export NETWORK=mainnet
    export REGISTRY_CONTRACT_ADDRESS=0x1234...  # Original Registry contract
    export TAIYI_CONTRACT_ADDRESS=0x5678...  # TaiyiRegistryCoordinator contract
    export RPC_URL=https://your-rpc-url
    export SLACK_BOT_TOKEN=xoxb-your-token  # Optional
    export SLACK_CHANNEL=your-channel  # Optional
    
    python example_taiyi_monitor.py
"""

import asyncio
import os
from registry_monitor.cli.main import RegistryMonitorCLI

async def main():
    """Main function to run the TaiyiRegistryCoordinator monitor"""
    
    print("🔍 TaiyiRegistryCoordinator Event Monitor Example")
    print("="*60)
    
    # Initialize the CLI
    cli = RegistryMonitorCLI()
    
    # Optionally add additional TaiyiRegistryCoordinator contracts manually
    # cli.add_taiyi_contract("0x...", "additional_taiyi_contract")
    
    # Run the monitor
    await cli.run_monitor_command()

if __name__ == "__main__":
    # Example environment setup (uncomment and modify as needed)
    # os.environ['NETWORK'] = 'mainnet'
    # os.environ['REGISTRY_CONTRACT_ADDRESS'] = '0x...'  # Your Registry contract
    # os.environ['TAIYI_CONTRACT_ADDRESS'] = '0x...'  # Your TaiyiRegistryCoordinator contract
    # os.environ['RPC_URL'] = 'https://eth.llamarpc.com'
    # os.environ['SLACK_BOT_TOKEN'] = 'xoxb-your-token'
    # os.environ['SLACK_CHANNEL'] = 'C091L7Q0ZJN'
    # os.environ['SHOW_HISTORY'] = 'true'
    # os.environ['FROM_BLOCK'] = '12345'
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Monitor stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}") 