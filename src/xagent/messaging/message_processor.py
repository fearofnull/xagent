"""
消息处理器模块

负责消息的预处理，包括去重、群聊@检测、消息解析、引用消息处理等
"""
import logging
import threading
from typing import Optional, Tuple, Any
from dataclasses import dataclass
from lark_oapi.api.im.v1 import P2ImMessageReceiveV1

from ..utils.cache import DeduplicationCache
from ..utils.command_parser import CommandParser
from .message_handler import MessageHandler
from .message_sender import MessageSender
from ..models import ParsedCommand

logger = logging.getLogger(__name__)


@dataclass
class ProcessedMessage:
    """处理后的消息数据"""
    message_id: str
    chat_id: str
    chat_type: str
    sender_id: Optional[str]
    username: Optional[str]
    message_content: str
    parsed_command: ParsedCommand
    temp_params: dict
    final_message: str
    session_id: str
    session_type: str


class MessageProcessor:
    """消息预处理器
    
    负责消息的预处理流程：
    1. 消息去重
    2. 群聊@检测
    3. 消息解析
    4. 命令解析
    5. 引用消息处理
    6. 会话信息提取
    """
    
    def __init__(
        self,
        dedup_cache: DeduplicationCache,
        message_handler: MessageHandler,
        message_sender: MessageSender,
        command_parser: CommandParser,
        bot_open_id_getter: callable
    ):
        """初始化消息处理器
        
        Args:
            dedup_cache: 去重缓存
            message_handler: 消息处理器
            message_sender: 消息发送器
            command_parser: 命令解析器
            bot_open_id_getter: 获取机器人 open_id 的回调函数
        """
        self.dedup_cache = dedup_cache
        self.message_handler = message_handler
        self.message_sender = message_sender
        self.command_parser = command_parser
        self._get_bot_open_id = bot_open_id_getter
    
    def process(self, data: P2ImMessageReceiveV1) -> Optional[ProcessedMessage]:
        """处理接收到的消息
        
        Args:
            data: 飞书消息接收事件
            
        Returns:
            处理后的消息数据，如果消息应该被跳过则返回 None
        """
        try:
            message_id = data.event.message.message_id
            chat_id = data.event.message.chat_id
            chat_type = data.event.message.chat_type
            
            sender_id = self._extract_sender_id(data)
            username = self._extract_username(data)
            logger.info(f"Received message {message_id} from user {sender_id}, username: {username}")
            
            if not self._check_duplicate(message_id):
                return None
            
            if not self._check_group_mention(data, chat_type):
                return None
            
            self._send_emoji_reaction_async(message_id)
            
            message_content = self._parse_message_content(data)
            if message_content is None:
                return None
            
            parsed_command, temp_params = self._parse_command(message_content)
            final_message = self._process_quoted_message(data, parsed_command)
            
            session_id, session_type = self._extract_session_info(chat_id, chat_type)
            
            return ProcessedMessage(
                message_id=message_id,
                chat_id=chat_id,
                chat_type=chat_type,
                sender_id=sender_id,
                username=username,
                message_content=message_content,
                parsed_command=parsed_command,
                temp_params=temp_params,
                final_message=final_message,
                session_id=session_id,
                session_type=session_type
            )
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return None
    
    def _extract_sender_id(self, data: P2ImMessageReceiveV1) -> Optional[str]:
        """提取发送者 ID"""
        try:
            if hasattr(data.event, 'sender') and hasattr(data.event.sender, 'sender_id'):
                return data.event.sender.sender_id.user_id
        except Exception as e:
            logger.warning(f"Failed to get sender_id: {e}")
        return None
    
    def _extract_username(self, data: P2ImMessageReceiveV1) -> Optional[str]:
        """提取发送者用户名"""
        try:
            if hasattr(data.event, 'sender'):
                # 尝试从 sender 中获取用户名
                if hasattr(data.event.sender, 'sender_type') and data.event.sender.sender_type == "user":
                    # 尝试从 sender.sender_id 中获取
                    if hasattr(data.event.sender, 'sender_id'):
                        # 飞书消息结构中，sender_id 可能包含 user_id
                        # 实际的用户名可能需要通过 API 获取
                        # 这里暂时返回 user_id 作为用户名
                        return data.event.sender.sender_id.user_id
        except Exception as e:
            logger.warning(f"Failed to get username: {e}")
        return None
    
    def _check_duplicate(self, message_id: str) -> bool:
        """检查消息是否重复"""
        if self.dedup_cache.is_processed(message_id):
            logger.info(f"Message {message_id} already processed, skipping")
            return False
        self.dedup_cache.mark_processed(message_id)
        return True
    
    def _check_group_mention(self, data: P2ImMessageReceiveV1, chat_type: str) -> bool:
        """检查群聊消息是否@了机器人"""
        if chat_type != "group":
            return True
        
        is_mentioned = self._is_bot_mentioned(data.event.message)
        if not is_mentioned:
            logger.info(f"Message in group chat does not mention bot, skipping")
            return False
        return True
    
    def _is_bot_mentioned(self, message) -> bool:
        """检测消息中是否@了机器人"""
        try:
            # 只有当消息中包含 mentions 字段时，才可能被@
            if not (hasattr(message, 'mentions') and message.mentions):
                return False
            
            bot_open_id = self._get_bot_open_id()
            
            # 如果获取到了机器人 open_id，检查是否被@
            if bot_open_id:
                for mention in message.mentions:
                    if hasattr(mention, 'id') and hasattr(mention.id, 'open_id'):
                        if mention.id.open_id == bot_open_id:
                            return True
                return False
            else:
                # 如果没有获取到机器人 open_id，无法准确检测，返回 False
                # 这样可以避免不@也回复的问题
                logger.warning("Bot open_id not available, cannot accurately check mention. Skipping.")
                return False
        except Exception as e:
            logger.warning(f"Error checking bot mention: {e}")
            return False
    
    def _send_emoji_reaction_async(self, message_id: str):
        """异步发送 emoji 反应"""
        threading.Thread(
            target=self._send_emoji_in_thread,
            args=(message_id,),
            daemon=True
        ).start()
    
    def _send_emoji_in_thread(self, message_id: str):
        """在线程中发送 emoji 反应"""
        try:
            self.message_handler.send_emoji_reaction_sync(message_id)
        except Exception as e:
            logger.warning(f"Failed to send emoji reaction in thread: {e}")
    
    def _parse_message_content(self, data: P2ImMessageReceiveV1) -> Optional[str]:
        """解析消息内容"""
        logger.info(f"Message type: {data.event.message.message_type}")
        
        message_content = self.message_handler.parse_message_content(data.event.message)
        
        if message_content.startswith("解析消息失败") or message_content.startswith("parse message failed"):
            self.message_sender.send_message(
                data.event.message.chat_type,
                data.event.message.chat_id,
                data.event.message.message_id,
                message_content
            )
            return None
        
        return message_content
    
    def _parse_command(self, message_content: str) -> Tuple[ParsedCommand, dict]:
        """解析命令"""
        logger.info(f"[解析命令] 原始消息内容: {message_content[:200]}...")
        parsed_command, temp_params = self.command_parser.parse_command(message_content)
        logger.info(f"[解析命令] 解析结果: provider={parsed_command.provider}, "
                   f"layer={parsed_command.execution_layer}, explicit={parsed_command.explicit}")
        return parsed_command, temp_params
    
    def _process_quoted_message(self, data: P2ImMessageReceiveV1, parsed_command: ParsedCommand) -> str:
        """处理引用消息"""
        final_message = parsed_command.message
        
        if hasattr(data.event.message, 'parent_id') and data.event.message.parent_id:
            logger.info(f"Detected parent_id: {data.event.message.parent_id}")
            quoted_content = self.message_handler.get_quoted_message(
                data.event.message.parent_id
            )
            
            if quoted_content:
                final_message = self.message_handler.combine_messages(
                    quoted_content, parsed_command.message
                )
                logger.info(f"Combined message with quoted content, length={len(final_message)}")
                logger.info(f"Combined message content: {final_message}")
        else:
            logger.info(f"No quoted message, using original message: {final_message}")
        
        return final_message
    
    def _extract_session_info(self, chat_id: str, chat_type: str) -> Tuple[str, str]:
        """提取会话信息"""
        session_id = chat_id
        session_type = "user" if chat_type == "p2p" else "group"
        logger.info(f"Session: session_id={session_id}, session_type={session_type}")
        return session_id, session_type
