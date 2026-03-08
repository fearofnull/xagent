"""
命令解析器模块

负责解析用户消息，识别 AI 提供商指令和命令类型
"""
import re
import logging
from typing import Optional, Dict, Tuple
from ..models import ParsedCommand

logger = logging.getLogger(__name__)


class CommandParser:
    """命令解析器
    
    解析用户消息，识别 AI 提供商前缀和 CLI 关键词
    """
    
    # AI 提供商前缀映射：前缀 -> (provider, layer)
    PREFIX_MAPPING = {
        # Unified API (routes through UnifiedAPIInterface) - 统一API入口
        "@gpt": ("unified", "api"),
        # Agent
        "@agent": ("agent", "api"),
        # OpenAI API
        "@openai-api": ("openai", "api"),
        # Claude API
        "@claude-api": ("claude", "api"),
        # Gemini API
        "@gemini-api": ("gemini", "api"),
        # Claude CLI
        "@claude-cli": ("claude", "cli"),
        "@code": ("claude", "cli"),
        # Gemini CLI
        "@gemini-cli": ("gemini", "cli"),
        # Qwen Code CLI
        "@qwen-cli": ("qwen", "cli"),
    }
    
    # CLI 关键词（中英文）
    CLI_KEYWORDS = [
        # 代码相关
        "查看代码", "view code", "分析代码", "analyze code", "代码库", "codebase",
        # 文件操作
        "修改文件", "modify file", "读取文件", "read file", "写入文件", "write file",
        "创建文件", "create file",
        # 命令执行
        "执行命令", "execute command", "运行脚本", "run script",
        # 项目分析
        "分析项目", "analyze project", "项目结构", "project structure",
    ]
    
    def parse_command(self, message: str) -> Tuple[ParsedCommand, Dict[str, str]]:
        """解析用户消息，返回解析结果和临时参数
        
        Args:
            message: 用户消息
            
        Returns:
            Tuple[ParsedCommand, Dict[str, str]]: (解析后的命令, 临时参数字典)
        """
        # 1. 提取临时参数
        clean_message, temp_params = self.parse_temp_params(message)
        
        # 2. 提取 AI 提供商前缀
        prefix_result = self.extract_provider_prefix(clean_message)
        
        if prefix_result:
            provider, layer, final_message = prefix_result
            logger.info(
                f"Command parsed with explicit prefix: provider={provider}, "
                f"layer={layer}, message_length={len(final_message)}, "
                f"temp_params={temp_params}"
            )
            return ParsedCommand(
                provider=provider,
                execution_layer=layer,
                message=final_message,
                explicit=True
            ), temp_params
        
        # 没有显式指定，返回默认值（使用统一API接口）
        logger.debug(f"No explicit prefix found, using unified API, temp_params={temp_params}")
        return ParsedCommand(
            provider="unified",  # 默认使用统一API接口
            execution_layer="api",  # 统一API接口总是API层
            message=clean_message,
            explicit=False
        ), temp_params
    
    def extract_provider_prefix(self, message: str) -> Optional[tuple[str, str, str]]:
        """提取 AI 提供商前缀
        
        Args:
            message: 用户消息
            
        Returns:
            Optional[tuple]: (provider, layer, clean_message) 或 None
        """
        # 大小写不敏感匹配
        message_lower = message.lower()
        
        # 按前缀长度降序排序，优先匹配更长的前缀
        # 这样 @claude-cli 会在 @claude 之前匹配
        sorted_prefixes = sorted(
            self.PREFIX_MAPPING.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )
        
        for prefix, (provider, layer) in sorted_prefixes:
            # 检查消息是否以前缀开头
            if message_lower.startswith(prefix.lower()):
                # 去除前缀，保留原始消息的大小写
                clean_message = message[len(prefix):].strip()
                return provider, layer, clean_message
        
        return None
    
    def detect_cli_keywords(self, message: str) -> bool:
        """检测消息是否包含需要 CLI 层的关键词
        
        Args:
            message: 用户消息
            
        Returns:
            bool: True 如果包含 CLI 关键词
        """
        # 大小写不敏感匹配
        message_lower = message.lower()
        
        for keyword in self.CLI_KEYWORDS:
            if keyword.lower() in message_lower:
                logger.debug(f"CLI keyword detected: '{keyword}' in message")
                return True
        
        return False
    
    def parse_temp_params(self, message: str) -> Tuple[str, Dict[str, str]]:
        """解析临时参数
        
        Args:
            message: 用户消息
            
        Returns:
            Tuple[str, Dict[str, str]]: (清理后的消息, 临时参数字典)
        """
        temp_params = {}
        clean_message = message
        
        # 匹配 --key=value 格式的参数
        pattern = r'--(\w+)=([^\s]+)'
        matches = re.findall(pattern, message)
        
        for key, value in matches:
            temp_params[key] = value
            # 从消息中移除该参数
            clean_message = re.sub(rf'--{key}={re.escape(value)}\s*', '', clean_message)
        
        return clean_message.strip(), temp_params
