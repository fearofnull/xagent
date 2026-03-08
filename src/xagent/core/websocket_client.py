"""
WebSocket 客户端模块

负责维护与飞书服务器的长连接，接收实时消息事件
"""
import lark_oapi as lark
from .event_handler import EventHandler
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class WebSocketClient:
    """WebSocket 客户端
    
    封装飞书 SDK 的 ws.Client，提供 WebSocket 长连接管理功能
    """
    
    def __init__(
        self, 
        app_id: str, 
        app_secret: str, 
        event_handler: EventHandler,
        log_level: lark.LogLevel = lark.LogLevel.INFO
    ):
        """初始化 WebSocket 客户端
        
        Args:
            app_id: 飞书应用 ID
            app_secret: 飞书应用密钥
            event_handler: 事件处理器实例
            log_level: 日志级别，默认为 INFO
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.event_handler = event_handler
        self.log_level = log_level
        self._ws_client: Optional[lark.ws.Client] = None
        
        # 构建事件分发器
        dispatcher = self.event_handler.build()
        
        # 创建 WebSocket 客户端
        try:
            self._ws_client = lark.ws.Client(
                self.app_id,
                self.app_secret,
                event_handler=dispatcher,
                log_level=self.log_level
            )
            logger.info("WebSocket client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize WebSocket client: {e}", exc_info=True)
            raise
    
    def start(self) -> None:
        """启动 WebSocket 长连接，开始接收事件
        
        此方法会阻塞当前线程，持续监听飞书服务器的事件推送
        
        Raises:
            Exception: 如果连接建立失败
        """
        if self._ws_client is None:
            raise RuntimeError("WebSocket client not initialized")
            
        try:
            logger.info("Starting WebSocket connection...")
            self._ws_client.start()
        except Exception as e:
            logger.error(
                f"WebSocket connection failed: {e}", 
                exc_info=True
            )
            raise
    
    def stop(self) -> None:
        """停止 WebSocket 连接
        
        优雅地关闭与飞书服务器的连接
        """
        if self._ws_client is not None:
            try:
                # 注意：lark_oapi 的 ws.Client 可能没有 stop 方法
                # 如果有，调用它；否则，连接会在程序退出时自动关闭
                if hasattr(self._ws_client, 'stop'):
                    self._ws_client.stop()
                    logger.info("WebSocket connection stopped")
                else:
                    logger.warning("WebSocket client does not have stop method")
            except Exception as e:
                logger.error(f"Error stopping WebSocket client: {e}", exc_info=True)
