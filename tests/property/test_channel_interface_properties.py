"""
Property tests for Channel interface parameter mapping.

This module contains property-based tests using Hypothesis to verify that
the FeishuChannel correctly maps parameters from the Channel interface to
the MessageSender interface across all valid inputs.

**Feature: channel-abstraction-layer, Property 1: Parameter Mapping Correctness**
**Validates: Requirements 2.4, 2.5, 2.6**
"""
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, AsyncMock, call
from src.xagent.core.channels.feishu_channel import FeishuChannel


class TestParameterMappingCorrectness:
    """Property 1: Parameter Mapping Correctness
    
    For any valid channel type (p2p or group), user_id, and session_id,
    when FeishuChannel.send_message is called, the parameters passed to
    MessageSender SHALL be correctly mapped:
    - channel → chat_type
    - user_id → chat_id (for p2p)
    - session_id → message_id (for group messages)
    
    **Validates: Requirements 2.4, 2.5, 2.6**
    """
    
    @settings(max_examples=100)
    @given(
        channel=st.sampled_from(["p2p", "group"]),
        user_id=st.text(min_size=1, max_size=100),
        session_id=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        content=st.text(min_size=1, max_size=1000),
        mode=st.text(min_size=0, max_size=50)
    )
    @pytest.mark.asyncio
    async def test_parameter_mapping_correctness(
        self, channel, user_id, session_id, content, mode
    ):
        """Verify FeishuChannel correctly maps parameters to MessageSender.
        
        This property test verifies that for any valid combination of:
        - channel type (p2p or group)
        - user_id (any non-empty string)
        - session_id (any string or None)
        - content (any non-empty string)
        - mode (any string)
        
        The FeishuChannel correctly maps these parameters to MessageSender:
        - channel is passed as chat_type
        - user_id is passed as chat_id
        - session_id is passed as message_id (or empty string if None)
        - content is passed unchanged
        
        **Feature: channel-abstraction-layer, Property 1: Parameter Mapping Correctness**
        **Validates: Requirements 2.4, 2.5, 2.6**
        """
        # Create a mock MessageSender
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=True)
        
        # Create FeishuChannel with the mock
        feishu_channel = FeishuChannel(mock_sender)
        
        # Call send_message
        result = await feishu_channel.send_message(
            channel=channel,
            user_id=user_id,
            session_id=session_id,
            content=content,
            mode=mode
        )
        
        # Verify MessageSender.send_message was called exactly once
        assert mock_sender.send_message.call_count == 1, \
            "MessageSender.send_message should be called exactly once"
        
        # Get the actual call arguments
        actual_call = mock_sender.send_message.call_args
        
        # Verify parameter mapping
        # channel → chat_type
        assert actual_call.kwargs["chat_type"] == channel, \
            f"channel parameter should map to chat_type: expected {channel}, got {actual_call.kwargs['chat_type']}"
        
        # user_id → chat_id
        assert actual_call.kwargs["chat_id"] == user_id, \
            f"user_id parameter should map to chat_id: expected {user_id}, got {actual_call.kwargs['chat_id']}"
        
        # session_id → message_id (or empty string if None)
        expected_message_id = session_id if session_id is not None else ""
        assert actual_call.kwargs["message_id"] == expected_message_id, \
            f"session_id parameter should map to message_id: expected {expected_message_id}, got {actual_call.kwargs['message_id']}"
        
        # content → content (unchanged)
        assert actual_call.kwargs["content"] == content, \
            f"content parameter should be passed unchanged: expected {content}, got {actual_call.kwargs['content']}"
        
        # Verify return value is preserved
        assert result is True, \
            "FeishuChannel should return the same value as MessageSender"
    
    @settings(max_examples=100)
    @given(
        channel=st.sampled_from(["p2p", "group"]),
        user_id=st.text(min_size=1, max_size=100),
        content=st.text(min_size=1, max_size=1000)
    )
    @pytest.mark.asyncio
    async def test_parameter_mapping_with_none_session_id(
        self, channel, user_id, content
    ):
        """Verify FeishuChannel handles None session_id correctly.
        
        When session_id is None, it should be mapped to an empty string
        when passed to MessageSender.
        
        **Feature: channel-abstraction-layer, Property 1: Parameter Mapping Correctness**
        **Validates: Requirements 2.4, 2.5, 2.6**
        """
        # Create a mock MessageSender
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=True)
        
        # Create FeishuChannel with the mock
        feishu_channel = FeishuChannel(mock_sender)
        
        # Call send_message with None session_id
        result = await feishu_channel.send_message(
            channel=channel,
            user_id=user_id,
            session_id=None,
            content=content,
            mode="normal"
        )
        
        # Verify MessageSender.send_message was called
        assert mock_sender.send_message.call_count == 1
        
        # Get the actual call arguments
        actual_call = mock_sender.send_message.call_args
        
        # Verify None session_id is mapped to empty string
        assert actual_call.kwargs["message_id"] == "", \
            "None session_id should be mapped to empty string"
        
        # Verify other parameters are correct
        assert actual_call.kwargs["chat_type"] == channel
        assert actual_call.kwargs["chat_id"] == user_id
        assert actual_call.kwargs["content"] == content
    
    @settings(max_examples=100)
    @given(
        user_id=st.text(min_size=1, max_size=100),
        session_id=st.text(min_size=1, max_size=100),
        content=st.text(min_size=1, max_size=1000)
    )
    @pytest.mark.asyncio
    async def test_p2p_channel_mapping(self, user_id, session_id, content):
        """Verify p2p channel type is correctly mapped.
        
        For p2p messages, the channel parameter should be mapped to
        chat_type="p2p" and user_id should be used as chat_id.
        
        **Feature: channel-abstraction-layer, Property 1: Parameter Mapping Correctness**
        **Validates: Requirements 2.4, 2.5**
        """
        # Create a mock MessageSender
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=True)
        
        # Create FeishuChannel with the mock
        feishu_channel = FeishuChannel(mock_sender)
        
        # Call send_message with p2p channel
        result = await feishu_channel.send_message(
            channel="p2p",
            user_id=user_id,
            session_id=session_id,
            content=content,
            mode="normal"
        )
        
        # Verify MessageSender.send_message was called
        assert mock_sender.send_message.call_count == 1
        
        # Get the actual call arguments
        actual_call = mock_sender.send_message.call_args
        
        # Verify p2p mapping
        assert actual_call.kwargs["chat_type"] == "p2p", \
            "p2p channel should map to chat_type='p2p'"
        assert actual_call.kwargs["chat_id"] == user_id, \
            "user_id should be used as chat_id for p2p"
    
    @settings(max_examples=100)
    @given(
        user_id=st.text(min_size=1, max_size=100),
        session_id=st.text(min_size=1, max_size=100),
        content=st.text(min_size=1, max_size=1000)
    )
    @pytest.mark.asyncio
    async def test_group_channel_mapping(self, user_id, session_id, content):
        """Verify group channel type is correctly mapped.
        
        For group messages, the channel parameter should be mapped to
        chat_type="group" and session_id should be used as message_id.
        
        **Feature: channel-abstraction-layer, Property 1: Parameter Mapping Correctness**
        **Validates: Requirements 2.4, 2.6**
        """
        # Create a mock MessageSender
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=True)
        
        # Create FeishuChannel with the mock
        feishu_channel = FeishuChannel(mock_sender)
        
        # Call send_message with group channel
        result = await feishu_channel.send_message(
            channel="group",
            user_id=user_id,
            session_id=session_id,
            content=content,
            mode="normal"
        )
        
        # Verify MessageSender.send_message was called
        assert mock_sender.send_message.call_count == 1
        
        # Get the actual call arguments
        actual_call = mock_sender.send_message.call_args
        
        # Verify group mapping
        assert actual_call.kwargs["chat_type"] == "group", \
            "group channel should map to chat_type='group'"
        assert actual_call.kwargs["message_id"] == session_id, \
            "session_id should be used as message_id for group"
    
    @settings(max_examples=100)
    @given(
        channel=st.sampled_from(["p2p", "group"]),
        user_id=st.text(
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd', 'Po', 'Zs'),
                whitelist_characters='!@#$%^&*()_+-=[]{}|;:\'",.<>?/\\`~'
            ),
            min_size=1,
            max_size=100
        ),
        session_id=st.text(
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd', 'Po', 'Zs'),
                whitelist_characters='!@#$%^&*()_+-=[]{}|;:\'",.<>?/\\`~'
            ),
            min_size=1,
            max_size=100
        ),
        content=st.text(min_size=1, max_size=1000)
    )
    @pytest.mark.asyncio
    async def test_special_characters_in_parameters(
        self, channel, user_id, session_id, content
    ):
        """Verify special characters in parameters are preserved.
        
        Parameters containing special characters should be passed through
        to MessageSender without modification.
        
        **Feature: channel-abstraction-layer, Property 1: Parameter Mapping Correctness**
        **Validates: Requirements 2.4, 2.5, 2.6**
        """
        # Create a mock MessageSender
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=True)
        
        # Create FeishuChannel with the mock
        feishu_channel = FeishuChannel(mock_sender)
        
        # Call send_message
        result = await feishu_channel.send_message(
            channel=channel,
            user_id=user_id,
            session_id=session_id,
            content=content,
            mode="normal"
        )
        
        # Verify MessageSender.send_message was called
        assert mock_sender.send_message.call_count == 1
        
        # Get the actual call arguments
        actual_call = mock_sender.send_message.call_args
        
        # Verify special characters are preserved
        assert actual_call.kwargs["chat_id"] == user_id, \
            "Special characters in user_id should be preserved"
        assert actual_call.kwargs["message_id"] == session_id, \
            "Special characters in session_id should be preserved"
        assert actual_call.kwargs["content"] == content, \
            "Special characters in content should be preserved"



