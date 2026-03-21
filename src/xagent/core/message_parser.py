"""
消息解析器模块

负责解析飞书消息内容，支持 21 种消息类型

官方文档参考：
https://open.feishu.cn/document/server-docs/im-v1/message-content-description/message_content
"""

import json
import re
import logging
from typing import Optional, List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


# ============ 高优先级消息类型解析函数 ============

def parse_text_content(content: str) -> str:
    """解析文本消息 content JSON
    
    飞书官方文档结构：
    {"text": "@_user_1 文本消息"}
    
    特殊处理：
    - 超链接格式：[超链接文本](超链接地址)
    - 邮箱超链接：[邮箱文本](mailto:邮箱地址)
    - @提及：@_user_X 形式
    
    输入: '{"text": "你好"}'
    输出: "你好"
    
    注意：不清理 @提及，保留原始文本
    """
    try:
        data = json.loads(content)
        return data.get("text", "")
    except (json.JSONDecodeError, TypeError):
        return ""


def parse_post_content(content: str) -> str:
    """解析富文本消息 content JSON
    
    飞书官方文档结构：
    {
      "title":"我是一个标题",
      "content":[
        [{"tag":"text","text":"第一行 :"}],
        [{"tag":"img","image_key":"img_xxx"}],
        [{"tag":"media","file_key":"file_xxx"}],
        [{"tag":"emotion","emoji_type":"SMILE"}],
        [{"tag":"hr"}],
        [{"tag":"code_block","language":"GO","text":"func main() {}"}]
      ]
    }
    
    支持的标签：
    - text：文本
    - a：超链接
    - at：@提及
    - img：图片
    - media：视频
    - emotion：表情
    - hr：分割线
    - code_block：代码块
    
    输入: '{"title":"标题","content":[[{"tag":"text","text":"内容"}]]}'
    输出: "标题 | 内容"
    """
    content_parts = []
    try:
        def _clean_text(value: str) -> str:
            if not isinstance(value, str):
                return ""
            return re.sub(r"\s+", " ", value).strip()
        
        def _select_post_body(node):
            if not isinstance(node, dict):
                return node
            if "post" in node and isinstance(node["post"], dict):
                node = node["post"]
            for lang in ("zh_cn", "en_us"):
                if lang in node and isinstance(node[lang], dict):
                    return node[lang]
            for value in node.values():
                if isinstance(value, dict) and ("content" in value or "title" in value):
                    return value
            return node
        
        def _post_item_to_text(item) -> str:
            if isinstance(item, str):
                return _clean_text(item)
            if not isinstance(item, dict):
                return ""
            if "elements" in item and isinstance(item["elements"], list):
                parts = [_post_item_to_text(sub) for sub in item["elements"]]
                return _clean_text("".join(parts))
            tag = item.get("tag", "")
            if tag == "text":
                return _clean_text(item.get("text") or item.get("content") or "")
            if tag == "a":
                text_val = _clean_text(item.get("text") or item.get("content") or "")
                href = _clean_text(item.get("href") or "")
                if text_val and href:
                    return f"{text_val} ({href})"
                return text_val or href
            if tag == "at":
                name = item.get("user_name") or item.get("user_id") or item.get("name") or ""
                name = _clean_text(name)
                return f"@{name}" if name else "@"
            if tag == "img":
                key = item.get("image_key") or item.get("img_key") or ""
                key = _clean_text(key)
                return f"[图片:{key}]" if key else "[图片]"
            if tag in ("emotion", "emoji"):
                emoji = _clean_text(item.get("emoji_type") or item.get("emoji") or "")
                return f":{emoji}:" if emoji else ""
            if tag == "media":
                file_key = item.get("file_key", "")
                return f"[视频:{file_key}]" if file_key else "[视频]"
            if tag == "code_block":
                code = item.get("text", "")
                lang = item.get("language", "")
                if code:
                    code = code.replace("\n", " ")
                    if lang:
                        return f"[代码块:{lang}] {code}"
                    return f"[代码块] {code}"
                return "[代码块]"
            if tag == "hr":
                return "---"
            if "text" in item and isinstance(item["text"], str):
                return _clean_text(item["text"])
            if "content" in item and isinstance(item["content"], str):
                return _clean_text(item["content"])
            return ""
        
        post = json.loads(content)
        post = _select_post_body(post)
        
        if isinstance(post, dict) and "title" in post:
            title = _clean_text(post.get("title", ""))
            if title:
                content_parts.append(title)
        
        if isinstance(post, dict) and "content" in post:
            post_content = post.get("content")
            if isinstance(post_content, list):
                for row in post_content:
                    if isinstance(row, list):
                        row_text = "".join(_post_item_to_text(item) for item in row)
                        row_text = _clean_text(row_text)
                        if row_text:
                            content_parts.append(row_text)
                    elif isinstance(row, dict):
                        row_text = _post_item_to_text(row)
                        row_text = _clean_text(row_text)
                        if row_text:
                            content_parts.append(row_text)
                    elif isinstance(row, str):
                        row_text = _clean_text(row)
                        if row_text:
                            content_parts.append(row_text)
            elif isinstance(post_content, str):
                text_val = _clean_text(post_content)
                if text_val:
                    content_parts.append(text_val)
        
        if content_parts:
            result = " | ".join(content_parts)
            if len(result) > 2000:
                result = result[:2000] + "..."
            return result
        return ""
    except Exception as e:
        logger.warning(f"Failed to parse post content: {e}")
        return ""


