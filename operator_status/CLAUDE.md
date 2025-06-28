# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

**Python Environment**: Use `/home/will/work/eth/luban/operator-status/.venv/bin/python3` for testing and running scripts.

**Install Dependencies**:
```bash
pip install -e .
```

**Run the CLI**:
```bash
# Check single validator delegation status
python main.py validator-delegation 0x8a1d7b8dd64e0aafe7ea7b6c95065c9364cf99d38470db679bdf5c9bed34755c947c6c3cdb2f4a66dd4d31aae7e23d7a

# Batch check validators from file
python main.py batch validators.txt

# List all validators with delegation data
python main.py list-validators

# Get validator registration info from PostgreSQL
python main.py validator-info 0x8a1d... --postgres-host localhost --postgres-port 5434
```

**Run the HTTP Server**:
```bash
# Start HTTP server with default settings
python start_server.py start

# Start with custom configuration
python start_server.py start --host 0.0.0.0 --port 8080 --redis-url redis://localhost:6379 --redis-key-prefix validators_by_operator

# Check server health
python start_server.py health

# Show current configuration
python start_server.py config

# Development mode with auto-reload
python start_server.py start --reload --log-level debug
```

## Project Architecture

**Purpose**: Helix validator delegation checker that queries Redis for delegation messages and PostgreSQL for validator registration status. Provides both CLI and HTTP API interfaces.

**Core Components**:
- `main.py` - CLI interface using typer with commands for checking validator delegation status
- `http_server.py` - FastAPI HTTP server exposing REST API endpoints for delegation operations
- `start_server.py` - HTTP server entry point with configuration management
- `services.py` - Business logic layer shared between CLI and HTTP interfaces
- `api_models.py` - HTTP request/response models and API schemas
- `redis_client.py` - Redis connection wrapper for accessing delegation message cache
- `database.py` - PostgreSQL client for querying validator registration data
- `delegation_parser.py` - Parses delegation messages from Redis and determines active delegations
- `validator_info.py` - Service for retrieving validator registration information
- `models.py` - Pydantic models for delegation messages, validation, and API responses

**Configuration**: 
- Database connection details are read from `helix/config.yml`
- Supports both Redis (delegation data) and PostgreSQL (registration data) backends
- Default config: PostgreSQL on localhost:5434, Redis on localhost:6379

**Data Models**:
- `SignedDelegation` - BLS-signed delegation messages (delegate/revoke actions)
- `DelegationQueryResult` - Aggregated results showing active delegations per validator
- `ValidatorInfo` - Basic validator registration status from PostgreSQL

**HTTP API Endpoints**:
- `GET /validator-delegation/{validator_key}` - Check delegation status for single validator
- `POST /batch` - Batch check validators (accepts JSON array of validator keys)
- `GET /list-validators` - List all validators with delegation data in Redis
- `GET /validator-info/{validator_key}` - Get validator registration info from PostgreSQL
- `GET /operator/{operator_address}` - Get validators registered to a specific operator (from operator_monitor Redis data)
- `GET /health` - Health check for Redis and PostgreSQL connections
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

**Output Formats**: 
- CLI: Table format (default) with rich formatting, JSON format for programmatic use
- HTTP API: JSON responses with structured data models and error handling