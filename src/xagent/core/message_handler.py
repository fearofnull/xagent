"""

消息处理器模块

负责解析和处理飞书消息，包括文本消息和引用消息

"""

import asyncio
import json
import logging
import re
from typing import Optional
from lark_oapi.api.im.v1 import (
    GetMessageRequest,
    GetMessageResponse,
    CreateMessageReactionRequest,
    CreateMessageReactionRequestBody,
    Emoji
)

from lark_oapi import Client as LarkClient
from ..utils.cache import DeduplicationCache
from .message_parser import (
    parse_text_content,
    parse_post_content,
    parse_card_content,
    replace_mentions,
)

logger = logging.getLogger(__name__)

class MessageHandler:
    """消息处理器
    负责解析飞书消息内容，处理引用消息，并组合消息
    """
    def __init__(self, client: LarkClient, dedup_cache: DeduplicationCache):
        """初始化消息处理器
        Args:
            client: 飞书 API 客户端
            dedup_cache: 消息去重缓存
        """
        self.client = client
        self.dedup_cache = dedup_cache
    def send_emoji_reaction_sync(self, message_id: str, emoji: str = "OK") -> bool:
        """发送emoji反应（同步方法，参考飞书官方SDK示例和CoPaw项目实现）
        在接收到用户消息后立即发送emoji反应，让用户知道消息已被接收。
        Args:
            message_id: 消息ID
            emoji: emoji代码字符串，如 "EYES", "OK", "Typing" 等
        Returns:
            是否成功发送
        Requirements: 需求1 - Emoji即时反馈
        """
        try:
            # 构建请求 - 使用 Emoji builder
            # 参考: https://github.com/larksuite/oapi-sdk-python/blob/main/samples/api/im/v1/create_message_reaction_sample.py
            request = (
                CreateMessageReactionRequest.builder()
                .message_id(message_id)
                .request_body(
                    CreateMessageReactionRequestBody.builder()
                    .reaction_type(Emoji.builder().emoji_type(emoji).build())
                    .build()
                )
                .build()
            )
            logger.debug(f"Sending emoji reaction '{emoji}' for message {message_id}")
            response = self.client.im.v1.message_reaction.create(request)
            if not response.success():
                logger.warning(
                    f"Failed to send emoji reaction: code={response.code}, "
                    f"msg={response.msg}, log_id={response.get_log_id()}, "
                    f"emoji={emoji}, message_id={message_id}"
                )
                return False
            logger.info(f"Emoji reaction sent for message {message_id}")
            return True
        except Exception as e:
            logger.warning(f"Error sending emoji reaction: {e}")
            return False
    def parse_message_content(self, message) -> str:
        """解析消息内容，提取文本内容
        Args:
            message: 飞书消息对象（EventMessage 或 dict），包含 message_type 和 content 字段
        Returns:
            提取的文本内容（已替换@提及为用户名）
        Raises:
            ValueError: 如果消息类型不是文本或解析失败
        """
        if hasattr(message, 'message_type'):
            message_type = message.message_type
            content_str = message.content
        else:
            message_type = message.get("message_type", "")
            content_str = message.get("content", "{}")
        
        mentions = getattr(message, 'mentions', None)
        
        if message_type == "text":
            try:
                text = parse_text_content(content_str)
                if not text:
                    raise ValueError("消息内容为空")
                text = replace_mentions(text, mentions)
                logger.debug(f"成功解析文本消息: {text[:50]}...")
                return text
            except json.JSONDecodeError as e:
                error_msg = f"消息内容 JSON 解析失败: {e}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            except Exception as e:
                error_msg = f"消息解析失败: {e}"
                logger.error(error_msg)
                raise ValueError(error_msg)
        
        elif message_type == "interactive":
            try:
                text = parse_card_content(content_str)
                if not text or text == "[卡片消息]":
                    error_msg = "卡片消息内容为空"
                    logger.warning(error_msg)
                    raise ValueError(error_msg)
                text = replace_mentions(text, mentions)
                logger.debug(f"成功解析卡片消息: {text[:50]}...")
                return text
            except json.JSONDecodeError as e:
                error_msg = f"卡片消息内容 JSON 解析失败: {e}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            except ValueError:
                raise
            except Exception as e:
                error_msg = f"消息解析失败: {e}"
                logger.error(error_msg)
                raise ValueError(error_msg)
        
        elif message_type == "post":
            try:
                logger.debug(f"接收到富文本消息，原始内容: {content_str[:500]}...")
                text = parse_post_content(content_str)
                if not text:
                    error_msg = "富文本消息内容为空"
                    logger.warning(error_msg)
                    raise ValueError(error_msg)
                text = replace_mentions(text, mentions)
                logger.debug(f"成功解析富文本消息: {text[:50]}...")
                return text
            except json.JSONDecodeError as e:
                error_msg = f"富文本消息内容 JSON 解析失败: {e}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            except ValueError:
                raise
            except Exception as e:
                error_msg = f"消息解析失败: {e}"
                logger.error(error_msg)
                raise ValueError(error_msg)
        
        else:
            error_msg = f"不支持的消息类型: {message_type}。请发送文本消息、卡片消息或富文本消息。"
            logger.warning(error_msg)
            raise ValueError(error_msg)
    
    def extract_post_content(self, post: dict) -> str:
        """提取富文本消息内容（向后兼容方法）
        
        注意：此方法保留用于向后兼容
        实际解析逻辑已迁移到 message_parser.parse_post_content
        """
        import json
        return parse_post_content(json.dumps(post, ensure_ascii=False))
    
    def get_quoted_message(self, parent_id: str) -> Optional[str]:
        """获取引用消息的内容
        调用飞书 API 获取引用消息，支持文本消息和卡片消息（interactive）
        Args:
            parent_id: 引用消息的 ID
        Returns:
            引用消息的文本内容，如果获取失败返回 None
        """
        if not parent_id:
            return None
        try:
            logger.info(f"正在获取引用消息: {parent_id}")
            # 构建请求
            request = (
                GetMessageRequest.builder()
                .message_id(parent_id)
                .build()
            )
            response: GetMessageResponse = self.client.im.v1.message.get(request)
            # 检查响应
            if not response.success():
                logger.warning(
                    f"获取引用消息失败: code={response.code}, "
                    f"msg={response.msg}, log_id={response.get_log_id()}"
                )
                return None
            # 提取消息内容
            # 兼容两种API响应格式：
            # 1. 真实API: response.data.items (列表)
            # 2. 测试Mock: response.data.message (单个对象)
            # 优先尝试获取message（测试Mock）
            if hasattr(response.data, 'message') and hasattr(response.data.message, 'message_type'):
                quoted_message = response.data.message
                message_type = quoted_message.message_type
                content_str = quoted_message.content
            # 尝试获取items（真实API）
            elif hasattr(response.data, 'items'):
                items = response.data.items
                if not items:
                    logger.warning(f"未找到消息: {parent_id}")
                    return None
                try:
                    if isinstance(items, list) and len(items) == 0:
                        logger.warning(f"未找到消息: {parent_id}")
                        return None
                    quoted_message = items[0] if isinstance(items, list) else items
                except (TypeError, AttributeError):
                    quoted_message = items
                # 真实API的消息结构
                message_type = quoted_message.msg_type
                content_str = quoted_message.body.content
            else:
                logger.warning(f"无法解析响应数据结构: {parent_id}")
                return None
            logger.debug(f"引用消息类型: {message_type}")
            
            mentions = getattr(quoted_message, 'mentions', None)
            
            if message_type == "text":
                text = parse_text_content(content_str)
                text = replace_mentions(text, mentions)
                logger.info(f"成功获取引用的文本消息: {text[:50]}...")
                return text
            elif message_type == "interactive":
                try:
                    text = parse_card_content(content_str)
                    text = replace_mentions(text, mentions)
                    logger.info(f"成功提取引用的卡片消息内容: {text[:100]}...")
                    return text
                except Exception as e:
                    logger.warning(f"解析卡片消息内容失败: {e}", exc_info=True)
                    return "[卡片消息]"
            elif message_type == "post":
                try:
                    text = parse_post_content(content_str)
                    text = replace_mentions(text, mentions)
                    logger.info(f"成功提取引用的富文本消息内容: {text[:100]}...")
                    return text
                except Exception as e:
                    logger.warning(f"解析富文本消息内容失败: {e}", exc_info=True)
                    return "[富文本消息]"
            else:
                logger.warning(f"不支持的引用消息类型: {message_type}")
                return f"[{message_type} 消息]"
        except Exception as e:
            logger.error(f"获取引用消息时发生异常: {e}", exc_info=True)
            return None
    def combine_messages(self, quoted: Optional[str], current: str) -> str:
        """组合引用消息和当前消息
        Args:
            quoted: 引用消息内容，可以为 None
            current: 当前消息内容
        Returns:
            组合后的消息字符串
        Note:
            使用单行格式，避免 CLI headless 模式的多行问题
            使用 >>> 作为分隔符，CLI友好且避免与消息内容冲突
        """
        if quoted:
            # 使用单行格式和 >>> 分隔符，避免 CLI headless 模式的多行问题
            # >>> 是CLI友好的分隔符，不会被shell解释为特殊字符
            combined = f"引用消息：{quoted} >>> 当前消息：{current}"
            logger.debug(f"组合消息: 引用消息长度={len(quoted)}, 当前消息长度={len(current)}")
            return combined
        else:
            logger.debug(f"无引用消息，返回当前消息: 长度={len(current)}")
            return current