def parse_image_content(content: str) -> str:
    """解析图片消息 content JSON
    
    飞书官方文档结构：
    {"image_key": "img_4adb3cc3-902b-4187-b0f1-842f67fd017g"}
    
    输入: '{"image_key": "img_xxx"}'
    输出: "[图片: img_xxx]"
    """
    try:
        data = json.loads(content)
        image_key = data.get("image_key", "")
        if image_key:
            return f"[图片: {image_key}]"
        return "[图片]"
    except (json.JSONDecodeError, TypeError):
        return "[图片]"


def parse_card_content(content: str) -> str:
    """解析卡片消息 content JSON
    
    飞书官方文档结构：
    {
      "config": {"wide_screen_mode": true},
      "header": {"title": {"content": "卡片标题", "tag": "plain_text"}},
      "elements": [
        {"tag": "div", "text": {"content": "卡片内容", "tag": "plain_text"}}
      ]
    }
    
    支持的元素：
    - button：按钮
    - text：文本
    - markdown：Markdown 文本
    - div：容器
    - a：超链接
    - at：@提及
    - hr：分割线
    - note：注释
    - select_static：静态选择器
    - overflow：溢出菜单
    - date_picker：日期选择器
    
    输入: '{"header":{"title":{"content":"标题"}},"elements":[...]}'
    输出: "标题 | 内容"
    """
    content_parts = []
    try:
        card = json.loads(content)
        
        def _clean_text(value: str) -> str:
            if not isinstance(value, str):
                return ""
            return re.sub(r'\s+', ' ', value).strip()
        
        def _extract_element_content(element: dict):
            if not isinstance(element, dict):
                return
            
            tag = element.get("tag", "")
            
            if tag == "text":
                text = element.get("text", "")
                if text:
                    content_parts.append(_clean_text(text))
                elif "content" in element:
                    content_parts.append(_clean_text(element["content"]))
            
            elif tag == "markdown":
                if "content" in element:
                    content_parts.append(_clean_text(element["content"]))
            
            elif tag == "div":
                if "text" in element:
                    text_obj = element["text"]
                    if isinstance(text_obj, dict) and "content" in text_obj:
                        content_parts.append(_clean_text(text_obj["content"]))
                if "fields" in element:
                    for field in element["fields"]:
                        if isinstance(field, dict) and "text" in field:
                            text_obj = field["text"]
                            if isinstance(text_obj, dict) and "content" in text_obj:
                                content_parts.append(_clean_text(text_obj["content"]))
                if "elements" in element:
                    for nested in element["elements"]:
                        _extract_element_content(nested)
            
            elif tag == "action":
                if "actions" in element:
                    for action in element["actions"]:
                        if isinstance(action, dict):
                            _extract_element_content(action)
            
            elif tag == "button":
                text = element.get("text", "")
                if isinstance(text, str):
                    content_parts.append(_clean_text(text))
                elif isinstance(text, dict) and "content" in text:
                    content_parts.append(_clean_text(text["content"]))
            
            elif tag == "note":
                if "elements" in element:
                    for nested in element["elements"]:
                        _extract_element_content(nested)
            
            elif tag == "column_set":
                if "columns" in element:
                    for column in element["columns"]:
                        if isinstance(column, dict) and "elements" in column:
                            for nested in column["elements"]:
                                _extract_element_content(nested)
            
            elif tag == "hr":
                pass
        
        if "title" in card:
            title = card["title"]
            if isinstance(title, str):
                content_parts.append(_clean_text(title))
        
        if "header" in card:
            header = card["header"]
            if "title" in header and "content" in header["title"]:
                content_parts.append(_clean_text(header["title"]["content"]))
        
        if "elements" in card:
            for element in card["elements"]:
                if isinstance(element, list):
                    for sub_element in element:
                        _extract_element_content(sub_element)
                else:
                    _extract_element_content(element)
        
        if content_parts:
            result = " | ".join(content_parts)
            if len(result) > 2000:
                result = result[:2000] + "..."
            return result
        return ""
    except Exception as e:
        logger.warning(f"Failed to parse card content: {e}")
        return ""


