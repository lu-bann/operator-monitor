"""
Service layer for Helix validator delegation operations.

This module extracts the business logic from CLI commands to provide
reusable services for both CLI and HTTP interfaces.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from pydantic import ValidationError

from redis_client import create_redis_client, HelixRedisClient
from delegation_parser import create_delegation_parser, DelegationParser
from database import create_postgres_client, HelixPostgreSQLClient
from validator_info import create_validator_info_service, ValidatorInfoService
from models import DelegationQueryResult, ValidatorInfo

# Import RedisValidatorStore from operator_monitor
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from operator_monitor.data.redis_event_store import RedisValidatorStore

logger = logging.getLogger(__name__)


class ValidatorDelegationService:
    """Service for validator delegation operations."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", timeout: int = 5):
        """Initialize the service with Redis connection parameters."""
        self.redis_url = redis_url
        self.timeout = timeout
        self._parser: Optional[DelegationParser] = None
    
    def _get_parser(self) -> DelegationParser:
        """Get or create delegation parser with Redis connection."""
        if self._parser is None:
            self._parser = create_delegation_parser(self.redis_url, self.timeout)
        return self._parser
    
    def validate_pubkey(self, pubkey: str) -> str:
        """Validate validator public key format."""
        if not pubkey:
            raise ValueError("Public key cannot be empty")
        
        # Require 0x prefix
        if not pubkey.startswith('0x'):
            raise ValueError("Validator public key must start with '0x'")
        
        hex_part = pubkey[2:]
        
        # Check hex format and length
        if not all(c in '0123456789abcdefABCDEF' for c in hex_part):
            raise ValueError(f"Invalid hex format: {pubkey}")
        
        if len(hex_part) != 96:  # 48 bytes = 96 hex characters
            raise ValueError(f"Invalid pubkey length: {len(hex_part)}. Expected 96 hex chars (48 bytes)")
        
        return pubkey
    
    def get_validator_delegation_status(self, validator_key: str) -> DelegationQueryResult:
        """
        Get delegation status for a single validator.
        
        Args:
            validator_key: Validator public key (hex, with or without 0x prefix)
            
        Returns:
            DelegationQueryResult with delegation information
            
        Raises:
            ValueError: If validator key is invalid
            Exception: If Redis connection or query fails
        """
        # Validate public key
        normalized_pubkey = self.validate_pubkey(validator_key)
        
        # Get delegation status
        parser = self._get_parser()
        result = parser.get_validator_delegation_status(normalized_pubkey)
        
        return result
    
    def check_validators_batch(self, validator_keys: List[str]) -> Dict[str, Any]:
        """
        Check delegation status for multiple validators.
        
        Args:
            validator_keys: List of validator public keys
            
        Returns:
            Dictionary with summary and results for each validator
            
        Raises:
            ValueError: If any validator key is invalid
            Exception: If Redis connection or query fails
        """
        # Validate all keys first
        validated_keys = []
        for key in validator_keys:
            try:
                normalized = self.validate_pubkey(key)
                validated_keys.append(normalized)
            except ValueError as e:
                logger.warning(f"Skipping invalid validator key {key}: {e}")
        
        if not validated_keys:
            raise ValueError("No valid validator keys provided")
        
        parser = self._get_parser()
        results = []
        
        for validator_key in validated_keys:
            try:
                result = parser.get_validator_delegation_status(validator_key)
                results.append(result)
            except Exception as e:
                logger.error(f"Error querying validator {validator_key}: {e}")
                # Continue with other validators
                continue
        
        # Calculate summary
        total_with_delegations = sum(1 for r in results if r.has_delegations)
        total_active_delegations = sum(r.active_delegation_count for r in results)
        
        return {
            "summary": {
                "total_validators": len(results),
                "validators_with_delegations": total_with_delegations,
                "total_active_delegations": total_active_delegations
            },
            "results": results
        }
    
    def list_validators_with_delegations(self) -> List[str]:
        """
        List all validators with delegation data in Redis.
        
        Returns:
            List of validator public keys that have delegation data
            
        Raises:
            Exception: If Redis connection or query fails
        """
        parser = self._get_parser()
        validators = parser.get_validators_with_delegations()
        return validators