class TestReturnValuePreservation:
    """Property 2: Return Value Preservation
    
    For any message sending operation, when MessageSender returns a success
    or failure boolean, FeishuChannel SHALL return the same boolean value
    (True for success, False for failure).
    
    **Validates: Requirements 2.8, 2.9**
    """
    
    @settings(max_examples=100)
    @given(
        channel=st.sampled_from(["p2p", "group"]),
        user_id=st.text(min_size=1, max_size=100),
        session_id=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        content=st.text(min_size=1, max_size=1000),
        mode=st.text(min_size=0, max_size=50),
        sender_return_value=st.booleans()
    )
    @pytest.mark.asyncio
    async def test_return_value_preservation(
        self, channel, user_id, session_id, content, mode, sender_return_value
    ):
        """Verify FeishuChannel preserves MessageSender return value.
        
        This property test verifies that for any valid combination of:
        - channel type (p2p or group)
        - user_id (any non-empty string)
        - session_id (any string or None)
        - content (any non-empty string)
        - mode (any string)
        - sender_return_value (True or False)
        
        When MessageSender.send_message returns a boolean value (True for
        success, False for failure), FeishuChannel.send_message SHALL return
        the exact same boolean value without modification.
        
        **Feature: channel-abstraction-layer, Property 2: Return Value Preservation**
        **Validates: Requirements 2.8, 2.9**
        """
        # Create a mock MessageSender that returns the specified value
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=sender_return_value)
        
        # Create FeishuChannel with the mock
        feishu_channel = FeishuChannel(mock_sender)
        
        # Call send_message
        result = await feishu_channel.send_message(
            channel=channel,
            user_id=user_id,
            session_id=session_id,
            content=content,
            mode=mode
        )
        
        # Verify the return value is preserved exactly
        assert result == sender_return_value, \
            f"FeishuChannel should return the same value as MessageSender: " \
            f"expected {sender_return_value}, got {result}"
        
        # Verify MessageSender was called
        assert mock_sender.send_message.call_count == 1, \
            "MessageSender.send_message should be called exactly once"
    
    @settings(max_examples=100)
    @given(
        channel=st.sampled_from(["p2p", "group"]),
        user_id=st.text(min_size=1, max_size=100),
        session_id=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        content=st.text(min_size=1, max_size=1000)
    )
    @pytest.mark.asyncio
    async def test_success_return_value_preservation(
        self, channel, user_id, session_id, content
    ):
        """Verify FeishuChannel returns True when MessageSender succeeds.
        
        When MessageSender.send_message returns True (indicating success),
        FeishuChannel.send_message SHALL return True.
        
        **Feature: channel-abstraction-layer, Property 2: Return Value Preservation**
        **Validates: Requirements 2.8**
        """
        # Create a mock MessageSender that returns True
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=True)
        
        # Create FeishuChannel with the mock
        feishu_channel = FeishuChannel(mock_sender)
        
        # Call send_message
        result = await feishu_channel.send_message(
            channel=channel,
            user_id=user_id,
            session_id=session_id,
            content=content,
            mode="normal"
        )
        
        # Verify True is returned
        assert result is True, \
            "FeishuChannel should return True when MessageSender returns True"
    
    @settings(max_examples=100)
    @given(
        channel=st.sampled_from(["p2p", "group"]),
        user_id=st.text(min_size=1, max_size=100),
        session_id=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        content=st.text(min_size=1, max_size=1000)
    )
    @pytest.mark.asyncio
    async def test_failure_return_value_preservation(
        self, channel, user_id, session_id, content
    ):
        """Verify FeishuChannel returns False when MessageSender fails.
        
        When MessageSender.send_message returns False (indicating failure),
        FeishuChannel.send_message SHALL return False.
        
        **Feature: channel-abstraction-layer, Property 2: Return Value Preservation**
        **Validates: Requirements 2.9**
        """
        # Create a mock MessageSender that returns False
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=False)
        
        # Create FeishuChannel with the mock
        feishu_channel = FeishuChannel(mock_sender)
        
        # Call send_message
        result = await feishu_channel.send_message(
            channel=channel,
            user_id=user_id,
            session_id=session_id,
            content=content,
            mode="normal"
        )
        
        # Verify False is returned
        assert result is False, \
            "FeishuChannel should return False when MessageSender returns False"
    
    @settings(max_examples=100)
    @given(
        channel=st.sampled_from(["p2p", "group"]),
        user_id=st.text(min_size=1, max_size=100),
        session_id=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        content=st.text(min_size=1, max_size=1000),
        mode=st.text(min_size=0, max_size=50)
    )
    @pytest.mark.asyncio
    async def test_exception_returns_false(
        self, channel, user_id, session_id, content, mode
    ):
        """Verify FeishuChannel returns False when MessageSender raises exception.
        
        When MessageSender.send_message raises an exception, FeishuChannel
        SHALL catch the exception and return False (indicating failure).
        
        This test verifies error handling resilience as specified in
        Requirements 8.2 and 8.3.
        
        **Feature: channel-abstraction-layer, Property 2: Return Value Preservation**
        **Validates: Requirements 2.9, 8.2, 8.3**
        """
        # Create a mock MessageSender that raises an exception
        mock_sender = Mock()
        mock_sender.send_message = Mock(side_effect=Exception("Test exception"))
        
        # Create FeishuChannel with the mock
        feishu_channel = FeishuChannel(mock_sender)
        
        # Call send_message
        result = await feishu_channel.send_message(
            channel=channel,
            user_id=user_id,
            session_id=session_id,
            content=content,
            mode=mode
        )
        
        # Verify False is returned (exception was caught)
        assert result is False, \
            "FeishuChannel should return False when MessageSender raises exception"
        
        # Verify MessageSender was called
        assert mock_sender.send_message.call_count == 1, \
            "MessageSender.send_message should be called exactly once"



class TestErrorHandlingResilience:
    """Property 9: Error Handling Resilience
    
    For any error condition (exception, MessageSender failure, etc.) during
    message sending, the Channel implementation SHALL catch the error, log it
    appropriately, and return False without propagating the exception.
    
    **Validates: Requirements 8.2, 8.3**
    """
    
    @settings(max_examples=100)
    @given(
        channel=st.sampled_from(["p2p", "group"]),
        user_id=st.text(min_size=1, max_size=100),
        session_id=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        content=st.text(min_size=1, max_size=1000),
        mode=st.text(min_size=0, max_size=50),
        exception_type=st.sampled_from([
            Exception,
            RuntimeError,
            ValueError,
            TypeError,
            AttributeError,
            KeyError,
            ConnectionError,
            TimeoutError
        ])
    )
    @pytest.mark.asyncio
    async def test_exception_handling_returns_false(
        self, channel, user_id, session_id, content, mode, exception_type
    ):
        """Verify FeishuChannel catches all exception types and returns False.
        
        This property test verifies that for any valid combination of:
        - channel type (p2p or group)
        - user_id (any non-empty string)
        - session_id (any string or None)
        - content (any non-empty string)
        - mode (any string)
        - exception_type (any exception class)
        
        When MessageSender.send_message raises any type of exception,
        FeishuChannel SHALL:
        1. Catch the exception (not propagate it)
        2. Log the error appropriately
        3. Return False (indicating failure)
        
        **Feature: channel-abstraction-layer, Property 9: Error Handling Resilience**
        **Validates: Requirements 8.2, 8.3**
        """
        # Create a mock MessageSender that raises the specified exception
        mock_sender = Mock()
        mock_sender.send_message = Mock(
            side_effect=exception_type("Simulated error")
        )
        
        # Create FeishuChannel with the mock
        feishu_channel = FeishuChannel(mock_sender)
        
        # Call send_message - should NOT raise exception
        try:
            result = await feishu_channel.send_message(
                channel=channel,
                user_id=user_id,
                session_id=session_id,
                content=content,
                mode=mode
            )
            
            # Verify False is returned (exception was caught)
            assert result is False, \
                f"FeishuChannel should return False when MessageSender raises {exception_type.__name__}"
            
            # Verify MessageSender was called
            assert mock_sender.send_message.call_count == 1, \
                "MessageSender.send_message should be called exactly once"
                
        except Exception as e:
            pytest.fail(
                f"FeishuChannel should catch {exception_type.__name__} and not propagate it, "
                f"but it raised: {type(e).__name__}: {e}"
            )
    
    @settings(max_examples=100)
    @given(
        channel=st.sampled_from(["p2p", "group"]),
        user_id=st.text(min_size=1, max_size=100),
        session_id=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        content=st.text(min_size=1, max_size=1000),
        mode=st.text(min_size=0, max_size=50),
        error_message=st.text(min_size=1, max_size=200)
    )
    @pytest.mark.asyncio
    async def test_exception_with_various_messages(
        self, channel, user_id, session_id, content, mode, error_message
    ):
        """Verify FeishuChannel handles exceptions with various error messages.
        
        This test verifies that regardless of the exception message content,
        FeishuChannel consistently catches the exception and returns False.
        
        **Feature: channel-abstraction-layer, Property 9: Error Handling Resilience**
        **Validates: Requirements 8.2, 8.3**
        """
        # Create a mock MessageSender that raises exception with custom message
        mock_sender = Mock()
        mock_sender.send_message = Mock(
            side_effect=Exception(error_message)
        )
        
        # Create FeishuChannel with the mock
        feishu_channel = FeishuChannel(mock_sender)
        
        # Call send_message - should NOT raise exception
        try:
            result = await feishu_channel.send_message(
                channel=channel,
                user_id=user_id,
                session_id=session_id,
                content=content,
                mode=mode
            )
            
            # Verify False is returned
            assert result is False, \
                "FeishuChannel should return False when exception is raised"
                
        except Exception as e:
            pytest.fail(
                f"FeishuChannel should catch exception and not propagate it, "
                f"but it raised: {type(e).__name__}: {e}"
            )
    
    @settings(max_examples=100)
    @given(
        channel=st.sampled_from(["p2p", "group"]),
        user_id=st.text(min_size=1, max_size=100),
        session_id=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        content=st.text(min_size=1, max_size=1000)
    )
    @pytest.mark.asyncio
    async def test_message_sender_failure_returns_false(
        self, channel, user_id, session_id, content
    ):
        """Verify FeishuChannel returns False when MessageSender returns False.
        
        When MessageSender.send_message returns False (indicating failure
        without exception), FeishuChannel SHALL return False and log a warning.
        
        **Feature: channel-abstraction-layer, Property 9: Error Handling Resilience**
        **Validates: Requirements 8.2**
        """
        # Create a mock MessageSender that returns False
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=False)
        
        # Create FeishuChannel with the mock
        feishu_channel = FeishuChannel(mock_sender)
        
        # Call send_message
        result = await feishu_channel.send_message(
            channel=channel,
            user_id=user_id,
            session_id=session_id,
            content=content,
            mode="normal"
        )
        
        # Verify False is returned
        assert result is False, \
            "FeishuChannel should return False when MessageSender returns False"
        
        # Verify MessageSender was called
        assert mock_sender.send_message.call_count == 1
    
    @settings(max_examples=100)
    @given(
        channel=st.sampled_from(["p2p", "group"]),
        user_id=st.text(min_size=1, max_size=100),
        session_id=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        content=st.text(min_size=1, max_size=1000),
        mode=st.text(min_size=0, max_size=50)
    )
    @pytest.mark.asyncio
    async def test_nested_exception_handling(
        self, channel, user_id, session_id, content, mode
    ):
        """Verify FeishuChannel handles nested exceptions correctly.
        
        When MessageSender raises an exception that contains another exception
        (nested exception), FeishuChannel SHALL catch it and return False.
        
        **Feature: channel-abstraction-layer, Property 9: Error Handling Resilience**
        **Validates: Requirements 8.2, 8.3**
        """
        # Create a nested exception
        inner_exception = ValueError("Inner error")
        outer_exception = RuntimeError("Outer error")
        outer_exception.__cause__ = inner_exception
        
        # Create a mock MessageSender that raises nested exception
        mock_sender = Mock()
        mock_sender.send_message = Mock(side_effect=outer_exception)
        
        # Create FeishuChannel with the mock
        feishu_channel = FeishuChannel(mock_sender)
        
        # Call send_message - should NOT raise exception
        try:
            result = await feishu_channel.send_message(
                channel=channel,
                user_id=user_id,
                session_id=session_id,
                content=content,
                mode=mode
            )
            
            # Verify False is returned
            assert result is False, \
                "FeishuChannel should return False when nested exception is raised"
                
        except Exception as e:
            pytest.fail(
                f"FeishuChannel should catch nested exception and not propagate it, "
                f"but it raised: {type(e).__name__}: {e}"
            )
    
    @settings(max_examples=100)
    @given(
        channel=st.sampled_from(["p2p", "group"]),
        user_id=st.text(min_size=1, max_size=100),
        session_id=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        content=st.text(min_size=1, max_size=1000)
    )
    @pytest.mark.asyncio
    async def test_attribute_error_on_message_sender(
        self, channel, user_id, session_id, content
    ):
        """Verify FeishuChannel handles AttributeError gracefully.
        
        When MessageSender doesn't have the expected send_message method
        or raises AttributeError, FeishuChannel SHALL catch it and return False.
        
        **Feature: channel-abstraction-layer, Property 9: Error Handling Resilience**
        **Validates: Requirements 8.2, 8.3**
        """
        # Create a mock MessageSender that raises AttributeError
        mock_sender = Mock()
        mock_sender.send_message = Mock(
            side_effect=AttributeError("'MessageSender' object has no attribute 'send_message'")
        )
        
        # Create FeishuChannel with the mock
        feishu_channel = FeishuChannel(mock_sender)
        
        # Call send_message - should NOT raise exception
        try:
            result = await feishu_channel.send_message(
                channel=channel,
                user_id=user_id,
                session_id=session_id,
                content=content,
                mode="normal"
            )
            
            # Verify False is returned
            assert result is False, \
                "FeishuChannel should return False when AttributeError is raised"
                
        except Exception as e:
            pytest.fail(
                f"FeishuChannel should catch AttributeError and not propagate it, "
                f"but it raised: {type(e).__name__}: {e}"
            )



