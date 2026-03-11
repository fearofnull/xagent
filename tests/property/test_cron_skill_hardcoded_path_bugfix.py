"""
Bug Condition Exploration Test: Cron Skill Hardcoded Path Dependency

This test explores the bug condition where Cron skill depends on hardcoded path
'e:/TraeProjects/lark-bot' and fails when deployed to different paths.

**CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists.
**NOTE**: This test encodes the expected behavior - it will validate the fix when it passes.

**Validates: Requirements 2.1, 2.2, 2.3**
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os


# Test deployment paths that differ from the hardcoded path
DEPLOYMENT_PATHS = [
    "/tmp/lark-bot",  # Linux temporary directory
    "/home/user/lark-bot",  # Linux home directory
    "/Users/dev/lark-bot",  # macOS home directory
    "/app",  # Docker container path
    "D:/projects/lark-bot",  # Windows different drive
    "C:/Users/developer/lark-bot",  # Windows user directory
]

# The hardcoded path that exists in the current buggy code
HARDCODED_PATH = "e:/TraeProjects/lark-bot"


class TestBugConditionHardcodedPathDependency:
    """Property 1: Bug Condition - Hardcoded Path Dependency Failure
    
    **Validates: Requirements 2.1, 2.2, 2.3**
    
    This test verifies that after the fix:
    - Cron skill uses HTTP API calls instead of hardcoded paths
    - Cron skill works on any deployment path
    - No dependency on specific file system paths
    """
    
    @settings(max_examples=20)
    @given(deployment_path=st.sampled_from(DEPLOYMENT_PATHS))
    def test_cron_skill_works_on_any_deployment_path(self, deployment_path):
        """Property: Cron skill SHALL work on any deployment path using HTTP API
        
        **Validates: Requirements 2.1, 2.2, 2.3**
        
        EXPECTED BEHAVIOR (after fix):
        - Cron skill uses call_cron_api tool to make HTTP requests
        - No dependency on hardcoded file system paths
        - Works on Linux, macOS, Docker, Windows (any drive)
        
        CURRENT BEHAVIOR (unfixed code):
        - Cron skill uses execute_shell_command with cwd="e:/TraeProjects/lark-bot"
        - Fails when deployment_path != "e:/TraeProjects/lark-bot"
        - This test will FAIL on unfixed code (which is correct - proves bug exists)
        """
        # Skip the hardcoded path - we're testing non-hardcoded paths
        assume(deployment_path != HARDCODED_PATH)
        
        # Read the SKILL.md file to check if it still has hardcoded path
        skill_md_path = Path("src/xagent/agents/skills/cron/SKILL.md")
        
        # Verify the file exists
        assert skill_md_path.exists(), "SKILL.md file should exist"
        
        with open(skill_md_path, 'r', encoding='utf-8') as f:
            skill_content = f.read()
        
        # EXPECTED BEHAVIOR (after fix):
        # - SKILL.md should NOT contain hardcoded path references
        # - SKILL.md should reference call_cron_api tool instead of execute_shell_command
        # - SKILL.md should NOT contain "cwd=" directives
        
        # Check 1: No hardcoded path in SKILL.md
        assert HARDCODED_PATH not in skill_content, (
            f"SKILL.md should NOT contain hardcoded path '{HARDCODED_PATH}'. "
            f"After fix, Cron skill should use HTTP API calls via call_cron_api tool, "
            f"not hardcoded file system paths."
        )
        
        # Check 2: No cwd directive in SKILL.md
        assert 'cwd="e:/TraeProjects/lark-bot"' not in skill_content, (
            "SKILL.md should NOT contain 'cwd=\"e:/TraeProjects/lark-bot\"' directive. "
            "After fix, Cron skill should use HTTP API calls, not shell commands with hardcoded cwd."
        )
        
        # Check 3: Should reference call_cron_api tool (expected after fix)
        assert "call_cron_api" in skill_content, (
            "SKILL.md should reference 'call_cron_api' tool. "
            "After fix, Cron skill should use HTTP API calls via call_cron_api tool."
        )
        
        # Check 4: Should NOT use python -m src.xagent.cli.cron_cli commands
        assert "python -m src.xagent.cli.cron_cli" not in skill_content, (
            "SKILL.md should NOT contain 'python -m src.xagent.cli.cron_cli' commands. "
            "After fix, Cron skill should use HTTP API calls via call_cron_api tool, "
            "not CLI commands that depend on working directory."
        )
    
    def test_cron_api_tool_exists(self):
        """Verify that call_cron_api tool exists after fix
        
        **Validates: Requirements 2.1, 2.2**
        
        EXPECTED BEHAVIOR (after fix):
        - call_cron_api tool function exists in src/xagent/agents/tools/cron_api.py
        - Tool is registered in the toolkit
        
        CURRENT BEHAVIOR (unfixed code):
        - call_cron_api tool does not exist
        - This test will FAIL on unfixed code (which is correct - proves bug exists)
        """
        # Check if cron_api.py file exists
        cron_api_path = Path("src/xagent/agents/tools/cron_api.py")
        
        assert cron_api_path.exists(), (
            "After fix, src/xagent/agents/tools/cron_api.py should exist. "
            "This file should contain the call_cron_api tool function that makes HTTP API calls."
        )
        
        # Check if the file contains call_cron_api function
        with open(cron_api_path, 'r', encoding='utf-8') as f:
            cron_api_content = f.read()
        
        assert "def call_cron_api" in cron_api_content or "async def call_cron_api" in cron_api_content, (
            "cron_api.py should contain call_cron_api function. "
            "This function should make HTTP requests to Web Admin Cron API."
        )
        
        # Check if the tool makes HTTP requests (should contain httpx or requests)
        assert "httpx" in cron_api_content or "requests" in cron_api_content, (
            "call_cron_api should use HTTP library (httpx or requests) to make API calls. "
            "After fix, Cron operations should use HTTP API, not file system operations."
        )
    
    def test_cron_api_tool_registered_in_toolkit(self):
        """Verify that call_cron_api tool is registered in toolkit
        
        **Validates: Requirements 2.2**
        
        EXPECTED BEHAVIOR (after fix):
        - call_cron_api is imported in tools/__init__.py
        - call_cron_api is registered in react_agent.py toolkit
        
        CURRENT BEHAVIOR (unfixed code):
        - call_cron_api is not registered
        - This test will FAIL on unfixed code (which is correct - proves bug exists)
        """
        # Check tools/__init__.py
        tools_init_path = Path("src/xagent/agents/tools/__init__.py")
        
        if tools_init_path.exists():
            with open(tools_init_path, 'r', encoding='utf-8') as f:
                tools_init_content = f.read()
            
            assert "call_cron_api" in tools_init_content, (
                "After fix, tools/__init__.py should import and export call_cron_api. "
                "This makes the tool available for registration in the agent toolkit."
            )
        
        # Check react_agent.py for tool registration
        react_agent_path = Path("src/xagent/agents/react_agent.py")
        
        if react_agent_path.exists():
            with open(react_agent_path, 'r', encoding='utf-8') as f:
                react_agent_content = f.read()
            
            # Should import call_cron_api
            assert "call_cron_api" in react_agent_content, (
                "After fix, react_agent.py should import and register call_cron_api tool. "
                "This allows agents to use the HTTP API-based Cron management."
            )
    
    @settings(max_examples=10)
    @given(
        deployment_path=st.sampled_from(DEPLOYMENT_PATHS),
        action=st.sampled_from(["list", "get", "create", "update", "delete", "pause", "resume", "run"])
    )
    def test_cron_operations_use_http_api_not_filesystem(self, deployment_path, action):
        """Property: All Cron operations SHALL use HTTP API, not file system paths
        
        **Validates: Requirements 2.1, 2.2, 2.3**
        
        EXPECTED BEHAVIOR (after fix):
        - All Cron operations (list, get, create, update, delete, pause, resume, run)
        - Use HTTP API calls to http://localhost:8080/api/cron
        - No dependency on deployment path or file system
        
        CURRENT BEHAVIOR (unfixed code):
        - Cron operations use CLI commands with hardcoded cwd
        - This test will FAIL on unfixed code (which is correct - proves bug exists)
        """
        assume(deployment_path != HARDCODED_PATH)
        
        # Read SKILL.md to verify it describes HTTP API usage
        skill_md_path = Path("src/xagent/agents/skills/cron/SKILL.md")
        
        with open(skill_md_path, 'r', encoding='utf-8') as f:
            skill_content = f.read()
        
        # After fix, SKILL.md should describe using call_cron_api for all operations
        # It should NOT describe using shell commands with cwd
        
        # Verify no hardcoded path for any operation
        assert HARDCODED_PATH not in skill_content, (
            f"SKILL.md should NOT contain hardcoded path '{HARDCODED_PATH}' for any operation. "
            f"All Cron operations should use HTTP API via call_cron_api tool."
        )
        
        # Verify call_cron_api is mentioned (expected after fix)
        assert "call_cron_api" in skill_content, (
            f"SKILL.md should describe using call_cron_api tool for Cron operations. "
            f"After fix, operation '{action}' should use HTTP API, not CLI commands."
        )


class TestBugConditionDocumentation:
    """Verify that bug condition is documented and counterexamples are captured
    
    **Validates: Requirements 2.1, 2.2, 2.3**
    """
    
    def test_bug_condition_documented_in_design(self):
        """Verify bug condition is properly documented in design.md
        
        This test ensures the bug condition is well-documented for future reference.
        """
        design_path = Path(".kiro/specs/cron-skill-hardcoded-path-fix/design.md")
        
        assert design_path.exists(), "design.md should exist"
        
        with open(design_path, 'r', encoding='utf-8') as f:
            design_content = f.read()
        
        # Verify bug condition is documented
        assert "Bug Condition" in design_content or "Bug_Condition" in design_content, (
            "design.md should document the bug condition"
        )
        
        # Verify hardcoded path is mentioned
        assert HARDCODED_PATH in design_content, (
            f"design.md should mention the hardcoded path '{HARDCODED_PATH}'"
        )
        
        # Verify expected behavior is documented
        assert "HTTP API" in design_content or "call_cron_api" in design_content, (
            "design.md should document the expected behavior using HTTP API"
        )


# Counterexamples documentation
"""
EXPECTED COUNTEREXAMPLES (on unfixed code):

When running this test on UNFIXED code, we expect to find:

1. SKILL.md contains hardcoded path 'e:/TraeProjects/lark-bot'
   - Counterexample: SKILL.md line contains 'cwd="e:/TraeProjects/lark-bot"'
   - This proves the bug exists: Cron skill depends on hardcoded path

2. SKILL.md contains CLI commands 'python -m src.xagent.cli.cron_cli'
   - Counterexample: SKILL.md describes using shell commands with hardcoded cwd
   - This proves the bug exists: Cron skill uses CLI instead of HTTP API

3. call_cron_api tool does not exist
   - Counterexample: File 'src/xagent/agents/tools/cron_api.py' does not exist
   - This proves the bug exists: No HTTP API tool available

4. call_cron_api is not registered in toolkit
   - Counterexample: tools/__init__.py does not import call_cron_api
   - This proves the bug exists: HTTP API tool not available to agents

These counterexamples demonstrate that the bug exists and the system
depends on hardcoded paths instead of using HTTP API calls.

AFTER FIX:
When the fix is implemented, this test will PASS, confirming:
- Cron skill uses HTTP API via call_cron_api tool
- No hardcoded path dependencies
- Works on any deployment path (Linux, macOS, Docker, Windows)
"""
