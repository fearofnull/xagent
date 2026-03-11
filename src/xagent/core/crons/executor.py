# -*- coding: utf-8 -*-
"""任务执行器"""
import asyncio
from typing import Any, Optional

from .models import CronJobSpec


class CronExecutor:
    """任务执行器"""

    def __init__(self, runner: Any, channel_manager: Any):
        """初始化执行器

        Args:
            runner: 运行器，用于执行 AI 任务
            channel_manager: 频道管理器，用于发送消息
        """
        self._runner = runner
        self._channel_manager = channel_manager

    async def execute(self, job: CronJobSpec) -> None:
        """执行任务

        Args:
            job: 任务规格

        Raises:
            ValueError: 任务类型不支持
        """
        if job.task_type == "text":
            await self._execute_text_task(job)
        elif job.task_type == "agent":
            await self._execute_agent_task(job)
        else:
            raise ValueError(f"不支持的任务类型: {job.task_type}")

    async def _execute_text_task(self, job: CronJobSpec) -> None:
        """执行文本任务

        Args:
            job: 任务规格

        Raises:
            ValueError: 文本任务缺少文本内容
        """
        if not job.text:
            raise ValueError("文本任务需要文本内容")

        # 优先使用 chat_id,如果为空则使用 user_id
        target_chat_id = job.dispatch.target.chat_id
        target_user_id = job.dispatch.target.user_id
        
        if not target_chat_id and not target_user_id:
            raise ValueError("必须提供 chat_id 或 user_id")
        
        # 发送文本消息到指定频道
        await self._send_message(
            channel=job.dispatch.channel,
            chat_id=target_chat_id,
            user_id=target_user_id,
            content=job.text,
            mode=job.dispatch.mode
        )

    async def _execute_agent_task(self, job: CronJobSpec) -> None:
        """执行 AI 任务

        Args:
            job: 任务规格

        Raises:
            ValueError: AI 任务缺少请求信息
        """
        if not job.request:
            raise ValueError("AI 任务需要请求信息")

        # 执行 AI 任务
        try:
            # 使用超时控制
            response = await asyncio.wait_for(
                self._runner.run(
                    input=job.request.input,
                    session_id=job.request.session_id,
                    user_id=job.request.user_id
                ),
                timeout=job.runtime.timeout_seconds
            )
        except asyncio.TimeoutError:
            response = f"任务执行超时（超过 {job.runtime.timeout_seconds} 秒）"
        except Exception as e:
            response = f"任务执行失败: {str(e)}"

        # 优先使用 chat_id,如果为空则使用 user_id
        target_chat_id = job.dispatch.target.chat_id
        target_user_id = job.dispatch.target.user_id
        
        # 发送响应到指定频道
        await self._send_message(
            channel=job.dispatch.channel,
            chat_id=target_chat_id,
            user_id=target_user_id,
            content=response,
            mode=job.dispatch.mode
        )

    async def _send_message(
        self, 
        channel: str, 
        chat_id: Optional[str],
        user_id: Optional[str],
        content: str, 
        mode: str
    ) -> None:
        """发送消息到频道

        Args:
            channel: 频道名称
            chat_id: 聊天 ID (优先使用)
            user_id: 用户 ID (当 chat_id 为空时使用)
            content: 消息内容
            mode: 发送模式
        """
        if self._channel_manager:
            try:
                await self._channel_manager.send_message(
                    channel=channel,
                    chat_id=chat_id,
                    user_id=user_id,
                    content=content,
                    mode=mode
                )
            except Exception as e:
                # 记录错误但不中断执行
                print(f"发送消息失败: {str(e)}")
