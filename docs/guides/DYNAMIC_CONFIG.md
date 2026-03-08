# 动态配置系统 / Dynamic Configuration System

## 概述 / Overview

飞书 AI 机器人支持动态配置系统，允许用户在对话窗口中直接配置机器人行为，无需修改环境变量或重启服务。

XAgent supports a dynamic configuration system that allows users to configure bot behavior directly in the chat window without modifying environment variables or restarting the service.

## 配置优先级 / Configuration Priority

配置系统采用四层优先级结构（从高到低）：

The configuration system uses a four-tier priority structure (from highest to lowest):

1. **临时参数 / Temporary Parameters** - 单次使用，通过 `--key=value` 格式传递
2. **会话配置 / Session Config** - 持久化配置，基于会话 ID
3. **全局配置 / Global Config** - 环境变量配置
4. **默认值 / Defaults** - 系统默认值

## 会话类型 / Session Types

### 私聊 / Private Chat
- 配置基于 `user_id`（用户级别）
- 每个用户有独立的配置
- Configuration is based on `user_id` (user-level)
- Each user has independent configuration

### 群聊 / Group Chat
- 配置基于 `chat_id`（群组级别）
- 群组内所有成员共享配置
- 任何成员都可以修改配置
- 系统会记录谁修改了配置
- Configuration is based on `chat_id` (group-level)
- All members in the group share the configuration
- Any member can modify the configuration
- The system tracks who modified the configuration

## 可配置项 / Configurable Items

| 配置项 / Config Item | 命令 / Command | 说明 / Description |
|---------------------|----------------|-------------------|
| 项目目录 / Project Directory | `/setdir <path>` | CLI 工具的目标项目目录 / Target project directory for CLI tools |
| 回复语言 / Response Language | `/lang <code>` | AI 回复的语言（如 zh-CN, en-US）/ Language for AI responses |
| 默认提供商 / Default Provider | `/provider <name>` | 默认 AI 提供商（claude, gemini, openai）/ Default AI provider |
| 默认执行层 / Default Layer | `/layer <type>` | 默认执行层（api, cli）/ Default execution layer |
| CLI 提供商 / CLI Provider | `/cliprovider <name>` | CLI 层专用提供商 / CLI-specific provider |

## 配置命令 / Configuration Commands

### 设置项目目录 / Set Project Directory

```
/setdir /path/to/project
```

设置 CLI 工具（如 Claude Code CLI、Gemini CLI）的目标项目目录。

Sets the target project directory for CLI tools (e.g., Claude Code CLI, Gemini CLI).

**示例 / Example:**
```
/setdir /home/user/my-project
```

### 设置回复语言 / Set Response Language

```
/lang <language-code>
```

设置 AI 回复的语言。支持的语言代码：

Sets the language for AI responses. Supported language codes:

- `zh-CN` - 中文（简体）/ Chinese (Simplified)
- `zh-TW` - 中文（繁體）/ Chinese (Traditional)
- `en-US` - English (US)
- `en-GB` - English (UK)
- `ja-JP` - 日本語 / Japanese
- `ko-KR` - 한국어 / Korean
- `fr-FR` - Français / French
- `de-DE` - Deutsch / German
- `es-ES` - Español / Spanish
- `ru-RU` - Русский / Russian
- `pt-BR` - Português (Brasil) / Portuguese (Brazil)
- `it-IT` - Italiano / Italian
- `ar-SA` - العربية / Arabic
- `hi-IN` - हिन्दी / Hindi

**示例 / Example:**
```
/lang zh-CN
/lang en-US
```

### 设置默认提供商 / Set Default Provider

```
/provider <provider-name>
```

设置默认的 AI 提供商。有效值：`claude`, `gemini`, `openai`

Sets the default AI provider. Valid values: `claude`, `gemini`, `openai`

**示例 / Example:**
```
/provider claude
/provider gemini
```

### 设置默认执行层 / Set Default Layer

```
/layer <layer-type>
```

设置默认的执行层。有效值：`api`, `cli`

Sets the default execution layer. Valid values: `api`, `cli`

**示例 / Example:**
```
/layer api
/layer cli
```

### 设置 CLI 提供商 / Set CLI Provider

```
/cliprovider <provider-name>
```

设置 CLI 层专用的提供商。有效值：`claude`, `gemini`

Sets the CLI-specific provider. Valid values: `claude`, `gemini`

**示例 / Example:**
```
/cliprovider claude
/cliprovider gemini
```

### 查看当前配置 / View Current Configuration

```
/config
配置
```

查看当前生效的配置和配置元数据。

View the current effective configuration and metadata.

**示例输出 / Example Output:**
```
⚙️ 当前配置 / Current Config:
- 项目目录 / Project Dir: /home/user/my-project
- 回复语言 / Language: zh-CN
- 默认提供商 / Provider: claude
- 默认执行层 / Layer: api
- CLI提供商 / CLI Provider: (使用默认 / Use default)

📊 配置元数据 / Metadata:
- 创建者 / Created by: ou_xxx
- 创建时间 / Created at: 2026-02-28T10:30:00
- 更新者 / Updated by: ou_yyy
- 更新时间 / Updated at: 2026-02-28T11:45:00
- 更新次数 / Update count: 5
```

