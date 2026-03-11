# -*- coding: utf-8 -*-
"""FeishuChannel unit tests

This module contains unit tests for the FeishuChannel adapter class.
Tests verify specific examples and integration points including:
- P2P message sending with specific parameters
- Group message sending with session_id
- Error conditions (MessageSender failure, exceptions)
- Parameter edge cases (empty strings, None values)

Requirements: 2.1, 2.2, 2.3, 8.3
"""
import pytest
from unittest.mock import Mock, AsyncMock
from src.xagent.core.channels.feishu_channel import FeishuChannel


class TestFeishuChannelP2PMessages:
    """Test P2P message sending scenarios"""
    
    @pytest.mark.asyncio
    async def test_send_p2p_message_success(self):
        """Test successful P2P message sending with specific parameters"""
        # Arrange
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=True)
        channel = FeishuChannel(mock_sender)
        
        # Act
        result = await channel.send_message(
            channel="p2p",
            user_id="ou_1234567890abcdef",
            session_id=None,
            content="Hello, this is a test message",
            mode="final"
        )
        
        # Assert
        assert result is True
        mock_sender.send_message.assert_called_once_with(
            chat_type="p2p",
            chat_id="ou_1234567890abcdef",
            message_id="",
            content="Hello, this is a test message"
        )
    
    @pytest.mark.asyncio
    async def test_send_p2p_message_with_long_user_id(self):
        """Test P2P message with very long user_id"""
        # Arrange
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=True)
        channel = FeishuChannel(mock_sender)
        long_user_id = "ou_" + "a" * 100
        
        # Act
        result = await channel.send_message(
            channel="p2p",
            user_id=long_user_id,
            session_id=None,
            content="Test message",
            mode="final"
        )
        
        # Assert
        assert result is True
        mock_sender.send_message.assert_called_once_with(
            chat_type="p2p",
            chat_id=long_user_id,
            message_id="",
            content="Test message"
        )
    
    @pytest.mark.asyncio
    async def test_send_p2p_message_with_special_characters(self):
        """Test P2P message with special characters in content"""
        # Arrange
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=True)
        channel = FeishuChannel(mock_sender)
        
        # Act
        result = await channel.send_message(
            channel="p2p",
            user_id="ou_test123",
            session_id=None,
            content='Test with "quotes" and \n newlines',
            mode="final"
        )
        
        # Assert
        assert result is True
        assert mock_sender.send_message.called


class TestFeishuChannelGroupMessages:
    """Test group message sending scenarios"""
    
    @pytest.mark.asyncio
    async def test_send_group_message_with_session_id(self):
        """Test group message sending with session_id"""
        # Arrange
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=True)
        channel = FeishuChannel(mock_sender)
        
        # Act
        result = await channel.send_message(
            channel="group",
            user_id="ou_group_user",
            session_id="om_1234567890abcdef",
            content="Group message content",
            mode="final"
        )
        
        # Assert
        assert result is True
        mock_sender.send_message.assert_called_once_with(
            chat_type="group",
            chat_id="ou_group_user",
            message_id="om_1234567890abcdef",
            content="Group message content"
        )
    
    @pytest.mark.asyncio
    async def test_send_group_message_without_session_id(self):
        """Test group message when session_id is None"""
        # Arrange
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=True)
        channel = FeishuChannel(mock_sender)
        
        # Act
        result = await channel.send_message(
            channel="group",
            user_id="ou_group_user",
            session_id=None,
            content="Group message without session",
            mode="final"
        )
        
        # Assert
        assert result is True
        mock_sender.send_message.assert_called_once_with(
            chat_type="group",
            chat_id="ou_group_user",
            message_id="",
            content="Group message without session"
        )


class TestFeishuChannelErrorConditions:
    """Test error handling scenarios"""
    
    @pytest.mark.asyncio
    async def test_message_sender_returns_false(self):
        """Test handling when MessageSender returns False"""
        # Arrange
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=False)
        channel = FeishuChannel(mock_sender)
        
        # Act
        result = await channel.send_message(
            channel="p2p",
            user_id="ou_test",
            session_id=None,
            content="Test message",
            mode="final"
        )
        
        # Assert
        assert result is False
        mock_sender.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_message_sender_raises_exception(self):
        """Test handling when MessageSender raises an exception"""
        # Arrange
        mock_sender = Mock()
        mock_sender.send_message = Mock(side_effect=RuntimeError("Network error"))
        channel = FeishuChannel(mock_sender)
        
        # Act
        result = await channel.send_message(
            channel="p2p",
            user_id="ou_test",
            session_id=None,
            content="Test message",
            mode="final"
        )
        
        # Assert
        assert result is False
        mock_sender.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_message_sender_raises_value_error(self):
        """Test handling when MessageSender raises ValueError"""
        # Arrange
        mock_sender = Mock()
        mock_sender.send_message = Mock(side_effect=ValueError("Invalid parameter"))
        channel = FeishuChannel(mock_sender)
        
        # Act
        result = await channel.send_message(
            channel="p2p",
            user_id="ou_test",
            session_id=None,
            content="Test message",
            mode="final"
        )
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_message_sender_raises_type_error(self):
        """Test handling when MessageSender raises TypeError"""
        # Arrange
        mock_sender = Mock()
        mock_sender.send_message = Mock(side_effect=TypeError("Type mismatch"))
        channel = FeishuChannel(mock_sender)
        
        # Act
        result = await channel.send_message(
            channel="group",
            user_id="ou_test",
            session_id="om_test",
            content="Test message",
            mode="final"
        )
        
        # Assert
        assert result is False


