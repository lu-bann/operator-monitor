"""
Redis client module for querying Helix relay delegation messages.

This module provides direct Redis access to query delegation data stored
in the Helix MEV relay using the key pattern: delegations:{validator_pubkey}
"""

import json
import logging
from typing import List, Optional, Dict, Any
import redis
from redis.exceptions import ConnectionError, TimeoutError

logger = logging.getLogger(__name__)


class HelixRedisClient:
    """Redis client for Helix relay delegation queries."""
    
    def __init__(self, redis_url: str, timeout: int = 5):
        """
        Initialize Redis client.
        
        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379)
            timeout: Connection timeout in seconds
        """
        self.redis_url = redis_url
        self.timeout = timeout
        self._client = None
        
    def connect(self) -> bool:
        """
        Establish Redis connection.
        
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
        """Close Redis connection."""
        if self._client:
            self._client.close()
            logger.info("Redis connection closed")
    
    def get_validator_delegations(self, validator_pubkey: str) -> List[Dict[str, Any]]:
        """
        Get delegation messages for a specific validator.
        
        Args:
            validator_pubkey: Validator public key (hex string with 0x prefix required)
            
        Returns:
            List of delegation message dictionaries, empty list if none found
            
        Raises:
            ConnectionError: If Redis connection is not established
            ValueError: If delegation data is malformed
        """
        if not self._client:
            raise ConnectionError("Redis client not connected. Call connect() first.")
        
        # Validator pubkey should already have 0x prefix (validated in CLI)
        # Construct Redis key following Helix pattern
        key = f"delegations:{validator_pubkey}"
        
        try:
            # Query Redis for delegation data
            delegation_data = self._client.get(key)
            
            if not delegation_data:
                logger.debug(f"No delegations found for validator {validator_pubkey}")
                return []
            
            # Parse JSON delegation array
            delegations = json.loads(delegation_data)
            
            if not isinstance(delegations, list):
                raise ValueError(f"Invalid delegation data format: expected list, got {type(delegations)}")
            
            logger.info(f"Found {len(delegations)} delegations for validator {validator_pubkey}")
            return delegations
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse delegation JSON for {validator_pubkey}: {e}")
            raise ValueError(f"Malformed delegation data in Redis: {e}")
        except Exception as e:
            logger.error(f"Error querying delegations for {validator_pubkey}: {e}")
            raise
    
    def list_delegation_keys(self, pattern: str = "delegations:*") -> List[str]:
        """
        List all delegation keys matching the pattern.
        
        Args:
            pattern: Redis key pattern to match
            
        Returns:
            List of matching Redis keys
        """
        if not self._client:
            raise ConnectionError("Redis client not connected. Call connect() first.")
        
        try:
            keys = self._client.keys(pattern)
            logger.info(f"Found {len(keys)} delegation keys matching pattern: {pattern}")
            return keys
        except Exception as e:
            logger.error(f"Error listing delegation keys: {e}")
            raise
    
    def get_all_delegations(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all delegation data from Redis.
        
        Returns:
            Dictionary mapping validator pubkeys to their delegation lists
        """
        delegation_keys = self.list_delegation_keys()
        all_delegations = {}
        
        for key in delegation_keys:
            # Extract validator pubkey from key (remove "delegations:" prefix)
            validator_pubkey = key.replace("delegations:", "")
            try:
                delegations = self.get_validator_delegations(validator_pubkey)
                if delegations:
                    all_delegations[validator_pubkey] = delegations
            except Exception as e:
                logger.warning(f"Failed to get delegations for key {key}: {e}")
                continue
        
        return all_delegations


def create_redis_client(redis_url: str, timeout: int = 5) -> HelixRedisClient:
    """
    Factory function to create and connect Redis client.
    
    Args:
        redis_url: Redis connection URL
        timeout: Connection timeout in seconds
        
    Returns:
        Connected HelixRedisClient instance
        
    Raises:
        ConnectionError: If connection fails
    """
    client = HelixRedisClient(redis_url, timeout)
    if not client.connect():
        raise ConnectionError(f"Failed to connect to Redis at {redis_url}")
    return client