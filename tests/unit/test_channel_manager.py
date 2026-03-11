# -*- coding: utf-8 -*-
"""ChannelManager unit tests

This module contains unit tests for the ChannelManager class.
Tests verify specific examples and integration points including:
- Registering and retrieving channels
- Sending messages through registered channels
- KeyError for non-existent channels
- Multiple channels registered simultaneously

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
"""
import pytest
from typing import Optional
from unittest.mock import Mock, AsyncMock
from src.xagent.core.channels.channel_manager import ChannelManager
from src.xagent.core.channels.base_channel import Channel


class MockChannel(Channel):
    """Mock Channel implementation for testing"""
    
    def __init__(self, name: str = "mock"):
        self.name = name
        self.send_message_mock = AsyncMock(return_value=True)
    
    async def send_message(
        self,
        receive_id: str,
        receive_id_type: str,
        content: str,
        message_id: Optional[str] = None
    ) -> bool:
        return await self.send_message_mock(receive_id, receive_id_type, content, message_id)


class TestChannelManagerRegistration:
    """Test channel registration and retrieval"""
    
    def test_register_and_retrieve_single_channel(self):
        """Test registering and retrieving a single channel"""
        # Arrange
        manager = ChannelManager()
        mock_channel = MockChannel("feishu")
        
        # Act
        manager.register_channel("feishu", mock_channel)
        retrieved = manager.get_channel("feishu")
        
        # Assert
        assert retrieved is mock_channel
    
    def test_register_multiple_channels(self):
        """Test registering multiple channels with different names"""
        # Arrange
        manager = ChannelManager()
        feishu_channel = MockChannel("feishu")
        slack_channel = MockChannel("slack")
        teams_channel = MockChannel("teams")
        
        # Act
        manager.register_channel("feishu", feishu_channel)
        manager.register_channel("slack", slack_channel)
        manager.register_channel("teams", teams_channel)
        
        # Assert
        assert manager.get_channel("feishu") is feishu_channel
        assert manager.get_channel("slack") is slack_channel
        assert manager.get_channel("teams") is teams_channel
    
    def test_overwrite_existing_channel(self):
        """Test that registering a channel with existing name overwrites it"""
        # Arrange
        manager = ChannelManager()
        old_channel = MockChannel("old")
        new_channel = MockChannel("new")
        
        # Act
        manager.register_channel("feishu", old_channel)
        manager.register_channel("feishu", new_channel)
        retrieved = manager.get_channel("feishu")
        
        # Assert
        assert retrieved is new_channel
        assert retrieved is not old_channel
    
    def test_register_channel_with_special_characters_in_name(self):
        """Test registering channel with special characters in name"""
        # Arrange
        manager = ChannelManager()
        mock_channel = MockChannel("test")
        
        # Act
        manager.register_channel("feishu-prod-v2", mock_channel)
        retrieved = manager.get_channel("feishu-prod-v2")
        
        # Assert
        assert retrieved is mock_channel


class TestChannelManagerRetrieval:
    """Test channel retrieval and error handling"""
    
    def test_get_non_existent_channel_raises_key_error(self):
        """Test that retrieving non-existent channel raises KeyError"""
        # Arrange
        manager = ChannelManager()
        
        # Act & Assert
        with pytest.raises(KeyError) as exc_info:
            manager.get_channel("non_existent")
        
        assert "Channel not registered: non_existent" in str(exc_info.value)
    
    def test_get_channel_before_any_registration(self):
        """Test getting channel from empty manager raises KeyError"""
        # Arrange
        manager = ChannelManager()
        
        # Act & Assert
        with pytest.raises(KeyError):
            manager.get_channel("feishu")
    
    def test_get_channel_after_different_channel_registered(self):
        """Test getting unregistered channel when other channels exist"""
        # Arrange
        manager = ChannelManager()
        manager.register_channel("slack", MockChannel("slack"))
        
        # Act & Assert
        with pytest.raises(KeyError) as exc_info:
            manager.get_channel("feishu")
        
        assert "feishu" in str(exc_info.value)


