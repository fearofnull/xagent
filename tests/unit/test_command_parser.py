"""
单元测试：命令解析器

验证命令解析器正确处理 CLI 前缀和默认行为
"""
import pytest
from src.xagent.utils.command_parser import CommandParser
from src.xagent.models import ParsedCommand


class TestCommandParserPrefixMapping:
    """测试命令前缀映射"""
    
    def test_agent_prefix_in_mapping(self):
        """验证 @agent 前缀存在于映射中"""
        parser = CommandParser()
        assert "@agent" in parser.PREFIX_MAPPING
        assert parser.PREFIX_MAPPING["@agent"] == ("agent", "api")
    
    def test_legacy_prefixes_not_in_mapping(self):
        """验证传统 API 前缀不在映射中"""
        parser = CommandParser()
        legacy_prefixes = ["@gpt", "@claude-api", "@gemini-api", "@openai"]
        
        for prefix in legacy_prefixes:
            assert prefix not in parser.PREFIX_MAPPING, \
                f"传统前缀 {prefix} 不应该存在于 PREFIX_MAPPING 中"
    
    def test_cli_prefixes_in_mapping(self):
        """验证所有 CLI 前缀存在于映射中"""
        parser = CommandParser()
        cli_prefixes = {
            "@claude": ("claude", "cli"),
            "@code": ("claude", "cli"),
            "@gemini": ("gemini", "cli"),
            "@qwen": ("qwen", "cli"),
        }
        
        for prefix, expected_value in cli_prefixes.items():
            assert prefix in parser.PREFIX_MAPPING, \
                f"CLI 前缀 {prefix} 应该存在于 PREFIX_MAPPING 中"
            assert parser.PREFIX_MAPPING[prefix] == expected_value, \
                f"CLI 前缀 {prefix} 的映射值应该是 {expected_value}"


class TestAgentCommandParsing:
    """测试 @agent 命令解析"""
    
    def test_agent_command_basic(self):
        """测试基本的 @agent 命令解析"""
        parser = CommandParser()
        parsed, params = parser.parse_command("@agent 你好")
        
        assert parsed.provider == "agent"
        assert parsed.execution_layer == "api"
        assert parsed.message == "你好"
        assert parsed.explicit is True
    
    def test_agent_command_with_long_message(self):
        """测试 @agent 命令带长消息"""
        parser = CommandParser()
        long_message = "请帮我分析这段代码的性能问题，并给出优化建议"
        parsed, params = parser.parse_command(f"@agent {long_message}")
        
        assert parsed.provider == "agent"
        assert parsed.execution_layer == "api"
        assert parsed.message == long_message
        assert parsed.explicit is True
    
    def test_agent_command_case_insensitive(self):
        """测试 @agent 命令大小写不敏感"""
        parser = CommandParser()
        test_cases = ["@AGENT 你好", "@Agent 你好", "@aGeNt 你好"]
        
        for test_case in test_cases:
            parsed, params = parser.parse_command(test_case)
            assert parsed.provider == "agent"
            assert parsed.execution_layer == "api"
            assert parsed.explicit is True
    
    def test_agent_command_with_extra_spaces(self):
        """测试 @agent 命令带额外空格"""
        parser = CommandParser()
        parsed, params = parser.parse_command("@agent    你好")
        
        assert parsed.provider == "agent"
        assert parsed.execution_layer == "api"
        assert parsed.message == "你好"
        assert parsed.explicit is True
    
    def test_agent_command_with_temp_params(self):
        """测试 @agent 命令带临时参数"""
        parser = CommandParser()
        parsed, params = parser.parse_command("@agent --model=gpt-4 你好")
        
        assert parsed.provider == "agent"
        assert parsed.execution_layer == "api"
        assert "你好" in parsed.message
        assert parsed.explicit is True
        assert params.get("model") == "gpt-4"


class TestLegacyPrefixRejection:
    """测试传统前缀不再被识别"""
    
    def test_gpt_prefix_not_recognized(self):
        """测试 @gpt 前缀不被识别"""
        parser = CommandParser()
        parsed, params = parser.parse_command("@gpt 你好")
        
        assert parsed.explicit is False
        assert parsed.provider == "agent"
        assert "@gpt" in parsed.message
    
    def test_claude_api_prefix_not_recognized(self):
        """测试 @claude-api 前缀不被识别"""
        parser = CommandParser()
        parsed, params = parser.parse_command("@claude-api 你好")
        
        assert parsed.explicit is False
        assert parsed.provider == "agent"
        assert "@claude-api" in parsed.message
    
    def test_gemini_api_prefix_not_recognized(self):
        """测试 @gemini-api 前缀不被识别"""
        parser = CommandParser()
        parsed, params = parser.parse_command("@gemini-api 你好")
        
        assert parsed.explicit is False
        assert parsed.provider == "agent"
        assert "@gemini-api" in parsed.message
    
    def test_openai_prefix_not_recognized(self):
        """测试 @openai 前缀不被识别"""
        parser = CommandParser()
        parsed, params = parser.parse_command("@openai 你好")
        
        assert parsed.explicit is False
        assert parsed.provider == "agent"
        assert "@openai" in parsed.message
    
    def test_all_legacy_prefixes_not_recognized(self):
        """测试所有传统前缀都不被识别"""
        parser = CommandParser()
        legacy_prefixes = ["@gpt", "@claude-api", "@gemini-api", "@openai"]
        
        for prefix in legacy_prefixes:
            parsed, params = parser.parse_command(f"{prefix} 测试消息")
            assert parsed.explicit is False, \
                f"传统前缀 {prefix} 不应该被识别为显式前缀"
            assert prefix in parsed.message, \
                f"未识别的前缀 {prefix} 应该保留在消息中"


