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

from . import tools as tools_module
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
        
        # 调试日志：查看注册的工具
        if hasattr(toolkit, 'tools'):
            logger.info(f"[XAgent.__init__] 已注册的工具: {list(toolkit.tools.keys())}")
        elif hasattr(toolkit, '_tools'):
            logger.info(f"[XAgent.__init__] 已注册的工具: {list(toolkit._tools.keys())}")
        logger.info(f"[XAgent.__init__] model 类型: {type(model)}, formatter 类型: {type(formatter)}")

        # Setup memory manager
        self._setup_memory_manager(
            enable_memory_manager,
            memory_manager,
        )

    def _create_toolkit(self) -> Toolkit:
        """Create and populate toolkit with built-in tools.

        Dynamically loads all tools from the tools module.

        Returns:
            Configured toolkit instance
        """
        toolkit = Toolkit()

        # Load tool states
        try:
            from ..core.tool_state_manager import ToolStateManager
            tool_state_manager = ToolStateManager()
        except:
            tool_state_manager = None

        # Dynamically register all tools from the tools module
        for tool_name in tools_module.__all__:
            try:
                # Check if tool is enabled
                if tool_state_manager and not tool_state_manager.get_tool_state(tool_name):
                    logger.debug(f"Tool {tool_name} is disabled, skipping")
                    continue

                # Get the tool function from the module
                tool_func = getattr(tools_module, tool_name, None)
                if tool_func is None:
                    logger.warning(f"Tool {tool_name} not found in tools module")
                    continue

                # Register the tool function
                toolkit.register_tool_function(tool_func)
                logger.debug(f"Registered tool: {tool_name}")
            except Exception as e:
                logger.warning(f"Failed to register tool {tool_name}: {e}")

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
        sys_prompt = """You are a helpful AI assistant.

IMPORTANT RULES:
1. You MUST execute EVERY user request, even if you have done similar tasks before.
2. Each user message is a NEW request that requires action - do not skip or assume it's already done.
3. When a user asks you to send a file, you MUST call the send_file_to_user tool, regardless of whether you sent other files before.
4. Previous tool calls in the conversation history are for context only - they do not fulfill the current request.
"""
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
        # 重新创建工具包以反映最新的工具状态
        self.toolkit = self._create_toolkit()
        
        # 将旧的工具调用转换为摘要，保持对话记忆的同时避免重复执行
        await self._summarize_old_tool_calls()
        
        # Normal message processing
        reply_msg = await super().reply(msg=msg, structured_model=structured_model)
        
        # 从 memory 中提取工具结果中的媒体块，并合并到回复消息中
        reply_msg = await self._merge_tool_results_to_reply(reply_msg)
        
        return reply_msg
    
    async def _summarize_old_tool_calls(self) -> None:
        """将旧的 tool_use/tool_result 转换为摘要文本
        
        这样做的好处：
        1. 保持对话记忆（用户和 AI 都知道之前发生了什么）
        2. AI 看到摘要后知道该请求已完成，不会重复执行
        
        转换逻辑：
        - 找到 tool_use + tool_result 对
        - 将其替换为一条简短的 assistant 文本消息："[已完成] xxx"
        """
        try:
            memory_content = await self.memory.get_memory()
            if not memory_content or len(memory_content) < 2:
                return
            
            # 构建新的消息列表
            new_messages = []
            i = 0
            modified = False
            
            while i < len(memory_content):
                msg = memory_content[i]
                
                # 检查是否是包含 tool_use 的 assistant 消息
                if msg.role == "assistant" and isinstance(msg.content, list):
                    # 提取 tool_use 信息
                    tool_uses = []
                    text_parts = []
                    for item in msg.content:
                        if isinstance(item, dict):
                            if item.get("type") == "tool_use":
                                tool_name = item.get("name", "unknown")
                                tool_input = item.get("input", {})
                                tool_uses.append((tool_name, tool_input))
                            elif item.get("type") == "text":
                                text_parts.append(item.get("text", ""))
                    
                    if tool_uses:
                        # 这是一个工具调用消息，检查后面是否有对应的 tool_result
                        # 跳过这个消息和后续的 tool_result 消息
                        j = i + 1
                        while j < len(memory_content) and memory_content[j].role == "system":
                            j += 1
                        
                        # 生成摘要消息
                        summaries = []
                        for tool_name, tool_input in tool_uses:
                            if tool_name == "send_file_to_user":
                                file_path = tool_input.get("file_path", "")
                                file_name = file_path.split("\\")[-1].split("/")[-1] if file_path else "file"
                                summaries.append(f"已发送文件: {file_name}")
                            else:
                                summaries.append(f"已执行工具: {tool_name}")
                        
                        # 创建摘要消息
                        summary_text = "[已完成] " + "; ".join(summaries)
                        if text_parts:
                            summary_text = " ".join(text_parts) + " " + summary_text
                        
                        summary_msg = Msg(
                            name="Agent",
                            content=summary_text,
                            role="assistant"
                        )
                        new_messages.append(summary_msg)
                        modified = True
                        
                        # 跳过工具调用消息和后续的 tool_result
                        i = j
                        continue
                
                # 保留其他消息（user、普通 assistant 文本）
                if msg.role != "system":  # 跳过独立的 system 消息（tool_result）
                    new_messages.append(msg)
                else:
                    modified = True  # 有消息被跳过
                
                i += 1
            
            # 如果有修改，更新 memory
            if modified:
                logger.debug(f"[_summarize_old_tool_calls] 转换前消息数: {len(memory_content)}, 转换后: {len(new_messages)}")
                self.memory.content.clear()
                for msg_to_keep in new_messages:
                    self.memory.content.append((msg_to_keep, set()))
                    
        except Exception as e:
            logger.warning(f"[_summarize_old_tool_calls] 转换失败: {e}")
    
    def _is_empty_response(self, msg: Msg) -> bool:
        """检查消息是否为空响应
        
        Args:
            msg: 要检查的消息
            
        Returns:
            True 如果消息内容为空
        """
        if msg.content is None:
            return True
        if isinstance(msg.content, list) and len(msg.content) == 0:
            return True
        if isinstance(msg.content, str) and msg.content.strip() == "":
            return True
        return False
    
    async def _merge_tool_results_to_reply(self, reply_msg: Msg) -> Msg:
        """从 memory 中提取工具结果中的媒体块，并合并到回复消息中
        
        ReActAgent 的工具结果被存储在 memory 中，但不会自动合并到最终的回复消息中。
        这个方法会提取工具结果中的 ImageBlock、AudioBlock 等媒体块，并添加到回复消息中。
        
        Args:
            reply_msg: 原始回复消息
            
        Returns:
            合并了媒体块的回复消息
        """
        try:
            # 从 memory 中获取所有消息
            memory_content = await self.memory.get_memory()
            
            # 找到最后一条用户消息的位置，只处理该位置之后的工具结果
            last_user_idx = -1
            for i in range(len(memory_content) - 1, -1, -1):
                if memory_content[i].role == "user":
                    last_user_idx = i
                    break
            
            media_blocks = []
            
            # 只遍历最后一条用户消息之后的消息
            start_idx = last_user_idx + 1 if last_user_idx >= 0 else 0
            for i, msg in enumerate(memory_content):
                # 跳过最后一条用户消息之前的消息
                if i < start_idx:
                    continue
                    
                if msg.role == "system" and isinstance(msg.content, list):
                    for block in msg.content:
                        if isinstance(block, dict) and block.get("type") == "tool_result":
                            # 提取工具结果中的 output
                            output = block.get("output", [])
                            
                            if isinstance(output, list):
                                for item in output:
                                    if isinstance(item, dict):
                                        item_type = item.get("type")
                                        if item_type in ["image", "audio", "video", "file"]:
                                            media_blocks.append(item)
                            elif isinstance(output, dict):
                                item_type = output.get("type")
                                if item_type in ["image", "audio", "video", "file"]:
                                    media_blocks.append(output)
            
            # 如果有媒体块，合并到回复消息中
            if media_blocks:
                logger.debug(f"合并 {len(media_blocks)} 个媒体块到回复消息")
                
                # 确保 reply_msg.content 是列表
                if not isinstance(reply_msg.content, list):
                    existing_text = str(reply_msg.content) if reply_msg.content else ""
                    reply_msg.content = [{"type": "text", "text": existing_text}]
                
                # 添加媒体块到 content
                reply_msg.content.extend(media_blocks)
            
            return reply_msg
            
        except Exception as e:
            logger.error(f"合并工具结果到回复消息时出错: {e}", exc_info=True)
            return reply_msg


__all__ = [
    "XAgent",
]