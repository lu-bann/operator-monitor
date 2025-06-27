"""
Delegation message parser for Helix relay Redis data.

This module provides high-level functions to query and parse delegation
messages from Redis, returning structured results.
"""

import logging
from typing import List, Dict, Any, Optional
from redis_client import HelixRedisClient
from models import (
    SignedDelegation, DelegationQueryResult, 
    parse_delegation_json, create_delegation_result
)

logger = logging.getLogger(__name__)


class DelegationParser:
    """High-level delegation message parser."""
    
    def __init__(self, redis_client: HelixRedisClient):
        """
        Initialize delegation parser.
        
        Args:
            redis_client: Connected Redis client instance
        """
        self.redis_client = redis_client
    
    def get_validator_delegation_status(self, validator_pubkey: str) -> DelegationQueryResult:
        """
        Get complete delegation status for a validator.
        
        Args:
            validator_pubkey: Validator public key (with or without 0x prefix)
            
        Returns:
            DelegationQueryResult with parsed delegation data
            
        Raises:
            ConnectionError: If Redis connection fails
            ValueError: If delegation data is malformed
        """
        logger.info(f"Querying delegation status for validator: {validator_pubkey}")
        
        # Query raw delegation data from Redis
        raw_delegations = self.redis_client.get_validator_delegations(validator_pubkey)
        
        if not raw_delegations:
            logger.debug(f"No delegations found for validator {validator_pubkey}")
            return create_delegation_result(validator_pubkey, [])
        
        # Parse and validate delegation messages
        try:
            delegations = parse_delegation_json(raw_delegations)
            logger.info(f"Successfully parsed {len(delegations)} delegations for validator {validator_pubkey}")
            
            # Create result with computed fields
            result = create_delegation_result(validator_pubkey, delegations)
            
            logger.info(f"Validator {validator_pubkey}: {result.total_delegations} total delegations, {result.active_delegation_count} active")
            return result
            
        except ValueError as e:
            logger.error(f"Failed to parse delegations for validator {validator_pubkey}: {e}")
            raise
    
    def check_delegation_relationship(self, validator_pubkey: str, delegatee_pubkey: str) -> bool:
        """
        Check if a specific delegation relationship exists.
        
        Args:
            validator_pubkey: Validator public key
            delegatee_pubkey: Delegatee public key
            
        Returns:
            True if validator is currently delegated to delegatee
        """
        try:
            result = self.get_validator_delegation_status(validator_pubkey)
            return result.is_delegated_to(delegatee_pubkey)
        except Exception as e:
            logger.error(f"Error checking delegation relationship: {e}")
            return False
    
    def get_all_validator_delegations(self) -> Dict[str, DelegationQueryResult]:
        """
        Get delegation status for all validators in Redis.
        
        Returns:
            Dictionary mapping validator pubkeys to their delegation results
        """
        logger.info("Querying all validator delegations from Redis")
        
        all_delegations = self.redis_client.get_all_delegations()
        results = {}
        
        for validator_pubkey, raw_delegations in all_delegations.items():
            try:
                delegations = parse_delegation_json(raw_delegations)
                result = create_delegation_result(validator_pubkey, delegations)
                results[validator_pubkey] = result
                
            except Exception as e:
                logger.warning(f"Failed to parse delegations for validator {validator_pubkey}: {e}")
                # Create empty result for failed parsing
                results[validator_pubkey] = create_delegation_result(validator_pubkey, [])
        
        logger.info(f"Successfully parsed delegations for {len(results)} validators")
        return results
    
    def get_validators_with_delegations(self) -> List[str]:
        """
        Get list of validator pubkeys that have delegation data.
        
        Returns:
            List of validator public keys with delegation data
        """
        try:
            delegation_keys = self.redis_client.list_delegation_keys()
            # Extract validator pubkeys from Redis keys
            validators = [key.replace("delegations:", "") for key in delegation_keys]
            logger.info(f"Found {len(validators)} validators with delegation data")
            return validators
        except Exception as e:
            logger.error(f"Error listing validators with delegations: {e}")
            return []
    
    def get_delegation_summary(self, validator_pubkey: str) -> Dict[str, Any]:
        """
        Get human-readable delegation summary for a validator.
        
        Args:
            validator_pubkey: Validator public key
            
        Returns:
            Dictionary with delegation summary information
        """
        try:
            result = self.get_validator_delegation_status(validator_pubkey)
            
            summary = {
                "validator_pubkey": f"0x{result.validator_pubkey}",
                "has_delegations": result.has_delegations,
                "total_delegations": result.total_delegations,
                "active_delegations": result.active_delegation_count,
                "active_delegatees": [f"0x{pubkey}" for pubkey in result.active_delegatees],
                "delegation_details": []
            }
            
            # Add detailed delegation information
            for delegation in result.delegations:
                detail = {
                    "action": delegation.message.action_name,
                    "delegatee": f"0x{delegation.delegatee_pubkey}",
                    "signature": f"0x{delegation.signature[:16]}..."  # Truncated signature
                }
                summary["delegation_details"].append(detail)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating delegation summary: {e}")
            return {
                "validator_pubkey": validator_pubkey,
                "error": str(e),
                "has_delegations": False,
                "total_delegations": 0,
                "active_delegations": 0,
                "active_delegatees": [],
                "delegation_details": []
            }
    
    def validate_delegation_data_integrity(self) -> Dict[str, Any]:
        """
        Validate integrity of all delegation data in Redis.
        
        Returns:
            Dictionary with validation results and statistics
        """
        logger.info("Validating delegation data integrity")
        
        stats = {
            "total_validators": 0,
            "valid_delegations": 0,
            "invalid_delegations": 0,
            "parsing_errors": [],
            "validation_summary": {}
        }
        
        try:
            all_delegations = self.redis_client.get_all_delegations()
            stats["total_validators"] = len(all_delegations)
            
            for validator_pubkey, raw_delegations in all_delegations.items():
                try:
                    delegations = parse_delegation_json(raw_delegations)
                    stats["valid_delegations"] += len(delegations)
                    
                    # Track validation stats per validator
                    stats["validation_summary"][validator_pubkey] = {
                        "status": "valid",
                        "delegation_count": len(delegations)
                    }
                    
                except Exception as e:
                    stats["invalid_delegations"] += len(raw_delegations) if isinstance(raw_delegations, list) else 1
                    error_info = {
                        "validator_pubkey": validator_pubkey,
                        "error": str(e),
                        "raw_data_preview": str(raw_delegations)[:200] + "..." if len(str(raw_delegations)) > 200 else str(raw_delegations)
                    }
                    stats["parsing_errors"].append(error_info)
                    
                    stats["validation_summary"][validator_pubkey] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            logger.info(f"Validation complete: {stats['valid_delegations']} valid, {stats['invalid_delegations']} invalid delegations")
            
        except Exception as e:
            logger.error(f"Error during data integrity validation: {e}")
            stats["global_error"] = str(e)
        
        return stats


def create_delegation_parser(redis_url: str, timeout: int = 5) -> DelegationParser:
    """
    Factory function to create delegation parser with connected Redis client.
    
    Args:
        redis_url: Redis connection URL
        timeout: Connection timeout in seconds
        
    Returns:
        DelegationParser instance with connected Redis client
        
    Raises:
        ConnectionError: If Redis connection fails
    """
    from redis_client import create_redis_client
    
    redis_client = create_redis_client(redis_url, timeout)
    return DelegationParser(redis_client)