"""
Claude API 执行器实现

调用 Claude API 执行 AI 任务。
支持对话历史上下文和可选参数配置。

参考文档: https://docs.anthropic.com/claude/reference/getting-started-with-the-api
"""
import time
import logging
from typing import Optional, List, Dict, Any
import anthropic
from .ai_api_executor import AIAPIExecutor
from ..models import ExecutionResult, Message

logger = logging.getLogger(__name__)


class ClaudeAPIExecutor(AIAPIExecutor):
    """Claude API 执行器
    
    使用 Anthropic Python SDK 调用 Claude API。
    支持多轮对话上下文和灵活的参数配置。
    """
    
    def __init__(
        self, 
        api_key: str,
        model: str = "claude-3-opus-20240229",
        timeout: int = 60,
        base_url: Optional[str] = None
    ):
        """初始化 Claude API 执行器
        
        Args:
            api_key: Anthropic API 密钥
            model: Claude 模型名称，默认使用 claude-3-opus-20240229
            timeout: 请求超时时间（秒）
            base_url: API 基础 URL（可选，用于兼容 Claude 的 API）
        """
        super().__init__(api_key, model, timeout)
        if base_url:
            self.client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
        else:
            self.client = anthropic.Anthropic(api_key=api_key)
    
    def get_provider_name(self) -> str:
        """返回 AI 提供商名称
        
        Returns:
            "claude-api"
        """
        return "claude-api"
    
    def format_messages(
        self, 
        user_prompt: str,
        conversation_history: Optional[List[Message]] = None
    ) -> List[Dict[str, str]]:
        """格式化为 Claude API 消息格式
        
        Claude API 使用 "user" 和 "assistant" 角色。
        
        Args:
            user_prompt: 用户提示
            conversation_history: 对话历史
            
        Returns:
            格式化后的消息列表，每个消息包含 role 和 content 字段
        """
        messages = []
        
        # 添加对话历史
        if conversation_history:
            for msg in conversation_history:
                messages.append({
                    "role": msg.role,  # "user" 或 "assistant"
                    "content": msg.content
                })
        
        # 添加当前用户消息
        messages.append({
            "role": "user",
            "content": user_prompt
        })
        
        return messages
    
    def execute(
        self, 
        user_prompt: str,
        conversation_history: Optional[List[Message]] = None,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """调用 Claude API 执行任务
        
        Args:
            user_prompt: 用户提示
            conversation_history: 对话历史（用于上下文）
            additional_params: 额外参数，支持：
                - temperature: 温度参数（0-2）
                - max_tokens: 最大输出 token 数
                
        Returns:
            ExecutionResult: 包含执行结果的对象
        """
        try:
            logger.info(f"Executing Claude API call with model={self.model}")
            messages = self.format_messages(user_prompt, conversation_history)
            
            # 构建请求参数
            request_params = {
                "model": self.model,
                "messages": messages,
            }
            
            # 添加可选参数
            if additional_params:
                if "temperature" in additional_params:
                    request_params["temperature"] = additional_params["temperature"]
                if "max_tokens" in additional_params:
                    request_params["max_tokens"] = additional_params["max_tokens"]
            
            logger.debug(f"Claude API request params: {request_params.keys()}")
            
            # 调用 API
            start_time = time.time()
            response = self.client.messages.create(**request_params)
            execution_time = time.time() - start_time
            
            # 提取响应内容
            content = response.content[0].text
            
            logger.info(
                f"Claude API call successful: execution_time={execution_time:.2f}s, "
                f"response_length={len(content)}"
            )
            
            return ExecutionResult(
                success=True,
                stdout=content,
                stderr="",
                error_message=None,
                execution_time=execution_time
            )
            
        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                error_message=f"Claude API error: {e}",
                execution_time=0
            )
        except Exception as e:
            logger.error(f"Unexpected error in Claude API execution: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                error_message=f"Unexpected error: {e}",
                execution_time=0
            )
