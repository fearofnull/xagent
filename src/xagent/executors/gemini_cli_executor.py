"""
Gemini CLI 执行器

执行 Gemini CLI 命令，支持 Gemini CLI 的原生会话管理。
"""
import subprocess
import time
import json
import os
import logging
from typing import Optional, List, Dict, Any
from filelock import FileLock
from .ai_cli_executor import AICLIExecutor
from ..models import ExecutionResult
from ..utils.git_sync import GitSyncModule

logger = logging.getLogger(__name__)


class GeminiCLIExecutor(AICLIExecutor):
    """Gemini CLI 执行器
    
    执行 Gemini CLI 命令，支持：
    - 工作目录管理（--cwd）
    - 原生会话管理（--session）
    - 用户会话映射（user_id -> gemini_session_id）
    - 会话持久化存储
    
    Requirements: 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 10.11, 10.13
    """
    
    def __init__(
        self,
        target_dir: str,
        timeout: int = 600,
        use_native_session: bool = True,
        session_storage_path: str = "./data/executor_sessions.json"
    ):
        """初始化 Gemini CLI 执行器
        
        Args:
            target_dir: 目标代码仓库目录
            timeout: 命令执行超时时间（秒）
            use_native_session: 是否使用 Gemini CLI 的原生会话管理
            session_storage_path: 会话映射存储路径
        """
        super().__init__(target_dir, timeout)
        self.use_native_session = use_native_session
        self.session_storage_path = session_storage_path
        self.session_map: Dict[str, Optional[str]] = {}  # user_id -> gemini_session_id
        
        # 初始化Git同步模块（需求5：CLI层Git自动同步）
        self.git_sync = GitSyncModule(enabled=True, timeout=30)
        
        # 加载会话映射
        self.load_session_mappings()
    
    def get_command_name(self) -> str:
        """返回 Gemini CLI 命令名称
        
        Windows 上需要使用 gemini.cmd，Unix-like 使用 gemini
        
        Returns:
            命令名称 "gemini.cmd" (Windows) 或 "gemini" (Unix-like)
        """
        import platform
        return "gemini.cmd" if platform.system() == "Windows" else "gemini"
    
    def get_provider_name(self) -> str:
        """返回提供商名称
        
        Returns:
            提供商名称
        """
        return "gemini-cli"
    
    def verify_directory(self) -> bool:
        """验证目标目录是否存在
        
        Returns:
            True 如果目录存在且可访问
        """
        return self._verify_directory_exists()
    
    def get_or_create_gemini_session(self, user_id: str) -> Optional[str]:
        """获取或创建 Gemini CLI 会话
        
        如果启用了原生会话管理，为每个用户维护一个 Gemini CLI 会话。
        首次执行时会话 ID 为 None，Gemini CLI 会自动生成。
        
        Args:
            user_id: 用户 ID
            
        Returns:
            Gemini 会话 ID，如果是首次执行则返回 None
        """
        if not self.use_native_session:
            return None
        
        if user_id not in self.session_map:
            # 创建新的会话映射，首次执行时会话 ID 为 None
            self.session_map[user_id] = None
        
        return self.session_map.get(user_id)
    
    def build_command_args(
        self,
        user_prompt: str,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """构建 Gemini CLI 命令参数
        
        Gemini CLI headless 模式要求：
        1. 查询作为位置参数（不使用 -p 标志）
        2. 使用 --resume 恢复会话
        3. 使用 --output-format json 获取结构化输出
        
        Args:
            user_prompt: 用户提示
            additional_params: 额外参数（user_id, model, temperature 等）
            
        Returns:
            命令参数列表
        """
        args = [self.get_command_name()]
        
        # 添加权限参数（需求2：CLI权限参数配置）
        # 权限参数位于命令参数列表的开头，避免权限不足导致执行失败
        args.append("--yolo")
        logger.debug(f"Added permission parameter: --yolo")
        
        # 如果启用原生会话管理，添加会话恢复参数
        if self.use_native_session and additional_params:
            user_id = additional_params.get("user_id")
            if user_id:
                session_id = self.get_or_create_gemini_session(user_id)
                if session_id:
                    args.extend(["--resume", session_id])
        
        # 使用 JSON 输出格式以便解析
        args.extend(["--output-format", "json"])
        
        # 添加额外参数
        if additional_params:
            for key, value in additional_params.items():
                # 跳过内部参数
                if key == "user_id":
                    continue
                
                # 布尔参数
                if value is True:
                    args.append(f"--{key}")
                # 其他参数
                elif value is not None:
                    args.extend([f"--{key}", str(value)])
        
        # 查询作为位置参数（必须在最后）
        args.append(user_prompt)
        
        return args
    
    def execute(
        self,
        user_prompt: str,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """执行 Gemini CLI 命令
        
        Args:
            user_prompt: 用户提示
            additional_params: 额外参数
            
        Returns:
            ExecutionResult: 执行结果
        """
        # 执行Git同步（需求5：CLI层Git自动同步）
        # 在CLI执行前自动拉取最新代码
        logger.info(f"Syncing Git repository: {self.target_dir}")
        sync_success, sync_output = self.git_sync.sync(self.target_dir)
        if sync_success:
            logger.debug(f"Git sync result: {sync_output}")
        else:
            logger.warning(f"Git sync failed but continuing: {sync_output}")
        
        # 验证目录
        if not self.verify_directory():
            error_msg = f"目标目录不存在: {self.target_dir}"
            logger.error(error_msg)
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                error_message=error_msg,
                execution_time=0
            )
        
        # 构建命令
        command_args = self.build_command_args(user_prompt, additional_params)
        logger.info(f"Executing Gemini CLI command: {' '.join(command_args[:3])}...")
        
        try:
            # 执行命令（在目标目录中执行）
            start_time = time.time()
            result = subprocess.run(
                command_args,
                cwd=self.target_dir,  # 在目标目录中执行
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=self.timeout
            )
            execution_time = time.time() - start_time
            
            logger.info(
                f"Gemini CLI execution completed: return_code={result.returncode}, "
                f"execution_time={execution_time:.2f}s, "
                f"stdout_length={len(result.stdout)}, stderr_length={len(result.stderr)}"
            )
            
            # 解析 JSON 输出
            response_text = result.stdout
            if result.returncode == 0 and result.stdout.strip():
                try:
                    # Gemini CLI 返回 JSON 格式的输出
                    output_json = json.loads(result.stdout)
                    response_text = output_json.get("response", result.stdout)
                    
                    # 提取会话 ID（如果有）
                    if self.use_native_session and additional_params:
                        user_id = additional_params.get("user_id")
                        if user_id:
                            # 从 JSON 输出中提取会话 ID
                            # 注意：需要根据实际输出格式调整
                            session_id = output_json.get("session_id") or output_json.get("sessionId")
                            if session_id:
                                self.update_session_id(user_id, session_id)
                except json.JSONDecodeError:
                    # 如果不是 JSON 格式，使用原始输出
                    logger.warning("Failed to parse Gemini CLI JSON output, using raw output")
                    response_text = result.stdout
            
            return ExecutionResult(
                success=result.returncode == 0,
                stdout=response_text,
                stderr=result.stderr,
                error_message=None if result.returncode == 0 else f"命令执行失败，返回码: {result.returncode}",
                execution_time=execution_time
            )
            
        except subprocess.TimeoutExpired:
            error_msg = f"命令执行超时（{self.timeout} 秒）"
            logger.error(error_msg)
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                error_message=error_msg,
                execution_time=self.timeout
            )
        except FileNotFoundError:
            error_msg = f"Gemini CLI 未安装或不在 PATH 中: {self.get_command_name()}"
            logger.error(error_msg)
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                error_message=error_msg,
                execution_time=0
            )
        except Exception as e:
            error_msg = f"执行命令时发生错误: {e}"
            logger.error(error_msg, exc_info=True)
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                error_message=error_msg,
                execution_time=0
            )

    
    def update_session_id(self, user_id: str, session_id: str) -> None:
        """更新用户的 Gemini CLI 会话 ID
        
        Args:
            user_id: 用户 ID
            session_id: Gemini 会话 ID
        """
        if self.use_native_session:
            self.session_map[user_id] = session_id
            self.save_session_mappings()
    
    def clear_session(self, user_id: str) -> None:
        """清除用户的 Gemini CLI 会话
        
        Args:
            user_id: 用户 ID
        """
        if user_id in self.session_map:
            del self.session_map[user_id]
            self.save_session_mappings()
    
    def save_session_mappings(self) -> None:
        """持久化会话映射到存储
        
        使用文件锁避免并发写入冲突
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.session_storage_path), exist_ok=True)
            
            # 使用文件锁
            lock_path = f"{self.session_storage_path}.lock"
            with FileLock(lock_path, timeout=10):
                # 加载现有数据
                data = {}
                if os.path.exists(self.session_storage_path):
                    with open(self.session_storage_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                
                # 更新 Gemini CLI 会话映射
                data['gemini_cli_sessions'] = self.session_map
                
                # 保存
                with open(self.session_storage_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    
        except Exception as e:
            # 记录错误但不抛出异常，避免影响主流程
            print(f"保存 Gemini CLI 会话映射失败: {e}")
    
    def load_session_mappings(self) -> None:
        """从存储加载会话映射"""
        try:
            if os.path.exists(self.session_storage_path):
                with open(self.session_storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.session_map = data.get('gemini_cli_sessions', {})
        except Exception as e:
            # 记录错误但不抛出异常，使用空映射继续
            print(f"加载 Gemini CLI 会话映射失败: {e}")
            self.session_map = {}
