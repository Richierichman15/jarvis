"""Utility functions for Discord bot."""
from .message_utils import (
    split_message_intelligently,
    send_long_message,
    send_error_webhook
)

__all__ = [
    'split_message_intelligently',
    'send_long_message',
    'send_error_webhook'
]

