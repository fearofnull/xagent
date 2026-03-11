"""Abstract base class for messaging platform channels.

This module defines the Channel interface that all messaging platform adapters
must implement. The interface provides a consistent API for sending messages
across different platforms while maintaining platform-agnostic abstractions.
"""

from abc import ABC, abstractmethod
from typing import Optional


class Channel(ABC):
    """Abstract base class for messaging platform channels.
    
    This interface defines the contract that all messaging platform adapters
    must implement. It provides a platform-agnostic API for sending messages
    with support for different ID types (chat_id, open_id, user_id, union_id),
    message replies, and flexible delivery options.
    
    Implementations should:
    - Support multiple receive_id_type values for flexibility
    - Handle message_id appropriately for reply functionality
    - Return True on successful message delivery, False on failure
    - Log errors appropriately without propagating exceptions
    - Support async operations for non-blocking message delivery
    """
    
    @abstractmethod
    async def send_message(
        self,
        receive_id: str,
        receive_id_type: str,
        content: str,
        message_id: Optional[str] = None
    ) -> bool:
        """Send a message through this channel.
        
        This method sends a message to a user or group through the messaging
        platform. The implementation should handle different ID types and
        support both new messages and replies.
        
        Args:
            receive_id: Receiver identifier. The meaning depends on receive_id_type:
                - chat_id: Chat/conversation ID (works for both private and group)
                - open_id: User's Open ID (application-level identifier)
                - user_id: User ID (tenant-level identifier)
                - union_id: Union ID (cross-application identifier)
            receive_id_type: Type of the receive_id. Supported values:
                "chat_id", "open_id", "user_id", "union_id"
            content: The message content to send. Format and length restrictions
                depend on the platform implementation.
            message_id: Optional message ID for replying to a specific message.
                If provided, the platform should send this as a reply/thread
                message. If None, sends as a new message.
        
        Returns:
            bool: True if the message was sent successfully, False if the
                message failed to send for any reason (network error, invalid
                parameters, platform rejection, etc.).
        
        Raises:
            This method should NOT raise exceptions. All errors should be caught,
            logged appropriately, and indicated by returning False.
        
        Example:
            >>> channel = SomePlatformChannel(...)
            >>> # Send new message with chat_id
            >>> success = await channel.send_message(
            ...     receive_id="oc_xxx",
            ...     receive_id_type="chat_id",
            ...     content="Hello, world!"
            ... )
            >>> # Reply to a message
            >>> success = await channel.send_message(
            ...     receive_id="oc_xxx",
            ...     receive_id_type="chat_id",
            ...     content="Reply text",
            ...     message_id="om_yyy"
            ... )
            >>> # Send with open_id (fallback)
            >>> success = await channel.send_message(
            ...     receive_id="ou_xxx",
            ...     receive_id_type="open_id",
            ...     content="Hello!"
            ... )
        """
        pass
