"""
智能路由器模块

根据解析的命令和消息内容，决定使用哪个 AI 执行器
"""
import logging
from typing import Optional, Any

from ..models import ParsedCommand
from .executor_registry import ExecutorRegistry, ExecutorNotAvailableError, AIExecutor
from ..utils.command_parser import CommandParser

logger = logging.getLogger(__name__)


class SmartRouter:
    """智能路由器
    
    根据用户指令智能选择执行器
    
    路由策略：
    1. 显式指定优先：如果用户使用了命令前缀，直接使用指定的提供商和层
    2. 无前缀默认：使用统一API接口（Web配置的提供商）
    3. 无降级：如果执行器不可用或API失败，直接报错，不降级到其他执行器
    """
    
    def __init__(
        self,
        executor_registry: ExecutorRegistry,
        unified_api_interface: Optional[AIExecutor] = None,
        bot_config: Optional[Any] = None
    ):
        """初始化智能路由器
        
        Args:
            executor_registry: 执行器注册表
            unified_api_interface: 统一API接口实例（必需）
            bot_config: 机器人配置对象
        """
        self.executor_registry = executor_registry
        self.command_parser = CommandParser()
        self.unified_api_interface = unified_api_interface
        self.bot_config = bot_config
        
        logger.info(
            f"SmartRouter initialized with "
            f"unified_api={'enabled' if unified_api_interface else 'disabled'}"
        )
    
    def route(self, parsed_command: ParsedCommand) -> AIExecutor:
        """根据解析的命令选择合适的执行器
        
        Args:
            parsed_command: 解析后的命令
            
        Returns:
            AIExecutor: 选择的执行器
            
        Raises:
            ExecutorNotAvailableError: 如果执行器不可用
        """
        provider = parsed_command.provider
        layer = parsed_command.execution_layer
        message_preview = parsed_command.message[:50] + "..." if len(parsed_command.message) > 50 else parsed_command.message
        
        # 特殊处理：如果provider是"agent"，使用Agent执行器
        if provider == "agent":
            # 检查Agent功能是否启用
            if hasattr(self.bot_config, 'agent_enabled') and not self.bot_config.agent_enabled:
                logger.info("[ROUTING] Agent functionality is disabled")
                raise ExecutorNotAvailableError(
                    "agent",
                    "agent",
                    "Agent 功能已被管理员禁用。"
                )
            
            logger.info("[ROUTING] Using Agent executor for @agent command")
            logger.debug(f"[ROUTING] Message: '{message_preview}'")
            try:
                executor = self.get_executor("agent", "agent")
                logger.info("[ROUTING] ✅ Using agent/agent (explicit)")
                return executor
            except ExecutorNotAvailableError as e:
                logger.error(
                    f"[ROUTING] ❌ Agent executor not available: {e.reason}"
                )
                raise ExecutorNotAvailableError(
                    "agent",
                    "agent",
                    f"Agent 执行器不可用: {e.reason}\n\n请检查配置。"
                )
        
        # 特殊处理：如果provider是"unified"，使用统一API接口
        if provider == "unified":
            if self.unified_api_interface is None:
                logger.error("[ROUTING] Unified API interface not configured")
                raise ExecutorNotAvailableError(
                    "unified",
                    "api",
                    "统一API接口未配置。请在Web管理界面配置AI提供商。"
                )
            
            logger.info("[ROUTING] Using Unified API interface for @gpt command")
            logger.debug(f"[ROUTING] Message: '{message_preview}'")
            
            return self.unified_api_interface
        
        # 如果用户显式指定了CLI前缀，直接使用指定的执行器
        if parsed_command.explicit:
            logger.info(
                f"[ROUTING] Explicit prefix detected → provider={provider}, layer={layer}"
            )
            logger.debug(f"[ROUTING] Message: '{message_preview}'")
            try:
                executor = self.get_executor(provider, layer)
                logger.info(f"[ROUTING] ✅ Using {provider}/{layer} (explicit)")
                return executor
            except ExecutorNotAvailableError as e:
                # 显式指定的执行器不可用，直接报错，不降级
                logger.error(
                    f"[ROUTING] ❌ Explicitly specified executor {provider}/{layer} not available: {e.reason}"
                )
                raise ExecutorNotAvailableError(
                    provider,
                    layer,
                    f"{provider}/{layer} 执行器不可用: {e.reason}\n\n请检查配置或尝试其他命令前缀。"
                )
        
        # 没有显式前缀：默认使用统一API接口
        logger.info("[ROUTING] No explicit prefix, using Unified API interface")
        logger.debug(f"[ROUTING] Message: '{message_preview}'")
        
        if self.unified_api_interface is None:
            logger.error("[ROUTING] Unified API interface not configured")
            raise ExecutorNotAvailableError(
                "unified",
                "api",
                "请先在Web管理界面配置AI提供商，或使用CLI命令前缀（如 @claude-cli, @gemini-cli）。\n\n访问 http://localhost:8080 配置提供商。"
            )
        
        return self.unified_api_interface
    
    def get_executor(self, provider: str, layer: str) -> AIExecutor:
        """通过 ExecutorRegistry 获取指定执行器
        
        Args:
            provider: 提供商名称
            layer: 执行层
            
        Returns:
            AIExecutor: 执行器实例
            
        Raises:
            ExecutorNotAvailableError: 如果执行器不可用
        """
        return self.executor_registry.get_executor(provider, layer)
