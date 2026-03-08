# Gunicorn 生产部署指南

本文档介绍如何使用 Gunicorn 在生产环境中部署 Web 管理界面。

## 目录

- [概述](#概述)
- [前置要求](#前置要求)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [Systemd 服务](#systemd-服务)
- [Nginx 反向代理](#nginx-反向代理)
- [监控和维护](#监控和维护)
- [故障排除](#故障排除)

## 概述

Gunicorn (Green Unicorn) 是一个 Python WSGI HTTP 服务器，适合在生产环境中运行 Flask 应用。相比 Flask 内置的开发服务器，Gunicorn 提供：

- **更好的性能**：多进程并发处理请求
- **更高的稳定性**：自动重启失败的 worker
- **生产级特性**：日志轮转、优雅重启、资源限制等

## 前置要求

- Python 3.11+
- 已安装项目依赖（包括 Gunicorn）
- 配置好的 `.env` 文件
- 至少 1GB 可用内存

## 快速开始

### 1. 安装 Gunicorn

```bash
# 如果还未安装
pip install gunicorn

# 或添加到 requirements.txt
echo "gunicorn>=21.2.0" >> requirements.txt
pip install -r requirements.txt
```

### 2. 配置环境变量

确保 `.env` 文件包含以下必需变量：

```bash
# 必需配置
WEB_ADMIN_PASSWORD=your_secure_password_here
JWT_SECRET_KEY=your_random_secret_key_here

# 可选配置
WEB_ADMIN_HOST=0.0.0.0
WEB_ADMIN_PORT=5000
WEB_ADMIN_WORKERS=5  # 默认为 (CPU核心数 * 2) + 1
WEB_ADMIN_LOG_LEVEL=info
WEB_ADMIN_STATIC_FOLDER=frontend/dist
```

### 3. 启动服务

```bash
# 使用配置文件启动
gunicorn -c gunicorn.conf.py wsgi:app

# 或直接指定参数
gunicorn \
    --bind 0.0.0.0:5000 \
    --workers 4 \
    --timeout 120 \
    --access-logfile logs/web_admin_access.log \
    --error-logfile logs/web_admin_error.log \
    wsgi:app
```

### 4. 验证部署

```bash
# 检查服务是否运行
curl http://localhost:5000/api/auth/login

# 查看日志
tail -f logs/web_admin_access.log
tail -f logs/web_admin_error.log
```

## 配置说明

### Worker 配置

**Worker 数量**：
```python
# 推荐公式：(2 x CPU核心数) + 1
workers = (2 * multiprocessing.cpu_count()) + 1

# 示例：
# 2核CPU：5 workers
# 4核CPU：9 workers
# 8核CPU：17 workers
```

**Worker 类型**：
- `sync`（默认）：适合 CPU 密集型任务
- `gevent`：适合 I/O 密集型任务（需要安装 gevent）
- `eventlet`：异步 I/O（需要安装 eventlet）

**Worker 超时**：
```python
timeout = 120  # 秒，根据实际请求处理时间调整
```

### 日志配置

**日志级别**：
- `debug`：详细调试信息
- `info`：一般信息（推荐）
- `warning`：警告信息
- `error`：错误信息
- `critical`：严重错误

**日志文件**：
```python
accesslog = 'logs/web_admin_access.log'  # 访问日志
errorlog = 'logs/web_admin_error.log'    # 错误日志
```

**日志格式**：
```python
# 访问日志包含：IP、时间、请求、状态码、响应大小、处理时间等
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
```

### 性能优化

**预加载应用**：
```python
preload_app = True  # 在 fork worker 前加载应用，节省内存
```

**Worker 重启**：
```python
max_requests = 1000  # Worker 处理 1000 个请求后重启，防止内存泄漏
max_requests_jitter = 50  # 随机化重启时间，避免所有 worker 同时重启
```

**Keep-Alive**：
```python
keepalive = 5  # 保持连接 5 秒，减少连接开销
```

### 安全配置

**请求限制**：
```python
limit_request_line = 4096  # 请求行最大长度
limit_request_fields = 100  # 请求头字段数量限制
limit_request_field_size = 8190  # 请求头字段大小限制
```

**代理信任**：
```python
forwarded_allow_ips = '127.0.0.1'  # 信任的代理 IP
```

## Systemd 服务

使用 Systemd 管理 Gunicorn 服务，实现自动启动和重启。

### 1. 创建服务文件

```bash
sudo nano /etc/systemd/system/xagent-web-admin.service
```

复制以下内容（根据实际路径调整）：

```ini
[Unit]
Description=XAgent Web Admin Interface
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/xagent
Environment="PATH=/opt/xagent/venv/bin"
EnvironmentFile=/opt/xagent/.env

ExecStart=/opt/xagent/venv/bin/gunicorn \
    -c /opt/xagent/gunicorn.conf.py \
    wsgi:app

Restart=always
RestartSec=10

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/xagent/logs /opt/xagent/data

# 资源限制
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
```

### 2. 启动服务

```bash
# 重新加载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start xagent-web-admin

# 设置开机自启
sudo systemctl enable xagent-web-admin

# 查看状态
sudo systemctl status xagent-web-admin

# 查看日志
sudo journalctl -u xagent-web-admin -f
```

### 3. 管理服务

```bash
# 停止服务
sudo systemctl stop xagent-web-admin

# 重启服务
sudo systemctl restart xagent-web-admin

# 重新加载配置（优雅重启）
sudo systemctl reload xagent-web-admin

# 查看服务日志
sudo journalctl -u xagent-web-admin --since today
```

## Nginx 反向代理

使用 Nginx 作为反向代理，提供 HTTPS、负载均衡、静态文件缓存等功能。

### 1. 安装 Nginx

```bash
sudo apt-get update
sudo apt-get install nginx
```

### 2. 配置 Nginx

创建配置文件 `/etc/nginx/sites-available/xagent-web-admin`：

```nginx
# HTTP 服务器（重定向到 HTTPS）
server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

# HTTPS 服务器
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL 证书配置
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # 日志
    access_log /var/log/nginx/xagent-access.log;
    error_log /var/log/nginx/xagent-error.log;
    
    # 客户端请求大小限制
    client_max_body_size 10M;
    
    # 代理到 Gunicorn
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # WebSocket 支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # 静态文件缓存（可选）
    location /static/ {
        alias /opt/xagent/frontend/dist/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # 健康检查端点
    location /health {
        access_log off;
        return 200 "OK\n";
        add_header Content-Type text/plain;
    }
}
```

### 3. 启用配置

```bash
# 创建符号链接
sudo ln -s /etc/nginx/sites-available/xagent-web-admin /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重新加载 Nginx
sudo systemctl reload nginx
```

### 4. 配置 SSL 证书（使用 Let's Encrypt）

```bash
# 安装 Certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期测试
sudo certbot renew --dry-run
```

## 监控和维护

### 查看进程状态

```bash
# 查看 Gunicorn 进程
ps aux | grep gunicorn

# 查看进程树
pstree -p $(pgrep -f gunicorn)

# 查看资源使用
top -p $(pgrep -f gunicorn | tr '\n' ',' | sed 's/,$//')
```

### 查看日志

```bash
# 访问日志
tail -f logs/web_admin_access.log

# 错误日志
tail -f logs/web_admin_error.log

# Systemd 日志
sudo journalctl -u xagent-web-admin -f

# 查看最近的错误
sudo journalctl -u xagent-web-admin -p err --since today
```

### 日志分析

```bash
# 统计请求数
cat logs/web_admin_access.log | wc -l

# 统计状态码分布
awk '{print $9}' logs/web_admin_access.log | sort | uniq -c | sort -rn

# 统计最慢的请求（响应时间 > 1秒）
awk '$NF > 1000000 {print $7, $9, $NF/1000000 "s"}' logs/web_admin_access.log | sort -k3 -rn | head -20

# 统计访问最多的 IP
awk '{print $1}' logs/web_admin_access.log | sort | uniq -c | sort -rn | head -20
```

### 性能监控

```bash
# 安装监控工具
pip install gunicorn[setproctitle]

# 查看 worker 状态
kill -TTIN $(cat logs/web_admin.pid)  # 增加 worker
kill -TTOU $(cat logs/web_admin.pid)  # 减少 worker
kill -HUP $(cat logs/web_admin.pid)   # 优雅重启
```

### 备份和恢复

```bash
# 备份配置和数据
tar -czf backup-$(date +%Y%m%d).tar.gz \
    .env \
    gunicorn.conf.py \
    wsgi.py \
    data/ \
    logs/

# 恢复
tar -xzf backup-20240101.tar.gz
```

## 故障排除

### 问题 1：服务启动失败

**检查日志**：
```bash
sudo journalctl -u xagent-web-admin -n 50
```

**常见原因**：
- 环境变量未设置（检查 `.env` 文件）
- 端口被占用（使用 `netstat -tuln | grep 5000` 检查）
- 权限问题（检查文件和目录权限）
- Python 依赖缺失（运行 `pip install -r requirements.txt`）

### 问题 2：Worker 频繁重启

**检查内存使用**：
```bash
free -h
ps aux --sort=-%mem | head -10
```

**解决方案**：
- 增加服务器内存
- 减少 worker 数量
- 调整 `max_requests` 参数
- 检查代码是否有内存泄漏

### 问题 3：请求超时

**调整超时设置**：
```python
# gunicorn.conf.py
timeout = 300  # 增加到 5 分钟
```

**Nginx 超时设置**：
```nginx
proxy_connect_timeout 300s;
proxy_send_timeout 300s;
proxy_read_timeout 300s;
```

### 问题 4：502 Bad Gateway

**检查 Gunicorn 是否运行**：
```bash
sudo systemctl status xagent-web-admin
```

**检查端口监听**：
```bash
netstat -tuln | grep 5000
```

**检查 Nginx 配置**：
```bash
sudo nginx -t
```

### 问题 5：日志文件过大

**配置日志轮转**：

创建 `/etc/logrotate.d/xagent-web-admin`：

```
/opt/xagent/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    missingok
    create 0640 www-data www-data
    sharedscripts
    postrotate
        kill -USR1 $(cat /opt/xagent/logs/web_admin.pid)
    endscript
}
```

## 性能优化建议

### 1. Worker 数量优化

根据负载调整 worker 数量：

```bash
# 低负载（< 100 并发）
WEB_ADMIN_WORKERS=4

# 中等负载（100-500 并发）
WEB_ADMIN_WORKERS=8

# 高负载（> 500 并发）
WEB_ADMIN_WORKERS=16
```

### 2. 使用异步 Worker

对于 I/O 密集型应用：

```bash
pip install gevent

# gunicorn.conf.py
worker_class = 'gevent'
worker_connections = 1000
```

### 3. 启用 HTTP/2

在 Nginx 配置中：

```nginx
listen 443 ssl http2;
```

### 4. 启用 Gzip 压缩

在 Nginx 配置中：

```nginx
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
```

### 5. 使用 CDN

将静态文件部署到 CDN，减轻服务器负载。

## 安全加固

### 1. 限制访问 IP

在 Nginx 配置中：

```nginx
# 只允许特定 IP 访问
allow 192.168.1.0/24;
deny all;
```

### 2. 启用速率限制

在 Nginx 配置中：

```nginx
# 限制请求速率
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location /api/ {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://127.0.0.1:5000;
}
```

### 3. 配置防火墙

```bash
# 只开放必要的端口
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### 4. 定期更新

```bash
# 更新系统
sudo apt-get update && sudo apt-get upgrade -y

# 更新 Python 依赖
pip install --upgrade -r requirements.txt
```

## 相关文档

- [部署指南](DEPLOYMENT.md)
- [快速部署](QUICKSTART.md)
- [配置文档](../CONFIGURATION.md)
- [Gunicorn 官方文档](https://docs.gunicorn.org/)

---

**祝你部署顺利！** 🚀
