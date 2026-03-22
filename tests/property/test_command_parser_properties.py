"""
属性测试：命令解析器一致性

使用 Hypothesis 进行属性测试，验证命令解析器在各种输入下的一致性行为。

**验证: 需求 4.1-4.8**
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from src.xagent.utils.command_parser import CommandParser
from src.xagent.models import ParsedCommand


# 定义有效的命令前缀
VALID_PREFIXES = ["@agent", "@claude", "@code", "@gemini", "@qwen"]

# 定义传统（已移除）的命令前缀
LEGACY_PREFIXES = ["@gpt", "@claude-api", "@gemini-api", "@openai"]

# 前缀到期望结果的映射
PREFIX_EXPECTATIONS = {
    "@agent": ("agent", "api"),
    "@claude": ("claude", "cli"),
    "@code": ("claude", "cli"),
    "@gemini": ("gemini", "cli"),
    "@qwen": ("qwen", "cli"),
}


class TestCommandPrefixProperties:
    """属性 4: 命令前缀更新
    
    **验证: 需求 4.1-4.8**
    测试所有有效前缀都能成功路由，传统前缀不再被识别
    """
    
    @settings(max_examples=100)
    @given(
        prefix=st.sampled_from(VALID_PREFIXES),
        message=st.text(min_size=1, max_size=100)
    )
    def test_valid_prefixes_always_parse_successfully(self, prefix, message):
        """属性：所有有效前缀都应该成功解析并路由
        
        **Validates: Requirements 4.4, 4.5, 4.6, 4.7, 4.8**
        """
        parser = CommandParser()
        command = f"{prefix} {message}"
        
        parsed, params = parser.parse_command(command)
        
        # 验证前缀被识别为显式前缀
        assert parsed.explicit is True, \
            f"有效前缀 {prefix} 应该被识别为显式前缀"
        
        # 验证路由到正确的提供商和执行层
        expected_provider, expected_layer = PREFIX_EXPECTATIONS[prefix]
        assert parsed.provider == expected_provider, \
            f"前缀 {prefix} 应该路由到提供商 {expected_provider}"
        assert parsed.execution_layer == expected_layer, \
            f"前缀 {prefix} 应该路由到执行层 {expected_layer}"
    
    @settings(max_examples=100)
    @given(
        prefix=st.sampled_from(LEGACY_PREFIXES),
        message=st.text(min_size=1, max_size=100)
    )
    def test_legacy_prefixes_not_recognized(self, prefix, message):
        """属性：传统前缀不应该被识别
        
        **Validates: Requirements 4.1, 4.2, 4.3**
        """
        parser = CommandParser()
        command = f"{prefix} {message}"
        
        parsed, params = parser.parse_command(command)
        
        # 验证传统前缀不被识别为显式前缀
        assert parsed.explicit is False, \
            f"传统前缀 {prefix} 不应该被识别为显式前缀"
        
        # 验证传统前缀保留在消息中（因为未被识别）
        assert prefix in parsed.message, \
            f"未识别的传统前缀 {prefix} 应该保留在消息中"
    
    @settings(max_examples=100)
    @given(prefix=st.sampled_from(VALID_PREFIXES))
    def test_valid_prefixes_case_insensitive(self, prefix):
        """属性：前缀解析应该是大小写不敏感的
        
        **Validates: Requirements 4.4-4.8**
        """
        parser = CommandParser()
        
        # 测试不同大小写变体
        case_variants = [
            prefix.upper(),
            prefix.lower(),
            prefix.capitalize(),
        ]
        
        for variant in case_variants:
            parsed, params = parser.parse_command(f"{variant} test")
            
            # 所有大小写变体都应该被识别
            assert parsed.explicit is True, \
                f"前缀 {prefix} 的大小写变体 {variant} 应该被识别"
            
            expected_provider, expected_layer = PREFIX_EXPECTATIONS[prefix]
            assert parsed.provider == expected_provider
            assert parsed.execution_layer == expected_layer


class TestMessageContentPreservation:
    """属性：命令解析保留消息内容
    
    **验证: 需求 4.1-4.8**
    测试命令解析正确保留消息内容，不丢失或修改用户输入
    """
    
    @settings(max_examples=100)
    @given(
        prefix=st.sampled_from(VALID_PREFIXES),
        message=st.text(min_size=1, max_size=200)
    )
    def test_message_content_preserved_after_prefix_removal(self, prefix, message):
        """属性：前缀移除后，消息内容应该完整保留
        
        **Validates: Requirements 4.4-4.8**
        """
        # 跳过只包含空白字符的消息
        assume(message.strip() != "")
        
        parser = CommandParser()
        command = f"{prefix} {message}"
        
        parsed, params = parser.parse_command(command)
        
        # 验证消息内容被保留（去除前后空格后应该相等）
        assert parsed.message.strip() == message.strip(), \
            f"消息内容应该被保留: 期望 '{message.strip()}', 实际 '{parsed.message.strip()}'"
    
    @settings(max_examples=100)
    @given(
        prefix=st.sampled_from(VALID_PREFIXES),
        message=st.text(
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd', 'Po', 'Zs'),
                whitelist_characters='!@#$%^&*()_+-=[]{}|;:\'",.<>?/\\`~'
            ),
            min_size=1,
            max_size=100
        )
    )
    def test_special_characters_preserved(self, prefix, message):
        """属性：特殊字符应该在解析后被保留
        
        **Validates: Requirements 4.4-4.8**
        """
        assume(message.strip() != "")
        
        parser = CommandParser()
        command = f"{prefix} {message}"
        
        parsed, params = parser.parse_command(command)
        
        # 验证特殊字符被保留
        assert parsed.message.strip() == message.strip(), \
            "特殊字符应该在解析后被保留"
    
    @settings(max_examples=100)
    @given(
        prefix=st.sampled_from(VALID_PREFIXES),
        # 生成包含中文、日文、韩文、emoji 的文本
        message=st.text(
            alphabet=st.characters(
                whitelist_categories=('Lo',),  # 其他字母（包括中日韩文字）
                min_codepoint=0x4E00,  # 中文起始
                max_codepoint=0x9FFF,  # 中文结束
            ),
            min_size=1,
            max_size=50
        )
    )
    def test_unicode_characters_preserved(self, prefix, message):
        """属性：Unicode 字符（中文、日文、韩文等）应该被保留
        
        **Validates: Requirements 4.4-4.8**
        """
        assume(message.strip() != "")
        
        parser = CommandParser()
        command = f"{prefix} {message}"
        
        parsed, params = parser.parse_command(command)
        
        # 验证 Unicode 字符被保留
        assert parsed.message.strip() == message.strip(), \
            "Unicode 字符应该在解析后被保留"


class TestWhitespaceHandling:
    """属性：空白字符处理
    
    **验证: 需求 4.1-4.8**
    测试命令解析正确处理各种空白字符情况
    """
    
    @settings(max_examples=100)
    @given(
        prefix=st.sampled_from(VALID_PREFIXES),
        spaces_before=st.integers(min_value=1, max_value=10),
        message=st.text(min_size=1, max_size=50)
    )
    def test_multiple_spaces_after_prefix_handled(self, prefix, spaces_before, message):
        """属性：前缀后的多个空格应该被正确处理
        
        **Validates: Requirements 4.4-4.8**
        """
        assume(message.strip() != "")
        
        parser = CommandParser()
        spaces = " " * spaces_before
        command = f"{prefix}{spaces}{message}"
        
        parsed, params = parser.parse_command(command)
        
        # 验证前缀被识别
        assert parsed.explicit is True
        
        # 验证消息内容被保留（空格被规范化）
        assert parsed.message.strip() == message.strip()
    
    @settings(max_examples=100)
    @given(
        prefix=st.sampled_from(VALID_PREFIXES),
        message=st.text(min_size=1, max_size=50)
    )
    def test_leading_trailing_spaces_in_message_preserved(self, prefix, message):
        """属性：消息中的前导和尾随空格应该被正确处理
        
        **Validates: Requirements 4.4-4.8**
        """
        parser = CommandParser()
        command = f"{prefix} {message}"
        
        parsed, params = parser.parse_command(command)
        
        # 验证前缀被识别
        assert parsed.explicit is True
        
        # 验证消息内容（CommandParser 会 strip 空格）
        assert parsed.message == message.strip()


class TestPrefixPriority:
    """属性：前缀优先级
    
    **验证: 需求 4.1-4.8**
    测试当消息包含多个可能的前缀时，解析器的行为
    注意：CommandParser 会在消息的任何位置查找前缀，按 PREFIX_MAPPING 中的顺序匹配
    """
    
    @settings(max_examples=50)
    @given(
        first_prefix=st.sampled_from(VALID_PREFIXES),
        second_prefix=st.sampled_from(VALID_PREFIXES),
        message=st.text(min_size=1, max_size=50)
    )
    def test_first_matching_prefix_recognized(self, first_prefix, second_prefix, message):
        """属性：当消息包含多个前缀时，识别第一个匹配的前缀
        
        **Validates: Requirements 4.4-4.8**
        CommandParser 按长度降序排序前缀，然后按字典序排序
        第一个匹配的前缀会被识别
        """
        assume(message.strip() != "")
        
        parser = CommandParser()
        command = f"{first_prefix} {second_prefix} {message}"
        
        parsed, params = parser.parse_command(command)
        
        # 确定哪个前缀会被识别
        # CommandParser 按长度降序排序，长度相同则按字典序
        # 然后找到第一个匹配的前缀
        sorted_prefixes = sorted(
            VALID_PREFIXES,
            key=lambda x: (-len(x), x)
        )
        
        expected_prefix = None
        for prefix in sorted_prefixes:
            if prefix in command.lower():
                expected_prefix = prefix
                break
        
        # 验证识别的是预期的前缀
        expected_provider, expected_layer = PREFIX_EXPECTATIONS[expected_prefix]
        assert parsed.provider == expected_provider, \
            f"Expected provider {expected_provider} for prefix {expected_prefix}, got {parsed.provider}"
        assert parsed.execution_layer == expected_layer
        assert parsed.explicit is True


class TestEdgeCases:
    """属性：边缘情况
    
    **验证: 需求 4.1-4.8**
    测试各种边缘情况下的解析行为
    """
    
    @settings(max_examples=100)
    @given(prefix=st.sampled_from(VALID_PREFIXES))
    def test_prefix_only_no_message(self, prefix):
        """属性：只有前缀没有消息时，应该正确解析
        
        **Validates: Requirements 4.4-4.8**
        """
        parser = CommandParser()
        
        parsed, params = parser.parse_command(prefix)
        
        # 验证前缀被识别
        assert parsed.explicit is True
        
        expected_provider, expected_layer = PREFIX_EXPECTATIONS[prefix]
        assert parsed.provider == expected_provider
        assert parsed.execution_layer == expected_layer
        
        # 消息应该为空
        assert parsed.message == ""
    
    @settings(max_examples=100)
    @given(
        prefix=st.sampled_from(VALID_PREFIXES),
        spaces=st.integers(min_value=1, max_value=20)
    )
    def test_prefix_with_only_spaces(self, prefix, spaces):
        """属性：前缀后只有空格时，应该正确解析
        
        **Validates: Requirements 4.4-4.8**
        """
        parser = CommandParser()
        command = f"{prefix}{' ' * spaces}"
        
        parsed, params = parser.parse_command(command)
        
        # 验证前缀被识别
        assert parsed.explicit is True
        
        expected_provider, expected_layer = PREFIX_EXPECTATIONS[prefix]
        assert parsed.provider == expected_provider
        assert parsed.execution_layer == expected_layer
        
        # 消息应该为空（空格被 strip）
        assert parsed.message == ""
    
    @settings(max_examples=100)
    @given(
        prefix=st.sampled_from(VALID_PREFIXES),
        position=st.integers(min_value=1, max_value=20),
        message=st.text(min_size=1, max_size=50)
    )
    def test_prefix_recognized_anywhere_in_message(self, prefix, position, message):
        """属性：前缀在消息的任何位置都应该被识别（只要它是完整的词）
        
        **Validates: Requirements 4.4-4.8**
        CommandParser 会在消息的任何位置查找前缀，只要前缀是完整的词
        （前后是空格或边界）
        """
        assume(message.strip() != "")
        
        parser = CommandParser()
        # 在消息前添加一些字符，使前缀不在开头
        command = f"{'x' * position} {prefix} {message}"
        
        parsed, params = parser.parse_command(command)
        
        # 前缀在消息中应该被识别为显式前缀（只要它是完整的词）
        assert parsed.explicit is True
        
        # 验证路由到正确的提供商
        expected_provider, expected_layer = PREFIX_EXPECTATIONS[prefix]
        assert parsed.provider == expected_provider
        assert parsed.execution_layer == expected_layer


class TestParsingConsistency:
    """属性：解析一致性
    
    **验证: 需求 4.1-4.8**
    测试相同输入的解析结果应该一致
    """
    
    @settings(max_examples=100)
    @given(
        prefix=st.sampled_from(VALID_PREFIXES),
        message=st.text(min_size=1, max_size=100)
    )
    def test_parsing_is_deterministic(self, prefix, message):
        """属性：相同输入的解析结果应该一致（确定性）
        
        **Validates: Requirements 4.4-4.8**
        """
        assume(message.strip() != "")
        
        parser = CommandParser()
        command = f"{prefix} {message}"
        
        # 解析两次
        parsed1, params1 = parser.parse_command(command)
        parsed2, params2 = parser.parse_command(command)
        
        # 验证两次解析结果完全一致
        assert parsed1.provider == parsed2.provider
        assert parsed1.execution_layer == parsed2.execution_layer
        assert parsed1.message == parsed2.message
        assert parsed1.explicit == parsed2.explicit
        assert params1 == params2
    
    @settings(max_examples=100)
    @given(
        prefix=st.sampled_from(VALID_PREFIXES),
        message=st.text(min_size=1, max_size=100)
    )
    def test_multiple_parser_instances_consistent(self, prefix, message):
        """属性：不同解析器实例的解析结果应该一致
        
        **Validates: Requirements 4.4-4.8**
        """
        assume(message.strip() != "")
        
        command = f"{prefix} {message}"
        
        # 创建两个解析器实例
        parser1 = CommandParser()
        parser2 = CommandParser()
        
        parsed1, params1 = parser1.parse_command(command)
        parsed2, params2 = parser2.parse_command(command)
        
        # 验证两个实例的解析结果一致
        assert parsed1.provider == parsed2.provider
        assert parsed1.execution_layer == parsed2.execution_layer
        assert parsed1.message == parsed2.message
        assert parsed1.explicit == parsed2.explicit


class TestPrefixMappingCompleteness:
    """属性：前缀映射完整性
    
    **验证: 需求 4.1-4.8**
    测试 PREFIX_MAPPING 包含所有有效前缀，不包含传统前缀
    """
    
    def test_all_valid_prefixes_in_mapping(self):
        """属性：所有有效前缀都应该在 PREFIX_MAPPING 中
        
        **Validates: Requirements 4.4, 4.5, 4.6, 4.7, 4.8**
        """
        parser = CommandParser()
        
        for prefix in VALID_PREFIXES:
            assert prefix in parser.PREFIX_MAPPING, \
                f"有效前缀 {prefix} 应该在 PREFIX_MAPPING 中"
            
            # 验证映射值正确
            expected_provider, expected_layer = PREFIX_EXPECTATIONS[prefix]
            actual_provider, actual_layer = parser.PREFIX_MAPPING[prefix]
            
            assert actual_provider == expected_provider, \
                f"前缀 {prefix} 的提供商映射应该是 {expected_provider}"
            assert actual_layer == expected_layer, \
                f"前缀 {prefix} 的执行层映射应该是 {expected_layer}"
    
    def test_no_legacy_prefixes_in_mapping(self):
        """属性：传统前缀不应该在 PREFIX_MAPPING 中
        
        **Validates: Requirements 4.1, 4.2, 4.3**
        """
        parser = CommandParser()
        
        for prefix in LEGACY_PREFIXES:
            assert prefix not in parser.PREFIX_MAPPING, \
                f"传统前缀 {prefix} 不应该在 PREFIX_MAPPING 中"
    
    def test_mapping_contains_only_expected_prefixes(self):
        """属性：PREFIX_MAPPING 应该只包含预期的前缀
        
        **Validates: Requirements 4.1-4.8**
        """
        parser = CommandParser()
        
        # 获取所有映射中的前缀
        actual_prefixes = set(parser.PREFIX_MAPPING.keys())
        expected_prefixes = set(VALID_PREFIXES)
        
        # 验证没有额外的前缀
        extra_prefixes = actual_prefixes - expected_prefixes
        assert len(extra_prefixes) == 0, \
            f"PREFIX_MAPPING 包含未预期的前缀: {extra_prefixes}"
        
        # 验证没有缺失的前缀
        missing_prefixes = expected_prefixes - actual_prefixes
        assert len(missing_prefixes) == 0, \
            f"PREFIX_MAPPING 缺少预期的前缀: {missing_prefixes}"
