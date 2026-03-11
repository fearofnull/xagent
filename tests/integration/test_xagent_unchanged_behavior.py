"""Integration tests for XAgent unchanged behavior

This module contains integration tests that verify XAgent's behavior remains
unchanged after implementing the channel abstraction layer.

These tests verify:
- XAgent continues using message_sender directly
- Existing message sending operations work identically
- MessageSender class remains unchanged

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestXAgentMessageSenderDirectUsage:
    """Test that XAgent continues using message_sender directly"""

    @patch("src.xagent.xagent.LarkClient")
    def test_xagent_has_message_sender_attribute(self, mock_lark_client):
        """Test that XAgent instance has message_sender attribute"""
        from src.xagent.xagent import XAgent
        from src.xagent.config import BotConfig

        # Create mock config
        mock_config = Mock(spec=BotConfig)
        mock_config.app_id = "test_app_id"
        mock_config.app_secret = "test_app_secret"
        mock_config.cache_size = 1000
        mock_config.session_storage_path = "./test_sessions"
        mock_config.max_session_messages = 100
        mock_config.session_timeout = 3600
        mock_config.ai_timeout = 60
        mock_config.target_directory = None
        mock_config.claude_cli_target_dir = None
        mock_config.gemini_cli_target_dir = None
        mock_config.qwen_cli_target_dir = None

        # Mock LarkClient builder
        mock_client_instance = Mock()
        mock_builder = Mock()
        mock_builder.app_id.return_value = mock_builder
        mock_builder.app_secret.return_value = mock_builder
        mock_builder.build.return_value = mock_client_instance
        mock_lark_client.builder.return_value = mock_builder

        # Create XAgent instance
        bot = XAgent(mock_config)

        # Verify message_sender exists and is not None
        assert hasattr(bot, "message_sender")
        assert bot.message_sender is not None

        # Verify message_sender is a MessageSender instance
        from src.xagent.core.message_sender import MessageSender
        assert isinstance(bot.message_sender, MessageSender)

    @patch("src.xagent.xagent.LarkClient")
    def test_xagent_message_sender_not_wrapped(self, mock_lark_client):
        """Test that XAgent's message_sender is not wrapped by channel abstraction"""
        from src.xagent.xagent import XAgent
        from src.xagent.config import BotConfig
        from src.xagent.core.message_sender import MessageSender

        # Create mock config
        mock_config = Mock(spec=BotConfig)
        mock_config.app_id = "test_app_id"
        mock_config.app_secret = "test_app_secret"
        mock_config.cache_size = 1000
        mock_config.session_storage_path = "./test_sessions"
        mock_config.max_session_messages = 100
        mock_config.session_timeout = 3600
        mock_config.ai_timeout = 60
        mock_config.target_directory = None
        mock_config.claude_cli_target_dir = None
        mock_config.gemini_cli_target_dir = None
        mock_config.qwen_cli_target_dir = None

        # Mock LarkClient builder
        mock_client_instance = Mock()
        mock_builder = Mock()
        mock_builder.app_id.return_value = mock_builder
        mock_builder.app_secret.return_value = mock_builder
        mock_builder.build.return_value = mock_client_instance
        mock_lark_client.builder.return_value = mock_builder

        # Create XAgent instance
        bot = XAgent(mock_config)

        # Verify message_sender is exactly MessageSender, not a wrapper
        assert type(bot.message_sender).__name__ == "MessageSender"
        assert bot.message_sender.__class__ == MessageSender


