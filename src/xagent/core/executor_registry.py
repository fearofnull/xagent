"""
执行器注册表模块

管理所有 AI 执行器的注册、发现和获取
"""
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
import logging
import json
import os
from pathlib import Path

from ..models import ExecutorMetadata, ExecutionResult

logger = logging.getLogger(__name__)


class ExecutorNotAvailableError(Exception):
    """执行器不可用异常"""
    
    def __init__(self, provider: str, layer: str, reason: str):
        self.provider = provider
        self.layer = layer
        self.reason = reason
        super().__init__(f"Executor {provider}/{layer} not available: {reason}")


class AIExecutor(ABC):
    """AI 执行器抽象基类"""
    
    @abstractmethod
    def execute(
        self,
        user_prompt: str,
        conversation_history: Optional[List[Any]] = None,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """执行 AI 调用"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查执行器是否可用"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """返回提供商名称"""
        pass


class ExecutorRegistry:
    """执行器注册表
    
    管理所有 AI 执行器的注册、发现和获取
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化执行器注册表

        Args:
            config_path: 配置文件路径（可选）
        """
        self.api_executors: Dict[str, AIExecutor] = {}
        self.cli_executors: Dict[str, AIExecutor] = {}
        self.agent_executors: Dict[str, AIExecutor] = {}
        self.executor_metadata: Dict[str, ExecutorMetadata] = {}
        self._availability_cache: Dict[str, bool] = {}
        self.config_path = config_path

        # 如果提供了配置文件路径，加载配置
        if config_path and os.path.exists(config_path):
            self._load_from_config(config_path)
    
    def register_api_executor(
        self,
        provider: str,
        executor: AIExecutor,
        metadata: Optional[ExecutorMetadata] = None
    ) -> None:
        """注册 API 执行器
        
        Args:
            provider: 提供商名称（如 "claude", "gemini", "openai"）
            executor: 执行器实例
            metadata: 执行器元数据（可选）
        """
        self.api_executors[provider] = executor
        
        if metadata:
            key = f"{provider}_api"
            self.executor_metadata[key] = metadata
            logger.info(f"Registered API executor: {provider} - {metadata.name}")
        else:
            logger.info(f"Registered API executor: {provider}")
    
    def register_cli_executor(
        self,
        provider: str,
        executor: AIExecutor,
        metadata: Optional[ExecutorMetadata] = None
    ) -> None:
        """注册 CLI 执行器

        Args:
            provider: 提供商名称（如 "claude", "gemini"）
            executor: 执行器实例
            metadata: 执行器元数据（可选）
        """
        self.cli_executors[provider] = executor

        if metadata:
            key = f"{provider}_cli"
            self.executor_metadata[key] = metadata
            logger.info(f"Registered CLI executor: {provider} - {metadata.name}")
        else:
            logger.info(f"Registered CLI executor: {provider}")

    def register_agent_executor(
        self,
        provider: str,
        executor: AIExecutor,
        metadata: Optional[ExecutorMetadata] = None
    ) -> None:
        """注册 Agent 执行器

        Args:
            provider: 提供商名称（如 "agent"）
            executor: 执行器实例
            metadata: 执行器元数据（可选）
        """
        self.agent_executors[provider] = executor

        if metadata:
            key = f"{provider}_agent"
            self.executor_metadata[key] = metadata
            logger.info(f"Registered Agent executor: {provider} - {metadata.name}")
        else:
            logger.info(f"Registered Agent executor: {provider}")
    
    def get_executor(self, provider: str, layer: str) -> AIExecutor:
        """获取指定提供商和层的执行器

        Args:
            provider: 提供商名称
            layer: 执行层（"api", "cli" 或 "agent"）

        Returns:
            执行器实例

        Raises:
            ExecutorNotAvailableError: 如果执行器不可用
        """
        # 选择对应的执行器字典
        if layer == "api":
            executors = self.api_executors
        elif layer == "cli":
            executors = self.cli_executors
        elif layer == "agent":
            executors = self.agent_executors
        else:
            raise ExecutorNotAvailableError(
                provider,
                layer,
                f"Invalid execution layer: {layer}"
            )

        # 检查执行器是否存在
        if provider not in executors:
            raise ExecutorNotAvailableError(
                provider,
                layer,
                f"Executor not registered"
            )

        executor = executors[provider]

        # 检查执行器是否可用（使用缓存）
        cache_key = f"{provider}_{layer}"
        if cache_key not in self._availability_cache:
            self._availability_cache[cache_key] = executor.is_available()

        if not self._availability_cache[cache_key]:
            # 获取不可用原因
            reason = self._get_unavailability_reason(provider, layer, executor)
            raise ExecutorNotAvailableError(provider, layer, reason)

        return executor
    
    def list_available_executors(self, layer: Optional[str] = None) -> List[str]:
        """列出所有可用的执行器

        Args:
            layer: 执行层过滤（"api", "cli" 或 "agent"），None 表示列出所有

        Returns:
            可用执行器的提供商名称列表
        """
        available = []

        # 检查 API 执行器
        if layer is None or layer == "api":
            for provider, executor in self.api_executors.items():
                if self.is_executor_available(provider, "api"):
                    available.append(f"{provider}/api")

        # 检查 CLI 执行器
        if layer is None or layer == "cli":
            for provider, executor in self.cli_executors.items():
                if self.is_executor_available(provider, "cli"):
                    available.append(f"{provider}/cli")

        # 检查 Agent 执行器
        if layer is None or layer == "agent":
            for provider, executor in self.agent_executors.items():
                if self.is_executor_available(provider, "agent"):
                    available.append(f"{provider}/agent")

        return available
    
    def get_executor_metadata(self, provider: str, layer: str) -> Optional[ExecutorMetadata]:
        """获取执行器元数据

        Args:
            provider: 提供商名称
            layer: 执行层（"api", "cli" 或 "agent"）

        Returns:
            执行器元数据，如果不存在则返回 None
        """
        key = f"{provider}_{layer}"
        return self.executor_metadata.get(key)
    
    def is_executor_available(self, provider: str, layer: str) -> bool:
        """检查执行器是否可用
        
        Args:
            provider: 提供商名称
            layer: 执行层
            
        Returns:
            True 如果执行器可用
        """
        try:
            self.get_executor(provider, layer)
            return True
        except ExecutorNotAvailableError:
            return False
    
    def clear_availability_cache(self) -> None:
        """清除可用性缓存
        
        用于强制重新检查执行器可用性
        """
        self._availability_cache.clear()
        logger.debug("Cleared executor availability cache")
    
    def _get_unavailability_reason(
        self,
        provider: str,
        layer: str,
        executor: AIExecutor
    ) -> str:
        """获取执行器不可用的原因
        
        Args:
            provider: 提供商名称
            layer: 执行层
            executor: 执行器实例
            
        Returns:
            不可用原因描述
        """
        # 获取元数据中的必需配置
        metadata = self.get_executor_metadata(provider, layer)
        if metadata and metadata.config_required:
            return f"Missing required configuration: {', '.join(metadata.config_required)}"
        
        # 默认原因
        if layer == "api":
            return "API key not configured or invalid"
        else:
            return "CLI tool not installed or target directory not accessible"
    
    def get_openai_executor(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: int = 60
    ) -> AIExecutor:
        """创建并返回 OpenAI 兼容执行器
        
        此方法用于统一 API 接口，根据提供商配置动态创建 OpenAI 兼容的执行器。
        支持标准 OpenAI API 以及任何兼容 OpenAI API 格式的服务。
        
        Args:
            base_url: API 端点 URL
            api_key: API 密钥
            model: 模型名称
            timeout: 请求超时时间（秒），默认 60 秒
            
        Returns:
            OpenAI 兼容执行器实例
            
        Example:
            >>> registry = ExecutorRegistry()
            >>> executor = registry.get_openai_executor(
            ...     base_url="https://api.openai.com/v1",
            ...     api_key="sk-...",
            ...     model="gpt-4"
            ... )
            >>> result = executor.execute("Hello, world!")
        """
        from ..executors.openai_api_executor import OpenAIAPIExecutor
        
        logger.info(
            f"Creating OpenAI compatible executor: "
            f"base_url={base_url}, model={model}, timeout={timeout}"
        )
        
        return OpenAIAPIExecutor(
            api_key=api_key,
            model=model,
            timeout=timeout,
            base_url=base_url
        )
    
    def _load_from_config(self, config_path: str) -> None:
        """从配置文件加载执行器注册信息
        
        Args:
            config_path: 配置文件路径
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 加载执行器元数据
            if 'executors' in config:
                for executor_config in config['executors']:
                    provider = executor_config.get('provider')
                    layer = executor_config.get('layer')
                    
                    if not provider or not layer:
                        continue
                    
                    # 创建元数据
                    metadata = ExecutorMetadata(
                        name=executor_config.get('name', f"{provider} {layer}"),
                        provider=provider,
                        layer=layer,
                        version=executor_config.get('version', '1.0.0'),
                        description=executor_config.get('description', ''),
                        capabilities=executor_config.get('capabilities', []),
                        command_prefixes=executor_config.get('command_prefixes', []),
                        priority=executor_config.get('priority', 10),
                        config_required=executor_config.get('config_required', [])
                    )
                    
                    # 存储元数据
                    key = f"{provider}_{layer}"
                    self.executor_metadata[key] = metadata
            
            logger.info(f"Loaded executor configuration from {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load executor configuration: {e}")
