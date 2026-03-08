"""
统一API接口模块

提供单一的@gpt命令前缀，根据配置管理器的默认提供商路由请求到对应的执行器。
支持OpenAI兼容、Claude兼容、Gemini兼容类型。
"""
import logging
from typing import Optional, List, Dict, Any

from .provider_config_manager import ProviderConfigManager
from .executor_registry import ExecutorRegistry, AIExecutor, ExecutorNotAvailableError
from ..models import ExecutionResult, ProviderConfig


logger = logging.getLogger(__name__)


class UnifiedAPIInterface(AIExecutor):
    """统一API接口
    
    提供单一的@gpt命令前缀，根据配置管理器的默认提供商路由请求。
    支持：
    - OpenAI兼容类型的提供商
    - 自动降级到其他可用提供商（可选）
    - 完善的错误处理和日志记录
    """
    
    def __init__(
        self,
        config_manager: ProviderConfigManager,
        executor_registry: ExecutorRegistry,
        enable_fallback: bool = False
    ):
        """初始化统一API接口
        
        Args:
            config_manager: 配置管理器实例
            executor_registry: 执行器注册表实例
            enable_fallback: 是否启用自动降级，默认为False
        """
        self.config_manager = config_manager
        self.executor_registry = executor_registry
        self.enable_fallback = enable_fallback
        
        logger.info(
            f"UnifiedAPIInterface initialized (fallback={'enabled' if enable_fallback else 'disabled'})"
        )
    
    def is_available(self) -> bool:
        """检查执行器是否可用
        
        Returns:
            True 如果有配置的默认提供商
        """
        default_config = self.config_manager.get_default()
        return default_config is not None
    
    def get_provider_name(self) -> str:
        """获取提供商名称
        
        Returns:
            提供商名称，格式为 "unified-api"
        """
        return "unified-api"
    
    def get_current_provider_config(self) -> Optional[ProviderConfig]:
        """获取当前使用的提供商配置
        
        Returns:
            当前默认提供商配置，如果未配置则返回 None
        """
        return self.config_manager.get_default()
    
    def execute(
        self,
        user_prompt: str,
        conversation_history: Optional[List[Dict]] = None,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """执行统一API调用
        
        根据默认提供商配置路由请求到对应的执行器。
        如果默认提供商不可用且启用了自动降级，会尝试其他可用提供商。
        
        Args:
            user_prompt: 用户消息
            conversation_history: 对话历史（可选）
            additional_params: 额外参数（可选，保持与AIExecutor基类签名一致）
            
        Returns:
            执行结果
        """
        message = user_prompt
        # 获取默认提供商配置
        default_config = self.config_manager.get_default()
        
        # 检查是否配置了默认提供商
        if not default_config:
            logger.error("未配置默认提供商")
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                error_message="请先在Web管理界面配置AI提供商",
                execution_time=0.0
            )
        
        # 尝试使用默认提供商
        try:
            executor = self._get_executor_for_config(default_config)
            logger.info(f"使用默认提供商: {default_config.name} ({default_config.type})")
            
            # 执行调用
            result = executor.execute(
                user_prompt=message,
                conversation_history=conversation_history
            )
            
            return result
            
        except ExecutorNotAvailableError as e:
            logger.warning(
                f"默认提供商 {default_config.name} 不可用: {e.reason}"
            )
            
            # 如果启用了自动降级，尝试其他提供商
            if self.enable_fallback:
                return self._fallback_to_alternative(default_config, message, conversation_history)
            else:
                # 返回错误消息
                error_msg = f"{default_config.name} 调用失败: {e.reason}"
                return ExecutionResult(
                    success=False,
                    stdout="",
                    stderr="",
                    error_message=error_msg,
                    execution_time=0.0
                )
        
        except Exception as e:
            logger.error(
                f"调用提供商 {default_config.name} 时发生错误: {e}",
                exc_info=True
            )
            
            # 如果启用了自动降级，尝试其他提供商
            if self.enable_fallback:
                return self._fallback_to_alternative(default_config, message, conversation_history)
            else:
                # 返回错误消息
                error_msg = f"{default_config.name} 调用失败: {str(e)}"
                return ExecutionResult(
                    success=False,
                    stdout="",
                    stderr="",
                    error_message=error_msg,
                    execution_time=0.0
                )
    
    def _get_executor_for_config(self, config: ProviderConfig) -> AIExecutor:
        """根据配置获取执行器
        
        根据配置的type字段选择对应的执行器：
        - openai_compatible: 使用OpenAI兼容执行器
        - claude_compatible: 使用Claude执行器
        - gemini_compatible: 使用Gemini执行器
        
        Args:
            config: 提供商配置
            
        Returns:
            执行器实例
            
        Raises:
            ExecutorNotAvailableError: 如果配置类型不支持或执行器不可用
        """
        if config.type == "openai_compatible":
            # 使用执行器注册表创建OpenAI兼容执行器
            return self.executor_registry.get_openai_executor(
                base_url=config.base_url,
                api_key=config.api_key,
                model=config.default_model
            )
        
        elif config.type == "claude_compatible":
            # 使用Claude执行器
            from ..executors.claude_api_executor import ClaudeAPIExecutor
            return ClaudeAPIExecutor(
                api_key=config.api_key,
                model=config.default_model,
                base_url=config.base_url
            )
        
        elif config.type == "gemini_compatible":
            # 使用Gemini执行器
            from ..executors.gemini_api_executor import GeminiAPIExecutor
            return GeminiAPIExecutor(
                api_key=config.api_key,
                model=config.default_model,
                base_url=config.base_url
            )
        
        else:
            # 未知类型
            raise ExecutorNotAvailableError(
                provider=config.name,
                layer="api",
                reason=f"不支持的配置类型: {config.type}"
            )
    
    def _fallback_to_alternative(
        self,
        failed_config: ProviderConfig,
        message: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> ExecutionResult:
        """降级到其他可用提供商
        
        当默认提供商不可用时，尝试使用其他已配置的提供商。
        优先选择相同类型的提供商，然后尝试其他类型。
        
        Args:
            failed_config: 失败的提供商配置
            message: 用户消息
            conversation_history: 对话历史
            
        Returns:
            执行结果
        """
        logger.info(f"尝试降级到其他可用提供商（失败的提供商: {failed_config.name}）")
        
        # 获取所有配置
        all_configs = self.config_manager.list_configs()
        
        # 过滤掉失败的配置
        alternative_configs = [
            config for config in all_configs
            if config.name != failed_config.name
        ]
        
        if not alternative_configs:
            logger.error("没有其他可用的提供商配置")
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                error_message="所有AI提供商当前不可用，请稍后重试",
                execution_time=0.0
            )
        
        # 优先尝试相同类型的提供商
        same_type_configs = [
            config for config in alternative_configs
            if config.type == failed_config.type
        ]
        
        # 构建尝试顺序：先相同类型，再其他类型
        try_order = same_type_configs + [
            config for config in alternative_configs
            if config not in same_type_configs
        ]
        
        # 尝试每个备选提供商
        for config in try_order:
            try:
                executor = self._get_executor_for_config(config)
                logger.warning(
                    f"Fallback to {config.name} due to {failed_config.name} unavailable"
                )
                
                # 执行调用
                result = executor.execute(
                    user_prompt=message,
                    conversation_history=conversation_history
                )
                
                # 在响应中添加降级提示
                if result.success and result.stdout:
                    fallback_notice = f"\n\n[注意: 使用了备用提供商 {config.name}]"
                    result.stdout += fallback_notice
                
                return result
                
            except Exception as e:
                logger.warning(
                    f"备选提供商 {config.name} 也不可用: {e}"
                )
                continue
        
        # 所有提供商都不可用
        logger.error("所有配置的提供商都不可用")
        return ExecutionResult(
            success=False,
            stdout="",
            stderr="",
            error_message="所有AI提供商当前不可用，请稍后重试",
            execution_time=0.0
        )
