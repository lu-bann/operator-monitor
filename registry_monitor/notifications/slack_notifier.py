"""Slack integration notifier"""

import logging
from typing import Dict, Any
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from .base_notifier import NotifierInterface

logger = logging.getLogger(__name__)


class SlackNotifier(NotifierInterface):
    """Sends notifications to Slack channels"""
    
    def __init__(self, token: str, channel: str):
        """
        Initialize Slack notifier
        
        Args:
            token: Slack bot token
            channel: Slack channel ID or name
        """
        self.token = token
        self.channel = channel
        self.client = WebClient(token=token)
        
        logger.info(f"Slack notifier initialized for channel: {channel}")
    
    def send(self, message: str, event: Dict[str, Any] = None) -> bool:
        """Send message to Slack channel"""
        try:
            response = self.client.chat_postMessage(
                channel=self.channel,
                text=message,
                unfurl_links=False,
                unfurl_media=False
            )
            
            if response['ok']:
                logger.info("Slack message sent successfully")
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
    
    def test_connection(self) -> bool:
        """Test Slack connection"""
        try:
            # Test with a simple message
            test_message = "🧪 Slack connection test - Registry Event Monitor"
            return self.send(test_message)
        except Exception as e:
            logger.error(f"Slack connection test failed: {e}")
            return False
    
    def format_slack_message(self, event: Dict[str, Any], network_config: dict) -> str:
        """Format an event specifically for Slack (moved from EventProcessor)"""
        # This method can be used by the notification manager
        # to format messages specifically for Slack if needed
        pass 