"""Event processing logic"""

import logging
from datetime import datetime
from typing import Dict, Any
from web3 import Web3

logger = logging.getLogger(__name__)


class EventProcessor:
    """Processes and formats Registry events"""
    
    def __init__(self, network_config: dict):
        """
        Initialize event processor
        
        Args:
            network_config: Network configuration dict
        """
        self.network_config = network_config
        
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
            formatted += self._format_registry_event(event_name, args)
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
    
    def _format_registry_event(self, event_name: str, args: Dict[str, Any]) -> str:
        """Format Registry contract events"""
        formatted = ""
        
        if event_name == "OperatorRegistered":
            formatted += f"📝 Registration Root: {args['registrationRoot'].hex()}\n"
            formatted += f"💰 Collateral: {Web3.from_wei(args['collateralWei'], 'ether')} ETH\n"
            formatted += f"👤 Owner: {args['owner']}\n"
            
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