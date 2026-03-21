# -*- coding: utf-8 -*-
"""Agent API 执行器

集成 AgentScope ReActAgent 的执行器
"""
import os
import logging
from typing import Optional, List, Dict, Any

from .ai_api_executor import AIAPIExecutor
from ..models import ExecutionResult, Message
from ..agents.react_agent import XAgent
from ..agents.memory import MemoryManager
from ..config import BotConfig

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
        provider_model = ""  # 不硬编码默认模型，让 model_factory 根据提供商类型决定
        provider_base_url = None
        provider_type = ""  # 不硬编码默认类型
        
        if provider_config_manager:
            default_config = provider_config_manager.get_default()
            if default_config:
                provider_api_key = default_config.api_key
                provider_model = default_config.default_model
                provider_type = default_config.type
                provider_base_url = default_config.base_url
        
        # 规范化提供商类型
        # 支持 xxx_compatible 格式和直接的 xxx 格式
        normalized_provider_type = self._normalize_provider_type(provider_type)
        
        super().__init__(provider_api_key, provider_model, timeout)
        
        # 设置环境变量（用于 model_factory）
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
            from ..agents.memory import MemoryManager
            from ..constant import WORKING_DIR, MEMORY_COMPACT_RATIO
            
            # 创建必要的组件
            token_counter = HuggingFaceTokenCounter(pretrained_model_name_or_path="gpt2")
            toolkit = Toolkit()
            
            # 初始化模型和格式化器
            from ..agents.model_factory import create_model_and_formatter
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
        
        # 从 additional_params 中提取上下文信息并设置环境变量
        if additional_params:
            chat_id = additional_params.get('chat_id')
            chat_type = additional_params.get('chat_type')
            user_id = additional_params.get('user_id')
            if chat_id:
                import os as _os
                _os.environ['CURRENT_CHAT_ID'] = chat_id
            if chat_type:
                import os as _os
                _os.environ['CURRENT_CHAT_TYPE'] = chat_type
            if user_id:
                import os as _os
                _os.environ['CURRENT_USER_ID'] = user_id
        
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
            logger.info(f"[execute] 准备调用 agent.reply，agent 类型: {type(self.agent)}")
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
                # 如果出现任何错误，不再重复调用agent.reply，避免重复回答
                logger.error(f"Error executing agent.reply: {e}")
                # 直接返回错误结果
                return ExecutionResult(
                    success=False,
                    stdout="",
                    stderr=str(e),
                    error_message=f"Agent执行失败: {str(e)}",
                    execution_time=0
                )
            
            logger.info(f"[execute] agent.reply 返回，result 类型: {type(result)}, result.content: {result.content}")
            
            # 提取回复内容
            text_parts = []
            media_blocks = []
            
            # 检查 content 字段
            if hasattr(result, "content"):
                if isinstance(result.content, str):
                    text_parts.append(result.content)
                elif isinstance(result.content, list):
                    # 处理content是列表的情况，提取文本内容和媒体内容
                    for item in result.content:
                        if isinstance(item, dict):
                            # 处理 tool_result 结构
                            if item.get("type") == "tool_result" and "output" in item:
                                logger.info(f"检测到 tool_result: {item}")
                                tool_output = item.get("output")
                                if isinstance(tool_output, list):
                                    for tool_item in tool_output:
                                        if isinstance(tool_item, dict):
                                            if tool_item.get("type") == "text" and "text" in tool_item:
                                                text_parts.append(tool_item["text"])
                                            elif tool_item.get("type") in ["image", "audio", "video", "file"] and "source" in tool_item:
                                                media_blocks.append(tool_item)
                                # 检查 tool_output 是否直接是一个对象（而不是列表）
                                elif isinstance(tool_output, dict):
                                    if tool_output.get("type") == "text" and "text" in tool_output:
                                        text_parts.append(tool_output["text"])
                                    elif tool_output.get("type") in ["image", "audio", "video", "file"] and "source" in tool_output:
                                        media_blocks.append(tool_output)
                            elif item.get("type") == "text" and "text" in item:
                                text_parts.append(item["text"])
                            elif item.get("type") in ["image", "audio", "video", "file"]:
                                # 媒体块可能是 dict 或对象
                                media_blocks.append(item)
                                logger.info(f"检测到媒体块(dict): {item.get('type')}")
                        elif hasattr(item, "type"):
                            # 注意：ImageBlock 和 TextBlock 实际上是 TypedDict，创建后是 dict 对象
                            # 这里处理的是真正的对象类型（如果有的话）
                            item_type = getattr(item, "type", None)
                            if item_type == "text" and hasattr(item, "text"):
                                text_parts.append(str(item.text))
                            elif item_type in ["image", "audio", "video", "file"]:
                                # 将对象转换为 dict
                                if hasattr(item, "source"):
                                    source = getattr(item, "source", {})
                                    if isinstance(source, dict):
                                        media_blocks.append({
                                            "type": item_type,
                                            "source": source
                                        })
                                        logger.info(f"检测到媒体块(对象): {item_type}")
                                    else:
                                        # 处理 source 是对象的情况
                                        media_blocks.append({
                                            "type": item_type,
                                            "source": {
                                                "type": getattr(source, "type", "url"),
                                                "url": getattr(source, "url", "")
                                            }
                                        })
                                        logger.info(f"检测到媒体块(对象source): {item_type}")
                else:
                    text_parts.append(str(result.content))
            
            # 不再从 system 字段提取文本内容，避免重复回答
            # 因为工具结果已经通过 _merge_tool_results_to_reply 合并到了 content 中
            
            # 生成输出文本
            # 如果有文本部分，拼接它们；如果没有文本但有媒体块，使用空字符串；否则尝试从 result 获取内容
            if text_parts:
                output = "".join(text_parts)
            elif media_blocks:
                # 有媒体块时不需要额外文本
                output = ""
            elif hasattr(result, 'content') and isinstance(result.content, str) and result.content:
                output = result.content
            else:
                # 最后的回退：不输出 Msg 对象的字符串表示
                output = ""
            
            # 处理媒体块，发送图片或文件
            logger.info(f"检测到媒体块数量: {len(media_blocks)}")
            if media_blocks:
                logger.info(f"媒体块内容: {media_blocks}")
                try:
                    from src.xagent.core.message_sender import MessageSender
                    from lark_oapi import Client as LarkClient
                    import os
                    
                    # 加载环境变量
                    def load_env():
                        env_path = os.path.join(os.path.dirname(__file__), '../../..', '.env')
                        config = {}
                        if os.path.exists(env_path):
                            with open(env_path, 'r', encoding='utf-8') as f:
                                for line in f:
                                    line = line.strip()
                                    if line and not line.startswith('#'):
                                        key, value = line.split('=', 1)
                                        config[key.strip()] = value.strip()
                        return config
                    
                    config = load_env()
                    app_id = config.get('FEISHU_APP_ID')
                    app_secret = config.get('FEISHU_APP_SECRET')
                    chat_id = config.get('FEISHU_CHAT_ID')
                    
                    logger.info(f"环境变量加载结果: app_id={app_id is not None}, app_secret={app_secret is not None}, chat_id={chat_id is not None}")
                    
                    if app_id and app_secret and chat_id:
                        client = LarkClient.builder().app_id(app_id).app_secret(app_secret).build()
                        message_sender = MessageSender(client)
                        
                        for media_block in media_blocks:
                            media_type = media_block.get("type") if isinstance(media_block, dict) else getattr(media_block, "type")
                            source = media_block.get("source") if isinstance(media_block, dict) else getattr(media_block, "source")
                            
                            logger.info(f"处理媒体块: type={media_type}, source={source}")
                            
                            if source:
                                media_url = source.get("url") if isinstance(source, dict) else getattr(source, "url")
                                logger.info(f"媒体URL: {media_url}")
                                
                                # 处理文件路径
                                file_path = None
                                if media_url:
                                    if media_url.startswith("file://"):
                                        # 从 file:// URL 提取文件路径
                                        file_path = media_url.replace("file://", "")
                                        # 处理 Windows 路径中的双反斜杠
                                        file_path = file_path.replace("\\\\", "\\")
                                        logger.info(f"从 file:// URL 提取文件路径: {file_path}")
                                    else:
                                        # 直接使用路径
                                        file_path = media_url
                                        logger.info(f"直接使用文件路径: {file_path}")
                                else:
                                    # 尝试直接获取 source 作为路径
                                    file_path = source if isinstance(source, str) else str(source)
                                    logger.info(f"尝试使用 source 作为文件路径: {file_path}")
                                
                                if file_path and os.path.exists(file_path):
                                    logger.info(f"文件存在，发送 {media_type} 消息")
                                    if media_type == "image":
                                        success = message_sender.send_message(
                                            chat_type="p2p",
                                            chat_id=chat_id,
                                            message_id="",
                                            content=file_path,
                                            msg_type="image"
                                        )
                                        logger.info(f"图片消息发送结果: {success}")
                                    elif media_type == "file":
                                        success = message_sender.send_message(
                                            chat_type="p2p",
                                            chat_id=chat_id,
                                            message_id="",
                                            content=file_path,
                                            msg_type="file"
                                        )
                                        logger.info(f"文件消息发送结果: {success}")
                                else:
                                    logger.error(f"文件不存在或路径无效: {file_path}")
                            else:
                                logger.error("媒体块缺少source")
                    else:
                        logger.error("缺少必要的环境变量")
                except Exception as e:
                    logger.error(f"发送媒体文件失败: {e}", exc_info=True)
            else:
                logger.info("没有检测到媒体块")
            
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

    @staticmethod
    def _normalize_provider_type(provider_type: str) -> str:
        """规范化提供商类型
        
        将各种格式的提供商类型转换为标准格式（openai, claude, gemini）
        
        Args:
            provider_type: 原始提供商类型，支持:
                - openai, openai_compatible
                - claude, claude_compatible
                - gemini, gemini_compatible
                
        Returns:
            规范化后的提供商类型（openai, claude, gemini）
            如果无法识别，默认返回 openai
        """
        if not provider_type:
            return "openai"
        
        provider_type_lower = provider_type.lower().strip()
        
        # 映射表
        type_mapping = {
            "openai": "openai",
            "openai_compatible": "openai",
            "claude": "claude",
            "claude_compatible": "claude",
            "anthropic": "claude",
            "anthropic_compatible": "claude",
            "gemini": "gemini",
            "gemini_compatible": "gemini",
            "google": "gemini",
            "google_compatible": "gemini",
        }
        
        return type_mapping.get(provider_type_lower, "openai")

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