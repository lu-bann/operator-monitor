#!/usr/bin/env python3
"""
Registry Event Monitor

This program listens to all events emitted from the Registry.sol contract
and prints them in real-time as they occur on the blockchain.
"""

import asyncio
import os
from typing import Dict, Any, List
from web3 import Web3
from datetime import datetime
import logging

# Slack integration
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Network configurations
NETWORK_CONFIGS = {
    'mainnet': {
        'name': 'Ethereum Mainnet',
        'chain_id': 1,
        'default_rpc': 'https://eth.llamarpc.com',
        'block_explorer': 'https://etherscan.io'
    },
    'holesky': {
        'name': 'Holesky Testnet',
        'chain_id': 17000,
        'default_rpc': 'https://ethereum-holesky.publicnode.com',
        'block_explorer': 'https://holesky.etherscan.io'
    },
    'hoodi': {
        'name': 'Hoodi Testnet',
        'chain_id': 5,
        'default_rpc': 'https://ethereum-hoodi-rpc.publicnode.com',
        'block_explorer': 'https://hoodi.etherscan.io'
    },
    'devnet': {
        'name': 'Local Devnet',
        'chain_id': 1337,
        'default_rpc': 'http://localhost:8545',
        'block_explorer': 'https://localhost:8545'
    }
}


