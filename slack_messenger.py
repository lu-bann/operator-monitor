#!/usr/bin/env python3
"""
Basic Slack Message Sender

Simple script to send messages to Slack channels.
Set SLACK_BOT_TOKEN environment variable or edit the script directly.
"""

import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Configuration - Set your bot token here or use environment variable
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN', 'your-bot-token-here')

def send_slack_message(channel, message):
    """Send a message to a Slack channel."""
    try:
        client = WebClient(token=SLACK_BOT_TOKEN)
        response = client.chat_postMessage(
            channel=channel,
            text=message
        )
        
        if response['ok']:
            print(f"✅ Message sent to {channel}")
            return True
        else:
            print(f"❌ Failed to send message: {response.get('error')}")
            return False
            
    except SlackApiError as e:
        print(f"❌ Slack API error: {e.response['error']}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    # Example usage
    channel = "C091L7Q0ZJN"  # Change this to your channel
    message = "Hello from luban-bot!"  # Change this to your message
    
    # Check if token is set
    if SLACK_BOT_TOKEN == 'your-bot-token-here':
        print("❌ Please set your SLACK_BOT_TOKEN environment variable or edit the script")
        print("   export SLACK_BOT_TOKEN='xoxb-your-bot-token-here'")
    else:
        send_slack_message(channel, message) 