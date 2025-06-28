"""
Helix Validator Delegation Checker

A Python command-line tool to check validator delegation submission rights
in the Helix MEV relay by querying Redis for delegation messages.

Usage:
    python main.py check 0x8a1d... --redis redis://localhost:6379
    python main.py batch validators.txt --redis redis://localhost:6379
    python main.py list --redis redis://localhost:6379
"""

import sys
import logging
from pathlib import Path
from typing import List, Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rich_print
import json

from redis_client import create_redis_client, HelixRedisClient
from delegation_parser import create_delegation_parser, DelegationParser
from database import create_postgres_client, HelixPostgreSQLClient
from validator_info import create_validator_info_service, ValidatorInfoService
from models import DelegationQueryResult, ValidatorInfo

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rich console for pretty output
console = Console()

# Typer app
app = typer.Typer(
    name="helix-delegation-checker",
    help="Check validator delegation submission rights in Helix MEV relay",
    add_completion=False
)


def validate_pubkey(pubkey: str) -> str:
    """Validate validator public key format (must start with 0x)."""
    if not pubkey:
        raise typer.BadParameter("Public key cannot be empty")
    
    # Require 0x prefix
    if not pubkey.startswith('0x'):
        raise typer.BadParameter("Validator public key must start with '0x'")
    
    hex_part = pubkey[2:]
    
    # Check hex format and length
    if not all(c in '0123456789abcdefABCDEF' for c in hex_part):
        raise typer.BadParameter(f"Invalid hex format: {pubkey}")
    
    if len(hex_part) != 96:  # 48 bytes = 96 hex characters
        raise typer.BadParameter(f"Invalid pubkey length: {len(hex_part)}. Expected 96 hex chars (48 bytes)")
    
    # Return exactly as user provided (with 0x prefix)
    return pubkey


def create_delegation_table(result: DelegationQueryResult) -> Table:
    """Create rich table for delegation results."""
    table = Table(title=f"Delegation Status for {result.validator_pubkey[:18]}...")
    
    table.add_column("Property", style="cyan", width=20)
    table.add_column("Value", style="white", width=60)
    
    table.add_row("Validator", result.validator_pubkey)
    table.add_row("Has Delegations", "✅ Yes" if result.has_delegations else "❌ No")
    table.add_row("Total Delegations", str(result.total_delegations))
    table.add_row("Active Delegations", str(result.active_delegation_count))
    
    if result.active_delegatees:
        delegatees = "\n".join([f"{pubkey[:18]}..." for pubkey in result.active_delegatees])
        table.add_row("Active Delegatees", delegatees)
    
    return table


def create_delegation_details_table(result: DelegationQueryResult) -> Optional[Table]:
    """Create detailed table of all delegation messages."""
    if not result.delegations:
        return None
    
    table = Table(title="Delegation Details")
    
    table.add_column("Action", style="yellow", width=10)
    table.add_column("Delegatee", style="cyan", width=20)
    table.add_column("Signature", style="dim", width=20)
    
    for delegation in result.delegations:
        action_display = "✅ Delegate" if delegation.is_delegation else "❌ Revoke"
        delegatee_display = f"{delegation.delegatee_pubkey[:18]}..."
        signature_display = f"0x{delegation.signature[:16]}..."
        
        table.add_row(action_display, delegatee_display, signature_display)
    
    return table


def create_validator_info_table(info: ValidatorInfo) -> Table:
    """Create simple table showing only registration status."""
    table = Table(title=f"Validator Registration Status for {info.validator_pubkey[:18]}...")
    
    table.add_column("Property", style="cyan", width=20)
    table.add_column("Value", style="white", width=60)
    
    table.add_row("Validator", info.validator_pubkey)
    table.add_row("Registered", "✅ Yes" if info.is_registered else "❌ No")
    
    return table




