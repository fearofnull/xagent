# -*- coding: utf-8 -*-
"""XAgent - Main agent implementation.

This module provides the main XAgent class built on ReActAgent,
with integrated tools, skills, and memory management.
"""
import asyncio
import logging
import os
from typing import Any, List, Literal, Optional

from agentscope.agent import ReActAgent
from agentscope.memory import InMemoryMemory
from agentscope.message import Msg
from agentscope.tool import Toolkit

from .tools import (
    execute_shell_command,
    read_file,
    write_file,
    edit_file,
    get_current_time,
    desktop_screenshot,
    send_file_to_user,
    call_cron_api,
)
from .memory import MemoryManager
from ..constant import (
    MEMORY_COMPACT_KEEP_RECENT,
    MEMORY_COMPACT_RATIO,
    WORKING_DIR,
)
from .model_factory import create_model_and_formatter

logger = logging.getLogger(__name__)


class XAgent(ReActAgent):
    """XAgent with integrated tools, skills, and memory management.

    This agent extends ReActAgent with:
    - Built-in tools (shell, file operations, browser, etc.)
    - Memory management with auto-compaction
    """

    def __init__(
        self,
        env_context: Optional[str] = None,
        enable_memory_manager: bool = True,
        memory_manager: MemoryManager | None = None,
        max_iters: int = 50,
        max_input_length: int = 128 * 1024,  # 128K = 131072 tokens
        provider_type: str = "openai",
    ):
        """Initialize XAgent.

        Args:
            env_context: Optional environment context to prepend to
                system prompt
            enable_memory_manager: Whether to enable memory manager
            memory_manager: Optional memory manager instance
            max_iters: Maximum number of reasoning-acting iterations
                (default: 50)
            max_input_length: Maximum input length in tokens for model
                context window (default: 128K = 131072)
            provider_type: Provider type (openai, claude, gemini)
        """
        self._env_context = env_context
        self._max_input_length = max_input_length

        # Memory compaction threshold: configurable ratio of max_input_length
        self._memory_compact_threshold = int(
            max_input_length * MEMORY_COMPACT_RATIO,
        )

        # Initialize toolkit with built-in tools
        toolkit = self._create_toolkit()

        # Build system prompt
        sys_prompt = self._build_sys_prompt()

        # Create model and formatter using factory method
        model, formatter = create_model_and_formatter(provider_type=provider_type)

        # Initialize parent ReActAgent
        super().__init__(
            name="Agent",
            model=model,
            sys_prompt=sys_prompt,
            toolkit=toolkit,
            memory=InMemoryMemory(),
            formatter=formatter,
            max_iters=max_iters,
        )

        # Setup memory manager
        self._setup_memory_manager(
            enable_memory_manager,
            memory_manager,
        )

    def _create_toolkit(self) -> Toolkit:
        """Create and populate toolkit with built-in tools.

        Returns:
            Configured toolkit instance
        """
        toolkit = Toolkit()

        # Register built-in tools
        toolkit.register_tool_function(execute_shell_command)
        toolkit.register_tool_function(read_file)
        toolkit.register_tool_function(write_file)
        toolkit.register_tool_function(edit_file)
        toolkit.register_tool_function(get_current_time)
        toolkit.register_tool_function(desktop_screenshot)
        toolkit.register_tool_function(send_file_to_user)
        toolkit.register_tool_function(call_cron_api)

        # Register skills from active_skills directory
        self._register_skills(toolkit)

        return toolkit

    def _register_skills(self, toolkit: Toolkit) -> None:
        """Load and register skills from working directory.

        Args:
            toolkit: Toolkit to register skills to
        """
        from .skills_manager import (
            ensure_skills_initialized,
            get_active_skills_dir,
            list_available_skills,
        )

        # Check skills initialization
        ensure_skills_initialized()

        working_skills_dir = get_active_skills_dir()
        available_skills = list_available_skills()

        for skill_name in available_skills:
            skill_dir = working_skills_dir / skill_name
            if skill_dir.exists():
                try:
                    toolkit.register_agent_skill(str(skill_dir))
                    logger.debug("Registered skill: %s", skill_name)
                except Exception as e:
                    logger.error(
                        "Failed to register skill '%s': %s",
                        skill_name,
                        e,
                    )

    def _build_sys_prompt(self) -> str:
        """Build system prompt from working dir files and env context.

        Returns:
            Complete system prompt string
        """
        sys_prompt = "You are a helpful AI assistant."
        if self._env_context is not None:
            sys_prompt = self._env_context + "\n\n" + sys_prompt
        return sys_prompt

    def _setup_memory_manager(
        self,
        enable_memory_manager: bool,
        memory_manager: MemoryManager | None,
    ) -> None:
        """Setup memory manager and register memory search tool if enabled.

        Args:
            enable_memory_manager: Whether to enable memory manager
            memory_manager: Optional memory manager instance
        """
        # Check env var: if ENABLE_MEMORY_MANAGER=false, disable memory manager
        env_enable_mm = os.getenv("ENABLE_MEMORY_MANAGER", "")
        if env_enable_mm.lower() == "false":
            enable_memory_manager = False

        self._enable_memory_manager: bool = enable_memory_manager
        self.memory_manager = memory_manager

        # Register memory_search tool if enabled and available
        if self._enable_memory_manager and self.memory_manager is not None:
            # update memory manager
            self.memory_manager.chat_model = self.model
            self.memory_manager.formatter = self.formatter
            memory_toolkit = Toolkit()
            memory_toolkit.register_tool_function(read_file)
            memory_toolkit.register_tool_function(write_file)
            memory_toolkit.register_tool_function(edit_file)
            self.memory_manager.toolkit = memory_toolkit

            self.memory = self.memory_manager.get_in_memory_memory()

            logger.debug("Memory manager setup completed")

    async def reply(
        self,
        msg: Msg | list[Msg] | None = None,
        structured_model: Any | None = None,
    ) -> Msg:
        """Override reply to process file blocks and handle commands.

        Args:
            msg: Input message(s) from user
            structured_model: Optional pydantic model for structured output

        Returns:
            Response message
        """
        # Normal message processing
        return await super().reply(msg=msg, structured_model=structured_model)


__all__ = [
    "XAgent",
]