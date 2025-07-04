# Helix Validator Delegation Checker

A Python script to check validator delegation submission rights in the Helix MEV relay by querying PostgreSQL and Redis databases.

## Features

- **Single Validator Check**: Check submission rights for a specific validator
- **Batch Processing**: Check multiple validators from a file
- **Builder Filtering**: Check rights for specific builders or all registered builders
- **Slot-specific Preferences**: Support for per-slot validator preferences
- **Multiple Output Formats**: Table, JSON, and summary formats
- **Redis Cache Integration**: Checks both database and cache for complete status
- **Rich CLI Interface**: Beautiful tables and colored output using Rich

## Installation

1. Install dependencies:
```bash
pip install -e .
```

2. Ensure Helix relay is running with PostgreSQL and Redis accessible
3. Update `helix/config.yml` with correct database connection details

## Database Schema

The script queries these PostgreSQL tables:
- `validator_registrations` - Main validator registration data
- `validator_preferences` - Validator filtering and trusted builder preferences  
- `slot_preferences` - Per-slot specific preferences
- `builder_info` - Registered builder information and permissions
- `trusted_proposers` - Whitelisted proposers
- `proposer_duties` - Current proposer duty assignments

Redis cache keys:
- `proposer-whitelist` - Cached proposer whitelist
- `delegations:{pubkey}` - Validator-specific delegation data
- `builder-info` - Cached builder information

## Usage

### Check Single Validator

```bash
# Basic check for all builders
python main.py check 0x8a1d7b8dd64e0aafe7ea7b6c95065c9364cf99d38470db679bdf5c9bed34755c947c6c3cdb2f4a66dd4d31aae7e23d7a

# Check specific builder
python main.py check 0x8a1d... --builder "flashbots"

# Check for specific slot
python main.py check 0x8a1d... --slot 123456

# JSON output
python main.py check 0x8a1d... --format json

# Custom config file
python main.py check 0x8a1d... --config /path/to/config.yml
```

### Batch Check Multiple Validators

```bash
# Check validators from file
python main.py batch example_validators.txt

# Save results to JSON file
python main.py batch validators.txt --output results.json

# Check specific builder for all validators
python main.py batch validators.txt --builder "flashbots"
```

### List All Builders

```bash
# Show all registered builders
python main.py list-builders
```

## Configuration

The script reads database connection details from `helix/config.yml`:

```yaml
postgres:
  hostname: localhost
  port: 5434
  db_name: helix_mev_relayer
  user: postgres
  password: postgres
  region: 0

redis:
  url: redis://localhost:6379
```

## Output Examples

### Table Format (Default)
```
3333333
 Builder ID  Has Rights  Registered  Active  Trusted  Builder OK  Filtering  Reason                                          
!GGGGGGG)
 flashbots    YES                      L                 Regional   Validator is registered and active | Builder   
                                                                            'flashbots' is permitted | Using regional      
                                                                            filtering | Builder 'flashbots' is in trusted   
                                                                            builders list |  Submission rights GRANTED   
            4           4            4        4         4            4           4                                                 
```

### JSON Format
```json
{
  "request": {
    "validator_pubkey": "0x8a1d7b8dd64e0aafe7ea7b6c95065c9364cf99d38470db679bdf5c9bed34755c947c6c3cdb2f4a66dd4d31aae7e23d7a",
    "builder_id": null,
    "slot_number": null,
    "check_current_duties": true
  },
  "results": [
    {
      "validator_pubkey": "8a1d7b8dd64e0aafe7ea7b6c95065c9364cf99d38470db679bdf5c9bed34755c947c6c3cdb2f4a66dd4d31aae7e23d7a",
      "builder_id": "flashbots",
      "has_submission_rights": true,
      "is_registered": true,
      "is_active": true,
      "is_trusted_proposer": false,
      "builder_permitted": true,
      "filtering_mode": 1,
      "trusted_builders": ["flashbots", "titan"],
      "reason": "Validator is registered and active | Builder 'flashbots' is permitted | Using regional filtering | Builder 'flashbots' is in trusted builders list |  Submission rights GRANTED"
    }
  ],
  "total_builders_checked": 1,
  "permitted_builders": 1
}
```

## Validation Logic

The script evaluates submission rights based on:

1. **Basic Registration**: Validator must be registered and active
2. **Builder Permissions**: Builder must be in the permitted builders list
3. **Filtering Preferences**: 
   - **Global filtering**: All permitted builders allowed
   - **Regional filtering**: Only trusted builders in validator's list allowed
4. **Slot-specific Overrides**: Per-slot preferences override general preferences
5. **Trusted Proposers**: Special whitelist that may bypass some restrictions

## Error Handling

- Database connection errors are logged and reported
- Invalid public keys are handled gracefully
- Missing validators or builders are reported with clear messages
- Redis connection failures fall back to database-only checks

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check PostgreSQL is running on configured host/port
   - Verify credentials in `helix/config.yml`
   - Ensure database `helix_mev_relayer` exists

2. **Redis Connection Failed**
   - Check Redis is running on configured URL
   - Verify Redis URL in `helix/config.yml`
   - Script will continue with database-only checks

3. **No Validators Found**
   - Verify validator public keys are correctly formatted (48 bytes hex)
   - Check that validators are actually registered in the database
   - Use `--verbose` flag for detailed logging

4. **Config File Not Found**
   - Ensure `helix/config.yml` exists in the correct location
   - Use `--config` flag to specify custom config path

### Debug Mode

Use `--verbose` flag for detailed logging:
```bash
python main.py check 0x8a1d... --verbose
```

## Development

To extend functionality:

1. **Add New Checks**: Extend `ValidatorDelegationChecker` class in `checker.py`
2. **New Data Models**: Add Pydantic models in `models.py` 
3. **Database Changes**: Update SQL queries and connection handling in `database.py`
4. **CLI Commands**: Add new Typer commands in `main.py`

## License

[Add your license information here]