class TestFeishuChannelParameterEdgeCases:
    """Test parameter edge cases"""
    
    @pytest.mark.asyncio
    async def test_empty_user_id(self):
        """Test with empty user_id string"""
        # Arrange
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=True)
        channel = FeishuChannel(mock_sender)
        
        # Act
        result = await channel.send_message(
            channel="p2p",
            user_id="",
            session_id=None,
            content="Test message",
            mode="final"
        )
        
        # Assert
        assert result is True
        mock_sender.send_message.assert_called_once_with(
            chat_type="p2p",
            chat_id="",
            message_id="",
            content="Test message"
        )
    
    @pytest.mark.asyncio
    async def test_empty_content(self):
        """Test with empty content string"""
        # Arrange
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=True)
        channel = FeishuChannel(mock_sender)
        
        # Act
        result = await channel.send_message(
            channel="p2p",
            user_id="ou_test",
            session_id=None,
            content="",
            mode="final"
        )
        
        # Assert
        assert result is True
        mock_sender.send_message.assert_called_once_with(
            chat_type="p2p",
            chat_id="ou_test",
            message_id="",
            content=""
        )
    
    @pytest.mark.asyncio
    async def test_empty_session_id(self):
        """Test with empty session_id string"""
        # Arrange
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=True)
        channel = FeishuChannel(mock_sender)
        
        # Act
        result = await channel.send_message(
            channel="group",
            user_id="ou_test",
            session_id="",
            content="Test message",
            mode="final"
        )
        
        # Assert
        assert result is True
        mock_sender.send_message.assert_called_once_with(
            chat_type="group",
            chat_id="ou_test",
            message_id="",
            content="Test message"
        )
    
    @pytest.mark.asyncio
    async def test_none_session_id_converts_to_empty_string(self):
        """Test that None session_id is converted to empty string"""
        # Arrange
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=True)
        channel = FeishuChannel(mock_sender)
        
        # Act
        result = await channel.send_message(
            channel="p2p",
            user_id="ou_test",
            session_id=None,
            content="Test message",
            mode="final"
        )
        
        # Assert
        assert result is True
        # Verify that None was converted to empty string
        call_args = mock_sender.send_message.call_args
        assert call_args[1]["message_id"] == ""


class TestFeishuChannelAsyncCompatibility:
    """Test async/sync MessageSender compatibility"""
    
    @pytest.mark.asyncio
    async def test_async_message_sender(self):
        """Test with async MessageSender"""
        # Arrange
        mock_sender = Mock()
        mock_sender.send_message = AsyncMock(return_value=True)
        channel = FeishuChannel(mock_sender)
        
        # Act
        result = await channel.send_message(
            channel="p2p",
            user_id="ou_test",
            session_id=None,
            content="Test message",
            mode="final"
        )
        
        # Assert
        assert result is True
        mock_sender.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sync_message_sender(self):
        """Test with synchronous MessageSender"""
        # Arrange
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=True)
        channel = FeishuChannel(mock_sender)
        
        # Act
        result = await channel.send_message(
            channel="p2p",
            user_id="ou_test",
            session_id=None,
            content="Test message",
            mode="final"
        )
        
        # Assert
        assert result is True
        mock_sender.send_message.assert_called_once()


class TestFeishuChannelParameterMapping:
    """Test parameter mapping from Channel interface to MessageSender"""
    
    @pytest.mark.asyncio
    async def test_channel_to_chat_type_mapping_p2p(self):
        """Test that channel='p2p' maps to chat_type='p2p'"""
        # Arrange
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=True)
        channel = FeishuChannel(mock_sender)
        
        # Act
        await channel.send_message(
            channel="p2p",
            user_id="ou_test",
            session_id=None,
            content="Test",
            mode="final"
        )
        
        # Assert
        call_args = mock_sender.send_message.call_args
        assert call_args[1]["chat_type"] == "p2p"
    
    @pytest.mark.asyncio
    async def test_channel_to_chat_type_mapping_group(self):
        """Test that channel='group' maps to chat_type='group'"""
        # Arrange
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=True)
        channel = FeishuChannel(mock_sender)
        
        # Act
        await channel.send_message(
            channel="group",
            user_id="ou_test",
            session_id="om_test",
            content="Test",
            mode="final"
        )
        
        # Assert
        call_args = mock_sender.send_message.call_args
        assert call_args[1]["chat_type"] == "group"
    
    @pytest.mark.asyncio
    async def test_user_id_to_chat_id_mapping(self):
        """Test that user_id maps to chat_id"""
        # Arrange
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=True)
        channel = FeishuChannel(mock_sender)
        test_user_id = "ou_specific_user_123"
        
        # Act
        await channel.send_message(
            channel="p2p",
            user_id=test_user_id,
            session_id=None,
            content="Test",
            mode="final"
        )
        
        # Assert
        call_args = mock_sender.send_message.call_args
        assert call_args[1]["chat_id"] == test_user_id
    
    @pytest.mark.asyncio
    async def test_session_id_to_message_id_mapping(self):
        """Test that session_id maps to message_id"""
        # Arrange
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=True)
        channel = FeishuChannel(mock_sender)
        test_session_id = "om_specific_session_456"
        
        # Act
        await channel.send_message(
            channel="group",
            user_id="ou_test",
            session_id=test_session_id,
            content="Test",
            mode="final"
        )
        
        # Assert
        call_args = mock_sender.send_message.call_args
        assert call_args[1]["message_id"] == test_session_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