class RegistryEventMonitor:
    def __init__(self, rpc_url: str, contract_address: str, network: str = 'mainnet', 
                 slack_token: str = None, slack_channel: str = None):
        """
        Initialize the Registry Event Monitor
        
        Args:
            rpc_url: The RPC URL of the Ethereum node
            contract_address: The deployed Registry contract address
            network: The network name (mainnet, holesky, goerli, sepolia)
            slack_token: Slack bot token for notifications
            slack_channel: Slack channel to send notifications to
        """
        self.network = network.lower()
        self.network_config = NETWORK_CONFIGS.get(self.network, NETWORK_CONFIGS['mainnet'])
        
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not self.web3.is_connected():
            raise ConnectionError("Failed to connect to Ethereum node")
        
        # Verify we're connected to the correct network
        try:
            chain_id = self.web3.eth.chain_id
            expected_chain_id = self.network_config['chain_id']
            if chain_id != expected_chain_id:
                logger.warning(f"Chain ID mismatch: expected {expected_chain_id} for {self.network}, got {chain_id}")
        except Exception as e:
            logger.warning(f"Could not verify chain ID: {e}")
        
        self.contract_address = Web3.to_checksum_address(contract_address)
        
        # Slack configuration
        self.slack_enabled = slack_token and slack_channel
        if self.slack_enabled:
            self.slack_client = WebClient(token=slack_token)
            self.slack_channel = slack_channel
            logger.info(f"Slack notifications enabled for channel: {slack_channel}")
        else:
            self.slack_client = None
            self.slack_channel = None
            logger.info("Slack notifications disabled")
        
        # Registry contract ABI - focusing on events
        self.contract_abi = [
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "registrationRoot", "type": "bytes32"},
                    {"indexed": False, "name": "collateralWei", "type": "uint256"},
                    {"indexed": False, "name": "owner", "type": "address"}
                ],
                "name": "OperatorRegistered",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": False, "name": "slashingType", "type": "uint8"},
                    {"indexed": True, "name": "registrationRoot", "type": "bytes32"},
                    {"indexed": False, "name": "owner", "type": "address"},
                    {"indexed": False, "name": "challenger", "type": "address"},
                    {"indexed": True, "name": "slasher", "type": "address"},
                    {"indexed": False, "name": "slashAmountWei", "type": "uint256"}
                ],
                "name": "OperatorSlashed",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "registrationRoot", "type": "bytes32"}
                ],
                "name": "OperatorUnregistered",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "registrationRoot", "type": "bytes32"},
                    {"indexed": False, "name": "collateralWei", "type": "uint256"}
                ],
                "name": "CollateralClaimed",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "registrationRoot", "type": "bytes32"},
                    {"indexed": False, "name": "collateralWei", "type": "uint256"}
                ],
                "name": "CollateralAdded",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "registrationRoot", "type": "bytes32"},
                    {"indexed": True, "name": "slasher", "type": "address"},
                    {"indexed": True, "name": "committer", "type": "address"}
                ],
                "name": "OperatorOptedIn",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "registrationRoot", "type": "bytes32"},
                    {"indexed": True, "name": "slasher", "type": "address"}
                ],
                "name": "OperatorOptedOut",
                "type": "event"
            }
        ]
        
        self.contract = self.web3.eth.contract(
            address=self.contract_address,
            abi=self.contract_abi
        )
        
        # SlashingType enum mapping
        self.slashing_types = {
            0: "Fraud",
            1: "Equivocation", 
            2: "Commitment"
        }
        
        logger.info(f"Connected to Ethereum node: {rpc_url}")
        logger.info(f"Monitoring Registry contract at: {self.contract_address}")

    def format_event(self, event: Dict[str, Any]) -> str:
        """Format an event for display"""
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
        formatted += f"📄 Contract: {self.contract_address}\n"
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

    def send_slack_message(self, message: str) -> bool:
        """Send a message to Slack channel"""
        if not self.slack_enabled:
            return False
            
        try:
            response = self.slack_client.chat_postMessage(
                channel=self.slack_channel,
                text=message,
                unfurl_links=False,
                unfurl_media=False
            )
            
            if response['ok']:
                logger.info(f"Slack message sent successfully")
                return True
            else:
                logger.error(f"Failed to send Slack message: {response.get('error')}")
                return False
                
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return False
        except Exception as e:
            logger.error(f"Error sending Slack message: {e}")
            return False

    def handle_event(self, event: Dict[str, Any]):
        """Handle and print an event, optionally send to Slack"""
        try:
            # Print to console
            formatted_event = self.format_event(event)
            print(formatted_event)
            logger.info(f"Event processed: {event['event']}")
            
            # Send to Slack if enabled
            if self.slack_enabled:
                slack_message = self.format_slack_message(event)
                success = self.send_slack_message(slack_message)
                if success:
                    print(f"📱 Slack notification sent for {event['event']}")
                else:
                    print(f"❌ Failed to send Slack notification for {event['event']}")
                    
        except Exception as e:
            logger.error(f"Error processing event: {e}")
            print(f"Raw event: {event}")

    async def listen_for_events(self, from_block='latest'):
        """
        Listen for all Registry events using improved async pattern
        
        Args:
            from_block: Block to start listening from ('latest', 'earliest', or block number)
        """
        logger.info(f"Starting event listener from block: {from_block}")
        
        # Create event filters for all events
        event_filters = []
        
        try:
            # Create filters for each event type
            event_filters.append(
                self.contract.events.OperatorRegistered.create_filter(fromBlock=from_block)
            )
            event_filters.append(
                self.contract.events.OperatorSlashed.create_filter(fromBlock=from_block)
            )
            event_filters.append(
                self.contract.events.OperatorUnregistered.create_filter(fromBlock=from_block)
            )
            event_filters.append(
                self.contract.events.CollateralClaimed.create_filter(fromBlock=from_block)
            )
            event_filters.append(
                self.contract.events.CollateralAdded.create_filter(fromBlock=from_block)
            )
            event_filters.append(
                self.contract.events.OperatorOptedIn.create_filter(fromBlock=from_block)
            )
            event_filters.append(
                self.contract.events.OperatorOptedOut.create_filter(fromBlock=from_block)
            )
            
            logger.info("Event filters created successfully")
            print("\n🚀 Registry Event Monitor is now running...")
            print("📡 Listening for events... (Press Ctrl+C to stop)")
            print("="*80)
            
        except Exception as e:
            logger.error(f"Error creating event filters: {e}")
            return
        
        # Improved async polling pattern
        while True:
            try:
                # Process all filters concurrently
                tasks = []
                for event_filter in event_filters:
                    tasks.append(self._process_filter(event_filter))
                
                await asyncio.gather(*tasks, return_exceptions=True)
                await asyncio.sleep(2)  # Poll every 2 seconds
                
            except KeyboardInterrupt:
                logger.info("Stopping event monitor...")
                break
            except Exception as e:
                logger.error(f"Error polling events: {e}")
                await asyncio.sleep(5)  # Wait longer on error

    async def _process_filter(self, event_filter):
        """Process a single event filter"""
        try:
            for event in event_filter.get_new_entries():
                self.handle_event(event)
        except Exception as e:
            logger.error(f"Error processing filter: {e}")

    def get_historical_events(self, from_block=0, to_block='latest', max_events=100):
        """
        Get historical events from the contract using improved pattern
        
        Args:
            from_block: Starting block number
            to_block: Ending block number ('latest' for current block)  
            max_events: Maximum number of events to retrieve
        """
        logger.info(f"Fetching historical events from block {from_block} to {to_block}")
        
        try:
            all_events = []
            
            # Use contract event filters for historical data - more reliable approach
            event_types = [
                'OperatorRegistered', 'OperatorSlashed', 'OperatorUnregistered',
                'CollateralClaimed', 'CollateralAdded', 'OperatorOptedIn', 'OperatorOptedOut'
            ]
            
            for event_name in event_types:
                try:
                    event_filter = getattr(self.contract.events, event_name).create_filter(
                        fromBlock=from_block,
                        toBlock=to_block
                    )
                    
                    # Get all entries for this event type
                    events = event_filter.get_all_entries()
                    all_events.extend(events)
                    
                except Exception as e:
                    logger.warning(f"Error fetching {event_name} events: {e}")
                    continue
            
            # Limit results
            if len(all_events) > max_events:
                all_events = all_events[-max_events:]  # Get most recent events
            
            logger.info(f"Found {len(all_events)} historical events")
            
            # Sort events by block number and transaction index
            all_events.sort(key=lambda x: (x['blockNumber'], x['transactionIndex']))
            
            if all_events:
                print(f"\n📚 HISTORICAL EVENTS ({len(all_events)} found)")
                print("="*80)
                for event in all_events:
                    self.handle_event(event)
            else:
                print("\n📚 No historical events found")
                
        except Exception as e:
            logger.error(f"Error fetching historical events: {e}")

    async def monitor_with_reconnection(self, from_block='latest', reconnect_delay=30):
        """
        Monitor events with automatic reconnection on connection loss
        
        Args:
            from_block: Block to start listening from
            reconnect_delay: Seconds to wait before reconnecting
        """
        while True:
            try:
                if not self.web3.is_connected():
                    logger.warning("Connection lost, attempting to reconnect...")
                    await asyncio.sleep(reconnect_delay)
                    continue
                
                await self.listen_for_events(from_block)
                
            except Exception as e:
                logger.error(f"Connection error: {e}")
                logger.info(f"Retrying in {reconnect_delay} seconds...")
                await asyncio.sleep(reconnect_delay)


