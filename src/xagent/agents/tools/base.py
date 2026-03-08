# -*- coding: utf-8 -*-
"""工具基类和相关数据结构

定义所有工具的基类和通用数据结构
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    output: str
    error: str = ""


class BaseTool(ABC):
    """工具基类
    
    所有工具的抽象基类，定义了工具的通用接口
    """
    
    def __init__(self, name: str, description: str, parameters: Dict[str, Any]):
        """初始化工具
        
        Args:
            name: 工具名称
            description: 工具描述
            parameters: 工具参数定义（JSON Schema 格式）
        """
        self.name = name
        self.description = description
        self.parameters = parameters
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            ToolResult: 工具执行结果
        """
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """获取工具 JSON Schema（用于 Function Calling）
        
        Returns:
            Dict: 工具的 JSON Schema
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
    
    def is_available(self) -> bool:
        """检查工具是否可用
        
        Returns:
            bool: 工具是否可用
        """
        return True
