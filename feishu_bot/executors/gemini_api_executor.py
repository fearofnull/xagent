"""
Gemini API 执行器实现

调用 Gemini API 执行 AI 任务。
支持对话历史上下文和可选参数配置。

参考文档: https://ai.google.dev/docs
"""
import time
import logging
import warnings
from typing import Optional, List, Dict, Any

# 忽略弃用警告
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")
import google.generativeai as genai
from feishu_bot.executors.ai_api_executor import AIAPIExecutor
from feishu_bot.models import ExecutionResult, Message

logger = logging.getLogger(__name__)


class GeminiAPIExecutor(AIAPIExecutor):
    """Gemini API 执行器
    
    使用 Google Generative AI Python SDK 调用 Gemini API。
    支持多轮对话上下文和灵活的参数配置。
    """
    
    def __init__(
        self, 
        api_key: str,
        model: str = "gemini-1.5-pro-latest",
        timeout: int = 60,
        base_url: Optional[str] = None
    ):
        """初始化 Gemini API 执行器
        
        Args:
            api_key: Google API 密钥
            model: Gemini 模型名称，默认使用 gemini-1.5-pro-latest
            timeout: 请求超时时间（秒）
            base_url: API 基础 URL（可选，用于兼容 Gemini 的 API）
        """
        super().__init__(api_key, model, timeout)
        genai.configure(api_key=api_key)
        if base_url:
            genai.configure(base_url=base_url)
        self.model = genai.GenerativeModel(model)
    
    def get_provider_name(self) -> str:
        """返回 AI 提供商名称
        
        Returns:
            "gemini-api"
        """
        return "gemini-api"
    
    def format_messages(
        self, 
        user_prompt: str,
        conversation_history: Optional[List[Message]] = None
    ) -> List[Dict[str, str]]:
        """格式化为 Gemini API 消息格式
        
        Gemini API 使用 "user" 和 "model" 角色。
        
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
                role = "user" if msg.role == "user" else "model"
                messages.append({
                    "role": role,
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
        """调用 Gemini API 执行任务
        
        Args:
            user_prompt: 用户提示
            conversation_history: 对话历史（用于上下文）
            additional_params: 额外参数，支持：
                - temperature: 温度参数（0-2）
                - max_output_tokens: 最大输出 token 数
                
        Returns:
            ExecutionResult: 包含执行结果的对象
        """
        try:
            logger.info(f"Executing Gemini API call with model={self.model.model_name}")
            messages = self.format_messages(user_prompt, conversation_history)
            
            # 构建请求参数
            request_params = {}
            
            # 添加可选参数
            if additional_params:
                if "temperature" in additional_params:
                    request_params["temperature"] = additional_params["temperature"]
                if "max_output_tokens" in additional_params:
                    request_params["max_output_tokens"] = additional_params["max_output_tokens"]
            
            logger.debug(f"Gemini API request params: {request_params.keys()}")
            
            # 调用 API
            start_time = time.time()
            
            # 如果有对话历史，使用 chat 模式
            if conversation_history:
                chat = self.model.start_chat(history=messages[:-1])
                response = chat.send_message(messages[-1]["content"], **request_params)
            else:
                response = self.model.generate_content(user_prompt, **request_params)
            
            execution_time = time.time() - start_time
            
            # 提取响应内容
            content = response.text
            
            logger.info(
                f"Gemini API call successful: execution_time={execution_time:.2f}s, "
                f"response_length={len(content)}"
            )
            
            return ExecutionResult(
                success=True,
                stdout=content,
                stderr="",
                error_message=None,
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                error_message=f"Gemini API error: {e}",
                execution_time=0
            )