# ============ 中优先级消息类型解析函数 ============

def parse_file_content(content: str) -> str:
    """解析文件消息 content JSON
    
    飞书官方文档结构：
    {"file_key": "file_xxx", "file_name": "report.pdf"}
    
    输入: '{"file_key": "file_xxx", "file_name": "report.pdf"}'
    输出: "[文件: report.pdf]"
    """
    try:
        data = json.loads(content)
        file_name = data.get("file_name", "")
        if file_name:
            return f"[文件: {file_name}]"
        return "[文件]"
    except (json.JSONDecodeError, TypeError):
        return "[文件]"


def parse_audio_content(content: str) -> str:
    """解析音频消息 content JSON
    
    飞书官方文档结构：
    {"file_key": "file_xxx", "duration": 60000}
    
    输入: '{"file_key": "file_xxx", "duration": 60000}'
    输出: "[音频: 60秒]"
    """
    try:
        data = json.loads(content)
        duration = data.get("duration", 0)
        if duration:
            seconds = duration // 1000
            return f"[音频: {seconds}秒]"
        return "[音频]"
    except (json.JSONDecodeError, TypeError):
        return "[音频]"


def parse_media_content(content: str) -> str:
    """解析视频消息 content JSON
    
    飞书官方文档结构：
    {"file_key": "file_xxx", "file_name": "video.mp4", "duration": 60000}
    
    输入: '{"file_key": "file_xxx", "file_name": "video.mp4", "duration": 60000}'
    输出: "[视频: video.mp4, 60秒]"
    """
    try:
        data = json.loads(content)
        file_name = data.get("file_name", "")
        duration = data.get("duration", 0)
        
        parts = []
        if file_name:
            parts.append(file_name)
        if duration:
            seconds = duration // 1000
            parts.append(f"{seconds}秒")
        
        if parts:
            return f"[视频: {', '.join(parts)}]"
        return "[视频]"
    except (json.JSONDecodeError, TypeError):
        return "[视频]"


