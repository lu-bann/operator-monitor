"""Historical event retrieval with chunking and retry mechanisms"""

import logging
import asyncio
from typing import List, Dict, Any, Union
from ..core.contract_interface import ContractInterface
from ..core.web3_client import Web3Client

logger = logging.getLogger(__name__)


class EventFetcher:
    """Handles fetching historical events with chunking and retry logic"""
    
    def __init__(self, web3_client: Web3Client, contracts: Union[ContractInterface, List[ContractInterface]], 
                 chunk_size: int = 50000, max_retries: int = 3):
        """
        Initialize event fetcher
        
        Args:
            web3_client: Web3Client instance
            contracts: Single contract or list of contracts to monitor
            chunk_size: Number of blocks per chunk
            max_retries: Maximum retry attempts per chunk
        """
        self.web3_client = web3_client
        # Ensure contracts is always a list
        self.contracts = contracts if isinstance(contracts, list) else [contracts]
        self.chunk_size = chunk_size
        self.max_retries = max_retries
    
    def get_historical_events(self, from_block: int = 0, to_block: str = 'latest', 
                            max_events: int = 100, contract_filter: str = None) -> List[Dict[str, Any]]:
        """
        Get historical events using improved chunking pattern
        
        Args:
            from_block: Starting block number
            to_block: Ending block number ('latest' for current block)  
            max_events: Maximum number of events to retrieve
            contract_filter: Optional contract name filter
            
        Returns:
            List of event dictionaries sorted by block number
        """
        logger.info(f"Fetching historical events from block {from_block} to {to_block}")
        
        try:
            # Get the actual end block number
            if to_block == 'latest':
                end_block = self.web3_client.get_current_block()
            else:
                end_block = int(to_block)
            
            # Calculate the total range
            total_range = end_block - from_block
            
            logger.info(f"Total block range: {total_range} blocks, using chunks of {self.chunk_size}")
            
            all_events = []
            
            # Filter contracts if specified
            contracts_to_process = self.contracts
            if contract_filter:
                contracts_to_process = [c for c in self.contracts if c.contract_name.lower() == contract_filter.lower()]
                if not contracts_to_process:
                    logger.warning(f"No contracts found matching filter: {contract_filter}")
                    return []
            
            # Process in chunks to avoid RPC limits
            current_block = from_block
            chunk_count = 0
            
            while current_block <= end_block:
                chunk_end = min(current_block + self.chunk_size - 1, end_block)
                chunk_count += 1
                
                logger.info(f"Processing chunk {chunk_count}: blocks {current_block} to {chunk_end}")
                
                chunk_events = self._fetch_chunk_with_retry(
                    contracts_to_process, current_block, chunk_end
                )
                all_events.extend(chunk_events)
                
                current_block = chunk_end + 1
            
            # Limit results
            if len(all_events) > max_events:
                all_events = all_events[-max_events:]  # Get most recent events
            
            # Sort events by block number and transaction index
            all_events.sort(key=lambda x: (x['blockNumber'], x['transactionIndex']))
            
            logger.info(f"Found {len(all_events)} historical events across {chunk_count} chunks")
            return all_events
            
        except Exception as e:
            logger.error(f"Error fetching historical events: {e}")
            return []
    
    def _fetch_chunk_with_retry(self, contracts: List[ContractInterface], from_block: int, 
                               to_block: int) -> List[Dict[str, Any]]:
        """Fetch events for a chunk with retry logic"""
        chunk_events = []
        
        for contract in contracts:
            event_types = contract.get_event_types()
            
            for event_name in event_types:
                for attempt in range(self.max_retries):
                    try:
                        events = contract.get_historical_events(
                            event_name, from_block, to_block
                        )
                        # Add contract info to events
                        for event in events:
                            # Convert AttributeDict to regular dict to allow modification
                            event_dict = dict(event)
                            event_dict['contract_name'] = contract.contract_name
                            event_dict['contract_address'] = contract.contract_address
                            chunk_events.append(event_dict)
                        break  # Success, exit retry loop
                        
                    except Exception as e:
                        logger.warning(
                            f"Attempt {attempt + 1}/{self.max_retries} failed for {contract.contract_name}.{event_name} "
                            f"events (blocks {from_block}-{to_block}): {e}"
                        )
                        
                        if attempt < self.max_retries - 1:
                            # Wait before retrying (exponential backoff)
                            wait_time = 2 ** attempt
                            logger.info(f"Retrying in {wait_time} seconds...")
                            import time
                            time.sleep(wait_time)
                        else:
                            logger.error(f"Max retries exceeded for {contract.contract_name}.{event_name}")
        
        return chunk_events
    
    async def get_historical_events_async(self, from_block: int = 0, to_block: str = 'latest', 
                                        max_events: int = 100, contract_filter: str = None) -> List[Dict[str, Any]]:
        """Async version of get_historical_events for better performance"""
        import concurrent.futures
        
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(
                executor, 
                self.get_historical_events, 
                from_block, to_block, max_events, contract_filter
            ) 