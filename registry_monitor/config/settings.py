"""Environment variable handling and settings"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings loaded from environment variables"""
    
    def __init__(self):
        self.network = os.getenv('NETWORK', 'mainnet').lower()
        self.rpc_url = os.getenv('RPC_URL')
        self.registry_contract_address = os.getenv('REGISTRY_CONTRACT_ADDRESS')
        
        # TaiyiRegistryCoordinator contract address (optional)
        self.taiyi_contract_address = os.getenv('TAIYI_CONTRACT_ADDRESS')
        
        # TaiyiEscrow contract address (optional)
        self.taiyi_escrow_contract_address = os.getenv('TAIYI_ESCROW_CONTRACT_ADDRESS')
        
        # Slack configuration
        self.slack_bot_token = os.getenv('SLACK_BOT_TOKEN')
        self.slack_channel = os.getenv('SLACK_CHANNEL', 'C091L7Q0ZJN')
        
        # Monitor behavior configuration
        self.show_history = os.getenv('SHOW_HISTORY', 'false').lower() in ('true', '1', 'yes', 'y')
        self.from_block = os.getenv('FROM_BLOCK', '')
        self.use_reconnection = os.getenv('USE_RECONNECTION', 'true').lower() in ('true', '1', 'yes', 'y')
        self.chunk_size = int(os.getenv('CHUNK_SIZE', '50000'))
        
    def validate(self):
        """Validate required settings"""
        if not self.registry_contract_address or self.registry_contract_address == "0x0000000000000000000000000000000000000000":
            raise ValueError("REGISTRY_CONTRACT_ADDRESS environment variable is required")
        
        from .networks import NETWORK_CONFIGS
        if self.network not in NETWORK_CONFIGS:
            raise ValueError(f"Unsupported network '{self.network}'. Supported: {', '.join(NETWORK_CONFIGS.keys())}")


# Global settings instance
settings = Settings() 