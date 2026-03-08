"""
消息发送器

负责向飞书发送消息，支持不同的发送策略。
"""
import logging
from typing import Optional
from lark_oapi import Client as LarkClient
from lark_oapi.api.im.v1 import (
    CreateMessageRequest,
    CreateMessageRequestBody,
    ReplyMessageRequest,
    ReplyMessageRequestBody
)

logger = logging.getLogger(__name__)


class MessageSender:
    """消息发送器
    
    根据聊天类型选择合适的发送策略：
    - p2p（私聊）：发送新消息
    - group（群聊）：回复消息
    
    Requirements: 6.1, 6.2, 6.3, 6.4
    """
    
    def __init__(self, client: LarkClient):
        """初始化消息发送器
        
        Args:
            client: 飞书客户端
        """
        self.client = client
    
    def send_message(
        self,
        chat_type: str,
        chat_id: str,
        message_id: str,
        content: str
    ) -> bool:
        """发送消息
        
        根据聊天类型选择发送策略：
        - p2p：使用 send_new_message
        - 其他：使用 reply_message
        
        Args:
            chat_type: 聊天类型（p2p, group 等）
            chat_id: 聊天 ID
            message_id: 消息 ID
            content: 消息内容
            
        Returns:
            True 如果发送成功
        """
        try:
            if chat_type == "p2p":
                return self.send_new_message(chat_id, content)
            else:
                return self.reply_message(message_id, content)
        except Exception as e:
            logger.error(f"Failed to send message: {e}", exc_info=True)
            return False
    
    def send_new_message(self, chat_id: str, content: str) -> bool:
        """发送新消息（用于私聊）
        
        Args:
            chat_id: 聊天 ID
            content: 消息内容
            
        Returns:
            True 如果发送成功
        """
        try:
            request = CreateMessageRequest.builder() \
                .receive_id_type("chat_id") \
                .request_body(
                    CreateMessageRequestBody.builder()
                    .receive_id(chat_id)
                    .msg_type("text")
                    .content(f'{{"text":"{self._escape_json(content)}"}}')
                    .build()
                ) \
                .build()
            
            response = self.client.im.v1.message.create(request)
            
            if not response.success():
                logger.error(
                    f"Failed to send new message: code={response.code}, "
                    f"msg={response.msg}, log_id={response.get_log_id()}"
                )
                return False
            
            logger.info(f"Successfully sent new message to chat {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending new message: {e}", exc_info=True)
            return False
    
    def reply_message(self, message_id: str, content: str) -> bool:
        """回复消息（用于群聊）
        
        Args:
            message_id: 要回复的消息 ID
            content: 消息内容
            
        Returns:
            True 如果发送成功
        """
        try:
            request = ReplyMessageRequest.builder() \
                .message_id(message_id) \
                .request_body(
                    ReplyMessageRequestBody.builder()
                    .msg_type("text")
                    .content(f'{{"text":"{self._escape_json(content)}"}}')
                    .build()
                ) \
                .build()
            
            response = self.client.im.v1.message.reply(request)
            
            if not response.success():
                logger.error(
                    f"Failed to reply message: code={response.code}, "
                    f"msg={response.msg}, log_id={response.get_log_id()}"
                )
                return False
            
            logger.info(f"Successfully replied to message {message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error replying message: {e}", exc_info=True)
            return False
    
    def _escape_json(self, text: str) -> str:
        """转义 JSON 字符串中的特殊字符
        
        Args:
            text: 原始文本
            
        Returns:
            转义后的文本
        """
        return text.replace('\\', '\\\\') \
                   .replace('"', '\\"') \
                   .replace('\n', '\\n') \
                   .replace('\r', '\\r') \
                   .replace('\t', '\\t')
