# -*- coding: utf-8 -*-
"""Tool State Manager

Manages the enabled/disabled state of tools.
"""
import json
import os
from typing import Dict, List, Optional, Callable

class ToolStateManager:
    """管理工具的启用/禁用状态"""

    def __init__(self, storage_path: str = "./data/tool_states.json", tool_list_provider: Optional[Callable[[], List[str]]] = None):
        """初始化工具状态管理器

        Args:
            storage_path: 工具状态存储文件路径
            tool_list_provider: 可选的工具列表提供者函数，用于获取当前所有可用工具
        """
        self.storage_path = storage_path
        self._tool_list_provider = tool_list_provider
        self._tool_states: Dict[str, bool] = {}
        self._load_states()

    def _load_states(self) -> None:
        """从存储文件加载工具状态"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    self._tool_states = json.load(f)
        except Exception as e:
            # 如果加载失败，使用默认状态
            self._tool_states = {}

    def _save_states(self) -> None:
        """保存工具状态到存储文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self._tool_states, f, indent=2, ensure_ascii=False)
        except Exception as e:
            pass

    def _get_all_tool_names(self) -> List[str]:
        """获取所有工具名称列表

        Returns:
            List[str]: 工具名称列表
        """
        if self._tool_list_provider:
            return self._tool_list_provider()
        return list(self._tool_states.keys())

    def get_tool_state(self, tool_name: str) -> bool:
        """获取工具的启用状态

        Args:
            tool_name: 工具名称

        Returns:
            bool: 工具是否启用，默认为 True
        """
        return self._tool_states.get(tool_name, True)

    def set_tool_state(self, tool_name: str, enabled: bool) -> None:
        """设置工具的启用状态

        Args:
            tool_name: 工具名称
            enabled: 工具是否启用
        """
        self._tool_states[tool_name] = enabled
        self._save_states()

    def toggle_tool_state(self, tool_name: str) -> bool:
        """切换工具的启用状态

        Args:
            tool_name: 工具名称

        Returns:
            bool: 切换后的启用状态
        """
        new_state = not self.get_tool_state(tool_name)
        self.set_tool_state(tool_name, new_state)
        return new_state

    def enable_all_tools(self) -> None:
        """启用所有工具"""
        for tool_name in self._get_all_tool_names():
            self._tool_states[tool_name] = True
        self._save_states()

    def disable_all_tools(self) -> None:
        """禁用所有工具"""
        for tool_name in self._get_all_tool_names():
            self._tool_states[tool_name] = False
        self._save_states()

    def get_all_tool_states(self) -> Dict[str, bool]:
        """获取所有工具的状态

        Returns:
            Dict[str, bool]: 工具名称到启用状态的映射
        """
        # 合并已保存的状态和当前所有工具的状态
        all_tools = self._get_all_tool_names()
        result = {}
        for tool_name in all_tools:
            result[tool_name] = self._tool_states.get(tool_name, True)
        return result