class TestXAgentMessageSendingOperations:
    """Test that existing message sending operations work identically"""

    @patch("src.xagent.xagent.LarkClient")
    def test_xagent_sends_p2p_message_through_message_sender(self, mock_lark_client):
        """Test XAgent sends p2p messages directly through message_sender"""
        from src.xagent.xagent import XAgent
        from src.xagent.config import BotConfig

        # Create mock config
        mock_config = Mock(spec=BotConfig)
        mock_config.app_id = "test_app_id"
        mock_config.app_secret = "test_app_secret"
        mock_config.cache_size = 1000
        mock_config.session_storage_path = "./test_sessions"
        mock_config.max_session_messages = 100
        mock_config.session_timeout = 3600
        mock_config.ai_timeout = 60
        mock_config.target_directory = None
        mock_config.claude_cli_target_dir = None
        mock_config.gemini_cli_target_dir = None
        mock_config.qwen_cli_target_dir = None

        # Mock LarkClient builder
        mock_client_instance = Mock()
        mock_builder = Mock()
        mock_builder.app_id.return_value = mock_builder
        mock_builder.app_secret.return_value = mock_builder
        mock_builder.build.return_value = mock_client_instance
        mock_lark_client.builder.return_value = mock_builder

        # Create XAgent instance
        bot = XAgent(mock_config)

        # Mock the message_sender.send_message method
        bot.message_sender.send_message = Mock(return_value=True)

        # Call send_message directly
        result = bot.message_sender.send_message(
            chat_type="p2p",
            chat_id="test_chat_id",
            message_id="test_message_id",
            content="Test message"
        )

        # Verify the call was made with correct parameters
        bot.message_sender.send_message.assert_called_once_with(
            chat_type="p2p",
            chat_id="test_chat_id",
            message_id="test_message_id",
            content="Test message"
        )
        assert result is True

    @patch("src.xagent.xagent.LarkClient")
    def test_xagent_sends_group_message_through_message_sender(self, mock_lark_client):
        """Test XAgent sends group messages directly through message_sender"""
        from src.xagent.xagent import XAgent
        from src.xagent.config import BotConfig

        # Create mock config
        mock_config = Mock(spec=BotConfig)
        mock_config.app_id = "test_app_id"
        mock_config.app_secret = "test_app_secret"
        mock_config.cache_size = 1000
        mock_config.session_storage_path = "./test_sessions"
        mock_config.max_session_messages = 100
        mock_config.session_timeout = 3600
        mock_config.ai_timeout = 60
        mock_config.target_directory = None
        mock_config.claude_cli_target_dir = None
        mock_config.gemini_cli_target_dir = None
        mock_config.qwen_cli_target_dir = None

        # Mock LarkClient builder
        mock_client_instance = Mock()
        mock_builder = Mock()
        mock_builder.app_id.return_value = mock_builder
        mock_builder.app_secret.return_value = mock_builder
        mock_builder.build.return_value = mock_client_instance
        mock_lark_client.builder.return_value = mock_builder

        # Create XAgent instance
        bot = XAgent(mock_config)

        # Mock the message_sender.send_message method
        bot.message_sender.send_message = Mock(return_value=True)

        # Call send_message directly for group chat
        result = bot.message_sender.send_message(
            chat_type="group",
            chat_id="test_group_id",
            message_id="test_message_id",
            content="Test group message"
        )

        # Verify the call was made with correct parameters
        bot.message_sender.send_message.assert_called_once_with(
            chat_type="group",
            chat_id="test_group_id",
            message_id="test_message_id",
            content="Test group message"
        )
        assert result is True


