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
    
    def format_event(self, event: Dict[str, Any]) -> str:
        """Format an event for console display"""
        event_name = event['event']
        args = event['args']
        block_number = event['blockNumber']
        tx_hash = event['transactionHash'].hex()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        formatted = f"\n{'='*80}\n"
        formatted += f"🔥 EVENT DETECTED: {event_name}\n"
        formatted += f"⏰ Timestamp: {timestamp}\n"
        formatted += f"📦 Block: {block_number}\n"
        formatted += f"🔗 Transaction: {tx_hash}\n"
        formatted += f"📄 Contract: {event['address']}\n"
        formatted += f"{'='*80}\n"
        
        # Format event-specific data
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
        
        formatted += f"{'='*80}\n"
        return formatted
    
    def format_slack_message(self, event: Dict[str, Any]) -> str:
        """Format an event for Slack (more concise than console output)"""
        event_name = event['event']
        args = event['args']
        block_number = event['blockNumber']
        tx_hash = event['transactionHash'].hex()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get the correct block explorer URL for the network
        block_explorer = self.network_config['block_explorer']
        
        # Create a more concise message for Slack
        message = f"🔥 *{event_name}* detected on {self.network_config['name']}!\n"
        message += f"⏰ {timestamp} | 📦 Block {block_number}\n"
        message += f"🔗 <{block_explorer}/tx/{tx_hash}|View Transaction>\n"
        
        # Add event-specific details (abbreviated)
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