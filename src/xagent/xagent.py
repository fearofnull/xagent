"""
飞书 AI 机器人主应用类

重构后的门面类，使用 MessageProcessor、CommandDispatcher、ExecutionCoordinator 和 ErrorHandler
"""
import logging
import os
from typing import Optional
from lark_oapi import Client as LarkClient
from lark_oapi.api.im.v1 import P2ImMessageReceiveV1

from .config import BotConfig
from .utils.cache import DeduplicationCache
from .messaging.message_handler import MessageHandler
from .session.session_manager import SessionManager
from .session.config_manager import ConfigManager
from .utils.command_parser import CommandParser
from .core.executor_registry import ExecutorRegistry
from .core.smart_router import SmartRouter
from .utils.response_formatter import ResponseFormatter
from .messaging.message_sender import MessageSender
from .messaging.event_handler import EventHandler
from .core.websocket_client import WebSocketClient
from .core.provider_config_manager import ProviderConfigManager
from .core.executor_factory import CLIExecutorFactory, AgentExecutorFactory
from .core.unified_config_manager import UnifiedConfigManager

from .messaging.message_processor import MessageProcessor, ProcessedMessage
from .messaging.command_dispatcher import CommandDispatcher
from .core.execution_coordinator import ExecutionCoordinator, ExecutionContext
from .core.error_handler import ErrorHandler

from .models import ExecutorMetadata

logger = logging.getLogger(__name__)


