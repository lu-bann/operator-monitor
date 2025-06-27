"""Web3 connection management"""

import logging
from web3 import Web3
from typing import Optional

from ..config import NETWORK_CONFIGS

logger = logging.getLogger(__name__)


class Web3Client:
    """Manages Web3 connection and network validation"""
    
    def __init__(self, rpc_url: str, network: str = 'mainnet'):
        """
        Initialize Web3 client with connection and network validation
        
        Args:
            rpc_url: The RPC URL of the Ethereum node
            network: The network name (mainnet, holesky, etc.)
        """
        self.network = network.lower()
        self.network_config = NETWORK_CONFIGS.get(self.network, NETWORK_CONFIGS['mainnet'])
        self.rpc_url = rpc_url
        
        # Initialize Web3 connection
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Validate connection
        self._validate_connection()
        self._verify_network()
        
        logger.info(f"Connected to Ethereum node: {rpc_url}")
        logger.info(f"Network: {self.network_config['name']} (Chain ID: {self.network_config['chain_id']})")
    
    def _validate_connection(self):
        """Validate Web3 connection"""
        if not self.web3.is_connected():
            raise ConnectionError("Failed to connect to Ethereum node")
    
    def _verify_network(self):
        """Verify we're connected to the correct network"""
        try:
            chain_id = self.web3.eth.chain_id
            expected_chain_id = self.network_config['chain_id']
            if chain_id != expected_chain_id:
                logger.warning(
                    f"Chain ID mismatch: expected {expected_chain_id} for {self.network}, got {chain_id}"
                )
        except Exception as e:
            logger.warning(f"Could not verify chain ID: {e}")
    
    def is_connected(self) -> bool:
        """Check if Web3 connection is active"""
        return self.web3.is_connected()
    
    def get_current_block(self) -> int:
        """Get current block number"""
        return self.web3.eth.block_number
    
    def health_check(self) -> dict:
        """Perform connection health check"""
        try:
            current_block = self.get_current_block()
            chain_id = self.web3.eth.chain_id
            
            return {
                'connected': True,
                'current_block': current_block,
                'chain_id': chain_id,
                'network': self.network,
                'rpc_url': self.rpc_url
            }
        except Exception as e:
            return {
                'connected': False,
                'error': str(e),
                'network': self.network,
                'rpc_url': self.rpc_url
            } 