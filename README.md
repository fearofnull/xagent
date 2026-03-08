# XAgent

一个功能强大的智能助手系统，集成多个主流 AI 服务（Claude、Gemini、OpenAI、Qwen 等），支持统一 API 接口、智能路由、会话管理和可视化配置。

## ✨ 核心特性

- 🤖 **统一 API 接口**: 通过 Web 管理界面配置任意 AI 提供商，使用 `@gpt` 统一调用
- 🔧 **CLI 代码工具**: Claude CLI、Gemini CLI、Qwen CLI，支持代码分析和文件操作
- 🤖 **XAgent 智能助手**: 具备工具调用、多步骤推理、文件操作、网络搜索等能力
- 🔀 **智能路由**: 自动识别意图，选择合适的执行方式
- 💬 **会话管理**: 上下文连续对话，自动管理会话历史
- 🎨 **Web 管理界面**: 可视化配置 AI 提供商、会话设置、全局配置
- 🔄 **动态配置**: 配置更改实时生效，无需重启服务
- 🔒 **安全可靠**: JWT 认证，敏感信息保护，数据本地存储

## 🏗️ 系统架构

系统采用统一 API + CLI 工具 + XAgent 的架构设计：

- **统一 API 接口**: 通过 Web 管理界面配置 AI 提供商，使用 `@gpt` 命令统一调用
- **CLI 工具集**: Claude CLI、Gemini CLI、Qwen CLI，支持代码分析和文件操作
- **XAgent 智能助手**: 具备工具调用、多步骤推理、文件操作、网络搜索等能力
- **智能路由**: 根据命令前缀和消息内容自动选择执行方式
- **Web 管理界面**: 可视化配置提供商、会话、全局设置

详细架构图和交互流程见本文档的[系统架构](#-系统架构)部分。

## 🚀 快速开始

### 方式 1: Docker 部署（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/fearofnull/feishu-ai-bot
cd feishu-ai-bot

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入飞书凭证

# 3. 启动服务（包括机器人和 Web 管理界面）
cd deployment/docker
docker-compose up -d

# 4. 查看日志
docker-compose logs -f feishu-bot
```

详细部署文档见 [Docker 部署指南](deployment/docker/README.md)。

### 方式 2: 本地运行

```bash
# 1. 安装 Python 依赖
pip install -r requirements.txt

# 2. 构建前端
cd frontend
npm install
npm run build
cd ..

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 填入配置

# 4. 启动服务（同时启动机器人和 Web 管理界面）
python main.py
```

### 必需配置

在 `.env` 文件中配置：

```bash
# 飞书应用凭证（必需）
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret

# Web 管理界面（推荐启用）
ENABLE_WEB_ADMIN=true
WEB_ADMIN_PORT=8080
WEB_ADMIN_PASSWORD=your_secure_password
JWT_SECRET_KEY=your_random_secret_key

# XAgent 配置（可选）
# Serper API Key（用于 XAgent 的网络搜索功能）
# 注册地址：https://serper.dev/
SERPER_API_KEY=your_serper_api_key
```

### 配置 AI 提供商

通过 Web 管理界面配置 AI 提供商：

1. 访问 `http://localhost:8080` 登录管理界面
2. 进入"提供商配置"页面
3. 添加 AI 提供商（如 Claude、Gemini、OpenAI 等）
4. 配置 API 密钥和模型参数
5. 设置默认提供商

完成后，使用 `@gpt` 命令即可调用配置的提供商。

详细配置说明见 [配置文档](docs/guides/CONFIGURATION.md)。

## 💡 使用示例

### 基本对话（使用统一 API）
```
@机器人 你好，介绍一下自己
@机器人 什么是 Python 装饰器？
@机器人 @gpt 解释量子计算原理
```

### CLI 代码工具
```
@机器人 @claude-cli 分析项目架构
@机器人 @gemini-cli 检查代码质量
@机器人 @qwen-cli 优化这段代码
```

### XAgent 智能助手
```
@机器人 @agent 查看今天的热点新闻
@机器人 @agent 搜索最新的 Python 3.12 特性
@机器人 @agent 读取并分析项目中的 README.md 文件
```

### 会话管理
```
@机器人 /help           # 查看帮助
@机器人 /session        # 查看会话信息
@机器人 /new            # 创建新会话
@机器人 /setdir /path   # 设置项目目录（CLI 工具使用）
@机器人 /lang zh-CN     # 设置回复语言
@机器人 /cliprovider claude  # 设置默认 CLI 提供商
```

更多使用方法见 [用户指南](docs/guides/USER_GUIDE.md)。

## 📚 文档

### 核心文档
- [用户指南](docs/guides/USER_GUIDE.md) - 如何使用机器人
- [配置指南](docs/guides/CONFIGURATION.md) - 详细配置说明

### Web 管理界面
- [Web 管理界面](docs/guides/WEB_ADMIN_README.md) - 完整的 Web 管理文档
- [Web 用户指南](docs/guides/WEB_ADMIN_USER_GUIDE.md) - Web 界面使用指南

### 部署文档
- [Docker 部署指南](deployment/docker/README.md) - Docker 容器化部署
- [部署指南](docs/deployment/DEPLOYMENT.md) - 完整部署文档
- [快速部署](docs/deployment/QUICKSTART.md) - 5 分钟快速部署

### 其他文档
- [动态配置](docs/guides/DYNAMIC_CONFIG.md) - 会话级配置
- [会话管理](docs/guides/SESSION_MANAGEMENT.md) - 会话管理说明
- [项目结构](docs/STRUCTURE.md) - 代码结构说明

## 🔒 安全与隐私

- ✅ 敏感信息本地存储，不提交到 Git
- ✅ API 密钥通过环境变量管理
- ✅ Web 管理界面 JWT 认证 + 速率限制
- ✅ 会话数据仅存储在本地
- ✅ 支持手动清理会话历史

详细安全说明见本文档的[安全与隐私](#-安全与隐私)部分。

## 🛠️ 技术栈

### 后端
- Python 3.8+
- Flask 3.0+
- lark-oapi (飞书 SDK)

### 前端
- Vue.js 3
- Element Plus
- Vite

### 部署
- Docker
- Nginx
- Systemd

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

**开始使用**: 查看 [快速开始](#-快速开始) 部署你的飞书 AI 机器人

**获取帮助**: 查看 [用户指南](docs/guides/USER_GUIDE.md) 了解详细使用方法
