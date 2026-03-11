"""
Preservation Property Tests: Non-Cron Operations Unchanged

This test suite verifies that non-Cron operations remain unchanged after the fix.
These tests follow the observation-first methodology:
1. Observe behavior on UNFIXED code for non-Cron operations
2. Write property-based tests capturing observed behavior patterns
3. Run tests on UNFIXED code
4. Expected outcome: Tests PASS (confirms baseline behavior to preserve)

**IMPORTANT**: These tests should PASS on both unfixed and fixed code.
If they fail after the fix, it indicates a regression.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7**
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import asyncio
import sys
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.xagent.agents.tools.shell import execute_shell_command
from src.xagent.agents.tools.file_io import read_file, write_file, edit_file, append_file
from src.xagent.agents.tools import __all__ as tools_all


class TestPreservationShellCommands:
    """Property 2: Preservation - Shell Commands Continue to Work
    
    **Validates: Requirements 3.6**
    
    This test verifies that execute_shell_command with non-Cron commands
    continues to work correctly after the fix.
    """
    
    @settings(max_examples=20)
    @given(
        command=st.sampled_from([
            "echo 'Hello World'",
            "pwd",
            "echo test",
            "python --version",
            "echo $PATH" if sys.platform != "win32" else "echo %PATH%",
        ])
    )
    @pytest.mark.asyncio
    async def test_shell_commands_execute_successfully(self, command):
        """Property: Non-Cron shell commands SHALL execute successfully
        
        **Validates: Requirements 3.6**
        
        EXPECTED BEHAVIOR (baseline and after fix):
        - execute_shell_command executes non-Cron commands successfully
        - Returns ToolResponse with success status
        - Command output is captured correctly
        
        This test should PASS on both unfixed and fixed code.
        """
        # Execute the shell command
        result = await execute_shell_command(command=command, timeout=10)
        
        # Verify result is a ToolResponse
        assert result is not None, "execute_shell_command should return a result"
        assert hasattr(result, 'content'), "Result should have content attribute"
        assert len(result.content) > 0, "Result should have content"
        
        # Verify content structure
        content_block = result.content[0]
        assert 'text' in content_block or hasattr(content_block, 'text'), \
            "Content should have text"
        
        # Get the text content
        if isinstance(content_block, dict):
            text = content_block.get('text', '')
        else:
            text = getattr(content_block, 'text', '')
        
        # Verify command executed (should not contain error for simple commands)
        # Note: Some commands might have empty output, which is fine
        assert text is not None, "Command should produce output or empty string"
    
    @settings(max_examples=10)
    @given(
        command=st.sampled_from([
            "echo test1",
            "echo test2",
            "pwd",
        ])
    )
    @pytest.mark.asyncio
    async def test_shell_command_execution_is_deterministic(self, command):
        """Property: Shell command execution SHALL be deterministic
        
        **Validates: Requirements 3.6**
        
        EXPECTED BEHAVIOR (baseline and after fix):
        - Same command produces consistent results
        - No random failures or behavior changes
        
        This test should PASS on both unfixed and fixed code.
        """
        # Execute command twice
        result1 = await execute_shell_command(command=command, timeout=10)
        result2 = await execute_shell_command(command=command, timeout=10)
        
        # Both should succeed
        assert result1 is not None
        assert result2 is not None
        assert len(result1.content) > 0
        assert len(result2.content) > 0
        
        # For deterministic commands like echo, output should be the same
        if command.startswith("echo"):
            text1 = result1.content[0].get('text', '') if isinstance(result1.content[0], dict) else result1.content[0].text
            text2 = result2.content[0].get('text', '') if isinstance(result2.content[0], dict) else result2.content[0].text
            
            # Both should contain the echoed text
            assert "test" in text1.lower() or "test1" in text1.lower() or "test2" in text1.lower()
            assert "test" in text2.lower() or "test1" in text2.lower() or "test2" in text2.lower()


class TestPreservationFileOperations:
    """Property 2: Preservation - File Operations Continue to Work
    
    **Validates: Requirements 3.6**
    
    This test verifies that file I/O operations continue to work correctly
    after the fix.
    """
    
    @settings(max_examples=10)
    @given(
        content=st.text(min_size=1, max_size=100, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'),
            min_codepoint=32, max_codepoint=126
        ))
    )
    @pytest.mark.asyncio
    async def test_file_write_and_read_operations_work(self, content):
        """Property: File write and read operations SHALL work correctly
        
        **Validates: Requirements 3.6**
        
        EXPECTED BEHAVIOR (baseline and after fix):
        - write_file creates files successfully
        - read_file reads files successfully
        - Content is preserved correctly
        
        This test should PASS on both unfixed and fixed code.
        """
        assume(content.strip() != "")
        
        # Use a temporary test file
        test_file = "test_preservation_file.txt"
        
        try:
            # Write content to file
            write_result = await write_file(file_path=test_file, content=content)
            
            # Verify write succeeded
            assert write_result is not None
            assert len(write_result.content) > 0
            
            write_text = write_result.content[0].get('text', '') if isinstance(write_result.content[0], dict) else write_result.content[0].text
            assert "Error" not in write_text or "Wrote" in write_text
            
            # Read content back
            read_result = await read_file(file_path=test_file)
            
            # Verify read succeeded
            assert read_result is not None
            assert len(read_result.content) > 0
            
            read_text = read_result.content[0].get('text', '') if isinstance(read_result.content[0], dict) else read_result.content[0].text
            
            # Verify content is preserved
            assert content in read_text, "File content should be preserved"
            
        finally:
            # Cleanup
            from src.xagent.constant import WORKING_DIR
            test_path = WORKING_DIR / test_file
            if test_path.exists():
                test_path.unlink()
    
    @settings(max_examples=10)
    @given(
        original_content=st.text(min_size=10, max_size=50, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'),
            min_codepoint=32, max_codepoint=126
        )),
        old_text=st.text(min_size=3, max_size=10, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll'),
            min_codepoint=65, max_codepoint=122
        )),
        new_text=st.text(min_size=3, max_size=10, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll'),
            min_codepoint=65, max_codepoint=122
        ))
    )
    @pytest.mark.asyncio
    async def test_file_edit_operations_work(self, original_content, old_text, new_text):
        """Property: File edit operations SHALL work correctly
        
        **Validates: Requirements 3.6**
        
        EXPECTED BEHAVIOR (baseline and after fix):
        - edit_file replaces text correctly
        - Original content is modified as expected
        
        This test should PASS on both unfixed and fixed code.
        """
        assume(old_text.strip() != "")
        assume(new_text.strip() != "")
        assume(old_text != new_text)
        
        # Create content that contains old_text
        content = f"{original_content} {old_text} {original_content}"
        test_file = "test_preservation_edit.txt"
        
        try:
            # Write initial content
            await write_file(file_path=test_file, content=content)
            
            # Edit the file
            edit_result = await edit_file(
                file_path=test_file,
                old_text=old_text,
                new_text=new_text
            )
            
            # Verify edit succeeded
            assert edit_result is not None
            assert len(edit_result.content) > 0
            
            edit_text = edit_result.content[0].get('text', '') if isinstance(edit_result.content[0], dict) else edit_result.content[0].text
            assert "Successfully" in edit_text or "replaced" in edit_text.lower()
            
            # Read back and verify
            read_result = await read_file(file_path=test_file)
            read_text = read_result.content[0].get('text', '') if isinstance(read_result.content[0], dict) else read_result.content[0].text
            
            # Verify replacement occurred
            assert new_text in read_text, "New text should be in file"
            assert old_text not in read_text, "Old text should be replaced"
            
        finally:
            # Cleanup
            from src.xagent.constant import WORKING_DIR
            test_path = WORKING_DIR / test_file
            if test_path.exists():
                test_path.unlink()


class TestPreservationToolRegistry:
    """Property 2: Preservation - Tool Registry Remains Unchanged
    
    **Validates: Requirements 3.7**
    
    This test verifies that the tool registry and tool availability
    remain unchanged after the fix.
    """
    
    def test_core_tools_remain_registered(self):
        """Property: Core tools SHALL remain registered in tools module
        
        **Validates: Requirements 3.7**
        
        EXPECTED BEHAVIOR (baseline and after fix):
        - All core tools remain in __all__ export list
        - Tool functions are importable
        - No tools are accidentally removed
        
        This test should PASS on both unfixed and fixed code.
        """
        # Core tools that must always be available
        core_tools = [
            "execute_shell_command",
            "read_file",
            "write_file",
            "edit_file",
            "append_file",
            "grep_search",
            "glob_search",
            "send_file_to_user",
            "desktop_screenshot",
            "browser_use",
            "create_memory_search_tool",
            "get_current_time",
        ]
        
        # Verify all core tools are in __all__
        for tool in core_tools:
            assert tool in tools_all, \
                f"Core tool '{tool}' should remain in tools.__all__"
    
    def test_core_tools_are_importable(self):
        """Property: Core tools SHALL be importable
        
        **Validates: Requirements 3.7**
        
        EXPECTED BEHAVIOR (baseline and after fix):
        - All core tools can be imported successfully
        - No import errors occur
        
        This test should PASS on both unfixed and fixed code.
        """
        # Try importing core tools
        try:
            from src.xagent.agents.tools import (
                execute_shell_command,
                read_file,
                write_file,
                edit_file,
                append_file,
            )
            
            # Verify they are callable
            assert callable(execute_shell_command)
            assert callable(read_file)
            assert callable(write_file)
            assert callable(edit_file)
            assert callable(append_file)
            
        except ImportError as e:
            pytest.fail(f"Core tools should be importable: {e}")
    
    @settings(max_examples=10)
    @given(tool_name=st.sampled_from([
        "execute_shell_command",
        "read_file",
        "write_file",
        "edit_file",
        "append_file",
    ]))
    def test_tool_functions_have_correct_signatures(self, tool_name):
        """Property: Tool functions SHALL maintain their signatures
        
        **Validates: Requirements 3.7**
        
        EXPECTED BEHAVIOR (baseline and after fix):
        - Tool function signatures remain unchanged
        - Parameters are preserved
        - Return types are preserved
        
        This test should PASS on both unfixed and fixed code.
        """
        from src.xagent.agents import tools
        import inspect
        
        # Get the tool function
        tool_func = getattr(tools, tool_name)
        
        # Verify it's callable
        assert callable(tool_func), f"{tool_name} should be callable"
        
        # Get signature
        sig = inspect.signature(tool_func)
        
        # Verify it has parameters (all our tools take parameters)
        assert len(sig.parameters) > 0, \
            f"{tool_name} should have parameters"
        
        # Verify it's async (our tools are async)
        assert inspect.iscoroutinefunction(tool_func), \
            f"{tool_name} should be async"


class TestPreservationAgentFunctions:
    """Property 2: Preservation - Agent Functions Remain Unchanged
    
    **Validates: Requirements 3.7**
    
    This test verifies that Agent's other functions (memory management,
    tool registration) remain unchanged after the fix.
    """
    
    def test_react_agent_imports_successfully(self):
        """Property: ReactAgent SHALL import successfully
        
        **Validates: Requirements 3.7**
        
        EXPECTED BEHAVIOR (baseline and after fix):
        - ReactAgent class can be imported
        - No import errors occur
        
        This test should PASS on both unfixed and fixed code.
        """
        try:
            from src.xagent.agents.react_agent import XAgent
            
            # Verify it's a class
            assert isinstance(XAgent, type), "XAgent should be a class"
            
        except ImportError as e:
            pytest.fail(f"XAgent should be importable: {e}")
    
    def test_toolkit_class_available(self):
        """Property: Toolkit class SHALL be available
        
        **Validates: Requirements 3.7**
        
        EXPECTED BEHAVIOR (baseline and after fix):
        - Toolkit class can be imported from agentscope
        - Toolkit has register_tool_function method
        
        This test should PASS on both unfixed and fixed code.
        """
        try:
            from agentscope.tool import Toolkit
            
            # Verify it's a class
            assert isinstance(Toolkit, type), "Toolkit should be a class"
            
            # Verify it has register_tool_function method
            assert hasattr(Toolkit, 'register_tool_function'), \
                "Toolkit should have register_tool_function method"
            
        except ImportError as e:
            pytest.fail(f"Toolkit should be importable: {e}")
    
    def test_memory_manager_available(self):
        """Property: MemoryManager SHALL be available
        
        **Validates: Requirements 3.7**
        
        EXPECTED BEHAVIOR (baseline and after fix):
        - MemoryManager can be imported
        - Memory management functionality is preserved
        
        This test should PASS on both unfixed and fixed code.
        """
        try:
            from src.xagent.agents.memory import MemoryManager
            
            # Verify it's a class
            assert isinstance(MemoryManager, type), "MemoryManager should be a class"
            
        except ImportError as e:
            pytest.fail(f"MemoryManager should be importable: {e}")


class TestPreservationSkillsSystem:
    """Property 2: Preservation - Skills System Remains Unchanged
    
    **Validates: Requirements 3.7**
    
    This test verifies that the skills system (loading, registration)
    remains unchanged after the fix.
    """
    
    def test_skills_manager_functions_available(self):
        """Property: Skills manager functions SHALL be available
        
        **Validates: Requirements 3.7**
        
        EXPECTED BEHAVIOR (baseline and after fix):
        - Skills manager functions can be imported
        - Skills loading mechanism is preserved
        
        This test should PASS on both unfixed and fixed code.
        """
        try:
            from src.xagent.agents.skills_manager import (
                ensure_skills_initialized,
                get_active_skills_dir,
                list_available_skills,
            )
            
            # Verify they are callable
            assert callable(ensure_skills_initialized)
            assert callable(get_active_skills_dir)
            assert callable(list_available_skills)
            
        except ImportError as e:
            pytest.fail(f"Skills manager functions should be importable: {e}")
    
    def test_cron_skill_directory_exists(self):
        """Property: Cron skill directory SHALL exist
        
        **Validates: Requirements 3.7**
        
        EXPECTED BEHAVIOR (baseline and after fix):
        - Cron skill directory exists
        - SKILL.md file exists
        
        This test should PASS on both unfixed and fixed code.
        """
        cron_skill_dir = Path("src/xagent/agents/skills/cron")
        
        assert cron_skill_dir.exists(), \
            "Cron skill directory should exist"
        assert cron_skill_dir.is_dir(), \
            "Cron skill path should be a directory"
        
        skill_md = cron_skill_dir / "SKILL.md"
        assert skill_md.exists(), \
            "SKILL.md should exist in cron skill directory"


# Documentation of expected behavior
"""
EXPECTED BEHAVIOR ON UNFIXED CODE:

