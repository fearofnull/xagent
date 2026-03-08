"""
AI CLI 执行器抽象基类

定义所有 AI CLI 执行器的通用接口和共享逻辑。
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import os
from ..models import ExecutionResult


class AICLIExecutor(ABC):
    """AI CLI 执行器抽象基类
    
    所有 AI CLI 执行器（Claude Code CLI、Gemini CLI）的基类。
    定义了通用接口和共享的初始化逻辑。
    
    Requirements: 3.1, 3.2
    """
    
    def __init__(self, target_dir: str, timeout: int = 600):
        """初始化 AI CLI 执行器
        
        Args:
            target_dir: 目标代码仓库目录
            timeout: 命令执行超时时间（秒），默认 600 秒
        """
        self.target_dir = target_dir
        self.timeout = timeout
    
    @abstractmethod
    def execute(
        self,
        user_prompt: str,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """执行 AI CLI 命令，返回执行结果
        
        Args:
            user_prompt: 用户提示
            additional_params: 额外参数（如 user_id, model, max_tokens 等）
            
        Returns:
            ExecutionResult: 执行结果
        """
        pass
    
    @abstractmethod
    def verify_directory(self) -> bool:
        """验证目标目录是否存在
        
        Returns:
            True 如果目录存在且可访问
        """
        pass
    
    @abstractmethod
    def get_command_name(self) -> str:
        """返回 AI CLI 命令名称
        
        Returns:
            命令名称（如 "claude", "claude.cmd", "gemini"）
        """
        pass
    
    @abstractmethod
    def build_command_args(
        self,
        user_prompt: str,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """构建 AI CLI 命令参数列表
        
        Args:
            user_prompt: 用户提示
            additional_params: 额外参数
            
        Returns:
            命令参数列表
        """
        pass
    
    def _verify_directory_exists(self) -> bool:
        """通用的目录验证实现
        
        Returns:
            True 如果目录存在且可访问
        """
        return os.path.exists(self.target_dir) and os.path.isdir(self.target_dir)
    
    def is_available(self) -> bool:
        """检查执行器是否可用
        
        Returns:
            True 如果目标目录存在
        """
        return self._verify_directory_exists()
