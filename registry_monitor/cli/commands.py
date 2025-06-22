"""Command implementations"""

import asyncio
import logging
from typing import Optional, Dict, Any, List, Union
from ..core import Web3Client, ContractInterface, EventProcessor
from ..notifications import NotificationManager
from ..data import EventFetcher

logger = logging.getLogger(__name__)


class MonitorCommand:
    """Main monitoring command"""
    
    def __init__(self, event_monitor, use_reconnection: bool = True):
        """Initialize monitor command"""
        self.event_monitor = event_monitor
        self.use_reconnection = use_reconnection
    
    async def execute(self):
        """Execute monitoring"""
        if self.use_reconnection:
            from ..monitor import ReconnectionHandler
            reconnection_handler = ReconnectionHandler(self.event_monitor)
            await reconnection_handler.monitor_with_reconnection()
        else:
            await self.event_monitor.listen_for_events()


class HistoryCommand:
    """Historical events command"""
    
    def __init__(self, web3_client: Web3Client, contracts: Union[ContractInterface, List[ContractInterface]],
                 event_processor: EventProcessor, notification_manager: NotificationManager,
                 chunk_size: int = 50000):
        """Initialize history command"""
        self.event_fetcher = EventFetcher(web3_client, contracts, chunk_size)
        self.event_processor = event_processor
        self.notification_manager = notification_manager
        # Ensure contracts is always a list
        self.contracts = contracts if isinstance(contracts, list) else [contracts]
    
    async def fetch_and_display_history(self, from_block: Optional[int] = None, 
                                      max_events: int = 50, contract_filter: str = None):
        """Fetch and display historical events"""
        try:
            # Calculate from_block if not provided
            if from_block is None:
                current_block = self.event_fetcher.web3_client.get_current_block()
                from_block = max(0, current_block - 1000)
            
            contract_names = [c.contract_name for c in self.contracts]
            filter_text = f" (filtering by {contract_filter})" if contract_filter else ""
            print(f"📚 Fetching historical events from block {from_block}")
            print(f"📄 Monitoring contracts: {', '.join(contract_names)}{filter_text}")
            
            # Fetch events
            events = await self.event_fetcher.get_historical_events_async(
                from_block=from_block,
                max_events=max_events,
                contract_filter=contract_filter
            )
            
            if events:
                print(f"\n📚 HISTORICAL EVENTS ({len(events)} found)")
                print("="*80)
                
                for event in events:
                    # Format and display each event
                    console_message = self.event_processor.format_event(event)
                    print(console_message)
                    
                    # Send notifications for historical events
                    try:
                        self.notification_manager.send_notification(console_message, event)
                        logger.debug(f"Notification sent for historical event: {event['event']}")
                    except Exception as e:
                        logger.warning(f"Failed to send notification for historical event {event['event']}: {e}")
            else:
                print("\n📚 No historical events found")
                
        except Exception as e:
            logger.error(f"Error fetching historical events: {e}")


class TestCommand:
    """Test connections and functionality"""
    
    def __init__(self, web3_client: Web3Client, notification_manager: NotificationManager):
        """Initialize test command"""
        self.web3_client = web3_client
        self.notification_manager = notification_manager
    
    async def run_all_tests(self):
        """Run all available tests"""
        print("🧪 Running Registry Event Monitor Tests")
        print("="*50)
        
        # Test Web3 connection
        await self._test_web3_connection()
        
        # Test notification channels
        await self._test_notifications()
        
        print("\n✅ All tests completed")
    
    async def _test_web3_connection(self):
        """Test Web3 connection"""
        print("\n🔗 Testing Web3 Connection...")
        
        try:
            health = self.web3_client.health_check()
            
            if health['connected']:
                print(f"✅ Web3 connection successful")
                print(f"   Current block: {health['current_block']}")
                print(f"   Chain ID: {health['chain_id']}")
                print(f"   Network: {health['network']}")
            else:
                print(f"❌ Web3 connection failed: {health.get('error')}")
                
        except Exception as e:
            print(f"❌ Web3 connection test failed: {e}")
    
    async def _test_notifications(self):
        """Test notification channels"""
        print("\n📢 Testing Notification Channels...")
        
        try:
            test_results = self.notification_manager.test_all_connections()
            
            for notifier, success in test_results.items():
                status = "✅" if success else "❌"
                print(f"{status} {notifier}")
                
        except Exception as e:
            print(f"❌ Notification test failed: {e}") 