@app.command(name="validator-delegation")
def validator_delegation(
    validator_key: str = typer.Argument(..., help="Validator public key (hex, with or without 0x prefix)"),
    redis: str = typer.Option("redis://localhost:6379", help="Redis connection URL"),
    format: str = typer.Option("table", help="Output format: table, json"),
    details: bool = typer.Option(False, help="Show detailed delegation messages"),
    timeout: int = typer.Option(5, help="Redis connection timeout in seconds"),
    verbose: bool = typer.Option(False, help="Enable verbose logging")
):
    """Check delegation status for a single validator."""
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Validate public key
        normalized_pubkey = validate_pubkey(validator_key)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Connecting to Redis...", total=None)
            
            # Create delegation parser
            parser = create_delegation_parser(redis, timeout)
            
            progress.update(task, description="Querying delegation data...")
            
            # Get delegation status
            result = parser.get_validator_delegation_status(normalized_pubkey)
            
            progress.update(task, description="Complete", completed=True)
        
        # Output results
        if format == "json":
            output = {
                "validator_pubkey": result.validator_pubkey,
                "has_delegations": result.has_delegations,
                "total_delegations": result.total_delegations,
                "active_delegations": result.active_delegation_count,
                "active_delegatees": result.active_delegatees,
                "delegations": []
            }
            
            for delegation in result.delegations:
                output["delegations"].append({
                    "action": delegation.message.action_name,
                    "delegatee": delegation.delegatee_pubkey,
                    "signature": f"0x{delegation.signature}"
                })
            
            rich_print(json.dumps(output, indent=2))
            
        else:  # table format
            console.print()
            console.print(create_delegation_table(result))
            
            if details and result.delegations:
                console.print()
                console.print(create_delegation_details_table(result))
        
        # Exit code based on results
        if result.has_delegations:
            console.print(f"\n✅ Found {result.active_delegation_count} active delegations")
            sys.exit(0)
        else:
            console.print("\n❌ No delegations found")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"\n❌ Error: {e}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)


