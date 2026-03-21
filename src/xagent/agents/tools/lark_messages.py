# -*- coding: utf-8 -*-
"""飞书消息历史读取工具"""

import logging
import os
from typing import Optional

from agentscope.tool import ToolResponse
from agentscope.message import TextBlock

from lark_oapi import Client as LarkClient
from lark_oapi.api.im.v1 import ListMessageRequest

from ...core.message_parser import (
    parse_message_body,
    replace_mentions,
    format_timestamp,
    format_sender_info,
)

logger = logging.getLogger(__name__)

_lark_client: Optional[LarkClient] = None


def _get_lark_client() -> LarkClient:
    """获取或创建飞书客户端单例"""
    global _lark_client
    if _lark_client is None:
        from ...config import BotConfig
        config = BotConfig.from_env()
        _lark_client = LarkClient.builder() \
            .app_id(config.app_id) \
            .app_secret(config.app_secret) \
            .build()
    return _lark_client


def _format_message_content(msg) -> str:
    """格式化单条消息内容（用于展示历史消息）"""
    try:
        msg_type = getattr(msg, 'msg_type', 'unknown')
        create_time = getattr(msg, 'create_time', '')
        sender = getattr(msg, 'sender', None)
        body = getattr(msg, 'body', None)
        mentions = getattr(msg, 'mentions', None)
        
        time_str = format_timestamp(create_time) if create_time else ""
        sender_str = format_sender_info(sender) if sender else "未知"
        
        content_str = ""
        if body:
            content = getattr(body, 'content', '')
            if content:
                content_str = parse_message_body(msg_type, content)
                content_str = replace_mentions(content_str, mentions)
        
        if time_str:
            return f"[{time_str}] {sender_str}: {content_str}"
        else:
            return f"{sender_str}: {content_str}"
    except Exception as e:
        return f"[解析失败: {str(e)}]"


async def get_lark_messages(
    chat_id: Optional[str] = None,
    page_size: int = 20,
    page_token: Optional[str] = None,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    sort_type: str = "ByCreateTimeDesc",
) -> ToolResponse:
    """获取飞书群或私聊的历史消息

    Args:
        chat_id: 聊天 ID（群聊或单聊），如不传入则自动使用当前会话ID
        page_size: 每次返回的消息数量，默认 20，最大 50
        page_token: 分页令牌，首次请求不填
        start_time: 起始时间戳（秒），可选
        end_time: 结束时间戳（秒），可选
        sort_type: 排序方式，默认 ByCreateTimeDesc（按创建时间倒序）
    
    Returns:
        ToolResponse: 包含历史消息的响应
    """
    try:
        # 如果没有传入 chat_id，尝试从环境变量获取
        if not chat_id:
            chat_id = os.environ.get('CURRENT_CHAT_ID')
            if not chat_id:
                return ToolResponse(
                    content=[
                        TextBlock(
                            type="text",
                            text="错误：无法获取 chat_id，请确保在正确的聊天环境中"
                        ),
                    ],
                )
        
        client = _get_lark_client()
        
        # 构建请求，只有当 page_token 不为 None 且不为空字符串时才设置
        builder = (
            ListMessageRequest.builder()
            .container_id_type("chat")
            .container_id(chat_id)
            .page_size(page_size)
            .sort_type(sort_type)
        )
        
        if page_token:
            builder.page_token(page_token)
        
        if start_time:
            builder.start_time(start_time)
        
        if end_time:
            builder.end_time(end_time)
        
        request = builder.build()
        
        response = client.im.v1.message.list(request)
        
        if not response.success():
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"获取消息失败: {response.msg} (code: {response.code})"
                    ),
                ],
            )
        
        messages = response.data.items
        page_token = response.data.page_token
        has_more = response.data.has_more
        
        formatted_messages = []
        for msg in messages:
            formatted_msg = _format_message_content(msg)
            formatted_messages.append(formatted_msg)
        
        # 构建简洁的返回文本，不包含可能导致AI误解的提示
        result_text = "\n\n".join(formatted_messages)
        
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=result_text
                ),
            ],
        )
    except Exception as e:
        logger.error(f"获取飞书消息失败: {e}", exc_info=True)
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"获取消息时发生错误: {str(e)}"
                ),
            ],
        )