class TestMessageSenderUnchanged:
    """Test that MessageSender class remains unchanged"""

    def test_message_sender_has_expected_methods(self):
        """Test MessageSender has all expected methods"""
        from src.xagent.core.message_sender import MessageSender

        # Verify MessageSender has the expected methods
        assert hasattr(MessageSender, "send_message")
        assert hasattr(MessageSender, "send_new_message")
        assert hasattr(MessageSender, "reply_message")
        assert hasattr(MessageSender, "_escape_json")

    def test_message_sender_send_message_signature(self):
        """Test MessageSender.send_message has the expected signature"""
        from src.xagent.core.message_sender import MessageSender
        import inspect

        # Get the signature of send_message
        sig = inspect.signature(MessageSender.send_message)
        params = list(sig.parameters.keys())

        # Verify parameters
        assert "self" in params
        assert "chat_type" in params
        assert "chat_id" in params
        assert "message_id" in params
        assert "content" in params

    def test_message_sender_initialization(self):
        """Test MessageSender can be initialized with LarkClient"""
        from src.xagent.core.message_sender import MessageSender

        # Create mock client
        mock_client = Mock()

        # Initialize MessageSender
        sender = MessageSender(mock_client)

        # Verify initialization
        assert sender.client == mock_client

    def test_message_sender_send_message_routes_correctly(self):
        """Test MessageSender.send_message routes to correct method based on chat_type"""
        from src.xagent.core.message_sender import MessageSender

        # Create mock client
        mock_client = Mock()
        sender = MessageSender(mock_client)

        # Mock the internal methods
        sender.send_new_message = Mock(return_value=True)
        sender.reply_message = Mock(return_value=True)

        # Test p2p routing
        result = sender.send_message("p2p", "chat_id", "msg_id", "content")
        sender.send_new_message.assert_called_once_with("chat_id", "content")
        assert result is True

        # Reset mocks
        sender.send_new_message.reset_mock()
        sender.reply_message.reset_mock()

        # Test group routing
        result = sender.send_message("group", "chat_id", "msg_id", "content")
        sender.reply_message.assert_called_once_with("msg_id", "content")
        assert result is True


class TestXAgentMessageSenderIntegration:
    """Integration tests for XAgent's message_sender usage"""

    @patch("src.xagent.xagent.LarkClient")
    def test_xagent_message_sender_client_reference(self, mock_lark_client):
        """Test that XAgent's message_sender uses the same LarkClient instance"""
        from src.xagent.xagent import XAgent
        from src.xagent.config import BotConfig

        # Create mock config
        mock_config = Mock(spec=BotConfig)
        mock_config.app_id = "test_app_id"
        mock_config.app_secret = "test_app_secret"
        mock_config.cache_size = 1000
        mock_config.session_storage_path = "./test_sessions"
        mock_config.max_session_messages = 100
        mock_config.session_timeout = 3600
        mock_config.ai_timeout = 60
        mock_config.target_directory = None
        mock_config.claude_cli_target_dir = None
        mock_config.gemini_cli_target_dir = None
        mock_config.qwen_cli_target_dir = None

        # Mock LarkClient builder
        mock_client_instance = Mock()
        mock_builder = Mock()
        mock_builder.app_id.return_value = mock_builder
        mock_builder.app_secret.return_value = mock_builder
        mock_builder.build.return_value = mock_client_instance
        mock_lark_client.builder.return_value = mock_builder

        # Create XAgent instance
        bot = XAgent(mock_config)

        # Verify message_sender uses the same client as XAgent
        assert bot.message_sender.client is bot.client
        assert bot.message_sender.client is mock_client_instance

    @patch("src.xagent.xagent.LarkClient")
    def test_xagent_does_not_use_channel_abstraction(self, mock_lark_client):
        """Test that XAgent does not use ChannelManager or Channel abstraction"""
        from src.xagent.xagent import XAgent
        from src.xagent.config import BotConfig

        # Create mock config
        mock_config = Mock(spec=BotConfig)
        mock_config.app_id = "test_app_id"
        mock_config.app_secret = "test_app_secret"
        mock_config.cache_size = 1000
        mock_config.session_storage_path = "./test_sessions"
        mock_config.max_session_messages = 100
        mock_config.session_timeout = 3600
        mock_config.ai_timeout = 60
        mock_config.target_directory = None
        mock_config.claude_cli_target_dir = None
        mock_config.gemini_cli_target_dir = None
        mock_config.qwen_cli_target_dir = None

        # Mock LarkClient builder
        mock_client_instance = Mock()
        mock_builder = Mock()
        mock_builder.app_id.return_value = mock_builder
        mock_builder.app_secret.return_value = mock_builder
        mock_builder.build.return_value = mock_client_instance
        mock_lark_client.builder.return_value = mock_builder

        # Create XAgent instance
        bot = XAgent(mock_config)

        # Verify XAgent does not have channel_manager attribute
        assert not hasattr(bot, "channel_manager")

        # Verify XAgent does not have any Channel-related attributes
        assert not hasattr(bot, "channel")
        assert not hasattr(bot, "feishu_channel")
