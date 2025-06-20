"""Contract interaction layer"""

import logging
from web3 import Web3
from typing import List

from ..config import REGISTRY_CONTRACT_ABI
from .web3_client import Web3Client

logger = logging.getLogger(__name__)


class  RegistryContract:
    """Interface for interacting with the Registry contract"""
    
    def __init__(self, web3_client: Web3Client, contract_address: str):
        """
        Initialize contract interface
        
        Args:
            web3_client: Web3Client instance
            contract_address: The deployed Registry contract address
        """
        self.web3_client = web3_client
        self.contract_address = Web3.to_checksum_address(contract_address)
        
        # Initialize contract instance
        self.contract = web3_client.web3.eth.contract(
            address=self.contract_address,
            abi=REGISTRY_CONTRACT_ABI
        )
        
        logger.info(f"Registry contract initialized at: {self.contract_address}")
    
    def create_event_filters(self, from_block='latest') -> List:
        """Create event filters for all Registry events"""
        event_filters = []
        
        try:
            # Create filters for each event type
            event_types = [
                'OperatorRegistered', 'OperatorSlashed', 'OperatorUnregistered',
                'CollateralClaimed', 'CollateralAdded', 'OperatorOptedIn', 'OperatorOptedOut'
            ]
            
            for event_type in event_types:
                event_filter = getattr(self.contract.events, event_type).create_filter(
                    fromBlock=from_block
                )
                event_filters.append(event_filter)
            
            logger.info(f"Created {len(event_filters)} event filters")
            return event_filters
            
        except Exception as e:
            logger.error(f"Error creating event filters: {e}")
            raise
    
    def get_historical_events(self, event_name: str, from_block: int, to_block: int):
        """Get historical events for a specific event type"""
        try:
            event_filter = getattr(self.contract.events, event_name).create_filter(
                fromBlock=from_block,
                toBlock=to_block
            )
            return event_filter.get_all_entries()
        except Exception as e:
            logger.warning(f"Error fetching {event_name} events for blocks {from_block}-{to_block}: {e}")
            return [] 