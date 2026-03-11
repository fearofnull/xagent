# -*- coding: utf-8 -*-
"""JsonJobRepository 单元测试"""
import os
import tempfile
import pytest

from src.xagent.core.crons.repo.json_repo import JsonJobRepository
from src.xagent.core.crons.models import CronJobSpec, CronJobSchedule, CronJobDispatch, CronJobTarget, CronJobRuntime


@pytest.fixture
def temp_jobs_dir():
    """临时任务目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_json_repo_init(temp_jobs_dir):
    """测试 JsonJobRepository 初始化"""
    from pathlib import Path
    repo = JsonJobRepository(path=Path(temp_jobs_dir) / "jobs.json")
    assert repo is not None


def test_json_repo_save_load(temp_jobs_dir):
    """测试保存和加载任务"""
    from pathlib import Path
    repo = JsonJobRepository(path=Path(temp_jobs_dir) / "jobs.json")
    
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
    
    # 保存任务
    import asyncio
    asyncio.run(repo.upsert_job(spec))
    
    # 加载任务
    jobs_file = asyncio.run(repo.load())
    assert len(jobs_file.jobs) == 1
    assert jobs_file.jobs[0].id == "test-job-1"
    assert jobs_file.jobs[0].name == "Test Job"


def test_json_repo_list_jobs(temp_jobs_dir):
    """测试列出所有任务"""
    from pathlib import Path
    repo = JsonJobRepository(path=Path(temp_jobs_dir) / "jobs.json")
    
    # 创建任务规格
    spec1 = CronJobSpec(
        id="test-job-1",
        name="Test Job 1",
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
    
    spec2 = CronJobSpec(
        id="test-job-2",
        name="Test Job 2",
        enabled=True,
        schedule=CronJobSchedule(
            type="cron",
            cron="0 10 * * *",
            timezone="UTC"
        ),
        task_type="text",
        text="Hello, World 2!",
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
    
    # 保存任务
    import asyncio
    asyncio.run(repo.upsert_job(spec1))
    asyncio.run(repo.upsert_job(spec2))
    
    # 列出任务
    jobs = asyncio.run(repo.list_jobs())
    assert len(jobs) == 2
    assert jobs[0].id == "test-job-1"
    assert jobs[1].id == "test-job-2"


def test_json_repo_get_job(temp_jobs_dir):
    """测试获取任务"""
    from pathlib import Path
    repo = JsonJobRepository(path=Path(temp_jobs_dir) / "jobs.json")
    
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
    
    # 保存任务
    import asyncio
    asyncio.run(repo.upsert_job(spec))
    
    # 获取任务
    job = asyncio.run(repo.get_job("test-job-1"))
    assert job is not None
    assert job.id == "test-job-1"
    assert job.name == "Test Job"
    
    # 获取不存在的任务
    job = asyncio.run(repo.get_job("non-existent-job"))
    assert job is None


def test_json_repo_delete_job(temp_jobs_dir):
    """测试删除任务"""
    from pathlib import Path
    repo = JsonJobRepository(path=Path(temp_jobs_dir) / "jobs.json")
    
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
    
    # 保存任务
    import asyncio
    asyncio.run(repo.upsert_job(spec))
    
    # 验证任务存在
    jobs = asyncio.run(repo.list_jobs())
    assert len(jobs) == 1
    
    # 删除任务
    deleted = asyncio.run(repo.delete_job("test-job-1"))
    assert deleted is True
    
    # 验证任务不存在
    jobs = asyncio.run(repo.list_jobs())
    assert len(jobs) == 0
    
    # 删除不存在的任务
    deleted = asyncio.run(repo.delete_job("non-existent-job"))
    assert deleted is False


if __name__ == "__main__":
    pytest.main([__file__])
