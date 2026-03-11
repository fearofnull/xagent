"""Channel manager for routing messages to different messaging platforms.

This module implements the ChannelManager class that manages multiple Channel
instances and routes messages to the appropriate channel based on channel name.
It provides a centralized interface for message delivery across different
messaging platforms.
"""

import logging
from typing import Dict, Optional
from .base_channel import Channel

logger = logging.getLogger(__name__)


class ChannelManager:
    """Manages multiple messaging channels.
    
    This class maintains a registry of Channel instances and routes messages
    to the appropriate channel based on the channel name. It provides a
    centralized interface for managing and using multiple messaging platforms
    simultaneously.
    
    The ChannelManager supports:
    - Dynamic channel registration at runtime
    - Channel lookup by name
    - Message routing to registered channels
    - Error handling for missing channels
    - Async message sending operations
    
    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 8.4, 10.2
    """
    
    def __init__(self):
        """Initialize the channel manager with an empty registry."""
        self._channels: Dict[str, Channel] = {}
        logger.info("ChannelManager initialized")
    
    def register_channel(self, name: str, channel: Channel) -> None:
        """Register a channel with the manager.
        
        This method adds a Channel instance to the registry, making it
        available for message routing. Channels can be registered at any
        time during runtime, including after initialization.
        
        Args:
            name: Channel name identifier (e.g., "feishu", "slack", "teams").
                This name will be used to route messages to this channel.
            channel: Channel instance implementing the Channel interface.
        
        Example:
            >>> manager = ChannelManager()
            >>> feishu = FeishuChannel(message_sender)
            >>> manager.register_channel("feishu", feishu)
        """
        self._channels[name] = channel
        logger.info(f"Registered channel: {name}")
    
    def get_channel(self, name: str) -> Channel:
        """Get a channel by name.
        
        This method retrieves a registered Channel instance by its name.
        If the channel is not found, it raises a KeyError.
        
        Args:
            name: Channel name identifier
            
        Returns:
            Channel instance associated with the given name
            
        Raises:
            KeyError: If the channel name is not registered
        
        Example:
            >>> manager = ChannelManager()
            >>> manager.register_channel("feishu", feishu_channel)
            >>> channel = manager.get_channel("feishu")
        """
        if name not in self._channels:
            raise KeyError(f"Channel not registered: {name}")
        return self._channels[name]
    
    async def send_message(
        self,
        channel: str,
        content: str,
        mode: str = "final",
        chat_id: Optional[str] = None,
        user_id: Optional[str] = None,
        message_id: Optional[str] = None
    ) -> bool:
        """Send a message through a specific channel.
        
        This method routes a message to the appropriate Channel instance
        based on the channel name. It supports multiple ID types with priority:
        chat_id > user_id
        
        Args:
            channel: Channel platform name (e.g., "feishu", "slack")
            content: Message content to send
            mode: Delivery mode (reserved for future use)
            chat_id: Chat ID (preferred, works for both private and group chats)
            user_id: User ID (open_id, used as fallback when chat_id is not available)
            message_id: Message ID for reply (optional)
            
        Returns:
            True if the message was sent successfully, False otherwise.
            Returns False if the channel is not registered or if any
            error occurs during message sending.
        
        Raises:
            ValueError: If both chat_id and user_id are None
        
        Example:
            >>> manager = ChannelManager()
            >>> manager.register_channel("feishu", feishu_channel)
            >>> # Send with chat_id (preferred)
            >>> success = await manager.send_message(
            ...     channel="feishu",
            ...     content="Hello!",
            ...     chat_id="oc_xxx",
            ...     mode="normal"
            ... )
            >>> # Send with user_id (fallback)
            >>> success = await manager.send_message(
            ...     channel="feishu",
            ...     content="Hello!",
            ...     user_id="ou_xxx",
            ...     mode="normal"
            ... )
        """
        try:
            # Determine receive_id and receive_id_type
            # Priority: chat_id > user_id
            if chat_id:
                receive_id = chat_id
                receive_id_type = "chat_id"
            elif user_id:
                receive_id = user_id
                receive_id_type = "open_id"
            else:
                raise ValueError("必须提供 chat_id 或 user_id")
            
            # Get the channel instance by name
            channel_instance = self.get_channel(channel)
            
            logger.info(
                f"Routing message: channel={channel}, "
                f"receive_id_type={receive_id_type}, "
                f"receive_id={receive_id[:20] if len(receive_id) > 20 else receive_id}"
            )
            
            # Route the message to the channel
            return await channel_instance.send_message(
                receive_id=receive_id,
                receive_id_type=receive_id_type,
                content=content,
                message_id=message_id
            )
        except ValueError as e:
            # Invalid parameters
            logger.error(f"Invalid parameters: {e}")
            return False
        except KeyError as e:
            # Channel not found in registry
            logger.error(f"Channel lookup failed: {e}")
            return False
        except Exception as e:
            # Any other error during message sending
            logger.error(f"Error sending message through channel manager: {e}", exc_info=True)
            return False
