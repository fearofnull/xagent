# -*- coding: utf-8 -*-
"""时间获取工具

获取当前时间信息
"""
import time
from datetime import datetime, timezone

from feishu_bot.agents.tools.base import BaseTool, ToolResult


class GetTimeTool(BaseTool):
    """时间获取工具"""
    
    def __init__(self):
        super().__init__(
            name="get_current_time",
            description="获取当前时间信息",
            parameters={
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "description": "时间格式（可选，默认：%Y-%m-%d %H:%M:%S）"
                    },
                    "timezone": {
                        "type": "string",
                        "description": "时区（可选，默认：UTC）"
                    }
                }
            }
        )
    
    async def execute(self, format: str = "%Y-%m-%d %H:%M:%S", timezone: str = "UTC") -> ToolResult:
        """获取当前时间
        
        Args:
            format: 时间格式
            timezone: 时区
            
        Returns:
            ToolResult: 执行结果
        """
        try:
            # 获取当前时间
            now = datetime.now(timezone.utc)
            
            # 格式化时间
            time_str = now.strftime(format)
            
            # 构建输出
            output = f"当前时间（{timezone}）: {time_str}\n"
            output += f"时间戳: {int(time.time())}\n"
            output += f"时区: {timezone}\n"
            output += f"格式: {format}\n"
            
            return ToolResult(success=True, output=output)
            
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
