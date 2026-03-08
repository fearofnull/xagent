# -*- coding: utf-8 -*-
"""网络搜索工具

使用 Serper API 进行网络搜索
"""
import aiohttp
from typing import Optional

from .base import BaseTool, ToolResult


class WebSearchTool(BaseTool):
    """网络搜索工具"""
    
    def __init__(self, api_key: Optional[str] = None, search_engine: str = "serper"):
        super().__init__(
            name="web_search",
            description="搜索互联网获取最新信息",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "返回结果数量（默认5）",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        )
        self.api_key = api_key
        self.search_engine = search_engine
    
    def is_available(self) -> bool:
        """检查工具是否可用
        
        Returns:
            bool: 工具是否可用
        """
        return self.api_key is not None
    
    async def execute(self, query: str, num_results: int = 5) -> ToolResult:
        """执行网络搜索
        
        Args:
            query: 搜索关键词
            num_results: 返回结果数量
            
        Returns:
            ToolResult: 执行结果
        """
        try:
            if not self.api_key:
                return ToolResult(
                    success=False,
                    output="",
                    error="未配置搜索 API 密钥"
                )
            
            if self.search_engine == "serper":
                result = await self._serper_search(query, num_results)
            else:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"不支持的搜索引擎: {self.search_engine}"
                )
            
            return result
            
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
    
    async def _serper_search(self, query: str, num_results: int) -> ToolResult:
        """使用 Serper API 进行搜索
        
        Args:
            query: 搜索关键词
            num_results: 返回结果数量
            
        Returns:
            ToolResult: 执行结果
        """
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        data = {
            "q": query,
            "num": num_results
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    data = await response.json()
                    results = self._format_serper_results(data)
                    return ToolResult(success=True, output=results)
                else:
                    error_text = await response.text()
                    return ToolResult(
                        success=False,
                        output="",
                        error=f"搜索失败: HTTP {response.status}, {error_text}"
                    )
    
    def _format_serper_results(self, data: dict) -> str:
        """格式化 Serper API 搜索结果
        
        Args:
            data: 搜索结果数据
            
        Returns:
            str: 格式化的搜索结果
        """
        results = []
        
        # 处理 organic 搜索结果
        organic_results = data.get("organic", [])
        for i, item in enumerate(organic_results, 1):
            title = item.get("title", "")
            link = item.get("link", "")
            snippet = item.get("snippet", "")
            
            result_str = f"**{i}. {title}**\n{snippet}\n链接: {link}\n"
            results.append(result_str)
        
        # 处理 knowledgeGraph 结果
        knowledge_graph = data.get("knowledgeGraph", {})
        if knowledge_graph:
            title = knowledge_graph.get("title", "")
            description = knowledge_graph.get("description", "")
            entity_type = knowledge_graph.get("type", "")
            
            kg_str = f"**知识图谱**\n**{title}** ({entity_type})\n{description}\n"
            results.insert(0, kg_str)
        
        # 处理 answerBox 结果
        answer_box = data.get("answerBox", {})
        if answer_box:
            answer = answer_box.get("answer", "")
            snippet = answer_box.get("snippet", "")
            title = answer_box.get("title", "")
            
            if answer:
                ab_str = f"**直接回答**\n{answer}\n"
            elif snippet:
                ab_str = f"**相关信息**\n{snippet}\n"
            else:
                ab_str = f"**相关信息**\n{title}\n"
            
            results.insert(0, ab_str)
        
        if not results:
            return "未找到相关结果"
        
        return "\n".join(results)
