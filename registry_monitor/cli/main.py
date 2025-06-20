"""New entry point for the Registry Event Monitor"""

import asyncio
import logging
import sys
from typing import Optional

from ..config import settings, NETWORK_CONFIGS
from ..core import Web3Client, RegistryContract, EventProcessor
from ..notifications import ConsoleNotifier, SlackNotifier, NotificationManager
from ..data import EventFetcher, InMemoryEventStore, NullEventStore
from ..monitor import EventMonitor, ReconnectionHandler
from .commands import MonitorCommand, HistoryCommand, TestCommand

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RegistryMonitorCLI:
    """Main CLI application"""
    
    def __init__(self):
        """Initialize CLI application"""
        self.settings = settings
        self.web3_client: Optional[Web3Client] = None
        self.registry_contract: Optional[RegistryContract] = None
        self.event_processor: Optional[EventProcessor] = None
        self.notification_manager: Optional[NotificationManager] = None
        self.event_monitor: Optional[EventMonitor] = None
        
    def _initialize_components(self):
        """Initialize all application components"""
        try:
            # Validate settings
            self.settings.validate()
            
            # Get network configuration
            network_config = NETWORK_CONFIGS[self.settings.network]
            
            # Use provided RPC URL or default for network
            rpc_url = self.settings.rpc_url or network_config['default_rpc']
            
            # Initialize Web3 client
            self.web3_client = Web3Client(rpc_url, self.settings.network)
            
            # Initialize contract interface
            self.registry_contract = RegistryContract(
                self.web3_client, 
                self.settings.contract_address
            )
            
            # Initialize event processor
            self.event_processor = EventProcessor(network_config)
            
            # Initialize notification manager
            self.notification_manager = NotificationManager()
            
            # Add console notifier (always available)
            console_notifier = ConsoleNotifier(verbose=True)
            self.notification_manager.add_notifier(console_notifier, is_fallback=True)
            
            # Add Slack notifier if configured
            if self.settings.slack_bot_token:
                slack_notifier = SlackNotifier(
                    self.settings.slack_bot_token,
                    self.settings.slack_channel
                )
                self.notification_manager.add_notifier(slack_notifier)
            
            # Initialize event store (in-memory for now)
            event_store = InMemoryEventStore(max_events=1000)
            
            # Initialize event monitor
            self.event_monitor = EventMonitor(
                self.web3_client,
                self.registry_contract,
                self.event_processor,
                self.notification_manager,
                event_store
            )
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise
    
    def _print_startup_info(self):
        """Print startup information"""
        network_config = NETWORK_CONFIGS[self.settings.network]
        rpc_url = self.settings.rpc_url or network_config['default_rpc']
        
        print("🔍 Registry Event Monitor")
        print("="*50)
        print(f"🌐 Network: {network_config['name']} (Chain ID: {network_config['chain_id']})")
        print(f"🔗 RPC URL: {rpc_url}")
        print(f"📄 Contract: {self.settings.contract_address}")
        print(f"🔍 Block Explorer: {network_config['block_explorer']}")
        
        # Show notification channels
        active_notifiers = self.notification_manager.get_active_notifiers()
        print(f"📢 Notifications: {', '.join(active_notifiers)}")
        
        # Show configuration
        print(f"📚 Show history: {self.settings.show_history}")
        print(f"🔄 Auto-reconnection: {self.settings.use_reconnection}")
        print(f"📦 Chunk size: {self.settings.chunk_size} blocks")
        
        if self.settings.show_history and self.settings.from_block:
            print(f"📦 Starting from block: {self.settings.from_block}")
    
    async def run_monitor_command(self):
        """Run the main monitoring command"""
        try:
            self._initialize_components()
            self._print_startup_info()
            
            # Test connections
            print("\n🧪 Testing connections...")
            test_results = self.notification_manager.test_all_connections()
            
            for notifier, success in test_results.items():
                status = "✅" if success else "❌"
                print(f"{status} {notifier}")
            
            # Fetch historical events if requested
            if self.settings.show_history:
                history_command = HistoryCommand(
                    self.web3_client,
                    self.registry_contract,
                    self.event_processor,
                    self.notification_manager,
                    self.settings.chunk_size
                )
                
                from_block = None
                if self.settings.from_block:
                    try:
                        from_block = int(self.settings.from_block)
                    except ValueError:
                        logger.warning(f"Invalid FROM_BLOCK: {self.settings.from_block}")
                
                await history_command.fetch_and_display_history(from_block)
            
            # Start monitoring
            if self.settings.use_reconnection:
                print("🔄 Starting with automatic reconnection monitoring...")
                reconnection_handler = ReconnectionHandler(self.event_monitor)
                await reconnection_handler.monitor_with_reconnection()
            else:
                print("🎯 Starting basic event monitoring...")
                await self.event_monitor.listen_for_events()
                
        except KeyboardInterrupt:
            print("\n👋 Event monitor stopped by user")
        except Exception as e:
            logger.error(f"Monitor command failed: {e}")
            sys.exit(1)
    
    async def run_test_command(self):
        """Run connection tests"""
        try:
            self._initialize_components()
            
            test_command = TestCommand(
                self.web3_client,
                self.notification_manager
            )
            
            await test_command.run_all_tests()
            
        except Exception as e:
            logger.error(f"Test command failed: {e}")
            sys.exit(1)
    
    async def run_history_command(self, from_block: Optional[int] = None, 
                                max_events: int = 50):
        """Run history fetch command"""
        try:
            self._initialize_components()
            
            history_command = HistoryCommand(
                self.web3_client,
                self.registry_contract,
                self.event_processor,
                self.notification_manager,
                self.settings.chunk_size
            )
            
            await history_command.fetch_and_display_history(from_block, max_events)
            
        except Exception as e:
            logger.error(f"History command failed: {e}")
            sys.exit(1)


async def main():
    """Main entry point"""
    cli = RegistryMonitorCLI()
    
    # For now, just run the monitor command
    # In the future, this can be expanded with argument parsing
    await cli.run_monitor_command()


if __name__ == "__main__":
    asyncio.run(main()) 