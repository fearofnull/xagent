# Web Admin Interface API 文档

## 概述

本文档描述了XAgent Web 管理界面的所有 RESTful API 端点。API 采用 JSON 格式进行数据交换，使用基于 JWT 的令牌认证。

**基础 URL**: `http://localhost:5000/api`

**认证方式**: Bearer Token (JWT)

**内容类型**: `application/json`

## 通用响应格式

### 成功响应

```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}
```

### 错误响应

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "用户友好的错误描述",
    "field": "field_name"
  }
}
```

## 认证

所有 API 端点（除了登录）都需要在请求头中包含有效的 JWT 令牌：

```
Authorization: Bearer <your_jwt_token>
```

---

## API 端点

### 1. 认证 API

#### 1.1 用户登录

**端点**: `POST /api/auth/login`

**描述**: 使用管理员密码登录，获取访问令牌。

**认证**: 不需要

**请求体**:
```json
{
  "password": "your_admin_password"
}
```


**成功响应** (200 OK):
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 7200,
    "expires_at": "2024-01-01T14:00:00"
  },
  "message": "Login successful"
}
```

**错误响应**:

- **400 Bad Request** - 缺少密码
```json
{
  "success": false,
  "error": {
    "code": "MISSING_PASSWORD",
    "message": "Password is required"
  }
}
```

- **401 Unauthorized** - 密码错误
```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid password"
  }
}
```

- **500 Internal Server Error** - 服务器内部错误
```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An error occurred during login"
  }
}
```

**示例请求**:
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"password": "your_password"}'
```


---

#### 1.2 用户登出

**端点**: `POST /api/auth/logout`

**描述**: 登出当前用户（客户端需要清除本地存储的令牌）。

**认证**: 需要

**请求体**: 无

**成功响应** (200 OK):
```json
{
  "success": true,
  "message": "Logout successful"
}
```

**错误响应**:

- **401 Unauthorized** - 令牌无效或过期
```json
{
  "success": false,
  "error": {
    "code": "INVALID_TOKEN",
    "message": "Invalid or expired token"
  }
}
```

**示例请求**:
```bash
curl -X POST http://localhost:5000/api/auth/logout \
  -H "Authorization: Bearer <your_token>"
```

---

### 2. 配置查询 API

#### 2.1 获取所有配置列表

**端点**: `GET /api/configs`

**描述**: 获取所有会话配置的列表，支持筛选、搜索和排序。

**认证**: 需要

**查询参数**:
- `session_type` (可选): 按会话类型筛选，可选值：`user`、`group`
- `search` (可选): 按 session_id 搜索（不区分大小写）
- `sort` (可选): 排序字段，默认为 `updated_at`
- `order` (可选): 排序顺序，可选值：`asc`（升序）、`desc`（降序，默认）


**成功响应** (200 OK):
```json
{
  "success": true,
  "data": [
    {
      "session_id": "ou_abc123",
      "session_type": "user",
      "config": {
        "target_project_dir": "/home/user/project",
        "response_language": "中文",
        "default_provider": "claude",
        "default_layer": "api",
        "default_cli_provider": null
      },
      "metadata": {
        "created_by": "ou_admin",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_by": "ou_admin",
        "updated_at": "2024-01-02T15:30:00Z",
        "update_count": 3
      }
    },
    {
      "session_id": "oc_group456",
      "session_type": "group",
      "config": {
        "target_project_dir": "/home/user/team-project",
        "response_language": "English",
        "default_provider": "gemini",
        "default_layer": "cli",
        "default_cli_provider": "claude"
      },
      "metadata": {
        "created_by": "ou_admin",
        "created_at": "2024-01-03T08:00:00Z",
        "updated_by": "ou_admin",
        "updated_at": "2024-01-03T08:00:00Z",
        "update_count": 1
      }
    }
  ]
}
```

**错误响应**:

- **401 Unauthorized** - 未认证
- **500 Internal Server Error** - 服务器错误

**示例请求**:
```bash
# 获取所有配置
curl -X GET http://localhost:5000/api/configs \
  -H "Authorization: Bearer <your_token>"

# 筛选用户配置
curl -X GET "http://localhost:5000/api/configs?session_type=user" \
  -H "Authorization: Bearer <your_token>"

# 搜索特定 session_id
curl -X GET "http://localhost:5000/api/configs?search=abc" \
  -H "Authorization: Bearer <your_token>"

# 按更新时间升序排序
curl -X GET "http://localhost:5000/api/configs?sort=updated_at&order=asc" \
  -H "Authorization: Bearer <your_token>"
```


---

#### 2.2 获取单个配置详情

**端点**: `GET /api/configs/:session_id`

**描述**: 获取指定会话的配置详情。

**认证**: 需要

**路径参数**:
- `session_id`: 会话 ID（用户 ID 或群组 ID）

**成功响应** (200 OK):
```json
{
  "success": true,
  "data": {
    "session_id": "ou_abc123",
    "session_type": "user",
    "config": {
      "target_project_dir": "/home/user/project",
      "response_language": "中文",
      "default_provider": "claude",
      "default_layer": "api",
      "default_cli_provider": null
    },
    "metadata": {
      "created_by": "ou_admin",
      "created_at": "2024-01-01T10:00:00Z",
      "updated_by": "ou_admin",
      "updated_at": "2024-01-02T15:30:00Z",
      "update_count": 3
    }
  }
}
```

**错误响应**:

- **404 Not Found** - 配置不存在
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Configuration for session ou_abc123 not found"
  }
}
```

