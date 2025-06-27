"""
Configuration module for Helix delegation checker.

Handles loading configuration from various sources:
- Command line arguments (primary)
- Environment variables
- Configuration files (for future PostgreSQL extension)
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path
import yaml
from pydantic import BaseModel, Field


class RedisConfig(BaseModel):
    """Redis connection configuration."""
    url: str = Field(default="redis://localhost:6379", description="Redis connection URL")
    timeout: int = Field(default=5, description="Connection timeout in seconds")
    max_connections: int = Field(default=10, description="Maximum connection pool size")


class PostgreSQLConfig(BaseModel):
    """PostgreSQL connection configuration (for future extension)."""
    hostname: str = Field(default="localhost", description="PostgreSQL hostname")
    port: int = Field(default=5432, description="PostgreSQL port")
    db_name: str = Field(default="helix_mev_relayer", description="Database name")
    user: str = Field(default="postgres", description="Database user")
    password: str = Field(default="postgres", description="Database password")
    region: int = Field(default=0, description="Database region")


class AppConfig(BaseModel):
    """Application configuration."""
    redis: RedisConfig = Field(default_factory=RedisConfig)
    postgresql: PostgreSQLConfig = Field(default_factory=PostgreSQLConfig)
    log_level: str = Field(default="INFO", description="Logging level")
    output_format: str = Field(default="table", description="Default output format")


def load_config_from_file(config_path: str) -> Optional[Dict[str, Any]]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary or None if file doesn't exist
    """
    path = Path(config_path)
    if not path.exists():
        return None
    
    try:
        with path.open() as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise ValueError(f"Failed to load config file {config_path}: {e}")


def load_config_from_env() -> Dict[str, Any]:
    """
    Load configuration from environment variables.
    
    Returns:
        Configuration dictionary
    """
    config = {}
    
    # Redis configuration
    if os.getenv("REDIS_URL"):
        config["redis"] = {"url": os.getenv("REDIS_URL")}
    
    if os.getenv("REDIS_TIMEOUT"):
        config.setdefault("redis", {})["timeout"] = int(os.getenv("REDIS_TIMEOUT"))
    
    # PostgreSQL configuration (for future use)
    pg_config = {}
    if os.getenv("POSTGRES_HOST"):
        pg_config["hostname"] = os.getenv("POSTGRES_HOST")
    if os.getenv("POSTGRES_PORT"):
        pg_config["port"] = int(os.getenv("POSTGRES_PORT"))
    if os.getenv("POSTGRES_DB"):
        pg_config["db_name"] = os.getenv("POSTGRES_DB")
    if os.getenv("POSTGRES_USER"):
        pg_config["user"] = os.getenv("POSTGRES_USER")
    if os.getenv("POSTGRES_PASSWORD"):
        pg_config["password"] = os.getenv("POSTGRES_PASSWORD")
    
    if pg_config:
        config["postgresql"] = pg_config
    
    # Application configuration
    if os.getenv("LOG_LEVEL"):
        config["log_level"] = os.getenv("LOG_LEVEL")
    
    return config


def create_app_config(
    redis_url: Optional[str] = None,
    redis_timeout: Optional[int] = None,
    postgres_host: Optional[str] = None,
    postgres_port: Optional[int] = None,
    postgres_db: Optional[str] = None,
    postgres_user: Optional[str] = None,
    postgres_password: Optional[str] = None,
    config_file: Optional[str] = None
) -> AppConfig:
    """
    Create application configuration from multiple sources.
    
    Priority order:
    1. Explicit parameters (highest)
    2. Environment variables
    3. Configuration file
    4. Defaults (lowest)
    
    Args:
        redis_url: Redis connection URL
        redis_timeout: Redis connection timeout
        postgres_host: PostgreSQL hostname
        postgres_port: PostgreSQL port
        postgres_db: PostgreSQL database name
        postgres_user: PostgreSQL user
        postgres_password: PostgreSQL password
        config_file: Path to configuration file
        
    Returns:
        AppConfig instance
    """
    # Start with defaults
    config_data = {}
    
    # Load from configuration file if specified
    if config_file:
        file_config = load_config_from_file(config_file)
        if file_config:
            config_data.update(file_config)
    
    # Load from environment variables
    env_config = load_config_from_env()
    if env_config:
        # Merge environment config
        for key, value in env_config.items():
            if key in config_data and isinstance(config_data[key], dict) and isinstance(value, dict):
                config_data[key].update(value)
            else:
                config_data[key] = value
    
    # Apply explicit parameters (highest priority)
    if redis_url:
        config_data.setdefault("redis", {})["url"] = redis_url
    
    if redis_timeout:
        config_data.setdefault("redis", {})["timeout"] = redis_timeout
    
    # PostgreSQL parameters
    if postgres_host:
        config_data.setdefault("postgresql", {})["hostname"] = postgres_host
    
    if postgres_port:
        config_data.setdefault("postgresql", {})["port"] = postgres_port
    
    if postgres_db:
        config_data.setdefault("postgresql", {})["db_name"] = postgres_db
    
    if postgres_user:
        config_data.setdefault("postgresql", {})["user"] = postgres_user
    
    if postgres_password:
        config_data.setdefault("postgresql", {})["password"] = postgres_password
    
    return AppConfig(**config_data)


def get_helix_config_path() -> Optional[str]:
    """
    Get path to Helix configuration file.
    
    Looks for helix/config.yml in the current directory and parent directories.
    
    Returns:
        Path to config file or None if not found
    """
    current_dir = Path.cwd()
    
    # Check current directory and parent directories
    for path in [current_dir] + list(current_dir.parents):
        helix_config = path / "helix" / "config.yml"
        if helix_config.exists():
            return str(helix_config)
    
    return None


def load_helix_config() -> Optional[AppConfig]:
    """
    Load configuration from Helix config file if available.
    
    Returns:
        AppConfig instance or None if config file not found
    """
    config_path = get_helix_config_path()
    if not config_path:
        return None
    
    try:
        return create_app_config(config_file=config_path)
    except Exception as e:
        # Log warning but don't fail
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to load Helix config from {config_path}: {e}")
        return None


# Default configuration instances
DEFAULT_CONFIG = AppConfig()
HELIX_CONFIG = load_helix_config()