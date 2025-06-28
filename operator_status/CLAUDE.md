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

## Project Architecture

**Purpose**: Helix validator delegation checker that queries Redis for delegation messages and PostgreSQL for validator registration status.

**Core Components**:
- `main.py` - CLI interface using typer with commands for checking validator delegation status
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

**Output Formats**: 
- Table format (default) with rich formatting
- JSON format for programmatic use