- **401 Unauthorized** - 未认证
- **500 Internal Server Error** - 服务器错误

**示例请求**:
```bash
curl -X GET http://localhost:5000/api/configs/ou_abc123 \
  -H "Authorization: Bearer <your_token>"
```


---

#### 2.3 获取有效配置

**端点**: `GET /api/configs/:session_id/effective`

**描述**: 获取应用优先级规则后的有效配置（会话配置 + 全局默认配置）。

**认证**: 需要

**路径参数**:
- `session_id`: 会话 ID

**成功响应** (200 OK):
```json
{
  "success": true,
  "data": {
    "effective_config": {
      "target_project_dir": "/home/user/project",
      "response_language": "中文",
      "default_provider": "claude",
      "default_layer": "api",
      "default_cli_provider": "gemini"
    }
  }
}
```

**说明**: 
- 如果会话配置中某个字段为 `null`，则使用全局配置的对应字段值
- 如果会话配置中某个字段有值，则使用会话配置的值

**错误响应**:

- **401 Unauthorized** - 未认证
- **500 Internal Server Error** - 服务器错误

**示例请求**:
```bash
curl -X GET http://localhost:5000/api/configs/ou_abc123/effective \
  -H "Authorization: Bearer <your_token>"
```

---

#### 2.4 获取全局配置

**端点**: `GET /api/configs/global`

**描述**: 获取全局默认配置。

**认证**: 需要

**成功响应** (200 OK):
```json
{
  "success": true,
  "data": {
    "global_config": {
      "target_project_dir": "/home/default/project",
      "response_language": "中文",
      "default_provider": "claude",
      "default_layer": "api",
      "default_cli_provider": null
    }
  }
}
```

**错误响应**:

- **401 Unauthorized** - 未认证
- **500 Internal Server Error** - 服务器错误

**示例请求**:
```bash
curl -X GET http://localhost:5000/api/configs/global \
  -H "Authorization: Bearer <your_token>"
```


---

### 3. 配置修改 API

#### 3.1 更新配置

**端点**: `PUT /api/configs/:session_id`

**描述**: 更新或创建会话配置。

**认证**: 需要

**路径参数**:
- `session_id`: 会话 ID

**请求体**:
```json
{
  "session_type": "user",
  "target_project_dir": "/home/user/new-project",
  "response_language": "English",
  "default_provider": "gemini",
  "default_layer": "cli",
  "default_cli_provider": "claude"
}
```

**字段说明**:
- `session_type` (可选): 会话类型，可选值：`user`、`group`，默认为 `user`
- `target_project_dir` (可选): 目标项目目录路径
- `response_language` (可选): 响应语言
- `default_provider` (可选): 默认提供商，可选值：`claude`、`gemini`、`openai`
- `default_layer` (可选): 默认层级，可选值：`api`、`cli`
- `default_cli_provider` (可选): 默认 CLI 提供商，可选值：`claude`、`gemini`、`openai`、`null`

**注意**: 
- 所有字段都是可选的，只需要传入需要更新的字段
- 传入空字符串或 `null` 将清除该字段的值


**成功响应** (200 OK):
```json
{
  "success": true,
  "data": {
    "session_id": "ou_abc123",
    "session_type": "user",
    "config": {
      "target_project_dir": "/home/user/new-project",
      "response_language": "English",
      "default_provider": "gemini",
      "default_layer": "cli",
      "default_cli_provider": "claude"
    },
    "metadata": {
      "created_by": "admin",
      "created_at": "2024-01-01T10:00:00Z",
      "updated_by": "admin",
      "updated_at": "2024-01-04T12:00:00Z",
      "update_count": 4
    }
  },
  "message": "Configuration updated successfully"
}
```

**错误响应**:

- **400 Bad Request** - 无效的 provider 值
```json
{
  "success": false,
  "error": {
    "code": "INVALID_PROVIDER",
    "message": "Invalid provider. Must be one of: ['claude', 'gemini', 'openai']",
    "field": "default_provider"
  }
}
```

- **400 Bad Request** - 无效的 layer 值
```json
{
  "success": false,
  "error": {
    "code": "INVALID_LAYER",
    "message": "Invalid layer. Must be one of: ['api', 'cli']",
    "field": "default_layer"
  }
}
```

- **401 Unauthorized** - 未认证
- **500 Internal Server Error** - 服务器错误

**示例请求**:
```bash
# 更新配置
curl -X PUT http://localhost:5000/api/configs/ou_abc123 \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "target_project_dir": "/home/user/new-project",
    "default_provider": "gemini"
  }'

# 清除某个字段
curl -X PUT http://localhost:5000/api/configs/ou_abc123 \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "default_cli_provider": null
  }'
```


---

#### 3.2 删除配置（重置）

