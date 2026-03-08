# Nginx 部署指南

本指南详细说明如何使用 Nginx 作为反向代理部署XAgent Web 管理界面。

## 目录

- [架构概述](#架构概述)
- [前置要求](#前置要求)
- [安装 Nginx](#安装-nginx)
- [配置 Nginx](#配置-nginx)
- [SSL/TLS 配置](#ssltls-配置)
- [性能优化](#性能优化)
- [安全加固](#安全加固)
- [故障排除](#故障排除)

## 架构概述

在生产环境中，推荐使用以下架构：

```
Internet
    ↓
Nginx (Port 80/443)
    ↓ (Reverse Proxy)
Gunicorn (Port 5000)
    ↓
Flask Application
```

**Nginx 的作用**：
- 处理 HTTPS/SSL 终止
- 提供静态文件服务（前端资源）
- 反向代理 API 请求到 Gunicorn
- 负载均衡（如果有多个 Gunicorn 实例）
- 请求缓存和压缩
- 安全防护（速率限制、IP 过滤等）

## 前置要求

1. **已安装并运行的 Gunicorn 服务**
   - 参考 [Gunicorn 部署指南](GUNICORN_DEPLOYMENT.md)
   - 确保 Gunicorn 在 127.0.0.1:5000 上运行

2. **前端已构建**
   ```bash
   cd frontend
   npm install
   npm run build
   ```
   构建产物位于 `frontend/dist/` 目录

3. **域名（可选但推荐）**
   - 用于 HTTPS 证书
   - 如果没有域名，可以使用 IP 地址和自签名证书

## 安装 Nginx

### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install nginx
```

### CentOS/RHEL

```bash
sudo yum install epel-release
sudo yum install nginx
```

### 验证安装

```bash
nginx -v
sudo systemctl status nginx
```

## 配置 Nginx

### 1. 复制配置文件

```bash
# 从项目根目录执行
sudo cp deployment/nginx.conf.example /etc/nginx/sites-available/xagent-web-admin
```

### 2. 修改配置

编辑配置文件：

```bash
sudo nano /etc/nginx/sites-available/xagent-web-admin
```

**必须修改的配置项**：

```nginx
# 1. 修改域名
server_name your-domain.com www.your-domain.com;
# 改为：
server_name admin.example.com;

# 2. 修改前端静态文件路径
root /opt/xagent/frontend/dist;
# 改为你的实际路径

# 3. 修改后端地址（如果不是默认的 127.0.0.1:5000）
upstream xagent_backend {
    server 127.0.0.1:5000 fail_timeout=0;
}

# 4. 修改 SSL 证书路径（稍后配置）
ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
```

### 3. 启用站点

```bash
# 创建符号链接
sudo ln -s /etc/nginx/sites-available/xagent-web-admin /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 如果测试通过，重新加载 Nginx
sudo systemctl reload nginx
```

### 4. 配置防火墙

```bash
# Ubuntu/Debian (UFW)
sudo ufw allow 'Nginx Full'
sudo ufw allow 'Nginx HTTP'
sudo ufw allow 'Nginx HTTPS'

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## SSL/TLS 配置

### 使用 Let's Encrypt（推荐）

Let's Encrypt 提供免费的 SSL 证书，自动续期。

#### 1. 安装 Certbot

```bash
# Ubuntu/Debian
sudo apt-get install certbot python3-certbot-nginx

# CentOS/RHEL
sudo yum install certbot python3-certbot-nginx
```

#### 2. 获取证书

**方法 1：自动配置（推荐）**

```bash
sudo certbot --nginx -d admin.example.com -d www.admin.example.com
```

Certbot 会自动：
- 验证域名所有权
- 获取证书
- 修改 Nginx 配置
- 设置自动续期

**方法 2：仅获取证书（手动配置）**

```bash
sudo certbot certonly --nginx -d admin.example.com
```

然后手动更新 Nginx 配置中的证书路径。

#### 3. 测试自动续期

```bash
sudo certbot renew --dry-run
```

#### 4. 设置自动续期

Certbot 会自动创建 cron 任务或 systemd timer。验证：

```bash
# 查看 systemd timer
sudo systemctl list-timers | grep certbot

# 或查看 cron 任务
sudo cat /etc/cron.d/certbot
```

### 使用自签名证书（开发/测试）

如果没有域名或仅用于内部测试：

```bash
# 创建证书目录
sudo mkdir -p /etc/nginx/ssl

# 生成自签名证书（有效期 365 天）
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/xagent.key \
    -out /etc/nginx/ssl/xagent.crt \
    -subj "/C=CN/ST=Beijing/L=Beijing/O=Company/CN=admin.example.com"

# 修改 Nginx 配置中的证书路径
ssl_certificate /etc/nginx/ssl/xagent.crt;
ssl_certificate_key /etc/nginx/ssl/xagent.key;
```

**注意**：自签名证书会在浏览器中显示安全警告，仅用于开发/测试环境。

## 性能优化

### 1. 启用 HTTP/2

HTTP/2 已在示例配置中启用：

```nginx
listen 443 ssl http2;
```

### 2. 使用 Unix Socket（可选）

Unix socket 比 TCP socket 性能更好：

**修改 Gunicorn 配置** (`gunicorn.conf.py`)：

```python
bind = 'unix:/opt/xagent/gunicorn.sock'
```

**修改 Nginx 配置**：

```nginx
upstream xagent_backend {
    server unix:/opt/xagent/gunicorn.sock fail_timeout=0;
}
```

**设置 socket 权限**：

```bash
# 确保 Nginx 用户可以访问 socket
sudo chown www-data:www-data /opt/xagent/gunicorn.sock
```

### 3. 调整 Worker 连接数

编辑 `/etc/nginx/nginx.conf`：

```nginx
events {
    worker_connections 2048;  # 增加连接数
    use epoll;                # Linux 上使用 epoll
}
```

### 4. 启用缓存（可选）

为 API 响应添加缓存（谨慎使用）：

```nginx
# 在 http 块中定义缓存区域
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m inactive=60m;

# 在 location /api/ 中启用缓存
location /api/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_key "$scheme$request_method$host$request_uri";
    add_header X-Cache-Status $upstream_cache_status;
    # ... 其他配置
}
```

### 5. 调整缓冲区大小

```nginx
# 在 http 或 server 块中
proxy_buffer_size 4k;
proxy_buffers 8 4k;
proxy_busy_buffers_size 8k;
```

## 安全加固

### 1. 限制访问 IP（可选）

如果只允许特定 IP 访问：

```nginx
# 在 server 块中
location / {
    allow 192.168.1.0/24;  # 允许内网
    allow 203.0.113.0/24;  # 允许办公网络
    deny all;              # 拒绝其他所有 IP
    
    # ... 其他配置
}
```

### 2. 启用速率限制

防止暴力破解和 DDoS 攻击：

```nginx
# 在 http 块中定义限制区域
limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=60r/m;

# 在 server 块中应用限制
location /api/auth/login {
    limit_req zone=login_limit burst=3 nodelay;
    limit_req_status 429;
    # ... 其他配置
}

location /api/ {
    limit_req zone=api_limit burst=10 nodelay;
    # ... 其他配置
}
```

### 3. 隐藏 Nginx 版本

编辑 `/etc/nginx/nginx.conf`：

```nginx
http {
    server_tokens off;  # 隐藏版本号
    # ...
}
```

### 4. 配置 ModSecurity（可选）

ModSecurity 是一个 Web 应用防火墙（WAF）：

```bash
# 安装 ModSecurity
sudo apt-get install libnginx-mod-security

# 配置规则集（OWASP Core Rule Set）
# 参考：https://github.com/SpiderLabs/ModSecurity-nginx
```

### 5. 定期更新

```bash
# 定期更新 Nginx 和系统
sudo apt-get update
sudo apt-get upgrade nginx
```

## 监控和日志

### 1. 查看访问日志

```bash
# 实时查看访问日志
sudo tail -f /var/log/nginx/xagent-web-admin-access.log

# 查看错误日志
sudo tail -f /var/log/nginx/xagent-web-admin-error.log
```

### 2. 日志轮转

Nginx 默认配置了日志轮转。验证：

```bash
cat /etc/logrotate.d/nginx
```

### 3. 监控 Nginx 状态（可选）

启用 stub_status 模块：

```nginx
# 在 server 块中添加
location /nginx_status {
    stub_status on;
    access_log off;
    allow 127.0.0.1;
    deny all;
}
```

查看状态：

```bash
curl http://localhost/nginx_status
```

## 故障排除

### 问题 1：502 Bad Gateway

**原因**：Nginx 无法连接到 Gunicorn 后端。

**解决方法**：

1. 检查 Gunicorn 是否运行：
   ```bash
   sudo systemctl status xagent-web-admin
   ```

2. 检查端口是否监听：
   ```bash
   sudo netstat -tuln | grep 5000
   ```

3. 检查防火墙规则：
   ```bash
   sudo iptables -L -n
   ```

4. 查看 Nginx 错误日志：
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

### 问题 2：403 Forbidden

**原因**：Nginx 没有权限访问静态文件。

**解决方法**：

1. 检查文件权限：
   ```bash
   ls -la /opt/xagent/frontend/dist/
   ```

2. 确保 Nginx 用户有读取权限：
   ```bash
   sudo chown -R www-data:www-data /opt/xagent/frontend/dist/
   sudo chmod -R 755 /opt/xagent/frontend/dist/
   ```

3. 检查 SELinux（CentOS/RHEL）：
   ```bash
   sudo setenforce 0  # 临时禁用
   # 或配置 SELinux 策略
   ```

### 问题 3：SSL 证书错误

**原因**：证书配置不正确或已过期。

**解决方法**：

1. 检查证书文件是否存在：
   ```bash
   sudo ls -la /etc/letsencrypt/live/your-domain.com/
   ```

2. 测试证书：
   ```bash
   sudo openssl x509 -in /etc/letsencrypt/live/your-domain.com/fullchain.pem -text -noout
   ```

3. 手动续期证书：
   ```bash
   sudo certbot renew
   ```

### 问题 4：静态文件 404

**原因**：前端构建产物路径不正确。

**解决方法**：

1. 确认前端已构建：
   ```bash
   ls -la /opt/xagent/frontend/dist/
   ```

2. 检查 Nginx 配置中的 root 路径：
   ```bash
   sudo grep "root" /etc/nginx/sites-available/xagent-web-admin
   ```

3. 重新构建前端：
   ```bash
   cd /opt/xagent/frontend
   npm run build
   ```

### 问题 5：配置测试失败

**原因**：Nginx 配置语法错误。

**解决方法**：

1. 查看详细错误信息：
   ```bash
   sudo nginx -t
   ```

2. 检查配置文件语法：
   - 确保每个指令以分号结尾
   - 确保大括号匹配
   - 确保路径正确

3. 使用配置检查工具：
   ```bash
   sudo nginx -T  # 显示完整配置
   ```

## 性能测试

### 使用 Apache Bench

```bash
# 安装 Apache Bench
sudo apt-get install apache2-utils

# 测试 API 性能
ab -n 1000 -c 10 https://admin.example.com/api/configs

# 测试静态文件性能
ab -n 1000 -c 10 https://admin.example.com/
```

### 使用 wrk

```bash
# 安装 wrk
sudo apt-get install wrk

# 测试性能
wrk -t4 -c100 -d30s https://admin.example.com/
```

## 最佳实践总结

1. **始终使用 HTTPS**：保护用户数据和认证令牌
2. **启用 HTTP/2**：提高性能
3. **配置安全头**：防止常见的 Web 攻击
4. **启用 Gzip 压缩**：减少传输大小
5. **合理配置缓存**：静态资源长期缓存，API 响应不缓存
6. **监控日志**：定期检查访问和错误日志
7. **定期更新**：保持 Nginx 和 SSL 证书最新
8. **备份配置**：在修改前备份配置文件
9. **使用速率限制**：防止滥用和攻击
10. **测试配置**：每次修改后运行 `nginx -t`

## 相关文档

- [Gunicorn 部署指南](GUNICORN_DEPLOYMENT.md)
- [完整部署指南](DEPLOYMENT.md)
- [Nginx 官方文档](https://nginx.org/en/docs/)
- [Let's Encrypt 文档](https://letsencrypt.org/docs/)

## 获取帮助

如果遇到问题：

1. 查看 Nginx 错误日志
2. 查看 Gunicorn 日志
3. 运行 `nginx -t` 检查配置
4. 参考本文档的故障排除部分
5. 提交 GitHub Issue 并附上详细错误信息
