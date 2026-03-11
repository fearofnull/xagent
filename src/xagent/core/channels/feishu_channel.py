"""Feishu platform channel adapter.

This module implements the Channel interface for the Feishu (Lark) messaging
platform. It adapts the generic Channel interface to work with the existing
MessageSender implementation, translating parameters and handling errors.
"""

import asyncio
import inspect
import logging
from typing import Optional
from .base_channel import Channel

logger = logging.getLogger(__name__)


class FeishuChannel(Channel):
    """Feishu platform channel adapter.
    
    This class implements the Channel interface by wrapping the existing
    MessageSender instance. It translates the generic Channel parameters
    to MessageSender-specific parameters:
    
    - channel → chat_type (p2p or group)
    - user_id → chat_id (for p2p messages)
    - session_id → message_id (for group messages)
    
    The adapter ensures that all errors are caught and logged, returning
    False on failure without propagating exceptions.
    
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 8.1, 8.2, 8.3, 10.3
    """
    
    def __init__(self, message_sender):
        """Initialize with existing MessageSender instance.
        
        Args:
            message_sender: The MessageSender instance to wrap. This should
                be the existing MessageSender used by XAgent.
        """
        self.message_sender = message_sender
    
    async def send_message(
        self,
        receive_id: str,
        receive_id_type: str,
        content: str,
        message_id: Optional[str] = None
    ) -> bool:
        """Send message via MessageSender.
        
        This method translates the generic Channel parameters to MessageSender
        parameters and invokes the appropriate MessageSender method. It supports
        both synchronous and asynchronous MessageSender implementations.
        
        Args:
            receive_id: Receiver ID
            receive_id_type: ID type ("chat_id", "open_id", "user_id", "union_id")
            content: Message content
            message_id: Message ID for reply (optional)
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            if message_id:
                # Reply to message
                result = self.message_sender.reply_message(message_id, content)
            else:
                # Send new message with specified ID type
                result = self.message_sender.send_new_message(
                    receive_id=receive_id,
                    content=content,
                    receive_id_type=receive_id_type
                )
            
            # Check if the result is a coroutine (async method)
            # If so, await it to get the actual boolean result
            if inspect.iscoroutine(result):
                success = await result
            else:
                success = result
            
            if success:
                logger.info(
                    f"Message sent successfully via Feishu: "
                    f"receive_id_type={receive_id_type}, "
                    f"receive_id={receive_id[:20] if len(receive_id) > 20 else receive_id}..."
                )
            else:
                logger.warning(
                    f"Failed to send message via Feishu: "
                    f"receive_id_type={receive_id_type}, "
                    f"receive_id={receive_id[:20] if len(receive_id) > 20 else receive_id}..."
                )
            
            return success
            
        except Exception as e:
            logger.error(
                f"Error sending message via Feishu: {e}",
                exc_info=True
            )
            return False
