"""Event processing logic"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from web3 import Web3

from .calldata_decoder import CalldataDecoder

logger = logging.getLogger(__name__)


class EventProcessor:
    """Processes and formats Registry events"""
    
    def __init__(self, network_config: dict, eigenlayer_middleware_address: str = None, web3_client=None, enable_calldata_decoding: bool = True):
        """
        Initialize event processor
        
        Args:
            network_config: Network configuration dict
            eigenlayer_middleware_address: EigenLayerMiddleware contract address for filtering
            web3_client: Web3Client instance for transaction fetching and calldata decoding
            enable_calldata_decoding: Whether to enable transaction calldata decoding
        """
        self.network_config = network_config
        self.eigenlayer_middleware_address = eigenlayer_middleware_address.lower() if eigenlayer_middleware_address else None
        self.web3_client = web3_client
        self.enable_calldata_decoding = enable_calldata_decoding
        
        # Initialize calldata decoder if web3_client is available and decoding is enabled
        self.calldata_decoder = CalldataDecoder(web3_client.web3) if (web3_client and enable_calldata_decoding) else None
        
        # SlashingType enum mapping
        self.slashing_types = {
            0: "Fraud",
            1: "Equivocation", 
            2: "Commitment"
        }
        
        # OperatorStatus enum mapping
        self.operator_statuses = {
            0: "NEVER_REGISTERED",
            1: "REGISTERED", 
            2: "DEREGISTERED"
        }
        
        # RestakingProtocol enum mapping
        self.restaking_protocols = {
            0: "NONE",
            1: "EIGENLAYER",
            2: "SYMBIOTIC"
        }
    
    def should_process_event(self, event: Dict[str, Any]) -> bool:
        """
        Check if an event should be processed based on filtering criteria
        
        Args:
            event: Event data dictionary
            
        Returns:
            bool: True if event should be processed, False otherwise
        """
        contract_name = event.get('contract_name', 'Unknown')
        
        # For EigenLayer AllocationManager events, only process if AVS matches EigenLayerMiddleware
        if contract_name == "EigenLayerAllocationManager":
            if not self.eigenlayer_middleware_address:
                logger.warning("AllocationManager event detected but no EigenLayerMiddleware address configured for filtering")
                return False
                
            event_name = event['event']
            args = event['args']
            
            if event_name in ['OperatorAddedToOperatorSet', 'OperatorRemovedFromOperatorSet']:
                operator_set = args.get('operatorSet')
                if operator_set:
                    avs_address = operator_set.get('avs', '').lower()
                    if avs_address != self.eigenlayer_middleware_address:
                        logger.debug(f"Ignoring AllocationManager event for AVS {avs_address} (not EigenLayerMiddleware)")
                        return False
        
        return True
    
    def format_event(self, event: Dict[str, Any]) -> str:
        """Format an event for display"""
        event_name = event['event']
        args = event['args']
        block_number = event['blockNumber']
        tx_hash = event['transactionHash'].hex()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        contract_name = event.get('contract_name', 'Unknown')
        
        # Get the correct block explorer URL for the network
        block_explorer = self.network_config['block_explorer']
        
        formatted = f"\n{'='*80}\n"
        formatted += f"🔥 EVENT DETECTED: {event_name}\n"
        formatted += f"⏰ Timestamp: {timestamp}\n"
        formatted += f"📦 Block: {block_number}\n"
        formatted += f"🔗 Transaction: {tx_hash}\n"
        formatted += f"🌐 Block Explorer: {block_explorer}/tx/{tx_hash}\n"
        formatted += f"📄 Contract: {contract_name} ({event['address']})\n"
        formatted += f"=={'='*76}==\n"
        
        # Contract-specific formatting
        if contract_name == "Registry":
            formatted += self._format_registry_event(event_name, args, event)
        elif contract_name == "TaiyiRegistryCoordinator":
            formatted += self._format_taiyi_registry_coordinator_event(event_name, args)
        elif contract_name == "TaiyiEscrow":
            formatted += self._format_taiyi_escrow_event(event_name, args)
        elif contract_name == "EigenLayerAllocationManager":
            formatted += self._format_eigenlayer_allocation_manager_event(event_name, args)
        else:
            # Generic formatting for unknown contract types
            formatted += self._format_generic_event(args)
        
        formatted += f"{'='*80}\n"
        return formatted
    
    def _format_registry_event(self, event_name: str, args: Dict[str, Any], event: Dict[str, Any] = None) -> str:
        """Format Registry contract events"""
        formatted = ""
        
        if event_name == "OperatorRegistered":
            formatted += f"📝 Registration Root: {args['registrationRoot'].hex()}\n"
            formatted += f"💰 Collateral: {Web3.from_wei(args['collateralWei'], 'ether')} ETH\n"
            formatted += f"👤 Owner: {args['owner']}\n"
            
            # Add transaction analysis for OperatorRegistered events
            if event and self.eigenlayer_middleware_address:
                tx_analysis = self._analyze_transaction_calldata(event)
                if tx_analysis:
                    formatted += f"\n{tx_analysis}"
            
        elif event_name == "OperatorSlashed":
            slashing_type = self.slashing_types.get(args['slashingType'], "Unknown")
            formatted += f"⚡ Slashing Type: {slashing_type}\n"
            formatted += f"📝 Registration Root: {args['registrationRoot'].hex()}\n"
            formatted += f"👤 Owner: {args['owner']}\n"
            formatted += f"🔍 Challenger: {args['challenger']}\n"
            formatted += f"⚔️  Slasher: {args['slasher']}\n"
            formatted += f"💸 Slashed Amount: {Web3.from_wei(args['slashAmountWei'], 'ether')} ETH\n"
            
        elif event_name == "OperatorUnregistered":
            formatted += f"📝 Registration Root: {args['registrationRoot'].hex()}\n"
            
        elif event_name == "CollateralClaimed":
            formatted += f"📝 Registration Root: {args['registrationRoot'].hex()}\n"
            formatted += f"💰 Claimed Amount: {Web3.from_wei(args['collateralWei'], 'ether')} ETH\n"
            
        elif event_name == "CollateralAdded":
            formatted += f"📝 Registration Root: {args['registrationRoot'].hex()}\n"
            formatted += f"💰 Added Amount: {Web3.from_wei(args['collateralWei'], 'ether')} ETH\n"
            
        elif event_name == "OperatorOptedIn":
            formatted += f"📝 Registration Root: {args['registrationRoot'].hex()}\n"
            formatted += f"⚔️  Slasher: {args['slasher']}\n"
            formatted += f"🔑 Committer: {args['committer']}\n"
            
        elif event_name == "OperatorOptedOut":
            formatted += f"📝 Registration Root: {args['registrationRoot'].hex()}\n"
            formatted += f"⚔️  Slasher: {args['slasher']}\n"
            
        return formatted
    
    def _format_taiyi_registry_coordinator_event(self, event_name: str, args: Dict[str, Any]) -> str:
        """Format TaiyiRegistryCoordinator contract events"""
        formatted = ""
        
        if event_name == "OperatorRegistered":
            formatted += f"👤 Operator: {args['operator']}\n"
            formatted += f"🆔 Operator ID: {args['operatorId'].hex()}\n"
            formatted += f"📋 Linglong Subset IDs: {list(args['linglongSubsetIds'])}\n"
            
        elif event_name == "OperatorDeregistered":
            formatted += f"👤 Operator: {args['operator']}\n"
            formatted += f"🆔 Operator ID: {args['operatorId'].hex()}\n"
            formatted += f"📋 Linglong Subset IDs: {list(args['linglongSubsetIds'])}\n"
            
        elif event_name == "OperatorStatusChanged":
            prev_status = self.operator_statuses.get(args['previousStatus'], f"Unknown({args['previousStatus']})")
            new_status = self.operator_statuses.get(args['newStatus'], f"Unknown({args['newStatus']})")
            formatted += f"👤 Operator: {args['operator']}\n"
            formatted += f"📊 Previous Status: {prev_status}\n"
            formatted += f"📊 New Status: {new_status}\n"
            
        elif event_name == "LinglongSubsetCreated":
            formatted += f"🆔 Linglong Subset ID: {args['linglongSubsetId']}\n"
            formatted += f"💰 Minimum Stake: {Web3.from_wei(args['minStake'], 'ether')} ETH\n"
            
        elif event_name == "OperatorAddedToSubset":
            formatted += f"👤 Operator: {args['operator']}\n"
            formatted += f"🆔 Linglong Subset ID: {args['linglongSubsetId']}\n"
            
        elif event_name == "OperatorRemovedFromSubset":
            formatted += f"👤 Operator: {args['operator']}\n"
            formatted += f"🆔 Linglong Subset ID: {args['linglongSubsetId']}\n"
            
        elif event_name == "SocketRegistryUpdated":
            formatted += f"🔄 Old Registry: {args['oldRegistry']}\n"
            formatted += f"🔄 New Registry: {args['newRegistry']}\n"
            
        elif event_name == "PubkeyRegistryUpdated":
            formatted += f"🔄 Old Registry: {args['oldRegistry']}\n"
            formatted += f"🔄 New Registry: {args['newRegistry']}\n"
            
        elif event_name == "OperatorSocketUpdate":
            formatted += f"🆔 Operator ID: {args['operatorId'].hex()}\n"
            formatted += f"🔌 Socket: {args['socket']}\n"
            
        elif event_name == "RestakingMiddlewareUpdated":
            protocol = self.restaking_protocols.get(args['restakingProtocol'], f"Unknown({args['restakingProtocol']})")
            formatted += f"🔗 Restaking Protocol: {protocol}\n"
            formatted += f"🔄 New Middleware: {args['newMiddleware']}\n"
            
        return formatted
    
    def _format_taiyi_escrow_event(self, event_name: str, args: Dict[str, Any]) -> str:
        """Format TaiyiEscrow contract events"""
        formatted = ""
        
        if event_name == "Deposited":
            formatted += f"👤 User: {args['user']}\n"
            formatted += f"💰 Amount: {Web3.from_wei(args['amount'], 'ether')} ETH\n"
            
        elif event_name == "Withdrawn":
            formatted += f"👤 User: {args['user']}\n"
            formatted += f"💸 Amount: {Web3.from_wei(args['amount'], 'ether')} ETH\n"
            
        elif event_name == "PaymentMade":
            execution_status = "✅ After Execution" if args['isAfterExec'] else "⏳ Pre-execution"
            formatted += f"👤 From: {args['from']}\n"
            formatted += f"💰 Amount: {Web3.from_wei(args['amount'], 'ether')} ETH\n"
            formatted += f"📋 Status: {execution_status}\n"
            
        elif event_name == "RequestedWithdraw":
            formatted += f"👤 User: {args['user']}\n"
            formatted += f"💰 Requested Amount: {Web3.from_wei(args['amount'], 'ether')} ETH\n"
        
        return formatted
    
    def _format_eigenlayer_allocation_manager_event(self, event_name: str, args: Dict[str, Any]) -> str:
        """Format EigenLayer AllocationManager contract events"""
        formatted = ""
        
        if event_name == "OperatorAddedToOperatorSet":
            operator_set = args['operatorSet']
            formatted += f"👤 Operator: {args['operator']}\n"
            formatted += f"🏢 AVS Address: {operator_set['avs']}\n"
            formatted += f"🆔 Operator Set ID: {operator_set['id']}\n"
            
        elif event_name == "OperatorRemovedFromOperatorSet":
            operator_set = args['operatorSet']
            formatted += f"👤 Operator: {args['operator']}\n"
            formatted += f"🏢 AVS Address: {operator_set['avs']}\n"
            formatted += f"🆔 Operator Set ID: {operator_set['id']}\n"
            
        return formatted
    
    def _format_generic_event(self, args: Dict[str, Any]) -> str:
        """Format generic events for unknown contracts"""
        formatted = "📋 Event Arguments:\n"
        for key, value in args.items():
            formatted += f"   {key}: {value}\n"
        return formatted
    
    def _format_registry_slack(self, event_name: str, args: Dict[str, Any]) -> str:
        """Format Registry events for Slack"""
        message = ""
        
        if event_name == "OperatorRegistered":
            collateral_eth = Web3.from_wei(args['collateralWei'], 'ether')
            message += f"💰 Collateral: {collateral_eth} ETH\n"
            message += f"👤 Owner: `{args['owner']}`"
            
        elif event_name == "OperatorSlashed":
            slashing_type = self.slashing_types.get(args['slashingType'], "Unknown")
            slashed_eth = Web3.from_wei(args['slashAmountWei'], 'ether')
            message += f"⚡ Type: {slashing_type}\n"
            message += f"💸 Slashed: {slashed_eth} ETH\n"
            message += f"👤 Owner: `{args['owner']}`\n"
            message += f"⚔️ Slasher: `{args['slasher']}`"
            
        elif event_name == "OperatorUnregistered":
            message += f"📝 Root: `{args['registrationRoot'].hex()[:10]}...`"
            
        elif event_name == "CollateralClaimed":
            claimed_eth = Web3.from_wei(args['collateralWei'], 'ether')
            message += f"💰 Claimed: {claimed_eth} ETH"
            
        elif event_name == "CollateralAdded":
            added_eth = Web3.from_wei(args['collateralWei'], 'ether')
            message += f"💰 Added: {added_eth} ETH"
            
        elif event_name == "OperatorOptedIn":
            message += f"⚔️ Slasher: `{args['slasher']}`\n"
            message += f"🔑 Committer: `{args['committer']}`"
            
        elif event_name == "OperatorOptedOut":
            message += f"⚔️ Slasher: `{args['slasher']}`"
            
        return message
    
    def _format_taiyi_slack(self, event_name: str, args: Dict[str, Any]) -> str:
        """Format TaiyiRegistryCoordinator events for Slack"""
        message = ""
        
        if event_name == "OperatorRegistered":
            message += f"👤 Operator: `{args['operator']}`\n"
            message += f"📋 Subsets: {list(args['linglongSubsetIds'])}"
            
        elif event_name == "OperatorDeregistered":
            message += f"👤 Operator: `{args['operator']}`\n"
            message += f"📋 Subsets: {list(args['linglongSubsetIds'])}"
            
        elif event_name == "OperatorStatusChanged":
            prev_status = self.operator_statuses.get(args['previousStatus'], f"Unknown({args['previousStatus']})")
            new_status = self.operator_statuses.get(args['newStatus'], f"Unknown({args['newStatus']})")
            message += f"👤 Operator: `{args['operator']}`\n"
            message += f"📊 Status: {prev_status} → {new_status}"
            
        elif event_name == "LinglongSubsetCreated":
            min_stake_eth = Web3.from_wei(args['minStake'], 'ether')
            message += f"🆔 Subset ID: {args['linglongSubsetId']}\n"
            message += f"💰 Min Stake: {min_stake_eth} ETH"
            
        elif event_name == "OperatorAddedToSubset":
            message += f"👤 Operator: `{args['operator']}`\n"
            message += f"➕ Added to Subset: {args['linglongSubsetId']}"
            
        elif event_name == "OperatorRemovedFromSubset":
            message += f"👤 Operator: `{args['operator']}`\n"
            message += f"➖ Removed from Subset: {args['linglongSubsetId']}"
            
        elif event_name == "SocketRegistryUpdated":
            message += f"🔄 Registry Updated: `{args['newRegistry']}`"
            
        elif event_name == "PubkeyRegistryUpdated":
            message += f"🔄 Registry Updated: `{args['newRegistry']}`"
            
        elif event_name == "OperatorSocketUpdate":
            message += f"🆔 Operator: `{args['operatorId'].hex()[:10]}...`\n"
            message += f"🔌 Socket: {args['socket']}"
            
        elif event_name == "RestakingMiddlewareUpdated":
            protocol = self.restaking_protocols.get(args['restakingProtocol'], f"Unknown({args['restakingProtocol']})")
            message += f"🔗 Protocol: {protocol}\n"
            message += f"🔄 Middleware: `{args['newMiddleware']}`"
            
        return message
    
    def _format_eigenlayer_allocation_manager_slack(self, event_name: str, args: Dict[str, Any]) -> str:
        """Format EigenLayer AllocationManager events for Slack"""
        message = ""
        
        if event_name == "OperatorAddedToOperatorSet":
            operator_set = args['operatorSet']
            message += f"👤 Operator: `{args['operator']}`\n"
            message += f"🏢 AVS: `{operator_set['avs']}`\n"
            message += f"🆔 Set ID: {operator_set['id']}"
            
        elif event_name == "OperatorRemovedFromOperatorSet":
            operator_set = args['operatorSet']
            message += f"👤 Operator: `{args['operator']}`\n"
            message += f"🏢 AVS: `{operator_set['avs']}`\n"
            message += f"🆔 Set ID: {operator_set['id']}"
            
        return message
    
    def _analyze_transaction_calldata(self, event: Dict[str, Any]) -> Optional[str]:
        """
        Analyze transaction calldata for Registry events
        
        Args:
            event: Event data dictionary
            
        Returns:
            Formatted transaction analysis string or None
        """
        if not self.calldata_decoder or not self.web3_client:
            logger.debug("Calldata decoder or web3_client not available")
            return None
        
        try:
            tx_hash = event.get('transactionHash')
            if not tx_hash:
                logger.debug("No transaction hash in event")
                return None
            
            # Convert bytes to hex string if needed
            if hasattr(tx_hash, 'hex'):
                tx_hash = tx_hash.hex()
            
            # Fetch transaction details
            transaction = self.web3_client.get_transaction_by_hash(tx_hash)
            if not transaction:
                logger.debug(f"Could not fetch transaction {tx_hash}")
                return None
            
            # Analyze transaction for EigenLayerMiddleware registerValidators call
            analysis = self.calldata_decoder.analyze_transaction_for_registry_event(
                transaction, self.eigenlayer_middleware_address
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing transaction calldata: {e}")
            return None
    
    def get_operator_validator_mapping(self, event: Dict[str, Any]) -> Optional[tuple]:
        """
        Extract operator address and validator public keys from Registry OperatorRegistered event
        
        Args:
            event: Event data dictionary
            
        Returns:
            Tuple of (operator_address, validator_pubkeys) or None if not applicable
        """
        if not self.calldata_decoder or not self.web3_client:
            logger.debug("Calldata decoder or web3_client not available")
            return None
        
        # Only process Registry OperatorRegistered events
        if (event.get('contract_name') != 'Registry' or 
            event.get('event') != 'OperatorRegistered'):
            return None
        
        try:
            tx_hash = event.get('transactionHash')
            if not tx_hash:
                logger.debug("No transaction hash in event")
                return None
            
            # Convert bytes to hex string if needed
            if hasattr(tx_hash, 'hex'):
                tx_hash = tx_hash.hex()
            
            # Fetch transaction details
            transaction = self.web3_client.get_transaction_by_hash(tx_hash)
            if not transaction:
                logger.debug(f"Could not fetch transaction {tx_hash}")
                return None
            
            # Extract operator address from transaction sender
            operator_address = transaction.get('from')
            if not operator_address:
                logger.debug("No 'from' address in transaction")
                return None
            
            # Check if transaction was sent to EigenLayerMiddleware
            to_address = transaction.get('to', '').lower()
            if (self.eigenlayer_middleware_address and 
                to_address != self.eigenlayer_middleware_address):
                logger.debug(f"Transaction not sent to EigenLayerMiddleware: {to_address}")
                return None
            
            # Decode calldata to extract validator public keys
            calldata = transaction.get('input', '0x')
            decoded = self.calldata_decoder.decode_register_validators_calldata(calldata)
            
            if not decoded or not decoded.get('registrations'):
                logger.debug("No registerValidators calldata found or no registrations")
                return None
            
            # Extract validator public keys
            validator_pubkeys = []
            for registration in decoded['registrations']:
                pubkey_hex = registration.get('pubkey_hex')
                if pubkey_hex:
                    validator_pubkeys.append(pubkey_hex)
            
            if not validator_pubkeys:
                logger.debug("No validator public keys found in calldata")
                return None
            
            logger.info(f"Extracted {len(validator_pubkeys)} validators for operator {operator_address}")
            return (operator_address, validator_pubkeys)
            
        except Exception as e:
            logger.error(f"Error extracting operator-validator mapping: {e}")
            return None
    
    def validate_event(self, event: Dict[str, Any]) -> bool:
        """Validate event structure and data"""
        try:
            # Basic validation
            required_fields = ['event', 'args', 'blockNumber', 'transactionHash', 'address']
            for field in required_fields:
                if field not in event:
                    logger.warning(f"Event missing required field: {field}")
                    return False
            
            # Event-specific validation can be added here
            return True
            
        except Exception as e:
            logger.error(f"Error validating event: {e}")
            return False 