class ValidatorRegistrationService:
    """Service for validator registration information from PostgreSQL."""
    
    def __init__(self, 
                 postgres_host: str = "localhost",
                 postgres_port: int = 5432,
                 postgres_db: str = "helix_mev_relayer",
                 postgres_user: str = "postgres",
                 postgres_password: str = "postgres"):
        """Initialize the service with PostgreSQL connection parameters."""
        self.postgres_host = postgres_host
        self.postgres_port = postgres_port
        self.postgres_db = postgres_db
        self.postgres_user = postgres_user
        self.postgres_password = postgres_password
        self._client: Optional[HelixPostgreSQLClient] = None
        self._service: Optional[ValidatorInfoService] = None
    
    def _get_service(self) -> ValidatorInfoService:
        """Get or create validator info service with PostgreSQL connection."""
        if self._service is None:
            self._client = create_postgres_client(
                self.postgres_host, 
                self.postgres_port, 
                self.postgres_db, 
                self.postgres_user, 
                self.postgres_password
            )
            self._service = create_validator_info_service(self._client)
        return self._service
    
    def validate_pubkey(self, pubkey: str) -> str:
        """Validate validator public key format."""
        if not pubkey:
            raise ValueError("Public key cannot be empty")
        
        # Require 0x prefix
        if not pubkey.startswith('0x'):
            raise ValueError("Validator public key must start with '0x'")
        
        hex_part = pubkey[2:]
        
        # Check hex format and length
        if not all(c in '0123456789abcdefABCDEF' for c in hex_part):
            raise ValueError(f"Invalid hex format: {pubkey}")
        
        if len(hex_part) != 96:  # 48 bytes = 96 hex characters
            raise ValueError(f"Invalid pubkey length: {len(hex_part)}. Expected 96 hex chars (48 bytes)")
        
        return pubkey
    
    def get_validator_info(self, validator_key: str) -> ValidatorInfo:
        """
        Get validator registration information from PostgreSQL.
        
        Args:
            validator_key: Validator public key (hex with 0x prefix)
            
        Returns:
            ValidatorInfo with registration status
            
        Raises:
            ValueError: If validator key is invalid
            Exception: If database connection or query fails
        """
        # Validate public key
        normalized_pubkey = self.validate_pubkey(validator_key)
        
        # Get validator info
        service = self._get_service()
        info = service.get_validator_info(normalized_pubkey)
        
        return info
    
    def disconnect(self):
        """Close database connections."""
        if self._client:
            self._client.disconnect()
            self._client = None
            self._service = None


class OperatorValidatorService:
    """Service for querying operator-validator mappings from Redis."""
    
    def __init__(self, 
                 redis_url: str = "redis://localhost:6379",
                 timeout: int = 5,
                 key_prefix: str = "validators_by_operator"):
        """Initialize the service with Redis connection parameters."""
        self.redis_url = redis_url
        self.timeout = timeout
        self.key_prefix = key_prefix
        self._store: Optional[RedisValidatorStore] = None
    
    def _get_store(self) -> RedisValidatorStore:
        """Get or create Redis validator store."""
        if self._store is None:
            self._store = RedisValidatorStore(
                redis_url=self.redis_url,
                key_prefix=self.key_prefix,
                timeout=self.timeout
            )
            if not self._store.connect():
                raise ConnectionError(f"Failed to connect to Redis at {self.redis_url}")
        return self._store
    
    def validate_operator_address(self, operator_address: str) -> str:
        """Validate operator Ethereum address format."""
        if not operator_address:
            raise ValueError("Operator address cannot be empty")
        
        # Require 0x prefix
        if not operator_address.startswith('0x'):
            raise ValueError("Operator address must start with '0x'")
        
        hex_part = operator_address[2:]
        
        # Check hex format and length
        if not all(c in '0123456789abcdefABCDEF' for c in hex_part):
            raise ValueError(f"Invalid hex format: {operator_address}")
        
        if len(hex_part) != 40:  # 20 bytes = 40 hex characters
            raise ValueError(f"Invalid operator address length: {len(hex_part)}. Expected 40 hex chars (20 bytes)")
        
        return operator_address
    
    def get_operator_validators(self, operator_address: str) -> List[str]:
        """
        Get validator public keys for an operator.
        
        Args:
            operator_address: Operator Ethereum address (hex with 0x prefix)
            
        Returns:
            List of validator public key hex strings
            
        Raises:
            ValueError: If operator address is invalid
            ConnectionError: If Redis connection fails
            Exception: If Redis query fails
        """
        # Validate operator address
        normalized_address = self.validate_operator_address(operator_address)
        
        # Get validators from Redis
        store = self._get_store()
        validators = store.get_operator_validators(normalized_address)
        
        return validators
    
    def disconnect(self):
        """Close Redis connections."""
        if self._store:
            self._store.disconnect()
            self._store = None


# Service factory functions for dependency injection

def create_validator_delegation_service(redis_url: str = "redis://localhost:6379", 
                                       timeout: int = 5) -> ValidatorDelegationService:
    """Create a validator delegation service instance."""
    return ValidatorDelegationService(redis_url=redis_url, timeout=timeout)


def create_validator_info_service_instance(postgres_host: str = "localhost",
                                         postgres_port: int = 5432,
                                         postgres_db: str = "helix_mev_relayer",
                                         postgres_user: str = "postgres",
                                         postgres_password: str = "postgres") -> ValidatorRegistrationService:
    """Create a validator info service instance."""
    return ValidatorRegistrationService(
        postgres_host=postgres_host,
        postgres_port=postgres_port,
        postgres_db=postgres_db,
        postgres_user=postgres_user,
        postgres_password=postgres_password
    )


def create_operator_service_instance(redis_url: str = "redis://localhost:6379",
                                   timeout: int = 5,
                                   key_prefix: str = "validators_by_operator") -> OperatorValidatorService:
    """Create an operator validator service instance."""
    return OperatorValidatorService(
        redis_url=redis_url,
        timeout=timeout,
        key_prefix=key_prefix
    )