# -*- coding: utf-8 -*-
"""测试消息解析模块"""

import json
import pytest
from src.xagent.core.message_parser import (
    parse_message_body,
    parse_text_content,
    parse_post_content,
    parse_image_content,
    parse_card_content,
    replace_mentions,
    format_timestamp,
    format_sender_info,
)


class TestParseTextContent:
    """测试文本消息解析"""
    
    def test_simple_text(self):
        """测试简单文本"""
        content = json.dumps({"text": "你好，世界"})
        result = parse_text_content(content)
        assert result == "你好，世界"
    
    def test_empty_text(self):
        """测试空文本"""
        content = json.dumps({"text": ""})
        result = parse_text_content(content)
        assert result == ""
    
    def test_text_with_mentions(self):
        """测试带@提及的文本"""
        content = json.dumps({"text": "@_user_1 @_user_2 帮我协调"})
        result = parse_text_content(content)
        assert "@_user_1" in result
        assert "@_user_2" in result


class TestReplaceMentions:
    """测试@提及替换"""
    
    def test_replace_with_names(self):
        """测试用用户名替换"""
        text = "@_user_1 @_user_2 帮我协调"
        mentions = [
            {"name": "张三"},
            {"name": "李四"}
        ]
        result = replace_mentions(text, mentions)
        assert result == "@张三 @李四 帮我协调"
    
    def test_no_mentions(self):
        """测试无mentions字段"""
        text = "@_user_1 @_user_2 帮我协调"
        result = replace_mentions(text, None)
        assert result == "@_user_1 @_user_2 帮我协调"
    
    def test_empty_mentions(self):
        """测试空mentions列表"""
        text = "@_user_1 @_user_2 帮我协调"
        result = replace_mentions(text, [])
        assert result == "@_user_1 @_user_2 帮我协调"
    
    def test_partial_mentions(self):
        """测试部分mentions有名字"""
        text = "@_user_1 @_user_2 帮我协调"
        mentions = [
            {"name": "张三"},
            {"name": ""}  # 空名字
        ]
        result = replace_mentions(text, mentions)
        assert result == "@张三 @_user_2 帮我协调"


class TestParsePostContent:
    """测试富文本消息解析"""
    
    def test_simple_post(self):
        """测试简单富文本"""
        content = json.dumps({
            "zh_cn": {
                "title": "标题",
                "content": [
                    [{"tag": "text", "text": "第一行"}],
                    [{"tag": "text", "text": "第二行"}]
                ]
            }
        })
        result = parse_post_content(content)
        assert "标题" in result
        assert "第一行" in result
        assert "第二行" in result
    
    def test_post_with_link(self):
        """测试带链接的富文本"""
        content = json.dumps({
            "zh_cn": {
                "content": [
                    [{"tag": "text", "text": "点击"}, {"tag": "a", "text": "这里", "href": "https://example.com"}]
                ]
            }
        })
        result = parse_post_content(content)
        assert "点击" in result
        assert "这里" in result


class TestParseImageContent:
    """测试图片消息解析"""
    
    def test_image_content(self):
        """测试图片消息"""
        content = json.dumps({"image_key": "img_v2_xxx"})
        result = parse_image_content(content)
        assert "[图片:" in result
        assert "img_v2_xxx" in result
    
    def test_image_without_key(self):
        """测试无key的图片消息"""
        content = json.dumps({})
        result = parse_image_content(content)
        assert result == "[图片]"


class TestParseCardContent:
    """测试卡片消息解析"""
    
    def test_simple_card(self):
        """测试简单卡片"""
        content = json.dumps({
            "title": "卡片标题",
            "elements": [
                {"tag": "text", "text": "卡片内容"}
            ]
        })
        result = parse_card_content(content)
        assert "卡片标题" in result
        assert "卡片内容" in result
    
    def test_card_with_header(self):
        """测试带header的卡片"""
        content = json.dumps({
            "header": {
                "title": {
                    "content": "标题"
                }
            },
            "elements": [
                {"tag": "div", "text": {"content": "内容"}}
            ]
        })
        result = parse_card_content(content)
        assert "标题" in result
    
    def test_card_with_button(self):
        """测试带按钮的卡片"""
        content = json.dumps({
            "elements": [
                {"tag": "action", "actions": [{"tag": "button", "text": "点击我"}]}
            ]
        })
        result = parse_card_content(content)
        assert "点击我" in result


class TestParseMessageBody:
    """测试消息体路由"""
    
    def test_route_text(self):
        """测试文本消息路由"""
        content = json.dumps({"text": "测试文本"})
        result = parse_message_body("text", content)
        assert result == "测试文本"
    
    def test_route_image(self):
        """测试图片消息路由"""
        content = json.dumps({"image_key": "img_xxx"})
        result = parse_message_body("image", content)
        assert "[图片:" in result
    
    def test_route_unknown(self):
        """测试未知消息类型"""
        content = json.dumps({})
        result = parse_message_body("unknown_type", content)
        assert "未知消息类型" in result


class TestFormatTimestamp:
    """测试时间戳格式化"""
    
    def test_valid_timestamp(self):
        """测试有效时间戳（毫秒级）"""
        result = format_timestamp("1705300200000")
        assert "2024" in result
    
    def test_empty_timestamp(self):
        """测试空时间戳"""
        result = format_timestamp("")
        assert result == ""
    
    def test_none_timestamp(self):
        """测试None时间戳"""
        result = format_timestamp(None)
        assert result == ""


class TestFormatSenderInfo:
    """测试发送者信息格式化"""
    
    def test_dict_sender(self):
        """测试字典格式发送者"""
        sender = {"id": "ou_xxx", "sender_type": "user"}
        result = format_sender_info(sender)
        assert "ou_xxx" in result
        assert "用户" in result
    
    def test_empty_sender(self):
        """测试空发送者"""
        result = format_sender_info({})
        assert result == "未知"
    
    def test_none_sender(self):
        """测试None发送者"""
        result = format_sender_info(None)
        assert result == "未知"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