class XAgent:
    """XAgent 主应用类（门面模式）
    
    作为系统的入口点，协调各个组件的工作：
    - MessageProcessor: 消息预处理
    - CommandDispatcher: 命令分发
    - ExecutionCoordinator: 执行协调
    - ErrorHandler: 错误处理
    """
    
    def __init__(self, config: BotConfig):
        """初始化 XAgent
        
        Args:
            config: 机器人配置
        """
        self.config = config

        # 复制 MD 提示词文件到工作目录
        self._copy_md_files_to_working_dir()

        self._init_lark_client()
        self._init_core_components()
        self._init_provider_config()
        self._register_executors()
        self._init_coordinators()
        self._init_event_handlers()

        logger.info("XAgent initialized successfully")

    def _copy_md_files_to_working_dir(self):
        """复制 MD 提示词文件到工作目录"""
        import shutil
        from pathlib import Path
        from .constant import WORKING_DIR

        # MD 文件源目录
        md_files_dir = Path(__file__).parent / "agents" / "md_files"

        if not md_files_dir.exists():
            logger.warning("MD files directory not found: %s", md_files_dir)
            return

        # 确保工作目录存在
        WORKING_DIR.mkdir(parents=True, exist_ok=True)

        # 复制所有 .md 文件到工作目录
        copied_count = 0
        for md_file in md_files_dir.glob("*.md"):
            target_file = WORKING_DIR / md_file.name
            if not target_file.exists():
                try:
                    shutil.copy2(md_file, target_file)
                    logger.info("Copied md file: %s", md_file.name)
                    copied_count += 1
                except Exception as e:
                    logger.error("Failed to copy md file '%s': %s", md_file.name, e)

        if copied_count > 0:
            logger.info("Copied %d md file(s) to %s", copied_count, WORKING_DIR)
    
    def _init_lark_client(self):
        """初始化飞书客户端"""
        logger.info("Building Lark client...")
        self.client = LarkClient.builder() \
            .app_id(self.config.app_id) \
            .app_secret(self.config.app_secret) \
            .build()
        logger.info("Lark client built successfully")
        
        # 通过飞书 API 获取机器人 open_id
        self.bot_open_id = self._get_bot_open_id()
        logger.info(f"Bot open_id: {self.bot_open_id}")
    
    def _get_bot_open_id(self):
        """通过飞书 API 获取机器人的 open_id"""
        import requests
        
        try:
            # 1. 获取 tenant_access_token
            token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
            token_data = {
                "app_id": self.config.app_id,
                "app_secret": self.config.app_secret
            }
            
            logger.info("Getting tenant_access_token...")
            token_response = requests.post(token_url, json=token_data, timeout=10)
            token_result = token_response.json()
            
            if token_result.get("code") != 0:
                logger.warning(f"Failed to get token: {token_result}")
                return None
            
            tenant_access_token = token_result.get("tenant_access_token")
            logger.info("Got tenant_access_token successfully")
            
            # 2. 获取机器人信息
            bot_url = "https://open.feishu.cn/open-apis/bot/v3/info"
            headers = {"Authorization": f"Bearer {tenant_access_token}"}
            
            logger.info("Getting bot info...")
            bot_response = requests.get(bot_url, headers=headers, timeout=10)
            bot_result = bot_response.json()
            
            if bot_result.get("code") == 0 and bot_result.get("bot"):
                bot_open_id = bot_result["bot"].get("open_id")
                logger.info(f"Successfully retrieved bot open_id: {bot_open_id}")
                return bot_open_id
            else:
                logger.warning(f"Failed to get bot info: {bot_result}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting bot open_id: {e}", exc_info=True)
            return None
    
    def _init_core_components(self):
        """初始化核心组件"""
        self.dedup_cache = DeduplicationCache(max_size=self.config.cache_size)
        self.message_handler = MessageHandler(self.client, self.dedup_cache)
        self.session_manager = SessionManager(
            storage_path=self.config.session_storage_path,
            max_messages=self.config.max_session_messages,
            session_timeout=self.config.session_timeout
        )
        self.command_parser = CommandParser()
        self.executor_registry = ExecutorRegistry()
        self.response_formatter = ResponseFormatter()
        self.message_sender = MessageSender(self.client)
    
    def _init_provider_config(self):
        """初始化提供商配置"""
        self.provider_config_manager = ProviderConfigManager(
            storage_path="./data/provider_configs.json"
        )
        
        # 初始化统一配置管理器
        self.unified_config = UnifiedConfigManager(
            bot_config=self.config,
            session_config_path="./data/session_configs.json",
            provider_config_path="./data/provider_configs.json"
        )
        
        # 为 Web Admin 提供兼容的 config_manager 属性
        self.config_manager = self.unified_config.session_manager
    
    def _init_coordinators(self):
        """初始化协调器"""
        self.smart_router = SmartRouter(
            executor_registry=self.executor_registry,
            bot_config=self.config
        )
        
        self.message_processor = MessageProcessor(
            dedup_cache=self.dedup_cache,
            message_handler=self.message_handler,
            message_sender=self.message_sender,
            command_parser=self.command_parser,
            bot_open_id_getter=lambda: self.bot_open_id
        )
        
        self.command_dispatcher = CommandDispatcher(
            unified_config=self.unified_config,
            session_manager=self.session_manager,
            message_sender=self.message_sender,
            executor_registry=self.executor_registry
        )
        
        self.execution_coordinator = ExecutionCoordinator(
            smart_router=self.smart_router,
            executor_registry=self.executor_registry,
            session_manager=self.session_manager,
            message_sender=self.message_sender,
            unified_config=self.unified_config,
            response_formatter=self.response_formatter
        )
        
        self.error_handler = ErrorHandler(message_sender=self.message_sender)
    
    def _init_event_handlers(self):
        """初始化事件处理器"""
        self.event_handler = EventHandler()
        self.event_handler.register_message_receive_handler(
            self._handle_message_receive
        )
        
        self.ws_client = WebSocketClient(
            app_id=self.config.app_id,
            app_secret=self.config.app_secret,
            event_handler=self.event_handler
        )
    
    def _register_executors(self) -> None:
        """注册所有 AI 执行器（使用工厂模式）"""
        self._register_cli_executors()
        self._register_agent_executor()
    
    def _register_cli_executors(self) -> None:
        """注册所有 CLI 执行器"""
        for cli_config in CLIExecutorFactory.CLI_CONFIGS:
            self._register_single_cli_executor(cli_config)
    
    def _register_single_cli_executor(self, cli_config) -> None:
        """注册单个 CLI 执行器"""
        target_dir = CLIExecutorFactory.get_target_dir(cli_config, self.config)
        if not target_dir:
            return
        
        executor = CLIExecutorFactory.create_executor(
            config=cli_config,
            target_dir=target_dir,
            timeout=self.config.ai_timeout,
            session_storage_path=self.config.session_storage_path
        )
        
        if executor:
            metadata = CLIExecutorFactory.create_metadata(cli_config)
            self.executor_registry.register_cli_executor(cli_config.provider, executor, metadata)
            logger.info(f"Registered {cli_config.name} executor (target: {target_dir})")
    
    def _register_agent_executor(self) -> None:
        """注册 Agent 执行器"""
        search_api_key = os.environ.get("SERPER_API_KEY")
        
        executor = AgentExecutorFactory.create_executor(
            timeout=self.config.ai_timeout,
            search_api_key=search_api_key,
            provider_config_manager=self.provider_config_manager
        )
        
        if executor:
            metadata = AgentExecutorFactory.create_metadata()
            self.executor_registry.register_agent_executor("agent", executor, metadata)
            logger.info("Registered Agent executor")
    
    def _handle_message_receive(self, data: P2ImMessageReceiveV1) -> None:
        """处理接收到的消息（门面方法）
        
        协调 MessageProcessor -> CommandDispatcher -> ExecutionCoordinator 的流程
        """
        try:
            # 打印原始消息
            logger.info(f"[原始消息] 接收到消息: message_id={data.event.message.message_id}, chat_type={data.event.message.chat_type}, sender_id={data.event.sender.sender_id}")
            logger.info(f"[原始消息] 消息内容: {data.event.message.content}")
            
            processed = self.message_processor.process(data)
            if processed is None:
                return
            
            from .models import ParsedCommand
            parsed_command = ParsedCommand(
                provider=processed.parsed_command.provider,
                execution_layer=processed.parsed_command.execution_layer,
                message=processed.final_message,
                explicit=processed.parsed_command.explicit
            )
            
            if self.command_dispatcher.dispatch(
                session_id=processed.session_id,
                session_type=processed.session_type,
                user_id=processed.sender_id,
                message=processed.message_content,
                chat_type=processed.chat_type,
                chat_id=processed.chat_id,
                message_id=processed.message_id
            ):
                return
            
            context = ExecutionContext(
                message_id=processed.message_id,
                chat_id=processed.chat_id,
                chat_type=processed.chat_type,
                sender_id=processed.sender_id,
                session_id=processed.session_id,
                session_type=processed.session_type,
                message_content=processed.message_content,
                parsed_command=parsed_command,
                temp_params=processed.temp_params,
                final_message=processed.final_message,
                username=processed.username,
                original_message=processed.message_content
            )
            
            self.execution_coordinator.execute(context)
            
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            self._send_fallback_error(data, str(e))
    
    def _send_fallback_error(self, data: P2ImMessageReceiveV1, error_msg: str):
        """发送兜底错误消息"""
        try:
            self.message_sender.send_message(
                data.event.message.chat_type,
                data.event.message.chat_id,
                data.event.message.message_id,
                f"处理消息时发生错误：{error_msg}"
            )
        except Exception:
            pass
    
    def start(self) -> None:
        """启动 XAgent"""
        logger.info("Starting XAgent...")
        self.ws_client.start()
    
    def stop(self) -> None:
        """停止 XAgent"""
        logger.info("Stopping XAgent...")
        self.ws_client.stop()
    
    def get_bot_info(self) -> dict:
        """获取机器人信息"""
        return {
            "app_id": self.config.app_id,
            "bot_open_id": self.bot_open_id
        }
