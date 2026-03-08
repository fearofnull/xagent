"""
消息去重缓存模块
使用 FIFO 队列防止重复处理相同的消息
"""
import logging
from collections import deque
from typing import Set

logger = logging.getLogger(__name__)


class DeduplicationCache:
    """消息去重缓存
    
    使用 collections.deque 实现 FIFO 队列，自动移除最早的条目。
    用于防止重复处理相同的飞书消息。
    
    Attributes:
        _cache: 存储消息 ID 的双端队列
        _cache_set: 用于快速查找的集合
        max_size: 缓存的最大容量
    """
    
    def __init__(self, max_size: int = 1000):
        """初始化去重缓存
        
        Args:
            max_size: 缓存的最大容量，默认 1000
        """
        self._cache = deque(maxlen=max_size)
        self._cache_set: Set[str] = set()
        self.max_size = max_size
    
    def is_processed(self, message_id: str) -> bool:
        """检查消息是否已处理
        
        Args:
            message_id: 消息的唯一标识符
            
        Returns:
            True 如果消息已经被处理过
        """
        is_duplicate = message_id in self._cache_set
        if is_duplicate:
            logger.info(f"Duplicate message detected and skipped: {message_id}")
        return is_duplicate
    
    def mark_processed(self, message_id: str) -> None:
        """标记消息为已处理
        
        Args:
            message_id: 消息的唯一标识符
        """
        # 如果消息已经在缓存中，不需要重复添加
        if message_id in self._cache_set:
            return
        
        # 如果缓存已满，deque 会自动移除最早的条目
        # 我们需要同步更新 set
        if len(self._cache) >= self.max_size:
            # 获取即将被移除的最早条目
            oldest = self._cache[0]
            self._cache_set.discard(oldest)
            logger.debug(f"Cache full, removing oldest message: {oldest}")
        
        # 添加新消息 ID
        self._cache.append(message_id)
        self._cache_set.add(message_id)
        logger.debug(f"Marked message as processed: {message_id}")
