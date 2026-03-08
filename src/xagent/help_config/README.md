# 配置模块

本模块管理系统配置和帮助信息。

## 帮助信息配置

### 文件位置

- 配置文件: `feishu_bot/config/help_messages.json`
- 加载器: `feishu_bot/config/help_loader.py`

### 为什么要配置化？

将帮助信息配置化有以下优势：

1. **集中管理**: 所有帮助内容在一个文件中，易于查找和修改
2. **避免遗漏**: 修改系统功能时，只需更新配置文件，不会忘记更新帮助信息
3. **结构化**: JSON 格式清晰，易于维护
4. **可扩展**: 未来可以支持多语言、动态加载等功能
5. **无需重启**: 可以实现热重载（未来功能）

### 配置文件结构

```json
{
  "version": "1.0.0",
  "last_updated": "2024-01-01",
  "help_message": {
    "title": "帮助标题",
    "sections": [
      {
        "title": "部分标题",
        "commands": [
          {
            "command": "命令",
            "description": "描述"
          }
        ]
      }
    ]
  }
}
```

### 如何更新帮助信息

#### 1. 添加新命令

在相应的 section 中添加新的 command 对象：

```json
{
  "command": "/newcommand <参数>",
  "description": "新命令的描述"
}
```

#### 2. 删除过时命令

直接从配置文件中删除对应的 command 对象。

例如，删除 `/layer` 命令：

```json
// 删除这个对象
{
  "command": "/layer <api|cli>",
  "description": "切换执行层（api=Web配置提供商, cli=代码能力）"
}
```

#### 3. 修改命令描述

直接修改 description 字段：

```json
{
  "command": "/cliprovider <claude|gemini|qwen>",
  "description": "设置默认CLI提供商（更新后的描述）"
}
```

#### 4. 添加新的部分

在 sections 数组中添加新的 section 对象：

```json
{
  "title": "🆕 **新功能 / New Features**",
  "commands": [
    {
      "command": "/feature",
      "description": "新功能描述"
    }
  ]
}
```

### 使用方法

#### 在代码中使用

```python
from feishu_bot.config.help_loader import get_help_message

# 获取帮助信息
help_text = get_help_message()
print(help_text)
```

#### 重新加载配置

```python
from feishu_bot.config.help_loader import get_help_loader

# 获取加载器实例
loader = get_help_loader()

# 重新加载配置
loader.reload()
```

### 最佳实践

1. **修改功能时同步更新**: 每次添加、删除或修改命令时，立即更新 `help_messages.json`
2. **保持版本号**: 更新配置后，更新 `version` 和 `last_updated` 字段
3. **测试帮助信息**: 修改后在飞书中发送 `/help` 命令测试显示效果
4. **保持格式一致**: 遵循现有的格式和缩进风格
5. **添加注释**: 在 Git 提交信息中说明更新了哪些帮助内容

### 示例：移除 /layer 命令

**修改前**:
```json
{
  "command": "/layer <api|cli>",
  "description": "切换执行层（api=Web配置提供商, cli=代码能力）"
}
```

**修改后**:
直接删除这个对象，保存文件即可。

### 故障排除

#### 配置文件加载失败

如果配置文件损坏或不存在，系统会使用后备配置（fallback config），显示最基本的帮助信息。

检查日志：
```
ERROR - Failed to load help messages: ...
```

解决方法：
1. 检查 JSON 格式是否正确（使用 JSON 验证工具）
2. 检查文件路径是否正确
3. 检查文件权限

#### 帮助信息显示不正确

1. 检查 JSON 格式是否正确
2. 检查字段名是否拼写正确（command, description, title 等）
3. 重启服务以重新加载配置

### 未来扩展

- [ ] 支持多语言（根据用户语言设置显示不同语言的帮助）
- [ ] 支持热重载（修改配置文件后自动重新加载）
- [ ] 支持通过 Web 管理界面编辑帮助信息
- [ ] 支持 Markdown 格式的帮助内容
- [ ] 支持按角色/权限显示不同的帮助内容
