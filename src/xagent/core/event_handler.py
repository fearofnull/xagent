"""
事件处理器模块

负责注册和分发飞书消息事件到对应的处理函数
"""
import lark_oapi as lark
from typing import Callable, Optional
import logging

logger = logging.getLogger(__name__)


class EventHandler:
    """事件处理器
    
    封装飞书 SDK 的 EventDispatcherHandler，提供消息事件注册和分发功能
    """
    
    def __init__(self, verification_token: str = "", encrypt_key: str = ""):
        """初始化事件处理器
        
        Args:
            verification_token: 验证令牌（可选）
            encrypt_key: 加密密钥（可选）
        """
        self.verification_token = verification_token
        self.encrypt_key = encrypt_key
        self._message_handler: Optional[Callable] = None
        self._dispatcher: Optional[lark.EventDispatcherHandler] = None
        
    def register_message_receive_handler(
        self, 
        handler: Callable
    ) -> None:
        """注册消息接收处理器
        
        Args:
            handler: 消息接收处理函数，接收 P2ImMessageReceiveV1 事件
        """
        self._message_handler = handler
        logger.info("Message receive handler registered")
        
    def build(self) -> lark.EventDispatcherHandler:
        """构建飞书 SDK 的事件分发器
        
        Returns:
            lark.EventDispatcherHandler: 飞书事件分发器实例
            
        Raises:
            ValueError: 如果未注册消息处理器
        """
        if self._message_handler is None:
            raise ValueError("Message handler must be registered before building")
            
        self._dispatcher = (
            lark.EventDispatcherHandler.builder(
                self.verification_token, 
                self.encrypt_key
            )
            .register_p2_im_message_receive_v1(self._message_handler)
            .build()
        )
        
        logger.info("Event dispatcher built successfully")
        return self._dispatcher
    
    def get_dispatcher(self) -> Optional[lark.EventDispatcherHandler]:
        """获取已构建的事件分发器
        
        Returns:
            Optional[lark.EventDispatcherHandler]: 事件分发器实例，如果未构建则返回 None
        """
        return self._dispatcher