### 重置配置 / Reset Configuration

```
/reset
重置配置
```

重置当前会话的所有配置，恢复到全局配置或默认值。

Reset all configuration for the current session, reverting to global config or defaults.

## 临时参数 / Temporary Parameters

临时参数允许在单次请求中覆盖配置，不会持久化保存。

Temporary parameters allow overriding configuration for a single request without persisting the changes.

### 语法 / Syntax

```
--key=value
```

### 支持的临时参数 / Supported Temporary Parameters

| 参数 / Parameter | 说明 / Description |
|-----------------|-------------------|
| `--dir=<path>` | 临时指定项目目录 / Temporarily specify project directory |
| `--lang=<code>` | 临时指定回复语言 / Temporarily specify response language |
| `--provider=<name>` | 临时指定提供商 / Temporarily specify provider |
| `--layer=<type>` | 临时指定执行层 / Temporarily specify layer |
| `--cliprovider=<name>` | 临时指定 CLI 提供商 / Temporarily specify CLI provider |

### 示例 / Examples

**临时使用不同的项目目录 / Temporarily use a different project directory:**
```
--dir=/tmp/test-project 查看项目结构
```

**临时使用英文回复 / Temporarily use English responses:**
```
--lang=en-US What is artificial intelligence?
```

**临时使用 Gemini API / Temporarily use Gemini API:**
```
--provider=gemini --layer=api 解释量子计算
```

**组合多个临时参数 / Combine multiple temporary parameters:**
```
--dir=/home/user/project --lang=zh-CN --provider=claude 分析代码
```

## 使用场景 / Use Cases

### 场景 1：私聊中设置个人偏好 / Scenario 1: Set Personal Preferences in Private Chat

```
用户: /lang zh-CN
机器人: ✅ 配置已更新 / Config updated: response_language = zh-CN

用户: /setdir /home/user/my-project
机器人: ✅ 配置已更新 / Config updated: target_project_dir = /home/user/my-project

用户: 查看项目结构
机器人: [使用 zh-CN 语言，在 /home/user/my-project 目录下执行]
```

### 场景 2：群聊中共享配置 / Scenario 2: Share Configuration in Group Chat

```
用户A: /setdir /team/shared-project
机器人: ✅ 配置已更新 / Config updated: target_project_dir = /team/shared-project

用户B: /config
机器人: ⚙️ 当前配置 / Current Config:
- 项目目录 / Project Dir: /team/shared-project
...
📊 配置元数据 / Metadata:
- 创建者 / Created by: ou_userA
- 更新者 / Updated by: ou_userA
...

用户B: 查看代码
机器人: [使用群组配置的 /team/shared-project 目录]
```

### 场景 3：临时参数覆盖 / Scenario 3: Temporary Parameter Override

```
用户: /config
机器人: ⚙️ 当前配置 / Current Config:
- 项目目录 / Project Dir: /home/user/project-a
...

用户: --dir=/home/user/project-b 查看 README
机器人: [临时使用 /home/user/project-b 目录，不影响持久化配置]

用户: 查看代码
机器人: [恢复使用 /home/user/project-a 目录]
```

## 配置持久化 / Configuration Persistence

配置数据保存在 `./data/session_configs.json` 文件中，包含：

Configuration data is saved in `./data/session_configs.json`, including:

- 会话 ID 和类型 / Session ID and type
- 所有配置项的值 / Values of all configuration items
- 创建者和更新者信息 / Creator and updater information
- 创建和更新时间戳 / Creation and update timestamps
- 更新次数 / Update count

## 配置验证 / Configuration Validation

系统会自动验证配置值的有效性：

The system automatically validates configuration values:

- **项目目录 / Project Directory**: 检查目录是否存在 / Checks if directory exists
- **提供商 / Provider**: 必须是 `claude`, `gemini`, 或 `openai` / Must be `claude`, `gemini`, or `openai`
- **执行层 / Layer**: 必须是 `api` 或 `cli` / Must be `api` or `cli`
- **语言代码 / Language Code**: 接受任何字符串，但建议使用标准代码 / Accepts any string, but standard codes are recommended

## 注意事项 / Notes

1. **群聊配置共享 / Group Config Sharing**: 群聊中的配置对所有成员可见和可修改，请谨慎设置敏感信息。
   - Group configuration is visible and modifiable by all members, be cautious with sensitive information.

2. **配置透明度 / Configuration Transparency**: 系统会记录谁创建和修改了配置，提供配置变更的可追溯性。
   - The system tracks who created and modified the configuration, providing traceability.

