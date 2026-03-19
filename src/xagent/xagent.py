"""
飞书 AI 机器人主应用类
"""
import asyncio
import logging
import json
import threading
import os
from typing import Optional
from lark_oapi import Client as LarkClient
from lark_oapi.api.im.v1 import P2ImMessageReceiveV1

from .config import BotConfig
from .utils.cache import DeduplicationCache
from .core.message_handler import MessageHandler
from .core.session_manager import SessionManager
from .core.config_manager import ConfigManager
from .utils.command_parser import CommandParser
from .core.executor_registry import ExecutorRegistry
from .core.smart_router import SmartRouter
from .utils.response_formatter import ResponseFormatter
from .core.message_sender import MessageSender
from .core.event_handler import EventHandler
from .core.websocket_client import WebSocketClient

# API Executors
from .executors.openai_api_executor import OpenAIAPIExecutor
from .executors.claude_api_executor import ClaudeAPIExecutor
from .executors.gemini_api_executor import GeminiAPIExecutor
from .executors.agent_executor import AgentExecutor

# CLI Executors
from .executors.claude_cli_executor import ClaudeCodeCLIExecutor
from .executors.gemini_cli_executor import GeminiCLIExecutor
from .executors.qwen_cli_executor import QwenCLIExecutor

from .models import ExecutorMetadata

logger = logging.getLogger(__name__)


