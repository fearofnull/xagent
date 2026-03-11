# -*- coding: utf-8 -*-
"""JSON存储库实现"""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .base import BaseJobRepository
from ..models import (
    CronJobSpec,
    CronJobSchedule,
    CronJobDispatch,
    CronJobTarget,
    CronJobRuntime,
    CronJobRequest,
    CronJobRequestInput,
)


@dataclass
class JobsFile:
    """任务文件"""
    jobs: List[CronJobSpec]


class JsonJobRepository(BaseJobRepository):
    """基于JSON文件的任务存储库"""

    def __init__(self, path: Path):
        """初始化存储库

        Args:
            path: 任务配置文件路径
        """
        self._path = path

    async def load(self) -> JobsFile:
        """加载任务文件"""
        if not self._path.exists():
            return JobsFile(jobs=[])

        with open(self._path, "r", encoding="utf-8") as f:
            data = json.load(f)

        jobs = []
        for job_data in data.get("jobs", []):
            # 构建任务对象
            job = CronJobSpec(
                id=job_data["id"],
                name=job_data["name"],
                enabled=job_data.get("enabled", True),
                schedule=CronJobSchedule(**job_data.get("schedule", {})),
                task_type=job_data.get("task_type", "text"),
                text=job_data.get("text"),
                request=CronJobRequest(
                    input=[
                        CronJobRequestInput(**item)
                        for item in job_data.get("request", {}).get("input", [])
                    ],
                    session_id=job_data.get("request", {}).get("session_id"),
                    user_id=job_data.get("request", {}).get("user_id", "cron")
                ) if job_data.get("request") else None,
                dispatch=CronJobDispatch(
                    type=job_data.get("dispatch", {}).get("type", "channel"),
                    channel=job_data.get("dispatch", {}).get("channel", "console"),
                    target=CronJobTarget(**job_data.get("dispatch", {}).get("target", {})),
                    mode=job_data.get("dispatch", {}).get("mode", "final"),
                    meta=job_data.get("dispatch", {}).get("meta", {})
                ),
                runtime=CronJobRuntime(**job_data.get("runtime", {})),
                meta=job_data.get("meta", {})
            )
            jobs.append(job)

        return JobsFile(jobs=jobs)

    async def save(self, jobs_file: JobsFile) -> None:
        """保存任务文件"""
        data = {
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "enabled": job.enabled,
                    "schedule": {
                        "type": job.schedule.type,
                        "cron": job.schedule.cron,
                        "timezone": job.schedule.timezone
                    },
                    "task_type": job.task_type,
                    "text": job.text,
                    "request": {
                        "input": [
                            {
                                "role": item.role,
                                "type": item.type,
                                "content": item.content
                            }
                            for item in job.request.input
                        ],
                        "session_id": job.request.session_id,
                        "user_id": job.request.user_id
                    } if job.request else None,
                    "dispatch": {
                        "type": job.dispatch.type,
                        "channel": job.dispatch.channel,
                        "target": {
                            "chat_id": job.dispatch.target.chat_id,
                            "user_id": job.dispatch.target.user_id
                        },
                        "mode": job.dispatch.mode,
                        "meta": job.dispatch.meta
                    },
                    "runtime": {
                        "max_concurrency": job.runtime.max_concurrency,
                        "timeout_seconds": job.runtime.timeout_seconds,
                        "misfire_grace_seconds": job.runtime.misfire_grace_seconds
                    },
                    "meta": job.meta
                }
                for job in jobs_file.jobs
            ]
        }

        # 确保目录存在
        self._path.parent.mkdir(parents=True, exist_ok=True)

        # 保存文件
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    async def list_jobs(self) -> List[CronJobSpec]:
        """列出所有任务"""
        jobs_file = await self.load()
        return jobs_file.jobs

    async def get_job(self, job_id: str) -> Optional[CronJobSpec]:
        """获取任务"""
        jobs_file = await self.load()
        for job in jobs_file.jobs:
            if job.id == job_id:
                return job
        return None

    async def upsert_job(self, spec: CronJobSpec) -> None:
        """创建或更新任务"""
        jobs_file = await self.load()
        updated = False

        # 查找并更新现有任务
        for i, job in enumerate(jobs_file.jobs):
            if job.id == spec.id:
                jobs_file.jobs[i] = spec
                updated = True
                break

        # 如果是新任务，添加到列表
        if not updated:
            jobs_file.jobs.append(spec)

        # 保存更新后的任务
        await self.save(jobs_file)

    async def delete_job(self, job_id: str) -> bool:
        """删除任务"""
        jobs_file = await self.load()
        original_count = len(jobs_file.jobs)

        # 过滤掉要删除的任务
        jobs_file.jobs = [job for job in jobs_file.jobs if job.id != job_id]

        # 如果任务数量发生变化，保存并返回True
        if len(jobs_file.jobs) != original_count:
            await self.save(jobs_file)
            return True

        return False
