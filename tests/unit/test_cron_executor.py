# -*- coding: utf-8 -*-
"""CronExecutor 单元测试"""
import pytest
from unittest.mock import Mock

from src.xagent.core.crons.executor import CronExecutor
from src.xagent.core.crons.models import CronJobSpec, CronJobSchedule, CronJobDispatch, CronJobTarget, CronJobRuntime


@pytest.fixture
def mock_runner():
    """模拟运行器"""
    return Mock()


@pytest.fixture
def mock_channel_manager():
    """模拟频道管理器"""
    return Mock()


@pytest.fixture
def cron_executor(mock_runner, mock_channel_manager):
    """CronExecutor 实例"""
    return CronExecutor(
        runner=mock_runner,
        channel_manager=mock_channel_manager
    )


def test_cron_executor_execute_text_task(cron_executor, mock_runner, mock_channel_manager):
    """测试执行文本任务"""
    # 创建文本任务规格
    spec = CronJobSpec(
        id="test-job-1",
        name="Test Text Job",
        enabled=True,
        schedule=CronJobSchedule(
            type="cron",
            cron="0 9 * * *",
            timezone="UTC"
        ),
        task_type="text",
        text="Hello, World!",
        dispatch=CronJobDispatch(
            type="channel",
            channel="console",
            target=CronJobTarget(
                user_id="test-user",
                session_id="test-session"
            ),
            mode="final",
            meta={}
        ),
        runtime=CronJobRuntime(
            max_concurrency=1,
            timeout_seconds=120,
            misfire_grace_seconds=60
        ),
        meta={}
    )
    
    # 执行任务
    import asyncio
    asyncio.run(cron_executor.execute(spec))
    
    # 验证频道管理器的 send_message 方法被调用
    mock_channel_manager.send_message.assert_called_once()


def test_cron_executor_execute_agent_task(cron_executor, mock_runner, mock_channel_manager):
    """测试执行 AI 任务"""
    # 创建 AI 任务规格
    from src.xagent.core.crons.models import CronJobRequest, CronJobRequestInput
    spec = CronJobSpec(
        id="test-job-2",
        name="Test Agent Job",
        enabled=True,
        schedule=CronJobSchedule(
            type="cron",
            cron="0 9 * * *",
            timezone="UTC"
        ),
        task_type="agent",
        text="What's the weather today?",
        request=CronJobRequest(
            input=[
                CronJobRequestInput(
                    role="user",
                    type="text",
                    content=[{"type": "text", "text": "What's the weather today?"}]
                )
            ],
            session_id="test-session",
            user_id="test-user"
        ),
        dispatch=CronJobDispatch(
            type="channel",
            channel="console",
            target=CronJobTarget(
                user_id="test-user",
                session_id="test-session"
            ),
            mode="final",
            meta={}
        ),
        runtime=CronJobRuntime(
            max_concurrency=1,
            timeout_seconds=120,
            misfire_grace_seconds=60
        ),
        meta={}
    )
    
    # 设置模拟运行器的返回值
    mock_runner.run.return_value = "The weather is sunny today."
    
    # 执行任务
    import asyncio
    asyncio.run(cron_executor.execute(spec))
    
    # 验证运行器的 run 方法被调用
    mock_runner.run.assert_called_once()
    
    # 验证频道管理器的 send_message 方法被调用
    mock_channel_manager.send_message.assert_called_once()


def test_cron_executor_execute_invalid_task_type(cron_executor, mock_runner, mock_channel_manager):
    """测试执行无效任务类型"""
    # 创建无效任务类型的任务规格
    spec = CronJobSpec(
        id="test-job-3",
        name="Test Invalid Job",
        enabled=True,
        schedule=CronJobSchedule(
            type="cron",
            cron="0 9 * * *",
            timezone="UTC"
        ),
        task_type="invalid",
        text="Hello, World!",
        dispatch=CronJobDispatch(
            type="channel",
            channel="console",
            target=CronJobTarget(
                user_id="test-user",
                session_id="test-session"
            ),
            mode="final",
            meta={}
        ),
        runtime=CronJobRuntime(
            max_concurrency=1,
            timeout_seconds=120,
            misfire_grace_seconds=60
        ),
        meta={}
    )
    
    # 执行任务，应该抛出异常
    import asyncio
    with pytest.raises(ValueError):
        asyncio.run(cron_executor.execute(spec))


if __name__ == "__main__":
    pytest.main([__file__])