class XAgent:
    """XAgent主应用类"""
    
    def __init__(self, config: BotConfig):
        """初始化XAgent
        
        Args:
            config: 机器人配置
        """
        self.config = config
        
        # 初始化飞书客户端
        self.client = LarkClient.builder() \
            .app_id(config.app_id) \
            .app_secret(config.app_secret) \
            .build()
        
        # 初始化核心组件
        self.dedup_cache = DeduplicationCache(max_size=config.cache_size)
        self.message_handler = MessageHandler(self.client, self.dedup_cache)
        self.session_manager = SessionManager(
            storage_path=config.session_storage_path,
            max_messages=config.max_session_messages,
            session_timeout=config.session_timeout
        )
        self.config_manager = ConfigManager(
            storage_path="./data/session_configs.json",
            global_config=config
        )
        self.command_parser = CommandParser()
        self.executor_registry = ExecutorRegistry()
        self.response_formatter = ResponseFormatter()
        self.message_sender = MessageSender(self.client)
        
        # 机器人的 open_id，用于检测是否被@
        self.bot_open_id = None
        
        # 初始化提供商配置管理器
        from .core.provider_config_manager import ProviderConfigManager
        self.provider_config_manager = ProviderConfigManager(
            storage_path="./data/provider_configs.json"
        )
        
        # 初始化并注册执行器
        self._register_executors()
        
        # 初始化统一API接口
        from .core.unified_api import UnifiedAPIInterface
        self.unified_api_interface = UnifiedAPIInterface(
            config_manager=self.provider_config_manager,
            executor_registry=self.executor_registry,
            enable_fallback=False  # 可以通过配置启用
        )
        
        # 初始化智能路由器
        self.smart_router = SmartRouter(
            executor_registry=self.executor_registry,
            unified_api_interface=self.unified_api_interface,
            bot_config=self.config
        )
        
        # 初始化事件处理器和 WebSocket 客户端
        self.event_handler = EventHandler()
        self.event_handler.register_message_receive_handler(
            self._handle_message_receive
        )
        
        self.ws_client = WebSocketClient(
            app_id=config.app_id,
            app_secret=config.app_secret,
            event_handler=self.event_handler
        )
        
        logger.info("XAgent initialized successfully")
    
    def _register_executors(self) -> None:
        """注册所有 AI 执行器"""
        # 注册 Claude Code CLI 执行器
        claude_cli_dir = self.config.claude_cli_target_dir or self.config.target_directory
        if claude_cli_dir:
            try:
                claude_cli = ClaudeCodeCLIExecutor(
                    target_dir=claude_cli_dir,
                    timeout=self.config.ai_timeout,
                    use_native_session=True,
                    session_storage_path=self.config.session_storage_path
                )
                claude_cli_metadata = ExecutorMetadata(
                    name="Claude Code CLI",
                    provider="claude",
                    layer="cli",
                    version="1.0.0",
                    description="Claude Code CLI for code analysis and operations",
                    capabilities=["code_analysis", "file_operations", "command_execution"],
                    command_prefixes=["@claude-cli", "@code"],
                    priority=1,
                    config_required=["target_directory"]
                )
                self.executor_registry.register_cli_executor(
                    "claude", claude_cli, claude_cli_metadata
                )
                logger.info(f"Registered Claude Code CLI executor (target: {claude_cli_dir})")
            except Exception as e:
                logger.warning(f"Failed to register Claude Code CLI executor: {e}")
        
        # 注册 Gemini CLI 执行器
        gemini_cli_dir = self.config.gemini_cli_target_dir or self.config.target_directory
        if gemini_cli_dir:
            try:
                gemini_cli = GeminiCLIExecutor(
                    target_dir=gemini_cli_dir,
                    timeout=self.config.ai_timeout,
                    use_native_session=True,
                    session_storage_path=self.config.session_storage_path
                )
                gemini_cli_metadata = ExecutorMetadata(
                    name="Gemini CLI",
                    provider="gemini",
                    layer="cli",
                    version="1.0.0",
                    description="Gemini CLI for code analysis and operations",
                    capabilities=["code_analysis", "file_operations", "command_execution"],
                    command_prefixes=["@gemini-cli"],
                    priority=2,
                    config_required=["target_directory"]
                )
                self.executor_registry.register_cli_executor(
                    "gemini", gemini_cli, gemini_cli_metadata
                )
                logger.info(f"Registered Gemini CLI executor (target: {gemini_cli_dir})")
            except Exception as e:
                logger.warning(f"Failed to register Gemini CLI executor: {e}")
        
        # 注册 Qwen Code CLI 执行器
        qwen_cli_dir = self.config.qwen_cli_target_dir or self.config.target_directory
        if qwen_cli_dir:
            try:
                qwen_cli = QwenCLIExecutor(
                    target_dir=qwen_cli_dir,
                    timeout=self.config.ai_timeout,
                    use_native_session=True,
                    session_storage_path=self.config.session_storage_path
                )
                qwen_cli_metadata = ExecutorMetadata(
                    name="Qwen Code CLI",
                    provider="qwen",
                    layer="cli",
                    version="1.0.0",
                    description="Qwen Code CLI for code analysis and operations",
                    capabilities=["code_analysis", "file_operations", "command_execution"],
                    command_prefixes=["@qwen-cli"],
                    priority=3,
                    config_required=["target_directory"]
                )
                self.executor_registry.register_cli_executor(
                    "qwen", qwen_cli, qwen_cli_metadata
                )
                logger.info(f"Registered Qwen Code CLI executor (target: {qwen_cli_dir})")
            except Exception as e:
                logger.warning(f"Failed to register Qwen Code CLI executor: {e}")
        
        # 注册 OpenAI API 执行器
        try:
            openai_api_key = os.environ.get("OPENAI_API_KEY")
            if openai_api_key:
                openai_executor = OpenAIAPIExecutor(
                    api_key=openai_api_key,
                    timeout=self.config.ai_timeout
                )
                openai_metadata = ExecutorMetadata(
                    name="OpenAI API",
                    provider="openai",
                    layer="api",
                    version="1.0.0",
                    description="OpenAI API for text generation",
                    capabilities=["text_generation"],
                    command_prefixes=["@openai-api"],
                    priority=1,
                    config_required=["openai_api_key"]
                )
                self.executor_registry.register_api_executor(
                    "openai", openai_executor, openai_metadata
                )
                logger.info("Registered OpenAI API executor")
        except Exception as e:
            logger.warning(f"Failed to register OpenAI API executor: {e}")
        
        # 注册 Claude API 执行器
        try:
            claude_api_key = os.environ.get("ANTHROPIC_API_KEY")
            if claude_api_key:
                claude_executor = ClaudeAPIExecutor(
                    api_key=claude_api_key,
                    timeout=self.config.ai_timeout
                )
                claude_metadata = ExecutorMetadata(
                    name="Claude API",
                    provider="claude",
                    layer="api",
                    version="1.0.0",
                    description="Claude API for text generation",
                    capabilities=["text_generation"],
                    command_prefixes=["@claude-api"],
                    priority=2,
                    config_required=["anthropic_api_key"]
                )
                self.executor_registry.register_api_executor(
                    "claude", claude_executor, claude_metadata
                )
                logger.info("Registered Claude API executor")
        except Exception as e:
            logger.warning(f"Failed to register Claude API executor: {e}")
        
        # 注册 Gemini API 执行器
        try:
            gemini_api_key = os.environ.get("GEMINI_API_KEY")
            if gemini_api_key:
                gemini_executor = GeminiAPIExecutor(
                    api_key=gemini_api_key,
                    timeout=self.config.ai_timeout
                )
                gemini_metadata = ExecutorMetadata(
                    name="Gemini API",
                    provider="gemini",
                    layer="api",
                    version="1.0.0",
                    description="Gemini API for text generation",
                    capabilities=["text_generation"],
                    command_prefixes=["@gemini-api"],
                    priority=3,
                    config_required=["gemini_api_key"]
                )
                self.executor_registry.register_api_executor(
                    "gemini", gemini_executor, gemini_metadata
                )
                logger.info("Registered Gemini API executor")
        except Exception as e:
            logger.warning(f"Failed to register Gemini API executor: {e}")
        
        # 注册 Agent 执行器
        try:
            search_api_key = os.environ.get("SERPER_API_KEY")
            agent_executor = AgentExecutor(
                timeout=self.config.ai_timeout,
                search_api_key=search_api_key,
                provider_config_manager=self.provider_config_manager
            )
            agent_metadata = ExecutorMetadata(
                name="Agent",
                provider="agent",
                layer="agent",
                version="1.0.0",
                description="Agent with tool calling capabilities",
                capabilities=["tool_calling", "multi_step_reasoning", "file_operations", "web_search", "shell_commands"],
                command_prefixes=["@agent"],
                priority=0,
                config_required=["openai_api_key"]
            )
            self.executor_registry.register_agent_executor(
                "agent", agent_executor, agent_metadata
            )
            logger.info("Registered Agent executor")
        except Exception as e:
            logger.warning(f"Failed to register Agent executor: {e}")
    
    def _handle_message_receive(self, data: P2ImMessageReceiveV1) -> None:
        """处理接收到的消息
        
        Args:
            data: 飞书消息接收事件
        """
        try:
            message_id = data.event.message.message_id
            chat_id = data.event.message.chat_id
            chat_type = data.event.message.chat_type
            
            # 安全获取sender_id，处理可能为None的情况
            sender_id = None
            try:
                if hasattr(data.event, 'sender') and hasattr(data.event.sender, 'sender_id'):
                    sender_id = data.event.sender.sender_id.user_id
            except Exception as e:
                logger.warning(f"Failed to get sender_id: {e}")
            
            logger.info(f"Received message {message_id} from user {sender_id}")
            
            # 1. 消息去重
            if self.dedup_cache.is_processed(message_id):
                logger.info(f"Message {message_id} already processed, skipping")
                return
            
            self.dedup_cache.mark_processed(message_id)
            
            # 2. 群聊@检测：如果是群聊且没有@机器人，则忽略消息
            if chat_type == "group":
                # 检查消息中是否包含@机器人的mentions
                is_mentioned = self._is_bot_mentioned(data.event.message)
                if not is_mentioned:
                    logger.info(f"Message {message_id} in group chat does not mention bot, skipping")
                    return
            
            # 3. 发送emoji反应（在线程中异步执行，不阻塞后续消息处理）
            threading.Thread(
                target=self._send_emoji_in_thread,
                args=(message_id,),
                daemon=True
            ).start()
            
            # 3. 消息解析
            # 调试：打印消息类型和所有属性
            logger.info(f"Message type: {data.event.message.message_type}")
            logger.info(f"Message attributes: {dir(data.event.message)}")
            if hasattr(data.event.message, 'parent_id'):
                logger.info(f"Parent ID: {data.event.message.parent_id}")
            else:
                logger.warning("parent_id attribute not found in message")
            
            message_content = self.message_handler.parse_message_content(
                data.event.message
            )
            
            if message_content.startswith("解析消息失败") or message_content.startswith("parse message failed"):
                # 非文本消息，直接返回错误
                self.message_sender.send_message(
                    chat_type, chat_id, message_id, message_content
                )
                return
            
            # 4. 命令解析（在组合引用消息之前，从当前消息中提取命令前缀和临时参数）
            parsed_command, temp_params = self.command_parser.parse_command(message_content)
            
            # 处理引用消息（使用解析后的消息内容）
            final_message = parsed_command.message
            if hasattr(data.event.message, 'parent_id') and data.event.message.parent_id:
                logger.info(f"Detected parent_id: {data.event.message.parent_id}")
                quoted_content = self.message_handler.get_quoted_message(
                    data.event.message.parent_id
                )
                logger.info(f"Quoted content retrieved: {quoted_content[:100] if quoted_content else 'None'}")
                if quoted_content:
                    # 组合引用消息和当前消息（使用去除前缀后的消息）
                    final_message = self.message_handler.combine_messages(
                        quoted_content, parsed_command.message
                    )
                    logger.info(f"Combined message with quoted content, length={len(final_message)}")
                else:
                    logger.warning("Quoted content is None, not combining messages")
            else:
                logger.info("No parent_id found, not processing quoted message")
            
            # 更新 parsed_command 的 message 为最终消息（包含引用内容）
            from .models import ParsedCommand
            parsed_command = ParsedCommand(
                provider=parsed_command.provider,
                execution_layer=parsed_command.execution_layer,
                message=final_message,
                explicit=parsed_command.explicit
            )
            logger.info(f"[DEBUG] parsed_command.message after update: {parsed_command.message[:300]}")
            logger.info(f"Final message to be sent to executor (first 200 chars): {final_message[:200]}")
            
            # 5. 确定会话 ID - 统一使用 chat_id (私聊和群聊都一样)
            # 优势:
            # 1. chat_id 总是可以获取,不依赖权限
            # 2. 飞书 P2P chat_id 是唯一且固定的,跨设备一致
            # 3. 逻辑简单,不需要 fallback
            session_id = chat_id
            session_type = "user" if chat_type == "p2p" else "group"
            
            logger.info(f"Session: session_id={session_id}, session_type={session_type}")
            
            # 6. 配置命令检查
            if self._handle_config_command(
                session_id, session_type, sender_id, parsed_command.message, 
                chat_type, chat_id, message_id
            ):
                return
            
            # 7. 会话命令检查
            if self._handle_session_command(
                sender_id, parsed_command.message, chat_type, chat_id, message_id
            ):
                return
            
            # 8. 获取有效配置（应用临时参数）
            effective_config = self.config_manager.get_effective_config(
                session_id, session_type, temp_params
            )
            
            # 9. 智能路由
            try:
                executor = self.smart_router.route(parsed_command)
            except Exception as e:
                error_msg = f"路由失败：{str(e)}"
                logger.error(error_msg)
                response = self.response_formatter.format_error(
                    message_content, error_msg
                )
                self.message_sender.send_message(
                    chat_type, chat_id, message_id, response
                )
                return
            
            # 10. AI 执行
            try:
                # 获取对话历史
                conversation_history = self.session_manager.get_conversation_history(
                    sender_id
                )
                
                # 获取执行器元数据
                provider_name = executor.get_provider_name()  # e.g., "openai-api", "claude-cli", "unified-api"
                
                # 特殊处理 unified-api：获取实际的提供商配置信息
                if provider_name == "unified-api":
                    executor_metadata = None
                    # 获取当前提供商配置
                    if hasattr(executor, 'get_current_provider_config'):
                        current_config = executor.get_current_provider_config()
                        if current_config:
                            # 格式：提供商名称 (模型名称)
                            executor_name_override = f"{current_config.name} ({current_config.default_model})"
                        else:
                            executor_name_override = "Unified API (@gpt)"
                    else:
                        executor_name_override = "Unified API (@gpt)"
                else:
                    # 解析 provider 和 layer
                    if "-" in provider_name:
                        parts = provider_name.rsplit("-", 1)  # 从右边分割一次
                        provider = parts[0]  # e.g., "openai", "claude"
                        layer = parts[1]     # e.g., "api", "cli"
                    else:
                        # 兜底：如果没有连字符，假设是 API
                        provider = provider_name
                        layer = "api"
                    
                    executor_metadata = self.executor_registry.get_executor_metadata(provider, layer)
                    executor_name_override = None
                executor_name = executor_name_override or (executor_metadata.name if executor_metadata else None)
                
                # 添加语言指令（使用有效配置中的语言设置）
                message_with_language = self._prepend_language_instruction(
                    parsed_command.message, effective_config["response_language"]
                )
                logger.info(f"[DEBUG] message_with_language after prepend: {message_with_language[:300]}")
                
                # 执行 AI
                if executor.get_provider_name().endswith("-api"):
                    # API 层：传递对话历史
                    logger.debug(f"[API] Executing with message: {message_with_language[:200]}...")
                    result = executor.execute(
                        message_with_language,
                        conversation_history=conversation_history
                    )
                else:
                    # CLI 层：使用原生会话，传递有效的项目目录
                    logger.info(f"[CLI] Executing with message: {message_with_language[:200]}...")
                    logger.info(f"[DEBUG] Full message_with_language length: {len(message_with_language)}")
                    logger.debug(f"[CLI] Message being passed to executor: {parsed_command.message[:200]}...")
                    # 临时更新 CLI 执行器的目标目录
                    if hasattr(executor, 'target_dir') and effective_config["target_project_dir"]:
                        original_target_dir = executor.target_dir
                        executor.target_dir = effective_config["target_project_dir"]
                        
                        result = executor.execute(
                            message_with_language,
                            additional_params={"user_id": sender_id}
                        )
                        
                        # 恢复原始目录
                        executor.target_dir = original_target_dir
                    else:
                        result = executor.execute(
                            message_with_language,
                            additional_params={"user_id": sender_id}
                        )
                
                # 11. 响应格式化
                # 11. 响应格式化
                if result.success:
                    response = self.response_formatter.format_response(
                        message_content, result.stdout, executor_name=executor_name
                    )
                else:
                    response = self.response_formatter.format_error(
                        message_content, result.error_message or result.stderr, executor_name=executor_name
                    )
                
                # 12. 消息发送（仅当有内容时发送）
                # Agent executor 可能已经单独发送了媒体文件，此时 stdout 为空
                if result.stdout or not result.success:
                    self.message_sender.send_message(
                        chat_type, chat_id, message_id, response
                    )
                
                # 13. 会话历史更新
                self.session_manager.add_message(sender_id, "user", parsed_command.message)
                self.session_manager.add_message(
                    sender_id, "assistant", result.stdout if result.success else result.error_message
                )
                
                logger.info(f"Successfully processed message {message_id}")
                
            except Exception as e:
                error_msg = f"AI 执行失败：{str(e)}"
                logger.error(error_msg, exc_info=True)
                response = self.response_formatter.format_error(
                    message_content, error_msg
                )
                self.message_sender.send_message(
                    chat_type, chat_id, message_id, response
                )
        
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            # 尝试发送错误消息给用户
            try:
                error_response = f"处理消息时发生错误：{str(e)}"
                self.message_sender.send_message(
                    data.event.message.chat_type,
                    data.event.message.chat_id,
                    data.event.message.message_id,
                    error_response
                )
            except:
                pass
    
    def _send_emoji_in_thread(self, message_id: str) -> None:
        """在线程中发送emoji反应"""
        try:
            self.message_handler.send_emoji_reaction_sync(message_id)
        except Exception as e:
            logger.warning(f"Failed to send emoji reaction in thread: {e}")
    
    def _is_bot_mentioned(self, message) -> bool:
        """检测消息中是否@了机器人
        
        Args:
            message: 飞书消息对象
            
        Returns:
            True 如果消息中@了当前机器人
        """
        try:
            # 检查 mentions 字段
            if hasattr(message, 'mentions') and message.mentions:
                # mentions 是一个列表，包含所有被@的用户/机器人
                for mention in message.mentions:
                    # 检查是否有 open_id
                    if hasattr(mention, 'id') and hasattr(mention.id, 'open_id'):
                        mention_open_id = mention.id.open_id
                        logger.debug(f"Found mention: {mention_open_id}")
                        
                        # 记录机器人的 open_id（如果还没有记录）
                        if self.bot_open_id is None:
                            self.bot_open_id = mention_open_id
                            logger.info(f"Bot open_id recorded: {self.bot_open_id}")
                        
                        # 检查是否@了当前机器人
                        if mention_open_id == self.bot_open_id:
                            logger.debug(f"Bot mentioned: {mention_open_id}")
                            return True
                
                # 如果没有@当前机器人，返回 False
                return False
            
            # 如果没有 mentions 字段，检查消息内容中是否包含 <at> 标签
            if hasattr(message, 'content'):
                content_str = message.content
                try:
                    content = json.loads(content_str)
                    text = content.get("text", "")
                    # 检查是否包含 <at> 标签
                    if "<at" in text:
                        logger.debug(f"Found <at> tag in message content")
                        # 如果已经记录了机器人的 open_id，检查是否在 <at> 标签中
                        if self.bot_open_id and f"<at id=\"{self.bot_open_id}\"" in text:
                            logger.debug(f"Bot mentioned in text: {self.bot_open_id}")
                            return True
                except:
                    pass
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking bot mention: {e}")
            # 出错时默认返回 False，避免漏掉消息
            return False
    
    def _handle_config_command(
        self,
        session_id: str,
        session_type: str,
        user_id: str,
        message: str,
        chat_type: str,
        chat_id: str,
        message_id: str
    ) -> bool:
        """处理配置命令
        
        Args:
            session_id: 会话 ID（user_id 或 chat_id）
            session_type: 会话类型（"user" 或 "group"）
            user_id: 操作用户 ID
            message: 消息内容
            chat_type: 聊天类型
            chat_id: 聊天 ID
            message_id: 消息 ID
            
        Returns:
            True 如果是配置命令并已处理
        """
        # 检查是否为配置命令
        if not self.config_manager.is_config_command(message):
            return False
        
        # 使用 config_manager 处理命令
        response = self.config_manager.handle_config_command(
            session_id, session_type, user_id, message
        )
        
        # 发送响应
        if response:
            self.message_sender.send_message(
                chat_type, chat_id, message_id, response
            )
            return True
        
        return False
    
    def _handle_session_command(
        self,
        user_id: str,
        message: str,
        chat_type: str,
        chat_id: str,
        message_id: str
    ) -> bool:
        """处理会话命令
        
        Args:
            user_id: 用户 ID
            message: 消息内容
            chat_type: 聊天类型
            chat_id: 聊天 ID
            message_id: 消息 ID
            
        Returns:
            True 如果是会话命令并已处理
        """
        # 检查是否为会话命令
        if not self.session_manager.is_session_command(message):
            return False
        
        # 使用 session_manager 处理命令
        response = self.session_manager.handle_session_command(user_id, message)
        
        # 如果是新会话命令，额外清除 CLI 会话
        message_lower = message.lower().strip()
        if message_lower in [cmd.lower() for cmd in self.session_manager.NEW_SESSION_COMMANDS]:
            for provider in ["claude", "gemini", "qwen"]:
                try:
                    cli_executor = self.executor_registry.get_executor(provider, "cli")
                    if hasattr(cli_executor, 'clear_session'):
                        cli_executor.clear_session(user_id)
                except:
                    pass
        
        # 发送响应
        if response:
            self.message_sender.send_message(
                chat_type, chat_id, message_id, response
            )
            return True
        
        return False
    
    def _prepend_language_instruction(self, message: str, language: Optional[str]) -> str:
        """在消息前添加语言指令
        
        Args:
            message: 原始消息
            language: 语言代码（如 zh-CN, en-US）
            
        Returns:
            添加了语言指令的消息（如果配置了语言）
        """
        if not language:
            return message
        
        # 语言代码到自然语言的映射
        language_map = {
            "zh-CN": "中文（简体）",
            "zh-TW": "中文（繁體）",
            "en-US": "English",
            "en-GB": "English (UK)",
            "ja-JP": "日本語",
            "ko-KR": "한국어",
            "fr-FR": "Français",
            "de-DE": "Deutsch",
            "es-ES": "Español",
            "ru-RU": "Русский",
            "pt-BR": "Português (Brasil)",
            "it-IT": "Italiano",
            "ar-SA": "العربية",
            "hi-IN": "हिन्दी",
        }
        
        language_name = language_map.get(language, language)
        instruction = f"Please respond in {language_name}."
        
        # 使用单行格式，避免 CLI headless 模式的多行问题
        return f"{instruction} {message}"
    
    def start(self) -> None:
        """启动XAgent"""
        logger.info("Starting XAgent...")
        self.ws_client.start()
    
    def stop(self) -> None:
        """停止XAgent"""
        logger.info("Stopping XAgent...")
        self.ws_client.stop()