**端点**: `DELETE /api/configs/:session_id`

**描述**: 删除指定会话的配置，恢复为使用全局默认配置。

**认证**: 需要

**路径参数**:
- `session_id`: 会话 ID

**成功响应** (200 OK):
```json
{
  "success": true,
  "message": "Configuration deleted successfully"
}
```

**错误响应**:

- **404 Not Found** - 配置不存在
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Configuration for session ou_abc123 not found"
  }
}
```

- **401 Unauthorized** - 未认证
- **500 Internal Server Error** - 服务器错误

**示例请求**:
```bash
curl -X DELETE http://localhost:5000/api/configs/ou_abc123 \
  -H "Authorization: Bearer <your_token>"
```

---

### 4. 导出导入 API

#### 4.1 导出配置

**端点**: `POST /api/configs/export`

**描述**: 导出所有配置为 JSON 文件。

**认证**: 需要

**请求体**: 无

**成功响应** (200 OK):
- 返回 JSON 文件下载
- 文件名格式：`xagent_configs_YYYYMMDD_HHMMSS.json`
- Content-Type: `application/json`


**导出文件格式**:
```json
{
  "export_timestamp": "2024-01-04T12:00:00Z",
  "export_version": "1.0",
  "configs": [
    {
      "session_id": "ou_abc123",
      "session_type": "user",
      "config": {
        "target_project_dir": "/home/user/project",
        "response_language": "中文",
        "default_provider": "claude",
        "default_layer": "api",
        "default_cli_provider": null
      },
      "metadata": {
        "created_by": "ou_admin",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_by": "ou_admin",
        "updated_at": "2024-01-02T15:30:00Z",
        "update_count": 3
      }
    }
  ]
}
```

**错误响应**:

- **401 Unauthorized** - 未认证
- **500 Internal Server Error** - 导出失败

**示例请求**:
```bash
curl -X POST http://localhost:5000/api/configs/export \
  -H "Authorization: Bearer <your_token>" \
  -o configs_backup.json
```

---

#### 4.2 导入配置

**端点**: `POST /api/configs/import`

**描述**: 从 JSON 文件导入配置。导入前会自动创建备份。

**认证**: 需要

**请求体**: 
- Content-Type: `multipart/form-data`
- 字段名: `file`
- 文件类型: JSON


**成功响应** (200 OK):
```json
{
  "success": true,
  "data": {
    "imported_count": 5
  },
  "message": "Successfully imported 5 configuration(s)"
}
```

**错误响应**:

- **400 Bad Request** - 未提供文件
```json
{
  "success": false,
  "error": {
    "code": "MISSING_FILE",
    "message": "No file provided in request"
  }
}
```

- **400 Bad Request** - JSON 格式错误
```json
{
  "success": false,
  "error": {
    "code": "INVALID_JSON",
    "message": "Invalid JSON format: Expecting value: line 1 column 1 (char 0)"
  }
}
```

- **400 Bad Request** - 缺少必需字段
```json
{
  "success": false,
  "error": {
    "code": "MISSING_CONFIGS",
    "message": "Import data must contain \"configs\" field"
  }
}
```

- **400 Bad Request** - 配置数据格式错误
```json
{
  "success": false,
  "error": {
    "code": "MISSING_REQUIRED_FIELDS",
    "message": "Configuration at index 0 is missing required fields: ['session_id', 'config']"
  }
}
```

- **400 Bad Request** - 无效的 provider 值
```json
{
  "success": false,
  "error": {
    "code": "INVALID_PROVIDER",
    "message": "Configuration at index 2 has invalid provider: invalid_provider"
  }
}
```

- **401 Unauthorized** - 未认证
- **500 Internal Server Error** - 导入失败


**示例请求**:
```bash
curl -X POST http://localhost:5000/api/configs/import \
  -H "Authorization: Bearer <your_token>" \
  -F "file=@configs_backup.json"
```

**导入文件要求**:
1. 必须是有效的 JSON 格式
2. 必须包含 `configs` 数组字段
3. 每个配置对象必须包含以下字段：
   - `session_id`: 会话 ID
   - `session_type`: 会话类型（`user` 或 `group`）
   - `config`: 配置对象，包含所有配置字段
   - `metadata`: 元数据对象，包含所有元数据字段
4. `provider` 和 `layer` 值必须有效
5. 文件必须是 UTF-8 编码

**备份说明**:
- 导入前会自动创建当前配置的备份
- 备份文件名格式：`session_configs.json.backup_YYYYMMDD_HHMMSS`
- 备份文件保存在配置文件相同目录

---

### 5. 定时任务 API

#### 5.1 获取所有定时任务

**端点**: `GET /api/cron/jobs`

**描述**: 获取所有定时任务的列表。

**认证**: 需要

**成功响应** (200 OK):
```json
{
  "success": true,
  "data": [
    {
      "id": "job-123",
      "name": "Daily Reminder",
      "enabled": true,
      "schedule": {
        "type": "cron",
        "cron": "0 9 * * *",
        "timezone": "UTC"
      },
      "task_type": "text",
      "text": "Good morning!",
      "dispatch": {
        "type": "channel",
        "channel": "console",
        "target": {
          "user_id": "test-user",
          "session_id": "test-session"
        },
        "mode": "final",
        "meta": {}
      },
      "runtime": {
        "max_concurrency": 1,
        "timeout_seconds": 120,
        "misfire_grace_seconds": 60
      },
      "meta": {}
    }
  ]
}
```

**错误响应**:

- **401 Unauthorized** - 未认证
- **500 Internal Server Error** - 服务器错误

**示例请求**:
```bash
curl -X GET http://localhost:5000/api/cron/jobs \
  -H "Authorization: Bearer <your_token>"
