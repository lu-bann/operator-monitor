"""Multi-channel notification orchestration"""

import logging
from typing import List, Dict, Any
from .base_notifier import NotifierInterface

logger = logging.getLogger(__name__)


class NotificationManager:
    """Manages multiple notification channels with error handling and fallbacks"""
    
    def __init__(self):
        """Initialize notification manager"""
        self.notifiers: List[NotifierInterface] = []
        self.fallback_notifiers: List[NotifierInterface] = []
    
    def add_notifier(self, notifier: NotifierInterface, is_fallback: bool = False):
        """
        Add a notifier to the manager
        
        Args:
            notifier: The notifier instance to add
            is_fallback: Whether this is a fallback notifier
        """
        if is_fallback:
            self.fallback_notifiers.append(notifier)
            logger.info(f"Added fallback notifier: {notifier.get_name()}")
        else:
            self.notifiers.append(notifier)
            logger.info(f"Added primary notifier: {notifier.get_name()}")
    
    def send_notification(self, message: str, event: Dict[str, Any] = None) -> bool:
        """
        Send notification through all configured channels
        
        Args:
            message: The message to send
            event: Optional event data for context
            
        Returns:
            bool: True if at least one notifier succeeded
        """
        success_count = 0
        
        # Try primary notifiers first
        for notifier in self.notifiers:
            try:
                if notifier.send(message, event):
                    success_count += 1
                    logger.debug(f"Notification sent via {notifier.get_name()}")
                else:
                    logger.warning(f"Failed to send via {notifier.get_name()}")
            except Exception as e:
                logger.error(f"Error with notifier {notifier.get_name()}: {e}")
        
        # If all primary notifiers failed, try fallbacks
        if success_count == 0 and self.fallback_notifiers:
            logger.warning("All primary notifiers failed, trying fallbacks...")
            
            for notifier in self.fallback_notifiers:
                try:
                    if notifier.send(message, event):
                        success_count += 1
                        logger.info(f"Fallback notification sent via {notifier.get_name()}")
                        break  # Only need one fallback to succeed
                except Exception as e:
                    logger.error(f"Error with fallback notifier {notifier.get_name()}: {e}")
        
        if success_count > 0:
            logger.info(f"Notification sent successfully via {success_count} channel(s)")
            return True
        else:
            logger.error("All notification channels failed")
            return False
    
    def test_all_connections(self) -> Dict[str, bool]:
        """Test all configured notifiers"""
        results = {}
        
        # Test primary notifiers
        for notifier in self.notifiers:
            try:
                results[notifier.get_name()] = notifier.test_connection()
            except Exception as e:
                logger.error(f"Error testing {notifier.get_name()}: {e}")
                results[notifier.get_name()] = False
        
        # Test fallback notifiers
        for notifier in self.fallback_notifiers:
            try:
                results[f"{notifier.get_name()} (fallback)"] = notifier.test_connection()
            except Exception as e:
                logger.error(f"Error testing fallback {notifier.get_name()}: {e}")
                results[f"{notifier.get_name()} (fallback)"] = False
        
        return results
    
    def get_active_notifiers(self) -> List[str]:
        """Get list of active notifier names"""
        active = []
        active.extend([n.get_name() for n in self.notifiers])
        active.extend([f"{n.get_name()} (fallback)" for n in self.fallback_notifiers])
        return active 