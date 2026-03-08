# -*- coding: utf-8 -*-
"""配置模块

包含机器人的配置管理功能
"""
import os
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings

from .utils import get_playwright_chromium_executable_path, is_running_in_container, get_system_default_browser


class AgentConfig(BaseSettings):
    """Agent 配置"""
    language: str = "zh-CN"


class AgentsConfig(BaseSettings):
    """Agents 配置"""
    language: str = "zh-CN"


class Config(BaseSettings):
    """主配置"""
    agents: AgentsConfig = AgentsConfig()


def load_config() -> Config:
    """加载配置
    
    Returns:
        Config: 配置对象
    """
    return Config()


class BotConfig:
    """机器人配置"""
    
    def __init__(
        self,
        app_id: str,
        app_secret: str,
        target_directory: Optional[str] = None,
        ai_timeout: int = 600,
        cache_size: int = 1000,
        session_storage_path: str = "./data/sessions.json",
        max_session_messages: int = 50,
        session_timeout: int = 86400,
        claude_cli_target_dir: Optional[str] = None,
        gemini_cli_target_dir: Optional[str] = None,
        qwen_cli_target_dir: Optional[str] = None,
        response_language: Optional[str] = None,
        default_cli_provider: Optional[str] = None,
        agent_enabled: bool = True
    ):
        """初始化机器人配置
        
        Args:
            app_id: 飞书应用 ID
            app_secret: 飞书应用密钥
            target_directory: 目标项目目录
            ai_timeout: AI 执行超时时间
            cache_size: 缓存大小
            session_storage_path: 会话存储路径
            max_session_messages: 单个会话最大消息数
            session_timeout: 会话超时时间
            claude_cli_target_dir: Claude CLI 目标目录
            gemini_cli_target_dir: Gemini CLI 目标目录
            qwen_cli_target_dir: Qwen CLI 目标目录
            response_language: 响应语言
            default_cli_provider: 默认 CLI 提供商
            agent_enabled: 是否启用 Agent 功能
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.target_directory = target_directory
        self.ai_timeout = ai_timeout
        self.cache_size = cache_size
        self.session_storage_path = session_storage_path
        self.max_session_messages = max_session_messages
        self.session_timeout = session_timeout
        self.claude_cli_target_dir = claude_cli_target_dir
        self.gemini_cli_target_dir = gemini_cli_target_dir
        self.qwen_cli_target_dir = qwen_cli_target_dir
        self.response_language = response_language
        self.default_cli_provider = default_cli_provider
        self.agent_enabled = agent_enabled
    
    @classmethod
    def from_env(cls) -> 'BotConfig':
        """从环境变量加载配置
        
        Returns:
            BotConfig: 配置对象
        """
        return cls(
            app_id=os.environ.get("FEISHU_APP_ID", ""),
            app_secret=os.environ.get("FEISHU_APP_SECRET", ""),
            target_directory=os.environ.get("TARGET_PROJECT_DIR"),
            ai_timeout=int(os.environ.get("AI_TIMEOUT", "600")),
            cache_size=int(os.environ.get("CACHE_SIZE", "1000")),
            session_storage_path=os.environ.get("SESSION_STORAGE_PATH", "./data/sessions.json"),
            max_session_messages=int(os.environ.get("MAX_SESSION_MESSAGES", "50")),
            session_timeout=int(os.environ.get("SESSION_TIMEOUT", "86400")),
            claude_cli_target_dir=os.environ.get("CLAUDE_CLI_TARGET_DIR"),
            gemini_cli_target_dir=os.environ.get("GEMINI_CLI_TARGET_DIR"),
            qwen_cli_target_dir=os.environ.get("QWEN_CLI_TARGET_DIR"),
            response_language=os.environ.get("RESPONSE_LANGUAGE"),
            default_cli_provider=os.environ.get("DEFAULT_CLI_PROVIDER"),
            agent_enabled=os.environ.get("AGENT_ENABLED", "true").lower() == "true"
        )

__all__ = [
    "AgentConfig",
    "AgentsConfig",
    "Config",
    "BotConfig",
    "load_config",
    "get_playwright_chromium_executable_path",
    "is_running_in_container",
    "get_system_default_browser",
]