```

---

#### 5.2 创建定时任务

**端点**: `POST /api/cron/jobs`

**描述**: 创建一个新的定时任务。

**认证**: 需要

**请求体**:
```json
{
  "id": "job-123",
  "name": "Daily Reminder",
  "enabled": true,
  "schedule": {
    "type": "cron",
    "cron": "0 9 * * *",
    "timezone": "UTC"
  },
  "task_type": "text",
  "text": "Good morning!",
  "dispatch": {
    "type": "channel",
    "channel": "console",
    "target": {
      "user_id": "test-user",
      "session_id": "test-session"
    },
    "mode": "final",
    "meta": {}
  },
  "runtime": {
    "max_concurrency": 1,
    "timeout_seconds": 120,
    "misfire_grace_seconds": 60
  },
  "meta": {}
}
```

**字段说明**:
- `id`: 任务 ID（唯一标识）
- `name`: 任务名称
- `enabled`: 是否启用
- `schedule`: 调度配置
- `task_type`: 任务类型（`text` 或 `agent`）
- `text`: 文本任务内容
- `dispatch`: 分发配置
- `runtime`: 运行时配置
- `meta`: 元数据

**成功响应** (200 OK):
```json
{
  "success": true,
  "data": {
    "id": "job-123",
    "name": "Daily Reminder",
    "enabled": true,
    "schedule": {
      "type": "cron",
      "cron": "0 9 * * *",
      "timezone": "UTC"
    },
    "task_type": "text",
    "text": "Good morning!",
    "dispatch": {
      "type": "channel",
      "channel": "console",
      "target": {
        "user_id": "test-user",
        "session_id": "test-session"
      },
      "mode": "final",
      "meta": {}
    },
    "runtime": {
      "max_concurrency": 1,
      "timeout_seconds": 120,
      "misfire_grace_seconds": 60
    },
    "meta": {}
  },
  "message": "Cron job created successfully"
}
```

**错误响应**:

- **400 Bad Request** - 无效的请求数据
- **401 Unauthorized** - 未认证
- **500 Internal Server Error** - 服务器错误

**示例请求**:
```bash
curl -X POST http://localhost:5000/api/cron/jobs \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "job-123",
    "name": "Daily Reminder",
    "enabled": true,
    "schedule": {
      "type": "cron",
      "cron": "0 9 * * *",
      "timezone": "UTC"
    },
    "task_type": "text",
    "text": "Good morning!",
    "dispatch": {
      "type": "channel",
      "channel": "console",
      "target": {
        "user_id": "test-user",
        "session_id": "test-session"
      },
      "mode": "final",
      "meta": {}
    },
    "runtime": {
      "max_concurrency": 1,
      "timeout_seconds": 120,
      "misfire_grace_seconds": 60
    },
    "meta": {}
  }'
```

---

#### 5.3 获取单个定时任务

**端点**: `GET /api/cron/jobs/:job_id`

**描述**: 获取指定定时任务的详情。

**认证**: 需要

**路径参数**:
- `job_id`: 任务 ID

**成功响应** (200 OK):
```json
{
  "success": true,
  "data": {
    "spec": {
      "id": "job-123",
      "name": "Daily Reminder",
      "enabled": true,
      "schedule": {
        "type": "cron",
        "cron": "0 9 * * *",
        "timezone": "UTC"
      },
      "task_type": "text",
      "text": "Good morning!",
      "dispatch": {
        "type": "channel",
        "channel": "console",
        "target": {
          "user_id": "test-user",
          "session_id": "test-session"
        },
        "mode": "final",
        "meta": {}
      },
      "runtime": {
        "max_concurrency": 1,
        "timeout_seconds": 120,
        "misfire_grace_seconds": 60
      },
      "meta": {}
    },
    "state": {
      "last_run_at": "2024-01-01T09:00:00Z",
      "next_run_at": "2024-01-02T09:00:00Z",
      "last_status": "success",
      "last_error": null
    }
  }
}
```

**错误响应**:

- **404 Not Found** - 任务不存在
- **401 Unauthorized** - 未认证
- **500 Internal Server Error** - 服务器错误

**示例请求**:
```bash
curl -X GET http://localhost:5000/api/cron/jobs/job-123 \
  -H "Authorization: Bearer <your_token>"
