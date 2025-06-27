"""Console output notifier"""

import logging
from typing import Dict, Any
from .base_notifier import NotifierInterface

logger = logging.getLogger(__name__)


class ConsoleNotifier(NotifierInterface):
    """Outputs notifications to console/stdout"""
    
    def __init__(self, verbose: bool = True):
        """
        Initialize console notifier
        
        Args:
            verbose: Whether to include detailed logging
        """
        self.verbose = verbose
    
    def send(self, message: str, event: Dict[str, Any] = None) -> bool:
        """Send message to console"""
        try:
            print(message)
            
            if self.verbose and event:
                logger.info(f"Event processed: {event['event']}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending console notification: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test console output (always available)"""
        try:
            print("✅ Console notifier connection test successful")
            return True
        except Exception as e:
            logger.error(f"Console notifier test failed: {e}")
            return False 