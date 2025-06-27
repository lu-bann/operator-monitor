"""Web3 connection management"""

import logging
from web3 import Web3
from typing import Optional, Dict, Any

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
    
    def get_transaction_by_hash(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get transaction details by transaction hash
        
        Args:
            tx_hash: Transaction hash as hex string
            
        Returns:
            Transaction data dictionary or None if not found
        """
        try:
            tx = self.web3.eth.get_transaction(tx_hash)
            # Convert HexBytes to hex strings for JSON serialization
            return {
                'hash': tx.hash.hex(),
                'blockNumber': tx.blockNumber,
                'blockHash': tx.blockHash.hex() if tx.blockHash else None,
                'transactionIndex': tx.transactionIndex,
                'from': tx['from'],
                'to': tx.to,
                'value': tx.value,
                'gas': tx.gas,
                'gasPrice': tx.gasPrice,
                'input': tx.input.hex(),
                'nonce': tx.nonce,
                'type': tx.get('type'),
                'chainId': tx.get('chainId')
            }
        except Exception as e:
            logger.error(f"Error fetching transaction {tx_hash}: {e}")
            return None
    
    def get_transaction_receipt(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get transaction receipt by transaction hash
        
        Args:
            tx_hash: Transaction hash as hex string
            
        Returns:
            Transaction receipt dictionary or None if not found
        """
        try:
            receipt = self.web3.eth.get_transaction_receipt(tx_hash)
            return {
                'transactionHash': receipt.transactionHash.hex(),
                'blockNumber': receipt.blockNumber,
                'blockHash': receipt.blockHash.hex(),
                'transactionIndex': receipt.transactionIndex,
                'from': receipt['from'],
                'to': receipt.to,
                'gasUsed': receipt.gasUsed,
                'cumulativeGasUsed': receipt.cumulativeGasUsed,
                'status': receipt.status,
                'logs': [
                    {
                        'address': log.address,
                        'topics': [topic.hex() for topic in log.topics],
                        'data': log.data.hex()
                    }
                    for log in receipt.logs
                ]
            }
        except Exception as e:
            logger.error(f"Error fetching transaction receipt {tx_hash}: {e}")
            return None
    
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