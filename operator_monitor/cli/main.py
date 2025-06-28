"""New entry point for the Operator Monitor"""

import asyncio
import logging
import sys
from typing import Optional, List, Dict, Any

from ..config import settings, NETWORK_CONFIGS, REGISTRY_CONTRACT_ABI, TAIYI_REGISTRY_COORDINATOR_ABI, TAIYI_ESCROW_ABI, TAIYI_CORE_ABI, EIGENLAYER_MIDDLEWARE_ABI, EIGENLAYER_ALLOCATION_MANAGER_ABI
from ..core import Web3Client, ContractInterface, EventProcessor, TaiyiRegistryCoordinatorContract, TaiyiEscrowContract, TaiyiCoreContract, EigenLayerMiddlewareContract, EigenLayerAllocationManagerContract
from ..core.contract_interface import RegistryContract
from ..notifications import ConsoleNotifier, SlackNotifier, NotificationManager
from ..data import EventFetcher, InMemoryEventStore, NullEventStore
from ..data.redis_event_store import RedisEventStore
from ..monitor import EventMonitor, ReconnectionHandler
from .commands import MonitorCommand, HistoryCommand, TestCommand

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ContractRegistry:
    """Registry for managing multiple contract types"""
    
    def __init__(self):
        self.contract_types = {}
        self.contract_configs = {}
    
    def register_contract_type(self, name: str, contract_class: type, abi: List[Dict]):
        """Register a new contract type"""
        self.contract_types[name] = {
            'class': contract_class,
            'abi': abi
        }
    
    def add_contract_config(self, name: str, contract_type: str, address: str):
        """Add a contract configuration"""
        if contract_type not in self.contract_types:
            raise ValueError(f"Unknown contract type: {contract_type}")
        
        self.contract_configs[name] = {
            'type': contract_type,
            'address': address
        }
    
    def create_contracts(self, web3_client: Web3Client) -> List[ContractInterface]:
        """Create all configured contract instances"""
        contracts = []
        
        for name, config in self.contract_configs.items():
            contract_type_info = self.contract_types[config['type']]
            contract_class = contract_type_info['class']
            
            # Create contract instance
            contract = contract_class(web3_client, config['address'])
            contracts.append(contract)
        
        return contracts