```

---

#### 5.4 更新定时任务

**端点**: `PUT /api/cron/jobs/:job_id`

**描述**: 更新指定的定时任务。

**认证**: 需要

**路径参数**:
- `job_id`: 任务 ID

**请求体**:
```json
{
  "id": "job-123",
  "name": "Updated Daily Reminder",
  "enabled": true,
  "schedule": {
    "type": "cron",
    "cron": "0 8 * * *",
    "timezone": "UTC"
  },
  "task_type": "text",
  "text": "Good morning! Have a nice day!",
  "dispatch": {
    "type": "channel",
    "channel": "console",
    "target": {
      "user_id": "test-user",
      "session_id": "test-session"
    },
    "mode": "final",
    "meta": {}
  },
  "runtime": {
    "max_concurrency": 1,
    "timeout_seconds": 120,
    "misfire_grace_seconds": 60
  },
  "meta": {}
}
```

**成功响应** (200 OK):
```json
{
  "success": true,
  "data": {
    "id": "job-123",
    "name": "Updated Daily Reminder",
    "enabled": true,
    "schedule": {
      "type": "cron",
      "cron": "0 8 * * *",
      "timezone": "UTC"
    },
    "task_type": "text",
    "text": "Good morning! Have a nice day!",
    "dispatch": {
      "type": "channel",
      "channel": "console",
      "target": {
        "user_id": "test-user",
        "session_id": "test-session"
      },
      "mode": "final",
      "meta": {}
    },
    "runtime": {
      "max_concurrency": 1,
      "timeout_seconds": 120,
      "misfire_grace_seconds": 60
    },
    "meta": {}
  },
  "message": "Cron job updated successfully"
}
```

**错误响应**:

- **400 Bad Request** - 无效的请求数据
- **404 Not Found** - 任务不存在
- **401 Unauthorized** - 未认证
- **500 Internal Server Error** - 服务器错误

**示例请求**:
```bash
curl -X PUT http://localhost:5000/api/cron/jobs/job-123 \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "job-123",
    "name": "Updated Daily Reminder",
    "enabled": true,
    "schedule": {
      "type": "cron",
      "cron": "0 8 * * *",
      "timezone": "UTC"
    },
    "task_type": "text",
    "text": "Good morning! Have a nice day!",
    "dispatch": {
      "type": "channel",
      "channel": "console",
      "target": {
        "user_id": "test-user",
        "session_id": "test-session"
      },
      "mode": "final",
      "meta": {}
    },
    "runtime": {
      "max_concurrency": 1,
      "timeout_seconds": 120,
      "misfire_grace_seconds": 60
    },
    "meta": {}
  }'
```

---

#### 5.5 删除定时任务

**端点**: `DELETE /api/cron/jobs/:job_id`

**描述**: 删除指定的定时任务。

**认证**: 需要

**路径参数**:
- `job_id`: 任务 ID

**成功响应** (200 OK):
```json
{
  "success": true,
  "message": "Cron job deleted successfully"
}
```

**错误响应**:

- **404 Not Found** - 任务不存在
- **401 Unauthorized** - 未认证
- **500 Internal Server Error** - 服务器错误

**示例请求**:
```bash
curl -X DELETE http://localhost:5000/api/cron/jobs/job-123 \
  -H "Authorization: Bearer <your_token>"
```

---

#### 5.6 暂停定时任务

**端点**: `POST /api/cron/jobs/:job_id/pause`

**描述**: 暂停指定的定时任务。

**认证**: 需要

**路径参数**:
- `job_id`: 任务 ID

**成功响应** (200 OK):
```json
{
  "success": true,
  "message": "Cron job paused successfully"
}
```

**错误响应**:

- **404 Not Found** - 任务不存在
- **401 Unauthorized** - 未认证
- **500 Internal Server Error** - 服务器错误

**示例请求**:
```bash
curl -X POST http://localhost:5000/api/cron/jobs/job-123/pause \
  -H "Authorization: Bearer <your_token>"
```

---

#### 5.7 恢复定时任务

**端点**: `POST /api/cron/jobs/:job_id/resume`

**描述**: 恢复指定的定时任务。

**认证**: 需要

**路径参数**:
- `job_id`: 任务 ID

**成功响应** (200 OK):
```json
{
  "success": true,
  "message": "Cron job resumed successfully"
}
```

**错误响应**:

- **404 Not Found** - 任务不存在
- **401 Unauthorized** - 未认证
- **500 Internal Server Error** - 服务器错误

**示例请求**:
```bash
curl -X POST http://localhost:5000/api/cron/jobs/job-123/resume \
  -H "Authorization: Bearer <your_token>"
```

---

#### 5.8 立即执行定时任务

**端点**: `POST /api/cron/jobs/:job_id/run`

**描述**: 立即执行指定的定时任务。

**认证**: 需要

**路径参数**:
- `job_id`: 任务 ID

**成功响应** (200 OK):
```json
{
  "success": true,
  "message": "Cron job started successfully"
}
```

**错误响应**:

- **404 Not Found** - 任务不存在
- **401 Unauthorized** - 未认证
- **500 Internal Server Error** - 服务器错误

**示例请求**:
```bash
curl -X POST http://localhost:5000/api/cron/jobs/job-123/run \
  -H "Authorization: Bearer <your_token>"
