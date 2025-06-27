#!/usr/bin/env python3
"""Debug version of the monitor with enhanced logging"""

import logging
import asyncio
import sys

# Configure debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)

# Enable debug for specific components
logging.getLogger('operator_monitor.core.calldata_decoder').setLevel(logging.DEBUG)
logging.getLogger('operator_monitor.core.event_processor').setLevel(logging.DEBUG)
logging.getLogger('operator_monitor.core.web3_client').setLevel(logging.DEBUG)

# Import and run the main CLI
from operator_monitor.cli.main import main

if __name__ == "__main__":
    print("🐛 DEBUG MODE ENABLED")
    print("=" * 50)
    print("Enhanced logging for:")
    print("  - CalldataDecoder")
    print("  - EventProcessor") 
    print("  - Web3Client")
    print("=" * 50)
    
    asyncio.run(main())