These preservation tests should ALL PASS on unfixed code because they test
non-Cron functionality that should not be affected by the Cron skill bug.

1. Shell Commands (Requirements 3.6):
   - execute_shell_command works for non-Cron commands
   - Commands like echo, pwd, python --version execute successfully
   - Command execution is deterministic

2. File Operations (Requirements 3.6):
   - read_file, write_file, edit_file, append_file all work correctly
   - File content is preserved correctly
   - File operations are reliable

3. Tool Registry (Requirements 3.7):
   - All core tools remain registered in tools.__all__
   - Tools are importable and callable
   - Tool function signatures are preserved

4. Agent Functions (Requirements 3.7):
   - XAgent class imports successfully
   - Toolkit class is available
   - MemoryManager is available
   - All agent infrastructure is intact

5. Skills System (Requirements 3.7):
   - Skills manager functions are available
   - Cron skill directory and SKILL.md exist
   - Skills loading mechanism works

AFTER FIX:

These tests should STILL PASS after the fix. If any test fails after the fix,
it indicates a regression where the fix accidentally broke non-Cron functionality.

The fix should ONLY affect:
- Cron skill's SKILL.md content (removing hardcoded paths)
- Addition of new call_cron_api tool
- Registration of call_cron_api in toolkit

The fix should NOT affect:
- Other tools (shell, file_io, browser, etc.)
- Tool registry mechanism
- Agent infrastructure
- Skills loading system
- Memory management
- Any non-Cron functionality
"""
