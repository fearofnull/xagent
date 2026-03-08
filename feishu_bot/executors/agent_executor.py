# -*- coding: utf-8 -*-
"""Agent API 执行器

集成 AgentScope ReActAgent 的执行器
"""
import os
import logging
from typing import Optional, List, Dict, Any

from feishu_bot.executors.ai_api_executor import AIAPIExecutor
from feishu_bot.models import ExecutionResult, Message
from feishu_bot.agents.react_agent import XAgent
from feishu_bot.agents.memory import MemoryManager
from feishu_bot.config import BotConfig

logger = logging.getLogger(__name__)


class AgentExecutor(AIAPIExecutor):
    """支持 Agent 能力的执行器"""
    
    def __init__(
        self,
        timeout: int = 60,
        allowed_paths: Optional[List[str]] = None,
        search_api_key: Optional[str] = None,
        allowed_commands: Optional[List[str]] = None,
        provider_config_manager: Optional[Any] = None
    ):
        """初始化 Agent 执行器
        
        Args:
            timeout: 超时时间
            allowed_paths: 允许的文件路径
            search_api_key: 搜索 API 密钥
            allowed_commands: 允许的 Shell 命令
            provider_config_manager: 提供商配置管理器
        """
        # 从提供商配置中获取配置
        provider_api_key = ""
        provider_model = "gpt-4o"
        provider_base_url = None
        provider_type = "openai"
        
        if provider_config_manager:
            default_config = provider_config_manager.get_default()
            if default_config:
                provider_api_key = default_config.api_key
                provider_model = default_config.default_model
                provider_type = default_config.type
                provider_base_url = default_config.base_url
        
        # 处理提供商类型
        normalized_provider_type = "openai"
        if provider_type == "openai_compatible":
            normalized_provider_type = "openai"
        elif provider_type == "claude_compatible":
            normalized_provider_type = "claude"
        elif provider_type == "gemini_compatible":
            normalized_provider_type = "gemini"
        
        super().__init__(provider_api_key, provider_model, timeout)
        
        # 设置环境变量
        if provider_api_key:
            if normalized_provider_type == "openai":
                os.environ["OPENAI_API_KEY"] = provider_api_key
                if provider_model:
                    os.environ["OPENAI_MODEL"] = provider_model
                if provider_base_url:
                    os.environ["OPENAI_BASE_URL"] = provider_base_url
            elif normalized_provider_type == "claude":
                os.environ["ANTHROPIC_API_KEY"] = provider_api_key
                if provider_model:
                    os.environ["ANTHROPIC_MODEL"] = provider_model
                if provider_base_url:
                    os.environ["ANTHROPIC_BASE_URL"] = provider_base_url
            elif normalized_provider_type == "gemini":
                os.environ["GEMINI_API_KEY"] = provider_api_key
                if provider_model:
                    os.environ["GEMINI_MODEL"] = provider_model
                if provider_base_url:
                    os.environ["GEMINI_BASE_URL"] = provider_base_url
        if search_api_key:
            os.environ["SERPER_API_KEY"] = search_api_key
        
        # 保存提供商类型
        self.provider_type = normalized_provider_type
        
        # 尝试初始化记忆管理器
        try:
            from agentscope.token import HuggingFaceTokenCounter
            from agentscope.tool import Toolkit
            from feishu_bot.agents.memory import MemoryManager
            from feishu_bot.constant import WORKING_DIR, MEMORY_COMPACT_RATIO
            
            # 创建必要的组件
            token_counter = HuggingFaceTokenCounter(pretrained_model_name_or_path="gpt2")
            toolkit = Toolkit()
            
            # 初始化模型和格式化器
            from feishu_bot.agents.model_factory import create_model_and_formatter
            model, formatter = create_model_and_formatter(provider_type=self.provider_type)
            
            # 初始化记忆管理器
            self.memory_manager = MemoryManager(
                working_dir=str(WORKING_DIR),
                chat_model=model,
                formatter=formatter,
                token_counter=token_counter,
                toolkit=toolkit,
                max_input_length=128 * 1024,  # 128K tokens
                memory_compact_ratio=MEMORY_COMPACT_RATIO
            )
            
            # 初始化 XAgent
            self.agent = XAgent(
                memory_manager=self.memory_manager,
                max_iters=50,
                provider_type=self.provider_type
            )
        except ImportError:
            logger.warning("reme package not installed, using XAgent without memory manager")
            # 没有 reme 包时，不使用记忆管理器
            self.memory_manager = None
            self.agent = XAgent(
                max_iters=50,
                provider_type=self.provider_type
            )
    
    def execute(
        self,
        user_prompt: str,
        conversation_history: Optional[List[Message]] = None,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """执行 Agent
        
        Args:
            user_prompt: 用户提示
            conversation_history: 对话历史
            additional_params: 额外参数
            
        Returns:
            ExecutionResult: 执行结果
        """
        import asyncio
        from agentscope.message import Msg
        
        try:
            # 转换对话历史为 AgentScope 消息格式
            messages = []
            if conversation_history:
                for msg in conversation_history:
                    if msg.role == "user":
                        messages.append(Msg(
                            name="User",
                            role="user",
                            content=msg.content
                        ))
                    elif msg.role == "assistant":
                        messages.append(Msg(
                            name="Assistant",
                            role="assistant",
                            content=msg.content
                        ))
            
            # 添加当前用户消息
            messages.append(Msg(
                name="User",
                role="user",
                content=user_prompt
            ))
            
            # 运行异步 Agent
            try:
                # 检查是否已经有运行中的事件循环
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果事件循环已经在运行，使用 create_task 并等待完成
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        # 在新线程中运行 asyncio.run
                        result = executor.submit(asyncio.run, self.agent.reply(messages)).result()
                else:
                    # 如果没有运行中的事件循环，使用 asyncio.run
                    result = asyncio.run(self.agent.reply(messages))
            except Exception as e:
                # 如果出现任何错误，尝试在新线程中运行
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    result = executor.submit(asyncio.run, self.agent.reply(messages)).result()
            
            # 提取回复内容
            if hasattr(result, "content"):
                if isinstance(result.content, str):
                    output = result.content
                elif isinstance(result.content, list):
                    # 处理content是列表的情况，提取文本内容
                    text_parts = []
                    for item in result.content:
                        if isinstance(item, dict) and item.get("type") == "text" and "text" in item:
                            text_parts.append(item["text"])
                        elif hasattr(item, "text"):
                            text_parts.append(str(item.text))
                    output = "".join(text_parts) if text_parts else str(result.content)
                else:
                    output = str(result.content)
            else:
                output = str(result)
            
            return ExecutionResult(
                success=True,
                stdout=output,
                stderr="",
                error_message=None,
                execution_time=0.0
            )
            
        except Exception as e:
            logger.error(f"Agent 执行失败: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                error_message=f"Agent 执行失败: {str(e)}",
                execution_time=0.0
            )
    
    def get_provider_name(self) -> str:
        """获取提供商名称
        
        Returns:
            str: 提供商名称
        """
        return "agent"
    
    def format_messages(
        self,
        user_prompt: str,
        conversation_history: Optional[List[Message]] = None
    ) -> List[Dict[str, str]]:
        """格式化消息（Agent 内部处理）
        
        Args:
            user_prompt: 用户提示
            conversation_history: 对话历史
            
        Returns:
            List[Dict]: 格式化的消息
        """
        return []
    
    def reset(self) -> None:
        """重置 Agent 状态"""
        logger.info("Agent 状态已重置")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计信息

        Returns:
            Dict: 统计信息
        """
        if self.memory_manager:
            return self.memory_manager.get_memory_stats()
        else:
            return {"error": "Memory manager not available"}

    def is_available(self) -> bool:
        """检查执行器是否可用

        Returns:
            bool: 如果执行器可用返回 True
        """
        # 检查与当前提供商类型对应的 API 密钥是否配置
        if self.provider_type == "openai":
            return bool(os.getenv("OPENAI_API_KEY"))
        elif self.provider_type == "claude":
            return bool(os.getenv("ANTHROPIC_API_KEY"))
        elif self.provider_type == "gemini":
            return bool(os.getenv("GEMINI_API_KEY"))
        else:
            return False