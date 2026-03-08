# 会话管理系统详细文档

## 概述

飞书AI机器人采用三层会话管理架构，充分利用CLI工具的原生会话能力，为用户提供连续、智能的对话体验。

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    用户 (User)                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              第1层：飞书机器人会话层                          │
│  - 管理用户交互历史                                           │
│  - 提供会话命令 (/new, /session, /history)                  │
│  - 会话轮换和过期管理                                         │
│  - 归档到 data/archived_sessions/                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
┌──────────────────────┐  ┌──────────────────────┐
│  第2层：Claude CLI   │  │  第3层：Gemini CLI   │
│      会话层          │  │      会话层          │
│                      │  │                      │
│ - 原生会话管理       │  │ - 原生会话管理       │
│ - --session 参数     │  │ - --resume 参数      │
│ - ~/.claude/sessions/│  │ - ~/.gemini/sessions/│
│ - user_id 映射       │  │ - user_id 映射       │
└──────────────────────┘  └──────────────────────┘
```

## 第1层：飞书机器人会话层

### 功能特性

1. **会话创建和管理**
   - 自动为每个用户创建独立会话
   - 会话ID使用UUID生成，全局唯一
   - 支持私聊和群聊两种会话类型

2. **消息历史记录**
   - 记录用户和AI的所有对话
   - 每条消息包含：角色（user/assistant）、内容、时间戳
   - 支持查询历史记录

3. **会话轮换机制**
   - 单个会话最大消息数：50条（可配置）
   - 会话超时时间：24小时（可配置）
   - 超过限制自动创建新会话并归档旧会话

4. **会话归档**
   - 旧会话自动归档到 `data/archived_sessions/`
   - 归档文件命名：`{user_id}_{session_id}_{timestamp}.json`
   - 归档内容包含完整的消息历史和元数据

### 会话命令

| 命令 | 别名 | 功能 |
|------|------|------|
| `/help` | `帮助`, `help` | 显示所有可用命令和使用说明 |
| `/session` | `会话信息` | 查看当前会话ID、消息数、创建时间、会话时长 |
| `/history` | `历史记录` | 查看对话历史（最近的消息） |
| `/new` | `新会话` | 创建新会话，清除所有三层会话 |

### 数据存储

**活跃会话**：`data/sessions.json`
```json
{
  "sessions": {
    "user_ou_123456": {
      "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "user_id": "ou_123456",
      "created_at": 1709280000,
      "last_active": 1709366400,
      "messages": [
        {
          "role": "user",
          "content": "你好",
          "timestamp": 1709280100
        },
        {
          "role": "assistant",
          "content": "你好！有什么可以帮助你的吗？",
          "timestamp": 1709280105
        }
      ]
    }
  }
}
```

**归档会话**：`data/archived_sessions/{user_id}_{session_id}_{timestamp}.json`
- 格式与活跃会话相同
- 用于历史记录查询和数据分析

## 第2层：Claude Code CLI 会话层

### 原生会话管理

Claude Code CLI 提供原生的会话管理功能，通过 `--session` 参数实现：

```bash
# 首次调用（不传 --session）
claude --add-dir /path/to/project -p "查看项目结构"
# Claude Code 自动创建新会话，返回 session_id

# 后续调用（传递 --session）
claude --add-dir /path/to/project --session abc123 -p "修改配置文件"
# Claude Code 加载会话上下文，理解之前的对话
```

### 会话映射机制

系统维护 user_id 到 Claude session_id 的映射：

**映射存储**：`data/executor_sessions.json`
```json
{
  "claude_cli_sessions": {
    "ou_123456": "claude_session_abc123",
    "ou_789012": "claude_session_def456"
  },
  "gemini_cli_sessions": {
    "ou_123456": "gemini_session_xyz789",
    "ou_789012": null
  }
}
```

### 工作流程

1. **首次调用**：
   - 检查 `session_map`，发现 user_id 不存在
   - 创建映射：`session_map[user_id] = None`
   - 执行命令时不传 `--session` 参数
   - Claude Code 自动创建新会话并存储到 `~/.claude/sessions/`

2. **后续调用**：
   - 检查 `session_map`，获取 session_id
   - 执行命令时传递 `--session <session_id>`
   - Claude Code 加载会话上下文，恢复对话历史

3. **会话清除**（`/new` 命令）：
   - 从 `session_map` 中删除 user_id 映射
   - 保存到 `data/executor_sessions.json`
   - 下次调用时重新创建新会话

### 会话存储位置

- **系统映射**：`data/executor_sessions.json`（由飞书机器人管理）
- **实际会话**：`~/.claude/sessions/`（由 Claude Code 管理）

## 第3层：Gemini CLI 会话层

### 原生会话管理

Gemini CLI 提供原生的会话管理功能，通过 `--resume` 参数实现：

```bash
# 首次调用（不传 --resume）
gemini --output-format json "查看项目结构"
# Gemini CLI 自动创建新会话，返回 session_id

