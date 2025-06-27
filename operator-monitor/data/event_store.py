"""Optional event persistence interface"""

import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class EventStoreInterface(ABC):
    """Abstract interface for event storage"""
    
    @abstractmethod
    def store_event(self, event: Dict[str, Any]) -> bool:
        """Store a single event"""
        pass
    
    @abstractmethod
    def store_events(self, events: List[Dict[str, Any]]) -> int:
        """Store multiple events, returns count of successful stores"""
        pass
    
    @abstractmethod
    def get_events(self, from_block: int = 0, to_block: Optional[int] = None, 
                  event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve stored events with optional filtering"""
        pass
    
    @abstractmethod
    def get_latest_block(self) -> Optional[int]:
        """Get the latest block number we have events for"""
        pass


class InMemoryEventStore(EventStoreInterface):
    """Simple in-memory event storage for caching"""
    
    def __init__(self, max_events: int = 10000):
        """
        Initialize in-memory store
        
        Args:
            max_events: Maximum number of events to keep in memory
        """
        self.events: List[Dict[str, Any]] = []
        self.max_events = max_events
        logger.info(f"In-memory event store initialized (max {max_events} events)")
    
    def store_event(self, event: Dict[str, Any]) -> bool:
        """Store a single event in memory"""
        try:
            self.events.append(event)
            
            # Keep only the most recent events
            if len(self.events) > self.max_events:
                self.events = self.events[-self.max_events:]
            
            return True
        except Exception as e:
            logger.error(f"Error storing event in memory: {e}")
            return False
    
    def store_events(self, events: List[Dict[str, Any]]) -> int:
        """Store multiple events in memory"""
        success_count = 0
        for event in events:
            if self.store_event(event):
                success_count += 1
        
        logger.info(f"Stored {success_count}/{len(events)} events in memory")
        return success_count
    
    def get_events(self, from_block: int = 0, to_block: Optional[int] = None, 
                  event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve events from memory with filtering"""
        filtered_events = []
        
        for event in self.events:
            # Block range filter
            if event['blockNumber'] < from_block:
                continue
            if to_block is not None and event['blockNumber'] > to_block:
                continue
            
            # Event type filter
            if event_type is not None and event['event'] != event_type:
                continue
            
            filtered_events.append(event)
        
        return filtered_events
    
    def get_latest_block(self) -> Optional[int]:
        """Get the latest block number in memory"""
        if not self.events:
            return None
        
        return max(event['blockNumber'] for event in self.events)
    
    def clear(self):
        """Clear all stored events"""
        self.events.clear()
        logger.info("In-memory event store cleared")


class NullEventStore(EventStoreInterface):
    """No-op event store for when persistence is disabled"""
    
    def store_event(self, event: Dict[str, Any]) -> bool:
        return True
    
    def store_events(self, events: List[Dict[str, Any]]) -> int:
        return len(events)
    
    def get_events(self, from_block: int = 0, to_block: Optional[int] = None, 
                  event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        return []
    
    def get_latest_block(self) -> Optional[int]:
        return None 