3. **临时参数不持久化 / Temporary Parameters Not Persisted**: 临时参数仅对当前请求有效，不会保存到配置文件。
   - Temporary parameters are only valid for the current request and are not saved to the configuration file.

4. **配置优先级 / Configuration Priority**: 临时参数 > 会话配置 > 全局配置 > 默认值
   - Temporary parameters > Session config > Global config > Defaults

5. **CLI 目录配置 / CLI Directory Config**: 设置项目目录后，CLI 工具会在该目录下执行操作。
   - After setting the project directory, CLI tools will execute operations in that directory.

## 故障排除 / Troubleshooting

### 配置未生效 / Configuration Not Taking Effect

1. 检查配置优先级，确认是否被更高优先级的配置覆盖
   - Check configuration priority to ensure it's not overridden by higher priority config

2. 使用 `/config` 命令查看当前生效的配置
   - Use `/config` command to view the current effective configuration

3. 检查配置值是否有效（如目录是否存在）
   - Check if the configuration value is valid (e.g., directory exists)

### 目录不存在错误 / Directory Does Not Exist Error

```
⚠️ 目录不存在 / Directory does not exist: /invalid/path
```

**解决方案 / Solution:**
- 确认目录路径正确 / Confirm the directory path is correct
- 确保目录已创建 / Ensure the directory is created
- 使用绝对路径而非相对路径 / Use absolute path instead of relative path

### 无效的提供商或执行层 / Invalid Provider or Layer

```
❌ 无效的提供商 / Invalid provider: invalid-name
有效值 / Valid values: claude, gemini, openai
```

**解决方案 / Solution:**
- 使用有效的配置值 / Use valid configuration values
- 参考本文档中的有效值列表 / Refer to the valid values list in this document

## 测试验证 / Test Verification

动态配置系统已通过完整的测试验证，包括：

The dynamic configuration system has been fully tested and verified, including:

### 单元测试 / Unit Tests

所有 16 个单元测试全部通过（100% 通过率）：

All 16 unit tests passed (100% pass rate):

1. ✅ 获取默认配置 / Get default configuration
2. ✅ 设置配置 / Set configuration
3. ✅ 设置语言配置 / Set language configuration
4. ✅ 设置提供商配置 / Set provider configuration
5. ✅ 无效提供商验证 / Invalid provider validation
6. ✅ 无效执行层验证 / Invalid layer validation
7. ✅ 临时参数覆盖 / Temporary parameter override
8. ✅ 配置优先级 / Configuration priority
9. ✅ 重置配置 / Reset configuration
10. ✅ 群组配置 / Group configuration
11. ✅ 配置持久化 / Configuration persistence
12. ✅ 解析临时参数 / Parse temporary parameters
13. ✅ 配置命令识别 / Configuration command recognition
14. ✅ 处理 setdir 命令 / Handle setdir command
15. ✅ 查看配置命令 / View configuration command
16. ✅ 更新次数统计 / Update count tracking

### 手动测试 / Manual Tests

所有 15 项手动测试全部通过：

All 15 manual tests passed:

1. ✅ 创建全局配置 / Create global configuration
2. ✅ 创建配置管理器 / Create configuration manager
3. ✅ 获取默认配置 / Get default configuration
4. ✅ 设置项目目录 / Set project directory
5. ✅ 设置语言 / Set language
6. ✅ 设置提供商 / Set provider
7. ✅ 查看配置信息 / View configuration info
8. ✅ 临时参数覆盖 / Temporary parameter override
9. ✅ 解析临时参数 / Parse temporary parameters
10. ✅ 配置命令识别 / Configuration command recognition
11. ✅ 处理配置命令 / Handle configuration command
12. ✅ 群聊配置 / Group chat configuration
13. ✅ 重置配置 / Reset configuration
14. ✅ 无效配置验证 / Invalid configuration validation
15. ✅ 清理测试文件 / Clean up test files

### 测试覆盖 / Test Coverage

- **配置优先级系统**: 临时参数 > 会话配置 > 全局配置 > 默认值
- **会话类型支持**: 私聊（user_id）和群聊（chat_id）
- **配置持久化**: JSON 文件存储和加载
- **配置验证**: 提供商、执行层、目录存在性
- **配置元数据**: 创建者、更新者、更新次数追踪
- **临时参数**: 解析和应用，不影响持久化配置
- **配置命令**: 识别和处理所有配置命令
- **错误处理**: 友好的错误提示和验证

测试代码位于 `tests/test_config_manager.py`。

Test code is located in `tests/test_config_manager.py`.

## 相关文档 / Related Documentation

- [README.md](../README.md) - 项目概述和快速开始 / Project overview and quick start
- [会话管理](../README.md#会话管理) - 会话命令和历史管理 / Session commands and history management
- [智能路由](../README.md#智能路由) - AI 提供商路由机制 / AI provider routing mechanism
- [实现总结](../IMPLEMENTATION_SUMMARY.md) - 动态配置系统实现详情 / Dynamic configuration system implementation details