def parse_calendar_content(content: str, calendar_type: str = "calendar") -> str:
    """解析日程消息 content JSON
    
    飞书官方文档结构：
    {"event_id": "xxx", "title": "会议", "start_time": 1234567890, "end_time": 1234571490}
    
    输入: '{"title": "会议", "start_time": 1234567890, "end_time": 1234571490}'
    输出: "[日程: 会议, 2024-07-29 10:00-11:00]"
    """
    try:
        data = json.loads(content)
        title = data.get("title", "")
        start_time = data.get("start_time", 0)
        end_time = data.get("end_time", 0)
        
        parts = []
        if title:
            parts.append(title)
        
        if start_time and end_time:
            start_dt = datetime.fromtimestamp(start_time / 1000)
            end_dt = datetime.fromtimestamp(end_time / 1000)
            time_str = f"{start_dt.strftime('%Y-%m-%d %H:%M')}-{end_dt.strftime('%H:%M')}"
            parts.append(time_str)
        
        if parts:
            type_name = {
                "share_calendar_event": "日程分享",
                "calendar": "日程邀请",
                "general_calendar": "日程"
            }.get(calendar_type, "日程")
            return f"[{type_name}: {', '.join(parts)}]"
        return "[日程]"
    except (json.JSONDecodeError, TypeError):
        return "[日程]"


def parse_share_chat_content(content: str) -> str:
    """解析群名片消息 content JSON
    
    飞书官方文档结构：
    {"chat_id": "oc_xxx", "name": "群聊名称"}
    
    输入: '{"chat_id": "oc_xxx", "name": "群聊名称"}'
    输出: "[群名片: 群聊名称]"
    """
    try:
        data = json.loads(content)
        name = data.get("name", "")
        if name:
            return f"[群名片: {name}]"
        return "[群名片]"
    except (json.JSONDecodeError, TypeError):
        return "[群名片]"


def parse_share_user_content(content: str) -> str:
    """解析个人名片消息 content JSON
    
    飞书官方文档结构：
    {"user_id": "ou_xxx", "name": "用户名称"}
    
    输入: '{"user_id": "ou_xxx", "name": "用户名称"}'
    输出: "[个人名片: 用户名称]"
    """
    try:
        data = json.loads(content)
        name = data.get("name", "")
        if name:
            return f"[个人名片: {name}]"
        return "[个人名片]"
    except (json.JSONDecodeError, TypeError):
        return "[个人名片]"


def parse_system_content(content: str) -> str:
    """解析系统消息 content JSON
    
    飞书官方文档结构：
    {"template": "add_member", "content": "张三 邀请 李四 加入了群聊"}
    
    输入: '{"template": "add_member", "content": "张三 邀请 李四 加入了群聊"}'
    输出: "张三 邀请 李四 加入了群聊"
    """
    try:
        data = json.loads(content)
        text = data.get("content", "")
        if text:
            return text
        return "[系统消息]"
    except (json.JSONDecodeError, TypeError):
        return "[系统消息]"


def parse_todo_content(content: str) -> str:
    """解析任务消息 content JSON
    
    飞书官方文档结构：
    {"title": {"tag": "text", "text": "任务标题"}, "due_time": 1234567890}
    
    输入: '{"title": {"tag": "text", "text": "任务标题"}, "due_time": 1234567890}'
    输出: "[任务: 任务标题, 截止: 2024-07-29 10:00]"
    """
    try:
        data = json.loads(content)
        
        title = ""
        title_obj = data.get("title", {})
        if isinstance(title_obj, dict):
            title = title_obj.get("text", "")
        
        due_time = data.get("due_time", 0)
        
        parts = []
        if title:
            parts.append(title)
        
        if due_time:
            due_dt = datetime.fromtimestamp(due_time / 1000)
            parts.append(f"截止: {due_dt.strftime('%Y-%m-%d %H:%M')}")
        
        if parts:
            return f"[任务: {', '.join(parts)}]"
        return "[任务]"
    except (json.JSONDecodeError, TypeError):
        return "[任务]"


