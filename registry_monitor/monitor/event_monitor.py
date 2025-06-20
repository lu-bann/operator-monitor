"""Core monitoring logic"""

import asyncio
import logging
from typing import Dict, Any, List
from ..core.web3_client import Web3Client
from ..core.contract_interface import RegistryContract
from ..core.event_processor import EventProcessor
from ..notifications.notification_manager import NotificationManager
from ..data.event_store import EventStoreInterface

logger = logging.getLogger(__name__)


class EventMonitor:
    """Core event monitoring engine"""
    
    def __init__(self, web3_client: Web3Client, registry_contract: RegistryContract,
                 event_processor: EventProcessor, notification_manager: NotificationManager,
                 event_store: EventStoreInterface = None):
        """
        Initialize event monitor
        
        Args:
            web3_client: Web3Client instance
            registry_contract: RegistryContract instance  
            event_processor: EventProcessor instance
            notification_manager: NotificationManager instance
            event_store: Optional event store for persistence
        """
        self.web3_client = web3_client
        self.registry_contract = registry_contract
        self.event_processor = event_processor
        self.notification_manager = notification_manager
        self.event_store = event_store
        
        logger.info("Event monitor initialized")
    
    async def listen_for_events(self, from_block='latest', poll_interval: int = 2):
        """
        Listen for all Registry events using improved async pattern
        
        Args:
            from_block: Block to start listening from ('latest', 'earliest', or block number)
            poll_interval: Seconds between polls
        """
        logger.info(f"Starting event listener from block: {from_block}")
        
        # Create event filters for all events
        try:
            event_filters = self.registry_contract.create_event_filters(from_block=from_block)
            logger.info("Event filters created successfully")
            
            print("\n🚀 Registry Event Monitor is now running...")
            print("📡 Listening for events... (Press Ctrl+C to stop)")
            print("="*80)
            
        except Exception as e:
            logger.error(f"Error creating event filters: {e}")
            raise
        
        # Improved async polling pattern
        while True:
            try:
                # Process all filters concurrently
                tasks = []
                for event_filter in event_filters:
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
                await self.handle_event(event)
        except Exception as e:
            logger.error(f"Error processing filter: {e}")
    
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
            
            # Format for Slack (if needed)
            slack_message = self.event_processor.format_slack_message(event)
            
            # Send notifications through all channels
            success = self.notification_manager.send_notification(console_message, event)
            
            if success:
                logger.info(f"Event {event['event']} processed and notifications sent")
            else:
                logger.warning(f"Event {event['event']} processed but notifications failed")
                
        except Exception as e:
            logger.error(f"Error processing event: {e}")
            print(f"Raw event: {event}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get monitor status information"""
        try:
            health = self.web3_client.health_check()
            active_notifiers = self.notification_manager.get_active_notifiers()
            
            return {
                'web3_connected': health['connected'],
                'current_block': health.get('current_block'),
                'chain_id': health.get('chain_id'),
                'network': health.get('network'),
                'active_notifiers': active_notifiers,
                'event_store_enabled': self.event_store is not None
            }
        except Exception as e:
            logger.error(f"Error getting monitor status: {e}")
            return {'error': str(e)} 