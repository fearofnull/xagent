# -*- coding: utf-8 -*-
"""定时任务数据模型"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


class CronJobTarget(BaseModel):
    """任务目标
    
    定时任务支持两种发送目标:
    1. 私聊 (P2P): 设置 user_id
    2. 群聊 (Group): 设置 chat_id
    
    优先使用 chat_id,如果为空则使用 user_id
    
    注意: 定时任务是主动发送,不支持回复消息
    """
    chat_id: Optional[str] = Field(
        None, 
        description="聊天 ID (私聊或群聊,优先使用)"
    )
    user_id: Optional[str] = Field(
        None, 
        description="用户 ID (open_id, 当 chat_id 为空时使用)"
    )


class CronJobDispatch(BaseModel):
    """任务分发"""
    type: str = "channel"
    channel: str = "console"
    target: CronJobTarget = Field(default_factory=CronJobTarget)
    mode: str = "final"
    meta: Dict[str, Any] = Field(default_factory=dict)


class CronJobSchedule(BaseModel):
    """任务调度"""
    type: str = "cron"
    cron: str = "0 0 * * *"
    timezone: str = "UTC"


class CronJobRuntime(BaseModel):
    """任务运行时配置"""
    max_concurrency: int = 1
    timeout_seconds: int = 120
    misfire_grace_seconds: int = 60


class CronJobRequestInput(BaseModel):
    """任务请求输入"""
    role: str
    type: str
    content: List[Dict[str, Any]]


class CronJobRequest(BaseModel):
    """任务请求"""
    input: List[CronJobRequestInput]
    session_id: Optional[str] = None
    user_id: str = "cron"


class CronJobSpec(BaseModel):
    """任务规格"""
    id: str
    name: str
    enabled: bool = True
    schedule: CronJobSchedule = Field(default_factory=CronJobSchedule)
    task_type: str = "text"  # text or agent
    text: Optional[str] = None
    request: Optional[CronJobRequest] = None
    dispatch: CronJobDispatch = Field(default_factory=CronJobDispatch)
    runtime: CronJobRuntime = Field(default_factory=CronJobRuntime)
    meta: Dict[str, Any] = Field(default_factory=dict)


class CronJobState(BaseModel):
    """任务状态"""
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    last_status: Optional[str] = None  # running, success, error
    last_error: Optional[str] = None


class CronJobView(BaseModel):
    """任务视图"""
    spec: CronJobSpec
    state: CronJobState