class TestChannelManagerMessageSending:
    """Test message sending through registered channels"""
    
    @pytest.mark.asyncio
    async def test_send_message_through_registered_channel(self):
        """Test sending message through a registered channel"""
        # Arrange
        manager = ChannelManager()
        mock_channel = MockChannel("feishu")
        manager.register_channel("feishu", mock_channel)
        
        # Act
        result = await manager.send_message(
            channel="feishu",
            user_id="ou_test123",
            content="Test message",
            mode="final"
        )
        
        # Assert
        assert result is True
        mock_channel.send_message_mock.assert_called_once_with(
            "ou_test123",  # receive_id
            "open_id",     # receive_id_type
            "Test message",
            None           # message_id
        )
    
    @pytest.mark.asyncio
    async def test_send_message_to_non_existent_channel_returns_false(self):
        """Test that sending to non-existent channel returns False"""
        # Arrange
        manager = ChannelManager()
        
        # Act
        result = await manager.send_message(
            channel="non_existent",
            user_id="ou_test",
            content="Test message",
            mode="final"
        )
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_send_message_with_chat_id(self):
        """Test sending message with chat_id parameter (preferred)"""
        # Arrange
        manager = ChannelManager()
        mock_channel = MockChannel("feishu")
        manager.register_channel("feishu", mock_channel)
        
        # Act
        result = await manager.send_message(
            channel="feishu",
            chat_id="oc_xxx",
            content="Group message",
            mode="final"
        )
        
        # Assert
        assert result is True
        # When chat_id is provided, it should be used with chat_id type
        mock_channel.send_message_mock.assert_called_once_with(
            "oc_xxx",      # receive_id
            "chat_id",     # receive_id_type
            "Group message",
            None           # message_id
        )
    
    @pytest.mark.asyncio
    async def test_send_message_when_channel_returns_false(self):
        """Test handling when channel send_message returns False"""
        # Arrange
        manager = ChannelManager()
        mock_channel = MockChannel("feishu")
        mock_channel.send_message_mock = AsyncMock(return_value=False)
        manager.register_channel("feishu", mock_channel)
        
        # Act
        result = await manager.send_message(
            channel="feishu",
            user_id="ou_test",
            content="Test message",
            mode="final"
        )
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_send_message_when_channel_raises_exception(self):
        """Test handling when channel raises an exception"""
        # Arrange
        manager = ChannelManager()
        mock_channel = MockChannel("feishu")
        mock_channel.send_message_mock = AsyncMock(side_effect=RuntimeError("Network error"))
        manager.register_channel("feishu", mock_channel)
        
        # Act
        result = await manager.send_message(
            channel="feishu",
            user_id="ou_test",
            content="Test message",
            mode="final"
        )
        
        # Assert
        assert result is False


class TestChannelManagerMultipleChannels:
    """Test scenarios with multiple channels registered simultaneously"""
    
    @pytest.mark.asyncio
    async def test_send_to_different_channels_independently(self):
        """Test sending messages to different channels independently"""
        # Arrange
        manager = ChannelManager()
        feishu_channel = MockChannel("feishu")
        slack_channel = MockChannel("slack")
        
        manager.register_channel("feishu", feishu_channel)
        manager.register_channel("slack", slack_channel)
        
        # Act
        feishu_result = await manager.send_message(
            channel="feishu",
            user_id="ou_feishu_user",
            content="Feishu message",
            mode="final"
        )
        
        slack_result = await manager.send_message(
            channel="slack",
            user_id="U123456",
            content="Slack message",
            mode="final"
        )
        
        # Assert
        assert feishu_result is True
        assert slack_result is True
        
        # Verify each channel received only its own message
        feishu_channel.send_message_mock.assert_called_once_with(
            "ou_feishu_user",
            "open_id",
            "Feishu message",
            None
        )
        
        slack_channel.send_message_mock.assert_called_once_with(
            "U123456",
            "open_id",
            "Slack message",
            None
        )
    
    @pytest.mark.asyncio
    async def test_one_channel_failure_does_not_affect_others(self):
        """Test that failure in one channel doesn't affect other channels"""
        # Arrange
        manager = ChannelManager()
        working_channel = MockChannel("working")
        failing_channel = MockChannel("failing")
        failing_channel.send_message_mock = AsyncMock(return_value=False)
        
        manager.register_channel("working", working_channel)
        manager.register_channel("failing", failing_channel)
        
        # Act
        failing_result = await manager.send_message(
            channel="failing",
            user_id="ou_test",
            content="Test",
            mode="final"
        )
        
        working_result = await manager.send_message(
            channel="working",
            user_id="ou_test",
            content="Test",
            mode="final"
        )
        
        # Assert
        assert failing_result is False
        assert working_result is True
    
    def test_retrieve_all_registered_channels(self):
        """Test retrieving all registered channels by name"""
        # Arrange
        manager = ChannelManager()
        channels = {
            "feishu": MockChannel("feishu"),
            "slack": MockChannel("slack"),
            "teams": MockChannel("teams"),
            "discord": MockChannel("discord")
        }
        
        # Act
        for name, channel in channels.items():
            manager.register_channel(name, channel)
        
        # Assert
        for name, expected_channel in channels.items():
            retrieved = manager.get_channel(name)
            assert retrieved is expected_channel
    
    @pytest.mark.asyncio
    async def test_concurrent_message_sending_to_multiple_channels(self):
        """Test sending messages to multiple channels concurrently"""
        # Arrange
        manager = ChannelManager()
        channel1 = MockChannel("channel1")
        channel2 = MockChannel("channel2")
        channel3 = MockChannel("channel3")
        
        manager.register_channel("channel1", channel1)
        manager.register_channel("channel2", channel2)
        manager.register_channel("channel3", channel3)
        
        # Act - Send messages to all channels
        result1 = await manager.send_message(
            channel="channel1",
            user_id="user1",
            content="msg1",
            mode="final"
        )
        result2 = await manager.send_message(
            channel="channel2",
            user_id="user2",
            content="msg2",
            mode="final"
        )
        result3 = await manager.send_message(
            channel="channel3",
            user_id="user3",
            content="msg3",
            mode="final"
        )
        
        # Assert
        assert result1 is True
        assert result2 is True
        assert result3 is True
        
        channel1.send_message_mock.assert_called_once()
        channel2.send_message_mock.assert_called_once()
        channel3.send_message_mock.assert_called_once()


