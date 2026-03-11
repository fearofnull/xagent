# -*- coding: utf-8 -*-
"""Cron集成测试 - 端到端测试"""
import os
import tempfile
import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta

from src.xagent.core.crons.manager import CronManager
from src.xagent.core.crons.models import (
    CronJobSpec, CronJobSchedule, CronJobDispatch, 
    CronJobTarget, CronJobRuntime
)


@pytest.fixture
def temp_jobs_dir():
    """临时任务目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest_asyncio.fixture
async def cron_manager(temp_jobs_dir):
    """CronManager实例"""
    os.environ["CRON_JOBS_DIR"] = temp_jobs_dir
    manager = CronManager()
    await manager.start()
    yield manager
    await manager.stop()


@pytest.mark.asyncio
async def test_cron_job_lifecycle(cron_manager):
    """测试任务完整生命周期"""
    # 1. 创建任务
    spec = CronJobSpec(
        id="test-lifecycle-job",
        name="Lifecycle Test Job",
        enabled=True,
        schedule=CronJobSchedule(
            type="cron",
            cron="0 9 * * *",
            timezone="UTC"
        ),
        task_type="text",
        text="Test message",
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
    
    await cron_manager.create_or_replace_job(spec)
    
    # 2. 验证任务被创建
    jobs = await cron_manager.list_jobs()
    assert len(jobs) == 1
    assert jobs[0].id == "test-lifecycle-job"
    
    # 3. 获取任务详情
    job = await cron_manager.get_job("test-lifecycle-job")
    assert job is not None
    assert job.name == "Lifecycle Test Job"
    
    # 4. 获取任务状态
    state = cron_manager.get_state("test-lifecycle-job")
    assert state is not None
    assert state.next_run_at is not None
    
    # 5. 暂停任务
    await cron_manager.pause_job("test-lifecycle-job")
    
    # 6. 恢复任务
    await cron_manager.resume_job("test-lifecycle-job")
    
    # 7. 更新任务
    job.name = "Updated Lifecycle Test Job"
    await cron_manager.create_or_replace_job(job)
    
    updated_job = await cron_manager.get_job("test-lifecycle-job")
    assert updated_job.name == "Updated Lifecycle Test Job"
    
    # 8. 删除任务
    deleted = await cron_manager.delete_job("test-lifecycle-job")
    assert deleted is True
    
    # 9. 验证任务已删除
    jobs = await cron_manager.list_jobs()
    assert len(jobs) == 0


@pytest.mark.asyncio
async def test_cron_job_execution(cron_manager):
    """测试任务执行"""
    # 创建一个立即执行的任务
    spec = CronJobSpec(
        id="test-execution-job",
        name="Execution Test Job",
        enabled=True,
        schedule=CronJobSchedule(
            type="cron",
            cron="* * * * *",  # 每分钟执行
            timezone="UTC"
        ),
        task_type="text",
        text="Execution test message",
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
    
    await cron_manager.create_or_replace_job(spec)
    
    # 立即执行任务
    await cron_manager.run_job("test-execution-job")
    
    # 等待任务执行完成
    await asyncio.sleep(2)
    
    # 验证任务状态已更新
    state = cron_manager.get_state("test-execution-job")
    assert state.last_run_at is not None
    assert state.last_status in ["success", "error"]
    
    # 清理
    await cron_manager.delete_job("test-execution-job")


@pytest.mark.asyncio
async def test_multiple_cron_jobs(cron_manager):
    """测试多个任务并发"""
    # 创建多个任务
    for i in range(5):
        spec = CronJobSpec(
            id=f"test-multi-job-{i}",
            name=f"Multi Test Job {i}",
            enabled=True,
            schedule=CronJobSchedule(
                type="cron",
                cron="0 9 * * *",
                timezone="UTC"
            ),
            task_type="text",
            text=f"Test message {i}",
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
        await cron_manager.create_or_replace_job(spec)
    
    # 验证所有任务都被创建
    jobs = await cron_manager.list_jobs()
    assert len(jobs) == 5
    
    # 清理所有任务
    for i in range(5):
        await cron_manager.delete_job(f"test-multi-job-{i}")
    
    # 验证所有任务都被删除
    jobs = await cron_manager.list_jobs()
    assert len(jobs) == 0


@pytest.mark.asyncio
async def test_cron_expression_validation(cron_manager):
    """测试Cron表达式验证"""
    # 有效的cron表达式
    valid_spec = CronJobSpec(
        id="test-valid-cron",
        name="Valid Cron Test",
        enabled=True,
        schedule=CronJobSchedule(
            type="cron",
            cron="0 9 * * *",
            timezone="UTC"
        ),
        task_type="text",
        text="Test",
        dispatch=CronJobDispatch(
            type="channel",
            channel="console",
            target=CronJobTarget(),
            mode="final",
            meta={}
        ),
        runtime=CronJobRuntime(),
        meta={}
    )
    
    await cron_manager.create_or_replace_job(valid_spec)
    job = await cron_manager.get_job("test-valid-cron")
    assert job is not None
    
    # 无效的cron表达式（字段数量错误）
    invalid_spec = CronJobSpec(
        id="test-invalid-cron",
        name="Invalid Cron Test",
        enabled=True,
        schedule=CronJobSchedule(
            type="cron",
            cron="0 9 * *",  # 只有4个字段，应该是5个
            timezone="UTC"
        ),
        task_type="text",
        text="Test",
        dispatch=CronJobDispatch(
            type="channel",
            channel="console",
            target=CronJobTarget(),
            mode="final",
            meta={}
        ),
        runtime=CronJobRuntime(),
        meta={}
    )
    
    with pytest.raises(ValueError):
        await cron_manager.create_or_replace_job(invalid_spec)
    
    # 清理
    await cron_manager.delete_job("test-valid-cron")


@pytest.mark.asyncio
async def test_system_restart_persistence(temp_jobs_dir):
    """测试系统重启后任务持久化"""
    os.environ["CRON_JOBS_DIR"] = temp_jobs_dir
    
    # 第一个CronManager实例
    manager1 = CronManager()
    await manager1.start()
    
    # 创建任务
    spec = CronJobSpec(
        id="test-persistence-job",
        name="Persistence Test Job",
        enabled=True,
        schedule=CronJobSchedule(
            type="cron",
            cron="0 9 * * *",
            timezone="UTC"
        ),
        task_type="text",
        text="Persistence test",
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
        runtime=CronJobRuntime(),
        meta={}
    )
    
    await manager1.create_or_replace_job(spec)
    await manager1.stop()
    
    # 第二个CronManager实例（模拟系统重启）
    manager2 = CronManager()
    await manager2.start()
    
    # 验证任务仍然存在
    jobs = await manager2.list_jobs()
    assert len(jobs) == 1
    assert jobs[0].id == "test-persistence-job"
    
    # 清理
    await manager2.delete_job("test-persistence-job")
    await manager2.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
