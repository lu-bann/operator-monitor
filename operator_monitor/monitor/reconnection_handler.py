"""Connection management and reconnection logic"""

import asyncio
import logging
from typing import Optional, Dict, Any
from .event_monitor import EventMonitor

logger = logging.getLogger(__name__)


class ReconnectionHandler:
    """Handles connection management and automatic reconnection"""
    
    def __init__(self, event_monitor: EventMonitor, 
                 reconnect_delay: int = 30, max_reconnection_attempts: int = 0):
        """
        Initialize reconnection handler
        
        Args:
            event_monitor: EventMonitor instance
            reconnect_delay: Seconds to wait before reconnecting
            max_reconnection_attempts: Maximum reconnection attempts (0 = infinite)
        """
        self.event_monitor = event_monitor
        self.reconnect_delay = reconnect_delay
        self.max_reconnection_attempts = max_reconnection_attempts
        self.reconnection_count = 0
        
        logger.info(f"Reconnection handler initialized (delay: {reconnect_delay}s)")
    
    async def monitor_with_reconnection(self, from_block='latest', poll_interval: int = 2):
        """
        Monitor events with automatic reconnection on connection loss
        
        Args:
            from_block: Block to start listening from
            poll_interval: Seconds between event polls
        """
        logger.info("Starting monitor with automatic reconnection")
        
        while True:
            try:
                # Check connection health
                if not self.event_monitor.web3_client.is_connected():
                    logger.warning("Connection lost, attempting to reconnect...")
                    
                    if not await self._attempt_reconnection():
                        continue  # Reconnection failed, try again
                    
                    # Reset reconnection count on successful connection
                    self.reconnection_count = 0
                
                # Start monitoring
                await self.event_monitor.listen_for_events(from_block, poll_interval)
                
            except KeyboardInterrupt:
                logger.info("Monitor stopped by user")
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                
                if not await self._attempt_reconnection():
                    logger.error("Max reconnection attempts reached, exiting")
                    break
    
    async def _attempt_reconnection(self) -> bool:
        """
        Attempt to reconnect with exponential backoff
        
        Returns:
            bool: True if reconnection successful
        """
        self.reconnection_count += 1
        
        # Check if we've exceeded max attempts
        if (self.max_reconnection_attempts > 0 and 
            self.reconnection_count > self.max_reconnection_attempts):
            logger.error(f"Maximum reconnection attempts ({self.max_reconnection_attempts}) exceeded")
            return False
        
        # Calculate backoff delay (exponential with maximum)
        backoff_delay = min(self.reconnect_delay * (2 ** (self.reconnection_count - 1)), 300)
        
        logger.info(f"Reconnection attempt {self.reconnection_count}, waiting {backoff_delay}s...")
        await asyncio.sleep(backoff_delay)
        
        try:
            # Test connection
            health = self.event_monitor.web3_client.health_check()
            if health['connected']:
                logger.info("Reconnection successful")
                return True
            else:
                logger.warning("Reconnection failed, connection still unhealthy")
                return False
                
        except Exception as e:
            logger.error(f"Reconnection attempt failed: {e}")
            return False
    
    def get_reconnection_stats(self) -> Dict[str, Any]:
        """Get reconnection statistics"""
        return {
            'reconnection_count': self.reconnection_count,
            'max_attempts': self.max_reconnection_attempts,
            'reconnect_delay': self.reconnect_delay
        } 