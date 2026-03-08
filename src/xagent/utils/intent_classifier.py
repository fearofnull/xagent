"""
意图分类器模块

使用AI判断用户消息是否需要CLI层处理
"""
import json
import logging
from typing import Optional, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class IntentClassification:
    """意图分类结果"""
    needs_cli: bool  # 是否需要CLI层
    confidence: float  # 置信度 (0-1)
    reason: str  # 判断理由
    category: str  # 意图类别


class IntentClassifier:
    """意图分类器
    
    使用AI判断用户消息是否需要访问本地代码库（CLI层）
    """
    
    # 分类提示词
    CLASSIFICATION_PROMPT = """你是一个智能路由助手。请判断用户的问题是否需要访问本地代码库。

需要访问本地代码库（CLI层）的情况：
- 查看、分析、修改现有代码文件
- 读取项目中的具体文件内容
- 分析项目结构或架构
- 执行本地命令或脚本
- 基于现有代码进行重构或优化

不需要访问本地代码库（API层）的情况：
- 一般性问答（如"你是谁"、"什么是Python"）
- 概念解释和理论知识
- 代码生成（不需要查看现有代码）
- 翻译、写作、总结等文本处理
- 算法讲解和示例代码

请以JSON格式返回判断结果：
{{
    "needs_cli": true/false,
    "confidence": 0.0-1.0,
    "reason": "判断理由",
    "category": "意图类别"
}}

用户问题：{message}

请直接返回JSON，不要有其他内容。"""
    
    def __init__(self, api_executor=None, use_cache: bool = True):
        """初始化意图分类器
        
        Args:
            api_executor: API执行器（用于调用AI）
            use_cache: 是否使用缓存
        """
        self.api_executor = api_executor
        self.use_cache = use_cache
        self.cache: Dict[str, IntentClassification] = {}
        
        # 关键词降级方案（当AI不可用时使用）
        self.cli_keywords = [
            "查看代码", "view code", "分析代码", "analyze code", "代码库", "codebase",
            "修改文件", "modify file", "读取文件", "read file", "写入文件", "write file",
            "创建文件", "create file", "执行命令", "execute command", "运行脚本", "run script",
            "分析项目", "analyze project", "项目结构", "project structure",
        ]
    
    def classify(self, message: str) -> IntentClassification:
        """分类用户消息意图
        
        Args:
            message: 用户消息
            
        Returns:
            IntentClassification: 分类结果
        """
        # 检查缓存
        if self.use_cache and message in self.cache:
            logger.debug(f"[INTENT] Using cached classification for message")
            return self.cache[message]
        
        # 尝试使用AI分类
        if self.api_executor:
            try:
                result = self._classify_with_ai(message)
                if result:
                    # 缓存结果
                    if self.use_cache:
                        self.cache[message] = result
                    return result
            except Exception as e:
                logger.warning(f"[INTENT] AI classification failed: {e}, falling back to keywords")
        
        # 降级到关键词检测
        return self._classify_with_keywords(message)
    
    def _classify_with_ai(self, message: str) -> Optional[IntentClassification]:
        """使用AI进行意图分类
        
        Args:
            message: 用户消息
            
        Returns:
            Optional[IntentClassification]: 分类结果，失败返回None
        """
        try:
            # 构建分类提示
            prompt = self.CLASSIFICATION_PROMPT.format(message=message)
            
            # 调用AI（使用简短的系统提示以节省token）
            logger.info(f"[INTENT] Classifying intent with AI...")
            result = self.api_executor.execute(
                user_prompt=prompt,
                conversation_history=None,  # 不需要历史上下文
                additional_params={
                    "max_tokens": 200,  # 限制输出长度
                    "temperature": 0.1,  # 低温度以获得更确定的结果
                }
            )
            
            if not result.success:
                logger.warning(f"[INTENT] AI execution failed: {result.error_message}")
                return None
            
            # 解析JSON响应
            response_text = result.stdout.strip()
            logger.debug(f"[INTENT] Raw AI response (first 200 chars): {repr(response_text[:200])}")
            
            # 尝试提取JSON（可能包含markdown代码块或其他格式）
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            # 如果响应以 { 开始但前面有空白，清理它
            if "{" in response_text:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                response_text = response_text[json_start:json_end]
            
            # 解析JSON
            classification_data = json.loads(response_text)
            
            classification = IntentClassification(
                needs_cli=classification_data.get("needs_cli", False),
                confidence=classification_data.get("confidence", 0.5),
                reason=classification_data.get("reason", "AI判断"),
                category=classification_data.get("category", "unknown")
            )
            
            logger.info(
                f"[INTENT] AI classification: needs_cli={classification.needs_cli}, "
                f"confidence={classification.confidence:.2f}, "
                f"category={classification.category}"
            )
            logger.debug(f"[INTENT] Reason: {classification.reason}")
            
            return classification
            
        except json.JSONDecodeError as e:
            logger.warning(f"[INTENT] Failed to parse AI response as JSON: {e}")
            logger.debug(f"[INTENT] Raw response text: {repr(response_text)}")
            return None
        except Exception as e:
            logger.error(f"[INTENT] Unexpected error in AI classification: {repr(e)}", exc_info=True)
            return None
    
    def _classify_with_keywords(self, message: str) -> IntentClassification:
        """使用关键词进行意图分类（降级方案）
        
        Args:
            message: 用户消息
            
        Returns:
            IntentClassification: 分类结果
        """
        message_lower = message.lower()
        
        # 检查是否包含CLI关键词
        for keyword in self.cli_keywords:
            if keyword.lower() in message_lower:
                logger.info(f"[INTENT] Keyword classification: needs_cli=True (keyword: '{keyword}')")
                return IntentClassification(
                    needs_cli=True,
                    confidence=0.7,  # 关键词匹配的置信度较低
                    reason=f"包含CLI关键词: {keyword}",
                    category="keyword_match"
                )
        
        # 默认不需要CLI
        logger.info(f"[INTENT] Keyword classification: needs_cli=False (no keywords found)")
        return IntentClassification(
            needs_cli=False,
            confidence=0.6,  # 默认判断的置信度较低
            reason="未检测到CLI关键词",
            category="default"
        )
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        logger.info("[INTENT] Cache cleared")
