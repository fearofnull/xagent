"""
单元测试 - Emoji即时反馈功能

测试需求1: Emoji即时反馈
- 验证emoji反应是否立即发送
- 验证日志是否正确记录
- 验证API调用失败时不影响消息处理
"""
import asyncio
import logging
import pytest
from unittest.mock import Mock, AsyncMock, patch
from lark_oapi.api.im.v1 import (
    CreateMessageReactionRequest,
    CreateMessageReactionResponse
)

from src.xagent.core.message_handler import MessageHandler
from src.xagent.utils.cache import DeduplicationCache


class TestEmojiResponder:
    """Emoji响应器单元测试"""
    
    @pytest.fixture
    def mock_client(self):
        """创建模拟的飞书客户端"""
        client = Mock()
        client.im = Mock()
        client.im.v1 = Mock()
        client.im.v1.message_reaction = Mock()
        return client
    
    @pytest.fixture
    def dedup_cache(self):
        """创建去重缓存"""
        return DeduplicationCache(max_size=1000, ttl=300)
    
    @pytest.fixture
    def message_handler(self, mock_client, dedup_cache):
        """创建消息处理器实例"""
        return MessageHandler(mock_client, dedup_cache)
    
    @pytest.mark.asyncio
    async def test_emoji_default_is_eyes(self, message_handler):
        """测试默认emoji为👀"""
        # 验证默认emoji参数
        message_id = "test_msg_123"
        
        # 创建成功响应
        mock_response = Mock(spec=CreateMessageReactionResponse)
        mock_response.success.return_value = True
        
        # 模拟API调用
        message_handler.client.im.v1.message_reaction.create = Mock(return_value=mock_response)
        
        # 调用方法（不传emoji参数，使用默认值）
        result = await message_handler.send_emoji_reaction(message_id)
        
        # 验证结果
        assert result is True
        
        # 验证API被调用
        assert message_handler.client.im.v1.message_reaction.create.called
        
        # 获取调用参数
        call_args = message_handler.client.im.v1.message_reaction.create.call_args
        request = call_args[0][0]
        
        # 验证emoji类型为👀
        assert request.request_body.reaction_type.emoji_type == "👀"
    
    @pytest.mark.asyncio
    async def test_emoji_sent_successfully(self, message_handler, caplog):
        """测试emoji成功发送并记录日志"""
        message_id = "test_msg_456"
        
        # 创建成功响应
        mock_response = Mock(spec=CreateMessageReactionResponse)
        mock_response.success.return_value = True
        
        # 模拟API调用
        message_handler.client.im.v1.message_reaction.create = Mock(return_value=mock_response)
        
        # 捕获日志
        with caplog.at_level(logging.INFO):
            result = await message_handler.send_emoji_reaction(message_id)
        
        # 验证返回值
        assert result is True
        
        # 验证日志记录
        assert f"Emoji reaction sent for message {message_id}" in caplog.text
    
    @pytest.mark.asyncio
    async def test_emoji_api_failure_does_not_interrupt(self, message_handler, caplog):
        """测试API调用失败时不中断流程"""
        message_id = "test_msg_789"
        
        # 创建失败响应
        mock_response = Mock(spec=CreateMessageReactionResponse)
        mock_response.success.return_value = False
        mock_response.code = 500
        mock_response.msg = "Internal Server Error"
        mock_response.get_log_id.return_value = "log_123"
        
        # 模拟API调用
        message_handler.client.im.v1.message_reaction.create = Mock(return_value=mock_response)
        
        # 捕获日志
        with caplog.at_level(logging.WARNING):
            result = await message_handler.send_emoji_reaction(message_id)
        
        # 验证返回值为False但不抛出异常
        assert result is False
        
        # 验证警告日志记录
        assert "Failed to send emoji reaction" in caplog.text
        assert "code=500" in caplog.text
    
    @pytest.mark.asyncio
    async def test_emoji_exception_does_not_interrupt(self, message_handler, caplog):
        """测试异常时不中断流程"""
        message_id = "test_msg_abc"
        
        # 模拟API调用抛出异常
        message_handler.client.im.v1.message_reaction.create = Mock(
            side_effect=Exception("Network error")
        )
        
        # 捕获日志
        with caplog.at_level(logging.WARNING):
            result = await message_handler.send_emoji_reaction(message_id)
        
        # 验证返回值为False但不抛出异常
        assert result is False
        
        # 验证警告日志记录
        assert "Error sending emoji reaction" in caplog.text
        assert "Network error" in caplog.text
    
    @pytest.mark.asyncio
    async def test_emoji_timeout_handling(self, message_handler, caplog):
        """测试200ms超时处理"""
        message_id = "test_msg_timeout"
        
        # 模拟API调用超时（延迟300ms）
        async def slow_api_call(*args, **kwargs):
            await asyncio.sleep(0.3)
            mock_response = Mock(spec=CreateMessageReactionResponse)
            mock_response.success.return_value = True
            return mock_response
        
        # 使用asyncio.to_thread模拟同步API调用
        with patch('asyncio.to_thread', side_effect=slow_api_call):
            with caplog.at_level(logging.WARNING):
                result = await message_handler.send_emoji_reaction(message_id)
        
        # 验证超时返回False
        assert result is False
        
        # 验证超时日志记录
        assert "Emoji reaction timeout" in caplog.text
    
    @pytest.mark.asyncio
    async def test_emoji_custom_emoji(self, message_handler):
        """测试自定义emoji"""
        message_id = "test_msg_custom"
        custom_emoji = "🎉"
        
        # 创建成功响应
        mock_response = Mock(spec=CreateMessageReactionResponse)
        mock_response.success.return_value = True
        
        # 模拟API调用
        message_handler.client.im.v1.message_reaction.create = Mock(return_value=mock_response)
        
        # 调用方法（传入自定义emoji）
        result = await message_handler.send_emoji_reaction(message_id, emoji=custom_emoji)
        
        # 验证结果
        assert result is True
        
        # 获取调用参数
        call_args = message_handler.client.im.v1.message_reaction.create.call_args
        request = call_args[0][0]
        
        # 验证emoji类型为自定义emoji
        assert request.request_body.reaction_type.emoji_type == custom_emoji
    
    @pytest.mark.asyncio
    async def test_emoji_response_time_under_200ms(self, message_handler):
        """测试emoji响应时间在200ms以内（正常情况）"""
        message_id = "test_msg_fast"
        
        # 创建快速响应（50ms）
        async def fast_api_call(*args, **kwargs):
            await asyncio.sleep(0.05)
            mock_response = Mock(spec=CreateMessageReactionResponse)
            mock_response.success.return_value = True
            return mock_response
        
        # 使用asyncio.to_thread模拟同步API调用
        with patch('asyncio.to_thread', side_effect=fast_api_call):
            import time
            start_time = time.time()
            result = await message_handler.send_emoji_reaction(message_id)
            elapsed_time = time.time() - start_time
        
        # 验证成功
        assert result is True
        
        # 验证响应时间在200ms以内
        assert elapsed_time < 0.2


