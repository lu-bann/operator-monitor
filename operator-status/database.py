"""
PostgreSQL database connection module for Helix relay validator data.

This module provides access to the Helix relay PostgreSQL database to query
validator registration, preferences, trusted proposers, and builder information.
"""

import logging
import psycopg2

logger = logging.getLogger(__name__)


class HelixPostgreSQLClient:
    """PostgreSQL client for Helix relay database queries."""
    
    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        """
        Initialize PostgreSQL client.
        
        Args:
            host: PostgreSQL hostname
            port: PostgreSQL port
            database: Database name
            user: Database user
            password: Database password
        """
        self.connection_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }
        self._connection = None
        
    def connect(self) -> bool:
        """
        Establish database connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self._connection = psycopg2.connect(**self.connection_params)
            logger.info(f"Successfully connected to PostgreSQL at {self.connection_params['host']}:{self.connection_params['port']}")
            return True
        except psycopg2.Error as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            logger.info("PostgreSQL connection closed")
    
    def _pubkey_to_bytes(self, pubkey: str) -> bytes:
        """
        Convert hex public key to bytes for PostgreSQL queries.
        
        Args:
            pubkey: Public key in hex format (with 0x prefix)
            
        Returns:
            Public key as bytes
        """
        if pubkey.startswith('0x'):
            pubkey = pubkey[2:]
        return bytes.fromhex(pubkey)
    
    def _bytes_to_pubkey(self, pubkey_bytes: bytes) -> str:
        """
        Convert bytes public key to hex string with 0x prefix.
        
        Args:
            pubkey_bytes: Public key as bytes
            
        Returns:
            Public key as hex string with 0x prefix
        """
        return f"0x{pubkey_bytes.hex()}"
    
    def is_validator_registered(self, validator_pubkey: str) -> bool:
        """
        Check if validator is registered.
        
        Args:
            validator_pubkey: Validator public key (hex with 0x prefix)
            
        Returns:
            True if validator is registered, False otherwise
        """
        if not self._connection:
            raise ConnectionError("Database not connected. Call connect() first.")
        
        pubkey_bytes = self._pubkey_to_bytes(validator_pubkey)
        
        try:
            with self._connection.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM validator_registrations WHERE public_key = %s",
                    (pubkey_bytes,)
                )
                return cursor.fetchone() is not None
                
        except psycopg2.Error as e:
            logger.error(f"Error checking validator registration: {e}")
            raise
    
    
    
    
    
    
    


def create_postgres_client(host: str, port: int, database: str, user: str, password: str) -> HelixPostgreSQLClient:
    """
    Factory function to create and connect PostgreSQL client.
    
    Args:
        host: PostgreSQL hostname
        port: PostgreSQL port
        database: Database name
        user: Database user
        password: Database password
        
    Returns:
        Connected HelixPostgreSQLClient instance
        
    Raises:
        ConnectionError: If connection fails
    """
    client = HelixPostgreSQLClient(host, port, database, user, password)
    if not client.connect():
        raise ConnectionError(f"Failed to connect to PostgreSQL at {host}:{port}")
    return client