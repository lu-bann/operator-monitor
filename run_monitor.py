#!/usr/bin/env python3
"""
Entry point for the modular Registry Event Monitor
"""

import asyncio
from registry_monitor import main

if __name__ == "__main__":
    asyncio.run(main()) 