"""Core monitoring logic"""

import asyncio
import logging
from typing import Dict, Any, List, Union
from ..core.web3_client import Web3Client
from ..core.contract_interface import ContractInterface
from ..core.event_processor import EventProcessor
from ..notifications.notification_manager import NotificationManager
from ..data.event_store import EventStoreInterface

logger = logging.getLogger(__name__)


class EventMonitor:
    """Core event monitoring engine"""
    
    def __init__(self, web3_client: Web3Client, contracts: Union[ContractInterface, List[ContractInterface]],
                 event_processor: EventProcessor, notification_manager: NotificationManager,
                 event_store: EventStoreInterface = None):
        """
        Initialize event monitor
        
        Args:
            web3_client: Web3Client instance
            contracts: Single contract or list of contracts to monitor
            event_processor: EventProcessor instance
            notification_manager: NotificationManager instance
            event_store: Optional event store for persistence
        """
        self.web3_client = web3_client
        # Ensure contracts is always a list
        self.contracts = contracts if isinstance(contracts, list) else [contracts]
        self.event_processor = event_processor
        self.notification_manager = notification_manager
        self.event_store = event_store
        
        contract_names = [c.contract_name for c in self.contracts]
        logger.info(f"Event monitor initialized with contracts: {', '.join(contract_names)}")
    
    async def listen_for_events(self, from_block='latest', poll_interval: int = 2):
        """
        Listen for all contract events using improved async pattern
        
        Args:
            from_block: Block to start listening from ('latest', 'earliest', or block number)
            poll_interval: Seconds between polls
        """
        logger.info(f"Starting event listener from block: {from_block}")
        
        # Create event filters for all contracts
        try:
            all_event_filters = []
            for contract in self.contracts:
                event_filters = contract.create_event_filters(from_block=from_block)
                all_event_filters.extend(event_filters)
            
            logger.info(f"Created {len(all_event_filters)} event filters across {len(self.contracts)} contracts")
            
            print("\n🚀 Multi-Contract Event Monitor is now running...")
            print(f"📡 Monitoring {len(self.contracts)} contracts... (Press Ctrl+C to stop)")
            for contract in self.contracts:
                print(f"   📄 {contract.contract_name}: {contract.contract_address}")
            print("="*80)
            
        except Exception as e:
            logger.error(f"Error creating event filters: {e}")
            raise
        
        # Improved async polling pattern
        while True:
            try:
                # Process all filters concurrently
                tasks = []
                for event_filter in all_event_filters:
                    tasks.append(self._process_filter(event_filter))
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Log any exceptions from filter processing
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(f"Error processing filter {i}: {result}")
                
                await asyncio.sleep(poll_interval)
                
            except KeyboardInterrupt:
                logger.info("Stopping event monitor...")
                break
            except Exception as e:
                logger.error(f"Error polling events: {e}")
                await asyncio.sleep(poll_interval * 2)  # Wait longer on error
    
    async def _process_filter(self, event_filter):
        """Process a single event filter"""
        try:
            for event in event_filter.get_new_entries():
                # Try to identify which contract this event came from
                event_contract = self._identify_contract_for_event(event)
                if event_contract:
                    event['contract_name'] = event_contract.contract_name
                    event['contract_address'] = event_contract.contract_address
                
                await self.handle_event(event)
        except Exception as e:
            logger.error(f"Error processing filter: {e}")
    
    def _identify_contract_for_event(self, event: Dict[str, Any]) -> ContractInterface:
        """Identify which contract an event belongs to"""
        event_address = event.get('address', '').lower()
        
        for contract in self.contracts:
            if contract.contract_address.lower() == event_address:
                return contract
        
        return None
    
    async def handle_event(self, event: Dict[str, Any]):
        """Handle and process an event"""
        try:
            # Validate event
            if not self.event_processor.validate_event(event):
                logger.warning("Invalid event received, skipping")
                return
            
            # Store event if persistence is enabled
            if self.event_store:
                self.event_store.store_event(event)
            
            # Format for console display
            console_message = self.event_processor.format_event(event)
            
            # Send notifications through all channels
            success = self.notification_manager.send_notification(console_message, event)
            
            if success:
                logger.info(f"Event {event['event']} from {event.get('contract_name', 'Unknown')} processed and notifications sent")
            else:
                logger.warning(f"Event {event['event']} from {event.get('contract_name', 'Unknown')} processed but notifications failed")
                
        except Exception as e:
            logger.error(f"Error processing event: {e}")
            print(f"Raw event: {event}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get monitor status information"""
        try:
            health = self.web3_client.health_check()
            active_notifiers = self.notification_manager.get_active_notifiers()
            
            contract_info = []
            for contract in self.contracts:
                contract_info.append({
                    'name': contract.contract_name,
                    'address': contract.contract_address,
                    'event_types': contract.get_event_types()
                })
            
            return {
                'web3_connected': health['connected'],
                'current_block': health.get('current_block'),
                'chain_id': health.get('chain_id'),
                'network': health.get('network'),
                'active_notifiers': active_notifiers,
                'event_store_enabled': self.event_store is not None,
                'contracts': contract_info
            }
        except Exception as e:
            logger.error(f"Error getting monitor status: {e}")
            return {'error': str(e)} 