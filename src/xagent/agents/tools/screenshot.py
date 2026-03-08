# -*- coding: utf-8 -*-
"""屏幕截图工具

捕获屏幕截图
"""
import os
import tempfile
from datetime import datetime

from .base import BaseTool, ToolResult


class ScreenshotTool(BaseTool):
    """屏幕截图工具"""
    
    def __init__(self, output_dir: str = "./data/screenshots"):
        super().__init__(
            name="desktop_screenshot",
            description="截取桌面屏幕",
            parameters={
                "type": "object",
                "properties": {
                    "output_path": {
                        "type": "string",
                        "description": "输出文件路径（可选）"
                    },
                    "format": {
                        "type": "string",
                        "description": "图片格式（可选，默认：png）"
                    }
                }
            }
        )
        self.output_dir = output_dir
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
    
    async def execute(self, output_path: str = None, format: str = "png") -> ToolResult:
        """执行屏幕截图
        
        Args:
            output_path: 输出文件路径
            format: 图片格式
            
        Returns:
            ToolResult: 执行结果
        """
        try:
            # 尝试导入必要的库
            try:
                from PIL import ImageGrab
            except ImportError:
                return ToolResult(
                    success=False,
                    output="",
                    error="需要安装 Pillow 库: pip install Pillow"
                )
            
            # 生成默认输出路径
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(self.output_dir, f"screenshot_{timestamp}.{format}")
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 捕获屏幕
            screenshot = ImageGrab.grab()
            
            # 保存截图
            screenshot.save(output_path, format=format)
            
            return ToolResult(
                success=True,
                output=f"成功截取屏幕并保存到: {output_path}",
                error=""
            )
            
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
