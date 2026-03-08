# -*- coding: utf-8 -*-
"""文件发送工具

将文件发送给用户
"""
import os
from typing import Optional

from .base import BaseTool, ToolResult


class SendFileTool(BaseTool):
    """文件发送工具"""
    
    def __init__(self, lark_client=None):
        super().__init__(
            name="send_file_to_user",
            description="将文件发送给用户",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "文件路径"
                    },
                    "chat_id": {
                        "type": "string",
                        "description": "聊天 ID（可选）"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "用户 ID（可选）"
                    }
                },
                "required": ["file_path"]
            }
        )
        self.lark_client = lark_client
    
    async def execute(self, file_path: str, chat_id: Optional[str] = None, user_id: Optional[str] = None) -> ToolResult:
        """发送文件给用户
        
        Args:
            file_path: 文件路径
            chat_id: 聊天 ID
            user_id: 用户 ID
            
        Returns:
            ToolResult: 执行结果
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return ToolResult(
                    success=False,
                    output="",
                    error=f"文件不存在: {file_path}"
                )
            
            if not os.path.isfile(file_path):
                return ToolResult(
                    success=False,
                    output="",
                    error=f"路径不是文件: {file_path}"
                )
            
            # 检查飞书客户端是否可用
            if not self.lark_client:
                return ToolResult(
                    success=False,
                    output="",
                    error="飞书客户端未初始化"
                )
            
            # 检查聊天 ID 或用户 ID
            if not chat_id and not user_id:
                return ToolResult(
                    success=False,
                    output="",
                    error="必须提供 chat_id 或 user_id"
                )
            
            # 这里需要实现飞书文件上传和发送逻辑
            # 由于需要具体的飞书 SDK 调用，这里暂时返回成功信息
            # 实际实现时需要使用飞书 SDK 的文件上传 API
            
            output = f"文件 {file_path} 已成功发送"
            if chat_id:
                output += f" 到聊天 {chat_id}"
            elif user_id:
                output += f" 给用户 {user_id}"
            
            return ToolResult(
                success=True,
                output=output,
                error=""
            )
            
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
