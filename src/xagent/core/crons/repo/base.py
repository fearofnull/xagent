# -*- coding: utf-8 -*-
"""存储库基类"""
from abc import ABC, abstractmethod
from typing import List, Optional

from ..models import CronJobSpec


class BaseJobRepository(ABC):
    """任务存储库基类"""

    @abstractmethod
    async def list_jobs(self) -> List[CronJobSpec]:
        """列出所有任务"""
        pass

    @abstractmethod
    async def get_job(self, job_id: str) -> Optional[CronJobSpec]:
        """获取任务"""
        pass

    @abstractmethod
    async def upsert_job(self, spec: CronJobSpec) -> None:
        """创建或更新任务"""
        pass

    @abstractmethod
    async def delete_job(self, job_id: str) -> bool:
        """删除任务"""
        pass

    @abstractmethod
    async def load(self) -> object:
        """加载任务"""
        pass

    @abstractmethod
    async def save(self, data: object) -> None:
        """保存任务"""
        pass
