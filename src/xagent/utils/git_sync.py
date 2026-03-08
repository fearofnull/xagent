"""Git代码同步模块

该模块提供Git仓库同步功能，用于CLI执行前自动拉取最新代码。
"""

import subprocess
import os
import logging

logger = logging.getLogger(__name__)


class GitSyncModule:
    """Git代码同步模块
    
    用于在CLI执行前自动执行git pull，确保代码是最新版本。
    
    Attributes:
        enabled: 是否启用自动同步
        timeout: git pull超时时间（秒）
    """
    
    def __init__(self, enabled: bool = True, timeout: int = 30):
        """初始化Git同步模块
        
        Args:
            enabled: 是否启用自动同步，默认为True
            timeout: git pull超时时间（秒），默认为30秒
        """
        self.enabled = enabled
        self.timeout = timeout
    
    def is_git_repo(self, working_dir: str) -> bool:
        """检查目录是否为有效的Git仓库
        
        Args:
            working_dir: 要检查的工作目录路径
            
        Returns:
            如果是有效的Git仓库返回True，否则返回False
        """
        if not os.path.exists(working_dir):
            return False
        
        git_dir = os.path.join(working_dir, '.git')
        return os.path.isdir(git_dir)
    
    def sync(self, working_dir: str) -> tuple[bool, str]:
        """同步代码（执行git pull）
        
        Args:
            working_dir: 工作目录路径
            
        Returns:
            元组 (是否成功, 输出信息)
            - 成功: (True, git pull输出)
            - 失败但继续: (True, 错误信息) - 失败不中断后续执行
        """
        if not self.enabled:
            logger.info("Git同步已禁用")
            return True, "Git同步已禁用"
        
        # 检查是否为Git仓库
        if not self.is_git_repo(working_dir):
            logger.warning(f"{working_dir} 不是Git仓库，跳过同步")
            return True, "不是Git仓库，跳过同步"
        
        try:
            # 执行git pull
            result = subprocess.run(
                ['git', 'pull'],
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            output = result.stdout + result.stderr
            
            if result.returncode == 0:
                logger.info(f"Git sync completed for {working_dir}")
                logger.debug(f"Git pull output: {output}")
                return True, output
            else:
                logger.error(f"Git pull failed: {output}")
                # 失败但不中断后续执行
                return True, f"Git pull失败但继续执行: {output}"
                
        except subprocess.TimeoutExpired:
            logger.error(f"Git pull timeout after {self.timeout}s")
            return True, "Git pull超时但继续执行"
        except Exception as e:
            logger.error(f"Git sync error: {e}")
            return True, f"Git同步错误但继续执行: {e}"
