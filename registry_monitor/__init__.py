"""Registry Event Monitor - Modular Implementation"""

__version__ = "2.0.0"
__author__ = "Registry Event Monitor Team"
__description__ = "Modular Ethereum Registry contract event monitoring system"

# Main exports
from .cli import main
from .config import settings
from .core import Web3Client, RegistryContract, EventProcessor
from .notifications import NotificationManager, ConsoleNotifier, SlackNotifier
from .monitor import EventMonitor, ReconnectionHandler
from .data import EventFetcher, InMemoryEventStore

__all__ = [
    'main',
    'settings', 
    'Web3Client',
    'RegistryContract',
    'EventProcessor',
    'NotificationManager',
    'ConsoleNotifier', 
    'SlackNotifier',
    'EventMonitor',
    'ReconnectionHandler',
    'EventFetcher',
    'InMemoryEventStore'
] 