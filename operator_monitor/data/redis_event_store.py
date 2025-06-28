"""Redis-based event storage for validator-operator mapping"""

import json
import logging
from typing import List, Dict, Any, Optional
import redis
from redis.exceptions import ConnectionError, TimeoutError

from .event_store import EventStoreInterface

logger = logging.getLogger(__name__)


class RedisValidatorStore:
    """Redis storage for mapping operators to their validator public keys"""
    
    def __init__(self, redis_url: str, key_prefix: str = "validators_by_operator", timeout: int = 5):
        """
        Initialize Redis validator store
        
        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379)
            key_prefix: Prefix for Redis keys storing validator mappings
            timeout: Connection timeout in seconds
        """
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.timeout = timeout
        self._client = None
        
        logger.info(f"Redis validator store initialized with prefix: {key_prefix}")
    
    def connect(self) -> bool:
        """
        Establish Redis connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self._client = redis.from_url(
                self.redis_url,
                socket_timeout=self.timeout,
                socket_connect_timeout=self.timeout,
                decode_responses=True
            )
            # Test connection
            self._client.ping()
            logger.info(f"Successfully connected to Redis at {self.redis_url}")
            return True
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return False
    
    def disconnect(self):
        """Close Redis connection"""
        if self._client:
            self._client.close()
            logger.info("Redis connection closed")
    
    def store_operator_validators(self, operator_address: str, validator_pubkeys: List[str]) -> bool:
        """
        Store validator public keys for an operator
        
        Args:
            operator_address: Ethereum address of the operator (with 0x prefix)
            validator_pubkeys: List of validator public key hex strings
            
        Returns:
            True if stored successfully, False otherwise
        """
        if not self._client:
            logger.error("Redis client not connected. Call connect() first.")
            return False
        
        try:
            # Normalize operator address to lowercase
            operator_key = f"{self.key_prefix}:{operator_address.lower()}"
            
            # Get existing validator keys for this operator
            existing_data = self._client.get(operator_key)
            existing_validators = []
            
            if existing_data:
                try:
                    existing_validators = json.loads(existing_data)
                    if not isinstance(existing_validators, list):
                        existing_validators = []
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON data for operator {operator_address}, resetting")
                    existing_validators = []
            
            # Merge with new validators (avoid duplicates)
            updated_validators = list(set(existing_validators + validator_pubkeys))
            
            # Store updated list
            self._client.set(operator_key, json.dumps(updated_validators))
            
            logger.info(f"Stored {len(validator_pubkeys)} validators for operator {operator_address} "
                       f"(total: {len(updated_validators)})")
            return True
            
        except Exception as e:
            logger.error(f"Error storing validators for operator {operator_address}: {e}")
            return False
    
    def get_operator_validators(self, operator_address: str) -> List[str]:
        """
        Get validator public keys for an operator
        
        Args:
            operator_address: Ethereum address of the operator
            
        Returns:
            List of validator public key hex strings, empty list if none found
        """
        if not self._client:
            logger.error("Redis client not connected. Call connect() first.")
            return []
        
        try:
            operator_key = f"{self.key_prefix}:{operator_address.lower()}"
            data = self._client.get(operator_key)
            
            if not data:
                return []
            
            validators = json.loads(data)
            if not isinstance(validators, list):
                logger.warning(f"Invalid data format for operator {operator_address}")
                return []
            
            return validators
            
        except Exception as e:
            logger.error(f"Error getting validators for operator {operator_address}: {e}")
            return []
    
    def get_all_operators(self) -> Dict[str, List[str]]:
        """
        Get all operator-validator mappings
        
        Returns:
            Dictionary mapping operator addresses to their validator lists
        """
        if not self._client:
            logger.error("Redis client not connected. Call connect() first.")
            return {}
        
        try:
            pattern = f"{self.key_prefix}:*"
            keys = self._client.keys(pattern)
            
            all_operators = {}
            for key in keys:
                # Extract operator address from key
                operator_address = key.replace(f"{self.key_prefix}:", "")
                validators = self.get_operator_validators(operator_address)
                if validators:
                    all_operators[operator_address] = validators
            
            logger.info(f"Retrieved {len(all_operators)} operators from Redis")
            return all_operators
            
        except Exception as e:
            logger.error(f"Error getting all operators: {e}")
            return {}
    
    def remove_operator(self, operator_address: str) -> bool:
        """
        Remove all validator mappings for an operator
        
        Args:
            operator_address: Ethereum address of the operator
            
        Returns:
            True if removed successfully, False otherwise
        """
        if not self._client:
            logger.error("Redis client not connected. Call connect() first.")
            return False
        
        try:
            operator_key = f"{self.key_prefix}:{operator_address.lower()}"
            result = self._client.delete(operator_key)
            
            if result:
                logger.info(f"Removed operator {operator_address} from Redis")
                return True
            else:
                logger.info(f"Operator {operator_address} not found in Redis")
                return False
                
        except Exception as e:
            logger.error(f"Error removing operator {operator_address}: {e}")
            return False


class RedisEventStore(EventStoreInterface):
    """Redis-based event store with validator-operator tracking capability"""
    
    def __init__(self, redis_url: str, key_prefix: str = "validators_by_operator", 
                 event_prefix: str = "events", timeout: int = 5):
        """
        Initialize Redis event store
        
        Args:
            redis_url: Redis connection URL
            key_prefix: Prefix for validator mapping keys
            event_prefix: Prefix for event storage keys
            timeout: Connection timeout in seconds
        """
        self.validator_store = RedisValidatorStore(redis_url, key_prefix, timeout)
        self.event_prefix = event_prefix
        self.redis_url = redis_url
        self.timeout = timeout
        self._client = None
        
        logger.info("Redis event store initialized")
    
    def connect(self) -> bool:
        """Connect to Redis"""
        return self.validator_store.connect()
    
    def disconnect(self):
        """Disconnect from Redis"""
        self.validator_store.disconnect()
    
    def store_event(self, event: Dict[str, Any]) -> bool:
        """Store a single event (basic implementation)"""
        # For now, we focus on validator mapping, but could extend to store events
        return True
    
    def store_events(self, events: List[Dict[str, Any]]) -> int:
        """Store multiple events (basic implementation)"""
        return len(events)
    
    def get_events(self, from_block: int = 0, to_block: Optional[int] = None, 
                  event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve stored events (basic implementation)"""
        return []
    
    def get_latest_block(self) -> Optional[int]:
        """Get latest block number (basic implementation)"""
        return None
    
    def store_operator_validators(self, operator_address: str, validator_pubkeys: List[str]) -> bool:
        """Store validator public keys for an operator"""
        return self.validator_store.store_operator_validators(operator_address, validator_pubkeys)
    
    def get_operator_validators(self, operator_address: str) -> List[str]:
        """Get validator public keys for an operator"""
        return self.validator_store.get_operator_validators(operator_address)
    
    def get_all_operators(self) -> Dict[str, List[str]]:
        """Get all operator-validator mappings"""
        return self.validator_store.get_all_operators()