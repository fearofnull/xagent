# -*- coding: utf-8 -*-
"""工具注册表

管理和发现所有可用的工具
"""
import logging
from typing import Dict, List, Optional, Type

from .tools.base import BaseTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """工具注册表
    
    管理和发现所有可用的工具
    """
    
    def __init__(self):
        """初始化工具注册表"""
        self._tools: Dict[str, BaseTool] = {}
    
    def register_tool(self, tool: BaseTool) -> None:
        """注册工具
        
        Args:
            tool: 要注册的工具实例
        """
        if tool.name in self._tools:
            logger.warning(f"工具 {tool.name} 已存在，将被覆盖")
        
        self._tools[tool.name] = tool
        logger.info(f"注册工具: {tool.name} - {tool.description}")
    
    def register_tool_class(self, tool_class: Type[BaseTool], **kwargs) -> None:
        """注册工具类
        
        Args:
            tool_class: 工具类
            **kwargs: 工具初始化参数
        """
        try:
            tool = tool_class(**kwargs)
            self.register_tool(tool)
        except Exception as e:
            logger.error(f"注册工具类 {tool_class.__name__} 失败: {e}")
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """获取工具
        
        Args:
            name: 工具名称
            
        Returns:
            Optional[BaseTool]: 工具实例，如果不存在则返回 None
        """
        return self._tools.get(name)
    
    def get_all_tools(self) -> List[BaseTool]:
        """获取所有工具
        
        Returns:
            List[BaseTool]: 所有工具实例列表
        """
        return list(self._tools.values())
    
    def get_available_tools(self) -> List[BaseTool]:
        """获取所有可用的工具
        
        Returns:
            List[BaseTool]: 可用工具实例列表
        """
        return [tool for tool in self._tools.values() if tool.is_available()]
    
    def get_tool_schemas(self) -> List[Dict]:
        """获取所有工具的 JSON Schema
        
        Returns:
            List[Dict]: 工具 JSON Schema 列表
        """
        return [tool.get_schema() for tool in self.get_available_tools()]
    
    def clear(self) -> None:
        """清空工具注册表"""
        self._tools.clear()
        logger.info("工具注册表已清空")
    
    def __contains__(self, name: str) -> bool:
        """检查工具是否存在
        
        Args:
            name: 工具名称
            
        Returns:
            bool: 工具是否存在
        """
        return name in self._tools
    
    def __len__(self) -> int:
        """获取工具数量
        
        Returns:
            int: 工具数量
        """
        return len(self._tools)
