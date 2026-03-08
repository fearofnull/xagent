"""
数据模型定义
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import time


@dataclass
class ExecutionResult:
    """AI 执行结果"""
    success: bool
    stdout: str
    stderr: str
    error_message: Optional[str]
    execution_time: float


@dataclass
class Message:
    """会话中的单条消息"""
    role: str  # "user" 或 "assistant"
    content: str
    timestamp: int = field(default_factory=lambda: int(time.time()))


@dataclass
class Session:
    """用户会话"""
    session_id: str
    user_id: str
    created_at: int
    last_active: int
    messages: List[Message] = field(default_factory=list)
    
    def is_expired(self, timeout: int) -> bool:
        """检查会话是否过期
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            True 如果会话已过期
        """
        return (time.time() - self.last_active) > timeout
    
    def should_rotate(self, max_messages: int) -> bool:
        """检查是否需要轮换会话
        
        Args:
            max_messages: 最大消息数
            
        Returns:
            True 如果需要轮换
        """
        return len(self.messages) >= max_messages


@dataclass
class ParsedCommand:
    """解析后的用户命令"""
    provider: str  # AI 提供商：claude, gemini, openai
    execution_layer: str  # 执行层：api 或 cli
    message: str  # 去除前缀后的实际消息内容
    explicit: bool  # 是否显式指定（用户使用了前缀）


@dataclass
class ExecutorMetadata:
    """执行器元数据"""
    name: str
    provider: str
    layer: str  # "api" 或 "cli"
    version: str
    description: str
    capabilities: List[str]
    command_prefixes: List[str]
    priority: int  # 优先级（数字越小优先级越高）
    config_required: List[str]  # 必需的配置项


@dataclass
class MessageReceiveEvent:
    """飞书消息接收事件"""
    message_id: str
    chat_id: str
    chat_type: str  # "p2p" 或 "group"
    message_type: str  # "text", "image", "file" 等
    content: str  # JSON 字符串
    parent_id: Optional[str]  # 引用消息的 ID
    sender_id: str
    create_time: int



@dataclass
class SessionConfig:
    """会话配置"""
    session_id: str  # chat_id 或 user_id
    session_type: str  # "user" 或 "group"
    target_project_dir: Optional[str]
    response_language: Optional[str]
    default_cli_provider: Optional[str]
    created_by: Optional[str]  # 创建者 user_id
    created_at: str  # ISO 格式时间戳
    updated_by: Optional[str]  # 最后更新者 user_id
    updated_at: str  # ISO 格式时间戳
    update_count: int  # 更新次数


@dataclass
class ProviderConfig:
    """提供商配置数据模型"""
    
    name: str  # 配置名称（唯一标识）
    type: str  # API兼容类型：openai_compatible, claude_compatible, gemini_compatible
    base_url: str  # API端点URL
    api_key: str  # API密钥
    models: List[str]  # 模型列表
    default_model: str  # 默认模型
    is_default: bool = False  # 是否为默认提供商
    created_at: str = ""  # 创建时间（ISO 8601格式）
    updated_at: str = ""  # 更新时间（ISO 8601格式）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            包含所有字段的字典
        """
        return {
            "name": self.name,
            "type": self.type,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "models": self.models,
            "default_model": self.default_model,
            "is_default": self.is_default,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    def to_safe_dict(self) -> Dict[str, Any]:
        """转换为安全字典（隐藏api_key）
        
        只显示api_key的前4位和后4位，中间用星号替代。
        如果api_key长度小于等于8位，则完全隐藏为"****"。
        
        Returns:
            包含所有字段的字典，但api_key被脱敏
        """
        data = self.to_dict()
        if self.api_key:
            # 只显示前4位和后4位
            if len(self.api_key) > 8:
                masked_middle = '*' * (len(self.api_key) - 8)
                data["api_key"] = f"{self.api_key[:4]}{masked_middle}{self.api_key[-4:]}"
            else:
                data["api_key"] = "****"
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProviderConfig":
        """从字典创建实例
        
        支持向后兼容：如果数据中只有 model 字段（旧格式），
        自动转换为 models 和 default_model 字段（新格式）。
        
        Args:
            data: 包含配置字段的字典
            
        Returns:
            ProviderConfig实例
        """
        # 向后兼容：处理旧格式（只有 model 字段）
        if "model" in data and "models" not in data:
            models = [data["model"]]
            default_model = data["model"]
        else:
            models = data.get("models", [])
            default_model = data.get("default_model", "")
        
        return cls(
            name=data["name"],
            type=data["type"],
            base_url=data["base_url"],
            api_key=data["api_key"],
            models=models,
            default_model=default_model,
            is_default=data.get("is_default", False),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", "")
        )