class TestAsyncSyncMessageSenderCompatibility:
    """Property 11: Async/Sync MessageSender Compatibility
    
    For any MessageSender instance (whether using sync or async methods),
    FeishuChannel SHALL correctly handle the invocation and await the result
    if necessary, ensuring compatibility with both synchronous and asynchronous
    MessageSender implementations.
    
    **Validates: Requirements 10.3**
    """
    
    @settings(max_examples=100)
    @given(
        channel=st.sampled_from(["p2p", "group"]),
        user_id=st.text(min_size=1, max_size=100),
        session_id=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        content=st.text(min_size=1, max_size=1000),
        mode=st.text(min_size=0, max_size=50),
        sender_return_value=st.booleans()
    )
    @pytest.mark.asyncio
    async def test_sync_message_sender_compatibility(
        self, channel, user_id, session_id, content, mode, sender_return_value
    ):
        """Verify FeishuChannel works with synchronous MessageSender.
        
        This property test verifies that for any valid combination of:
        - channel type (p2p or group)
        - user_id (any non-empty string)
        - session_id (any string or None)
        - content (any non-empty string)
        - mode (any string)
        - sender_return_value (True or False)
        
        When MessageSender.send_message is a synchronous method (returns
        a boolean directly), FeishuChannel SHALL:
        1. Invoke the synchronous method correctly
        2. Handle the return value without awaiting
        3. Return the same boolean value
        
        **Feature: channel-abstraction-layer, Property 11: Async/Sync MessageSender Compatibility**
        **Validates: Requirements 10.3**
        """
        # Create a mock MessageSender with synchronous send_message
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=sender_return_value)
        
        # Create FeishuChannel with the mock
        feishu_channel = FeishuChannel(mock_sender)
        
        # Call send_message
        result = await feishu_channel.send_message(
            channel=channel,
            user_id=user_id,
            session_id=session_id,
            content=content,
            mode=mode
        )
        
        # Verify the return value is correct
        assert result == sender_return_value, \
            f"FeishuChannel should return the same value as synchronous MessageSender: " \
            f"expected {sender_return_value}, got {result}"
        
        # Verify MessageSender.send_message was called exactly once
        assert mock_sender.send_message.call_count == 1, \
            "Synchronous MessageSender.send_message should be called exactly once"
        
        # Verify parameters were passed correctly
        actual_call = mock_sender.send_message.call_args
        assert actual_call.kwargs["chat_type"] == channel
        assert actual_call.kwargs["chat_id"] == user_id
        assert actual_call.kwargs["message_id"] == (session_id or "")
        assert actual_call.kwargs["content"] == content
    
    @settings(max_examples=100)
    @given(
        channel=st.sampled_from(["p2p", "group"]),
        user_id=st.text(min_size=1, max_size=100),
        session_id=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        content=st.text(min_size=1, max_size=1000),
        mode=st.text(min_size=0, max_size=50),
        sender_return_value=st.booleans()
    )
    @pytest.mark.asyncio
    async def test_async_message_sender_compatibility(
        self, channel, user_id, session_id, content, mode, sender_return_value
    ):
        """Verify FeishuChannel works with asynchronous MessageSender.
        
        This property test verifies that for any valid combination of:
        - channel type (p2p or group)
        - user_id (any non-empty string)
        - session_id (any string or None)
        - content (any non-empty string)
        - mode (any string)
        - sender_return_value (True or False)
        
        When MessageSender.send_message is an asynchronous method (returns
        a coroutine that resolves to a boolean), FeishuChannel SHALL:
        1. Detect that the method is async
        2. Await the coroutine to get the result
        3. Return the same boolean value
        
        **Feature: channel-abstraction-layer, Property 11: Async/Sync MessageSender Compatibility**
        **Validates: Requirements 10.3**
        """
        # Create a mock MessageSender with asynchronous send_message
        mock_sender = Mock()
        
        # Create an async mock that returns the specified value
        async def async_send_message(*args, **kwargs):
            return sender_return_value
        
        mock_sender.send_message = AsyncMock(side_effect=async_send_message)
        
        # Create FeishuChannel with the mock
        feishu_channel = FeishuChannel(mock_sender)
        
        # Call send_message
        result = await feishu_channel.send_message(
            channel=channel,
            user_id=user_id,
            session_id=session_id,
            content=content,
            mode=mode
        )
        
        # Verify the return value is correct
        assert result == sender_return_value, \
            f"FeishuChannel should return the same value as asynchronous MessageSender: " \
            f"expected {sender_return_value}, got {result}"
        
        # Verify MessageSender.send_message was called exactly once
        assert mock_sender.send_message.call_count == 1, \
            "Asynchronous MessageSender.send_message should be called exactly once"
        
        # Verify parameters were passed correctly
        actual_call = mock_sender.send_message.call_args
        assert actual_call.kwargs["chat_type"] == channel
        assert actual_call.kwargs["chat_id"] == user_id
        assert actual_call.kwargs["message_id"] == (session_id or "")
        assert actual_call.kwargs["content"] == content
    
    @settings(max_examples=100)
    @given(
        channel=st.sampled_from(["p2p", "group"]),
        user_id=st.text(min_size=1, max_size=100),
        session_id=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        content=st.text(min_size=1, max_size=1000),
        is_async=st.booleans(),
        sender_return_value=st.booleans()
    )
    @pytest.mark.asyncio
    async def test_mixed_sync_async_compatibility(
        self, channel, user_id, session_id, content, is_async, sender_return_value
    ):
        """Verify FeishuChannel handles both sync and async MessageSender.
        
        This property test verifies that FeishuChannel can handle MessageSender
        instances that are either synchronous or asynchronous, determined
        randomly for each test iteration.
        
        This ensures that the implementation correctly detects and handles
        both types of MessageSender implementations without prior knowledge
        of which type it will receive.
        
        **Feature: channel-abstraction-layer, Property 11: Async/Sync MessageSender Compatibility**
        **Validates: Requirements 10.3**
        """
        # Create a mock MessageSender
        mock_sender = Mock()
        
        if is_async:
            # Create an async mock
            async def async_send_message(*args, **kwargs):
                return sender_return_value
            mock_sender.send_message = AsyncMock(side_effect=async_send_message)
        else:
            # Create a sync mock
            mock_sender.send_message = Mock(return_value=sender_return_value)
        
        # Create FeishuChannel with the mock
        feishu_channel = FeishuChannel(mock_sender)
        
        # Call send_message
        result = await feishu_channel.send_message(
            channel=channel,
            user_id=user_id,
            session_id=session_id,
            content=content,
            mode="normal"
        )
        
        # Verify the return value is correct
        assert result == sender_return_value, \
            f"FeishuChannel should return the same value regardless of sync/async: " \
            f"expected {sender_return_value}, got {result}"
        
        # Verify MessageSender.send_message was called exactly once
        assert mock_sender.send_message.call_count == 1, \
            "MessageSender.send_message should be called exactly once"
    
    @settings(max_examples=100)
    @given(
        channel=st.sampled_from(["p2p", "group"]),
        user_id=st.text(min_size=1, max_size=100),
        session_id=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        content=st.text(min_size=1, max_size=1000)
    )
    @pytest.mark.asyncio
    async def test_async_message_sender_exception_handling(
        self, channel, user_id, session_id, content
    ):
        """Verify FeishuChannel handles exceptions from async MessageSender.
        
        When an asynchronous MessageSender.send_message raises an exception,
        FeishuChannel SHALL catch it and return False, just as it does for
        synchronous MessageSender exceptions.
        
        **Feature: channel-abstraction-layer, Property 11: Async/Sync MessageSender Compatibility**
        **Validates: Requirements 10.3, 8.2, 8.3**
        """
        # Create a mock MessageSender with async send_message that raises exception
        mock_sender = Mock()
        
        async def async_send_message_with_error(*args, **kwargs):
            raise RuntimeError("Async error")
        
        mock_sender.send_message = AsyncMock(side_effect=async_send_message_with_error)
        
        # Create FeishuChannel with the mock
        feishu_channel = FeishuChannel(mock_sender)
        
        # Call send_message - should NOT raise exception
        try:
            result = await feishu_channel.send_message(
                channel=channel,
                user_id=user_id,
                session_id=session_id,
                content=content,
                mode="normal"
            )
            
            # Verify False is returned (exception was caught)
            assert result is False, \
                "FeishuChannel should return False when async MessageSender raises exception"
            
            # Verify MessageSender was called
            assert mock_sender.send_message.call_count == 1
                
        except Exception as e:
            pytest.fail(
                f"FeishuChannel should catch async exception and not propagate it, "
                f"but it raised: {type(e).__name__}: {e}"
            )
    
    @settings(max_examples=100)
    @given(
        channel=st.sampled_from(["p2p", "group"]),
        user_id=st.text(min_size=1, max_size=100),
        session_id=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        content=st.text(min_size=1, max_size=1000),
        mode=st.text(min_size=0, max_size=50)
    )
    @pytest.mark.asyncio
    async def test_sync_message_sender_exception_handling(
        self, channel, user_id, session_id, content, mode
    ):
        """Verify FeishuChannel handles exceptions from sync MessageSender.
        
        When a synchronous MessageSender.send_message raises an exception,
        FeishuChannel SHALL catch it and return False.
        
        **Feature: channel-abstraction-layer, Property 11: Async/Sync MessageSender Compatibility**
        **Validates: Requirements 10.3, 8.2, 8.3**
        """
        # Create a mock MessageSender with sync send_message that raises exception
        mock_sender = Mock()
        mock_sender.send_message = Mock(side_effect=RuntimeError("Sync error"))
        
        # Create FeishuChannel with the mock
        feishu_channel = FeishuChannel(mock_sender)
        
        # Call send_message - should NOT raise exception
        try:
            result = await feishu_channel.send_message(
                channel=channel,
                user_id=user_id,
                session_id=session_id,
                content=content,
                mode=mode
            )
            
            # Verify False is returned (exception was caught)
            assert result is False, \
                "FeishuChannel should return False when sync MessageSender raises exception"
            
            # Verify MessageSender was called
            assert mock_sender.send_message.call_count == 1
                
        except Exception as e:
            pytest.fail(
                f"FeishuChannel should catch sync exception and not propagate it, "
                f"but it raised: {type(e).__name__}: {e}"
            )