```

---

## 错误码说明

### 认证错误 (401)

| 错误码 | 描述 | 解决方法 |
|--------|------|----------|
| `AUTHENTICATION_ERROR` | 认证失败 | 检查令牌是否有效 |
| `INVALID_CREDENTIALS` | 密码错误 | 使用正确的管理员密码 |
| `INVALID_TOKEN` | 令牌无效 | 重新登录获取新令牌 |
| `TOKEN_EXPIRED` | 令牌已过期 | 重新登录获取新令牌 |

### 验证错误 (400)

| 错误码 | 描述 | 解决方法 |
|--------|------|----------|
| `VALIDATION_ERROR` | 验证失败 | 检查请求数据格式 |
| `MISSING_FIELD` | 缺少必需字段 | 提供所有必需字段 |
| `MISSING_PASSWORD` | 缺少密码 | 在请求体中提供密码 |
| `INVALID_PROVIDER` | 无效的提供商 | 使用 claude、gemini 或 openai |
| `INVALID_LAYER` | 无效的层级 | 使用 api 或 cli |
| `INVALID_JSON` | JSON 格式错误 | 检查 JSON 语法 |
| `INVALID_FORMAT` | 数据格式错误 | 检查数据结构 |
| `MISSING_FILE` | 未提供文件 | 在请求中包含文件 |
| `EMPTY_FILENAME` | 文件名为空 | 选择有效的文件 |
| `INVALID_ENCODING` | 文件编码错误 | 使用 UTF-8 编码 |
| `MISSING_CONFIGS` | 缺少 configs 字段 | 确保导入文件包含 configs 数组 |
| `INVALID_CONFIGS_FORMAT` | configs 格式错误 | configs 必须是数组 |
| `MISSING_REQUIRED_FIELDS` | 缺少必需字段 | 提供所有必需的配置字段 |
| `MISSING_CONFIG_FIELDS` | 缺少配置字段 | 提供所有配置字段 |
| `MISSING_METADATA_FIELDS` | 缺少元数据字段 | 提供所有元数据字段 |
| `INVALID_CLI_PROVIDER` | 无效的 CLI 提供商 | 使用有效的提供商值 |


### 资源不存在错误 (404)

| 错误码 | 描述 | 解决方法 |
|--------|------|----------|
| `NOT_FOUND` | 资源不存在 | 检查资源 ID 是否正确 |
| `CONFIG_NOT_FOUND` | 配置不存在 | 使用存在的 session_id |

### 服务器错误 (500)

| 错误码 | 描述 | 解决方法 |
|--------|------|----------|
| `INTERNAL_ERROR` | 服务器内部错误 | 查看服务器日志，联系管理员 |
| `FILE_ERROR` | 文件操作错误 | 检查文件权限和磁盘空间 |
| `DATABASE_ERROR` | 数据库错误 | 检查数据库连接和状态 |

---

## 数据模型

### SessionConfig 对象

```typescript
{
  session_id: string;           // 会话 ID（用户 ID 或群组 ID）
  session_type: "user" | "group";  // 会话类型
  config: {
    target_project_dir: string | null;      // 目标项目目录
    response_language: string | null;       // 响应语言
    default_provider: "claude" | "gemini" | "openai" | null;  // 默认提供商
    default_layer: "api" | "cli" | null;    // 默认层级
    default_cli_provider: "claude" | "gemini" | "openai" | null;  // 默认 CLI 提供商
  };
  metadata: {
    created_by: string;         // 创建者 ID
    created_at: string;         // 创建时间（ISO 8601 格式）
    updated_by: string;         // 更新者 ID
    updated_at: string;         // 更新时间（ISO 8601 格式）
    update_count: number;       // 更新次数
  };
}
```

### Token 对象

```typescript
{
  token: string;        // JWT 令牌
  expires_in: number;   // 过期时间（秒）
  expires_at: string;   // 过期时间戳（ISO 8601 格式）
}
```


---

## 使用示例

### 完整工作流程示例

#### 1. 登录获取令牌

```bash
# 登录
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"password": "your_password"}' \
  | jq -r '.data.token')

echo "Token: $TOKEN"
```

#### 2. 获取所有配置

```bash
# 获取配置列表
curl -X GET http://localhost:5000/api/configs \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'
```

#### 3. 创建或更新配置

```bash
# 创建新配置
curl -X PUT http://localhost:5000/api/configs/ou_new_user \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_type": "user",
    "target_project_dir": "/home/user/my-project",
    "response_language": "中文",
    "default_provider": "claude",
    "default_layer": "api"
  }' \
  | jq '.'
```

#### 4. 查看配置详情

```bash
# 获取配置详情
curl -X GET http://localhost:5000/api/configs/ou_new_user \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'

# 获取有效配置
curl -X GET http://localhost:5000/api/configs/ou_new_user/effective \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'
```

#### 5. 导出配置

```bash
# 导出所有配置
curl -X POST http://localhost:5000/api/configs/export \
  -H "Authorization: Bearer $TOKEN" \
  -o backup_$(date +%Y%m%d).json

echo "Configurations exported to backup_$(date +%Y%m%d).json"
```

#### 6. 导入配置

```bash
# 导入配置
curl -X POST http://localhost:5000/api/configs/import \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@backup_20240104.json" \
  | jq '.'
