# -*- coding: utf-8 -*-
"""飞书消息历史读取工具"""

import logging
from typing import Optional

from agentscope.tool import ToolResponse
from agentscope.message import TextBlock

from lark_oapi import Client as LarkClient
from lark_oapi.api.im.v1 import ListMessageRequest

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
    """格式化单条消息内容"""
    try:
        msg_type = getattr(msg, 'msg_type', 'unknown')
        body = getattr(msg, 'body', {}) or {}
        
        if isinstance(body, dict):
            content = body.get('content', '')
        else:
            content = str(body)
        
        sender = getattr(msg, 'sender', {}) or {}
        if isinstance(sender, dict):
            sender_id = sender.get('id', 'unknown')
            sender_type = sender.get('sender_type', 'unknown')
        else:
            sender_id = 'unknown'
            sender_type = 'unknown'
        
        create_time = getattr(msg, 'create_time', 'unknown')
        
        if msg_type == 'text':
            import json
            try:
                content_obj = json.loads(content)
                text = content_obj.get('text', content)
            except (json.JSONDecodeError, TypeError):
                text = content
            return f"[{create_time}] {sender_id} ({sender_type}): {text}"
        else:
            return f"[{create_time}] {sender_id} ({sender_type}) [{msg_type}]: {content[:200]}"
    except Exception as e:
        return f"[解析失败] {str(e)}"


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
        sort_type: 排序方式，"ByCreateTimeAsc" 或 "ByCreateTimeDesc"

    Returns:
        ToolResponse: 包含消息列表或错误信息
    """
    # 如果没有提供 chat_id，尝试从环境变量获取
    if not chat_id:
        import os
        chat_id = os.environ.get('CURRENT_CHAT_ID')
        if not chat_id:
            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text="错误: 无法获取当前聊天ID。请确保在飞书会话中调用此工具，或手动提供 chat_id 参数。"
                )]
            )
    
    if page_size < 1 or page_size > 50:
        return ToolResponse(
            content=[TextBlock(
                type="text",
                text="错误: page_size 必须在 1-50 之间"
            )]
        )

    if sort_type not in ("ByCreateTimeAsc", "ByCreateTimeDesc"):
        return ToolResponse(
            content=[TextBlock(
                type="text",
                text="错误: sort_type 必须是 'ByCreateTimeAsc' 或 'ByCreateTimeDesc'"
            )]
        )

    try:
        client = _get_lark_client()

        request_builder = (
            ListMessageRequest.builder()
            .container_id_type("chat")
            .container_id(chat_id)
            .page_size(page_size)
            .sort_type(sort_type)
        )

        if page_token:
            request_builder.page_token(page_token)
        if start_time:
            request_builder.start_time(str(start_time))
        if end_time:
            request_builder.end_time(str(end_time))

        request = request_builder.build()
        response = client.im.v1.message.list(request)

        if not response.success():
            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=f"获取消息失败: code={response.code}, msg={response.msg}"
                )]
            )

        data = response.data
        messages = data.items if data else []

        if not messages:
            return ToolResponse(
                content=[TextBlock(type="text", text="没有找到消息记录")]
            )

        formatted_messages = [_format_message_content(msg) for msg in messages]
        result_text = f"共获取 {len(messages)} 条消息:\n\n" + "\n\n".join(formatted_messages)

        if hasattr(data, 'page_token') and data.page_token and hasattr(data, 'has_more') and data.has_more:
            result_text += f"\n\n⚠️ 还有更多消息，请使用 page_token=\"{data.page_token}\" 继续获取"

        return ToolResponse(content=[TextBlock(type="text", text=result_text)])

    except Exception as e:
        logger.error(f"获取飞书消息失败: {e}")
        return ToolResponse(
            content=[TextBlock(type="text", text=f"获取消息失败: {str(e)}")]
        )