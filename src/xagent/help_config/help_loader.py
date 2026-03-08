"""
帮助信息加载器 - 从配置文件加载和格式化帮助信息
"""
import json
import os
import logging
from typing import Dict, Any, List
from pathlib import Path


logger = logging.getLogger(__name__)


class HelpMessageLoader:
    """帮助信息加载器
    
    从 JSON 配置文件加载帮助信息，支持：
    - 结构化的帮助内容
    - 易于维护和更新
    - 多语言支持（未来扩展）
    """
    
    def __init__(self, config_path: str = None):
        """初始化帮助信息加载器
        
        Args:
            config_path: 配置文件路径，默认使用内置配置
        """
        if config_path is None:
            # 使用默认配置文件路径
            current_dir = Path(__file__).parent
            config_path = current_dir / "help_messages.json"
        
        self.config_path = config_path
        self.help_data = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件
        
        Returns:
            配置数据字典
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Loaded help messages from {self.config_path}")
            return data
        except FileNotFoundError:
            logger.error(f"Help messages config file not found: {self.config_path}")
            return self._get_fallback_config()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse help messages config: {e}")
            return self._get_fallback_config()
        except Exception as e:
            logger.error(f"Failed to load help messages: {e}")
            return self._get_fallback_config()
    
    def _get_fallback_config(self) -> Dict[str, Any]:
        """获取后备配置（当配置文件加载失败时使用）
        
        Returns:
            最小化的帮助信息配置
        """
        return {
            "version": "fallback",
            "help_message": {
                "title": "📖 飞书AI机器人使用帮助 / Help",
                "sections": [
                    {
                        "title": "基本命令 / Basic Commands",
                        "commands": [
                            {
                                "command": "@gpt",
                                "description": "使用Web配置的AI提供商"
                            },
                            {
                                "command": "/help",
                                "description": "显示帮助信息"
                            }
                        ]
                    }
                ]
            }
        }
    
    def get_help_message(self) -> str:
        """获取格式化的帮助信息
        
        Returns:
            格式化的帮助文本
        """
        help_msg = self.help_data.get("help_message", {})
        lines = []
        
        # 标题
        title = help_msg.get("title", "Help")
        lines.append(title)
        lines.append("")
        
        # 各个部分
        sections = help_msg.get("sections", [])
        for section in sections:
            # 部分标题
            section_title = section.get("title", "")
            if section_title:
                lines.append(section_title)
                lines.append("")
            
            # 子部分（如果有）
            subsections = section.get("subsections", [])
            if subsections:
                for subsection in subsections:
                    subsection_title = subsection.get("title", "")
                    if subsection_title:
                        lines.append(f"  {subsection_title}")
                    
                    commands = subsection.get("commands", [])
                    for cmd in commands:
                        command = cmd.get("command", "")
                        description = cmd.get("description", "")
                        lines.append(f"    {command} - {description}")
                    
                    lines.append("")
            
            # 直接命令列表
            commands = section.get("commands", [])
            if commands:
                for cmd in commands:
                    command = cmd.get("command", "")
                    description = cmd.get("description", "")
                    lines.append(f"  {command} - {description}")
                lines.append("")
            
            # 示例列表
            examples = section.get("examples", [])
            if examples:
                for example in examples:
                    lines.append(f"  {example}")
                lines.append("")
            
            # 信息列表
            info = section.get("info", [])
            if info:
                for info_item in info:
                    lines.append(f"  {info_item}")
                lines.append("")
        
        return "\n".join(lines).strip()
    
    def reload(self) -> None:
        """重新加载配置文件"""
        self.help_data = self._load_config()
        logger.info("Help messages reloaded")
    
    def get_version(self) -> str:
        """获取配置版本
        
        Returns:
            配置版本号
        """
        return self.help_data.get("version", "unknown")


# 全局单例实例
_help_loader = None


def get_help_loader() -> HelpMessageLoader:
    """获取全局帮助信息加载器实例
    
    Returns:
        HelpMessageLoader 实例
    """
    global _help_loader
    if _help_loader is None:
        _help_loader = HelpMessageLoader()
    return _help_loader


def get_help_message() -> str:
    """快捷函数：获取帮助信息
    
    Returns:
        格式化的帮助文本
    """
    return get_help_loader().get_help_message()
