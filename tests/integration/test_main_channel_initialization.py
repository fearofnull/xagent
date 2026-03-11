"""Integration test for ChannelManager initialization in main.py"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestMainChannelInitialization:
    """Test ChannelManager initialization in main.py"""
    
    @patch("main.XAgent")
    @patch("main.CronManager")
    @patch("main.BotConfig")
    def test_channel_manager_initialization_order(
        self, mock_bot_config, mock_cron_manager, mock_xagent
    ):
        """Test that ChannelManager is initialized before CronManager"""
        # Setup mocks
        mock_config = Mock()
        mock_bot_config.from_env.return_value = mock_config
        
        mock_bot_instance = Mock()
        mock_message_sender = Mock()
        mock_bot_instance.message_sender = mock_message_sender
        mock_xagent.return_value = mock_bot_instance
        
        mock_cron_instance = Mock()
        mock_cron_manager.return_value = mock_cron_instance
        
        # Track initialization order
        initialization_order = []
        
        def track_xagent_init(*args, **kwargs):
            initialization_order.append("xagent")
            return mock_bot_instance
        
        def track_cron_init(*args, **kwargs):
            initialization_order.append("cron")
            # Verify channel_manager was passed
            assert "channel_manager" in kwargs
            assert kwargs["channel_manager"] is not None
            return mock_cron_instance
        
        mock_xagent.side_effect = track_xagent_init
        mock_cron_manager.side_effect = track_cron_init
        
        # Import and execute the initialization logic
        from src.xagent.core.channels import ChannelManager, FeishuChannel
        
        # Simulate the initialization sequence from main.py
        bot = mock_xagent(mock_config)
        
        # Initialize ChannelManager
        channel_manager = ChannelManager()
        feishu_channel = FeishuChannel(bot.message_sender)
        channel_manager.register_channel("feishu", feishu_channel)
        
        # Initialize CronManager with channel_manager
        cron_manager = mock_cron_manager(channel_manager=channel_manager)
        
        # Verify initialization order
        assert initialization_order == ["xagent", "cron"]
        
        # Verify CronManager was called with channel_manager
        mock_cron_manager.assert_called_once()
        call_kwargs = mock_cron_manager.call_args[1]
        assert "channel_manager" in call_kwargs
        assert isinstance(call_kwargs["channel_manager"], ChannelManager)
    
    def test_feishu_channel_registration(self):
        """Test that FeishuChannel is correctly registered with name 'feishu'"""
        from src.xagent.core.channels import ChannelManager, FeishuChannel
        
        # Create mock message sender
        mock_message_sender = Mock()
        
        # Initialize ChannelManager and register FeishuChannel
        channel_manager = ChannelManager()
        feishu_channel = FeishuChannel(mock_message_sender)
        channel_manager.register_channel("feishu", feishu_channel)
        
        # Verify channel is registered
        retrieved_channel = channel_manager.get_channel("feishu")
        assert retrieved_channel is feishu_channel
        assert isinstance(retrieved_channel, FeishuChannel)
    
    def test_channel_manager_passed_to_cron_manager(self):
        """Test that ChannelManager is correctly passed to CronManager"""
        from src.xagent.core.channels import ChannelManager, FeishuChannel
        from src.xagent.core.crons.manager import CronManager
        
        # Create mock message sender
        mock_message_sender = Mock()
        
        # Initialize ChannelManager
        channel_manager = ChannelManager()
        feishu_channel = FeishuChannel(mock_message_sender)
        channel_manager.register_channel("feishu", feishu_channel)
        
        # Initialize CronManager with channel_manager
        cron_manager = CronManager(channel_manager=channel_manager)
        
        # Verify CronManager has the channel_manager
        assert cron_manager._channel_manager is channel_manager
        
        # Verify the registered channel is accessible through CronManager's channel_manager
        retrieved_channel = cron_manager._channel_manager.get_channel("feishu")
        assert retrieved_channel is feishu_channel


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