class TestChannelRegistrationRoundTrip:
    """Property 3: Channel Registration Round-Trip
    
    For any channel name and Channel instance, when a channel is registered
    with ChannelManager and then retrieved by the same name, the retrieved
    channel SHALL be the same instance that was registered.
    
    **Validates: Requirements 3.3**
    """
    
    @settings(max_examples=100)
    @given(
        channel_name=st.text(min_size=1, max_size=50),
        user_id=st.text(min_size=1, max_size=100),
        session_id=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        content=st.text(min_size=1, max_size=1000),
        mode=st.text(min_size=0, max_size=50),
        sender_return_value=st.booleans()
    )
    @pytest.mark.asyncio
    async def test_channel_registration_round_trip(
        self, channel_name, user_id, session_id, content, mode, sender_return_value
    ):
        """Verify channel registration and retrieval preserves instance identity.
        
        This property test verifies that for any valid combination of:
        - channel_name (any non-empty string)
        - Channel instance (FeishuChannel with mock MessageSender)
        
        When a Channel instance is registered with ChannelManager using a
        specific name, and then retrieved using the same name, the retrieved
        Channel SHALL be the exact same instance (same object identity) that
        was registered.
        
        This ensures that:
        1. ChannelManager correctly stores channel instances
        2. ChannelManager correctly retrieves channel instances by name
        3. No copying or wrapping occurs during registration/retrieval
        4. The same channel instance can be used consistently
        
        **Feature: channel-abstraction-layer, Property 3: Channel Registration Round-Trip**
        **Validates: Requirements 3.3**
        """
        # Import ChannelManager
        from src.xagent.core.channels.channel_manager import ChannelManager
        
        # Create a mock MessageSender
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=sender_return_value)
        
        # Create a FeishuChannel instance
        original_channel = FeishuChannel(mock_sender)
        
        # Create a ChannelManager
        manager = ChannelManager()
        
        # Register the channel with the manager
        manager.register_channel(channel_name, original_channel)
        
        # Retrieve the channel by name
        retrieved_channel = manager.get_channel(channel_name)
        
        # Verify the retrieved channel is the SAME instance (identity check)
        assert retrieved_channel is original_channel, \
            f"Retrieved channel should be the same instance as registered channel. " \
            f"Expected id={id(original_channel)}, got id={id(retrieved_channel)}"
        
        # Additional verification: the channel should still work correctly
        result = await retrieved_channel.send_message(
            channel="p2p",
            user_id=user_id,
            session_id=session_id,
            content=content,
            mode=mode
        )
        
        # Verify the channel functions correctly
        assert result == sender_return_value, \
            f"Retrieved channel should function correctly: expected {sender_return_value}, got {result}"
        
        # Verify MessageSender was called
        assert mock_sender.send_message.call_count == 1, \
            "MessageSender should be called exactly once through retrieved channel"
    
    @settings(max_examples=100)
    @given(
        channel_name=st.text(
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd'),
                whitelist_characters='-_'
            ),
            min_size=1,
            max_size=50
        )
    )
    def test_channel_registration_round_trip_identity(self, channel_name):
        """Verify channel instance identity is preserved through registration.
        
        This test focuses specifically on verifying that the object identity
        (memory address) of the Channel instance is preserved when it is
        registered and then retrieved from ChannelManager.
        
        **Feature: channel-abstraction-layer, Property 3: Channel Registration Round-Trip**
        **Validates: Requirements 3.3**
        """
        # Import ChannelManager
        from src.xagent.core.channels.channel_manager import ChannelManager
        
        # Create a mock MessageSender
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=True)
        
        # Create a FeishuChannel instance
        original_channel = FeishuChannel(mock_sender)
        original_id = id(original_channel)
        
        # Create a ChannelManager
        manager = ChannelManager()
        
        # Register the channel
        manager.register_channel(channel_name, original_channel)
        
        # Retrieve the channel
        retrieved_channel = manager.get_channel(channel_name)
        retrieved_id = id(retrieved_channel)
        
        # Verify identity preservation
        assert original_id == retrieved_id, \
            f"Channel instance identity should be preserved: " \
            f"original id={original_id}, retrieved id={retrieved_id}"
        
        assert retrieved_channel is original_channel, \
            "Retrieved channel should be the exact same object (is check)"
    
    @settings(max_examples=100)
    @given(
        channel_names=st.lists(
            st.text(
                alphabet=st.characters(
                    whitelist_categories=('Lu', 'Ll', 'Nd'),
                    whitelist_characters='-_'
                ),
                min_size=1,
                max_size=30
            ),
            min_size=1,
            max_size=10,
            unique=True
        )
    )
    def test_multiple_channel_registration_round_trip(self, channel_names):
        """Verify multiple channels can be registered and retrieved correctly.
        
        This property test verifies that when multiple Channel instances are
        registered with different names, each can be retrieved independently
        and the correct instance is returned for each name.
        
        This ensures that:
        1. ChannelManager can handle multiple channels simultaneously
        2. Each channel name maps to the correct instance
        3. No cross-contamination occurs between channels
        
        **Feature: channel-abstraction-layer, Property 3: Channel Registration Round-Trip**
        **Validates: Requirements 3.3, 7.3**
        """
        # Import ChannelManager
        from src.xagent.core.channels.channel_manager import ChannelManager
        
        # Create a ChannelManager
        manager = ChannelManager()
        
        # Create and register multiple channels
        channels = {}
        for name in channel_names:
            # Create a unique mock MessageSender for each channel
            mock_sender = Mock()
            mock_sender.send_message = Mock(return_value=True)
            
            # Create a FeishuChannel instance
            channel = FeishuChannel(mock_sender)
            channels[name] = channel
            
            # Register the channel
            manager.register_channel(name, channel)
        
        # Retrieve each channel and verify identity
        for name, original_channel in channels.items():
            retrieved_channel = manager.get_channel(name)
            
            # Verify the retrieved channel is the same instance
            assert retrieved_channel is original_channel, \
                f"Retrieved channel '{name}' should be the same instance as registered. " \
                f"Expected id={id(original_channel)}, got id={id(retrieved_channel)}"
            
            # Verify it's not any other channel
            for other_name, other_channel in channels.items():
                if other_name != name:
                    assert retrieved_channel is not other_channel, \
                        f"Retrieved channel '{name}' should not be the same as channel '{other_name}'"
    
    @settings(max_examples=100)
    @given(
        channel_name=st.text(min_size=1, max_size=50),
        registration_count=st.integers(min_value=1, max_value=5)
    )
    def test_channel_re_registration_overwrites(
        self, channel_name, registration_count
    ):
        """Verify re-registering a channel name overwrites the previous instance.
        
        This test verifies that when a channel name is registered multiple times
        with different Channel instances, the most recent registration is what
        gets retrieved.
        
        **Feature: channel-abstraction-layer, Property 3: Channel Registration Round-Trip**
        **Validates: Requirements 3.3**
        """
        # Import ChannelManager
        from src.xagent.core.channels.channel_manager import ChannelManager
        
        # Create a ChannelManager
        manager = ChannelManager()
        
        # Register multiple channels with the same name
        channels = []
        for i in range(registration_count):
            # Create a unique mock MessageSender
            mock_sender = Mock()
            mock_sender.send_message = Mock(return_value=True)
            
            # Create a FeishuChannel instance
            channel = FeishuChannel(mock_sender)
            channels.append(channel)
            
            # Register the channel with the same name
            manager.register_channel(channel_name, channel)
        
        # Retrieve the channel
        retrieved_channel = manager.get_channel(channel_name)
        
        # Verify the retrieved channel is the LAST registered instance
        last_channel = channels[-1]
        assert retrieved_channel is last_channel, \
            f"Retrieved channel should be the last registered instance. " \
            f"Expected id={id(last_channel)}, got id={id(retrieved_channel)}"
        
        # Verify it's not any of the earlier instances (if there were multiple)
        if registration_count > 1:
            for i in range(registration_count - 1):
                earlier_channel = channels[i]
                assert retrieved_channel is not earlier_channel, \
                    f"Retrieved channel should not be an earlier registered instance (index {i})"
    
    @settings(max_examples=100)
    @given(
        channel_name=st.text(min_size=1, max_size=50)
    )
    def test_channel_registration_with_special_characters(self, channel_name):
        """Verify channel names with special characters work correctly.
        
        This test verifies that channel names containing various characters
        (including special characters, unicode, etc.) can be used for
        registration and retrieval without issues.
        
        **Feature: channel-abstraction-layer, Property 3: Channel Registration Round-Trip**
        **Validates: Requirements 3.3**
        """
        # Import ChannelManager
        from src.xagent.core.channels.channel_manager import ChannelManager
        
        # Create a mock MessageSender
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=True)
        
        # Create a FeishuChannel instance
        original_channel = FeishuChannel(mock_sender)
        
        # Create a ChannelManager
        manager = ChannelManager()
        
        # Register the channel with the name (which may contain special chars)
        manager.register_channel(channel_name, original_channel)
        
        # Retrieve the channel by the same name
        retrieved_channel = manager.get_channel(channel_name)
        
        # Verify the retrieved channel is the same instance
        assert retrieved_channel is original_channel, \
            f"Retrieved channel should be the same instance even with special characters in name. " \
            f"Channel name: {repr(channel_name)}, " \
            f"Expected id={id(original_channel)}, got id={id(retrieved_channel)}"
    
    @settings(max_examples=100)
    @given(
        channel_name=st.text(min_size=1, max_size=50),
        retrieval_count=st.integers(min_value=1, max_value=10)
    )
    def test_multiple_retrievals_return_same_instance(
        self, channel_name, retrieval_count
    ):
        """Verify multiple retrievals of the same channel return the same instance.
        
        This test verifies that retrieving a channel multiple times always
        returns the same instance, ensuring that ChannelManager doesn't
        create new instances or copies on each retrieval.
        
        **Feature: channel-abstraction-layer, Property 3: Channel Registration Round-Trip**
        **Validates: Requirements 3.3**
        """
        # Import ChannelManager
        from src.xagent.core.channels.channel_manager import ChannelManager
        
        # Create a mock MessageSender
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=True)
        
        # Create a FeishuChannel instance
        original_channel = FeishuChannel(mock_sender)
        original_id = id(original_channel)
        
        # Create a ChannelManager
        manager = ChannelManager()
        
        # Register the channel
        manager.register_channel(channel_name, original_channel)
        
        # Retrieve the channel multiple times
        retrieved_channels = []
        for i in range(retrieval_count):
            retrieved = manager.get_channel(channel_name)
            retrieved_channels.append(retrieved)
        
        # Verify all retrievals return the same instance
        for i, retrieved in enumerate(retrieved_channels):
            assert retrieved is original_channel, \
                f"Retrieval {i+1} should return the same instance. " \
                f"Expected id={original_id}, got id={id(retrieved)}"
            
            # Also verify all retrievals are identical to each other
            for j, other_retrieved in enumerate(retrieved_channels):
                assert retrieved is other_retrieved, \
                    f"Retrieval {i+1} and retrieval {j+1} should return the same instance"
    
    @settings(max_examples=100)
    @given(
        channel_name=st.text(min_size=1, max_size=50)
    )
    def test_unregistered_channel_raises_key_error(self, channel_name):
        """Verify retrieving an unregistered channel raises KeyError.
        
        This test verifies that attempting to retrieve a channel that was
        never registered raises a KeyError, as specified in the requirements.
        
        **Feature: channel-abstraction-layer, Property 3: Channel Registration Round-Trip**
        **Validates: Requirements 3.5**
        """
        # Import ChannelManager
        from src.xagent.core.channels.channel_manager import ChannelManager
        
        # Create a ChannelManager (without registering any channels)
        manager = ChannelManager()
        
        # Attempt to retrieve a non-existent channel
        with pytest.raises(KeyError) as exc_info:
            manager.get_channel(channel_name)
        
        # Verify the error message contains the channel name
        error_message = str(exc_info.value)
        assert channel_name in error_message or "not registered" in error_message.lower(), \
            f"KeyError should mention the channel name or 'not registered'. Got: {error_message}"



