# 项目目录结构

本文档描述了飞书AI机器人项目的目录结构。

## 根目录结构

```
lark-bot/
├── xagent/          # 核心代码包
├── tests/               # 测试代码
├── scripts/             # 脚本工具
├── docs/                # 项目文档
├── data/                # 运行时数据（会话数据等）
├── .env.example         # 环境变量模板
├── .gitignore           # Git 忽略文件
├── docker-compose.yml   # Docker Compose 配置
├── Dockerfile           # Docker 镜像构建文件
├── lark_bot.py          # 主程序入口
├── requirements.txt     # Python 依赖
└── README.md            # 项目说明
```

## 详细目录说明

### xagent/ - 核心代码包

```
xagent/
├── core/                # 核心功能模块
│   ├── event_handler.py         # 事件处理器
│   ├── executor_registry.py     # 执行器注册表
│   ├── message_handler.py       # 消息处理器
│   ├── message_sender.py        # 消息发送器
│   ├── session_manager.py       # 会话管理器
│   ├── smart_router.py          # 智能路由器
│   └── websocket_client.py      # WebSocket 客户端
├── executors/           # AI 执行器
│   ├── ai_api_executor.py       # API 执行器基类
│   ├── ai_cli_executor.py       # CLI 执行器基类
│   ├── claude_api_executor.py   # Claude API 执行器
│   ├── claude_cli_executor.py   # Claude CLI 执行器
│   ├── gemini_api_executor.py   # Gemini API 执行器
│   ├── gemini_cli_executor.py   # Gemini CLI 执行器
│   └── openai_api_executor.py   # OpenAI API 执行器
├── utils/               # 工具类
│   ├── cache.py                 # 消息去重缓存
│   ├── command_parser.py        # 命令解析器
│   ├── intent_classifier.py     # 意图分类器
│   ├── response_formatter.py    # 响应格式化器
│   └── ssl_config.py            # SSL 配置
├── __init__.py          # 包初始化
├── config.py            # 配置管理
├── xagent.py        # 主应用类
└── models.py            # 数据模型
```

### tests/ - 测试代码

```
tests/
├── test_*.py            # 单元测试
├── test_*_properties.py # 属性测试（Property-Based Testing）
└── test_integration.py  # 集成测试
```

测试类型：
- **单元测试**：测试单个模块的功能
- **属性测试**：使用 Hypothesis 进行基于属性的测试
- **集成测试**：测试完整的消息处理流程

### scripts/ - 脚本工具

```
scripts/
├── test/                # 测试脚本
│   ├── get_chat_id.py           # 获取群聊 ID
│   ├── run_integration_test.py  # 运行集成测试
│   ├── send_test_message.py     # 发送测试消息
│   └── README.md                # 测试脚本说明
├── deploy.sh            # 部署管理脚本
├── verify_config.py     # 配置验证脚本
└── README.md            # 脚本说明
```

### docs/ - 项目文档

```
docs/
├── deployment/          # 部署相关文档
│   ├── DEPLOYMENT.md            # 完整部署指南
│   └── QUICKSTART.md            # 快速部署指南
├── CONFIGURATION.md     # 配置说明
├── LANGUAGE_CONFIGURATION.md    # 语言配置说明
├── USER_GUIDE.md        # 用户指南
└── README.md            # 文档索引
```

### data/ - 运行时数据

```
data/
├── archived_sessions/   # 归档的会话数据
├── executor_sessions.json       # 执行器会话映射
└── sessions.json        # 用户会话数据
```

**注意**：此目录包含用户数据，已添加到 `.gitignore`，不会提交到 Git。

## 配置文件

### .env - 环境变量配置

包含敏感信息（API 密钥、应用凭证等），不提交到 Git。

### .env.example - 环境变量模板

配置模板，包含所有可配置项的说明和示例。

### docker-compose.yml - Docker Compose 配置

定义 Docker 容器的配置，包括：
- 环境变量加载
- 数据卷挂载
- 资源限制
- 日志配置

### Dockerfile - Docker 镜像构建

定义如何构建 Docker 镜像。

## 主程序入口

### lark_bot.py

主程序入口，负责：
- 加载配置
- 初始化机器人
- 启动定时任务
- 启动 WebSocket 连接

## 依赖管理

### requirements.txt

列出所有 Python 依赖包及其版本。

## 开发工具配置

### .gitignore

定义 Git 忽略的文件和目录，包括：
- Python 缓存文件
- 虚拟环境
- 敏感配置文件
- 运行时数据
- 测试输出

### .dockerignore

定义 Docker 构建时忽略的文件，减小镜像体积。

## 隐藏目录

### .git/ - Git 版本控制

Git 仓库数据，由 Git 自动管理。

### .hypothesis/ - Hypothesis 测试数据

Hypothesis 框架生成的测试数据和缓存。

### .pytest_cache/ - Pytest 缓存

Pytest 测试框架的缓存数据。

### .kiro/ - Kiro 配置

Kiro IDE 的配置和规范文件（如果使用 Kiro 开发）。

## 文件命名规范

### Python 文件
- 模块文件：`snake_case.py`（如 `message_handler.py`）
- 测试文件：`test_*.py`（如 `test_cache.py`）
- 属性测试：`test_*_properties.py`（如 `test_cache_properties.py`）

### 文档文件
- 大写：`README.md`、`STRUCTURE.md`
- 描述性名称：`CONFIGURATION.md`、`USER_GUIDE.md`

### 配置文件
- 环境变量：`.env`、`.env.example`
- Docker：`Dockerfile`、`docker-compose.yml`
- Git：`.gitignore`、`.dockerignore`

## 路径约定

### 相对路径
所有脚本和配置中的路径都相对于项目根目录。

### 数据路径
- 会话数据：`./data/sessions.json`
- 执行器会话：`./data/executor_sessions.json`

### 配置路径
- 环境变量：`./.env`
- 配置模板：`./.env.example`

## 添加新功能

### 添加新的执行器
1. 在 `xagent/executors/` 创建新文件
2. 继承 `AIAPIExecutor` 或 `AICLIExecutor`
3. 在 `xagent/xagent.py` 中注册

### 添加新的工具类
1. 在 `xagent/utils/` 创建新文件
2. 在 `xagent/utils/__init__.py` 中导出

### 添加新的测试
1. 在 `tests/` 创建 `test_*.py` 文件
2. 使用 pytest 框架编写测试
3. 运行 `pytest tests/` 验证

### 添加新的脚本
1. 在 `scripts/` 或 `scripts/test/` 创建脚本
2. 添加适当的注释和文档
3. 更新 `scripts/README.md`

### 添加新的文档
1. 在 `docs/` 或相应子目录创建文档
2. 使用 Markdown 格式
3. 更新 `docs/README.md` 索引

## 维护建议

### 定期清理
- 删除 `.hypothesis/` 和 `.pytest_cache/`（测试缓存）
- 清理 `data/archived_sessions/`（旧会话数据）

### 备份重要数据
- 定期备份 `data/` 目录
- 备份 `.env` 配置文件（注意安全）

### 更新依赖
```bash
# 更新依赖
pip install --upgrade -r requirements.txt

# 生成新的 requirements.txt
pip freeze > requirements.txt
```

## 相关文档

- [README.md](README.md) - 项目说明
- [docs/README.md](docs/README.md) - 文档索引
- [scripts/README.md](scripts/README.md) - 脚本说明