# 后续调用（传递 --resume）
gemini --resume xyz789 --output-format json "修改配置文件"
# Gemini CLI 加载会话上下文，理解之前的对话
```

### 会话映射机制

与 Claude CLI 类似，系统维护 user_id 到 Gemini session_id 的映射。

### 工作流程

1. **首次调用**：
   - 检查 `session_map`，发现 user_id 不存在
   - 创建映射：`session_map[user_id] = None`
   - 执行命令时不传 `--resume` 参数
   - Gemini CLI 自动创建新会话并存储到 `~/.gemini/sessions/`

2. **后续调用**：
   - 检查 `session_map`，获取 session_id
   - 执行命令时传递 `--resume <session_id>`
   - Gemini CLI 加载会话上下文，恢复对话历史

3. **会话清除**（`/new` 命令）：
   - 从 `session_map` 中删除 user_id 映射
   - 保存到 `data/executor_sessions.json`
   - 下次调用时重新创建新会话

### 会话存储位置

- **系统映射**：`data/executor_sessions.json`（由飞书机器人管理）
- **实际会话**：`~/.gemini/sessions/`（由 Gemini CLI 管理）

## `/new` 命令完整流程

当用户发送 `/new` 命令时，系统执行以下操作：

### 1. 命令识别

```python
# xagent/xagent.py
def _handle_session_command(self, user_id, message, ...):
    if not self.session_manager.is_session_command(message):
        return False
    
    response = self.session_manager.handle_session_command(user_id, message)
    
    # 检测到 /new 命令，额外清除 CLI 会话
    message_lower = message.lower().strip()
    if message_lower in [cmd.lower() for cmd in self.session_manager.NEW_SESSION_COMMANDS]:
        for provider in ["claude", "gemini"]:
            cli_executor = self.executor_registry.get_executor(provider, "cli")
            if hasattr(cli_executor, 'clear_session'):
                cli_executor.clear_session(user_id)
```

### 2. 飞书机器人会话处理

```python
# xagent/core/session_manager.py
def create_new_session(self, user_id: str) -> Session:
    # 归档旧会话
    if user_id in self.sessions:
        old_session = self.sessions[user_id]
        self._archive_session(old_session)  # 保存到 data/archived_sessions/
    
    # 创建新会话
    session = Session(
        session_id=str(uuid.uuid4()),
        user_id=user_id,
        created_at=int(time.time()),
        last_active=int(time.time()),
        messages=[]
    )
    
    self.sessions[user_id] = session
    self.save_sessions()  # 保存到 data/sessions.json
    
    return session
```

### 3. Claude CLI 会话清除

```python
# xagent/executors/claude_cli_executor.py
def clear_session(self, user_id: str) -> None:
    if user_id in self.session_map:
        del self.session_map[user_id]
        self.save_session_mappings()  # 保存到 data/executor_sessions.json
```

### 4. Gemini CLI 会话清除

```python
# xagent/executors/gemini_cli_executor.py
def clear_session(self, user_id: str) -> None:
    if user_id in self.session_map:
        del self.session_map[user_id]
        self.save_session_mappings()  # 保存到 data/executor_sessions.json
```

### 5. 返回确认消息

```
✅ 已创建新会话 / New session created
```

### 流程图

```
用户发送 /new
    │
    ▼
命令识别 (xagent.py)
    │
    ▼
会话管理器处理 (session_manager.py)
    ├─► 归档旧会话 → data/archived_sessions/
    └─► 创建新会话 → data/sessions.json
    │
    ▼
清除 Claude CLI 会话映射
    └─► 删除 user_id 映射 → data/executor_sessions.json
    │
    ▼
清除 Gemini CLI 会话映射
    └─► 删除 user_id 映射 → data/executor_sessions.json
    │
    ▼
返回确认消息
```

## API层 vs CLI层会话管理

### API层（Claude API、Gemini API、OpenAI API）

**特点**：
- 无状态，每次调用需要传递完整对话历史
- 系统从飞书机器人会话中提取历史消息
- 格式化为API要求的消息格式
- 每次调用都包含完整上下文

**实现**：
```python
# 获取对话历史
conversation_history = self.session_manager.get_conversation_history(sender_id)