def parse_vote_content(content: str) -> str:
    """解析投票消息 content JSON
    
    飞书官方文档结构：
    {"title": "投票主题", "options": [{"text": "选项1"}, {"text": "选项2"}]}
    
    输入: '{"title": "投票主题", "options": [{"text": "选项1"}, {"text": "选项2"}]}'
    输出: "[投票: 投票主题, 选项: 选项1, 选项2]"
    """
    try:
        data = json.loads(content)
        title = data.get("title", "")
        options = data.get("options", [])
        
        parts = []
        if title:
            parts.append(title)
        
        if options:
            option_texts = [opt.get("text", "") for opt in options if opt.get("text")]
            if option_texts:
                parts.append(f"选项: {', '.join(option_texts)}")
        
        if parts:
            return f"[投票: {', '.join(parts)}]"
        return "[投票]"
    except (json.JSONDecodeError, TypeError):
        return "[投票]"


def parse_merge_forward_content(content: str) -> str:
    """解析合并转发消息 content JSON
    
    飞书官方文档结构：
    {"content": "Merged and Forwarded Message"}
    
    注意：消息内容固定为 "Merged and Forwarded Message"
    需要调用获取指定消息的内容接口，获取合并转发消息中的子消息
    
    输入: '{"content": "Merged and Forwarded Message"}'
    输出: "[合并转发消息]"
    """
    try:
        data = json.loads(content)
        return "[合并转发消息]"
    except (json.JSONDecodeError, TypeError):
        return "[合并转发消息]"


# ============ 低优先级消息类型解析函数 ============

def parse_folder_content(content: str) -> str:
    """解析文件夹消息 content JSON
    
    飞书官方文档结构：
    {"folder_token": "xxx", "name": "文件夹名称"}
    
    输入: '{"folder_token": "xxx", "name": "我的文档"}'
    输出: "[文件夹: 我的文档]"
    """
    try:
        data = json.loads(content)
        name = data.get("name", "")
        if name:
            return f"[文件夹: {name}]"
        return "[文件夹]"
    except (json.JSONDecodeError, TypeError):
        return "[文件夹]"


def parse_sticker_content(content: str) -> str:
    """解析表情包消息 content JSON
    
    飞书官方文档结构：
    {"file_key": "xxx", "type": "static"}
    
    输入: '{"file_key": "xxx", "type": "static"}'
    输出: "[表情包]"
    """
    try:
        data = json.loads(content)
        return "[表情包]"
    except (json.JSONDecodeError, TypeError):
        return "[表情包]"


def parse_hongbao_content(content: str) -> str:
    """解析红包消息 content JSON
    
    飞书官方文档结构：
    {"text": "恭喜发财，大吉大利"}
    
    输入: '{"text": "恭喜发财，大吉大利"}'
    输出: "[红包: 恭喜发财，大吉大利]"
    """
    try:
        data = json.loads(content)
        text = data.get("text", "")
        if text:
            return f"[红包: {text}]"
        return "[红包]"
    except (json.JSONDecodeError, TypeError):
        return "[红包]"


def parse_location_content(content: str) -> str:
    """解析位置消息 content JSON
    
    飞书官方文档结构：
    {"name": "位置名称", "longitude": 116.397, "latitude": 39.918}
    
    输入: '{"name": "北京市朝阳区", "longitude": 116.397, "latitude": 39.918}'
    输出: "[位置: 北京市朝阳区]"
    """
    try:
        data = json.loads(content)
        name = data.get("name", "")
        if name:
            return f"[位置: {name}]"
        return "[位置]"
    except (json.JSONDecodeError, TypeError):
        return "[位置]"


def parse_video_chat_content(content: str) -> str:
    """解析视频通话消息 content JSON
    
    飞书官方文档结构：
    {"subject": "会议主题", "start_time": 1234567890}
    
    输入: '{"subject": "产品评审", "start_time": 1234567890}'
    输出: "[视频通话: 产品评审]"
    """
    try:
        data = json.loads(content)
        subject = data.get("subject", "")
        if subject:
            return f"[视频通话: {subject}]"
        return "[视频通话]"
    except (json.JSONDecodeError, TypeError):
        return "[视频通话]"


# ============ @提及处理函数 ============

