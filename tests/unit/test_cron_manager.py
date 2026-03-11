# -*- coding: utf-8 -*-
"""CronManager 单元测试"""
import os
import tempfile
import pytest
from datetime import datetime

from src.xagent.core.crons.manager import CronManager
from src.xagent.core.crons.models import CronJobSpec, CronJobSchedule, CronJobDispatch, CronJobTarget, CronJobRuntime


@pytest.fixture
def temp_jobs_dir():
    """临时任务目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_cron_manager_init(temp_jobs_dir):
    """测试 CronManager 初始化"""
    # 设置环境变量
    os.environ["CRON_JOBS_DIR"] = temp_jobs_dir
    
    # 初始化 CronManager
    cron_manager = CronManager()
    assert cron_manager is not None
    
    # 启动和停止
    cron_manager.start_sync()
    cron_manager.stop_sync()


def test_cron_manager_create_job(temp_jobs_dir):
    """测试创建任务"""
    # 设置环境变量
    os.environ["CRON_JOBS_DIR"] = temp_jobs_dir
    
    # 初始化 CronManager
    cron_manager = CronManager()
    cron_manager.start_sync()
    
    try:
        # 创建任务规格
        spec = CronJobSpec(
            id="test-job-1",
            name="Test Job",
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
        
        # 创建任务
        cron_manager.create_or_replace_job_sync(spec)
        
        # 验证任务是否创建成功
        jobs = cron_manager.list_jobs_sync()
        assert len(jobs) == 1
        assert jobs[0].id == "test-job-1"
        assert jobs[0].name == "Test Job"
        
        # 获取任务
        job = cron_manager.get_job_sync("test-job-1")
        assert job is not None
        assert job.id == "test-job-1"
        
        # 获取任务状态
        state = cron_manager.get_state_sync("test-job-1")
        assert state is not None
        
    finally:
        cron_manager.stop_sync()


def test_cron_manager_update_job(temp_jobs_dir):
    """测试更新任务"""
    # 设置环境变量
    os.environ["CRON_JOBS_DIR"] = temp_jobs_dir
    
    # 初始化 CronManager
    cron_manager = CronManager()
    cron_manager.start_sync()
    
    try:
        # 创建任务
        spec = CronJobSpec(
            id="test-job-2",
            name="Test Job",
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
        cron_manager.create_or_replace_job_sync(spec)
        
        # 更新任务
        spec.name = "Updated Test Job"
        spec.text = "Updated Hello, World!"
        cron_manager.create_or_replace_job_sync(spec)
        
        # 验证任务是否更新成功
        job = cron_manager.get_job_sync("test-job-2")
        assert job is not None
        assert job.name == "Updated Test Job"
        assert job.text == "Updated Hello, World!"
        
    finally:
        cron_manager.stop_sync()


def test_cron_manager_delete_job(temp_jobs_dir):
    """测试删除任务"""
    # 设置环境变量
    os.environ["CRON_JOBS_DIR"] = temp_jobs_dir
    
    # 初始化 CronManager
    cron_manager = CronManager()
    cron_manager.start_sync()
    
    try:
        # 创建任务
        spec = CronJobSpec(
            id="test-job-3",
            name="Test Job",
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
        cron_manager.create_or_replace_job_sync(spec)
        
        # 验证任务是否创建成功
        jobs = cron_manager.list_jobs_sync()
        assert len(jobs) == 1
        
        # 删除任务
        deleted = cron_manager.delete_job_sync("test-job-3")
        assert deleted is True
        
        # 验证任务是否删除成功
        jobs = cron_manager.list_jobs_sync()
        assert len(jobs) == 0
        
    finally:
        cron_manager.stop_sync()


def test_cron_manager_pause_resume_job(temp_jobs_dir):
    """测试暂停和恢复任务"""
    # 设置环境变量
    os.environ["CRON_JOBS_DIR"] = temp_jobs_dir
    
    # 初始化 CronManager
    cron_manager = CronManager()
    cron_manager.start_sync()
    
    try:
        # 创建任务
        spec = CronJobSpec(
            id="test-job-4",
            name="Test Job",
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
        cron_manager.create_or_replace_job_sync(spec)
        
        # 暂停任务
        cron_manager.pause_job_sync("test-job-4")
        
        # 恢复任务
        cron_manager.resume_job_sync("test-job-4")
        
        # 验证任务是否存在
        job = cron_manager.get_job_sync("test-job-4")
        assert job is not None
        
    finally:
        cron_manager.stop_sync()


if __name__ == "__main__":
    pytest.main([__file__])