class TestChannelManagerEdgeCases:
    """Test edge cases and boundary conditions"""
    
    @pytest.mark.asyncio
    async def test_send_message_with_empty_content(self):
        """Test sending message with empty content string"""
        # Arrange
        manager = ChannelManager()
        mock_channel = MockChannel("feishu")
        manager.register_channel("feishu", mock_channel)
        
        # Act
        result = await manager.send_message(
            channel="feishu",
            user_id="ou_test",
            content="",
            mode="final"
        )
        
        # Assert
        assert result is True
        mock_channel.send_message_mock.assert_called_once_with(
            "ou_test",
            "open_id",
            "",
            None
        )
    
    @pytest.mark.asyncio
    async def test_send_message_with_very_long_content(self):
        """Test sending message with very long content"""
        # Arrange
        manager = ChannelManager()
        mock_channel = MockChannel("feishu")
        manager.register_channel("feishu", mock_channel)
        long_content = "A" * 10000
        
        # Act
        result = await manager.send_message(
            channel="feishu",
            user_id="ou_test",
            content=long_content,
            mode="final"
        )
        
        # Assert
        assert result is True
        call_args = mock_channel.send_message_mock.call_args
        assert call_args[0][2] == long_content  # content is 3rd positional arg
    
    def test_register_channel_with_empty_name(self):
        """Test registering channel with empty string name"""
        # Arrange
        manager = ChannelManager()
        mock_channel = MockChannel("test")
        
        # Act
        manager.register_channel("", mock_channel)
        retrieved = manager.get_channel("")
        
        # Assert
        assert retrieved is mock_channel
    
    @pytest.mark.asyncio
    async def test_send_message_with_special_characters_in_user_id(self):
        """Test sending message with special characters in user_id"""
        # Arrange
        manager = ChannelManager()
        mock_channel = MockChannel("feishu")
        manager.register_channel("feishu", mock_channel)
        
        # Act
        result = await manager.send_message(
            channel="feishu",
            user_id="ou_test@#$%^&*()",
            content="Test",
            mode="final"
        )
        
        # Assert
        assert result is True
        call_args = mock_channel.send_message_mock.call_args
        assert call_args[0][0] == "ou_test@#$%^&*()"  # receive_id is 1st positional arg
    
    @pytest.mark.asyncio
    async def test_send_message_with_both_chat_id_and_user_id(self):
        """Test that chat_id takes priority over user_id"""
        # Arrange
        manager = ChannelManager()
        mock_channel = MockChannel("feishu")
        manager.register_channel("feishu", mock_channel)
        
        # Act
        result = await manager.send_message(
            channel="feishu",
            chat_id="oc_xxx",
            user_id="ou_xxx",
            content="Test",
            mode="final"
        )
        
        # Assert
        assert result is True
        # Should use chat_id, not user_id
        mock_channel.send_message_mock.assert_called_once_with(
            "oc_xxx",      # receive_id (chat_id takes priority)
            "chat_id",     # receive_id_type
            "Test",
            None
        )
    
    @pytest.mark.asyncio
    async def test_send_message_without_chat_id_or_user_id(self):
        """Test that sending without chat_id or user_id returns False"""
        # Arrange
        manager = ChannelManager()
        mock_channel = MockChannel("feishu")
        manager.register_channel("feishu", mock_channel)
        
        # Act
        result = await manager.send_message(
            channel="feishu",
            content="Test",
            mode="final"
        )
        
        # Assert
        assert result is False
        # Should not call the channel's send_message
        mock_channel.send_message_mock.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