def replace_mentions(text: str, mentions: Optional[List[Dict]]) -> str:
    """将 @_user_X 占位符替换为真实用户名
    
    飞书消息中的 @提及有两种表示：
    1. 消息内容中的占位符："@_user_1 @_user_2 帮我协调"
    2. mentions 字段中的真实信息：[{"name": "张三"}, {"name": "李四"}]
    
    替换策略：
    - 如果有 mentions 且 name 不为空 → 替换为 @用户名
    - 如果没有 mentions 或 name 为空 → 保留占位符（不清理）
    
    示例：
    - 有 mentions："@_user_1 @_user_2 帮我协调" → "@张三 @李四 帮我协调"
    - 无 mentions："@_user_1 @_user_2 帮我协调" → "@_user_1 @_user_2 帮我协调"
    
    Args:
        text: 消息文本（包含 @_user_X 占位符）
        mentions: 消息对象的 mentions 字段
    
    Returns:
        替换后的文本
    """
    if not mentions:
        return text
    
    mention_map = {}
    for i, mention in enumerate(mentions, start=1):
        placeholder = f"@_user_{i}"
        
        name = ""
        if isinstance(mention, dict):
            name = mention.get("name", "")
        elif hasattr(mention, 'name'):
            name = mention.name
        
        if name:
            mention_map[placeholder] = f"@{name}"
    
    for placeholder, user_mention in mention_map.items():
        text = text.replace(placeholder, user_mention)
    
    return text


# ============ 格式化函数 ============

def format_timestamp(timestamp_ms: str) -> str:
    """格式化时间戳
    
    Args:
        timestamp_ms: 毫秒级时间戳字符串
    
    Returns:
        格式化后的时间字符串，如 "2024-07-29 15:27:05"
    """
    try:
        timestamp = int(timestamp_ms) / 1000
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return ""


def format_sender_info(sender) -> str:
    """格式化发送者信息
    
    Args:
        sender: 发送者信息（字典或对象）
    
    Returns:
        格式化后的发送者信息，如 "用户(ou_xxx)" 或 "机器人(cli_xxx)"
    """
    if not sender:
        return "未知"
    
    # 支持字典和对象两种类型
    if isinstance(sender, dict):
        sender_type = sender.get("sender_type", "")
        sender_id = sender.get("id", "")
    else:
        # 对象类型，使用 getattr
        sender_type = getattr(sender, "sender_type", "")
        sender_id = getattr(sender, "id", "")
    
    if sender_type == "app":
        return f"机器人({sender_id[:10]}...)"
    elif sender_type == "user":
        return f"用户({sender_id[:10]}...)"
    else:
        return f"发送者({sender_id[:10]}...)"


# ============ 组合解析函数 ============

def parse_message_body(msg_type: str, content: str) -> str:
    """根据消息类型解析 content
    
    自动路由到对应的解析函数
    
    Args:
        msg_type: 消息类型（text/post/image/file/...）
        content: 消息内容 JSON 字符串
    
    Returns:
        解析后的文本内容
    """
    parsers = {
        "text": parse_text_content,
        "post": parse_post_content,
        "image": parse_image_content,
        "file": parse_file_content,
        "folder": parse_folder_content,
        "audio": parse_audio_content,
        "media": parse_media_content,
        "sticker": parse_sticker_content,
        "interactive": parse_card_content,
        "hongbao": parse_hongbao_content,
        "share_calendar_event": lambda c: parse_calendar_content(c, "share_calendar_event"),
        "calendar": lambda c: parse_calendar_content(c, "calendar"),
        "general_calendar": lambda c: parse_calendar_content(c, "general_calendar"),
        "share_chat": parse_share_chat_content,
        "share_user": parse_share_user_content,
        "system": parse_system_content,
        "location": parse_location_content,
        "video_chat": parse_video_chat_content,
        "todo": parse_todo_content,
        "vote": parse_vote_content,
        "merge_forward": parse_merge_forward_content,
    }
    
    parser = parsers.get(msg_type)
    if parser:
        return parser(content)
    
    return f"[未知消息类型: {msg_type}]"
