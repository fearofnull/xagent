"""
Feishu AI Bot Package

飞书 AI 机器人包，提供与多个 AI 提供商集成的能力。
"""

__version__ = "1.0.0"

from .utils.cache import DeduplicationCache
from .utils.command_parser import CommandParser
from .config import BotConfig
from .core.message_handler import MessageHandler
from .core.executor_registry import (
    ExecutorRegistry,
    ExecutorNotAvailableError,
    AIExecutor,
)
from .core.smart_router import SmartRouter
from .executors.ai_api_executor import AIAPIExecutor
from .executors.ai_cli_executor import AICLIExecutor
from .executors.claude_cli_executor import ClaudeCodeCLIExecutor
from .executors.gemini_cli_executor import GeminiCLIExecutor
from .models import (
    ExecutionResult,
    Message,
    Session,
    ParsedCommand,
    ExecutorMetadata,
    MessageReceiveEvent,
)

__all__ = [
    "DeduplicationCache",
    "CommandParser",
    "BotConfig",
    "MessageHandler",
    "ExecutorRegistry",
    "ExecutorNotAvailableError",
    "AIExecutor",
    "SmartRouter",
    "AIAPIExecutor",
    "AICLIExecutor",
    "ClaudeCodeCLIExecutor",
    "GeminiCLIExecutor",
    "ExecutionResult",
    "Message",
    "Session",
    "ParsedCommand",
    "ExecutorMetadata",
    "MessageReceiveEvent",
]
