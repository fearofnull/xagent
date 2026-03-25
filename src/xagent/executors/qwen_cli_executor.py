"""
Qwen Code CLI 执行器

执行 Qwen Code CLI 命令，支持 headless 模式和原生会话管理。
参考文档: https://qwenlm.github.io/qwen-code-docs/zh/users/features/headless/
"""
import platform
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


class QwenCLIExecutor(AICLIExecutor):
    """Qwen Code CLI 执行器

    执行 Qwen Code CLI 命令，支持：
    - 工作目录管理（cwd）
    - 原生会话管理（--resume <session_id>）
    - 用户会话映射（user_id -> qwen_session_id）
    - 会话持久化存储
    - JSON 输出格式解析
    """

    def __init__(
        self,
        target_dir: str,
        timeout: int = 600,
        use_native_session: bool = True,
        session_storage_path: str = "./data/executor_sessions.json"
    ):
        super().__init__(target_dir, timeout)
        self.use_native_session = use_native_session
        self.session_storage_path = session_storage_path
        self.session_map: Dict[str, Optional[str]] = {}  # user_id -> qwen_session_id

        self.git_sync = GitSyncModule(enabled=True, timeout=30)
        self.load_session_mappings()

    def get_command_name(self) -> str:
        return "qwen.cmd" if platform.system() == "Windows" else "qwen"

    def get_provider_name(self) -> str:
        return "qwen-cli"

    def verify_directory(self) -> bool:
        return self._verify_directory_exists()

    def get_or_create_session(self, user_id: str) -> Optional[str]:
        if not self.use_native_session:
            return None
        if user_id not in self.session_map:
            self.session_map[user_id] = None
        return self.session_map.get(user_id)

    def build_command_args(
        self,
        user_prompt: str,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """构建 Qwen Code CLI headless 命令参数

        格式：qwen --yolo [--continue] [--resume <session_id>] --output-format json
        """
        args = [self.get_command_name()]

        # 自动批准所有操作（headless 必须）
        args.append("--yolo")

        # 会话恢复
        if self.use_native_session and additional_params:
            user_id = additional_params.get("user_id")
            if user_id:
                session_id = self.get_or_create_session(user_id)
                if session_id:
                    args.extend(["--resume", session_id])
                else:
                    # 没有会话 ID 时使用 --continue 继续当前项目的最新会话
                    args.append("--continue")

        # JSON 输出，便于解析 session_id 和 result
        args.extend(["--output-format", "json"])

        return args

    def execute(
        self,
        user_prompt: str,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        # Git 同步
        logger.info(f"Syncing Git repository: {self.target_dir}")
        sync_success, sync_output = self.git_sync.sync(self.target_dir)
        if not sync_success:
            logger.warning(f"Git sync failed but continuing: {sync_output}")

        if not self.verify_directory():
            error_msg = f"目标目录不存在: {self.target_dir}"
            logger.error(error_msg)
            return ExecutionResult(
                success=False, stdout="", stderr="",
                error_message=error_msg, execution_time=0
            )

        command_args = self.build_command_args(user_prompt, additional_params)
        logger.info(f"Executing Qwen CLI command: {' '.join(command_args[:3])}...")

        try:
            start_time = time.time()
            # 用安全规则包装用户提示
            wrapped_prompt = self._wrap_prompt_with_security_rules(user_prompt)
            
            result = subprocess.run(
                command_args,
                cwd=self.target_dir,
                capture_output=True,
                text=True,
                encoding='utf-8',
                input=wrapped_prompt,
                timeout=self.timeout
            )
            execution_time = time.time() - start_time

            logger.info(
                f"Qwen CLI execution completed: return_code={result.returncode}, "
                f"execution_time={execution_time:.2f}s, "
                f"stdout_length={len(result.stdout)}, stderr_length={len(result.stderr)}"
            )

            response_text = result.stdout

            if result.returncode == 0 and result.stdout.strip():
                try:
                    # Qwen Code 输出 JSON 数组，格式：[{type: "system", ...}, {type: "assistant", ...}, {type: "result", ...}]
                    messages = json.loads(result.stdout)
                    if isinstance(messages, list):
                        # 优先取 result 消息的 result 字段
                        for msg in messages:
                            if isinstance(msg, dict) and msg.get("type") == "result":
                                response_text = msg.get("result", result.stdout)
                                break
                        else:
                            # 没有 result 消息，取最后一条 assistant 消息的文本
                            for msg in reversed(messages):
                                if isinstance(msg, dict) and msg.get("type") == "assistant":
                                    message_data = msg.get("message", {})
                                    content = message_data.get("content", [])
                                    if isinstance(content, list):
                                        texts = [c.get("text", "") for c in content if c.get("type") == "text"]
                                        if texts:
                                            response_text = "\n".join(texts)
                                            break
                                    elif isinstance(content, str):
                                        response_text = content
                                        break

                        # 提取 session_id（从任意消息中取）
                        if self.use_native_session and additional_params:
                            user_id = additional_params.get("user_id")
                            if user_id:
                                for msg in messages:
                                    if isinstance(msg, dict):
                                        sid = msg.get("session_id")
                                        if sid:
                                            self.update_session_id(user_id, sid)
                                            break

                except json.JSONDecodeError:
                    logger.warning("Failed to parse Qwen CLI JSON output, using raw output")
                    response_text = result.stdout

            execution_result = ExecutionResult(
                success=result.returncode == 0,
                stdout=response_text,
                stderr=result.stderr,
                error_message=None if result.returncode == 0 else f"命令执行失败，返回码: {result.returncode}",
                execution_time=execution_time
            )
            original_user_prompt = additional_params.get('original_message') if additional_params else None
            return self._apply_hooks(execution_result, additional_params, original_user_prompt)

        except subprocess.TimeoutExpired:
            error_msg = f"命令执行超时（{self.timeout} 秒）"
            logger.error(error_msg)
            return ExecutionResult(
                success=False, stdout="", stderr="",
                error_message=error_msg, execution_time=self.timeout
            )
        except FileNotFoundError:
            error_msg = f"Qwen Code CLI 未安装或不在 PATH 中: {self.get_command_name()}"
            logger.error(error_msg)
            return ExecutionResult(
                success=False, stdout="", stderr="",
                error_message=error_msg, execution_time=0
            )
        except Exception as e:
            error_msg = f"执行命令时发生错误: {e}"
            logger.error(error_msg, exc_info=True)
            return ExecutionResult(
                success=False, stdout="", stderr=str(e),
                error_message=error_msg, execution_time=0
            )

    def update_session_id(self, user_id: str, session_id: str) -> None:
        if self.use_native_session:
            self.session_map[user_id] = session_id
            self.save_session_mappings()

    def clear_session(self, user_id: str) -> None:
        if user_id in self.session_map:
            del self.session_map[user_id]
            self.save_session_mappings()

    def save_session_mappings(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.session_storage_path), exist_ok=True)
            lock_path = f"{self.session_storage_path}.lock"
            with FileLock(lock_path, timeout=10):
                data = {}
                if os.path.exists(self.session_storage_path):
                    with open(self.session_storage_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                data['qwen_cli_sessions'] = self.session_map
                with open(self.session_storage_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存 Qwen CLI 会话映射失败: {e}")

    def load_session_mappings(self) -> None:
        try:
            if os.path.exists(self.session_storage_path):
                with open(self.session_storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.session_map = data.get('qwen_cli_sessions', {})
        except Exception as e:
            logger.warning(f"加载 Qwen CLI 会话映射失败: {e}")
            self.session_map = {}
