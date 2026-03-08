"""
Task 11.1 集成测试 - @gpt 命令端到端测试

测试 @gpt 命令从解析到执行的完整流程：
1. 命令解析：@gpt 命令正确解析为 (unified, api)
2. 路由：命令路由到 UnifiedAPIInterface
3. 配置：UnifiedAPIInterface 从 ProviderConfigManager 读取默认提供商配置
4. 执行：使用 Web 配置的 API Key 和模型参数

需求: 9.1, 9.2, 9.6, 9.7
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from src.xagent.utils.command_parser import CommandParser
from src.xagent.core.smart_router import SmartRouter
from src.xagent.core.unified_api import UnifiedAPIInterface
from src.xagent.core.provider_config_manager import ProviderConfigManager
from src.xagent.core.executor_registry import ExecutorRegistry, AIExecutor
from src.xagent.models import ParsedCommand, ProviderConfig, ExecutionResult


class TestGptCommandE2E:
    """@gpt 命令端到端测试"""
    
    def test_gpt_command_full_flow_with_openai_config(self):
        """测试 @gpt 命令完整流程（使用 OpenAI 配置）
        
        验证：
        1. CommandParser 正确解析 @gpt 命令
        2. SmartRouter 路由到 UnifiedAPIInterface
        3. UnifiedAPIInterface 从 ProviderConfigManager 读取默认配置
        4. 使用 Web 配置的 API Key 和模型参数创建执行器
        
        需求: 9.1, 9.2, 9.6, 9.7
        """
        # 1. 准备测试数据
        test_message = "@gpt 请帮我分析这段代码"
        test_api_key = "sk-test-key-12345"
        test_base_url = "https://api.openai.com/v1"
        test_model = "gpt-4"
        
        # 2. 创建 ProviderConfigManager 并添加测试配置
        config_manager = ProviderConfigManager(storage_path="data/test_provider_configs.json")
        test_config = ProviderConfig(
            name="TestOpenAI",
            type="openai_compatible",
            base_url=test_base_url,
            api_key=test_api_key,
            models=["gpt-4", "gpt-3.5-turbo"],
            default_model=test_model,
            is_default=True
        )
        success, msg = config_manager.add_config(test_config)
        assert success, f"添加测试配置失败: {msg}"
        
        # 3. 创建 ExecutorRegistry（mock OpenAI 执行器）
        registry = ExecutorRegistry()
        
        # Mock OpenAI 执行器
        mock_openai_executor = Mock(spec=AIExecutor)
        mock_openai_executor.execute.return_value = ExecutionResult(
            success=True,
            stdout="这是一段测试代码分析结果",
            stderr="",
            error_message=None,
            execution_time=1.5
        )
        mock_openai_executor.is_available.return_value = True
        mock_openai_executor.get_provider_name.return_value = "openai"
        
        # Mock get_openai_executor 方法
        with patch.object(registry, 'get_openai_executor', return_value=mock_openai_executor) as mock_get_executor:
            # 4. 创建 UnifiedAPIInterface
            unified_api = UnifiedAPIInterface(
                config_manager=config_manager,
                executor_registry=registry
            )
            
            # 5. 创建 SmartRouter
            router = SmartRouter(
                executor_registry=registry,
                unified_api_interface=unified_api
            )
            
            # 6. 创建 CommandParser
            parser = CommandParser()
            
            # 7. 解析命令
            parsed, params = parser.parse_command(test_message)
            
            # 验证解析结果
            assert parsed.provider == "unified", "应该解析为 unified 提供商"
            assert parsed.execution_layer == "api", "应该解析为 api 执行层"
            assert parsed.message == "请帮我分析这段代码", "消息内容应该正确"
            assert parsed.explicit is True, "应该识别为显式前缀"
            
            # 8. 路由到执行器
            executor = router.route(parsed)
            
            # 验证路由结果
            assert executor == unified_api, "应该路由到 UnifiedAPIInterface"
            
            # 9. 执行命令
            result = executor.execute(
                user_prompt=parsed.message,
                conversation_history=None
            )
            
            # 验证执行结果
            assert result.success is True, "执行应该成功"
            assert "测试代码分析结果" in result.stdout, "应该返回正确的结果"
            
            # 10. 验证使用了正确的配置参数
            mock_get_executor.assert_called_once_with(
                base_url=test_base_url,
                api_key=test_api_key,
                model=test_model
            )
            
            # 11. 验证执行器被调用
            mock_openai_executor.execute.assert_called_once()
            call_args = mock_openai_executor.execute.call_args
            assert call_args[1]['user_prompt'] == "请帮我分析这段代码"
    
    def test_gpt_command_with_empty_config(self):
        """测试 @gpt 命令在没有配置时返回错误
        
        验证：
        1. 当 ProviderConfigManager 没有默认配置时
        2. UnifiedAPIInterface 返回明确的错误提示
        3. 错误提示引导用户访问 Web 管理界面
        
        需求: 9.8
        """
        # 1. 创建空的 ProviderConfigManager
        config_manager = ProviderConfigManager(storage_path="data/test_empty_configs.json")
        
        # 2. 创建 ExecutorRegistry
        registry = ExecutorRegistry()
        
        # 3. 创建 UnifiedAPIInterface
        unified_api = UnifiedAPIInterface(
            config_manager=config_manager,
            executor_registry=registry
        )
        
        # 4. 创建 SmartRouter
        router = SmartRouter(
            executor_registry=registry,
            unified_api_interface=unified_api
        )
        
        # 5. 创建 CommandParser
        parser = CommandParser()
        
        # 6. 解析命令
        parsed, params = parser.parse_command("@gpt 你好")
        
        # 7. 路由到执行器
        executor = router.route(parsed)
        
        # 8. 执行命令
        result = executor.execute(
            user_prompt=parsed.message,
            conversation_history=None
        )
        
        # 9. 验证错误结果
        assert result.success is False, "应该返回失败"
        assert result.error_message is not None, "应该有错误消息"
        assert "请先在Web管理界面配置AI提供商" in result.error_message, \
            "错误消息应该引导用户配置提供商"
    
    def test_gpt_command_routing_not_using_legacy_executors(self):
        """测试 @gpt 命令不使用传统 API 执行器
        
        验证：
        1. @gpt 命令路由到 UnifiedAPIInterface
        2. 不会路由到传统的 ClaudeAPIExecutor、GeminiAPIExecutor
        3. 使用 Web 配置的提供商
        
        需求: 9.1, 9.2
        """
        # 1. 创建 ProviderConfigManager 并添加测试配置
        config_manager = ProviderConfigManager(storage_path="data/test_routing_configs.json")
        test_config = ProviderConfig(
            name="TestProvider",
            type="openai_compatible",
            base_url="https://api.test.com/v1",
            api_key="test-key",
            models=["test-model"],
            default_model="test-model",
            is_default=True
        )
        config_manager.add_config(test_config)
        
        # 2. 创建 ExecutorRegistry
        registry = ExecutorRegistry()
        
        # Mock OpenAI 执行器
        mock_executor = Mock(spec=AIExecutor)
        mock_executor.execute.return_value = ExecutionResult(
            success=True,
            stdout="测试结果",
            stderr="",
            error_message=None,
            execution_time=1.0
        )
        
        with patch.object(registry, 'get_openai_executor', return_value=mock_executor):
            # 3. 创建 UnifiedAPIInterface
            unified_api = UnifiedAPIInterface(
                config_manager=config_manager,
                executor_registry=registry
            )
            
            # 4. 创建 SmartRouter
            router = SmartRouter(
                executor_registry=registry,
                unified_api_interface=unified_api
            )
            
            # 5. 解析并路由 @gpt 命令
            parser = CommandParser()
            parsed, params = parser.parse_command("@gpt 测试")
            executor = router.route(parsed)
            
            # 6. 验证路由结果
            assert executor == unified_api, "应该路由到 UnifiedAPIInterface"
            assert executor is not None, "执行器不应该为 None"
            
            # 7. 验证不是传统执行器
            # UnifiedAPIInterface 的类名不应该包含 "ClaudeAPIExecutor" 或 "GeminiAPIExecutor"
            executor_class_name = executor.__class__.__name__
            assert "ClaudeAPIExecutor" not in executor_class_name, \
                "不应该使用 ClaudeAPIExecutor"
            assert "GeminiAPIExecutor" not in executor_class_name, \
                "不应该使用 GeminiAPIExecutor"
            assert executor_class_name == "UnifiedAPIInterface", \
                "应该使用 UnifiedAPIInterface"
    
    def test_gpt_command_with_conversation_history(self):
        """测试 @gpt 命令支持对话历史
        
        验证：
        1. @gpt 命令可以传递对话历史
        2. 对话历史正确传递给执行器
        
        需求: 9.1, 9.2
        """
        # 1. 准备测试数据
        conversation_history = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"}
        ]
        
        # 2. 创建配置
        config_manager = ProviderConfigManager(storage_path="data/test_history_configs.json")
        test_config = ProviderConfig(
            name="TestProvider",
            type="openai_compatible",
            base_url="https://api.test.com/v1",
            api_key="test-key",
            models=["test-model"],
            default_model="test-model",
            is_default=True
        )
        config_manager.add_config(test_config)
        
        # 3. 创建 ExecutorRegistry
        registry = ExecutorRegistry()
        
        # Mock OpenAI 执行器
        mock_executor = Mock(spec=AIExecutor)
        mock_executor.execute.return_value = ExecutionResult(
            success=True,
            stdout="基于历史对话的回复",
            stderr="",
            error_message=None,
            execution_time=1.0
        )
        
        with patch.object(registry, 'get_openai_executor', return_value=mock_executor):
            # 4. 创建 UnifiedAPIInterface
            unified_api = UnifiedAPIInterface(
                config_manager=config_manager,
                executor_registry=registry
            )
            
            # 5. 解析命令
            parser = CommandParser()
            parsed, params = parser.parse_command("@gpt 继续")
            
            # 6. 执行命令（带对话历史）
            result = unified_api.execute(
                user_prompt=parsed.message,
                conversation_history=conversation_history
            )
            
            # 7. 验证执行成功
            assert result.success is True
            
            # 8. 验证对话历史被传递
            mock_executor.execute.assert_called_once()
            call_args = mock_executor.execute.call_args
            assert call_args[1]['conversation_history'] == conversation_history
    
    def test_gpt_command_with_multiple_models_in_config(self):
        """测试 @gpt 命令使用配置中的默认模型
        
        验证：
        1. 配置中可以有多个模型
        2. 使用 default_model 指定的模型
        3. 不使用其他模型
        
        需求: 9.6, 9.7
        """
        # 1. 创建配置（包含多个模型）
        config_manager = ProviderConfigManager(storage_path="data/test_multi_model_configs.json")
        test_config = ProviderConfig(
            name="TestProvider",
            type="openai_compatible",
            base_url="https://api.test.com/v1",
            api_key="test-key",
            models=["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
            default_model="gpt-4-turbo",  # 指定默认模型
            is_default=True
        )
        config_manager.add_config(test_config)
        
        # 2. 创建 ExecutorRegistry
        registry = ExecutorRegistry()
        
        # Mock OpenAI 执行器
        mock_executor = Mock(spec=AIExecutor)
        mock_executor.execute.return_value = ExecutionResult(
            success=True,
            stdout="测试结果",
            stderr="",
            error_message=None,
            execution_time=1.0
        )
        
        with patch.object(registry, 'get_openai_executor', return_value=mock_executor) as mock_get_executor:
            # 3. 创建 UnifiedAPIInterface
            unified_api = UnifiedAPIInterface(
                config_manager=config_manager,
                executor_registry=registry
            )
            
            # 4. 解析并执行命令
            parser = CommandParser()
            parsed, params = parser.parse_command("@gpt 测试")
            result = unified_api.execute(
                user_prompt=parsed.message,
                conversation_history=None
            )
            
            # 5. 验证使用了默认模型
            mock_get_executor.assert_called_once()
            call_args = mock_get_executor.call_args
            assert call_args[1]['model'] == "gpt-4-turbo", \
                "应该使用配置中的默认模型 gpt-4-turbo"
    
    def test_gpt_command_case_insensitive(self):
        """测试 @gpt 命令大小写不敏感
        
        验证：
        1. @GPT、@Gpt、@gPt 等都能正确识别
        2. 都路由到 UnifiedAPIInterface
        
        需求: 9.1
        """
        # 1. 创建配置
        config_manager = ProviderConfigManager(storage_path="data/test_case_configs.json")
        test_config = ProviderConfig(
            name="TestProvider",
            type="openai_compatible",
            base_url="https://api.test.com/v1",
            api_key="test-key",
            models=["test-model"],
            default_model="test-model",
            is_default=True
        )
        config_manager.add_config(test_config)
        
        # 2. 创建 ExecutorRegistry
        registry = ExecutorRegistry()
        
        # Mock OpenAI 执行器
        mock_executor = Mock(spec=AIExecutor)
        mock_executor.execute.return_value = ExecutionResult(
            success=True,
            stdout="测试结果",
            stderr="",
            error_message=None,
            execution_time=1.0
        )
        
        with patch.object(registry, 'get_openai_executor', return_value=mock_executor):
            # 3. 创建 UnifiedAPIInterface 和 SmartRouter
            unified_api = UnifiedAPIInterface(
                config_manager=config_manager,
                executor_registry=registry
            )
            router = SmartRouter(
                executor_registry=registry,
                unified_api_interface=unified_api
            )
            
            # 4. 测试不同大小写的前缀
            parser = CommandParser()
            test_cases = ["@gpt 测试", "@GPT 测试", "@Gpt 测试", "@gPt 测试"]
            
            for test_case in test_cases:
                parsed, params = parser.parse_command(test_case)
                
                # 验证解析结果
                assert parsed.provider == "unified", \
                    f"命令 '{test_case}' 应该解析为 unified 提供商"
                assert parsed.execution_layer == "api", \
                    f"命令 '{test_case}' 应该解析为 api 执行层"
                assert parsed.explicit is True, \
                    f"命令 '{test_case}' 应该识别为显式前缀"
                
                # 验证路由结果
                executor = router.route(parsed)
                assert executor == unified_api, \
                    f"命令 '{test_case}' 应该路由到 UnifiedAPIInterface"


class TestGptCommandErrorHandling:
    """@gpt 命令错误处理测试"""
    
    def test_gpt_command_with_api_call_failure(self):
        """测试 @gpt 命令在 API 调用失败时的错误处理
        
        验证：
        1. API 调用失败时返回错误结果
        2. 错误消息包含提供商名称和错误信息
        
        需求: 9.8
        """
        # 1. 创建配置
        config_manager = ProviderConfigManager(storage_path="data/test_error_configs.json")
        test_config = ProviderConfig(
            name="TestProvider",
            type="openai_compatible",
            base_url="https://api.test.com/v1",
            api_key="test-key",
            models=["test-model"],
            default_model="test-model",
            is_default=True
        )
        config_manager.add_config(test_config)
        
        # 2. 创建 ExecutorRegistry
        registry = ExecutorRegistry()
        
        # Mock OpenAI 执行器（模拟失败）
        mock_executor = Mock(spec=AIExecutor)
        mock_executor.execute.side_effect = Exception("API 调用超时")
        
        with patch.object(registry, 'get_openai_executor', return_value=mock_executor):
            # 3. 创建 UnifiedAPIInterface
            unified_api = UnifiedAPIInterface(
                config_manager=config_manager,
                executor_registry=registry
            )
            
            # 4. 解析并执行命令
            parser = CommandParser()
            parsed, params = parser.parse_command("@gpt 测试")
            result = unified_api.execute(
                user_prompt=parsed.message,
                conversation_history=None
            )
            
            # 5. 验证错误处理
            assert result.success is False, "应该返回失败"
            assert result.error_message is not None, "应该有错误消息"
            assert "TestProvider" in result.error_message, \
                "错误消息应该包含提供商名称"
            assert "调用失败" in result.error_message, \
                "错误消息应该说明调用失败"
    
    def test_gpt_command_with_unsupported_config_type(self):
        """测试 @gpt 命令在配置类型不支持时的错误处理
        
        验证：
        1. 不支持的配置类型返回错误
        2. 错误消息说明不支持的类型
        
        需求: 9.8
        """
        # 1. 创建配置（使用不支持的类型）
        config_manager = ProviderConfigManager(storage_path="data/test_unsupported_configs.json")
        test_config = ProviderConfig(
            name="TestProvider",
            type="unsupported_type",  # 不支持的类型
            base_url="https://api.test.com/v1",
            api_key="test-key",
            models=["test-model"],
            default_model="test-model",
            is_default=True
        )
        config_manager.add_config(test_config)
        
        # 2. 创建 ExecutorRegistry
        registry = ExecutorRegistry()
        
        # 3. 创建 UnifiedAPIInterface
        unified_api = UnifiedAPIInterface(
            config_manager=config_manager,
            executor_registry=registry
        )
        
        # 4. 解析并执行命令
        parser = CommandParser()
        parsed, params = parser.parse_command("@gpt 测试")
        result = unified_api.execute(
            user_prompt=parsed.message,
            conversation_history=None
        )
        
        # 5. 验证错误处理
        assert result.success is False, "应该返回失败"
        assert result.error_message is not None, "应该有错误消息"
        assert "不支持的配置类型" in result.error_message or \
               "unsupported_type" in result.error_message, \
            "错误消息应该说明配置类型不支持"


class TestGptCommandIntegrationWithRouter:
    """@gpt 命令与路由器集成测试"""
    
    def test_gpt_command_explicit_routing(self):
        """测试 @gpt 命令的显式路由
        
        验证：
        1. @gpt 命令被识别为显式前缀
        2. 直接路由到 UnifiedAPIInterface，不经过智能判断
        
        需求: 9.1, 9.2
        """
        # 1. 创建配置
        config_manager = ProviderConfigManager(storage_path="data/test_explicit_configs.json")
        test_config = ProviderConfig(
            name="TestProvider",
            type="openai_compatible",
            base_url="https://api.test.com/v1",
            api_key="test-key",
            models=["test-model"],
            default_model="test-model",
            is_default=True
        )
        config_manager.add_config(test_config)
        
        # 2. 创建 ExecutorRegistry
        registry = ExecutorRegistry()
        
        # Mock OpenAI 执行器
        mock_executor = Mock(spec=AIExecutor)
        mock_executor.execute.return_value = ExecutionResult(
            success=True,
            stdout="测试结果",
            stderr="",
            error_message=None,
            execution_time=1.0
        )
        
        with patch.object(registry, 'get_openai_executor', return_value=mock_executor):
            # 3. 创建 UnifiedAPIInterface
            unified_api = UnifiedAPIInterface(
                config_manager=config_manager,
                executor_registry=registry
            )
            
            # 4. 创建 SmartRouter（禁用 AI 意图分类）
            router = SmartRouter(
                executor_registry=registry,
                unified_api_interface=unified_api,
                use_ai_intent_classification=False  # 禁用 AI 意图分类
            )
            
            # 5. 解析命令
            parser = CommandParser()
            parsed, params = parser.parse_command("@gpt 查看代码")  # 包含 CLI 关键词
            
            # 6. 验证解析结果
            assert parsed.explicit is True, "应该识别为显式前缀"
            
            # 7. 路由命令
            executor = router.route(parsed)
            
            # 8. 验证路由结果
            # 即使消息包含 CLI 关键词，也应该路由到 UnifiedAPIInterface（因为显式指定）
            assert executor == unified_api, \
                "显式指定 @gpt 应该路由到 UnifiedAPIInterface，不受关键词影响"
    
    def test_gpt_command_vs_cli_command_routing(self):
        """测试 @gpt 命令与 CLI 命令的路由区别
        
        验证：
        1. @gpt 命令路由到 UnifiedAPIInterface
        2. @claude-cli 命令路由到 CLI 执行器
        3. 两者使用不同的配置来源
        
        需求: 9.1, 9.3
        """
        # 1. 创建配置
        config_manager = ProviderConfigManager(storage_path="data/test_routing_diff_configs.json")
        test_config = ProviderConfig(
            name="TestProvider",
            type="openai_compatible",
            base_url="https://api.test.com/v1",
            api_key="test-key",
            models=["test-model"],
            default_model="test-model",
            is_default=True
        )
        config_manager.add_config(test_config)
        
        # 2. 创建 ExecutorRegistry
        registry = ExecutorRegistry()
        
        # Mock OpenAI 执行器（用于 @gpt）
        mock_api_executor = Mock(spec=AIExecutor)
        mock_api_executor.execute.return_value = ExecutionResult(
            success=True,
            stdout="API 结果",
            stderr="",
            error_message=None,
            execution_time=1.0
        )
        
        # Mock CLI 执行器（用于 @claude-cli）
        mock_cli_executor = Mock(spec=AIExecutor)
        mock_cli_executor.execute.return_value = ExecutionResult(
            success=True,
            stdout="CLI 结果",
            stderr="",
            error_message=None,
            execution_time=2.0
        )
        
        with patch.object(registry, 'get_openai_executor', return_value=mock_api_executor), \
             patch.object(registry, 'get_executor', side_effect=lambda p, l: mock_cli_executor if l == "cli" else mock_api_executor):
            
            # 3. 创建 UnifiedAPIInterface
            unified_api = UnifiedAPIInterface(
                config_manager=config_manager,
                executor_registry=registry
            )
            
            # 4. 创建 SmartRouter
            router = SmartRouter(
                executor_registry=registry,
                unified_api_interface=unified_api
            )
            
            # 5. 解析并路由 @gpt 命令
            parser = CommandParser()
            gpt_parsed, _ = parser.parse_command("@gpt 分析代码")
            gpt_executor = router.route(gpt_parsed)
            
            # 6. 解析并路由 @claude-cli 命令
            cli_parsed, _ = parser.parse_command("@claude-cli 分析代码")
            cli_executor = router.route(cli_parsed)
            
            # 7. 验证路由结果不同
            assert gpt_executor == unified_api, "@gpt 应该路由到 UnifiedAPIInterface"
            assert cli_executor == mock_cli_executor, "@claude-cli 应该路由到 CLI 执行器"
            assert gpt_executor != cli_executor, "@gpt 和 @claude-cli 应该路由到不同的执行器"


def test_cleanup():
    """清理测试文件"""
    import os
    test_files = [
        "data/test_provider_configs.json",
        "data/test_empty_configs.json",
        "data/test_routing_configs.json",
        "data/test_history_configs.json",
        "data/test_multi_model_configs.json",
        "data/test_case_configs.json",
        "data/test_error_configs.json",
        "data/test_unsupported_configs.json",
        "data/test_explicit_configs.json",
        "data/test_routing_diff_configs.json",
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass  # 忽略清理错误


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