class TestCliPrefixParsing:
    """测试 CLI 前缀解析"""
    
    def test_claude_cli_prefix(self):
        """测试 @claude 前缀解析"""
        parser = CommandParser()
        parsed, params = parser.parse_command("@claude 分析代码")
        
        assert parsed.provider == "claude"
        assert parsed.execution_layer == "cli"
        assert parsed.message == "分析代码"
        assert parsed.explicit is True
    
    def test_code_prefix(self):
        """测试 @code 前缀解析"""
        parser = CommandParser()
        parsed, params = parser.parse_command("@code 修改文件")
        
        assert parsed.provider == "claude"
        assert parsed.execution_layer == "cli"
        assert parsed.message == "修改文件"
        assert parsed.explicit is True
    
    def test_gemini_cli_prefix(self):
        """测试 @gemini 前缀解析"""
        parser = CommandParser()
        parsed, params = parser.parse_command("@gemini 查看项目结构")
        
        assert parsed.provider == "gemini"
        assert parsed.execution_layer == "cli"
        assert parsed.message == "查看项目结构"
        assert parsed.explicit is True
    
    def test_qwen_cli_prefix(self):
        """测试 @qwen 前缀解析"""
        parser = CommandParser()
        parsed, params = parser.parse_command("@qwen 执行命令")
        
        assert parsed.provider == "qwen"
        assert parsed.execution_layer == "cli"
        assert parsed.message == "执行命令"
        assert parsed.explicit is True
    
    def test_all_cli_prefixes(self):
        """测试所有 CLI 前缀都能正确解析"""
        parser = CommandParser()
        cli_test_cases = [
            ("@claude", "claude", "cli"),
            ("@code", "claude", "cli"),
            ("@gemini", "gemini", "cli"),
            ("@qwen", "qwen", "cli"),
        ]
        
        for prefix, expected_provider, expected_layer in cli_test_cases:
            parsed, params = parser.parse_command(f"{prefix} 测试消息")
            assert parsed.provider == expected_provider, \
                f"前缀 {prefix} 应该解析为提供商 {expected_provider}"
            assert parsed.execution_layer == expected_layer, \
                f"前缀 {prefix} 应该解析为执行层 {expected_layer}"
            assert parsed.explicit is True, \
                f"前缀 {prefix} 应该被识别为显式前缀"


class TestPrefixPriority:
    """测试前缀优先级"""
    
    def test_longer_prefix_takes_priority(self):
        """测试更长的前缀优先匹配"""
        parser = CommandParser()
        
        parsed, params = parser.parse_command("@claude 测试")
        assert parsed.provider == "claude"
        assert parsed.execution_layer == "cli"
        assert parsed.explicit is True


class TestMessageContentPreservation:
    """测试消息内容保留"""
    
    def test_message_content_preserved_after_prefix(self):
        """测试前缀后的消息内容被正确保留"""
        parser = CommandParser()
        test_cases = [
            ("@agent 你好世界", "你好世界"),
            ("@claude 分析这段代码", "分析这段代码"),
            ("@code 修改 main.py 文件", "修改 main.py 文件"),
        ]
        
        for command, expected_message in test_cases:
            parsed, params = parser.parse_command(command)
            assert parsed.message == expected_message, \
                f"命令 '{command}' 的消息内容应该是 '{expected_message}'"
    
    def test_special_characters_preserved(self):
        """测试特殊字符被保留"""
        parser = CommandParser()
        special_message = "测试!@#$%^&*()_+-=[]{}|;':\",./<>?"
        parsed, params = parser.parse_command(f"@agent {special_message}")
        
        assert parsed.message == special_message
    
    def test_unicode_characters_preserved(self):
        """测试 Unicode 字符被保留"""
        parser = CommandParser()
        unicode_message = "你好世界 🌍 こんにちは 안녕하세요"
        parsed, params = parser.parse_command(f"@agent {unicode_message}")
        
        assert parsed.message == unicode_message