```

#### 7. 删除配置

```bash
# 删除配置
curl -X DELETE http://localhost:5000/api/configs/ou_new_user \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'
```

#### 8. 登出

```bash
# 登出
curl -X POST http://localhost:5000/api/auth/logout \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'
```


---

## Python 客户端示例

```python
import requests
import json

class WebAdminClient:
    """Web Admin API 客户端"""
    
    def __init__(self, base_url="http://localhost:5000", password=None):
        self.base_url = base_url
        self.password = password
        self.token = None
    
    def login(self):
        """登录获取令牌"""
        response = requests.post(
            f"{self.base_url}/api/auth/login",
            json={"password": self.password}
        )
        response.raise_for_status()
        data = response.json()
        self.token = data['data']['token']
        return self.token
    
    def _get_headers(self):
        """获取请求头"""
        if not self.token:
            self.login()
        return {"Authorization": f"Bearer {self.token}"}
    
    def get_configs(self, session_type=None, search=None):
        """获取配置列表"""
        params = {}
        if session_type:
            params['session_type'] = session_type
        if search:
            params['search'] = search
        
        response = requests.get(
            f"{self.base_url}/api/configs",
            headers=self._get_headers(),
            params=params
        )
        response.raise_for_status()
        return response.json()['data']
    
    def get_config(self, session_id):
        """获取单个配置"""
        response = requests.get(
            f"{self.base_url}/api/configs/{session_id}",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()['data']
    
    def update_config(self, session_id, config_data):
        """更新配置"""
        response = requests.put(
            f"{self.base_url}/api/configs/{session_id}",
            headers=self._get_headers(),
            json=config_data
        )
        response.raise_for_status()
        return response.json()['data']
    
    def delete_config(self, session_id):
        """删除配置"""
        response = requests.delete(
            f"{self.base_url}/api/configs/{session_id}",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    def export_configs(self, output_file):
        """导出配置"""
        response = requests.post(
            f"{self.base_url}/api/configs/export",
            headers=self._get_headers()
        )
        response.raise_for_status()
        
        with open(output_file, 'wb') as f:
            f.write(response.content)
        return output_file
    
    def import_configs(self, input_file):
        """导入配置"""
        with open(input_file, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{self.base_url}/api/configs/import",
                headers=self._get_headers(),
                files=files
            )
        response.raise_for_status()
        return response.json()['data']
    
    def logout(self):
        """登出"""
        response = requests.post(
            f"{self.base_url}/api/auth/logout",
            headers=self._get_headers()
        )
        response.raise_for_status()
        self.token = None
        return response.json()


# 使用示例
if __name__ == "__main__":
    # 创建客户端
    client = WebAdminClient(password="your_password")
    
    # 登录
    client.login()
    print("Logged in successfully")
    
    # 获取所有配置
    configs = client.get_configs()
    print(f"Found {len(configs)} configurations")
    
    # 创建新配置
    new_config = client.update_config(
        session_id="ou_test_user",
        config_data={
            "session_type": "user",
            "target_project_dir": "/home/user/project",
            "default_provider": "claude"
        }
    )
    print(f"Created config: {new_config['session_id']}")
    
    # 导出配置
    client.export_configs("backup.json")
    print("Configurations exported")
    
    # 登出
    client.logout()
    print("Logged out")
```


---

## JavaScript/TypeScript 客户端示例

```typescript
// web-admin-client.ts
import axios, { AxiosInstance } from 'axios';

interface LoginResponse {
  token: string;
  expires_in: number;
  expires_at: string;
}

interface SessionConfig {
  session_id: string;
  session_type: 'user' | 'group';
  config: {
    target_project_dir: string | null;
    response_language: string | null;
    default_provider: 'claude' | 'gemini' | 'openai' | null;
    default_layer: 'api' | 'cli' | null;
    default_cli_provider: 'claude' | 'gemini' | 'openai' | null;
  };
  metadata: {
    created_by: string;
    created_at: string;
    updated_by: string;
    updated_at: string;
    update_count: number;
  };
}

class WebAdminClient {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor(baseURL: string = 'http://localhost:5000', private password?: string) {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 请求拦截器：自动添加令牌
    this.client.interceptors.request.use((config) => {
      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`;
      }
      return config;
    });

    // 响应拦截器：处理错误
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          this.token = null;
          throw new Error('Authentication failed. Please login again.');
        }
        throw error;
      }
    );
  }

  async login(): Promise<string> {
    const response = await this.client.post<{ data: LoginResponse }>('/api/auth/login', {
      password: this.password,
    });
    this.token = response.data.data.token;
    return this.token;
  }

  async logout(): Promise<void> {
    await this.client.post('/api/auth/logout');
    this.token = null;
  }

  async getConfigs(params?: {
    session_type?: 'user' | 'group';
    search?: string;
    sort?: string;
    order?: 'asc' | 'desc';
  }): Promise<SessionConfig[]> {
    const response = await this.client.get<{ data: SessionConfig[] }>('/api/configs', {
      params,
    });
    return response.data.data;
  }

  async getConfig(sessionId: string): Promise<SessionConfig> {
    const response = await this.client.get<{ data: SessionConfig }>(
      `/api/configs/${sessionId}`
    );
    return response.data.data;
  }

  async getEffectiveConfig(sessionId: string): Promise<any> {
    const response = await this.client.get(`/api/configs/${sessionId}/effective`);
    return response.data.data.effective_config;
  }

  async getGlobalConfig(): Promise<any> {
    const response = await this.client.get('/api/configs/global');
    return response.data.data.global_config;
  }

  async updateConfig(
    sessionId: string,
    configData: Partial<SessionConfig['config']> & { session_type?: 'user' | 'group' }
  ): Promise<SessionConfig> {
    const response = await this.client.put<{ data: SessionConfig }>(
      `/api/configs/${sessionId}`,
      configData
    );
    return response.data.data;
  }

  async deleteConfig(sessionId: string): Promise<void> {
    await this.client.delete(`/api/configs/${sessionId}`);
  }

  async exportConfigs(): Promise<Blob> {
    const response = await this.client.post('/api/configs/export', null, {
      responseType: 'blob',
    });
    return response.data;
  }

  async importConfigs(file: File): Promise<{ imported_count: number }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post<{ data: { imported_count: number } }>(
      '/api/configs/import',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data.data;
  }
}

// 使用示例
async function example() {
  const client = new WebAdminClient('http://localhost:5000', 'your_password');

  try {
    // 登录
    await client.login();
    console.log('Logged in successfully');

    // 获取所有配置
    const configs = await client.getConfigs();
    console.log(`Found ${configs.length} configurations`);

    // 创建新配置
    const newConfig = await client.updateConfig('ou_test_user', {
      session_type: 'user',
      target_project_dir: '/home/user/project',
      default_provider: 'claude',
    });
    console.log('Created config:', newConfig.session_id);

    // 导出配置
    const blob = await client.exportConfigs();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'configs_backup.json';
    a.click();
    console.log('Configurations exported');

    // 登出
    await client.logout();
    console.log('Logged out');
  } catch (error) {
    console.error('Error:', error);
  }
}
```


---

## 安全最佳实践

### 1. 令牌管理

- **存储**: 将令牌存储在安全的位置（如 localStorage 或 sessionStorage）
- **传输**: 始终使用 HTTPS 传输令牌
- **过期**: 令牌过期后需要重新登录
- **清除**: 登出时清除本地存储的令牌

### 2. 密码安全

- 使用强密码（至少 12 个字符，包含大小写字母、数字、特殊字符）
- 通过环境变量配置密码，不要硬编码
- 定期更换管理员密码

### 3. HTTPS

- 生产环境必须使用 HTTPS
- 使用有效的 SSL/TLS 证书
- 配置 HSTS（HTTP Strict Transport Security）

### 4. 访问控制

- 限制管理界面的访问 IP（如果可能）
- 使用防火墙规则保护服务器
- 定期审查访问日志

### 5. 错误处理

- 不要在错误消息中暴露敏感信息
- 记录详细的错误日志用于调试
- 向用户显示友好的错误消息

---

## 速率限制

当前版本暂未实现速率限制。建议在生产环境中配置以下限制：

- **登录接口**: 每 IP 每分钟最多 5 次尝试
- **API 接口**: 每令牌每分钟最多 60 次请求

可以使用 Nginx 或其他反向代理实现速率限制。

---

## 版本历史

### v1.0.0 (2024-01-04)

- 初始版本发布
- 实现认证 API（登录、登出）
- 实现配置查询 API（列表、详情、有效配置、全局配置）
- 实现配置修改 API（更新、删除）
- 实现导出导入 API
- 统一错误处理和响应格式

---

## 常见问题

### Q: 令牌过期后如何处理？

A: 令牌过期后，API 会返回 401 状态码。客户端应该捕获这个错误，清除本地令牌，并引导用户重新登录。

### Q: 如何批量更新多个配置？

A: 目前没有批量更新的专用接口。可以使用导出-修改-导入的方式：
1. 导出所有配置
2. 修改 JSON 文件
3. 导入修改后的配置

### Q: 删除配置后能恢复吗？

A: 删除配置是永久性的。建议在删除前先导出配置作为备份。导入操作会自动创建备份。

### Q: 如何查看某个会话的实际使用配置？

A: 使用 `/api/configs/:session_id/effective` 端点获取有效配置，该配置已应用优先级规则（会话配置优先于全局配置）。

### Q: 支持哪些 provider 和 layer 值？

A: 
- Provider: `claude`、`gemini`、`openai`
- Layer: `api`、`cli`

### Q: 如何处理网络错误？

A: 客户端应该实现重试机制和错误提示。对于网络错误，可以自动重试 1-2 次。对于 5xx 错误，建议不要自动重试。

---

## 技术支持

如有问题或建议，请联系：

- 项目仓库: [GitHub Repository]
- 文档: [Documentation]
- 问题反馈: [Issue Tracker]

---

**文档版本**: 1.0.0  
**最后更新**: 2024-01-04  
**维护者**: XAgent Team
