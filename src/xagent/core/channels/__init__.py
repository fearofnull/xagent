"""Channel abstraction layer for messaging platforms"""

from .base_channel import Channel
from .feishu_channel import FeishuChannel
from .channel_manager import ChannelManager

__all__ = ["Channel", "FeishuChannel", "ChannelManager"]
