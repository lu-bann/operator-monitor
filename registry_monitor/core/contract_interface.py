"""Contract interaction layer"""

import logging
from web3 import Web3
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

from ..config import REGISTRY_CONTRACT_ABI, TAIYI_REGISTRY_COORDINATOR_ABI, TAIYI_ESCROW_ABI, TAIYI_CORE_ABI, EIGENLAYER_MIDDLEWARE_ABI
from .web3_client import Web3Client

logger = logging.getLogger(__name__)


class ContractInterface(ABC):
    """Base interface for interacting with smart contracts"""
    
    def __init__(self, web3_client: Web3Client, contract_address: str, abi: List[Dict], contract_name: str = "Contract"):
        """
        Initialize contract interface
        
        Args:
            web3_client: Web3Client instance
            contract_address: The deployed contract address
            abi: Contract ABI
            contract_name: Name of the contract for logging
        """
        self.web3_client = web3_client
        self.contract_address = Web3.to_checksum_address(contract_address)
        self.contract_name = contract_name
        
        # Initialize contract instance
        self.contract = web3_client.web3.eth.contract(
            address=self.contract_address,
            abi=abi
        )
        
        logger.info(f"{self.contract_name} contract initialized at: {self.contract_address}")
    
    @abstractmethod
    def get_event_types(self) -> List[str]:
        """Return list of event types to monitor for this contract"""
        pass
    
    def create_event_filters(self, from_block='latest', event_types: Optional[List[str]] = None) -> List:
        """Create event filters for contract events"""
        if event_types is None:
            event_types = self.get_event_types()
            
        event_filters = []
        
        try:
            for event_type in event_types:
                if hasattr(self.contract.events, event_type):
                    event_filter = getattr(self.contract.events, event_type).create_filter(
                        fromBlock=from_block
                    )
                    event_filters.append(event_filter)
                else:
                    logger.warning(f"Event type '{event_type}' not found in {self.contract_name} contract")
            
            logger.info(f"Created {len(event_filters)} event filters for {self.contract_name}")
            return event_filters
            
        except Exception as e:
            logger.error(f"Error creating event filters for {self.contract_name}: {e}")
            raise
    
    def get_historical_events(self, event_name: str, from_block: int, to_block: int):
        """Get historical events for a specific event type"""
        try:
            if not hasattr(self.contract.events, event_name):
                logger.warning(f"Event '{event_name}' not found in {self.contract_name} contract")
                return []
                
            event_filter = getattr(self.contract.events, event_name).create_filter(
                fromBlock=from_block,
                toBlock=to_block
            )
            return event_filter.get_all_entries()
        except Exception as e:
            logger.warning(f"Error fetching {event_name} events for blocks {from_block}-{to_block} from {self.contract_name}: {e}")
            return [] 
    
    def get_all_historical_events(self, from_block: int, to_block: int, event_types: Optional[List[str]] = None) -> Dict[str, List]:
        """Get all historical events for multiple event types"""
        if event_types is None:
            event_types = self.get_event_types()
            
        all_events = {}
        for event_type in event_types:
            all_events[event_type] = self.get_historical_events(event_type, from_block, to_block)
        
        return all_events


class RegistryContract(ContractInterface):
    """Interface for interacting with the Registry contract"""
    
    def __init__(self, web3_client: Web3Client, contract_address: str):
        """
        Initialize Registry contract interface
        
        Args:
            web3_client: Web3Client instance
            contract_address: The deployed Registry contract address
        """
        super().__init__(
            web3_client=web3_client,
            contract_address=contract_address,
            abi=REGISTRY_CONTRACT_ABI,
            contract_name="Registry"
        )
    
    def get_event_types(self) -> List[str]:
        """Return Registry-specific event types"""
        return [
            'OperatorRegistered', 'OperatorSlashed', 'OperatorUnregistered',
            'CollateralClaimed', 'CollateralAdded', 'OperatorOptedIn', 'OperatorOptedOut'
        ]


class TaiyiRegistryCoordinatorContract(ContractInterface):
    """Interface for interacting with the TaiyiRegistryCoordinator contract"""
    
    def __init__(self, web3_client: Web3Client, contract_address: str):
        """
        Initialize TaiyiRegistryCoordinator contract interface
        
        Args:
            web3_client: Web3Client instance
            contract_address: The deployed TaiyiRegistryCoordinator contract address
        """
        super().__init__(
            web3_client=web3_client,
            contract_address=contract_address,
            abi=TAIYI_REGISTRY_COORDINATOR_ABI,
            contract_name="TaiyiRegistryCoordinator"
        )
    
    def get_event_types(self) -> List[str]:
        """Return TaiyiRegistryCoordinator-specific event types"""
        return [
            'OperatorRegistered', 'OperatorDeregistered', 'OperatorStatusChanged',
            'LinglongSubsetCreated', 'OperatorAddedToSubset', 'OperatorRemovedFromSubset',
            'SocketRegistryUpdated', 'PubkeyRegistryUpdated', 'OperatorSocketUpdate',
            'RestakingMiddlewareUpdated'
        ]


class TaiyiEscrowContract(ContractInterface):
    """Interface for interacting with the TaiyiEscrow contract"""
    
    def __init__(self, web3_client: Web3Client, contract_address: str):
        """
        Initialize TaiyiEscrow contract interface
        
        Args:
            web3_client: Web3Client instance
            contract_address: The deployed TaiyiEscrow contract address
        """
        super().__init__(
            web3_client=web3_client,
            contract_address=contract_address,
            abi=TAIYI_ESCROW_ABI,
            contract_name="TaiyiEscrow"
        )
    
    def get_event_types(self) -> List[str]:
        """Return TaiyiEscrow-specific event types"""
        return [
            'Deposited', 'Withdrawn', 'PaymentMade', 'RequestedWithdraw'
        ]


class TaiyiCoreContract(ContractInterface):
    """Interface for interacting with the TaiyiCore contract"""
    
    def __init__(self, web3_client: Web3Client, contract_address: str):
        """
        Initialize TaiyiCore contract interface
        
        Args:
            web3_client: Web3Client instance
            contract_address: The deployed TaiyiCore contract address
        """
        super().__init__(
            web3_client=web3_client,
            contract_address=contract_address,
            abi=TAIYI_CORE_ABI,
            contract_name="TaiyiCore"
        )
    
    def get_event_types(self) -> List[str]:
        """Return TaiyiCore-specific event types"""
        return [
            'Exhausted', 'TipCollected', 'PreconfRequestExecuted', 'TipReceived', 'EthSponsored'
        ]


class EigenLayerMiddlewareContract(ContractInterface):
    """Interface for interacting with the EigenLayerMiddleware contract"""
    
    def __init__(self, web3_client: Web3Client, contract_address: str):
        """
        Initialize EigenLayerMiddleware contract interface
        
        Args:
            web3_client: Web3Client instance
            contract_address: The deployed EigenLayerMiddleware contract address
        """
        super().__init__(
            web3_client=web3_client,
            contract_address=contract_address,
            abi=EIGENLAYER_MIDDLEWARE_ABI,
            contract_name="EigenLayerMiddleware"
        )
    
    def get_event_types(self) -> List[str]:
        """Return EigenLayerMiddleware-specific event types"""
        return [
            'RewardsHandlerSet', 'RewardsInitiatorSet', 'ValidatorsRegistered',
            'ValidatorsUnregistered', 'DelegationsBatchSet', 'SlasherOptedIn'
        ] 