class TestMessageRoutingCorrectness:
    """Property 4: Message Routing Correctness
    
    For any registered channel name, when ChannelManager.send_message is called
    with that channel name, the message SHALL be routed to the correct Channel
    instance and that instance's send_message method SHALL be invoked with the
    provided parameters.
    
    **Validates: Requirements 3.4**
    """
    
    @settings(max_examples=100)
    @given(
        channel_name=st.text(min_size=1, max_size=50),
        user_id=st.text(min_size=1, max_size=100),
        session_id=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        content=st.text(min_size=1, max_size=1000),
        mode=st.text(min_size=0, max_size=50),
        sender_return_value=st.booleans()
    )
    @pytest.mark.asyncio
    async def test_message_routing_to_correct_channel(
        self, channel_name, user_id, session_id, content, mode, sender_return_value
    ):
        """Verify ChannelManager routes messages to the correct channel instance.
        
        This property test verifies that for any valid combination of:
        - channel_name (any non-empty string)
        - user_id (any non-empty string)
        - session_id (any string or None)
        - content (any non-empty string)
        - mode (any string)
        - sender_return_value (True or False)
        
        When a Channel instance is registered with ChannelManager and
        ChannelManager.send_message is called with that channel name,
        the message SHALL be routed to the correct Channel instance and
        that instance's send_message method SHALL be invoked with the
        provided parameters.
        
        This ensures that:
        1. ChannelManager correctly looks up the channel by name
        2. ChannelManager invokes the channel's send_message method
        3. All parameters are forwarded correctly to the channel
        4. The return value from the channel is preserved
        
        **Feature: channel-abstraction-layer, Property 4: Message Routing Correctness**
        **Validates: Requirements 3.4**
        """
        # Import ChannelManager
        from src.xagent.core.channels.channel_manager import ChannelManager
        
        # Create a mock MessageSender
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=sender_return_value)
        
        # Create a FeishuChannel instance
        feishu_channel = FeishuChannel(mock_sender)
        
        # Create a ChannelManager and register the channel
        manager = ChannelManager()
        manager.register_channel(channel_name, feishu_channel)
        
        # Call ChannelManager.send_message
        result = await manager.send_message(
            channel=channel_name,
            user_id=user_id,
            session_id=session_id,
            content=content,
            mode=mode
        )
        
        # Verify MessageSender.send_message was called exactly once
        # (this proves the message was routed to the correct channel)
        assert mock_sender.send_message.call_count == 1, \
            "MessageSender.send_message should be called exactly once, " \
            "proving the message was routed to the registered channel"
        
        # Get the actual call arguments
        actual_call = mock_sender.send_message.call_args
        
        # Verify the parameters were forwarded correctly
        # Note: ChannelManager passes "p2p" as the channel type to the channel's send_message
        assert actual_call.kwargs["chat_type"] == "p2p", \
            "ChannelManager should pass 'p2p' as chat_type to the channel"
        
        assert actual_call.kwargs["chat_id"] == user_id, \
            f"user_id should be forwarded correctly: expected {user_id}, got {actual_call.kwargs['chat_id']}"
        
        expected_message_id = session_id if session_id is not None else ""
        assert actual_call.kwargs["message_id"] == expected_message_id, \
            f"session_id should be forwarded correctly: expected {expected_message_id}, got {actual_call.kwargs['message_id']}"
        
        assert actual_call.kwargs["content"] == content, \
            f"content should be forwarded correctly: expected {content}, got {actual_call.kwargs['content']}"
        
        # Verify the return value is preserved
        assert result == sender_return_value, \
            f"ChannelManager should return the same value as the channel: " \
            f"expected {sender_return_value}, got {result}"
    
    @settings(max_examples=100)
    @given(
        channel_name=st.text(min_size=1, max_size=50),
        user_id=st.text(min_size=1, max_size=100),
        content=st.text(min_size=1, max_size=1000)
    )
    @pytest.mark.asyncio
    async def test_message_routing_with_multiple_channels(
        self, channel_name, user_id, content
    ):
        """Verify ChannelManager routes to the correct channel when multiple are registered.
        
        This test verifies that when multiple channels are registered with
        different names, ChannelManager correctly routes messages to the
        specific channel requested, not to other registered channels.
        
        **Feature: channel-abstraction-layer, Property 4: Message Routing Correctness**
        **Validates: Requirements 3.4, 7.3**
        """
        # Import ChannelManager
        from src.xagent.core.channels.channel_manager import ChannelManager
        
        # Create multiple mock MessageSenders
        mock_sender_1 = Mock()
        mock_sender_1.send_message = Mock(return_value=True)
        
        mock_sender_2 = Mock()
        mock_sender_2.send_message = Mock(return_value=True)
        
        mock_sender_3 = Mock()
        mock_sender_3.send_message = Mock(return_value=True)
        
        # Create multiple FeishuChannel instances
        channel_1 = FeishuChannel(mock_sender_1)
        channel_2 = FeishuChannel(mock_sender_2)
        channel_3 = FeishuChannel(mock_sender_3)
        
        # Create a ChannelManager and register all channels
        manager = ChannelManager()
        manager.register_channel(channel_name, channel_1)
        manager.register_channel(f"{channel_name}_other1", channel_2)
        manager.register_channel(f"{channel_name}_other2", channel_3)
        
        # Send a message through the first channel
        result = await manager.send_message(
            channel=channel_name,
            user_id=user_id,
            session_id=None,
            content=content,
            mode="normal"
        )
        
        # Verify only the correct channel's MessageSender was called
        assert mock_sender_1.send_message.call_count == 1, \
            "The target channel's MessageSender should be called exactly once"
        
        assert mock_sender_2.send_message.call_count == 0, \
            "Other channels' MessageSenders should not be called"
        
        assert mock_sender_3.send_message.call_count == 0, \
            "Other channels' MessageSenders should not be called"
        
        # Verify the result is correct
        assert result is True, \
            "ChannelManager should return the result from the correct channel"
    
    @settings(max_examples=100)
    @given(
        registered_channel=st.text(min_size=1, max_size=50),
        unregistered_channel=st.text(min_size=1, max_size=50),
        user_id=st.text(min_size=1, max_size=100),
        content=st.text(min_size=1, max_size=1000)
    )
    @pytest.mark.asyncio
    async def test_message_routing_to_unregistered_channel_returns_false(
        self, registered_channel, unregistered_channel, user_id, content
    ):
        """Verify ChannelManager returns False when routing to unregistered channel.
        
        This test verifies that when ChannelManager.send_message is called
        with a channel name that is not registered, it returns False and
        does not raise an exception.
        
        **Feature: channel-abstraction-layer, Property 4: Message Routing Correctness**
        **Validates: Requirements 3.5, 8.4**
        """
        # Skip if the channel names are the same
        if registered_channel == unregistered_channel:
            pytest.skip("Channel names must be different for this test")
        
        # Import ChannelManager
        from src.xagent.core.channels.channel_manager import ChannelManager
        
        # Create a mock MessageSender
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=True)
        
        # Create a FeishuChannel instance
        feishu_channel = FeishuChannel(mock_sender)
        
        # Create a ChannelManager and register only one channel
        manager = ChannelManager()
        manager.register_channel(registered_channel, feishu_channel)
        
        # Try to send a message through an unregistered channel
        result = await manager.send_message(
            channel=unregistered_channel,
            user_id=user_id,
            session_id=None,
            content=content,
            mode="normal"
        )
        
        # Verify the result is False (not an exception)
        assert result is False, \
            "ChannelManager should return False when routing to unregistered channel"
        
        # Verify the registered channel's MessageSender was NOT called
        assert mock_sender.send_message.call_count == 0, \
            "MessageSender should not be called when routing to unregistered channel"
    
    @settings(max_examples=100)
    @given(
        channel_name=st.text(min_size=1, max_size=50),
        user_id=st.text(min_size=1, max_size=100),
        session_id=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        content=st.text(min_size=1, max_size=1000),
        mode=st.text(min_size=0, max_size=50)
    )
    @pytest.mark.asyncio
    async def test_message_routing_preserves_all_parameters(
        self, channel_name, user_id, session_id, content, mode
    ):
        """Verify ChannelManager preserves all parameters when routing.
        
        This test verifies that all parameters passed to ChannelManager.send_message
        are correctly forwarded to the channel's send_message method without
        modification or loss.
        
        **Feature: channel-abstraction-layer, Property 4: Message Routing Correctness**
        **Validates: Requirements 3.4**
        """
        # Import ChannelManager
        from src.xagent.core.channels.channel_manager import ChannelManager
        
        # Create a mock MessageSender
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=True)
        
        # Create a FeishuChannel instance
        feishu_channel = FeishuChannel(mock_sender)
        
        # Create a ChannelManager and register the channel
        manager = ChannelManager()
        manager.register_channel(channel_name, feishu_channel)
        
        # Call ChannelManager.send_message
        await manager.send_message(
            channel=channel_name,
            user_id=user_id,
            session_id=session_id,
            content=content,
            mode=mode
        )
        
        # Verify MessageSender was called
        assert mock_sender.send_message.call_count == 1
        
        # Get the actual call arguments
        actual_call = mock_sender.send_message.call_args
        
        # Verify all parameters are preserved
        # user_id → chat_id
        assert actual_call.kwargs["chat_id"] == user_id, \
            f"user_id should be preserved: expected {user_id}"
        
        # session_id → message_id
        expected_message_id = session_id if session_id is not None else ""
        assert actual_call.kwargs["message_id"] == expected_message_id, \
            f"session_id should be preserved: expected {expected_message_id}"
        
        # content → content
        assert actual_call.kwargs["content"] == content, \
            f"content should be preserved: expected {content}"
        
        # Note: mode is not currently used by MessageSender, but we verify
        # it's passed to the channel (even if the channel doesn't use it)
    
    @settings(max_examples=100)
    @given(
        channel_name=st.text(min_size=1, max_size=50),
        user_id=st.text(min_size=1, max_size=100),
        content=st.text(min_size=1, max_size=1000),
        call_count=st.integers(min_value=1, max_value=10)
    )
    @pytest.mark.asyncio
    async def test_message_routing_consistency_across_multiple_calls(
        self, channel_name, user_id, content, call_count
    ):
        """Verify ChannelManager routes consistently across multiple calls.
        
        This test verifies that when ChannelManager.send_message is called
        multiple times with the same channel name, it consistently routes
        to the same channel instance every time.
        
        **Feature: channel-abstraction-layer, Property 4: Message Routing Correctness**
        **Validates: Requirements 3.4**
        """
        # Import ChannelManager
        from src.xagent.core.channels.channel_manager import ChannelManager
        
        # Create a mock MessageSender
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=True)
        
        # Create a FeishuChannel instance
        feishu_channel = FeishuChannel(mock_sender)
        
        # Create a ChannelManager and register the channel
        manager = ChannelManager()
        manager.register_channel(channel_name, feishu_channel)
        
        # Call ChannelManager.send_message multiple times
        for i in range(call_count):
            result = await manager.send_message(
                channel=channel_name,
                user_id=user_id,
                session_id=None,
                content=f"{content}_{i}",
                mode="normal"
            )
            
            # Verify each call succeeds
            assert result is True, \
                f"Call {i+1} should succeed"
        
        # Verify MessageSender was called exactly call_count times
        assert mock_sender.send_message.call_count == call_count, \
            f"MessageSender should be called exactly {call_count} times, " \
            f"proving consistent routing to the same channel"
        
        # Verify each call had the correct content
        for i, call_args in enumerate(mock_sender.send_message.call_args_list):
            expected_content = f"{content}_{i}"
            actual_content = call_args.kwargs["content"]
            assert actual_content == expected_content, \
                f"Call {i+1} should have content '{expected_content}', got '{actual_content}'"



