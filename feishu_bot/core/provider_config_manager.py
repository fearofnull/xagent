"""
提供商配置管理器

负责管理AI提供商配置的CRUD操作、默认提供商设置和配置持久化。
"""
import json
import os
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from feishu_bot.models import ProviderConfig


logger = logging.getLogger(__name__)


class ProviderConfigManager:
    """提供商配置管理器
    
    管理多个AI提供商配置，支持：
    - 添加、更新、删除配置
    - 设置和获取默认提供商
    - 配置持久化到JSON文件
    - 配置导出和导入
    """
    
    def __init__(self, storage_path: str = "data/provider_configs.json"):
        """初始化配置管理器
        
        Args:
            storage_path: 配置文件路径，默认为 data/provider_configs.json
        """
        self.storage_path = storage_path
        self.configs: Dict[str, ProviderConfig] = {}
        self.version = "1.0"
        self._last_mtime = 0.0  # 记录文件最后修改时间
        
        # 确保存储目录存在
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        
        # 尝试加载现有配置
        self.load()
    
    def add_config(self, config: ProviderConfig) -> Tuple[bool, str]:
        """添加新配置
        
        验证配置名称的唯一性，如果名称已存在则拒绝添加。
        添加成功后自动保存到文件。
        
        Args:
            config: 要添加的提供商配置
            
        Returns:
            (是否成功, 消息)
        """
        # 验证名称唯一性
        if config.name in self.configs:
            return False, f"配置名称 '{config.name}' 已存在"
        
        # 验证多模型配置
        if not config.models or len(config.models) == 0:
            return False, "models列表不能为空，至少需要配置一个模型"
        
        if config.default_model not in config.models:
            return False, f"default_model '{config.default_model}' 必须在models列表中"
        
        # 设置创建时间
        if not config.created_at:
            config.created_at = datetime.now().astimezone().replace(microsecond=0).isoformat()
        if not config.updated_at:
            config.updated_at = config.created_at
        
        # 添加配置
        self.configs[config.name] = config
        
        # 保存到文件
        if not self.save():
            return False, "保存配置文件失败"
        
        logger.info(f"添加提供商配置: {config.name}")
        return True, "配置添加成功"
    
    def update_config(self, name: str, config: ProviderConfig) -> Tuple[bool, str]:
        """更新现有配置
        
        如果配置不存在则返回失败。
        更新成功后自动保存到文件。
        
        Args:
            name: 要更新的配置名称
            config: 新的配置对象
            
        Returns:
            (是否成功, 消息)
        """
        # 验证配置存在
        if name not in self.configs:
            return False, f"配置 '{name}' 不存在"
        
        # 如果更改了名称，需要验证新名称的唯一性
        if config.name != name and config.name in self.configs:
            return False, f"配置名称 '{config.name}' 已存在"
        
        # 验证多模型配置
        if not config.models or len(config.models) == 0:
            return False, "models列表不能为空，至少需要配置一个模型"
        
        if config.default_model not in config.models:
            return False, f"default_model '{config.default_model}' 必须在models列表中"
        
        # 保留创建时间和默认状态，更新修改时间
        old_config = self.configs[name]
        config.created_at = old_config.created_at
        config.is_default = old_config.is_default
        config.updated_at = datetime.now().astimezone().replace(microsecond=0).isoformat()
        
        # 如果名称改变，删除旧名称的配置
        if config.name != name:
            del self.configs[name]
        
        # 更新配置
        self.configs[config.name] = config
        
        # 保存到文件
        if not self.save():
            return False, "保存配置文件失败"
        
        logger.info(f"更新提供商配置: {name} -> {config.name}")
        return True, "配置更新成功"
    
    def delete_config(self, name: str) -> Tuple[bool, str]:
        """删除配置
        
        删除成功后自动保存到文件。
        
        Args:
            name: 要删除的配置名称
            
        Returns:
            (是否成功, 消息)
        """
        # 验证配置存在
        if name not in self.configs:
            return False, f"配置 '{name}' 不存在"
        
        # 删除配置
        del self.configs[name]
        
        # 保存到文件
        if not self.save():
            return False, "保存配置文件失败"
        
        logger.info(f"删除提供商配置: {name}")
        return True, "配置删除成功"
    
    def get_config(self, name: str) -> Optional[ProviderConfig]:
        """根据名称获取配置
        
        Args:
            name: 配置名称
            
        Returns:
            配置对象，如果不存在则返回 None
        """
        return self.configs.get(name)
    
    def list_configs(self) -> List[ProviderConfig]:
        """返回所有配置列表
        
        Returns:
            所有配置的列表
        """
        return list(self.configs.values())
    
    def set_default(self, name: str) -> Tuple[bool, str]:
        """设置默认提供商
        
        将指定配置设置为默认，同时取消其他配置的默认标记。
        设置成功后自动保存到文件。
        
        Args:
            name: 要设置为默认的配置名称
            
        Returns:
            (是否成功, 消息)
        """
        # 验证配置存在
        if name not in self.configs:
            return False, f"配置 '{name}' 不存在"
        
        # 取消所有配置的默认标记
        for config in self.configs.values():
            config.is_default = False
        
        # 设置指定配置为默认
        self.configs[name].is_default = True
        self.configs[name].updated_at = datetime.now().astimezone().replace(microsecond=0).isoformat()
        
        # 保存到文件
        if not self.save():
            return False, "保存配置文件失败"
        
        logger.info(f"设置默认提供商: {name}")
        return True, f"已将 '{name}' 设置为默认提供商"
    
    def get_default(self) -> Optional[ProviderConfig]:
        """获取默认提供商配置
        
        自动检查配置文件是否被修改，如果修改了则重新加载。
        
        Returns:
            默认提供商配置，如果没有设置默认则返回 None
        """
        # 检查文件是否被修改
        self.reload_if_changed()
        
        for config in self.configs.values():
            if config.is_default:
                return config
        return None
    
    def reload_if_changed(self) -> bool:
        """检查配置文件是否被修改，如果修改了则重新加载
        
        Returns:
            True 如果重新加载了配置
        """
        if not os.path.exists(self.storage_path):
            return False
        
        try:
            current_mtime = os.path.getmtime(self.storage_path)
            if current_mtime > self._last_mtime:
                logger.info(f"检测到配置文件已更新，重新加载配置")
                self.load()
                return True
        except Exception as e:
            logger.warning(f"检查配置文件修改时间失败: {e}")
        
        return False
    
    def save(self) -> bool:
        """保存配置到文件
        
        将所有配置保存到JSON文件，包含version字段。
        设置文件权限为600（仅所有者可读写）。
        
        Returns:
            是否保存成功
        """
        try:
            # 构建保存数据
            data = {
                "version": self.version,
                "configs": [config.to_dict() for config in self.configs.values()]
            }
            
            # 写入文件
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # 设置文件权限为600（仅所有者可读写）
            os.chmod(self.storage_path, 0o600)
            
            logger.debug(f"配置已保存到: {self.storage_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False
    
    def load(self) -> bool:
        """从文件加载配置
        
        如果文件不存在，创建新文件并初始化为空配置列表。
        如果文件损坏或格式错误，记录错误并使用空配置列表。
        
        Returns:
            是否加载成功
        """
        # 如果文件不存在，初始化为空配置
        if not os.path.exists(self.storage_path):
            logger.info(f"配置文件不存在，将创建新文件: {self.storage_path}")
            self.configs = {}
            self._last_mtime = 0.0
            return self.save()
        
        try:
            # 记录文件修改时间
            self._last_mtime = os.path.getmtime(self.storage_path)
            
            # 读取文件
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 验证版本
            if "version" in data:
                self.version = data["version"]
            
            # 加载配置
            self.configs = {}
            for config_data in data.get("configs", []):
                config = ProviderConfig.from_dict(config_data)
                self.configs[config.name] = config
            
            logger.info(f"从文件加载了 {len(self.configs)} 个配置")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"配置文件格式错误: {e}")
            logger.warning("使用空配置列表继续运行")
            self.configs = {}
            self._last_mtime = 0.0
            return False
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            logger.warning("使用空配置列表继续运行")
            self.configs = {}
            self._last_mtime = 0.0
            return False
    
    def export_config(self, path: str) -> bool:
        """导出配置到指定文件
        
        Args:
            path: 导出文件路径
            
        Returns:
            是否导出成功
        """
        try:
            # 构建导出数据
            data = {
                "version": self.version,
                "configs": [config.to_dict() for config in self.configs.values()]
            }
            
            # 确保目录存在
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # 写入文件
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置已导出到: {path}")
            return True
            
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            return False
    
    def import_config(self, path: str) -> Tuple[bool, str]:
        """从文件导入配置
        
        导入的配置会合并到现有配置中。
        如果存在同名配置，会被覆盖。
        
        Args:
            path: 导入文件路径
            
        Returns:
            (是否成功, 消息)
        """
        try:
            # 读取文件
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 验证格式
            if "configs" not in data:
                return False, "导入文件格式错误：缺少 configs 字段"
            
            # 导入配置
            imported_count = 0
            for config_data in data["configs"]:
                try:
                    config = ProviderConfig.from_dict(config_data)
                    self.configs[config.name] = config
                    imported_count += 1
                except Exception as e:
                    logger.warning(f"跳过无效配置: {e}")
            
            # 保存到文件
            if not self.save():
                return False, "保存配置文件失败"
            
            logger.info(f"从 {path} 导入了 {imported_count} 个配置")
            return True, f"成功导入 {imported_count} 个配置"
            
        except json.JSONDecodeError as e:
            return False, f"导入文件格式错误: {e}"
            
        except FileNotFoundError:
            return False, f"导入文件不存在: {path}"
            
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            return False, f"导入配置失败: {e}"
