"""
OpenAI API 执行器实现

调用 OpenAI API 执行 AI 任务。
支持对话历史上下文和可选参数配置。

参考文档: https://platform.openai.com/docs/api-reference/chat
"""
import time
import logging
from typing import Optional, List, Dict, Any
import openai
from .ai_api_executor import AIAPIExecutor
from ..models import ExecutionResult, Message

logger = logging.getLogger(__name__)


class OpenAIAPIExecutor(AIAPIExecutor):
    """OpenAI API 执行器
    
    使用 OpenAI Python SDK 调用 OpenAI API。
    支持多轮对话上下文和灵活的参数配置。
    
    Requirements: 14.3, 14.4, 14.5, 14.6, 14.7, 14.8, 14.9, 14.10, 15.1, 15.4, 15.5, 15.6
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        timeout: int = 60,
        base_url: Optional[str] = None
    ):
        """初始化 OpenAI API 执行器
        
        Args:
            api_key: OpenAI API 密钥
            model: OpenAI 模型名称，默认使用 gpt-4o
            timeout: 请求超时时间（秒）
            base_url: API 基础 URL（可选，用于兼容 OpenAI 的 API）
        """
        super().__init__(api_key, model, timeout)
        default_headers = {"API-KEY": api_key}
        if base_url:
            self.client = openai.OpenAI(
                api_key=api_key,
                base_url=base_url,
                default_headers=default_headers,
            )
        else:
            self.client = openai.OpenAI(
                api_key=api_key,
                default_headers=default_headers,
            )
    
    def get_provider_name(self) -> str:
        """返回 AI 提供商名称
        
        Returns:
            "openai-api"
        """
        return "openai-api"
    
    def format_messages(
        self,
        user_prompt: str,
        conversation_history: Optional[List[Message]] = None
    ) -> List[Dict[str, str]]:
        """格式化为 OpenAI API 消息格式
        
        OpenAI API 使用 "user" 和 "assistant" 角色。
        
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
        """调用 OpenAI API 执行任务
        
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
            logger.info(f"Executing OpenAI API call with model={self.model}")
            messages = self.format_messages(user_prompt, conversation_history)
            
            # 构建请求参数
            request_params = {
                "model": self.model,
                "messages": messages,
            }
            use_max_completion_tokens = str(self.model).startswith("gpt-5")
            
            # 添加可选参数
            if additional_params:
                if "temperature" in additional_params:
                    request_params["temperature"] = additional_params["temperature"]
                if "max_tokens" in additional_params:
                    if use_max_completion_tokens:
                        request_params["max_completion_tokens"] = additional_params["max_tokens"]
                    else:
                        request_params["max_tokens"] = additional_params["max_tokens"]
            
            logger.debug(f"OpenAI API request params: {request_params.keys()}")
            
            # 调用 API
            start_time = time.time()
            response = self.client.chat.completions.create(**request_params)
            execution_time = time.time() - start_time
            
            # 提取响应内容，添加空值检查
            if not response or not response.choices:
                logger.error(f"OpenAI API returned empty response: {response}")
                return ExecutionResult(
                    success=False,
                    stdout="",
                    stderr="API returned empty response",
                    error_message="OpenAI API returned empty or invalid response",
                    execution_time=execution_time
                )
            
            content = response.choices[0].message.content or ""

            # Fallback: try raw HTTP if content is empty
            if not content:
                try:
                    import httpx
                    base_url = (self.client.base_url if hasattr(self.client, "base_url") else None) or ""
                    base_url = str(base_url).rstrip("/")
                    url = f"{base_url}/chat/completions" if base_url else ""
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}",
                        "API-KEY": self.api_key,
                    }
                    payload = {
                        "model": self.model,
                        "messages": messages,
                    }
                    if "temperature" in request_params:
                        payload["temperature"] = request_params["temperature"]
                    if "max_completion_tokens" in request_params:
                        payload["max_completion_tokens"] = request_params["max_completion_tokens"]
                    if "max_tokens" in request_params:
                        payload["max_tokens"] = request_params["max_tokens"]
                    raw_resp = httpx.post(url, headers=headers, json=payload, timeout=60.0)
                    raw_json = raw_resp.json()
                    content = raw_json.get("choices", [{}])[0].get("message", {}).get("content", "") or ""
                except Exception as e:
                    logger.warning(f"OpenAI raw HTTP fallback failed: {e}")
            
            logger.info(
                f"OpenAI API call successful: execution_time={execution_time:.2f}s, "
                f"response_length={len(content)}"
            )
            
            return ExecutionResult(
                success=True,
                stdout=content,
                stderr="",
                error_message=None,
                execution_time=execution_time
            )
            
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                error_message=f"OpenAI API error: {e}",
                execution_time=0
            )
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI API execution: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                error_message=f"Unexpected error: {e}",
                execution_time=0
            )