class TestEmojiIntegration:
    """Emoji集成测试 - 验证与消息处理流程的集成"""
    
    @pytest.mark.asyncio
    async def test_emoji_does_not_block_message_processing(self):
        """测试emoji发送不阻塞消息处理"""
        # 创建模拟客户端
        mock_client = Mock()
        mock_client.im = Mock()
        mock_client.im.v1 = Mock()
        mock_client.im.v1.message_reaction = Mock()
        
        # 创建慢速响应（模拟网络延迟）
        async def slow_api_call(*args, **kwargs):
            await asyncio.sleep(0.5)  # 500ms延迟
            mock_response = Mock(spec=CreateMessageReactionResponse)
            mock_response.success.return_value = True
            return mock_response
        
        mock_client.im.v1.message_reaction.create = Mock(return_value=None)
        
        # 创建消息处理器
        dedup_cache = DeduplicationCache(max_size=1000, ttl=300)
        message_handler = MessageHandler(mock_client, dedup_cache)
        
        # 模拟异步调用emoji发送（类似feishu_bot.py中的实现）
        message_id = "test_msg_async"
        
        # 使用asyncio.create_task异步调用
        with patch('asyncio.to_thread', side_effect=slow_api_call):
            task = asyncio.create_task(
                message_handler.send_emoji_reaction(message_id)
            )
            
            # 立即继续执行（不等待emoji发送完成）
            import time
            start_time = time.time()
            
            # 模拟后续消息处理
            await asyncio.sleep(0.01)  # 10ms的后续处理
            
            elapsed_time = time.time() - start_time
        
        # 验证后续处理没有被阻塞（应该在50ms内完成）
        assert elapsed_time < 0.1
        
        # 清理任务
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