def main():
    """Main function to run the event monitor"""
    
    # Network configuration
    NETWORK = os.getenv('NETWORK', 'mainnet').lower()
    if NETWORK not in NETWORK_CONFIGS:
        print(f"❌ ERROR: Unsupported network '{NETWORK}'")
        print(f"Supported networks: {', '.join(NETWORK_CONFIGS.keys())}")
        return
    
    network_config = NETWORK_CONFIGS[NETWORK]
    
    # Configuration - All via environment variables
    RPC_URL = os.getenv('RPC_URL', network_config['default_rpc'])
    CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS', "0x2725F18FD97A99a3105C86331d253C431345CF30")
    
    # Slack configuration
    SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN', None)
    SLACK_CHANNEL = os.getenv('SLACK_CHANNEL', 'C091L7Q0ZJN')
    
    # Monitor behavior configuration via environment variables
    SHOW_HISTORY = os.getenv('SHOW_HISTORY', 'false').lower() in ('true', '1', 'yes', 'y')
    FROM_BLOCK = os.getenv('FROM_BLOCK', '')
    USE_RECONNECTION = os.getenv('USE_RECONNECTION', 'true').lower() in ('true', '1', 'yes', 'y')
    
    print("🔍 Registry Event Monitor")
    print("="*50)
    print(f"🌐 Network: {network_config['name']} (Chain ID: {network_config['chain_id']})")
    print(f"🔗 RPC URL: {RPC_URL}")
    print(f"📄 Contract: {CONTRACT_ADDRESS}")
    print(f"🔍 Block Explorer: {network_config['block_explorer']}")
    
    if CONTRACT_ADDRESS == "0x0000000000000000000000000000000000000000" or CONTRACT_ADDRESS == "0x2725F18FD97A99a3105C86331d253C431345CF30":
        print("❌ ERROR: Please set the CONTRACT_ADDRESS environment variable")
        print("Example: export CONTRACT_ADDRESS='0x1234567890123456789012345678901234567890'")
        return
    
    # Check Slack configuration
    if SLACK_BOT_TOKEN:
        print(f"📱 Slack notifications enabled for channel: {SLACK_CHANNEL}")
    else:
        print("📱 Slack notifications disabled (no bot token provided)")
        print("   To enable: export SLACK_BOT_TOKEN='xoxb-your-bot-token-here'")
        print("   To set channel: export SLACK_CHANNEL='your-channel-id'")
    
    # Display configuration
    print(f"📚 Show history: {SHOW_HISTORY}")
    print(f"🔄 Auto-reconnection: {USE_RECONNECTION}")
    if SHOW_HISTORY and FROM_BLOCK:
        print(f"📦 Starting from block: {FROM_BLOCK}")
    
    try:
        # Initialize the monitor with network and Slack support
        monitor = RegistryEventMonitor(
            RPC_URL, 
            CONTRACT_ADDRESS,
            network=NETWORK,
            slack_token=SLACK_BOT_TOKEN,
            slack_channel=SLACK_CHANNEL
        )
        
        # Test Slack connection if enabled
        if monitor.slack_enabled:
            test_message = f"🚀 Registry Event Monitor started on {network_config['name']} and ready to send notifications!"
            if monitor.send_slack_message(test_message):
                print("✅ Slack connection test successful")
            else:
                print("❌ Slack connection test failed")
        
        # Fetch historical events if requested
        if SHOW_HISTORY:
            if FROM_BLOCK:
                try:
                    from_block = int(FROM_BLOCK)
                except ValueError:
                    print(f"❌ Invalid FROM_BLOCK value: {FROM_BLOCK}. Using default.")
                    current_block = monitor.web3.eth.block_number
                    from_block = max(0, current_block - 1000)
            else:
                current_block = monitor.web3.eth.block_number
                from_block = max(0, current_block - 1000)
            
            print(f"📚 Fetching historical events from block {from_block}")
            monitor.get_historical_events(from_block=from_block, max_events=50)
        
        # Start monitoring
        if USE_RECONNECTION:
            print("🔄 Starting with automatic reconnection monitoring...")
            asyncio.run(monitor.monitor_with_reconnection())
        else:
            print("🎯 Starting basic event monitoring...")
            asyncio.run(monitor.listen_for_events())
        
    except KeyboardInterrupt:
        print("\n👋 Event monitor stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main() 