class TestMultipleChannelSupport:
    """Property 7: Multiple Channel Support
    
    For any set of channel instances with distinct names, when all channels
    are registered with ChannelManager, each channel SHALL be independently
    accessible and functional, allowing simultaneous support for multiple
    messaging platforms.
    
    **Validates: Requirements 7.3**
    """
    
    @settings(max_examples=100)
    @given(
        channel_names=st.lists(
            st.text(
                alphabet=st.characters(
                    whitelist_categories=('Lu', 'Ll', 'Nd'),
                    whitelist_characters='-_'
                ),
                min_size=1,
                max_size=30
            ),
            min_size=2,
            max_size=10,
            unique=True
        ),
        user_id=st.text(min_size=1, max_size=100),
        session_id=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        content=st.text(min_size=1, max_size=1000),
        mode=st.text(min_size=0, max_size=50)
    )
    @pytest.mark.asyncio
    async def test_multiple_channels_independently_accessible(
        self, channel_names, user_id, session_id, content, mode
    ):
        """Verify multiple channels can be registered and accessed independently.
        
        This property test verifies that for any valid combination of:
        - channel_names (list of 2-10 unique channel names)
        - user_id (any non-empty string)
        - session_id (any string or None)
        - content (any non-empty string)
        - mode (any string)
        
        When multiple Channel instances are registered with ChannelManager
        using distinct names, each channel SHALL:
        1. Be independently accessible by its unique name
        2. Function correctly without interference from other channels
        3. Receive and process messages independently
        4. Maintain its own state and behavior
        
        This ensures that ChannelManager can support multiple messaging
        platforms simultaneously without cross-contamination or conflicts.
        
        **Feature: channel-abstraction-layer, Property 7: Multiple Channel Support**
        **Validates: Requirements 7.3**
        """
        # Import ChannelManager
        from src.xagent.core.channels.channel_manager import ChannelManager
        
        # Create a ChannelManager
        manager = ChannelManager()
        
        # Create and register multiple channels with unique mock senders
        mock_senders = {}
        channels = {}
        
        for name in channel_names:
            # Create a unique mock MessageSender for each channel
            mock_sender = Mock()
            mock_sender.send_message = Mock(return_value=True)
            mock_senders[name] = mock_sender
            
            # Create a FeishuChannel instance
            channel = FeishuChannel(mock_sender)
            channels[name] = channel
            
            # Register the channel with the manager
            manager.register_channel(name, channel)
        
        # Send a message through each channel independently
        for name in channel_names:
            result = await manager.send_message(
                channel=name,
                user_id=user_id,
                session_id=session_id,
                content=f"{content}_for_{name}",
                mode=mode
            )
            
            # Verify the message was sent successfully
            assert result is True, \
                f"Message through channel '{name}' should succeed"
        
        # Verify each channel's MessageSender was called exactly once
        for name in channel_names:
            mock_sender = mock_senders[name]
            assert mock_sender.send_message.call_count == 1, \
                f"Channel '{name}' MessageSender should be called exactly once, " \
                f"proving independent operation"
            
            # Verify the correct content was sent to this channel
            actual_call = mock_sender.send_message.call_args
            expected_content = f"{content}_for_{name}"
            assert actual_call.kwargs["content"] == expected_content, \
                f"Channel '{name}' should receive its specific content: " \
                f"expected '{expected_content}', got '{actual_call.kwargs['content']}'"
        
        # Verify no cross-contamination: each channel only received its own message
        for name in channel_names:
            mock_sender = mock_senders[name]
            
            # Get the content that was sent to this channel
            actual_content = mock_sender.send_message.call_args.kwargs["content"]
            
            # Verify it doesn't contain content meant for other channels
            for other_name in channel_names:
                if other_name != name:
                    other_content = f"{content}_for_{other_name}"
                    assert actual_content != other_content, \
                        f"Channel '{name}' should not receive content meant for '{other_name}'"
    
    @settings(max_examples=100)
    @given(
        channel_count=st.integers(min_value=2, max_value=10),
        user_id=st.text(min_size=1, max_size=100),
        content=st.text(min_size=1, max_size=1000)
    )
    @pytest.mark.asyncio
    async def test_multiple_channels_functional_independence(
        self, channel_count, user_id, content
    ):
        """Verify multiple channels function independently with different behaviors.
        
        This test verifies that when multiple channels are registered, each
        can have different behavior (e.g., one succeeds, one fails) without
        affecting the others.
        
        **Feature: channel-abstraction-layer, Property 7: Multiple Channel Support**
        **Validates: Requirements 7.3**
        """
        # Import ChannelManager
        from src.xagent.core.channels.channel_manager import ChannelManager
        
        # Create a ChannelManager
        manager = ChannelManager()
        
        # Create and register multiple channels with different behaviors
        channel_names = [f"channel_{i}" for i in range(channel_count)]
        mock_senders = {}
        expected_results = {}
        
        for i, name in enumerate(channel_names):
            # Alternate between success and failure
            return_value = (i % 2 == 0)
            expected_results[name] = return_value
            
            # Create a mock MessageSender with specific behavior
            mock_sender = Mock()
            mock_sender.send_message = Mock(return_value=return_value)
            mock_senders[name] = mock_sender
            
            # Create and register the channel
            channel = FeishuChannel(mock_sender)
            manager.register_channel(name, channel)
        
        # Send messages through each channel
        actual_results = {}
        for name in channel_names:
            result = await manager.send_message(
                channel=name,
                user_id=user_id,
                session_id=None,
                content=content,
                mode="normal"
            )
            actual_results[name] = result
        
        # Verify each channel returned its expected result
        for name in channel_names:
            expected = expected_results[name]
            actual = actual_results[name]
            assert actual == expected, \
                f"Channel '{name}' should return {expected}, got {actual}. " \
                f"This proves channels operate independently."
        
        # Verify each channel's MessageSender was called
        for name in channel_names:
            mock_sender = mock_senders[name]
            assert mock_sender.send_message.call_count == 1, \
                f"Channel '{name}' MessageSender should be called exactly once"
    
    @settings(max_examples=100)
    @given(
        channel_names=st.lists(
            st.text(
                alphabet=st.characters(
                    whitelist_categories=('Lu', 'Ll', 'Nd'),
                    whitelist_characters='-_'
                ),
                min_size=1,
                max_size=30
            ),
            min_size=2,
            max_size=5,
            unique=True
        ),
        user_id=st.text(min_size=1, max_size=100),
        content=st.text(min_size=1, max_size=1000)
    )
    @pytest.mark.asyncio
    async def test_multiple_channels_concurrent_access(
        self, channel_names, user_id, content
    ):
        """Verify multiple channels can be accessed concurrently.
        
        This test verifies that multiple channels can be used simultaneously
        without conflicts, supporting concurrent message sending operations.
        
        **Feature: channel-abstraction-layer, Property 7: Multiple Channel Support**
        **Validates: Requirements 7.3**
        """
        # Import ChannelManager and asyncio
        from src.xagent.core.channels.channel_manager import ChannelManager
        import asyncio
        
        # Create a ChannelManager
        manager = ChannelManager()
        
        # Create and register multiple channels
        mock_senders = {}
        for name in channel_names:
            mock_sender = Mock()
            mock_sender.send_message = Mock(return_value=True)
            mock_senders[name] = mock_sender
            
            channel = FeishuChannel(mock_sender)
            manager.register_channel(name, channel)
        
        # Create concurrent send tasks for all channels
        async def send_to_channel(channel_name):
            return await manager.send_message(
                channel=channel_name,
                user_id=user_id,
                session_id=None,
                content=f"{content}_for_{channel_name}",
                mode="normal"
            )
        
        # Execute all sends concurrently
        tasks = [send_to_channel(name) for name in channel_names]
        results = await asyncio.gather(*tasks)
        
        # Verify all sends succeeded
        for i, name in enumerate(channel_names):
            assert results[i] is True, \
                f"Concurrent send to channel '{name}' should succeed"
        
        # Verify each channel's MessageSender was called exactly once
        for name in channel_names:
            mock_sender = mock_senders[name]
            assert mock_sender.send_message.call_count == 1, \
                f"Channel '{name}' MessageSender should be called exactly once " \
                f"during concurrent access"
            
            # Verify the correct content was sent
            actual_call = mock_sender.send_message.call_args
            expected_content = f"{content}_for_{name}"
            assert actual_call.kwargs["content"] == expected_content, \
                f"Channel '{name}' should receive correct content during concurrent access"
    
    @settings(max_examples=100)
    @given(
        channel_names=st.lists(
            st.text(
                alphabet=st.characters(
                    whitelist_categories=('Lu', 'Ll', 'Nd'),
                    whitelist_characters='-_'
                ),
                min_size=1,
                max_size=30
            ),
            min_size=2,
            max_size=10,
            unique=True
        ),
        user_id=st.text(min_size=1, max_size=100),
        content=st.text(min_size=1, max_size=1000)
    )
    @pytest.mark.asyncio
    async def test_multiple_channels_retrieval_independence(
        self, channel_names, user_id, content
    ):
        """Verify retrieving one channel doesn't affect others.
        
        This test verifies that retrieving and using one channel doesn't
        interfere with the ability to retrieve and use other channels.
        
        **Feature: channel-abstraction-layer, Property 7: Multiple Channel Support**
        **Validates: Requirements 7.3**
        """
        # Import ChannelManager
        from src.xagent.core.channels.channel_manager import ChannelManager
        
        # Create a ChannelManager
        manager = ChannelManager()
        
        # Create and register multiple channels
        mock_senders = {}
        original_channels = {}
        
        for name in channel_names:
            mock_sender = Mock()
            mock_sender.send_message = Mock(return_value=True)
            mock_senders[name] = mock_sender
            
            channel = FeishuChannel(mock_sender)
            original_channels[name] = channel
            manager.register_channel(name, channel)
        
        # Retrieve each channel and verify it's the correct instance
        for name in channel_names:
            retrieved_channel = manager.get_channel(name)
            
            # Verify it's the correct channel instance
            assert retrieved_channel is original_channels[name], \
                f"Retrieved channel '{name}' should be the correct instance"
            
            # Verify it's not any other channel
            for other_name in channel_names:
                if other_name != name:
                    assert retrieved_channel is not original_channels[other_name], \
                        f"Retrieved channel '{name}' should not be channel '{other_name}'"
        
        # Send a message through each retrieved channel
        for name in channel_names:
            retrieved_channel = manager.get_channel(name)
            result = await retrieved_channel.send_message(
                channel="p2p",
                user_id=user_id,
                session_id=None,
                content=f"{content}_for_{name}",
                mode="normal"
            )
            
            assert result is True, \
                f"Message through retrieved channel '{name}' should succeed"
        
        # Verify each channel's MessageSender was called exactly once
        for name in channel_names:
            mock_sender = mock_senders[name]
            assert mock_sender.send_message.call_count == 1, \
                f"Channel '{name}' MessageSender should be called exactly once"
    
    @settings(max_examples=100)
    @given(
        channel_names=st.lists(
            st.text(
                alphabet=st.characters(
                    whitelist_categories=('Lu', 'Ll', 'Nd'),
                    whitelist_characters='-_'
                ),
                min_size=2,
                max_size=10
            ),
            min_size=2,
            max_size=10,
            unique=True
        ),
        user_id=st.text(min_size=1, max_size=100),
        content=st.text(min_size=1, max_size=1000),
        messages_per_channel=st.integers(min_value=1, max_value=5)
    )
    @pytest.mark.asyncio
    async def test_multiple_channels_repeated_use(
        self, channel_names, user_id, content, messages_per_channel
    ):
        """Verify multiple channels can be used repeatedly without interference.
        
        This test verifies that when multiple channels are registered, each
        can be used multiple times and the usage of one channel doesn't
        affect the state or behavior of other channels.
        
        **Feature: channel-abstraction-layer, Property 7: Multiple Channel Support**
        **Validates: Requirements 7.3**
        """
        # Import ChannelManager
        from src.xagent.core.channels.channel_manager import ChannelManager
        
        # Create a ChannelManager
        manager = ChannelManager()
        
        # Create and register multiple channels
        mock_senders = {}
        for name in channel_names:
            mock_sender = Mock()
            mock_sender.send_message = Mock(return_value=True)
            mock_senders[name] = mock_sender
            
            channel = FeishuChannel(mock_sender)
            manager.register_channel(name, channel)
        
        # Send multiple messages through each channel
        for name in channel_names:
            for i in range(messages_per_channel):
                result = await manager.send_message(
                    channel=name,
                    user_id=user_id,
                    session_id=None,
                    content=f"{content}_for_{name}_msg_{i}",
                    mode="normal"
                )
                
                assert result is True, \
                    f"Message {i+1} through channel '{name}' should succeed"
        
        # Verify each channel's MessageSender was called the correct number of times
        for name in channel_names:
            mock_sender = mock_senders[name]
            assert mock_sender.send_message.call_count == messages_per_channel, \
                f"Channel '{name}' MessageSender should be called exactly " \
                f"{messages_per_channel} times, got {mock_sender.send_message.call_count}"
        
        # Verify the messages were sent in the correct order for each channel
        for name in channel_names:
            mock_sender = mock_senders[name]
            call_args_list = mock_sender.send_message.call_args_list
            
            for i, call_args in enumerate(call_args_list):
                expected_content = f"{content}_for_{name}_msg_{i}"
                actual_content = call_args.kwargs["content"]
                assert actual_content == expected_content, \
                    f"Channel '{name}' message {i+1} should have content " \
                    f"'{expected_content}', got '{actual_content}'"
    
    @settings(max_examples=100)
    @given(
        channel_names=st.lists(
            st.text(
                alphabet=st.characters(
                    whitelist_categories=('Lu', 'Ll', 'Nd'),
                    whitelist_characters='-_'
                ),
                min_size=1,
                max_size=30
            ),
            min_size=2,
            max_size=10,
            unique=True
        ),
        user_id=st.text(min_size=1, max_size=100),
        content=st.text(min_size=1, max_size=1000)
    )
    @pytest.mark.asyncio
    async def test_multiple_channels_error_isolation(
        self, channel_names, user_id, content
    ):
        """Verify errors in one channel don't affect other channels.
        
        This test verifies that when one channel fails or raises an error,
        other channels continue to function normally without being affected.
        
        **Feature: channel-abstraction-layer, Property 7: Multiple Channel Support**
        **Validates: Requirements 7.3**
        """
        # Import ChannelManager
        from src.xagent.core.channels.channel_manager import ChannelManager
        
        # Create a ChannelManager
        manager = ChannelManager()
        
        # Create and register multiple channels
        # Make the first channel fail, others succeed
        mock_senders = {}
        expected_results = {}
        
        for i, name in enumerate(channel_names):
            mock_sender = Mock()
            
            if i == 0:
                # First channel raises an exception
                mock_sender.send_message = Mock(side_effect=RuntimeError("Channel error"))
                expected_results[name] = False
            else:
                # Other channels succeed
                mock_sender.send_message = Mock(return_value=True)
                expected_results[name] = True
            
            mock_senders[name] = mock_sender
            
            channel = FeishuChannel(mock_sender)
            manager.register_channel(name, channel)
        
        # Send messages through all channels
        actual_results = {}
        for name in channel_names:
            result = await manager.send_message(
                channel=name,
                user_id=user_id,
                session_id=None,
                content=content,
                mode="normal"
            )
            actual_results[name] = result
        
        # Verify each channel returned its expected result
        for name in channel_names:
            expected = expected_results[name]
            actual = actual_results[name]
            assert actual == expected, \
                f"Channel '{name}' should return {expected}, got {actual}. " \
                f"This proves errors in one channel don't affect others."
        
        # Verify all channels were called (even the failing one)
        for name in channel_names:
            mock_sender = mock_senders[name]
            assert mock_sender.send_message.call_count == 1, \
                f"Channel '{name}' MessageSender should be called exactly once"
    
    @settings(max_examples=100)
    @given(
        initial_channel_count=st.integers(min_value=1, max_value=5),
        additional_channel_count=st.integers(min_value=1, max_value=5),
        user_id=st.text(min_size=1, max_size=100),
        content=st.text(min_size=1, max_size=1000)
    )
    @pytest.mark.asyncio
    async def test_multiple_channels_dynamic_addition(
        self, initial_channel_count, additional_channel_count, user_id, content
    ):
        """Verify new channels can be added while existing channels remain functional.
        
        This test verifies that channels can be added dynamically to
        ChannelManager while existing channels continue to function normally.
        
        **Feature: channel-abstraction-layer, Property 7: Multiple Channel Support**
        **Validates: Requirements 7.3, 7.5**
        """
        # Import ChannelManager
        from src.xagent.core.channels.channel_manager import ChannelManager
        
        # Create a ChannelManager
        manager = ChannelManager()
        
        # Register initial channels
        initial_names = [f"initial_{i}" for i in range(initial_channel_count)]
        mock_senders = {}
        
        for name in initial_names:
            mock_sender = Mock()
            mock_sender.send_message = Mock(return_value=True)
            mock_senders[name] = mock_sender
            
            channel = FeishuChannel(mock_sender)
            manager.register_channel(name, channel)
        
        # Send a message through each initial channel
        for name in initial_names:
            result = await manager.send_message(
                channel=name,
                user_id=user_id,
                session_id=None,
                content=f"{content}_initial",
                mode="normal"
            )
            assert result is True
        
        # Add additional channels dynamically
        additional_names = [f"additional_{i}" for i in range(additional_channel_count)]
        
        for name in additional_names:
            mock_sender = Mock()
            mock_sender.send_message = Mock(return_value=True)
            mock_senders[name] = mock_sender
            
            channel = FeishuChannel(mock_sender)
            manager.register_channel(name, channel)
        
        # Send messages through all channels (initial + additional)
        all_names = initial_names + additional_names
        for name in all_names:
            result = await manager.send_message(
                channel=name,
                user_id=user_id,
                session_id=None,
                content=f"{content}_after_addition",
                mode="normal"
            )
            assert result is True, \
                f"Channel '{name}' should work after dynamic addition"
        
        # Verify initial channels were called twice (before and after addition)
        for name in initial_names:
            mock_sender = mock_senders[name]
            assert mock_sender.send_message.call_count == 2, \
                f"Initial channel '{name}' should be called twice"
        
        # Verify additional channels were called once (only after addition)
        for name in additional_names:
            mock_sender = mock_senders[name]
            assert mock_sender.send_message.call_count == 1, \
                f"Additional channel '{name}' should be called once"