# 执行 API
result = executor.execute(
    message_with_language,
    conversation_history=conversation_history
)
```

### CLI层（Claude Code CLI、Gemini CLI）

**特点**：
- 有状态，CLI工具自己管理会话
- 系统只需传递 session_id
- CLI工具自动加载上下文
- 更好的代码操作连续性

**实现**：
```python
# 执行 CLI（传递 user_id，执行器内部处理会话）
result = executor.execute(
    message_with_language,
    additional_params={"user_id": sender_id}
)
```

## 配置选项

### 环境变量配置

```bash
# 会话存储路径
SESSION_STORAGE_PATH=./data/sessions.json

# 单个会话最大消息数
MAX_SESSION_MESSAGES=50

# 会话超时时间（秒）
SESSION_TIMEOUT=86400  # 24小时
```

### 代码配置

```python
# xagent/config.py
class BotConfig:
    def __init__(self):
        self.session_storage_path = os.getenv("SESSION_STORAGE_PATH", "./data/sessions.json")
        self.max_session_messages = int(os.getenv("MAX_SESSION_MESSAGES", "50"))
        self.session_timeout = int(os.getenv("SESSION_TIMEOUT", "86400"))
```

## 数据持久化

### 文件锁机制

系统使用 `filelock` 库避免并发写入冲突：

```python
from filelock import FileLock

def save_sessions(self):
    lock_path = f"{self.storage_path}.lock"
    with FileLock(lock_path, timeout=10):
        # 写入文件
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
```

### 自动备份

建议定期备份会话数据：

```bash
# 备份活跃会话
cp data/sessions.json data/sessions.json.backup

# 备份执行器会话映射
cp data/executor_sessions.json data/executor_sessions.json.backup

# 备份归档会话
tar -czf archived_sessions_backup.tar.gz data/archived_sessions/
```

## 故障排查

### 会话丢失

**问题**：用户报告会话历史丢失

**可能原因**：
1. 会话超时自动清理
2. 达到最大消息数自动轮换
3. 文件损坏

**解决方法**：
```bash
# 检查归档会话
ls -la data/archived_sessions/

# 恢复归档会话
# 找到对应的归档文件，复制内容到 sessions.json
```

### CLI会话不连续

**问题**：CLI层无法记住之前的对话

**可能原因**：
1. 会话映射丢失
2. CLI工具会话文件损坏
3. `/new` 命令清除了会话

**解决方法**：
```bash
# 检查会话映射
cat data/executor_sessions.json

# 检查 CLI 会话文件
ls -la ~/.claude/sessions/
ls -la ~/.gemini/sessions/

# 如果映射存在但会话不连续，可能是 CLI 工具问题
# 尝试清除并重新创建
rm -rf ~/.claude/sessions/*
rm -rf ~/.gemini/sessions/*
```

### 会话文件损坏

**问题**：机器人启动时报错，无法加载会话

**解决方法**：
```bash
# 备份损坏的文件
mv data/sessions.json data/sessions.json.corrupted

# 创建空会话文件
echo '{"sessions": {}}' > data/sessions.json

# 重启机器人
python lark_bot.py
```

## 性能优化

### 会话清理

定期清理过期会话以节省存储空间：

```python
# 手动清理
from xagent.core.session_manager import SessionManager
sm = SessionManager()
cleaned = sm.cleanup_expired_sessions()
print(f"Cleaned {cleaned} expired sessions")
```

### 归档压缩

压缩旧的归档会话：

```bash
# 压缩30天前的归档
find data/archived_sessions/ -name "*.json" -mtime +30 -exec gzip {} \;
```

### 限制消息数

减少单个会话的最大消息数以提高性能：

```bash
# 在 .env 中设置
MAX_SESSION_MESSAGES=20  # 默认50
```

## 最佳实践

1. **定期备份**：每天备份会话数据
2. **监控存储**：定期检查 `data/` 目录大小
3. **清理归档**：定期清理或压缩旧归档
4. **会话轮换**：根据使用情况调整最大消息数和超时时间
5. **日志监控**：关注会话相关的日志，及时发现问题

## 未来改进

- [ ] 支持会话导出和导入
- [ ] 支持会话搜索和分析
- [ ] 支持多设备会话同步
- [ ] 支持会话分享功能
- [ ] 优化大规模会话的性能