class TestDefaultBehavior:
    """测试默认行为"""
    
    def test_no_prefix_uses_agent(self):
        """测试无前缀消息使用 Agent"""
        parser = CommandParser()
        parsed, params = parser.parse_command("你好")
        
        assert parsed.provider == "agent"
        assert parsed.execution_layer == "api"
        assert parsed.message == "你好"
        assert parsed.explicit is False
    
    def test_unrecognized_prefix_uses_agent(self):
        """测试未识别的前缀使用 Agent"""
        parser = CommandParser()
        parsed, params = parser.parse_command("@unknown 你好")
        
        assert parsed.provider == "agent"
        assert parsed.execution_layer == "api"
        assert "@unknown" in parsed.message
        assert parsed.explicit is False


class TestEdgeCases:
    """测试边缘情况"""
    
    def test_empty_message(self):
        """测试空消息"""
        parser = CommandParser()
        parsed, params = parser.parse_command("")
        
        assert parsed.provider == "agent"
        assert parsed.message == ""
        assert parsed.explicit is False
    
    def test_whitespace_only_message(self):
        """测试只有空格的消息"""
        parser = CommandParser()
        parsed, params = parser.parse_command("   ")
        
        assert parsed.provider == "agent"
        assert parsed.explicit is False
    
    def test_empty_message_after_prefix(self):
        """测试前缀后空消息"""
        parser = CommandParser()
        parsed, params = parser.parse_command("@agent")
        
        assert parsed.provider == "agent"
        assert parsed.execution_layer == "api"
        assert parsed.message == ""
        assert parsed.explicit is True
    
    def test_prefix_only_with_spaces(self):
        """测试只有前缀和空格"""
        parser = CommandParser()
        parsed, params = parser.parse_command("@agent   ")
        
        assert parsed.provider == "agent"
        assert parsed.execution_layer == "api"
        assert parsed.message == ""
        assert parsed.explicit is True
    
    def test_prefix_in_middle_of_message(self):
        """测试前缀在消息中间（会被识别，因为支持任意位置匹配）"""
        parser = CommandParser()
        parsed, params = parser.parse_command("你好 @agent 世界")
        
        assert parsed.explicit is True
        assert parsed.provider == "agent"
        assert "@agent" not in parsed.message
    
    def test_multiple_prefixes(self):
        """测试多个前缀（只识别第一个）"""
        parser = CommandParser()
        parsed, params = parser.parse_command("@agent @code 你好")
        
        assert parsed.provider == "agent"
        assert parsed.execution_layer == "api"
        assert parsed.explicit is True
        assert "@code" in parsed.message


class TestTempParams:
    """测试临时参数解析"""
    
    def test_single_temp_param(self):
        """测试单个临时参数"""
        parser = CommandParser()
        parsed, params = parser.parse_command("@agent --model=gpt-4 你好")
        
        assert params.get("model") == "gpt-4"
        assert parsed.message == "你好"
    
    def test_multiple_temp_params(self):
        """测试多个临时参数"""
        parser = CommandParser()
        parsed, params = parser.parse_command(
            "@agent --model=gpt-4 --temp=0.7 你好"
        )
        
        assert params.get("model") == "gpt-4"
        assert params.get("temp") == "0.7"
        assert parsed.message == "你好"
    
    def test_temp_param_with_spaces(self):
        """测试带空格的临时参数值"""
        parser = CommandParser()
        parsed, params = parser.parse_command(
            '@agent --dir="/path/with spaces" 你好'
        )
        
        assert params.get("dir") == '"/path/with'
        assert parsed.message == 'spaces" 你好'
    
    def test_temp_params_removed_from_message(self):
        """测试临时参数从消息中移除"""
        parser = CommandParser()
        parsed, params = parser.parse_command(
            "@agent --key=value 原始消息"
        )
        
        assert "--key=value" not in parsed.message
        assert parsed.message == "原始消息"


class TestCliKeywords:
    """测试 CLI 关键词检测"""
    
    def test_cli_keywords_detection(self):
        """测试 CLI 关键词检测"""
        parser = CommandParser()
        
        assert parser.detect_cli_keywords("查看代码") is True
        assert parser.detect_cli_keywords("view code") is True
        assert parser.detect_cli_keywords("分析代码") is True
        assert parser.detect_cli_keywords("修改文件") is True
        assert parser.detect_cli_keywords("执行命令") is True
    
    def test_non_cli_keywords(self):
        """测试非 CLI 关键词"""
        parser = CommandParser()
        
        assert parser.detect_cli_keywords("你好") is False
        assert parser.detect_cli_keywords("什么是 AI") is False
        assert parser.detect_cli_keywords("今天天气怎么样") is False
    
    def test_cli_keywords_case_insensitive(self):
        """测试 CLI 关键词大小写不敏感"""
        parser = CommandParser()
        
        assert parser.detect_cli_keywords("VIEW CODE") is True
        assert parser.detect_cli_keywords("Analyze Code") is True
        assert parser.detect_cli_keywords("RUN SCRIPT") is True
