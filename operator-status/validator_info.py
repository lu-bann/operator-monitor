"""
Validator information query module for PostgreSQL data.

This module provides high-level functions to query and combine validator
information from the PostgreSQL database.
"""

import logging
from typing import Dict, Any
from database import HelixPostgreSQLClient
from models import ValidatorInfo

logger = logging.getLogger(__name__)


class ValidatorInfoService:
    """High-level service for validator information queries."""
    
    def __init__(self, postgres_client: HelixPostgreSQLClient):
        """
        Initialize validator info service.
        
        Args:
            postgres_client: Connected PostgreSQL client instance
        """
        self.postgres_client = postgres_client
    
    def get_validator_info(self, validator_pubkey: str) -> ValidatorInfo:
        """
        Get validator registration status.
        
        Args:
            validator_pubkey: Validator public key (hex with 0x prefix)
            
        Returns:
            ValidatorInfo with registration status
        """
        logger.info(f"Checking validator registration for: {validator_pubkey}")
        
        is_registered = self.postgres_client.is_validator_registered(validator_pubkey)
        
        return ValidatorInfo(
            validator_pubkey=validator_pubkey,
            is_registered=is_registered
        )
    


def create_validator_info_service(postgres_client: HelixPostgreSQLClient) -> ValidatorInfoService:
    """
    Factory function to create validator info service.
    
    Args:
        postgres_client: Connected PostgreSQL client
        
    Returns:
        ValidatorInfoService instance
    """
    return ValidatorInfoService(postgres_client)