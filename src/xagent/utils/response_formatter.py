"""
响应格式化器

格式化 AI 响应消息，确保消息格式清晰易读。
"""
from typing import Optional


class ResponseFormatter:
    """响应格式化器
    
    格式化 AI 执行结果为用户友好的消息格式。
    
    Requirements: 5.1, 5.2, 5.3, 5.4
    """
    
    def format_response(
        self,
        user_message: str,
        ai_output: str,
        error: Optional[str] = None,
        executor_name: Optional[str] = None
    ) -> str:
        """格式化响应消息
        
        Args:
            user_message: 用户原始消息
            ai_output: AI 输出内容
            error: 错误信息（可选）
            executor_name: 执行器名称（可选），例如 "Claude API", "OpenAI API", "Claude Code CLI"
            
        Returns:
            格式化后的响应消息
        """
        if error:
            return self.format_error(user_message, error, executor_name)
        
        # 成功响应格式
        # 如果提供了执行器名称，在响应前添加标识
        if executor_name:
            return f"【使用 {executor_name} 回答】\n\n{ai_output}"
        
        # 直接返回 AI 输出，不添加额外的格式化
        return ai_output
    
    def format_error(
        self,
        user_message: str,
        error_message: str,
        executor_name: Optional[str] = None
    ) -> str:
        """格式化错误消息
        
        Args:
            user_message: 用户原始消息
            error_message: 错误信息
            executor_name: 执行器名称（可选）
            
        Returns:
            格式化后的错误消息
        """
        if executor_name:
            return f"【使用 {executor_name} 回答】\n\n❌ 处理失败 / Error\n\n{error_message}"
        return f"❌ 处理失败 / Error\n\n{error_message}"