# Feature: unified-api-provider-system, Property 1: Emoji反应发送
# 对于任何接收到的用户消息，系统应该调用飞书API发送emoji反应
@pytest.mark.asyncio
async def test_property_emoji_sent_for_any_message():
    """属性测试: 对于任何接收到的用户消息，系统应该调用飞书API发送emoji反应"""
    # 创建模拟客户端
    mock_client = Mock()
    mock_client.im = Mock()
    mock_client.im.v1 = Mock()
    mock_client.im.v1.message_reaction = Mock()
    
    # 创建成功响应
    mock_response = Mock(spec=CreateMessageReactionResponse)
    mock_response.success.return_value = True
    mock_client.im.v1.message_reaction.create = Mock(return_value=mock_response)
    
    # 创建消息处理器
    dedup_cache = DeduplicationCache(max_size=1000, ttl=300)
    message_handler = MessageHandler(mock_client, dedup_cache)
    
    # 测试多个不同的消息ID
    test_message_ids = [
        "msg_001",
        "msg_abc_123",
        "om_1234567890abcdef",
        "test_message_with_long_id_12345678901234567890"
    ]
    
    for message_id in test_message_ids:
        # 重置mock
        mock_client.im.v1.message_reaction.create.reset_mock()
        
        # 调用方法
        result = await message_handler.send_emoji_reaction(message_id)
        
        # 验证API被调用
        assert mock_client.im.v1.message_reaction.create.called, \
            f"API should be called for message {message_id}"
        
        # 验证返回成功
        assert result is True, \
            f"Should return True for message {message_id}"


# Feature: unified-api-provider-system, Property 2: Emoji发送失败不中断流程
# 对于任何emoji发送失败的情况，系统应该记录错误日志但继续执行后续的消息处理流程
@pytest.mark.asyncio
async def test_property_emoji_failure_does_not_interrupt():
    """属性测试: emoji发送失败不中断流程"""
    # 创建模拟客户端
    mock_client = Mock()
    mock_client.im = Mock()
    mock_client.im.v1 = Mock()
    mock_client.im.v1.message_reaction = Mock()
    
    # 创建消息处理器
    dedup_cache = DeduplicationCache(max_size=1000, ttl=300)
    message_handler = MessageHandler(mock_client, dedup_cache)
    
    # 测试各种失败场景
    failure_scenarios = [
        # API返回失败
        {
            "name": "API failure",
            "setup": lambda: Mock(
                return_value=Mock(
                    success=Mock(return_value=False),
                    code=500,
                    msg="Internal Server Error",
                    get_log_id=Mock(return_value="log_123")
                )
            )
        },
        # 抛出异常
        {
            "name": "Exception",
            "setup": lambda: Mock(side_effect=Exception("Network error"))
        },
        # 超时
        {
            "name": "Timeout",
            "setup": lambda: Mock(side_effect=asyncio.TimeoutError())
        }
    ]
    
    for scenario in failure_scenarios:
        # 设置失败场景
        mock_client.im.v1.message_reaction.create = scenario["setup"]()
        
        # 调用方法（不应该抛出异常）
        try:
            result = await message_handler.send_emoji_reaction("test_msg")
            
            # 验证返回False但不抛出异常
            assert result is False, \
                f"Should return False for scenario: {scenario['name']}"
            
        except Exception as e:
            pytest.fail(
                f"Should not raise exception for scenario: {scenario['name']}, "
                f"but got: {type(e).__name__}: {e}"
            )
