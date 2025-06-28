#!/usr/bin/env python3
"""
Entry point for starting the Helix Validator Delegation HTTP server.

This script provides a production-ready way to start the FastAPI server
with configurable options for host, port, and other server settings.
"""

import os
import logging
import typer
from typing import Optional
import uvicorn

from api_models import ServerConfig
from http_server import create_app

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Typer app for CLI
cli_app = typer.Typer(
    name="helix-delegation-server",
    help="Start HTTP server for Helix validator delegation API",
    add_completion=False
)


@cli_app.command()
def start(
    host: str = typer.Option("0.0.0.0", help="Host to bind the server to"),
    port: int = typer.Option(8000, help="Port to bind the server to"),
    reload: bool = typer.Option(False, help="Enable auto-reload for development"),
    workers: int = typer.Option(1, help="Number of worker processes"),
    log_level: str = typer.Option("info", help="Log level (debug, info, warning, error)"),
    redis_url: str = typer.Option("redis://localhost:6379", help="Redis connection URL"),
    redis_timeout: int = typer.Option(5, help="Redis connection timeout in seconds"),
    redis_key_prefix: str = typer.Option("validators_by_operator", help="Redis key prefix for operator-validator mappings"),
    postgres_host: str = typer.Option("localhost", help="PostgreSQL hostname"),
    postgres_port: int = typer.Option(5432, help="PostgreSQL port"),
    postgres_db: str = typer.Option("helix_mev_relayer", help="PostgreSQL database name"),
    postgres_user: str = typer.Option("postgres", help="PostgreSQL username"),
    postgres_password: str = typer.Option("postgres", help="PostgreSQL password"),
):
    """
    Start the Helix Validator Delegation HTTP server.
    
    This command starts a FastAPI server that provides REST API endpoints
    for checking validator delegation status and related operations.
    """
    
    # Configure logging level
    numeric_level = getattr(logging, log_level.upper(), None)
    if isinstance(numeric_level, int):
        logging.getLogger().setLevel(numeric_level)
    
    # Create server configuration
    config = ServerConfig(
        redis_url=redis_url,
        redis_timeout=redis_timeout,
        redis_key_prefix=redis_key_prefix,
        postgres_host=postgres_host,
        postgres_port=postgres_port,
        postgres_db=postgres_db,
        postgres_user=postgres_user,
        postgres_password=postgres_password
    )
    
    # Create configured app
    from http_server import create_app
    app = create_app(config)
    
    # Log startup information
    logger.info(f"Starting Helix Validator Delegation API server")
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    logger.info(f"Workers: {workers}")
    logger.info(f"Log level: {log_level}")
    logger.info(f"Redis URL: {redis_url}")
    logger.info(f"Redis Key Prefix: {redis_key_prefix}")
    logger.info(f"PostgreSQL: {postgres_host}:{postgres_port}/{postgres_db}")
    
    if reload and workers > 1:
        logger.warning("Auto-reload is enabled, ignoring workers setting")
        workers = 1
    
    try:
        # Start the server
        uvicorn.run(
            app,
            host=host,
            port=port,
            workers=workers if not reload else 1,
            reload=False,  # Can't use reload with app instance
            log_level=log_level,
            access_log=True,
            # Production optimizations
            loop="auto",
            http="auto"
        )
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise typer.Exit(1)


@cli_app.command()
def config():
    """
    Show current configuration from environment variables.
    
    This command displays the configuration that would be used
    when starting the server, including values from environment variables.
    """
    print("Current Configuration:")
    print("=" * 50)
    
    # Server settings
    print(f"Host: {os.getenv('HOST', '0.0.0.0')}")
    print(f"Port: {os.getenv('PORT', '8000')}")
    print(f"Log Level: {os.getenv('LOG_LEVEL', 'info')}")
    
    # Redis settings
    print(f"Redis URL: {os.getenv('REDIS_URL', 'redis://localhost:6379')}")
    print(f"Redis Timeout: {os.getenv('REDIS_TIMEOUT', '5')}")
    print(f"Redis Key Prefix: {os.getenv('REDIS_KEY_PREFIX', 'validators_by_operator')}")
    
    # PostgreSQL settings
    print(f"PostgreSQL Host: {os.getenv('POSTGRES_HOST', 'localhost')}")
    print(f"PostgreSQL Port: {os.getenv('POSTGRES_PORT', '5432')}")
    print(f"PostgreSQL Database: {os.getenv('POSTGRES_DB', 'helix_mev_relayer')}")
    print(f"PostgreSQL User: {os.getenv('POSTGRES_USER', 'postgres')}")
    print(f"PostgreSQL Password: {'***' if os.getenv('POSTGRES_PASSWORD') else 'postgres'}")


@cli_app.command()
def health():
    """
    Check health of the services (Redis and PostgreSQL).
    
    This command tests connectivity to Redis and PostgreSQL
    without starting the full HTTP server.
    """
    from services import create_validator_delegation_service, create_validator_info_service_instance
    
    print("Health Check")
    print("=" * 30)
    
    # Test Redis
    print("Testing Redis connection...")
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        timeout = int(os.getenv('REDIS_TIMEOUT', '5'))
        
        service = create_validator_delegation_service(redis_url=redis_url, timeout=timeout)
        service._get_parser()
        print(f"✅ Redis: Connected to {redis_url}")
    except Exception as e:
        print(f"❌ Redis: Failed to connect - {e}")
    
    # Test PostgreSQL
    print("Testing PostgreSQL connection...")
    try:
        host = os.getenv('POSTGRES_HOST', 'localhost')
        port = int(os.getenv('POSTGRES_PORT', '5432'))
        db = os.getenv('POSTGRES_DB', 'helix_mev_relayer')
        user = os.getenv('POSTGRES_USER', 'postgres')
        password = os.getenv('POSTGRES_PASSWORD', 'postgres')
        
        service = create_validator_info_service_instance(
            postgres_host=host,
            postgres_port=port,
            postgres_db=db,
            postgres_user=user,
            postgres_password=password
        )
        service._get_service()
        service.disconnect()
        print(f"✅ PostgreSQL: Connected to {host}:{port}/{db}")
    except Exception as e:
        print(f"❌ PostgreSQL: Failed to connect - {e}")


def main():
    """Main entry point."""
    cli_app()


if __name__ == "__main__":
    main()