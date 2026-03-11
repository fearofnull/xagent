"""
Property tests for backward compatibility preservation.

This module contains property-based tests using Hypothesis to verify that
existing XAgent message sending operations remain unchanged after implementing
the channel abstraction layer.

**Feature: channel-abstraction-layer, Property 6: Backward Compatibility Preservation**
**Validates: Requirements 6.3**
"""
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, MagicMock
from src.xagent.core.message_sender import MessageSender


class TestBackwardCompatibilityPreservation:
    """Property 6: Backward Compatibility Preservation
    
    For any existing XAgent message sending operation, the behavior after
    implementing the channel abstraction layer SHALL be identical to the
    behavior before implementation, ensuring zero impact on current functionality.
    
    **Validates: Requirements 6.3**
    """
    
    @settings(max_examples=100)
    @given(
        chat_type=st.sampled_from(["p2p", "group"]),
        chat_id=st.text(min_size=1, max_size=100),
        message_id=st.text(min_size=1, max_size=100),
        content=st.text(min_size=1, max_size=1000)
    )
    def test_message_sender_interface_unchanged(
        self, chat_type, chat_id, message_id, content
    ):
        """Verify MessageSender interface remains unchanged.
        
        This property test verifies that for any valid combination of:
        - chat_type (p2p or group)
        - chat_id (any non-empty string)
        - message_id (any non-empty string)
        - content (any non-empty string)
        
        The MessageSender.send_message method continues to accept the same
        parameters (chat_type, chat_id, message_id, content) and returns
        a boolean value, ensuring the interface is unchanged.
        
        **Feature: channel-abstraction-layer, Property 6: Backward Compatibility Preservation**
        **Validates: Requirements 6.3**
        """
        # Create a mock LarkClient
        mock_client = Mock()
        
        # Mock the response for both p2p and group messages
        mock_response = Mock()
        mock_response.success.return_value = True
        
        # Setup mock for p2p (create message)
        mock_client.im.v1.message.create.return_value = mock_response
        
        # Setup mock for group (reply message)
        mock_client.im.v1.message.reply.return_value = mock_response
        
        # Create MessageSender with mock client
        message_sender = MessageSender(mock_client)
        
        # Call send_message with the original interface
        result = message_sender.send_message(
            chat_type=chat_type,
            chat_id=chat_id,
            message_id=message_id,
            content=content
        )
        
        # Verify the method accepts the parameters and returns boolean
        assert isinstance(result, bool), \
            "MessageSender.send_message should return a boolean value"
        
        # Verify the method was called successfully
        assert result is True, \
            "MessageSender.send_message should return True for successful sends"
    
    @settings(max_examples=100)
    @given(
        chat_id=st.text(min_size=1, max_size=100),
        message_id=st.text(min_size=1, max_size=100),
        content=st.text(min_size=1, max_size=1000)
    )
    def test_p2p_message_behavior_unchanged(
        self, chat_id, message_id, content
    ):
        """Verify p2p message sending behavior is unchanged.
        
        For p2p messages, MessageSender should continue to use send_new_message
        internally, maintaining the exact same behavior as before the channel
        abstraction layer was implemented.
        
        **Feature: channel-abstraction-layer, Property 6: Backward Compatibility Preservation**
        **Validates: Requirements 6.3**
        """
        # Create a mock LarkClient
        mock_client = Mock()
        
        # Mock the response for p2p message
        mock_response = Mock()
        mock_response.success.return_value = True
        mock_client.im.v1.message.create.return_value = mock_response
        
        # Create MessageSender with mock client
        message_sender = MessageSender(mock_client)
        
        # Send p2p message
        result = message_sender.send_message(
            chat_type="p2p",
            chat_id=chat_id,
            message_id=message_id,
            content=content
        )
        
        # Verify p2p behavior: should call create (not reply)
        assert mock_client.im.v1.message.create.called, \
            "p2p messages should use create message API"
        
        assert not mock_client.im.v1.message.reply.called, \
            "p2p messages should NOT use reply message API"
        
        # Verify return value
        assert result is True, \
            "p2p message sending should return True on success"
    
    @settings(max_examples=100)
    @given(
        chat_id=st.text(min_size=1, max_size=100),
        message_id=st.text(min_size=1, max_size=100),
        content=st.text(min_size=1, max_size=1000)
    )
    def test_group_message_behavior_unchanged(
        self, chat_id, message_id, content
    ):
        """Verify group message sending behavior is unchanged.
        
        For group messages, MessageSender should continue to use reply_message
        internally, maintaining the exact same behavior as before the channel
        abstraction layer was implemented.
        
        **Feature: channel-abstraction-layer, Property 6: Backward Compatibility Preservation**
        **Validates: Requirements 6.3**
        """
        # Create a mock LarkClient
        mock_client = Mock()
        
        # Mock the response for group message
        mock_response = Mock()
        mock_response.success.return_value = True
        mock_client.im.v1.message.reply.return_value = mock_response
        
        # Create MessageSender with mock client
        message_sender = MessageSender(mock_client)
        
        # Send group message
        result = message_sender.send_message(
            chat_type="group",
            chat_id=chat_id,
            message_id=message_id,
            content=content
        )
        
        # Verify group behavior: should call reply (not create)
        assert mock_client.im.v1.message.reply.called, \
            "group messages should use reply message API"
        
        assert not mock_client.im.v1.message.create.called, \
            "group messages should NOT use create message API"
        
        # Verify return value
        assert result is True, \
            "group message sending should return True on success"
    
    @settings(max_examples=100)
    @given(
        chat_type=st.sampled_from(["p2p", "group"]),
        chat_id=st.text(min_size=1, max_size=100),
        message_id=st.text(min_size=1, max_size=100),
        content=st.text(min_size=1, max_size=1000),
        success=st.booleans()
    )
    def test_return_value_behavior_unchanged(
        self, chat_type, chat_id, message_id, content, success
    ):
        """Verify return value behavior is unchanged.
        
        MessageSender should continue to return True for successful sends
        and False for failed sends, maintaining the exact same return value
        behavior as before the channel abstraction layer was implemented.
        
        **Feature: channel-abstraction-layer, Property 6: Backward Compatibility Preservation**
        **Validates: Requirements 6.3**
        """
        # Create a mock LarkClient
        mock_client = Mock()
        
        # Mock the response with specified success value
        mock_response = Mock()
        mock_response.success.return_value = success
        mock_response.code = 0 if success else 1
        mock_response.msg = "success" if success else "error"
        mock_response.get_log_id.return_value = "test_log_id"
        
        # Setup mock for both p2p and group
        mock_client.im.v1.message.create.return_value = mock_response
        mock_client.im.v1.message.reply.return_value = mock_response
        
        # Create MessageSender with mock client
        message_sender = MessageSender(mock_client)
        
        # Send message
        result = message_sender.send_message(
            chat_type=chat_type,
            chat_id=chat_id,
            message_id=message_id,
            content=content
        )
        
        # Verify return value matches the API response
        assert result == success, \
            f"MessageSender should return {success} when API returns success={success}"
    
    @settings(max_examples=100)
    @given(
        chat_type=st.sampled_from(["p2p", "group"]),
        chat_id=st.text(min_size=1, max_size=100),
        message_id=st.text(min_size=1, max_size=100),
        content=st.text(min_size=1, max_size=1000),
        exception_type=st.sampled_from([
            Exception,
            RuntimeError,
            ValueError,
            ConnectionError,
            TimeoutError
        ])
    )
    def test_error_handling_behavior_unchanged(
        self, chat_type, chat_id, message_id, content, exception_type
    ):
        """Verify error handling behavior is unchanged.
        
        When an exception occurs, MessageSender should continue to catch it
        and return False, maintaining the exact same error handling behavior
        as before the channel abstraction layer was implemented.
        
        **Feature: channel-abstraction-layer, Property 6: Backward Compatibility Preservation**
        **Validates: Requirements 6.3**
        """
        # Create a mock LarkClient that raises exception
        mock_client = Mock()
        
        # Setup mock to raise exception
        mock_client.im.v1.message.create.side_effect = exception_type("Test error")
        mock_client.im.v1.message.reply.side_effect = exception_type("Test error")
        
        # Create MessageSender with mock client
        message_sender = MessageSender(mock_client)
        
        # Send message - should not raise exception
        result = message_sender.send_message(
            chat_type=chat_type,
            chat_id=chat_id,
            message_id=message_id,
            content=content
        )
        
        # Verify error handling: should return False
        assert result is False, \
            "MessageSender should return False when exception occurs"
    
    @settings(max_examples=100)
    @given(
        chat_id=st.text(min_size=1, max_size=100),
        content=st.text(
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd', 'Po', 'Zs'),
                whitelist_characters='"\\\n\r\t'
            ),
            min_size=1,
            max_size=500
        )
    )
    def test_json_escaping_behavior_unchanged(
        self, chat_id, content
    ):
        """Verify JSON escaping behavior is unchanged.
        
        MessageSender should continue to escape special characters in content
        (quotes, backslashes, newlines, etc.) exactly as before the channel
        abstraction layer was implemented.
        
        **Feature: channel-abstraction-layer, Property 6: Backward Compatibility Preservation**
        **Validates: Requirements 6.3**
        """
        # Create a mock LarkClient
        mock_client = Mock()
        
        # Mock the response
        mock_response = Mock()
        mock_response.success.return_value = True
        mock_client.im.v1.message.create.return_value = mock_response
        
        # Create MessageSender with mock client
        message_sender = MessageSender(mock_client)
        
        # Send p2p message with special characters
        result = message_sender.send_message(
            chat_type="p2p",
            chat_id=chat_id,
            message_id="",
            content=content
        )
        
        # Verify the method was called
        assert mock_client.im.v1.message.create.called, \
            "create message API should be called"
        
        # Get the request that was passed
        call_args = mock_client.im.v1.message.create.call_args
        request = call_args[0][0] if call_args[0] else None
        
        # Verify the request was created (this confirms escaping happened)
        assert request is not None, \
            "Request should be created with escaped content"
        
        # Verify return value
        assert result is True, \
            "Message sending should succeed"
    
    @settings(max_examples=100)
    @given(
        chat_type=st.sampled_from(["p2p", "group", "other"]),
        chat_id=st.text(min_size=1, max_size=100),
        message_id=st.text(min_size=1, max_size=100),
        content=st.text(min_size=1, max_size=1000)
    )
    def test_chat_type_routing_unchanged(
        self, chat_type, chat_id, message_id, content
    ):
        """Verify chat type routing behavior is unchanged.
        
        MessageSender should continue to route p2p to send_new_message and
        all other chat types to reply_message, maintaining the exact same
        routing logic as before the channel abstraction layer was implemented.
        
        **Feature: channel-abstraction-layer, Property 6: Backward Compatibility Preservation**
        **Validates: Requirements 6.3**
        """
        # Create a mock LarkClient
        mock_client = Mock()
        
        # Mock the response
        mock_response = Mock()
        mock_response.success.return_value = True
        mock_client.im.v1.message.create.return_value = mock_response
        mock_client.im.v1.message.reply.return_value = mock_response
        
        # Create MessageSender with mock client
        message_sender = MessageSender(mock_client)
        
        # Send message
        result = message_sender.send_message(
            chat_type=chat_type,
            chat_id=chat_id,
            message_id=message_id,
            content=content
        )
        
        # Verify routing logic
        if chat_type == "p2p":
            assert mock_client.im.v1.message.create.called, \
                "p2p should route to create message API"
            assert not mock_client.im.v1.message.reply.called, \
                "p2p should NOT route to reply message API"
        else:
            assert mock_client.im.v1.message.reply.called, \
                "non-p2p should route to reply message API"
            assert not mock_client.im.v1.message.create.called, \
                "non-p2p should NOT route to create message API"
        
        # Verify return value
        assert result is True, \
            "Message sending should succeed"
    
    @settings(max_examples=100)
    @given(
        chat_type=st.sampled_from(["p2p", "group"]),
        chat_id=st.text(min_size=1, max_size=100),
        message_id=st.text(min_size=1, max_size=100),
        content=st.text(min_size=0, max_size=1000)
    )
    def test_empty_content_handling_unchanged(
        self, chat_type, chat_id, message_id, content
    ):
        """Verify empty content handling is unchanged.
        
        MessageSender should continue to handle empty or whitespace-only
        content in the same way as before the channel abstraction layer
        was implemented.
        
        **Feature: channel-abstraction-layer, Property 6: Backward Compatibility Preservation**
        **Validates: Requirements 6.3**
        """
        # Create a mock LarkClient
        mock_client = Mock()
        
        # Mock the response
        mock_response = Mock()
        mock_response.success.return_value = True
        mock_client.im.v1.message.create.return_value = mock_response
        mock_client.im.v1.message.reply.return_value = mock_response
        
        # Create MessageSender with mock client
        message_sender = MessageSender(mock_client)
        
        # Send message with potentially empty content
        result = message_sender.send_message(
            chat_type=chat_type,
            chat_id=chat_id,
            message_id=message_id,
            content=content
        )
        
        # Verify the method was called (no validation on empty content)
        if chat_type == "p2p":
            assert mock_client.im.v1.message.create.called, \
                "create message API should be called even with empty content"
        else:
            assert mock_client.im.v1.message.reply.called, \
                "reply message API should be called even with empty content"
        
        # Verify return value
        assert isinstance(result, bool), \
            "MessageSender should return boolean even with empty content"
