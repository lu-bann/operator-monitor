"""Abstract base class for notifications"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class NotifierInterface(ABC):
    """Abstract base class for notification systems"""
    
    @abstractmethod
    def send(self, message: str, event: Dict[str, Any] = None) -> bool:
        """
        Send a notification message
        
        Args:
            message: The formatted message to send
            event: Optional event data for context
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test the notification service connection
        
        Returns:
            bool: True if connection is working
        """
        pass
    
    def get_name(self) -> str:
        """Get the name of this notifier"""
        return self.__class__.__name__ 