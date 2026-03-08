# 部署指南

本文档介绍如何将飞书AI机器人部署到云端服务器。

## 目录

- [Docker 部署（推荐）](#docker-部署推荐)
- [直接部署](#直接部署)
- [Gunicorn 生产部署](#gunicorn-生产部署)
- [云服务商部署](#云服务商部署)
- [常见问题](#常见问题)

## Docker 部署（推荐）

使用 Docker 部署是最简单和可靠的方式。

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+（可选，但推荐）
- 至少 1GB 内存
- 至少 2GB 磁盘空间

### 快速开始

#### 1. 准备配置文件

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件，填入你的凭证
nano .env  # 或使用其他编辑器
```

必需配置：
- `FEISHU_APP_ID`: 飞书应用ID
- `FEISHU_APP_SECRET`: 飞书应用密钥
- 至少一个AI API密钥（`CLAUDE_API_KEY`、`GEMINI_API_KEY` 或 `OPENAI_API_KEY`）

#### 2. 使用 Docker Compose 启动（推荐）

```bash
# 构建并启动容器
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止容器
docker-compose down

# 重启容器
docker-compose restart
```

#### 3. 使用 Docker 命令启动

```bash
# 构建镜像
docker build -t xagent .

# 运行容器
docker run -d \
  --name xagent \
  --restart unless-stopped \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  xagent

# 查看日志
docker logs -f xagent

# 停止容器
docker stop xagent

# 删除容器
docker rm xagent
```

### 数据持久化

容器使用数据卷来持久化会话数据：

```yaml
volumes:
  - ./data:/app/data  # 会话数据存储在宿主机的 ./data 目录
```

这样即使容器重启，会话数据也不会丢失。

### 更新部署

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build

# 或使用 Docker 命令
docker build -t xagent .
docker stop xagent
docker rm xagent
docker run -d \
  --name xagent \
  --restart unless-stopped \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  xagent
```

### CLI 功能支持

如果需要使用 CLI 功能（Claude Code CLI 或 Gemini CLI），需要：

#### 方案1：在容器内安装 CLI 工具

修改 `Dockerfile`，添加 CLI 工具安装：

```dockerfile
# 安装 Node.js（Claude Code CLI 需要）
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# 安装 Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code-cli

# 或安装 Gemini CLI
# RUN npm install -g @google/generative-ai-cli
```

然后挂载目标代码仓库：

```yaml
volumes:
  - ./data:/app/data
  - /path/to/your/project:/workspace:ro  # 只读挂载
```

配置环境变量：

```bash
TARGET_PROJECT_DIR=/workspace
```

#### 方案2：使用宿主机的 CLI 工具（不推荐）

这种方式需要容器能访问宿主机的 CLI 工具，配置较复杂，不推荐。

### 资源限制

在 `docker-compose.yml` 中已配置资源限制：

```yaml
deploy:
  resources:
    limits:
      cpus: '2'        # 最多使用 2 个 CPU 核心
      memory: 2G       # 最多使用 2GB 内存
    reservations:
      cpus: '0.5'      # 保留 0.5 个 CPU 核心
      memory: 512M     # 保留 512MB 内存
```

根据实际需求调整这些值。

## 直接部署

如果不使用 Docker，可以直接在服务器上运行。

### 前置要求

- Python 3.11+
- pip
- 至少 1GB 内存
- 至少 2GB 磁盘空间

### 部署步骤

#### 1. 安装依赖

```bash
# 更新系统
sudo apt-get update && sudo apt-get upgrade -y

# 安装 Python 和 pip
sudo apt-get install -y python3.11 python3.11-venv python3-pip

# 安装 Git
sudo apt-get install -y git
```

#### 2. 克隆项目

```bash
# 克隆代码
git clone https://github.com/fearofnull/xagent.git
cd xagent

# 创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 3. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置
nano .env
```

#### 4. 使用 systemd 管理服务

创建服务文件 `/etc/systemd/system/feishu-bot.service`：

```ini
[Unit]
Description=Feishu AI Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/lark-bot
Environment="PATH=/path/to/lark-bot/venv/bin"
ExecStart=/path/to/lark-bot/venv/bin/python lark_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
# 重新加载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start feishu-bot

# 设置开机自启
sudo systemctl enable feishu-bot

# 查看状态
sudo systemctl status feishu-bot

# 查看日志
sudo journalctl -u feishu-bot -f
```

## Gunicorn 生产部署

对于 Web 管理界面，推荐使用 Gunicorn 作为生产级 WSGI 服务器。Gunicorn 提供更好的性能、稳定性和生产级特性。

### 快速开始

```bash
# 安装 Gunicorn（如果还未安装）
pip install gunicorn

# 使用配置文件启动
gunicorn -c gunicorn.conf.py wsgi:app

# 或使用启动脚本
./scripts/start_web_admin.sh production
```

### 配置说明

项目根目录下的 `gunicorn.conf.py` 提供了生产就绪的配置：

- **Worker 配置**：自动根据 CPU 核心数计算最优 worker 数量
- **超时设置**：120 秒请求超时，30 秒优雅关闭超时
- **日志配置**：访问日志和错误日志分离，支持自定义格式
- **性能优化**：预加载应用、worker 自动重启、keep-alive 连接
- **安全设置**：请求大小限制、代理 IP 信任配置

### 环境变量

通过环境变量自定义配置：

```bash
# .env 文件
WEB_ADMIN_HOST=0.0.0.0
WEB_ADMIN_PORT=5000
WEB_ADMIN_WORKERS=5  # 默认为 (CPU核心数 * 2) + 1
WEB_ADMIN_LOG_LEVEL=info
WEB_ADMIN_PASSWORD=your_secure_password
JWT_SECRET_KEY=your_random_secret_key
```

### Systemd 服务

使用 Systemd 管理 Gunicorn 服务：

```bash
# 复制服务文件
sudo cp deployment/feishu-bot-web-admin.service /etc/systemd/system/

# 根据实际路径修改服务文件
sudo nano /etc/systemd/system/feishu-bot-web-admin.service

# 启动服务
sudo systemctl daemon-reload
sudo systemctl start feishu-bot-web-admin
sudo systemctl enable feishu-bot-web-admin

# 查看状态
sudo systemctl status feishu-bot-web-admin
```

### Nginx 反向代理

推荐使用 Nginx 作为反向代理，提供 HTTPS、负载均衡等功能。配置示例请参考 [Gunicorn 部署指南](GUNICORN_DEPLOYMENT.md#nginx-反向代理)。

### 详细文档

完整的 Gunicorn 配置、优化、监控和故障排除指南，请参考：

📖 **[Gunicorn 生产部署指南](GUNICORN_DEPLOYMENT.md)**

该文档包含：
- 详细的配置说明
- Systemd 服务配置
- Nginx 反向代理配置
- SSL/HTTPS 配置
- 性能优化建议
- 监控和日志分析
- 故障排除指南

## 云服务商部署

### 阿里云 ECS

1. 购买 ECS 实例（推荐配置：2核4GB）
2. 安装 Docker 和 Docker Compose
3. 按照 [Docker 部署](#docker-部署推荐) 步骤操作

### 腾讯云 CVM

1. 购买 CVM 实例（推荐配置：2核4GB）
2. 安装 Docker 和 Docker Compose
3. 按照 [Docker 部署](#docker-部署推荐) 步骤操作

### AWS EC2

1. 创建 EC2 实例（推荐：t3.small 或更高）
2. 安装 Docker 和 Docker Compose：

```bash
# 安装 Docker
sudo yum update -y
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

3. 按照 [Docker 部署](#docker-部署推荐) 步骤操作

### Google Cloud Platform (GCP)

1. 创建 Compute Engine 实例（推荐：e2-small 或更高）
2. 安装 Docker 和 Docker Compose
3. 按照 [Docker 部署](#docker-部署推荐) 步骤操作

### Azure VM

1. 创建虚拟机（推荐：Standard B2s 或更高）
2. 安装 Docker 和 Docker Compose
3. 按照 [Docker 部署](#docker-部署推荐) 步骤操作

## 监控和日志

### 查看日志

**Docker Compose**：
```bash
# 实时查看日志
docker-compose logs -f

# 查看最近 100 行日志
docker-compose logs --tail=100

# 查看特定时间的日志
docker-compose logs --since 2024-01-01T00:00:00
```

**Docker**：
```bash
# 实时查看日志
docker logs -f xagent

# 查看最近 100 行日志
docker logs --tail=100 xagent
```

**systemd**：
```bash
# 实时查看日志
sudo journalctl -u feishu-bot -f

# 查看最近 100 行日志
sudo journalctl -u feishu-bot -n 100
```

### 日志轮转

Docker 已配置日志轮转（在 `docker-compose.yml` 中）：

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"   # 单个日志文件最大 10MB
    max-file: "3"     # 保留最近 3 个日志文件
```

### 监控指标

**查看容器资源使用**：
```bash
# 实时监控
docker stats xagent

# 查看容器详情
docker inspect xagent
```

**查看系统资源**：
```bash
# CPU 和内存使用
top

# 磁盘使用
df -h

# 网络连接
netstat -tuln
```

## 安全建议

### 1. 文件权限设置

为了增强安全性，建议在生产环境中设置正确的文件权限：

**自动设置（推荐）**：

```bash
# 使用提供的脚本自动设置所有文件权限
python scripts/set_file_permissions.py
```

该脚本会：
- 将配置文件（.env、session_configs.json、备份文件）权限设置为 600（仅所有者可读写）
- 将日志文件权限设置为 640（所有者可读写，组可读）

**手动设置**：

```bash
# 设置配置文件权限为 600
chmod 600 .env
chmod 600 data/session_configs.json
chmod 600 data/session_configs.json.backup*

# 设置日志文件权限为 640
chmod 640 logs/*.log*

# 设置目录权限
chmod 755 data
chmod 755 logs
```

**验证权限**：

```bash
# 查看配置文件权限
ls -l .env data/session_configs.json*

# 查看日志文件权限
ls -l logs/*.log*
```

**注意**：
- 在 Windows 系统上，Unix 风格的文件权限可能不会完全生效
- 建议在 Linux/Unix 系统上运行权限设置脚本
- 权限设置应该在部署后立即执行

### 2. 保护敏感信息

- ✅ 不要将 `.env` 文件提交到 Git
- ✅ 使用环境变量或密钥管理服务存储凭证
- ✅ 定期轮换 API 密钥

### 3. 网络安全

- ✅ 配置防火墙，只开放必要的端口
- ✅ 使用 HTTPS（如果需要 webhook）
- ✅ 限制容器的网络访问

### 4. 更新和备份

- ✅ 定期更新系统和依赖
- ✅ 定期备份会话数据（`./data` 目录）
- ✅ 监控日志，及时发现异常

### 5. 资源限制

- ✅ 配置容器资源限制，防止资源耗尽
- ✅ 设置日志轮转，防止磁盘占满
- ✅ 监控资源使用情况

## 常见问题

### Q1: 容器启动失败

**检查日志**：
```bash
docker-compose logs
```

**常见原因**：
- 配置文件错误（检查 `.env` 文件）
- 端口冲突（检查是否有其他服务占用端口）
- 内存不足（增加服务器内存或调整资源限制）

### Q2: 机器人无法连接飞书

**检查**：
- 飞书应用凭证是否正确
- 网络连接是否正常
- 防火墙是否阻止了连接

**测试连接**：
```bash
# 进入容器
docker exec -it xagent bash

# 测试网络
ping open.feishu.cn
```

### Q3: AI 调用失败

**检查**：
- API 密钥是否正确
- API 配额是否用完
- 网络是否能访问 AI 服务

**测试 API**：
```bash
# 进入容器
docker exec -it xagent bash

# 测试配置
python config.py
```

### Q4: 会话数据丢失

**原因**：
- 数据卷未正确挂载
- 容器被删除时未保留数据

**解决**：
- 确保 `docker-compose.yml` 中配置了数据卷
- 定期备份 `./data` 目录

### Q5: 内存占用过高

**解决**：
- 调整 `MAX_SESSION_MESSAGES` 配置，减少会话历史
- 调整 `CACHE_SIZE` 配置，减少缓存大小
- 增加服务器内存
- 配置容器内存限制

### Q6: CLI 功能不可用

**原因**：
- CLI 工具未安装
- 目标代码仓库未挂载
- 权限不足

**解决**：
- 按照 [CLI 功能支持](#cli-功能支持) 配置
- 检查目录挂载和权限
- 查看日志确认错误信息

## 性能优化

### 1. 使用多阶段构建

优化 Dockerfile，减小镜像体积：

```dockerfile
# 构建阶段
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# 运行阶段
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "lark_bot.py"]
```

### 2. 使用缓存

在 `docker-compose.yml` 中配置构建缓存：

```yaml
build:
  context: .
  dockerfile: Dockerfile
  cache_from:
    - xagent:latest
```

### 3. 优化资源配置

根据实际使用情况调整资源限制：

```yaml
deploy:
  resources:
    limits:
      cpus: '1'      # 如果负载不高，可以降低
      memory: 1G     # 根据实际使用调整
```

## 相关文档

- [快速开始](../../README.md#快速开始)
- [配置文档](../CONFIGURATION.md)
- [快速部署指南](QUICKSTART.md)
