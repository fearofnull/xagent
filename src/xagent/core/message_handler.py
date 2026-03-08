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
            request = CreateMessageReactionRequest.builder() \
                .message_id(message_id) \
                .request_body(
                    CreateMessageReactionRequestBody.builder()
                    .reaction_type(
                        Emoji.builder().emoji_type(emoji).build()
                    )
                    .build()
                ) \
                .build()
            
            # 直接同步调用（在线程中执行，无需async）
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
            提取的文本内容（已清理@提及标记）
            
        Raises:
            ValueError: 如果消息类型不是文本或解析失败
        """
        # 处理 EventMessage 对象或字典
        if hasattr(message, 'message_type'):
            # EventMessage 对象
            message_type = message.message_type
            content_str = message.content
        else:
            # 字典
            message_type = message.get("message_type", "")
            content_str = message.get("content", "{}")
        
        # 处理文本消息
        if message_type == "text":
            # 解析消息内容
            try:
                content = json.loads(content_str)
                text = content.get("text", "")
                
                if not text:
                    raise ValueError("消息内容为空")
                
                # 清理@提及标记
                text = self._clean_mentions(text)
                
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
        
        # 处理卡片消息
        elif message_type == "interactive":
            try:
                # 解析 content 字段为 JSON 对象
                content = json.loads(content_str)
                
                # 调用 extract_card_content 提取文本内容
                extracted_content = self.extract_card_content(content)
                
                # 验证提取的内容非空
                if not extracted_content or extracted_content == "[卡片消息]":
                    error_msg = "卡片消息内容为空"
                    logger.warning(error_msg)
                    raise ValueError(error_msg)
                
                # 添加调试日志记录提取的内容（前50个字符）
                logger.debug(f"成功解析卡片消息: {extracted_content[:50]}...")
                
                # 返回提取的文本内容
                return extracted_content
                
            except json.JSONDecodeError as e:
                error_msg = f"卡片消息内容 JSON 解析失败: {e}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            except ValueError:
                # 重新抛出 ValueError（如空内容错误）
                raise
            except Exception as e:
                error_msg = f"消息解析失败: {e}"
                logger.error(error_msg)
                raise ValueError(error_msg)
        
        # 不支持的消息类型
        else:
            error_msg = f"不支持的消息类型: {message_type}。请发送文本消息或卡片消息。"
            logger.warning(error_msg)
            raise ValueError(error_msg)
    
    def _clean_mentions(self, text: str) -> str:
        """清理消息中的@提及标记
        
        Args:
            text: 原始消息文本
            
        Returns:
            清理后的文本
        """
        # 移除 <at user_id="xxx">xxx</at> 格式的@提及
        text = re.sub(r'<at user_id="[^"]*">[^<]*</at>', '', text)
        
        # 移除 @_user_1, @_user_2 等占位符
        text = re.sub(r'@_user_\d+', '', text)
        
        # 移除 @_all 等特殊提及
        text = re.sub(r'@_all', '', text)
        
        # 清理多余的空格
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_card_content(self, card: dict) -> str:
        """递归提取卡片消息中的所有可读文本内容
        
        Args:
            card: 卡片JSON对象（dict）
            
        Returns:
            提取的文本内容，格式为"[卡片消息]\n{内容}"或"[卡片消息]"（降级处理）
        """
        content_parts = []
        
        try:
            # 提取 title（飞书API返回的扁平化结构）
            if "title" in card:
                title = card["title"]
                if isinstance(title, str) and title:
                    # 清理换行符和多余空白，转换为单行
                    title = re.sub(r'\s+', ' ', title).strip()
                    if title:  # 再次检查清理后是否为空
                        content_parts.append(title)
            
            # 提取 header 部分（飞书官方文档的发送格式）
            if "header" in card:
                header = card["header"]
                if "title" in header and "content" in header["title"]:
                    title = header["title"]["content"]
                    if title:
                        # 清理换行符和多余空白，转换为单行
                        title = re.sub(r'\s+', ' ', title).strip()
                        if title:  # 再次检查清理后是否为空
                            content_parts.append(title)
            
            # 递归处理 elements 数组
            if "elements" in card:
                elements = card["elements"]
                if isinstance(elements, list):
                    for element in elements:
                        # 检查是否是二维数组（飞书API返回的扁平化结构）
                        if isinstance(element, list):
                            # 处理二维数组中的每个元素
                            for sub_element in element:
                                self._extract_element_content(sub_element, content_parts)
                        else:
                            # 处理一维数组（飞书官方文档的发送格式）
                            self._extract_element_content(element, content_parts)
            
            # 格式化输出
            if content_parts:
                # 使用单行格式，避免 CLI headless 模式的多行问题
                # 使用 | 分隔不同部分，保持单行
                content = " | ".join(content_parts)
                # 限制总长度（最大2000字符）
                if len(content) > 2000:
                    content = content[:2000] + "..."
                return f"[卡片消息] {content}"
            else:
                # 如果未提取到内容，返回降级处理
                return "[卡片消息]"
                
        except Exception as e:
            logger.warning(f"提取卡片内容时发生异常: {e}")
            return "[卡片消息]"
    
    def _extract_element_content(self, element: dict, content_parts: list) -> None:
        """递归提取单个元素的文本内容
        
        Args:
            element: 元素对象
            content_parts: 内容列表，用于收集提取的文本
        """
        if not isinstance(element, dict):
            return
        
        tag = element.get("tag", "")
        
        # 处理 text 元素
        if tag == "text":
            # 飞书API返回的扁平化结构：直接在 "text" 字段
            if "text" in element:
                text = element["text"]
                if text:
                    # 清理换行符和多余空白，转换为单行
                    text = re.sub(r'\s+', ' ', text).strip()
                    if text:  # 再次检查清理后是否为空
                        content_parts.append(text)
            # 飞书官方文档的发送格式：在 "content" 字段
            elif "content" in element:
                content = element["content"]
                if content:
                    # 清理换行符和多余空白，转换为单行
                    content = re.sub(r'\s+', ' ', content).strip()
                    if content:  # 再次检查清理后是否为空
                        content_parts.append(content)
        
        # 处理 markdown 元素
        elif tag == "markdown":
            if "content" in element:
                content = element["content"]
                if content:
                    # 清理换行符和多余空白，转换为单行
                    content = re.sub(r'\s+', ' ', content).strip()
                    if content:  # 再次检查清理后是否为空
                        content_parts.append(content)
        
        # 处理 div 元素
        elif tag == "div":
            # 提取 text 字段
            if "text" in element:
                text_obj = element["text"]
                if isinstance(text_obj, dict) and "content" in text_obj:
                    content = text_obj["content"]
                    if content:
                        # 清理换行符和多余空白，转换为单行
                        content = re.sub(r'\s+', ' ', content).strip()
                        if content:  # 再次检查清理后是否为空
                            content_parts.append(content)
            
            # 递归处理 fields
            if "fields" in element:
                fields = element["fields"]
                if isinstance(fields, list):
                    for field in fields:
                        if isinstance(field, dict) and "text" in field:
                            text_obj = field["text"]
                            if isinstance(text_obj, dict) and "content" in text_obj:
                                content = text_obj["content"]
                                if content:
                                    # 清理换行符和多余空白，转换为单行
                                    content = re.sub(r'\s+', ' ', content).strip()
                                    if content:  # 再次检查清理后是否为空
                                        content_parts.append(content)
            
            # 递归处理嵌套的 elements
            if "elements" in element:
                nested_elements = element["elements"]
                if isinstance(nested_elements, list):
                    for nested_element in nested_elements:
                        self._extract_element_content(nested_element, content_parts)
        
        # 处理 action 元素（包含 actions 数组）
        elif tag == "action":
            if "actions" in element:
                actions = element["actions"]
                if isinstance(actions, list):
                    for action in actions:
                        if isinstance(action, dict):
                            # 递归处理每个 action（通常是 button）
                            self._extract_element_content(action, content_parts)
        
        # 处理 button 元素
        elif tag == "button":
            # 飞书API返回的扁平化结构：直接在 "text" 字段
            if "text" in element:
                text = element["text"]
                # text可能是字符串或对象
                if isinstance(text, str) and text:
                    # 清理换行符和多余空白，转换为单行
                    text = re.sub(r'\s+', ' ', text).strip()
                    if text:  # 再次检查清理后是否为空
                        content_parts.append(text)
                elif isinstance(text, dict) and "content" in text:
                    content = text["content"]
                    if content:
                        # 清理换行符和多余空白，转换为单行
                        content = re.sub(r'\s+', ' ', content).strip()
                        if content:  # 再次检查清理后是否为空
                            content_parts.append(content)
        
        # 处理 url_preview 元素
        elif tag == "url_preview":
            if "title" in element:
                title = element["title"]
                if title:
                    # 清理换行符和多余空白，转换为单行
                    title = re.sub(r'\s+', ' ', title).strip()
                    if title:  # 再次检查清理后是否为空
                        content_parts.append(title)
            if "description" in element:
                description = element["description"]
                if description:
                    # 清理换行符和多余空白，转换为单行
                    description = re.sub(r'\s+', ' ', description).strip()
                    if description:  # 再次检查清理后是否为空
                        content_parts.append(description)
        
        # 处理 column_set 元素
        elif tag == "column_set":
            if "columns" in element:
                columns = element["columns"]
                if isinstance(columns, list):
                    for column in columns:
                        if isinstance(column, dict) and "elements" in column:
                            column_elements = column["elements"]
                            if isinstance(column_elements, list):
                                for column_element in column_elements:
                                    self._extract_element_content(column_element, content_parts)
        
        # 处理 field 元素（key-value对）
        elif tag == "field":
            if "text" in element:
                text_obj = element["text"]
                if isinstance(text_obj, dict) and "content" in text_obj:
                    content = text_obj["content"]
                    if content:
                        # 清理换行符和多余空白，转换为单行
                        content = re.sub(r'\s+', ' ', content).strip()
                        if content:  # 再次检查清理后是否为空
                            content_parts.append(content)
        
        # 处理 hr 元素（分隔线，跳过）
        elif tag == "hr":
            pass  # 分隔线不包含文本内容，跳过
    
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
            request = GetMessageRequest.builder() \
                .message_id(parent_id) \
                .build()
            
            # 调用 API
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
            
            # 处理文本消息
            if message_type == "text":
                content = json.loads(content_str)
                text = content.get("text", "")
                logger.info(f"成功获取引用的文本消息: {text[:50]}...")
                return text
            
            # 处理卡片消息（interactive）
            elif message_type == "interactive":
                # 卡片消息通常包含复杂的 JSON 结构
                # 调用 extract_card_content 提取完整内容
                try:
                    content = json.loads(content_str)
                    logger.debug(f"卡片消息原始内容: {json.dumps(content, ensure_ascii=False)[:500]}...")
                    result = self.extract_card_content(content)
                    
                    # 添加详细调试：检查提取结果
                    if result == "[卡片消息]" or result == "[卡片消息]\n":
                        logger.warning(f"卡片内容提取失败，仅返回占位符。卡片结构: {json.dumps(content, ensure_ascii=False)[:1000]}")
                    
                    logger.info(f"成功提取引用的卡片消息内容: {result[:100]}...")
                    return result
                    
                except Exception as e:
                    logger.warning(f"解析卡片消息内容失败: {e}", exc_info=True)
                    return "[卡片消息]"
            
            # 其他消息类型
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