@app.command()
def batch(
    validators_file: str = typer.Argument(..., help="File containing validator public keys (one per line)"),
    redis: str = typer.Option("redis://localhost:6379", help="Redis connection URL"),
    output: Optional[str] = typer.Option(None, help="Output file for results (JSON format)"),
    timeout: int = typer.Option(5, help="Redis connection timeout in seconds"),
    verbose: bool = typer.Option(False, help="Enable verbose logging")
):
    """Check delegation status for multiple validators from file."""
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Read validator keys from file
        validators_path = Path(validators_file)
        if not validators_path.exists():
            raise typer.BadParameter(f"File not found: {validators_file}")
        
        validator_keys = []
        with validators_path.open() as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    try:
                        normalized = validate_pubkey(line)
                        validator_keys.append(normalized)
                    except typer.BadParameter as e:
                        console.print(f"⚠️ Skipping invalid key on line {line_num}: {e}", style="yellow")
        
        if not validator_keys:
            console.print("❌ No valid validator keys found in file", style="red")
            sys.exit(1)
        
        console.print(f"📋 Processing {len(validator_keys)} validators...")
        
        # Create delegation parser
        parser = create_delegation_parser(redis, timeout)
        
        results = []
        
        with Progress(console=console) as progress:
            task = progress.add_task("Checking delegations...", total=len(validator_keys))
            
            for validator_key in validator_keys:
                try:
                    result = parser.get_validator_delegation_status(validator_key)
                    results.append(result)
                    
                    status = f"✅ {result.active_delegation_count} active" if result.has_delegations else "❌ None"
                    progress.console.print(f"0x{validator_key[:16]}... - {status}")
                    
                except Exception as e:
                    progress.console.print(f"❌ 0x{validator_key[:16]}... - Error: {e}", style="red")
                    if verbose:
                        progress.console.print_exception()
                
                progress.advance(task)
        
        # Summary
        total_with_delegations = sum(1 for r in results if r.has_delegations)
        total_active_delegations = sum(r.active_delegation_count for r in results)
        
        console.print(f"\n📊 Summary:")
        console.print(f"  • Total validators checked: {len(results)}")
        console.print(f"  • Validators with delegations: {total_with_delegations}")
        console.print(f"  • Total active delegations: {total_active_delegations}")
        
        # Save results if output file specified
        if output:
            output_data = {
                "summary": {
                    "total_validators": len(results),
                    "validators_with_delegations": total_with_delegations,
                    "total_active_delegations": total_active_delegations
                },
                "results": []
            }
            
            for result in results:
                validator_data = {
                    "validator_pubkey": f"0x{result.validator_pubkey}",
                    "has_delegations": result.has_delegations,
                    "active_delegations": result.active_delegation_count,
                    "active_delegatees": [f"0x{pubkey}" for pubkey in result.active_delegatees]
                }
                output_data["results"].append(validator_data)
            
            with open(output, 'w') as f:
                json.dump(output_data, f, indent=2)
            
            console.print(f"💾 Results saved to {output}")
        
    except Exception as e:
        console.print(f"\n❌ Error: {e}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)


@app.command()
def list_validators(
    redis: str = typer.Option("redis://localhost:6379", help="Redis connection URL"),
    timeout: int = typer.Option(5, help="Redis connection timeout in seconds"),
    verbose: bool = typer.Option(False, help="Enable verbose logging")
):
    """List all validators with delegation data in Redis."""
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        parser = create_delegation_parser(redis, timeout)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Scanning Redis for validators...", total=None)
            
            validators = parser.get_validators_with_delegations()
            
            progress.update(task, description="Complete", completed=True)
        
        if not validators:
            console.print("❌ No validators with delegation data found", style="yellow")
            sys.exit(1)
        
        console.print(f"\n📋 Found {len(validators)} validators with delegation data:")
        
        for validator in validators:
            console.print(f"  • {validator}")
        
    except Exception as e:
        console.print(f"\n❌ Error: {e}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)


@app.command()
def validator_info(
    validator_key: str = typer.Argument(..., help="Validator public key (hex with 0x prefix)"),
    postgres_host: str = typer.Option("localhost", help="PostgreSQL hostname"),
    postgres_port: int = typer.Option(5432, help="PostgreSQL port"),
    postgres_db: str = typer.Option("helix_mev_relayer", help="PostgreSQL database name"),
    postgres_user: str = typer.Option("postgres", help="PostgreSQL user"),
    postgres_password: str = typer.Option("postgres", help="PostgreSQL password"),
    format: str = typer.Option("table", help="Output format: table, json"),
    verbose: bool = typer.Option(False, help="Enable verbose logging")
):
    """Get validator information from PostgreSQL database."""
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Validate public key
        normalized_pubkey = validate_pubkey(validator_key)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Connecting to PostgreSQL...", total=None)
            
            # Create PostgreSQL client
            postgres_client = create_postgres_client(
                postgres_host, postgres_port, postgres_db, postgres_user, postgres_password
            )
            
            progress.update(task, description="Querying validator information...")
            
            # Create validator info service and get data
            validator_service = create_validator_info_service(postgres_client)
            info = validator_service.get_validator_info(normalized_pubkey)
            
            progress.update(task, description="Complete", completed=True)
        
        # Output results
        if format == "json":
            output = {
                "validator_pubkey": info.validator_pubkey,
                "is_registered": info.is_registered
            }
            rich_print(json.dumps(output, indent=2))
            
        else:  # table format
            console.print()
            console.print(create_validator_info_table(info))
        
        postgres_client.disconnect()
        
        # Exit code based on registration status
        if info.is_registered:
            console.print(f"\n✅ Validator is registered in the database")
            sys.exit(0)
        else:
            console.print(f"\n❌ Validator is not registered in the database")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"\n❌ Error: {e}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)






if __name__ == "__main__":
    app()