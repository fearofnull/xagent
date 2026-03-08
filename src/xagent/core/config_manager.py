"""
配置管理器 - 管理会话级别的动态配置
"""
import json
import os
import time
import logging
from typing import Dict, Optional, Any, List
from pathlib import Path
from filelock import FileLock

from ..models import SessionConfig

# Import optimized JSON utilities if available
try:
    from ..web_admin.json_utils import dump, load
    HAS_JSON_UTILS = True
except ImportError:
    # Fallback to standard json
    from json import dump, load
    HAS_JSON_UTILS = False


logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器
    
    负责管理会话级别的动态配置，支持：
    - 私聊：基于 user_id 的用户级配置
    - 群聊：基于 chat_id 的群组级配置
    - 临时参数：单次使用的参数覆盖
    - 配置持久化（JSON 文件存储）
    - 配置历史追踪
    - 配置命令处理（/setdir, /lang, /config 等）
    """
    
    # 支持的配置命令
    CONFIG_COMMANDS = {
        "/setdir": "target_project_dir",
        "/lang": "response_language",
        "/cliprovider": "default_cli_provider",
    }
    
    # 查看配置命令
    VIEW_CONFIG_COMMANDS = ["/config", "配置"]
    RESET_CONFIG_COMMANDS = ["/reset", "重置配置"]
    
    # 有效的配置值
    VALID_CLI_PROVIDERS = ["claude", "gemini", "qwen"]
    VALID_PROVIDERS = VALID_CLI_PROVIDERS  # 别名,保持向后兼容
    
    def __init__(
        self,
        storage_path: str = "./data/session_configs.json",
        global_config: Optional[Any] = None
    ):
        """初始化配置管理器
        
        Args:
            storage_path: 配置存储路径
            global_config: 全局配置对象（BotConfig）
        """
        self.storage_path = storage_path
        self.global_config = global_config
        self.configs: Dict[str, SessionConfig] = {}
        
        # Cache for effective configs (5 minute TTL)
        self._effective_config_cache: Dict[str, tuple[Dict[str, Any], float]] = {}
        self._cache_ttl = 300  # 5 minutes
        
        # 确保存储目录存在
        storage_dir = os.path.dirname(storage_path)
        if storage_dir:
            os.makedirs(storage_dir, exist_ok=True)
        
        # 文件锁路径
        self.lock_path = f"{storage_path}.lock"
        
        # 加载现有配置
        self.load_configs()
        
        logger.info(f"ConfigManager initialized: storage={storage_path}, caching enabled")
    
    def get_effective_config(
        self,
        session_id: str,
        session_type: str,
        temp_params: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """获取有效配置（优先级：临时参数 > 会话配置 > 全局配置 > 默认值）
        
        Uses caching to improve performance for frequently accessed configs.
        
        Args:
            session_id: 会话 ID（user_id 或 chat_id）
            session_type: 会话类型（"user" 或 "group"）
            temp_params: 临时参数字典
            
        Returns:
            有效配置字典
        """
        # If no temp params, try to use cache
        if not temp_params:
            cache_key = f"{session_id}:{session_type}"
            if cache_key in self._effective_config_cache:
                cached_config, cached_time = self._effective_config_cache[cache_key]
                # Check if cache is still valid
                if time.time() - cached_time < self._cache_ttl:
                    logger.debug(f"Using cached effective config for {session_id}")
                    return cached_config.copy()  # Return a copy to prevent modification
        
        # 1. 从默认值开始
        effective = {
            "target_project_dir": "",
            "response_language": None,
            "default_cli_provider": None,
        }
        
        # 2. 应用全局配置
        if self.global_config:
            effective["target_project_dir"] = self.global_config.target_directory or ""
            # 检查 BotConfig 是否有 response_language 属性
            if hasattr(self.global_config, 'response_language'):
                effective["response_language"] = self.global_config.response_language
            # 检查 BotConfig 是否有 default_cli_provider 属性
            if hasattr(self.global_config, 'default_cli_provider'):
                effective["default_cli_provider"] = self.global_config.default_cli_provider
        
        # 3. 应用会话配置
        if session_id in self.configs:
            session_config = self.configs[session_id]
            if session_config.target_project_dir is not None:
                effective["target_project_dir"] = session_config.target_project_dir
            if session_config.response_language is not None:
                effective["response_language"] = session_config.response_language
            if session_config.default_cli_provider is not None:
                effective["default_cli_provider"] = session_config.default_cli_provider
        
        # Cache the result if no temp params
        if not temp_params:
            cache_key = f"{session_id}:{session_type}"
            self._effective_config_cache[cache_key] = (effective.copy(), time.time())
            logger.debug(f"Cached effective config for {session_id}")
        
        # 4. 应用临时参数（最高优先级）
        if temp_params:
            if "dir" in temp_params:
                effective["target_project_dir"] = temp_params["dir"]
            if "lang" in temp_params:
                effective["response_language"] = temp_params["lang"]
            if "cliprovider" in temp_params:
                effective["default_cli_provider"] = temp_params["cliprovider"]
        
        return effective

    
    def set_config(
        self,
        session_id: str,
        session_type: str,
        config_key: str,
        config_value: str,
        user_id: str
    ) -> tuple[bool, str]:
        """设置会话配置
        
        Args:
            session_id: 会话 ID（user_id 或 chat_id）
            session_type: 会话类型（"user" 或 "group"）
            config_key: 配置键
            config_value: 配置值
            user_id: 操作用户 ID
            
        Returns:
            (成功标志, 消息)
        """
        # 验证配置值
        if config_key == "default_cli_provider":
            if config_value not in self.VALID_CLI_PROVIDERS:
                return False, f"❌ 无效的CLI提供商 / Invalid CLI provider: {config_value}\n有效值 / Valid values: {', '.join(self.VALID_CLI_PROVIDERS)}"
        
        elif config_key == "target_project_dir":
            # 验证目录是否存在
            if config_value and not os.path.exists(config_value):
                return False, f"⚠️ 目录不存在 / Directory does not exist: {config_value}"
        
        # 获取或创建配置
        if session_id not in self.configs:
            self.configs[session_id] = SessionConfig(
                session_id=session_id,
                session_type=session_type,
                target_project_dir=None,
                response_language=None,
                default_cli_provider=None,
                created_by=user_id,
                created_at=self._get_timestamp(),
                updated_by=user_id,
                updated_at=self._get_timestamp(),
                update_count=0
            )
        
        config = self.configs[session_id]
        
        # 更新配置值
        if config_key == "target_project_dir":
            config.target_project_dir = config_value
        elif config_key == "response_language":
            config.response_language = config_value
        elif config_key == "default_cli_provider":
            config.default_cli_provider = config_value
        
        # 更新元数据
        config.updated_by = user_id
        config.updated_at = self._get_timestamp()
        config.update_count += 1
        
        # Invalidate cache for this session
        self._invalidate_cache(session_id, session_type)
        
        # 保存配置
        self.save_configs()
        
        logger.info(
            f"Config updated: session={session_id}, type={session_type}, "
            f"key={config_key}, value={config_value}, user={user_id}"
        )
        
        return True, f"✅ 配置已更新 / Config updated: {config_key} = {config_value}"
    
    def reset_config(self, session_id: str) -> tuple[bool, str]:
        """重置会话配置
        
        Args:
            session_id: 会话 ID
            
        Returns:
            (成功标志, 消息)
        """
        if session_id in self.configs:
            session_type = self.configs[session_id].session_type
            del self.configs[session_id]
            
            # Invalidate cache for this session
            self._invalidate_cache(session_id, session_type)
            
            self.save_configs()
            logger.info(f"Config reset for session: {session_id}")
            return True, "✅ 配置已重置 / Config reset"
        
        return False, "ℹ️ 没有配置需要重置 / No config to reset"
    
    def get_config_info(self, session_id: str) -> str:
        """获取配置信息
        
        Args:
            session_id: 会话 ID
            
        Returns:
            格式化的配置信息
        """
        effective = self.get_effective_config(session_id, "user")
        
        lines = ["⚙️ 当前配置 / Current Config:"]
        lines.append(f"- 项目目录 / Project Dir: {effective['target_project_dir'] or '(未设置 / Not set)'}")
        lines.append(f"- 回复语言 / Language: {effective['response_language'] or '(自动 / Auto)'}")
        lines.append(f"- CLI提供商 / CLI Provider: {effective['default_cli_provider'] or '(使用默认 / Use default)'}")
        
        # 如果有会话配置，显示元数据
        if session_id in self.configs:
            config = self.configs[session_id]
            lines.append(f"\n📊 配置元数据 / Metadata:")
            lines.append(f"- 创建者 / Created by: {config.created_by}")
            lines.append(f"- 创建时间 / Created at: {config.created_at}")
            lines.append(f"- 更新者 / Updated by: {config.updated_by}")
            lines.append(f"- 更新时间 / Updated at: {config.updated_at}")
            lines.append(f"- 更新次数 / Update count: {config.update_count}")
        
        return "\n".join(lines)
    
    def is_config_command(self, message: str) -> bool:
        """检查消息是否为配置命令
        
        Args:
            message: 用户消息
            
        Returns:
            True 如果是配置命令
        """
        message_lower = message.strip().lower()
        
        # 检查是否以配置命令开头
        for cmd in self.CONFIG_COMMANDS.keys():
            if message_lower.startswith(cmd.lower()):
                return True
        
        # 检查查看配置命令
        if message_lower in [cmd.lower() for cmd in self.VIEW_CONFIG_COMMANDS]:
            return True
        
        # 检查重置配置命令
        if message_lower in [cmd.lower() for cmd in self.RESET_CONFIG_COMMANDS]:
            return True
        
        return False
    
    def handle_config_command(
        self,
        session_id: str,
        session_type: str,
        user_id: str,
        message: str
    ) -> Optional[str]:
        """处理配置命令
        
        Args:
            session_id: 会话 ID（user_id 或 chat_id）
            session_type: 会话类型（"user" 或 "group"）
            user_id: 操作用户 ID
            message: 用户消息
            
        Returns:
            命令响应消息，如果不是配置命令则返回 None
        """
        message_lower = message.strip().lower()
        
        # 查看配置命令
        if message_lower in [cmd.lower() for cmd in self.VIEW_CONFIG_COMMANDS]:
            return self.get_config_info(session_id)
        
        # 重置配置命令
        if message_lower in [cmd.lower() for cmd in self.RESET_CONFIG_COMMANDS]:
            success, msg = self.reset_config(session_id)
            return msg
        
        # 设置配置命令
        for cmd, config_key in self.CONFIG_COMMANDS.items():
            if message_lower.startswith(cmd.lower()):
                # 提取配置值
                value = message[len(cmd):].strip()
                
                if not value:
                    return f"❌ 请提供配置值 / Please provide a value\n用法 / Usage: {cmd} <value>"
                
                success, msg = self.set_config(
                    session_id, session_type, config_key, value, user_id
                )
                return msg
        
        return None
    
    def parse_temp_params(self, message: str) -> tuple[str, Dict[str, str]]:
        """解析临时参数
        
        Args:
            message: 用户消息
            
        Returns:
            (清理后的消息, 临时参数字典)
        """
        import re
        
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
    
    def save_configs(self) -> None:
        """持久化所有配置到存储"""
        try:
            # 使用文件锁避免并发写入冲突
            with FileLock(self.lock_path, timeout=10):
                # 转换为可序列化的格式
                data = {
                    "configs": {
                        session_id: self._config_to_dict(config)
                        for session_id, config in self.configs.items()
                    }
                }
                
                # 写入文件 (使用优化的JSON序列化)
                with open(self.storage_path, 'w', encoding='utf-8') as f:
                    if HAS_JSON_UTILS:
                        dump(data, f, indent=2)
                    else:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                
                logger.debug(f"Saved {len(self.configs)} configs to {self.storage_path}")
        
        except Exception as e:
            logger.error(f"Failed to save configs: {e}")
    
    def load_configs(self) -> None:
        """从存储加载配置"""
        if not os.path.exists(self.storage_path):
            logger.info("No existing configs file found, starting fresh")
            return
        
        try:
            # 使用文件锁避免读取时被写入
            with FileLock(self.lock_path, timeout=10):
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    if HAS_JSON_UTILS:
                        data = load(f)
                    else:
                        data = json.load(f)
                
                # 从字典恢复配置对象
                configs_data = data.get("configs", {})
                self.configs = {
                    session_id: self._dict_to_config(config_dict)
                    for session_id, config_dict in configs_data.items()
                }
                
                logger.info(f"Loaded {len(self.configs)} configs from {self.storage_path}")
        
        except Exception as e:
            logger.error(f"Failed to load configs: {e}")
            self.configs = {}
    
    def _invalidate_cache(self, session_id: str, session_type: str) -> None:
        """Invalidate cache for a specific session
        
        Args:
            session_id: Session ID
            session_type: Session type
        """
        cache_key = f"{session_id}:{session_type}"
        if cache_key in self._effective_config_cache:
            del self._effective_config_cache[cache_key]
            logger.debug(f"Invalidated cache for {session_id}")
    
    def clear_cache(self) -> None:
        """Clear all cached effective configs"""
        self._effective_config_cache.clear()
        logger.info("Cleared all config cache")
    
    def _config_to_dict(self, config: SessionConfig) -> Dict[str, Any]:
        """将 SessionConfig 对象转换为字典
        
        Args:
            config: SessionConfig 对象
            
        Returns:
            字典表示
        """
        return {
            "session_id": config.session_id,
            "session_type": config.session_type,
            "target_project_dir": config.target_project_dir,
            "response_language": config.response_language,
            "default_cli_provider": config.default_cli_provider,
            "created_by": config.created_by,
            "created_at": config.created_at,
            "updated_by": config.updated_by,
            "updated_at": config.updated_at,
            "update_count": config.update_count,
        }
    
    def _dict_to_config(self, data: Dict[str, Any]) -> SessionConfig:
        """从字典恢复 SessionConfig 对象
        
        Args:
            data: 字典数据
            
        Returns:
            SessionConfig 对象
        """
        return SessionConfig(
            session_id=data["session_id"],
            session_type=data["session_type"],
            target_project_dir=data.get("target_project_dir"),
            response_language=data.get("response_language"),
            default_cli_provider=data.get("default_cli_provider"),
            created_by=data.get("created_by"),
            created_at=data["created_at"],
            updated_by=data.get("updated_by"),
            updated_at=data["updated_at"],
            update_count=data.get("update_count", 0),
        )
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳字符串
        
        Returns:
            ISO 格式的时间戳
        """
        from datetime import datetime
        return datetime.now().isoformat()
