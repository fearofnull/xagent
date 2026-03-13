﻿# -*- coding: utf-8 -*-
"""核心调度管理器"""
import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .executor import CronExecutor
from .models import CronJobSpec, CronJobState
from .repo.json_repo import JsonJobRepository

HEARTBEAT_JOB_ID = "_heartbeat"

logger = logging.getLogger(__name__)


@dataclass
class _Runtime:
    """运行时信息"""
    sem: asyncio.Semaphore


class CronManager:
    """核心调度管理器"""

    def __init__(
        self,
        *,
        repo: Optional[JsonJobRepository] = None,
        runner: Optional[Any] = None,
        channel_manager: Optional[Any] = None,
        timezone: str = "Asia/Shanghai",
    ):
        """初始化管理器

        Args:
            repo: 任务存储库
            runner: 运行器，用于执行 AI 任务
            channel_manager: 频道管理器，用于发送消息。如果为 None，将创建默认的 ChannelManager
            timezone: 时区
        """
        import os
        from pathlib import Path
        
        # 初始化默认存储库
        if repo is None:
            jobs_dir = os.environ.get("CRON_JOBS_DIR", "./data/cron")
            jobs_path = Path(jobs_dir) / "jobs.json"
            jobs_path.parent.mkdir(parents=True, exist_ok=True)
            repo = JsonJobRepository(path=jobs_path)
        
        # 初始化默认运行器
        if runner is None:
            # 创建一个使用 AgentExecutor 的 runner 适配器
            class RunnerAdapter:
                async def run(self, input, session_id, user_id):
                    """异步执行 AI Agent 任务（带工具能力）"""
                    from src.xagent.core.provider_config_manager import ProviderConfigManager
                    from src.xagent.executors.agent_executor import AgentExecutor
                    
                    # 初始化配置管理器
                    provider_config_manager = ProviderConfigManager(storage_path="./data/provider_configs.json")
                    
                    # 获取默认 provider 配置
                    default_config = provider_config_manager.get_default()
                    if not default_config:
                        return "错误: 未配置默认的 AI provider"
                    
                    # Build message text from structured input
                    def _extract_text(value):
                        parts = []
                        if value is None:
                            return ""
                        if isinstance(value, str):
                            return value
                        if isinstance(value, list):
                            for item in value:
                                parts.append(_extract_text(item))
                            return "\n".join([p for p in parts if p])
                        if isinstance(value, dict):
                            if "text" in value and value["text"]:
                                return str(value["text"])
                            if "content" in value:
                                return _extract_text(value.get("content"))
                        if hasattr(value, "content"):
                            return _extract_text(getattr(value, "content"))
                        return ""

                    message = _extract_text(input).strip()
                    if not message:
                        return "Error: empty task input"
                    
                    # 使用 AgentExecutor（带工具能力）
                    try:
                        executor = AgentExecutor(
                            timeout=3600,  # 60分钟超时
                            provider_config_manager=provider_config_manager
                        )
                        
                        # 使用 asyncio.to_thread 在线程池中执行同步方法
                        result = await asyncio.to_thread(executor.execute, message)
                        return result.stdout if hasattr(result, "stdout") else str(result)
                    except Exception as e:
                        logger.error(f"Agent 执行失败: {str(e)}", exc_info=True)
                        return f"执行失败: {str(e)}"
            
            runner = RunnerAdapter()
        
        # 初始化默认频道管理器
        if channel_manager is None:
            from src.xagent.core.channels import ChannelManager
            
            # 创建默认的空 ChannelManager
            # 注意：实际使用时应该在应用初始化阶段（如 main.py）中
            # 使用配置好的 MessageSender 创建 FeishuChannel 并注册到 ChannelManager
            channel_manager = ChannelManager()
            logger.info("Created default empty ChannelManager")
        
        self._repo = repo
        self._runner = runner
        self._channel_manager = channel_manager
        # 暂时不初始化调度器，在start时根据当前事件循环初始化
        self._scheduler = None
        self._executor = CronExecutor(
            runner=runner,
            channel_manager=channel_manager,
        )

        self._lock = asyncio.Lock()
        self._states: Dict[str, CronJobState] = {}
        self._rt: Dict[str, _Runtime] = {}
        self._started = False
        self._timezone = timezone

    async def start(self) -> None:
        """启动调度器"""
        async with self._lock:
            if self._started:
                return
            jobs_file = await self._repo.load()

            # 初始化调度器，使用 BackgroundScheduler
            if self._scheduler is None:
                self._scheduler = BackgroundScheduler(timezone=self._timezone)

            self._scheduler.start()
            
            # 标记为已启动（必须在注册任务之前设置）
            self._started = True
            
            # 注册所有任务
            for job in jobs_file.jobs:
                await self._register_or_update(job)

            logger.info("CronManager started")

    async def stop(self) -> None:
        """停止调度器"""
        async with self._lock:
            if not self._started:
                return
            self._scheduler.shutdown(wait=False)
            # 重置调度器为None，下次start时会重新初始化
            self._scheduler = None
            self._started = False
            logger.info("CronManager stopped")

    # ----- 同步方法 -----
    
    def start_sync(self) -> None:
        """同步启动调度器"""
        # 使用当前事件循环或创建一个新的
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(self.start())
    
    def stop_sync(self) -> None:
        """同步停止调度器"""
        # 使用当前事件循环或创建一个新的
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(self.stop())
    
    def list_jobs_sync(self) -> list[CronJobSpec]:
        """同步列出所有任务"""
        # 使用当前事件循环或创建一个新的
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.list_jobs())
    
    def get_job_sync(self, job_id: str) -> Optional[CronJobSpec]:
        """同步获取任务"""
        # 使用当前事件循环或创建一个新的
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.get_job(job_id))
    
    def get_state_sync(self, job_id: str) -> CronJobState:
        """同步获取任务状态"""
        return self.get_state(job_id)
    
    def create_or_replace_job_sync(self, spec: CronJobSpec) -> None:
        """同步创建或更新任务"""
        # 使用当前事件循环或创建一个新的
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(self.create_or_replace_job(spec))
    
    def delete_job_sync(self, job_id: str) -> bool:
        """同步删除任务"""
        # 使用当前事件循环或创建一个新的
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.delete_job(job_id))
    
    def pause_job_sync(self, job_id: str) -> None:
        """同步暂停任务"""
        # 使用当前事件循环或创建一个新的
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(self.pause_job(job_id))
    
    def resume_job_sync(self, job_id: str) -> None:
        """同步恢复任务"""
        # 使用当前事件循环或创建一个新的
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(self.resume_job(job_id))
    
    def run_job_sync(self, job_id: str) -> None:
        """同步立即执行任务

        Raises:
            KeyError: 任务不存在
        """
        # 使用当前事件循环或创建一个新的
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(self.run_job(job_id))

    # ----- read/state -----

    async def list_jobs(self) -> list[CronJobSpec]:
        """列出所有任务"""
        return await self._repo.list_jobs()

    async def get_job(self, job_id: str) -> Optional[CronJobSpec]:
        """获取任务"""
        return await self._repo.get_job(job_id)

    def get_state(self, job_id: str) -> CronJobState:
        """获取任务状态"""
        return self._states.get(job_id, CronJobState())

    # ----- write/control -----

    async def create_or_replace_job(self, spec: CronJobSpec) -> None:
        """创建或更新任务"""
        async with self._lock:
            await self._repo.upsert_job(spec)
            if self._started:
                await self._register_or_update(spec)

    async def delete_job(self, job_id: str) -> bool:
        """删除任务"""
        async with self._lock:
            if self._started and self._scheduler and self._scheduler.get_job(job_id):
                self._scheduler.remove_job(job_id)
            self._states.pop(job_id, None)
            self._rt.pop(job_id, None)
            return await self._repo.delete_job(job_id)

    async def pause_job(self, job_id: str) -> None:
        """暂停任务"""
        async with self._lock:
            if self._started and self._scheduler:
                self._scheduler.pause_job(job_id)

    async def resume_job(self, job_id: str) -> None:
        """恢复任务"""
        async with self._lock:
            if self._started and self._scheduler:
                self._scheduler.resume_job(job_id)

    async def run_job(self, job_id: str) -> None:
        """立即执行任务

        Raises:
            KeyError: 任务不存在
        """
        job = await self._repo.get_job(job_id)
        if not job:
            raise KeyError(f"任务不存在: {job_id}")
        logger.info(
            "cron run_job (async): job_id=%s channel=%s task_type=%s "
            "target_chat_id=%s target_user_id=%s",
            job_id,
            job.dispatch.channel,
            job.task_type,
            (job.dispatch.target.chat_id or "")[:40],
            (job.dispatch.target.user_id or "")[:40],
        )
        task = asyncio.create_task(
            self._execute_once(job),
            name=f"cron-run-{job_id}",
        )
        task.add_done_callback(lambda t: self._task_done_cb(t, job))

    # ----- callbacks -----

    def _task_done_cb(self, task: asyncio.Task, job: CronJobSpec) -> None:
        """任务完成回调

        Args:
            task: 任务
            job: 任务规格
        """
        if task.cancelled():
            return
        exc = task.exception()
        if exc is not None:
            logger.error(
                "cron background task %s failed: %s",
                task.get_name(),
                repr(exc),
            )

    # ----- internal -----

    async def _register_or_update(self, spec: CronJobSpec) -> None:
        """注册或更新任务

        Args:
            spec: 任务规格
        """
        # 任务并发控制信号量
        self._rt[spec.id] = _Runtime(
            sem=asyncio.Semaphore(spec.runtime.max_concurrency),
        )

        trigger = self._build_trigger(spec)

        # 替换现有任务
        if self._started and self._scheduler:
            if self._scheduler.get_job(spec.id):
                self._scheduler.remove_job(spec.id)

            self._scheduler.add_job(
                self._scheduled_callback_sync,  # 使用同步包装器
                trigger=trigger,
                id=spec.id,
                args=[spec.id],
                misfire_grace_time=spec.runtime.misfire_grace_seconds,
                replace_existing=True,
            )

            if not spec.enabled:
                self._scheduler.pause_job(spec.id)

            # 更新下次运行时间
            aps_job = self._scheduler.get_job(spec.id)
            st = self._states.get(spec.id, CronJobState())
            st.next_run_at = aps_job.next_run_time if aps_job else None
            self._states[spec.id] = st

    def _build_trigger(self, spec: CronJobSpec) -> CronTrigger:
        """构建触发器

        Args:
            spec: 任务规格

        Returns:
            CronTrigger: 触发器

        Raises:
            ValueError: cron 表达式格式错误
        """
        # 确保 5 个字段（无秒）
        parts = [p for p in spec.schedule.cron.split() if p]
        if len(parts) != 5:
            raise ValueError(
                f"cron 表达式必须有 5 个字段，得到 {len(parts)}: "
                f"{spec.schedule.cron}",
            )

        minute, hour, day, month, day_of_week = parts
        
        # 验证每个字段的有效性
        self._validate_cron_field(minute, 0, 59, "分钟")
        self._validate_cron_field(hour, 0, 23, "小时")
        self._validate_cron_field(day, 1, 31, "日期")
        self._validate_cron_field(month, 1, 12, "月份")
        self._validate_cron_field(day_of_week, 0, 6, "星期")

        return CronTrigger(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            timezone=spec.schedule.timezone,
        )
    
    def _validate_cron_field(self, field: str, min_val: int, max_val: int, field_name: str):
        """验证 cron 表达式字段
        
        Args:
            field: 字段值
            min_val: 最小值
            max_val: 最大值
            field_name: 字段名称
            
        Raises:
            ValueError: 字段值无效
        """
        # 支持通配符
        if field == "*":
            return
        
        # 支持范围，如 1-5
        if "-" in field:
            start, end = field.split("-")
            try:
                start_val = int(start)
                end_val = int(end)
                if start_val < min_val or end_val > max_val or start_val > end_val:
                    raise ValueError(f"{field_name}范围无效: {field}")
            except ValueError:
                raise ValueError(f"{field_name}范围格式无效: {field}")
            return
        
        # 支持逗号分隔，如 1,3,5
        if "," in field:
            values = field.split(",")
            for val in values:
                try:
                    int_val = int(val)
                    if int_val < min_val or int_val > max_val:
                        raise ValueError(f"{field_name}值无效: {val}")
                except ValueError:
                    raise ValueError(f"{field_name}值格式无效: {val}")
            return
        
        # 支持步长，如 */5
        if "/" in field:
            parts = field.split("/")
            if len(parts) != 2:
                raise ValueError(f"{field_name}步长格式无效: {field}")
            
            interval_part = parts[1]
            try:
                interval = int(interval_part)
                if interval <= 0:
                    raise ValueError(f"{field_name}步长必须大于 0: {interval}")
            except ValueError:
                raise ValueError(f"{field_name}步长格式无效: {interval_part}")
            return
        
        # 单个数字
        try:
            int_val = int(field)
            if int_val < min_val or int_val > max_val:
                raise ValueError(f"{field_name}值超出范围 [{min_val}-{max_val}]: {int_val}")
        except ValueError:
            raise ValueError(f"{field_name}值格式无效: {field}")

    def _scheduled_callback_sync(self, job_id: str) -> None:
        """同步调度回调（用于 BackgroundScheduler）

        Args:
            job_id: 任务 ID
        """
        # 在新的事件循环中运行异步回调
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._scheduled_callback(job_id))
        finally:
            loop.close()

    async def _scheduled_callback(self, job_id: str) -> None:
        """调度回调

        Args:
            job_id: 任务 ID
        """
        job = await self._repo.get_job(job_id)
        if not job:
            return

        await self._execute_once(job)

        # 刷新下次运行时间
        if self._started and self._scheduler:
            aps_job = self._scheduler.get_job(job_id)
            st = self._states.get(job_id, CronJobState())
            st.next_run_at = aps_job.next_run_time if aps_job else None
            self._states[job_id] = st

    async def _execute_once(self, job: CronJobSpec) -> None:
        """执行一次任务

        Args:
            job: 任务规格
        """
        rt = self._rt.get(job.id)
        if not rt:
            rt = _Runtime(sem=asyncio.Semaphore(job.runtime.max_concurrency))
            self._rt[job.id] = rt

        async with rt.sem:
            st = self._states.get(job.id, CronJobState())
            st.last_status = "running"
            self._states[job.id] = st

            try:
                await self._executor.execute(job)
                st.last_status = "success"
                st.last_error = None
                logger.info(
                    "cron _execute_once: job_id=%s status=success",
                    job.id,
                )
            except Exception as e:
                st.last_status = "error"
                st.last_error = repr(e)
                logger.warning(
                    "cron _execute_once: job_id=%s status=error error=%s",
                    job.id,
                    repr(e),
                )
                raise
            finally:
                st.last_run_at = datetime.utcnow()
                self._states[job.id] = st
