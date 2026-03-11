# -*- coding: utf-8 -*-
"""CronManager ChannelManager integration tests"""
import os
import tempfile
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.xagent.core.crons.manager import CronManager
from src.xagent.core.crons.models import (
    CronJobSpec,
    CronJobSchedule,
    CronJobDispatch,
    CronJobTarget,
    CronJobRuntime,
    CronJobRequest,
    CronJobRequestInput
)
from src.xagent.core.channels import ChannelManager, FeishuChannel


@pytest.fixture
def temp_jobs_dir():
    """临时任务目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_cron_manager_accepts_channel_manager(temp_jobs_dir):
    """测试 CronManager 接受 ChannelManager 参数"""
    os.environ["CRON_JOBS_DIR"] = temp_jobs_dir
    
    # 创建一个 mock ChannelManager
    mock_channel_manager = MagicMock(spec=ChannelManager)
    
    # 初始化 CronManager 并传入 channel_manager
    cron_manager = CronManager(channel_manager=mock_channel_manager)
    
    # 验证 channel_manager 被正确设置
    assert cron_manager._channel_manager is mock_channel_manager


def test_cron_manager_creates_default_channel_manager(temp_jobs_dir):
    """测试 CronManager 在未提供 channel_manager 时创建默认的 ChannelManager"""
    os.environ["CRON_JOBS_DIR"] = temp_jobs_dir
    
    # 初始化 CronManager 不传入 channel_manager
    cron_manager = CronManager()
    
    # 验证 channel_manager 被创建
    assert cron_manager._channel_manager is not None
    
    # 验证 channel_manager 是 ChannelManager 实例
    assert isinstance(cron_manager._channel_manager, ChannelManager)


def test_cron_manager_default_channel_manager_is_empty(temp_jobs_dir):
    """测试默认 ChannelManager 是空的（需要在应用初始化时配置）"""
    os.environ["CRON_JOBS_DIR"] = temp_jobs_dir
    
    # 初始化 CronManager 不传入 channel_manager
    cron_manager = CronManager()
    
    # 验证 channel_manager 被创建
    assert cron_manager._channel_manager is not None
    assert isinstance(cron_manager._channel_manager, ChannelManager)
    
    # 验证默认 channel_manager 是空的（没有注册任何频道）
    # 这是预期的，因为实际的频道应该在应用初始化时（如 main.py）注册
    with pytest.raises(KeyError):
        cron_manager._channel_manager.get_channel("feishu")


def test_cron_manager_uses_provided_channel_manager(temp_jobs_dir):
    """测试 CronManager 使用提供的 ChannelManager"""
    os.environ["CRON_JOBS_DIR"] = temp_jobs_dir
    
    # 创建一个自定义的 ChannelManager
    custom_channel_manager = ChannelManager()
    
    # 创建一个 mock channel
    mock_channel = MagicMock()
    mock_channel.send_message = AsyncMock(return_value=True)
    
    # 注册 mock channel
    custom_channel_manager.register_channel("custom", mock_channel)
    
    # 初始化 CronManager 并传入自定义 channel_manager
    cron_manager = CronManager(channel_manager=custom_channel_manager)
    
    # 验证 CronManager 使用的是自定义的 channel_manager
    assert cron_manager._channel_manager is custom_channel_manager
    
    # 验证可以获取自定义的 channel
    custom_channel = cron_manager._channel_manager.get_channel("custom")
    assert custom_channel is mock_channel


def test_cron_manager_executor_receives_channel_manager(temp_jobs_dir):
    """测试 CronExecutor 接收到 ChannelManager"""
    os.environ["CRON_JOBS_DIR"] = temp_jobs_dir
    
    # 创建一个 mock ChannelManager
    mock_channel_manager = MagicMock(spec=ChannelManager)
    
    # 初始化 CronManager
    cron_manager = CronManager(channel_manager=mock_channel_manager)
    
    # 验证 executor 接收到了 channel_manager
    assert cron_manager._executor._channel_manager is mock_channel_manager


@pytest.mark.asyncio
async def test_cron_manager_sends_text_message_through_channel(temp_jobs_dir):
    """测试 CronManager 通过 ChannelManager 发送文本消息
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
    """
    os.environ["CRON_JOBS_DIR"] = temp_jobs_dir
    
    # 创建 mock ChannelManager
    mock_channel_manager = MagicMock(spec=ChannelManager)
    mock_channel_manager.send_message = AsyncMock(return_value=True)
    
    # 初始化 CronManager
    cron_manager = CronManager(channel_manager=mock_channel_manager)
    
    # 创建一个文本任务
    job_spec = CronJobSpec(
        id="test-text-job",
        name="Test Text Job",
        task_type="text",
        text="Hello from cron!",
        dispatch=CronJobDispatch(
            channel="feishu",
            target=CronJobTarget(
                user_id="user123",
                session_id="session456"
            ),
            mode="final"
        )
    )
    
    # 执行任务
    await cron_manager._execute_once(job_spec)
    
    # 验证 send_message 被调用，参数正确
    mock_channel_manager.send_message.assert_called_once_with(
        channel="feishu",
        user_id="user123",
        session_id="session456",
        content="Hello from cron!",
        mode="final"
    )


@pytest.mark.asyncio
async def test_cron_manager_sends_agent_message_through_channel(temp_jobs_dir):
    """测试 CronManager 通过 ChannelManager 发送 agent 任务响应
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
    """
    os.environ["CRON_JOBS_DIR"] = temp_jobs_dir
    
    # 创建 mock ChannelManager
    mock_channel_manager = MagicMock(spec=ChannelManager)
    mock_channel_manager.send_message = AsyncMock(return_value=True)
    
    # 创建 mock runner
    mock_runner = MagicMock()
    mock_runner.run = AsyncMock(return_value="Agent response")
    
    # 初始化 CronManager
    cron_manager = CronManager(
        channel_manager=mock_channel_manager,
        runner=mock_runner
    )
    
    # 创建一个 agent 任务
    job_spec = CronJobSpec(
        id="test-agent-job",
        name="Test Agent Job",
        task_type="agent",
        request=CronJobRequest(
            input=[
                CronJobRequestInput(
                    role="user",
                    type="text",
                    content=[{"text": "What is the weather?"}]
                )
            ],
            session_id="session789",
            user_id="user456"
        ),
        dispatch=CronJobDispatch(
            channel="feishu",
            target=CronJobTarget(
                user_id="user456",
                session_id="session789"
            ),
            mode="final"
        )
    )
    
    # 执行任务
    await cron_manager._execute_once(job_spec)
    
    # 验证 runner.run 被调用
    mock_runner.run.assert_called_once()
    
    # 验证 send_message 被调用，参数正确
    mock_channel_manager.send_message.assert_called_once_with(
        channel="feishu",
        user_id="user456",
        session_id="session789",
        content="Agent response",
        mode="final"
    )


@pytest.mark.asyncio
async def test_cron_manager_handles_channel_send_failure(temp_jobs_dir):
    """测试 CronManager 处理频道发送失败的情况
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
    """
    os.environ["CRON_JOBS_DIR"] = temp_jobs_dir
    
    # 创建 mock ChannelManager，模拟发送失败
    mock_channel_manager = MagicMock(spec=ChannelManager)
    mock_channel_manager.send_message = AsyncMock(side_effect=Exception("Channel send failed"))
    
    # 初始化 CronManager
    cron_manager = CronManager(channel_manager=mock_channel_manager)
    
    # 创建一个文本任务
    job_spec = CronJobSpec(
        id="test-fail-job",
        name="Test Fail Job",
        task_type="text",
        text="This should fail",
        dispatch=CronJobDispatch(
            channel="feishu",
            target=CronJobTarget(
                user_id="user999",
                session_id="session999"
            ),
            mode="final"
        )
    )
    
    # 执行任务 - 应该不会抛出异常，而是优雅地处理错误
    # CronExecutor 的 _send_message 方法会捕获异常并打印错误
    await cron_manager._execute_once(job_spec)
    
    # 验证 send_message 被调用
    mock_channel_manager.send_message.assert_called_once()
    
    # 任务状态应该是 success（因为 executor 捕获了异常）
    state = cron_manager.get_state("test-fail-job")
    assert state.last_status == "success"


@pytest.mark.asyncio
async def test_cron_manager_with_none_channel_manager_parameter(temp_jobs_dir):
    """测试 CronManager 使用 None 作为 channel_manager 参数时创建默认实例
    
    Requirements: 4.1, 4.2
    """
    os.environ["CRON_JOBS_DIR"] = temp_jobs_dir
    
    # 显式传入 None
    cron_manager = CronManager(channel_manager=None)
    
    # 验证创建了默认的 ChannelManager
    assert cron_manager._channel_manager is not None
    assert isinstance(cron_manager._channel_manager, ChannelManager)
    
    # 验证 executor 也接收到了 channel_manager
    assert cron_manager._executor._channel_manager is not None
    assert isinstance(cron_manager._executor._channel_manager, ChannelManager)


@pytest.mark.asyncio
async def test_cron_manager_sends_message_with_none_session_id(temp_jobs_dir):
    """测试 CronManager 发送消息时 session_id 为 None 的情况
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
    """
    os.environ["CRON_JOBS_DIR"] = temp_jobs_dir
    
    # 创建 mock ChannelManager
    mock_channel_manager = MagicMock(spec=ChannelManager)
    mock_channel_manager.send_message = AsyncMock(return_value=True)
    
    # 初始化 CronManager
    cron_manager = CronManager(channel_manager=mock_channel_manager)
    
    # 创建一个文本任务，session_id 为 None
    job_spec = CronJobSpec(
        id="test-no-session-job",
        name="Test No Session Job",
        task_type="text",
        text="Message without session",
        dispatch=CronJobDispatch(
            channel="feishu",
            target=CronJobTarget(
                user_id="user111",
                session_id=None  # 显式设置为 None
            ),
            mode="final"
        )
    )
    
    # 执行任务
    await cron_manager._execute_once(job_spec)
    
    # 验证 send_message 被调用，session_id 为 None
    mock_channel_manager.send_message.assert_called_once_with(
        channel="feishu",
        user_id="user111",
        session_id=None,
        content="Message without session",
        mode="final"
    )


@pytest.mark.asyncio
async def test_cron_manager_handles_agent_task_timeout(temp_jobs_dir):
    """测试 CronManager 处理 agent 任务超时的情况
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
    """
    os.environ["CRON_JOBS_DIR"] = temp_jobs_dir
    
    # 创建 mock ChannelManager
    mock_channel_manager = MagicMock(spec=ChannelManager)
    mock_channel_manager.send_message = AsyncMock(return_value=True)
    
    # 创建 mock runner，模拟超时
    import asyncio
    mock_runner = MagicMock()
    async def slow_run(*args, **kwargs):
        await asyncio.sleep(10)  # 模拟长时间运行
        return "Should not reach here"
    mock_runner.run = slow_run
    
    # 初始化 CronManager
    cron_manager = CronManager(
        channel_manager=mock_channel_manager,
        runner=mock_runner
    )
    
    # 创建一个 agent 任务，设置短超时时间
    job_spec = CronJobSpec(
        id="test-timeout-job",
        name="Test Timeout Job",
        task_type="agent",
        request=CronJobRequest(
            input=[
                CronJobRequestInput(
                    role="user",
                    type="text",
                    content=[{"text": "Long running task"}]
                )
            ],
            user_id="user777"
        ),
        dispatch=CronJobDispatch(
            channel="feishu",
            target=CronJobTarget(
                user_id="user777",
                session_id="session777"
            ),
            mode="final"
        ),
        runtime=CronJobRuntime(
            timeout_seconds=1  # 1秒超时
        )
    )
    
    # 执行任务
    await cron_manager._execute_once(job_spec)
    
    # 验证 send_message 被调用，内容包含超时信息
    mock_channel_manager.send_message.assert_called_once()
    call_args = mock_channel_manager.send_message.call_args
    assert "超时" in call_args.kwargs["content"] or "timeout" in call_args.kwargs["content"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