class RegistryMonitorCLI:
    """Main CLI application"""
    
    def __init__(self):
        """Initialize CLI application"""
        self.settings = settings
        self.web3_client: Optional[Web3Client] = None
        self.contracts: List[ContractInterface] = []
        self.event_processor: Optional[EventProcessor] = None
        self.notification_manager: Optional[NotificationManager] = None
        self.event_monitor: Optional[EventMonitor] = None
        self.contract_registry = ContractRegistry()
        
        # Register default contract types
        self._register_default_contracts()
    
    def _register_default_contracts(self):
        """Register default contract types"""
        # Register Registry contract
        self.contract_registry.register_contract_type(
            'registry', 
            RegistryContract, 
            REGISTRY_CONTRACT_ABI
        )
        
        # Register TaiyiRegistryCoordinator contract
        self.contract_registry.register_contract_type(
            'taiyi_registry_coordinator',
            TaiyiRegistryCoordinatorContract,
            TAIYI_REGISTRY_COORDINATOR_ABI
        )
        
        # Register TaiyiEscrow contract
        self.contract_registry.register_contract_type(
            'taiyi_escrow',
            TaiyiEscrowContract,
            TAIYI_ESCROW_ABI
        )
        
        # Register TaiyiCore contract
        self.contract_registry.register_contract_type(
            'taiyi_core',
            TaiyiCoreContract,
            TAIYI_CORE_ABI
        )
        
        # Register EigenLayerMiddleware contract
        self.contract_registry.register_contract_type(
            'eigenlayer_middleware',
            EigenLayerMiddlewareContract,
            EIGENLAYER_MIDDLEWARE_ABI
        )
        
        # Register EigenLayer AllocationManager contract
        self.contract_registry.register_contract_type(
            'eigenlayer_allocation_manager',
            EigenLayerAllocationManagerContract,
            EIGENLAYER_ALLOCATION_MANAGER_ABI
        )
        
        # Add default Registry contract configuration
        self.contract_registry.add_contract_config(
            'main_registry',
            'registry', 
            self.settings.registry_contract_address
        )
        
        # Add TaiyiRegistryCoordinator contract if configured
        if self.settings.taiyi_coordinator_contract_address:
            self.contract_registry.add_contract_config(
                'taiyi_coordinator',
                'taiyi_registry_coordinator',
                self.settings.taiyi_coordinator_contract_address
            )
            logger.info(f"Added TaiyiRegistryCoordinator from environment: {self.settings.taiyi_coordinator_contract_address}")
        
        # Add TaiyiEscrow contract if configured
        if self.settings.taiyi_escrow_contract_address:
            self.contract_registry.add_contract_config(
                'taiyi_escrow',
                'taiyi_escrow',
                self.settings.taiyi_escrow_contract_address
            )
            logger.info(f"Added TaiyiEscrow from environment: {self.settings.taiyi_escrow_contract_address}")
        
        # Add TaiyiCore contract if configured
        if self.settings.taiyi_core_contract_address:
            self.contract_registry.add_contract_config(
                'taiyi_core',
                'taiyi_core',
                self.settings.taiyi_core_contract_address
            )
            logger.info(f"Added TaiyiCore from environment: {self.settings.taiyi_core_contract_address}")
        
        # Add EigenLayerMiddleware contract if configured
        if self.settings.eigenlayer_middleware_contract_address:
            self.contract_registry.add_contract_config(
                'eigenlayer_middleware',
                'eigenlayer_middleware',
                self.settings.eigenlayer_middleware_contract_address
            )
            logger.info(f"Added EigenLayerMiddleware from environment: {self.settings.eigenlayer_middleware_contract_address}")
        
        # Add EigenLayer AllocationManager contract if configured
        if self.settings.eigenlayer_allocation_manager_contract_address:
            self.contract_registry.add_contract_config(
                'eigenlayer_allocation_manager',
                'eigenlayer_allocation_manager',
                self.settings.eigenlayer_allocation_manager_contract_address
            )
            logger.info(f"Added EigenLayer AllocationManager from environment: {self.settings.eigenlayer_allocation_manager_contract_address}")
    
    def add_taiyi_contract(self, contract_address: str, name: str = "taiyi_coordinator"):
        """Add a TaiyiRegistryCoordinator contract to monitor"""
        self.contract_registry.add_contract_config(
            name,
            'taiyi_registry_coordinator',
            contract_address
        )
        logger.info(f"Added TaiyiRegistryCoordinator contract: {contract_address}")
    
    def add_taiyi_escrow_contract(self, contract_address: str, name: str = "taiyi_escrow"):
        """Add a TaiyiEscrow contract to monitor"""
        self.contract_registry.add_contract_config(
            name,
            'taiyi_escrow',
            contract_address
        )
        logger.info(f"Added TaiyiEscrow contract: {contract_address}")
    
    def add_taiyi_core_contract(self, contract_address: str, name: str = "taiyi_core"):
        """Add a TaiyiCore contract to monitor"""
        self.contract_registry.add_contract_config(
            name,
            'taiyi_core',
            contract_address
        )
        logger.info(f"Added TaiyiCore contract: {contract_address}")
    
    def _initialize_components(self):
        """Initialize all components for the monitor"""
        try:
            # Validate settings
            self.settings.validate()
            
            # Get network configuration
            network_config = NETWORK_CONFIGS[self.settings.network]
            
            # Initialize Web3 client
            rpc_url = self.settings.rpc_url or network_config['default_rpc']
            self.web3_client = Web3Client(rpc_url, self.settings.network)
            
            # Create contract instances
            self.contracts = self.contract_registry.create_contracts(self.web3_client)
            
            # Initialize event processor with EigenLayerMiddleware address for filtering and web3_client
            self.event_processor = EventProcessor(
                network_config, 
                eigenlayer_middleware_address=self.settings.eigenlayer_middleware_contract_address,
                web3_client=self.web3_client,
                enable_calldata_decoding=self.settings.enable_calldata_decoding
            )
            
            # Initialize notification manager
            self.notification_manager = NotificationManager()
            
            # Add console notifier (always available as fallback)
            console_notifier = ConsoleNotifier(verbose=True)
            self.notification_manager.add_notifier(console_notifier, is_fallback=True)
            
            # Add Slack notifier if configured
            if self.settings.slack_bot_token:
                slack_notifier = SlackNotifier(
                    token=self.settings.slack_bot_token,
                    channel=self.settings.slack_channel
                )
                self.notification_manager.add_notifier(slack_notifier)
            
            # Initialize event store
            event_store = InMemoryEventStore(max_events=1000)
            
            # Initialize Redis store if enabled
            redis_store = None
            if self.settings.enable_redis_storage:
                try:
                    redis_store = RedisEventStore(
                        redis_url=self.settings.redis_url,
                        key_prefix=self.settings.redis_key_prefix,
                        timeout=self.settings.redis_timeout
                    )
                    if redis_store.connect():
                        logger.info("Redis validator store enabled")
                    else:
                        logger.warning("Redis connection failed, disabling Redis storage")
                        redis_store = None
                except Exception as e:
                    logger.error(f"Error initializing Redis store: {e}")
                    redis_store = None
            
            # Initialize event monitor
            self.event_monitor = EventMonitor(
                web3_client=self.web3_client,
                contracts=self.contracts,
                event_processor=self.event_processor,
                notification_manager=self.notification_manager,
                event_store=event_store,
                redis_store=redis_store
            )
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise
    
    async def run_monitor_command(self):
        """Run the monitor command"""
        try:
            self._initialize_components()
            
            print(f"\n🔍 Registry Event Monitor - {self.settings.network.upper()}")
            print("="*80)
            
            # Display configuration
            network_config = NETWORK_CONFIGS[self.settings.network]
            rpc_url = self.settings.rpc_url or network_config['default_rpc']
            
            print(f"🌐 Network: {network_config['name']} (Chain ID: {network_config['chain_id']})")
            print(f"🔗 RPC URL: {rpc_url}")
            print(f"📄 Contracts being monitored:")
            for contract in self.contracts:
                print(f"   - {contract.contract_name}: {contract.contract_address}")
            print(f"🔍 Block Explorer: {network_config['block_explorer']}")
            
            # Test connections
            print("\n🧪 Testing connections...")
            
            # Test Web3 connection
            health = self.web3_client.health_check()
            if health['connected']:
                print(f"✅ Web3 connection successful")
                print(f"   Current block: {health['current_block']}")
                print(f"   Chain ID: {health['chain_id']}")
            else:
                print(f"❌ Web3 connection failed: {health.get('error')}")
                return
            
            # Test notifications
            test_results = self.notification_manager.test_all_connections()
            for notifier, success in test_results.items():
                status = "✅" if success else "❌"
                print(f"{status} {notifier}")
            
            # Show history if requested
            if self.settings.show_history:
                from_block = int(self.settings.from_block) if self.settings.from_block else 0
                print(f"\n📚 Fetching historical events from block {from_block}...")
                
                event_fetcher = EventFetcher(self.web3_client, self.contracts, chunk_size=self.settings.chunk_size)
                historical_events = await event_fetcher.get_historical_events_async(
                    from_block=from_block,
                    to_block='latest',
                    max_events=100
                )
                
                if historical_events:
                    print(f"Found {len(historical_events)} historical events")
                    for event in historical_events:
                        await self.event_monitor.handle_event(event)
                else:
                    print("No historical events found")
            
            # Start monitoring
            if self.settings.use_reconnection:
                print(f"\n🔄 Auto-reconnection enabled")
                reconnection_handler = ReconnectionHandler(self.event_monitor)
                await reconnection_handler.monitor_with_reconnection()
            else:
                print(f"\n🔄 Auto-reconnection disabled")
                await self.event_monitor.listen_for_events()
                
        except KeyboardInterrupt:
            print("\n👋 Monitor stopped by user")
        except Exception as e:
            logger.error(f"Error running monitor: {e}")
            raise
    
    async def run_history_command(self, from_block: int, to_block: str = 'latest', max_events: int = 100):
        """Run the history command"""
        try:
            self._initialize_components()
            
            print(f"\n📚 Fetching historical events from block {from_block} to {to_block}")
            print("="*80)
            
            event_fetcher = EventFetcher(self.web3_client, self.contracts, chunk_size=self.settings.chunk_size)
            historical_events = await event_fetcher.get_historical_events_async(
                from_block=from_block,
                to_block=to_block,
                max_events=max_events
            )
            
            if historical_events:
                print(f"Found {len(historical_events)} historical events")
                for event in historical_events:
                    await self.event_monitor.handle_event(event)
            else:
                print("No historical events found")
                
        except Exception as e:
            logger.error(f"Error running history command: {e}")
            raise
    
    async def run_test_command(self):
        """Run the test command"""
        try:
            self._initialize_components()
            
            print(f"\n🧪 Testing Registry Event Monitor - {self.settings.network.upper()}")
            print("="*80)
            
            # Test Web3 connection
            print("Testing Web3 connection...")
            health = self.web3_client.health_check()
            
            if health['connected']:
                print(f"✅ Web3 connection successful")
                print(f"   Current block: {health['current_block']}")
                print(f"   Chain ID: {health['chain_id']}")
                print(f"   Network: {health['network']}")
            else:
                print(f"❌ Web3 connection failed: {health.get('error')}")
            
            # Test contract connections
            print(f"\nTesting contract connections...")
            for contract in self.contracts:
                try:
                    # Test if we can create event filters
                    event_types = contract.get_event_types()
                    print(f"✅ {contract.contract_name} contract accessible")
                    print(f"   Address: {contract.contract_address}")
                    print(f"   Events: {', '.join(event_types)}")
                except Exception as e:
                    print(f"❌ {contract.contract_name} contract error: {e}")
            
            # Test notifications
            print(f"\nTesting notifications...")
            test_results = self.notification_manager.test_all_connections()
            
            for notifier, success in test_results.items():
                status = "✅" if success else "❌"
                print(f"{status} {notifier}")
            
            print(f"\n✅ Test completed")
            
        except Exception as e:
            logger.error(f"Error running test: {e}")
            raise


async def main():
    """Main entry point"""
    cli = RegistryMonitorCLI()
    
    if len(sys.argv) < 2:
        print("Usage: python -m registry_monitor.cli.main <command> [options]")
        print("Commands:")
        print("  monitor                    - Start monitoring for events")
        print("  history <from_block>      - Fetch historical events")
        print("  test                      - Test connections")
        return
    
    command = sys.argv[1].lower()
    
    try:
        if command == "monitor":
            await cli.run_monitor_command()
        elif command == "history":
            if len(sys.argv) < 3:
                print("Usage: python -m registry_monitor.cli.main history <from_block> [to_block] [max_events]")
                return
            from_block = int(sys.argv[2])
            to_block = sys.argv[3] if len(sys.argv) > 3 else 'latest'
            max_events = int(sys.argv[4]) if len(sys.argv) > 4 else 100
            await cli.run_history_command(from_block, to_block, max_events)
        elif command == "test":
            await cli.run_test_command()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: monitor, history, test")
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 