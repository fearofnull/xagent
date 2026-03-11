# Cron API 文档

## 概述

Cron API 提供了完整的定时任务管理功能，支持创建、查询、更新、删除、暂停、恢复和立即执行定时任务。

## 基础信息

- **Base URL**: `/api/cron`
- **认证方式**: JWT Token (通过 `Authorization: Bearer <token>` 头部传递)
- **Content-Type**: `application/json`

## API 端点

### 1. 列出所有任务

获取所有定时任务列表。

**请求**:
```http
GET /api/cron/jobs
Authorization: Bearer <token>
```

**响应**:
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
        "channel": "feishu",
        "target": {
          "user_id": "user123",
          "session_id": "session456"
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

---

### 2. 创建任务

创建一个新的定时任务。

**请求**:
```http
POST /api/cron/jobs
Authorization: Bearer <token>
Content-Type: application/json

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
    "channel": "feishu",
    "target": {
      "user_id": "user123",
      "session_id": "session456"
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

**响应**:
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
      "channel": "feishu",
      "target": {
        "user_id": "user123",
        "session_id": "session456"
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
}
```

---

### 3. 获取任务详情

获取指定任务的详细信息和状态。

**请求**:
```http
GET /api/cron/jobs/{job_id}
Authorization: Bearer <token>
```

**响应**:
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
        "channel": "feishu",
        "target": {
          "user_id": "user123",
          "session_id": "session456"
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
      "last_run_at": "2024-01-01T12:00:00Z",
      "next_run_at": "2024-01-02T09:00:00Z",
      "last_status": "success",
      "last_error": null
    }
  }
}
```

---

### 4. 更新任务

更新现有任务的配置。

**请求**:
```http
PUT /api/cron/jobs/{job_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "id": "job-123",
  "name": "Daily Reminder Updated",
  "enabled": true,
  "schedule": {
    "type": "cron",
    "cron": "0 10 * * *",
    "timezone": "UTC"
  },
  "task_type": "text",
  "text": "Good morning! Updated",
  "dispatch": {
    "type": "channel",
    "channel": "feishu",
    "target": {
      "user_id": "user123",
      "session_id": "session456"
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

**响应**:
```json
{
  "success": true,
  "data": {
    "id": "job-123",
    "name": "Daily Reminder Updated",
    "enabled": true,
    "schedule": {
      "type": "cron",
      "cron": "0 10 * * *",
      "timezone": "UTC"
    },
    "task_type": "text",
    "text": "Good morning! Updated",
    "dispatch": {
      "type": "channel",
      "channel": "feishu",
      "target": {
        "user_id": "user123",
        "session_id": "session456"
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
}
```

---

### 5. 删除任务

删除指定的定时任务。

**请求**:
```http
DELETE /api/cron/jobs/{job_id}
Authorization: Bearer <token>
```

**响应**:
```json
{
  "success": true,
  "message": "Job deleted successfully"
}
```

---

### 6. 暂停任务

暂停指定任务的执行。

**请求**:
```http
POST /api/cron/jobs/{job_id}/pause
Authorization: Bearer <token>
```

**响应**:
```json
{
  "success": true,
  "message": "Job paused successfully"
}
```

---

### 7. 恢复任务

恢复已暂停任务的执行。

**请求**:
```http
POST /api/cron/jobs/{job_id}/resume
Authorization: Bearer <token>
```

**响应**:
```json
{
  "success": true,
  "message": "Job resumed successfully"
}
```

---

### 8. 立即执行任务

立即执行指定任务（不等待下次调度时间）。

**请求**:
```http
POST /api/cron/jobs/{job_id}/run
Authorization: Bearer <token>
```

**响应**:
```json
{
  "success": true,
  "message": "Job started successfully"
}
```

---

## 数据模型

### CronJobSpec

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| id | string | 是 | 任务唯一标识符 |
| name | string | 是 | 任务名称 |
| enabled | boolean | 否 | 是否启用（默认: true） |
| schedule | CronJobSchedule | 是 | 调度配置 |
| task_type | string | 是 | 任务类型（"text" 或 "agent"） |
| text | string | 条件 | 文本内容（task_type="text"时必需） |
| request | CronJobRequest | 条件 | AI请求（task_type="agent"时必需） |
| dispatch | CronJobDispatch | 是 | 分发配置 |
| runtime | CronJobRuntime | 否 | 运行时配置 |
| meta | object | 否 | 元数据 |

### CronJobSchedule

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| type | string | 是 | 调度类型（固定为"cron"） |
| cron | string | 是 | Cron表达式（5字段格式） |
| timezone | string | 否 | 时区（默认: "UTC"） |

### CronJobDispatch

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| type | string | 是 | 分发类型（固定为"channel"） |
| channel | string | 是 | 频道名称（"feishu", "console"等） |
| target | CronJobTarget | 是 | 目标配置 |
| mode | string | 否 | 发送模式（默认: "final"） |
| meta | object | 否 | 元数据 |

### CronJobTarget

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| user_id | string | 否 | 用户ID |
| session_id | string | 否 | 会话ID |

### CronJobRuntime

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| max_concurrency | integer | 否 | 最大并发数（默认: 1） |
| timeout_seconds | integer | 否 | 超时时间（默认: 120） |
| misfire_grace_seconds | integer | 否 | 错过执行宽限期（默认: 60） |

### CronJobState

| 字段 | 类型 | 描述 |
|------|------|------|
| last_run_at | datetime | 上次运行时间 |
| next_run_at | datetime | 下次运行时间 |
| last_status | string | 上次状态（"running", "success", "error"） |
| last_error | string | 上次错误信息 |

---

## Cron 表达式格式

Cron表达式使用5字段格式（不包含秒）：

```
分钟 小时 日期 月份 星期
```

### 字段说明

| 字段 | 允许值 | 特殊字符 |
|------|--------|----------|
| 分钟 | 0-59 | * , - / |
| 小时 | 0-23 | * , - / |
| 日期 | 1-31 | * , - / |
| 月份 | 1-12 | * , - / |
| 星期 | 0-6 (0=周日) | * , - / |

### 特殊字符

- `*` - 所有值
- `,` - 值列表分隔符
- `-` - 值范围
- `/` - 步长值

### 常用示例

| 表达式 | 描述 |
|--------|------|
| `0 9 * * *` | 每天 9:00 |
| `0 */2 * * *` | 每 2 小时 |
| `30 8 * * 1-5` | 工作日 8:30 |
| `0 0 * * 0` | 每周日零点 |
| `*/15 * * * *` | 每 15 分钟 |
| `0 12 1 * *` | 每月1日中午12点 |
| `0 0 1 1 *` | 每年1月1日零点 |

---

## 错误码

| 错误码 | HTTP状态码 | 描述 |
|--------|-----------|------|
| VALIDATION_ERROR | 400 | 请求参数验证失败 |
| INVALID_CRON | 400 | 无效的Cron表达式 |
| BAD_REQUEST | 400 | 请求格式错误 |
| NOT_FOUND | 404 | 任务不存在 |
| PERMISSION_DENIED | 403 | 权限不足 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |

### 错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid cron expression: 0 9 * *"
  }
}
```

---

## 使用示例

### Python 示例

```python
import requests

# API基础URL
BASE_URL = "http://localhost:8080/api/cron"
TOKEN = "your_jwt_token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# 创建任务
job_data = {
    "id": "daily-reminder-001",
    "name": "Daily Morning Reminder",
    "enabled": True,
    "schedule": {
        "type": "cron",
        "cron": "0 9 * * *",
        "timezone": "UTC"
    },
    "task_type": "text",
    "text": "Good morning! Time to start your day!",
    "dispatch": {
        "type": "channel",
        "channel": "feishu",
        "target": {
            "user_id": "user123",
            "session_id": "session456"
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

response = requests.post(f"{BASE_URL}/jobs", json=job_data, headers=headers)
print(response.json())

# 列出所有任务
response = requests.get(f"{BASE_URL}/jobs", headers=headers)
print(response.json())

# 获取任务详情
response = requests.get(f"{BASE_URL}/jobs/daily-reminder-001", headers=headers)
print(response.json())

# 暂停任务
response = requests.post(f"{BASE_URL}/jobs/daily-reminder-001/pause", headers=headers)
print(response.json())

# 恢复任务
response = requests.post(f"{BASE_URL}/jobs/daily-reminder-001/resume", headers=headers)
print(response.json())

# 立即执行任务
response = requests.post(f"{BASE_URL}/jobs/daily-reminder-001/run", headers=headers)
print(response.json())

# 删除任务
response = requests.delete(f"{BASE_URL}/jobs/daily-reminder-001", headers=headers)
print(response.json())
```

### cURL 示例

```bash
# 获取JWT Token（假设已有登录接口）
TOKEN="your_jwt_token"

# 创建任务
curl -X POST http://localhost:8080/api/cron/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "daily-reminder-001",
    "name": "Daily Morning Reminder",
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
      "channel": "feishu",
      "target": {
        "user_id": "user123",
        "session_id": "session456"
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

# 列出所有任务
curl -X GET http://localhost:8080/api/cron/jobs \
  -H "Authorization: Bearer $TOKEN"

# 获取任务详情
curl -X GET http://localhost:8080/api/cron/jobs/daily-reminder-001 \
  -H "Authorization: Bearer $TOKEN"

# 暂停任务
curl -X POST http://localhost:8080/api/cron/jobs/daily-reminder-001/pause \
  -H "Authorization: Bearer $TOKEN"

# 恢复任务
curl -X POST http://localhost:8080/api/cron/jobs/daily-reminder-001/resume \
  -H "Authorization: Bearer $TOKEN"

# 立即执行任务
curl -X POST http://localhost:8080/api/cron/jobs/daily-reminder-001/run \
  -H "Authorization: Bearer $TOKEN"

# 删除任务
curl -X DELETE http://localhost:8080/api/cron/jobs/daily-reminder-001 \
  -H "Authorization: Bearer $TOKEN"
```

---

## 最佳实践

1. **任务ID命名**: 使用有意义的ID，建议格式：`{type}-{purpose}-{timestamp}`
2. **Cron表达式**: 使用在线工具（如 crontab.guru）验证表达式
3. **时区设置**: 明确指定时区，避免时区混淆
4. **错误处理**: 始终检查API响应的`success`字段
5. **任务监控**: 定期检查任务状态，处理失败的任务
6. **并发控制**: 根据任务特性设置合适的`max_concurrency`
7. **超时设置**: 根据任务复杂度设置合理的`timeout_seconds`
8. **权限管理**: 确保只有授权用户可以管理任务

---

## 常见问题

### Q: 如何设置每天特定时间执行的任务？
A: 使用cron表达式 `0 HH * * *`，其中HH是小时（0-23）。例如每天9点：`0 9 * * *`

### Q: 任务执行失败后会自动重试吗？
A: 不会自动重试。需要手动调用 `/api/cron/jobs/{job_id}/run` 重新执行。

### Q: 如何查看任务执行历史？
A: 通过 `/api/cron/jobs/{job_id}` 获取任务状态，包含上次执行时间、状态和错误信息。

### Q: 可以同时运行多个相同任务吗？
A: 由`runtime.max_concurrency`控制。默认为1，表示同一时间只能运行一个实例。

### Q: 错过的任务会补执行吗？
A: 在`misfire_grace_seconds`宽限期内的任务会立即执行，超过宽限期的任务会被跳过。

### Q: 如何修改任务的执行时间？
A: 使用PUT `/api/cron/jobs/{job_id}` 更新任务的`schedule.cron`字段。

---

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 支持基本的CRUD操作
- 支持任务暂停/恢复
- 支持立即执行任务
- 支持文本和AI任务类型
