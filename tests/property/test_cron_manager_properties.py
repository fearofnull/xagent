"""
Property tests for CronManager parameter forwarding.

This module contains property-based tests using Hypothesis to verify that
CronManager correctly forwards all message parameters to ChannelManager
without modification.

**Feature: channel-abstraction-layer, Property 5: CronManager Parameter Forwarding**
**Validates: Requirements 4.5**
"""
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, AsyncMock, patch
from src.xagent.core.crons.manager import CronManager
from src.xagent.core.crons.models import (
    CronJobSpec,
    CronJobDispatch,
    CronJobTarget,
    CronJobSchedule,
    CronJobRuntime
)


class TestCronManagerParameterForwarding:
    """Property 5: CronManager Parameter Forwarding
    
    For any message parameters (channel, user_id, session_id, content, mode),
    when CronManager sends a message, all parameters SHALL be forwarded
    correctly to ChannelManager.send_message without modification.
    
    **Validates: Requirements 4.5**
    """
    
    @settings(max_examples=100)
    @given(
        channel=st.text(min_size=1, max_size=50),
        user_id=st.text(min_size=1, max_size=100),
        session_id=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        content=st.text(min_size=1, max_size=1000),
        mode=st.text(min_size=1, max_size=50)
    )
    @pytest.mark.asyncio
    async def test_text_task_parameter_forwarding(
        self, channel, user_id, session_id, content, mode
    ):
        """Verify CronManager forwards all parameters correctly for text tasks.
        
        This property test verifies that for any valid combination of:
        - channel (any non-empty string)
        - user_id (any non-empty string)
        - session_id (any string or None)
        - content (any non-empty string)
        - mode (any non-empty string)
        
        When CronManager executes a text task, all parameters are forwarded
        to ChannelManager.send_message without modification.
        
        **Feature: channel-abstraction-layer, Property 5: CronManager Parameter Forwarding**
        **Validates: Requirements 4.5**
        """
        # Create a mock ChannelManager
        mock_channel_manager = Mock()
        mock_channel_manager.send_message = AsyncMock(return_value=True)
        
        # Create a mock runner (not used for text tasks)
        mock_runner = Mock()
        
        # Create CronManager with mocks
        cron_manager = CronManager(
            runner=mock_runner,
            channel_manager=mock_channel_manager
        )
        
        # Create a text task with the generated parameters
        job_spec = CronJobSpec(
            id="test_job",
            name="Test Job",
            enabled=True,
            task_type="text",
            text=content,
            dispatch=CronJobDispatch(
                type="channel",
                channel=channel,
                target=CronJobTarget(
                    user_id=user_id,
                    session_id=session_id
                ),
                mode=mode
            ),
            schedule=CronJobSchedule(
                type="cron",
                cron="0 0 * * *",
                timezone="UTC"
            ),
            runtime=CronJobRuntime(
                max_concurrency=1,
                timeout_seconds=120
            )
        )
        
        # Execute the task
        await cron_manager._executor.execute(job_spec)
        
        # Verify ChannelManager.send_message was called exactly once
        assert mock_channel_manager.send_message.call_count == 1, \
            "ChannelManager.send_message should be called exactly once"
        
        # Get the actual call arguments
        actual_call = mock_channel_manager.send_message.call_args
        
        # Verify all parameters are forwarded without modification
        assert actual_call.kwargs["channel"] == channel, \
            f"channel parameter should be forwarded unchanged: expected {channel}, got {actual_call.kwargs['channel']}"
        
        assert actual_call.kwargs["user_id"] == user_id, \
            f"user_id parameter should be forwarded unchanged: expected {user_id}, got {actual_call.kwargs['user_id']}"
        
        assert actual_call.kwargs["session_id"] == session_id, \
            f"session_id parameter should be forwarded unchanged: expected {session_id}, got {actual_call.kwargs['session_id']}"
        
        assert actual_call.kwargs["content"] == content, \
            f"content parameter should be forwarded unchanged: expected {content}, got {actual_call.kwargs['content']}"
        
        assert actual_call.kwargs["mode"] == mode, \
            f"mode parameter should be forwarded unchanged: expected {mode}, got {actual_call.kwargs['mode']}"
    
    @settings(max_examples=100)
    @given(
        channel=st.text(min_size=1, max_size=50),
        user_id=st.text(min_size=1, max_size=100),
        session_id=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        mode=st.text(min_size=1, max_size=50),
        agent_response=st.text(min_size=1, max_size=500)
    )
    @pytest.mark.asyncio
    async def test_agent_task_parameter_forwarding(
        self, channel, user_id, session_id, mode, agent_response
    ):
        """Verify CronManager forwards all parameters correctly for agent tasks.
        
        This property test verifies that for any valid combination of:
        - channel (any non-empty string)
        - user_id (any non-empty string)
        - session_id (any string or None)
        - mode (any non-empty string)
        - agent_response (any non-empty string)
        
        When CronManager executes an agent task, all parameters are forwarded
        to ChannelManager.send_message without modification, with the content
        being the agent's response.
        
        **Feature: channel-abstraction-layer, Property 5: CronManager Parameter Forwarding**
        **Validates: Requirements 4.5**
        """
        # Create a mock ChannelManager
        mock_channel_manager = Mock()
        mock_channel_manager.send_message = AsyncMock(return_value=True)
        
        # Create a mock runner that returns the agent_response
        mock_runner = Mock()
        mock_runner.run = AsyncMock(return_value=agent_response)
        
        # Create CronManager with mocks
        cron_manager = CronManager(
            runner=mock_runner,
            channel_manager=mock_channel_manager
        )
        
        # Create an agent task with the generated parameters
        from src.xagent.core.crons.models import CronJobRequest, CronJobRequestInput
        
        job_spec = CronJobSpec(
            id="test_agent_job",
            name="Test Agent Job",
            enabled=True,
            task_type="agent",
            request=CronJobRequest(
                input=[
                    CronJobRequestInput(
                        role="user",
                        type="text",
                        content=[{"text": "test input"}]
                    )
                ],
                session_id="test_session",
                user_id="test_user"
            ),
            dispatch=CronJobDispatch(
                type="channel",
                channel=channel,
                target=CronJobTarget(
                    user_id=user_id,
                    session_id=session_id
                ),
                mode=mode
            ),
            schedule=CronJobSchedule(
                type="cron",
                cron="0 0 * * *",
                timezone="UTC"
            ),
            runtime=CronJobRuntime(
                max_concurrency=1,
                timeout_seconds=120
            )
        )
        
        # Execute the task
        await cron_manager._executor.execute(job_spec)
        
        # Verify ChannelManager.send_message was called exactly once
        assert mock_channel_manager.send_message.call_count == 1, \
            "ChannelManager.send_message should be called exactly once"
        
        # Get the actual call arguments
        actual_call = mock_channel_manager.send_message.call_args
        
        # Verify all parameters are forwarded without modification
        assert actual_call.kwargs["channel"] == channel, \
            f"channel parameter should be forwarded unchanged: expected {channel}, got {actual_call.kwargs['channel']}"
        
        assert actual_call.kwargs["user_id"] == user_id, \
            f"user_id parameter should be forwarded unchanged: expected {user_id}, got {actual_call.kwargs['user_id']}"
        
        assert actual_call.kwargs["session_id"] == session_id, \
            f"session_id parameter should be forwarded unchanged: expected {session_id}, got {actual_call.kwargs['session_id']}"
        
        # For agent tasks, content should be the agent's response
        assert actual_call.kwargs["content"] == agent_response, \
            f"content parameter should be the agent response: expected {agent_response}, got {actual_call.kwargs['content']}"
        
        assert actual_call.kwargs["mode"] == mode, \
            f"mode parameter should be forwarded unchanged: expected {mode}, got {actual_call.kwargs['mode']}"
    
    @settings(max_examples=100)
    @given(
        channel=st.text(min_size=1, max_size=50),
        user_id=st.text(min_size=1, max_size=100),
        content=st.text(min_size=1, max_size=1000),
        mode=st.text(min_size=1, max_size=50)
    )
    @pytest.mark.asyncio
    async def test_parameter_forwarding_with_none_session_id(
        self, channel, user_id, content, mode
    ):
        """Verify CronManager forwards None session_id correctly.
        
        When session_id is None, it should be forwarded as None to
        ChannelManager.send_message without modification.
        
        **Feature: channel-abstraction-layer, Property 5: CronManager Parameter Forwarding**
        **Validates: Requirements 4.5**
        """
        # Create a mock ChannelManager
        mock_channel_manager = Mock()
        mock_channel_manager.send_message = AsyncMock(return_value=True)
        
        # Create a mock runner
        mock_runner = Mock()
        
        # Create CronManager with mocks
        cron_manager = CronManager(
            runner=mock_runner,
            channel_manager=mock_channel_manager
        )
        
        # Create a text task with None session_id
        job_spec = CronJobSpec(
            id="test_job_none_session",
            name="Test Job None Session",
            enabled=True,
            task_type="text",
            text=content,
            dispatch=CronJobDispatch(
                type="channel",
                channel=channel,
                target=CronJobTarget(
                    user_id=user_id,
                    session_id=None
                ),
                mode=mode
            ),
            schedule=CronJobSchedule(
                type="cron",
                cron="0 0 * * *",
                timezone="UTC"
            ),
            runtime=CronJobRuntime(
                max_concurrency=1,
                timeout_seconds=120
            )
        )
        
        # Execute the task
        await cron_manager._executor.execute(job_spec)
        
        # Verify ChannelManager.send_message was called
        assert mock_channel_manager.send_message.call_count == 1
        
        # Get the actual call arguments
        actual_call = mock_channel_manager.send_message.call_args
        
        # Verify session_id is None (not converted to empty string or other value)
        assert actual_call.kwargs["session_id"] is None, \
            f"session_id should be forwarded as None, got {actual_call.kwargs['session_id']}"