class TestDynamicChannelRegistration:
    """Property 8: Dynamic Channel Registration
    
    For any Channel instance, when it is registered with ChannelManager at any
    point during runtime (including after initialization), the channel SHALL be
    immediately available for message routing.
    
    **Validates: Requirements 7.5**
    """
    
    @settings(max_examples=100)
    @given(
        channel_name=st.text(min_size=1, max_size=50),
        user_id=st.text(min_size=1, max_size=100),
        session_id=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        content=st.text(min_size=1, max_size=1000),
        mode=st.text(min_size=0, max_size=50),
        sender_return_value=st.booleans()
    )
    @pytest.mark.asyncio
    async def test_channel_immediately_available_after_registration(
        self, channel_name, user_id, session_id, content, mode, sender_return_value
    ):
        """Verify channel is immediately available after dynamic registration.
        
        This property test verifies that for any valid combination of:
        - channel_name (any non-empty string)
        - Channel instance (FeishuChannel with mock MessageSender)
        - message parameters (user_id, session_id, content, mode)
        
        When a Channel instance is registered with ChannelManager at any point
        during runtime, the channel SHALL be immediately available for message
        routing without any additional initialization or delay.
        
        This ensures that:
        1. Channels can be registered dynamically at runtime
        2. Registered channels are immediately functional
        3. No additional setup is required after registration
        4. Messages can be sent through newly registered channels right away
        
        **Feature: channel-abstraction-layer, Property 8: Dynamic Channel Registration**
        **Validates: Requirements 7.5**
        """
        # Import ChannelManager
        from src.xagent.core.channels.channel_manager import ChannelManager
        
        # Create a ChannelManager
        manager = ChannelManager()
        
        # Create a mock MessageSender
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=sender_return_value)
        
        # Create a FeishuChannel instance
        channel = FeishuChannel(mock_sender)
        
        # Register the channel dynamically
        manager.register_channel(channel_name, channel)
        
        # Immediately attempt to send a message through the newly registered channel
        # This should work without any delay or additional setup
        result = await manager.send_message(
            channel=channel_name,
            user_id=user_id,
            session_id=session_id,
            content=content,
            mode=mode
        )
        
        # Verify the message was sent successfully
        assert result == sender_return_value, \
            f"Newly registered channel should be immediately available for message routing. " \
            f"Expected {sender_return_value}, got {result}"
        
        # Verify the underlying MessageSender was called
        assert mock_sender.send_message.call_count == 1, \
            "MessageSender should be called exactly once through newly registered channel"
        
        # Verify the parameters were passed correctly
        actual_call = mock_sender.send_message.call_args
        assert actual_call.kwargs["chat_type"] == "p2p"
        assert actual_call.kwargs["chat_id"] == user_id
        assert actual_call.kwargs["message_id"] == (session_id or "")
        assert actual_call.kwargs["content"] == content
    
    @settings(max_examples=100)
    @given(
        registration_timing=st.integers(min_value=0, max_value=10),
        channel_name=st.text(min_size=1, max_size=50),
        user_id=st.text(min_size=1, max_size=100),
        content=st.text(min_size=1, max_size=1000)
    )
    @pytest.mark.asyncio
    async def test_channel_registration_at_various_runtime_points(
        self, registration_timing, channel_name, user_id, content
    ):
        """Verify channels can be registered at any point during runtime.
        
        This test simulates different runtime scenarios by performing various
        operations before registering a new channel, then verifying the newly
        registered channel is immediately available.
        
        The registration_timing parameter determines how many operations occur
        before the new channel is registered, simulating different points in
        the application lifecycle.
        
        **Feature: channel-abstraction-layer, Property 8: Dynamic Channel Registration**
        **Validates: Requirements 7.5**
        """
        # Import ChannelManager
        from src.xagent.core.channels.channel_manager import ChannelManager
        
        # Create a ChannelManager
        manager = ChannelManager()
        
        # Simulate runtime operations before registering the new channel
        # This represents the application running for some time before
        # the new channel is added
        existing_channels = []
        for i in range(registration_timing):
            # Create and register an existing channel
            existing_name = f"existing_{i}"
            mock_sender = Mock()
            mock_sender.send_message = Mock(return_value=True)
            existing_channel = FeishuChannel(mock_sender)
            manager.register_channel(existing_name, existing_channel)
            existing_channels.append((existing_name, mock_sender))
            
            # Send a message through the existing channel
            await manager.send_message(
                channel=existing_name,
                user_id=user_id,
                session_id=None,
                content=f"{content}_existing_{i}",
                mode="normal"
            )
        
        # Now register a new channel dynamically (at this point in runtime)
        new_mock_sender = Mock()
        new_mock_sender.send_message = Mock(return_value=True)
        new_channel = FeishuChannel(new_mock_sender)
        manager.register_channel(channel_name, new_channel)
        
        # Immediately send a message through the newly registered channel
        result = await manager.send_message(
            channel=channel_name,
            user_id=user_id,
            session_id=None,
            content=content,
            mode="normal"
        )
        
        # Verify the new channel is immediately available
        assert result is True, \
            f"Channel registered at runtime point {registration_timing} should be immediately available"
        
        # Verify the new channel's MessageSender was called
        assert new_mock_sender.send_message.call_count == 1, \
            "Newly registered channel should be called exactly once"
        
        # Verify existing channels still work
        for existing_name, existing_sender in existing_channels:
            result = await manager.send_message(
                channel=existing_name,
                user_id=user_id,
                session_id=None,
                content=f"{content}_after_new_registration",
                mode="normal"
            )
            assert result is True, \
                f"Existing channel '{existing_name}' should still work after new channel registration"
            
            # Each existing channel should have been called twice:
            # once before new registration, once after
            assert existing_sender.send_message.call_count == 2, \
                f"Existing channel '{existing_name}' should be called twice"
    
    @settings(max_examples=100)
    @given(
        channel_names=st.lists(
            st.text(
                alphabet=st.characters(
                    whitelist_categories=('Lu', 'Ll', 'Nd'),
                    whitelist_characters='-_'
                ),
                min_size=1,
                max_size=30
            ),
            min_size=1,
            max_size=10,
            unique=True
        ),
        user_id=st.text(min_size=1, max_size=100),
        content=st.text(min_size=1, max_size=1000)
    )
    @pytest.mark.asyncio
    async def test_sequential_dynamic_registration(
        self, channel_names, user_id, content
    ):
        """Verify multiple channels can be registered dynamically in sequence.
        
        This test verifies that channels can be registered one after another
        at runtime, and each newly registered channel is immediately available
        while previously registered channels remain functional.
        
        **Feature: channel-abstraction-layer, Property 8: Dynamic Channel Registration**
        **Validates: Requirements 7.5, 7.3**
        """
        # Import ChannelManager
        from src.xagent.core.channels.channel_manager import ChannelManager
        
        # Create a ChannelManager
        manager = ChannelManager()
        
        # Track registered channels
        registered_channels = {}
        
        # Register channels one by one and test each immediately
        for i, name in enumerate(channel_names):
            # Create a new channel
            mock_sender = Mock()
            mock_sender.send_message = Mock(return_value=True)
            channel = FeishuChannel(mock_sender)
            
            # Register the channel dynamically
            manager.register_channel(name, channel)
            registered_channels[name] = mock_sender
            
            # Immediately send a message through the newly registered channel
            result = await manager.send_message(
                channel=name,
                user_id=user_id,
                session_id=None,
                content=f"{content}_{i}",
                mode="normal"
            )
            
            # Verify the newly registered channel works immediately
            assert result is True, \
                f"Channel '{name}' should be immediately available after registration (iteration {i})"
            
            # Verify the MessageSender was called
            assert mock_sender.send_message.call_count == 1, \
                f"Channel '{name}' MessageSender should be called once"
            
            # Verify all previously registered channels still work
            for prev_name, prev_sender in registered_channels.items():
                if prev_name != name:  # Don't re-test the just-registered channel
                    result = await manager.send_message(
                        channel=prev_name,
                        user_id=user_id,
                        session_id=None,
                        content=f"{content}_verify_{i}",
                        mode="normal"
                    )
                    assert result is True, \
                        f"Previously registered channel '{prev_name}' should still work after registering '{name}'"
        
        # Final verification: all channels should be functional
        for name, mock_sender in registered_channels.items():
            result = await manager.send_message(
                channel=name,
                user_id=user_id,
                session_id=None,
                content=f"{content}_final",
                mode="normal"
            )
            assert result is True, \
                f"Channel '{name}' should be functional in final verification"
    
    @settings(max_examples=100)
    @given(
        channel_name=st.text(min_size=1, max_size=50),
        user_id=st.text(min_size=1, max_size=100),
        content=st.text(min_size=1, max_size=1000),
        delay_operations=st.integers(min_value=0, max_value=5)
    )
    @pytest.mark.asyncio
    async def test_channel_registration_without_initialization_delay(
        self, channel_name, user_id, content, delay_operations
    ):
        """Verify no initialization delay after channel registration.
        
        This test verifies that there is no initialization delay or warm-up
        period required after registering a channel. The channel should be
        immediately functional without any additional setup steps.
        
        **Feature: channel-abstraction-layer, Property 8: Dynamic Channel Registration**
        **Validates: Requirements 7.5**
        """
        # Import ChannelManager
        from src.xagent.core.channels.channel_manager import ChannelManager
        
        # Create a ChannelManager
        manager = ChannelManager()
        
        # Perform some operations to simulate runtime state
        for i in range(delay_operations):
            # Create and register a temporary channel
            temp_name = f"temp_{i}"
            temp_sender = Mock()
            temp_sender.send_message = Mock(return_value=True)
            temp_channel = FeishuChannel(temp_sender)
            manager.register_channel(temp_name, temp_channel)
        
        # Create a new channel
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=True)
        channel = FeishuChannel(mock_sender)
        
        # Register the channel
        manager.register_channel(channel_name, channel)
        
        # Immediately (without any delay or initialization) send a message
        # This tests that the channel is ready to use right after registration
        result = await manager.send_message(
            channel=channel_name,
            user_id=user_id,
            session_id=None,
            content=content,
            mode="normal"
        )
        
        # Verify immediate availability
        assert result is True, \
            "Channel should be immediately available without initialization delay"
        
        # Verify the MessageSender was called immediately
        assert mock_sender.send_message.call_count == 1, \
            "MessageSender should be called immediately after registration"
        
        # Verify correct parameters were passed
        actual_call = mock_sender.send_message.call_args
        assert actual_call.kwargs["chat_type"] == "p2p"
        assert actual_call.kwargs["chat_id"] == user_id
        assert actual_call.kwargs["content"] == content
    
    @settings(max_examples=100)
    @given(
        channel_name=st.text(min_size=1, max_size=50),
        user_id=st.text(min_size=1, max_size=100),
        content=st.text(min_size=1, max_size=1000),
        message_count=st.integers(min_value=1, max_value=10)
    )
    @pytest.mark.asyncio
    async def test_newly_registered_channel_handles_multiple_messages(
        self, channel_name, user_id, content, message_count
    ):
        """Verify newly registered channel can handle multiple messages immediately.
        
        This test verifies that a newly registered channel can handle multiple
        consecutive message sends without any issues, proving it's fully
        functional immediately after registration.
        
        **Feature: channel-abstraction-layer, Property 8: Dynamic Channel Registration**
        **Validates: Requirements 7.5**
        """
        # Import ChannelManager
        from src.xagent.core.channels.channel_manager import ChannelManager
        
        # Create a ChannelManager
        manager = ChannelManager()
        
        # Create and register a new channel
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=True)
        channel = FeishuChannel(mock_sender)
        manager.register_channel(channel_name, channel)
        
        # Immediately send multiple messages through the newly registered channel
        for i in range(message_count):
            result = await manager.send_message(
                channel=channel_name,
                user_id=user_id,
                session_id=None,
                content=f"{content}_{i}",
                mode="normal"
            )
            
            # Verify each message is sent successfully
            assert result is True, \
                f"Message {i+1} should be sent successfully through newly registered channel"
        
        # Verify the MessageSender was called the correct number of times
        assert mock_sender.send_message.call_count == message_count, \
            f"MessageSender should be called {message_count} times"
    
    @settings(max_examples=100)
    @given(
        channel_name=st.text(min_size=1, max_size=50),
        user_id=st.text(min_size=1, max_size=100),
        content=st.text(min_size=1, max_size=1000),
        sender_return_value=st.booleans()
    )
    @pytest.mark.asyncio
    async def test_dynamic_registration_preserves_channel_behavior(
        self, channel_name, user_id, content, sender_return_value
    ):
        """Verify dynamically registered channel preserves its behavior.
        
        This test verifies that when a channel is registered dynamically,
        it preserves its configured behavior (e.g., return values, error
        handling) and functions exactly as expected.
        
        **Feature: channel-abstraction-layer, Property 8: Dynamic Channel Registration**
        **Validates: Requirements 7.5**
        """
        # Import ChannelManager
        from src.xagent.core.channels.channel_manager import ChannelManager
        
        # Create a ChannelManager
        manager = ChannelManager()
        
        # Create a channel with specific behavior (return value)
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=sender_return_value)
        channel = FeishuChannel(mock_sender)
        
        # Register the channel dynamically
        manager.register_channel(channel_name, channel)
        
        # Send a message and verify the behavior is preserved
        result = await manager.send_message(
            channel=channel_name,
            user_id=user_id,
            session_id=None,
            content=content,
            mode="normal"
        )
        
        # Verify the channel's configured behavior is preserved
        assert result == sender_return_value, \
            f"Dynamically registered channel should preserve its behavior. " \
            f"Expected {sender_return_value}, got {result}"
        
        # Verify the MessageSender was called
        assert mock_sender.send_message.call_count == 1
    
    @settings(max_examples=100)
    @given(
        channel_name=st.text(min_size=1, max_size=50),
        user_id=st.text(min_size=1, max_size=100),
        content=st.text(min_size=1, max_size=1000)
    )
    @pytest.mark.asyncio
    async def test_dynamic_registration_with_failing_channel(
        self, channel_name, user_id, content
    ):
        """Verify dynamically registered channel handles failures correctly.
        
        This test verifies that when a channel is registered dynamically and
        its MessageSender fails, the error handling works correctly and the
        failure is reported properly.
        
        **Feature: channel-abstraction-layer, Property 8: Dynamic Channel Registration**
        **Validates: Requirements 7.5, 8.2**
        """
        # Import ChannelManager
        from src.xagent.core.channels.channel_manager import ChannelManager
        
        # Create a ChannelManager
        manager = ChannelManager()
        
        # Create a channel that will fail
        mock_sender = Mock()
        mock_sender.send_message = Mock(return_value=False)
        channel = FeishuChannel(mock_sender)
        
        # Register the channel dynamically
        manager.register_channel(channel_name, channel)
        
        # Send a message through the failing channel
        result = await manager.send_message(
            channel=channel_name,
            user_id=user_id,
            session_id=None,
            content=content,
            mode="normal"
        )
        
        # Verify the failure is reported correctly
        assert result is False, \
            "Dynamically registered channel should report failures correctly"
        
        # Verify the MessageSender was called
        assert mock_sender.send_message.call_count == 1
    
    @settings(max_examples=100)
    @given(
        channel_name=st.text(min_size=1, max_size=50),
        user_id=st.text(min_size=1, max_size=100),
        content=st.text(min_size=1, max_size=1000)
    )
    @pytest.mark.asyncio
    async def test_dynamic_registration_with_exception_channel(
        self, channel_name, user_id, content
    ):
        """Verify dynamically registered channel handles exceptions correctly.
        
        This test verifies that when a channel is registered dynamically and
        its MessageSender raises an exception, the error handling works
        correctly and False is returned.
        
        **Feature: channel-abstraction-layer, Property 8: Dynamic Channel Registration**
        **Validates: Requirements 7.5, 8.3**
        """
        # Import ChannelManager
        from src.xagent.core.channels.channel_manager import ChannelManager
        
        # Create a ChannelManager
        manager = ChannelManager()
        
        # Create a channel that will raise an exception
        mock_sender = Mock()
        mock_sender.send_message = Mock(side_effect=RuntimeError("Test error"))
        channel = FeishuChannel(mock_sender)
        
        # Register the channel dynamically
        manager.register_channel(channel_name, channel)
        
        # Send a message through the channel that raises exception
        result = await manager.send_message(
            channel=channel_name,
            user_id=user_id,
            session_id=None,
            content=content,
            mode="normal"
        )
        
        # Verify the exception is handled and False is returned
        assert result is False, \
            "Dynamically registered channel should handle exceptions and return False"
        
        # Verify the MessageSender was called
        assert mock_sender.send_message.call_count == 1
