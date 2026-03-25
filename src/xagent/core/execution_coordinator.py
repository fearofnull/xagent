"""
执行协调器模块

负责协调 AI 执行流程，包括路由、执行、响应格式化等
"""
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

from .smart_router import SmartRouter
from .executor_registry import ExecutorRegistry
from ..session.session_manager import SessionManager
from ..messaging.message_sender import MessageSender
from ..utils.response_formatter import ResponseFormatter
from ..models import ParsedCommand, ExecutionResult

logger = logging.getLogger(__name__)


LANGUAGE_MAP = {
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


@dataclass
class ExecutionContext:
    """执行上下文"""
    message_id: str
    chat_id: str
    chat_type: str
    sender_id: Optional[str]
    session_id: str
    session_type: str
    message_content: str
    parsed_command: ParsedCommand
    temp_params: dict
    final_message: str
    username: Optional[str] = None
    original_message: Optional[str] = None


class ExecutionCoordinator:
    """执行协调器
    
    负责协调 AI 执行流程：
    1. 获取有效配置
    2. 智能路由选择执行器
    3. 执行 AI 任务
    4. 格式化响应
    5. 更新会话历史
    """
    
    def __init__(
        self,
        smart_router: SmartRouter,
        executor_registry: ExecutorRegistry,
        session_manager: SessionManager,
        message_sender: MessageSender,
        unified_config,
        response_formatter: ResponseFormatter
    ):
        """初始化执行协调器
        
        Args:
            smart_router: 智能路由器
            executor_registry: 执行器注册表
            session_manager: 会话管理器
            message_sender: 消息发送器
            unified_config: 统一配置管理器
            response_formatter: 响应格式化器
        """
        self.smart_router = smart_router
        self.executor_registry = executor_registry
        self.session_manager = session_manager
        self.message_sender = message_sender
        self.unified_config = unified_config
        self.response_formatter = response_formatter
    
    def execute(self, context: ExecutionContext) -> bool:
        """执行 AI 任务
        
        Args:
            context: 执行上下文
            
        Returns:
            True 如果执行成功
        """
        try:
            effective_config = self.unified_config.get_effective_config(
                context.session_id, context.session_type, context.temp_params
            )
            
            executor = self._route_to_executor(context.parsed_command, context.message_content)
            if executor is None:
                return False
            
            result, executor_name = self._execute_ai(
                executor, context, effective_config
            )
            
            self._send_response(result, context, executor_name)
            
            self._update_session_history(context.sender_id, context.parsed_command.message, result)
            
            logger.info(f"Successfully processed message {context.message_id}")
            return result.success
            
        except Exception as e:
            logger.error(f"Execution failed: {e}", exc_info=True)
            self._send_error_response(context, str(e))
            return False
    
    def _route_to_executor(self, parsed_command: ParsedCommand, original_message: str):
        """路由到执行器"""
        try:
            return self.smart_router.route(parsed_command)
        except Exception as e:
            error_msg = f"路由失败：{str(e)}"
            logger.error(error_msg)
            return None
    
    def _execute_ai(
        self,
        executor,
        context: ExecutionContext,
        effective_config: Dict[str, Any]
    ) -> tuple[ExecutionResult, Optional[str]]:
        """执行 AI 任务"""
        conversation_history = self.session_manager.get_conversation_history(context.sender_id)
        
        provider_name = executor.get_provider_name()
        provider, layer = self._parse_provider_name(provider_name)
        
        executor_metadata = self.executor_registry.get_executor_metadata(provider, layer)
        executor_name = executor_metadata.name if executor_metadata else None
        
        message_with_language = self._prepend_language_instruction(
            context.final_message, effective_config.get("response_language")
        )
        
        # 打印要处理的提示词
        logger.info(f"[处理提示词] 执行器: {executor_name}, 提示词长度: {len(message_with_language)}")
        logger.info(f"[处理提示词] 内容: {message_with_language}")
        
        additional_params = {
            "user_id": context.sender_id,
            "username": context.username,
            "chat_id": context.chat_id,
            "chat_type": context.chat_type,
            "session_id": context.session_id,
            "original_message": context.original_message or context.message_content
        }
        
        if provider_name == "agent":
            result = self._execute_agent(
                executor, message_with_language, conversation_history, additional_params
            )
        else:
            result = self._execute_cli(
                executor, message_with_language, additional_params, effective_config
            )
        
        return result, executor_name
    
    def _parse_provider_name(self, provider_name: str) -> tuple:
        """解析 provider 名称"""
        if "-" in provider_name:
            parts = provider_name.rsplit("-", 1)
            return parts[0], parts[1]
        return provider_name, "agent"
    
    def _execute_agent(
        self,
        executor,
        message: str,
        conversation_history: list,
        additional_params: dict
    ) -> ExecutionResult:
        """执行 Agent 层任务"""
        logger.debug(f"[Agent] Executing with message: {message[:200]}...")
        return executor.execute(
            message,
            conversation_history=conversation_history,
            additional_params=additional_params
        )
    
    def _execute_cli(
        self,
        executor,
        message: str,
        additional_params: dict,
        effective_config: Dict[str, Any]
    ) -> ExecutionResult:
        """执行 CLI 层任务"""
        logger.info(f"[CLI] Executing with message: {message[:200]}...")
        
        target_dir = effective_config.get("target_project_dir")
        original_message = additional_params.get('original_message')
        
        if hasattr(executor, 'target_dir') and target_dir:
            original_target_dir = executor.target_dir
            executor.target_dir = target_dir
            result = executor.execute(message, additional_params=additional_params)
            executor.target_dir = original_target_dir
            return result
        
        return executor.execute(message, additional_params=additional_params)
    
    def _send_response(self, result: ExecutionResult, context: ExecutionContext, executor_name: Optional[str]):
        """发送响应"""
        if result.success:
            response = self.response_formatter.format_response(
                context.message_content, result.stdout, executor_name=executor_name
            )
        else:
            response = self.response_formatter.format_error(
                context.message_content, result.error_message or result.stderr, executor_name=executor_name
            )
        
        if result.stdout or not result.success:
            self.message_sender.send_message(
                context.chat_type, context.chat_id, context.message_id, response
            )
    
    def _send_error_response(self, context: ExecutionContext, error_msg: str):
        """发送错误响应"""
        response = self.response_formatter.format_error(
            context.message_content, f"执行失败：{error_msg}"
        )
        self.message_sender.send_message(
            context.chat_type, context.chat_id, context.message_id, response
        )
    
    def _update_session_history(
        self,
        sender_id: Optional[str],
        user_message: str,
        result: ExecutionResult
    ):
        """更新会话历史"""
        if not sender_id:
            return
        
        self.session_manager.add_message(sender_id, "user", user_message)
        self.session_manager.add_message(
            sender_id, "assistant",
            result.stdout if result.success else result.error_message
        )
    
    def _prepend_language_instruction(self, message: str, response_language: Optional[str]) -> str:
        """在消息前添加语言指令"""
        if not response_language or response_language not in LANGUAGE_MAP:
            return message
        
        language_name = LANGUAGE_MAP.get(response_language, response_language)
        return f"请使用{language_name}回答以下问题：\n\n{message}"