class TestCronManagerErrorResilience:
    """Property 10: CronManager Error Resilience
    
    For any channel send failure, when CronManager attempts to send a message
    and the operation fails, CronManager SHALL handle the failure gracefully
    and continue operating without crashing.
    
    **Validates: Requirements 8.5**
    """
    
    @settings(max_examples=100)
    @given(
        channel=st.text(min_size=1, max_size=50),
        user_id=st.text(min_size=1, max_size=100),
        session_id=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        content=st.text(min_size=1, max_size=1000),
        mode=st.text(min_size=1, max_size=50)
    )
    @pytest.mark.asyncio
    async def test_text_task_handles_channel_send_failure(
        self, channel, user_id, session_id, content, mode
    ):
        """Verify CronManager handles channel send failures gracefully for text tasks.
        
        This property test verifies that for any valid combination of parameters,
        when ChannelManager.send_message returns False (indicating failure),
        CronManager SHALL:
        1. Not crash or raise an exception
        2. Complete the task execution
        3. Continue operating normally
        
        **Feature: channel-abstraction-layer, Property 10: CronManager Error Resilience**
        **Validates: Requirements 8.5**
        """
        # Create a mock ChannelManager that always returns False (failure)
        mock_channel_manager = Mock()
        mock_channel_manager.send_message = AsyncMock(return_value=False)
        
        # Create a mock runner
        mock_runner = Mock()
        
        # Create CronManager with mocks
        cron_manager = CronManager(
            runner=mock_runner,
            channel_manager=mock_channel_manager
        )
        
        # Create a text task
        job_spec = CronJobSpec(
            id="test_job_failure",
            name="Test Job Failure",
            enabled=True,
            task_type="text",
            text=content,
            dispatch=CronJobDispatch(
                type="channel",
                channel=channel,
                target=CronJobTarget(
                    user_id=user_id,
                    session_id=session_id
                ),
                mode=mode
            ),
            schedule=CronJobSchedule(
                type="cron",
                cron="0 0 * * *",
                timezone="UTC"
            ),
            runtime=CronJobRuntime(
                max_concurrency=1,
                timeout_seconds=120
            )
        )
        
        # Execute the task - should not raise an exception
        try:
            await cron_manager._executor.execute(job_spec)
            execution_succeeded = True
        except Exception as e:
            execution_succeeded = False
            pytest.fail(
                f"CronManager should handle channel send failure gracefully, "
                f"but raised exception: {type(e).__name__}: {e}"
            )
        
        # Verify execution completed without crashing
        assert execution_succeeded, \
            "CronManager should complete execution even when channel send fails"
        
        # Verify ChannelManager.send_message was called
        assert mock_channel_manager.send_message.call_count == 1, \
            "ChannelManager.send_message should be called despite expected failure"
    
    @settings(max_examples=100)
    @given(
        channel=st.text(min_size=1, max_size=50),
        user_id=st.text(min_size=1, max_size=100),
        session_id=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        mode=st.text(min_size=1, max_size=50),
        agent_response=st.text(min_size=1, max_size=500)
    )
    @pytest.mark.asyncio
    async def test_agent_task_handles_channel_send_failure(
        self, channel, user_id, session_id, mode, agent_response
    ):
        """Verify CronManager handles channel send failures gracefully for agent tasks.
        
        This property test verifies that for any valid combination of parameters,
        when ChannelManager.send_message returns False after an agent task completes,
        CronManager SHALL:
        1. Not crash or raise an exception
        2. Complete the task execution
        3. Continue operating normally
        
        **Feature: channel-abstraction-layer, Property 10: CronManager Error Resilience**
        **Validates: Requirements 8.5**
        """
        # Create a mock ChannelManager that always returns False (failure)
        mock_channel_manager = Mock()
        mock_channel_manager.send_message = AsyncMock(return_value=False)
        
        # Create a mock runner that returns the agent_response
        mock_runner = Mock()
        mock_runner.run = AsyncMock(return_value=agent_response)
        
        # Create CronManager with mocks
        cron_manager = CronManager(
            runner=mock_runner,
            channel_manager=mock_channel_manager
        )
        
        # Create an agent task
        from src.xagent.core.crons.models import CronJobRequest, CronJobRequestInput
        
        job_spec = CronJobSpec(
            id="test_agent_job_failure",
            name="Test Agent Job Failure",
            enabled=True,
            task_type="agent",
            request=CronJobRequest(
                input=[
                    CronJobRequestInput(
                        role="user",
                        type="text",
                        content=[{"text": "test input"}]
                    )
                ],
                session_id="test_session",
                user_id="test_user"
            ),
            dispatch=CronJobDispatch(
                type="channel",
                channel=channel,
                target=CronJobTarget(
                    user_id=user_id,
                    session_id=session_id
                ),
                mode=mode
            ),
            schedule=CronJobSchedule(
                type="cron",
                cron="0 0 * * *",
                timezone="UTC"
            ),
            runtime=CronJobRuntime(
                max_concurrency=1,
                timeout_seconds=120
            )
        )
        
        # Execute the task - should not raise an exception
        try:
            await cron_manager._executor.execute(job_spec)
            execution_succeeded = True
        except Exception as e:
            execution_succeeded = False
            pytest.fail(
                f"CronManager should handle channel send failure gracefully, "
                f"but raised exception: {type(e).__name__}: {e}"
            )
        
        # Verify execution completed without crashing
        assert execution_succeeded, \
            "CronManager should complete execution even when channel send fails"
        
        # Verify ChannelManager.send_message was called
        assert mock_channel_manager.send_message.call_count == 1, \
            "ChannelManager.send_message should be called despite expected failure"
    
    @settings(max_examples=100)
    @given(
        channel=st.text(min_size=1, max_size=50),
        user_id=st.text(min_size=1, max_size=100),
        session_id=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        content=st.text(min_size=1, max_size=1000),
        mode=st.text(min_size=1, max_size=50),
        exception_type=st.sampled_from([
            Exception,
            RuntimeError,
            ValueError,
            KeyError,
            AttributeError,
            TypeError
        ])
    )
    @pytest.mark.asyncio
    async def test_text_task_handles_channel_send_exception(
        self, channel, user_id, session_id, content, mode, exception_type
    ):
        """Verify CronManager handles channel send exceptions gracefully.
        
        This property test verifies that for any valid combination of parameters,
        when ChannelManager.send_message raises an exception,
        CronManager SHALL:
        1. Not propagate the exception
        2. Complete the task execution
        3. Continue operating normally
        
        **Feature: channel-abstraction-layer, Property 10: CronManager Error Resilience**
        **Validates: Requirements 8.5**
        """
        # Create a mock ChannelManager that raises an exception
        mock_channel_manager = Mock()
        mock_channel_manager.send_message = AsyncMock(
            side_effect=exception_type("Simulated channel failure")
        )
        
        # Create a mock runner
        mock_runner = Mock()
        
        # Create CronManager with mocks
        cron_manager = CronManager(
            runner=mock_runner,
            channel_manager=mock_channel_manager
        )
        
        # Create a text task
        job_spec = CronJobSpec(
            id="test_job_exception",
            name="Test Job Exception",
            enabled=True,
            task_type="text",
            text=content,
            dispatch=CronJobDispatch(
                type="channel",
                channel=channel,
                target=CronJobTarget(
                    user_id=user_id,
                    session_id=session_id
                ),
                mode=mode
            ),
            schedule=CronJobSchedule(
                type="cron",
                cron="0 0 * * *",
                timezone="UTC"
            ),
            runtime=CronJobRuntime(
                max_concurrency=1,
                timeout_seconds=120
            )
        )
        
        # Execute the task - should not raise an exception
        try:
            await cron_manager._executor.execute(job_spec)
            execution_succeeded = True
        except Exception as e:
            execution_succeeded = False
            pytest.fail(
                f"CronManager should handle channel send exception gracefully, "
                f"but raised exception: {type(e).__name__}: {e}"
            )
        
        # Verify execution completed without crashing
        assert execution_succeeded, \
            "CronManager should complete execution even when channel send raises exception"
        
        # Verify ChannelManager.send_message was called
        assert mock_channel_manager.send_message.call_count == 1, \
            "ChannelManager.send_message should be called despite expected exception"
    
    @settings(max_examples=100)
    @given(
        channel=st.text(min_size=1, max_size=50),
        user_id=st.text(min_size=1, max_size=100),
        session_id=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        content=st.text(min_size=1, max_size=1000),
        mode=st.text(min_size=1, max_size=50)
    )
    @pytest.mark.asyncio
    async def test_multiple_tasks_continue_after_failure(
        self, channel, user_id, session_id, content, mode
    ):
        """Verify CronManager continues processing tasks after a send failure.
        
        This property test verifies that when one task's channel send fails,
        subsequent tasks can still execute successfully. This ensures that
        CronManager's error handling doesn't leave it in a broken state.
        
        **Feature: channel-abstraction-layer, Property 10: CronManager Error Resilience**
        **Validates: Requirements 8.5**
        """
        # Create a mock ChannelManager that fails first, then succeeds
        call_count = 0
        
        async def send_message_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return False  # First call fails
            else:
                return True  # Subsequent calls succeed
        
        mock_channel_manager = Mock()
        mock_channel_manager.send_message = AsyncMock(side_effect=send_message_side_effect)
        
        # Create a mock runner
        mock_runner = Mock()
        
        # Create CronManager with mocks
        cron_manager = CronManager(
            runner=mock_runner,
            channel_manager=mock_channel_manager
        )
        
        # Create first task (will fail)
        job_spec_1 = CronJobSpec(
            id="test_job_1",
            name="Test Job 1",
            enabled=True,
            task_type="text",
            text=content,
            dispatch=CronJobDispatch(
                type="channel",
                channel=channel,
                target=CronJobTarget(
                    user_id=user_id,
                    session_id=session_id
                ),
                mode=mode
            ),
            schedule=CronJobSchedule(
                type="cron",
                cron="0 0 * * *",
                timezone="UTC"
            ),
            runtime=CronJobRuntime(
                max_concurrency=1,
                timeout_seconds=120
            )
        )
        
        # Create second task (will succeed)
        job_spec_2 = CronJobSpec(
            id="test_job_2",
            name="Test Job 2",
            enabled=True,
            task_type="text",
            text=content + "_second",
            dispatch=CronJobDispatch(
                type="channel",
                channel=channel,
                target=CronJobTarget(
                    user_id=user_id,
                    session_id=session_id
                ),
                mode=mode
            ),
            schedule=CronJobSchedule(
                type="cron",
                cron="0 0 * * *",
                timezone="UTC"
            ),
            runtime=CronJobRuntime(
                max_concurrency=1,
                timeout_seconds=120
            )
        )
        
        # Execute both tasks - neither should raise an exception
        try:
            await cron_manager._executor.execute(job_spec_1)
            await cron_manager._executor.execute(job_spec_2)
            execution_succeeded = True
        except Exception as e:
            execution_succeeded = False
            pytest.fail(
                f"CronManager should continue operating after failure, "
                f"but raised exception: {type(e).__name__}: {e}"
            )
        
        # Verify both executions completed
        assert execution_succeeded, \
            "CronManager should continue processing tasks after a send failure"
        
        # Verify both tasks called send_message
        assert mock_channel_manager.send_message.call_count == 2, \
            "Both tasks should attempt to send messages"
    
    @settings(max_examples=100)
    @given(
        channel=st.text(min_size=1, max_size=50),
        user_id=st.text(min_size=1, max_size=100),
        session_id=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        content=st.text(min_size=1, max_size=1000),
        mode=st.text(min_size=1, max_size=50)
    )
    @pytest.mark.asyncio
    async def test_text_task_handles_none_channel_manager(
        self, channel, user_id, session_id, content, mode
    ):
        """Verify CronManager handles None channel_manager gracefully.
        
        This property test verifies that when channel_manager is None,
        CronManager SHALL:
        1. Not crash or raise an exception
        2. Complete the task execution
        3. Continue operating normally
        
        This tests the edge case where channel_manager might not be properly
        initialized or is explicitly set to None.
        
        **Feature: channel-abstraction-layer, Property 10: CronManager Error Resilience**
        **Validates: Requirements 8.5**
        """
        # Create a mock runner
        mock_runner = Mock()
        
        # Create CronManager with None channel_manager
        # Note: The constructor creates a default ChannelManager if None is passed,
        # so we need to set it to None after construction to test this edge case
        cron_manager = CronManager(
            runner=mock_runner,
            channel_manager=None
        )
        
        # Explicitly set channel_manager to None on the executor to test edge case
        cron_manager._executor._channel_manager = None
        
        # Create a text task
        job_spec = CronJobSpec(
            id="test_job_none_cm",
            name="Test Job None CM",
            enabled=True,
            task_type="text",
            text=content,
            dispatch=CronJobDispatch(
                type="channel",
                channel=channel,
                target=CronJobTarget(
                    user_id=user_id,
                    session_id=session_id
                ),
                mode=mode
            ),
            schedule=CronJobSchedule(
                type="cron",
                cron="0 0 * * *",
                timezone="UTC"
            ),
            runtime=CronJobRuntime(
                max_concurrency=1,
                timeout_seconds=120
            )
        )
        
        # Execute the task - should not raise an exception
        try:
            await cron_manager._executor.execute(job_spec)
            execution_succeeded = True
        except Exception as e:
            execution_succeeded = False
            pytest.fail(
                f"CronManager should handle None channel_manager gracefully, "
                f"but raised exception: {type(e).__name__}: {e}"
            )
        
        # Verify execution completed without crashing
        assert execution_succeeded, \
            "CronManager should complete execution even when channel_manager is None"
