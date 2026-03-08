"""
AI API 执行器抽象基类

定义所有 AI API 执行器的通用接口和共享逻辑。
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from ..models import ExecutionResult, Message


class AIAPIExecutor(ABC):
    """AI API 执行器抽象基类
    
    所有 AI API 执行器（Claude API、Gemini API、OpenAI API）的基类。
    定义了通用接口和共享的初始化逻辑。
    
    Requirements: 14.1, 14.2, 14.3
    """
    
    def __init__(self, api_key: str, model: Optional[str] = None, timeout: int = 60):
        """初始化 AI API 执行器
        
        Args:
            api_key: API 密钥
            model: 模型名称（可选，使用默认模型）
            timeout: 请求超时时间（秒）
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
    
    @abstractmethod
    def execute(
        self,
        user_prompt: str,
        conversation_history: Optional[List[Message]] = None,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """执行 AI API 调用，返回执行结果
        
        Args:
            user_prompt: 用户提示
            conversation_history: 对话历史（用于上下文）
            additional_params: 额外参数（如 temperature, max_tokens）
            
        Returns:
            ExecutionResult: 执行结果
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """返回 AI 提供商名称
        
        Returns:
            提供商名称（如 "claude-api", "gemini-api", "openai-api"）
        """
        pass
    
    @abstractmethod
    def format_messages(
        self,
        user_prompt: str,
        conversation_history: Optional[List[Message]] = None
    ) -> List[Dict[str, str]]:
        """将用户提示和对话历史格式化为 API 所需的消息格式
        
        不同的 AI API 有不同的消息格式要求：
        - Claude API: {"role": "user"/"assistant", "content": "..."}
        - Gemini API: {"role": "user"/"model", "parts": ["..."]}
        - OpenAI API: {"role": "user"/"assistant", "content": "..."}
        
        Args:
            user_prompt: 用户提示
            conversation_history: 对话历史
            
        Returns:
            格式化后的消息列表
        """
        pass
    
    def is_available(self) -> bool:
        """检查执行器是否可用
        
        Returns:
            True 如果 API 密钥已配置
        """
        return bool(self.api_key)
