# Cron 使用示例

本文档提供了定时任务功能的实际使用示例。

## 目录

1. [CLI 工具使用](#cli-工具使用)
2. [文本任务示例](#文本任务示例)
3. [AI任务示例](#ai任务示例)
4. [常见场景](#常见场景)
5. [通过AI Agent创建任务](#通过ai-agent创建任务)

---

## CLI 工具使用

### 基本命令

```bash
# 查看帮助
python -m src.xagent.cli.cron_cli --help

# 列出所有任务
python -m src.xagent.cli.cron_cli list

# 查看任务详情
python -m src.xagent.cli.cron_cli get <job_id>

# 查看任务状态
python -m src.xagent.cli.cron_cli state <job_id>

# 删除任务
python -m src.xagent.cli.cron_cli delete <job_id>

# 暂停任务
python -m src.xagent.cli.cron_cli pause <job_id>

# 恢复任务
python -m src.xagent.cli.cron_cli resume <job_id>

# 立即执行任务
python -m src.xagent.cli.cron_cli run <job_id>
```

### 创建任务

#### 方式1：命令行参数

```bash
python -m src.xagent.cli.cron_cli create \
  --type text \
  --name "每日早安" \
  --cron "0 9 * * *" \
  --channel feishu \
  --target-user "ou_xxxxxxxxxxxxx" \
  --target-session "om_xxxxxxxxxxxxx" \
  --text "早上好！"
```

#### 方式2：JSON 文件

```bash
python -m src.xagent.cli.cron_cli create -f docs/cron_job_example.json
```

JSON 文件示例（`docs/cron_job_example.json`）：
```json
{
  "id": "daily-morning-greeting",
  "name": "每日早安问候",
  "enabled": true,
  "schedule": {
    "type": "cron",
    "cron": "0 9 * * *",
    "timezone": "Asia/Shanghai"
  },
  "task_type": "text",
  "text": "早上好！新的一天开始了，祝你今天工作顺利！",
  "dispatch": {
    "type": "channel",
    "channel": "feishu",
    "target": {
      "user_id": "ou_xxxxxxxxxxxxx",
      "session_id": "om_xxxxxxxxxxxxx"
    },
    "mode": "final",
    "meta": {}
  },
  "runtime": {
    "max_concurrency": 1,
    "timeout_seconds": 120,
    "misfire_grace_seconds": 60
  },
  "meta": {
    "created_by": "admin",
    "description": "每天早上9点发送问候消息"
  }
}
```

### 常用 Cron 表达式

```bash
# 每天 9:00
--cron "0 9 * * *"

# 每 2 小时
--cron "0 */2 * * *"

# 工作日 8:30
--cron "30 8 * * 1-5"

# 每周日零点
--cron "0 0 * * 0"

# 每 15 分钟
--cron "*/15 * * * *"

# 每月1号中午12点
--cron "0 12 1 * *"
```

---

## 文本任务示例

### 示例1: 每日早晨提醒

创建一个每天早上9点发送提醒的任务。

```python
import requests

BASE_URL = "http://localhost:8080/api/cron"
TOKEN = "your_jwt_token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

job_data = {
    "id": "morning-reminder",
    "name": "Morning Reminder",
    "enabled": True,
    "schedule": {
        "type": "cron",
        "cron": "0 9 * * *",  # 每天9:00
        "timezone": "UTC"
    },
    "task_type": "text",
    "text": "早上好！新的一天开始了，加油！💪",
    "dispatch": {
        "type": "channel",
        "channel": "feishu",
        "target": {
            "user_id": "your_user_id",
            "session_id": "your_session_id"
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
```

### 示例2: 工作日下班提醒

创建一个工作日下午6点的下班提醒。

```python
job_data = {
    "id": "workday-end-reminder",
    "name": "Workday End Reminder",
    "enabled": True,
    "schedule": {
        "type": "cron",
        "cron": "0 18 * * 1-5",  # 周一到周五18:00
        "timezone": "UTC"
    },
    "task_type": "text",
    "text": "下班时间到了！记得整理今天的工作，准备明天的计划。",
    "dispatch": {
        "type": "channel",
        "channel": "feishu",
        "target": {
            "user_id": "your_user_id",
            "session_id": "your_session_id"
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
```

### 示例3: 每小时健康提醒

创建一个每小时提醒休息的任务。

```python
job_data = {
    "id": "hourly-health-reminder",
    "name": "Hourly Health Reminder",
    "enabled": True,
    "schedule": {
        "type": "cron",
        "cron": "0 * * * *",  # 每小时整点
        "timezone": "UTC"
    },
    "task_type": "text",
    "text": "该休息一下了！站起来活动活动，喝杯水，保护眼睛。👀💧",
    "dispatch": {
        "type": "channel",
        "channel": "feishu",
        "target": {
            "user_id": "your_user_id",
            "session_id": "your_session_id"
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
```

---

## AI任务示例

### 示例4: 每日天气播报

创建一个每天早上8点查询天气的AI任务。

```python
job_data = {
    "id": "daily-weather-report",
    "name": "Daily Weather Report",
    "enabled": True,
    "schedule": {
        "type": "cron",
        "cron": "0 8 * * *",  # 每天8:00
        "timezone": "UTC"
    },
    "task_type": "agent",
    "request": {
        "input": [
            {
                "role": "user",
                "type": "text",
                "content": [
                    {
                        "type": "text",
                        "text": "请查询今天的天气情况，并给出穿衣建议。"
                    }
                ]
            }
        ],
        "session_id": "weather-session",
        "user_id": "cron"
    },
    "dispatch": {
        "type": "channel",
        "channel": "feishu",
        "target": {
            "user_id": "your_user_id",
            "session_id": "your_session_id"
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
```

### 示例5: 每周工作总结

创建一个每周五下午5点生成工作总结的AI任务。

```python
job_data = {
    "id": "weekly-work-summary",
    "name": "Weekly Work Summary",
    "enabled": True,
    "schedule": {
        "type": "cron",
        "cron": "0 17 * * 5",  # 每周五17:00
        "timezone": "UTC"
    },
    "task_type": "agent",
    "request": {
        "input": [
            {
                "role": "user",
                "type": "text",
                "content": [
                    {
                        "type": "text",
                        "text": "请帮我总结本周的工作内容，包括完成的任务、遇到的问题和下周计划。"
                    }
                ]
            }
        ],
        "session_id": "summary-session",
        "user_id": "cron"
    },
    "dispatch": {
        "type": "channel",
        "channel": "feishu",
        "target": {
            "user_id": "your_user_id",
            "session_id": "your_session_id"
        },
        "mode": "final",
        "meta": {}
    },
    "runtime": {
        "max_concurrency": 1,
        "timeout_seconds": 180,  # AI任务可能需要更长时间
        "misfire_grace_seconds": 60
    },
    "meta": {}
}

response = requests.post(f"{BASE_URL}/jobs", json=job_data, headers=headers)
print(response.json())
```

---

## 常见场景

### 场景1: 会议提醒系统

创建多个会议提醒任务。

```python
# 每周一上午10点的周会提醒
weekly_meeting = {
    "id": "weekly-meeting-reminder",
    "name": "Weekly Meeting Reminder",
    "enabled": True,
    "schedule": {
        "type": "cron",
        "cron": "0 10 * * 1",  # 每周一10:00
        "timezone": "UTC"
    },
    "task_type": "text",
    "text": "⏰ 周会提醒：10:30 在会议室A有团队周会，请准时参加！",
    "dispatch": {
        "type": "channel",
        "channel": "feishu",
        "target": {
            "user_id": "your_user_id",
            "session_id": "your_session_id"
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

# 每天下午3点的站会提醒
daily_standup = {
    "id": "daily-standup-reminder",
    "name": "Daily Standup Reminder",
    "enabled": True,
    "schedule": {
        "type": "cron",
        "cron": "0 15 * * 1-5",  # 工作日15:00
        "timezone": "UTC"
    },
    "task_type": "text",
    "text": "⏰ 站会提醒：15:15 有每日站会，请准备好今天的进展和遇到的问题！",
    "dispatch": {
        "type": "channel",
        "channel": "feishu",
        "target": {
            "user_id": "your_user_id",
            "session_id": "your_session_id"
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

# 批量创建
for job in [weekly_meeting, daily_standup]:
    response = requests.post(f"{BASE_URL}/jobs", json=job, headers=headers)
    print(f"Created: {job['name']}")
    print(response.json())
```

### 场景2: 健康管理系统

创建一系列健康提醒任务。

```python
health_reminders = [
    {
        "id": "morning-water-reminder",
        "name": "Morning Water Reminder",
        "cron": "0 9 * * *",
        "text": "💧 早上好！记得喝一杯温水，开启健康的一天！"
    },
    {
        "id": "lunch-reminder",
        "name": "Lunch Reminder",
        "cron": "0 12 * * *",
        "text": "🍱 午餐时间到了！记得按时吃饭，营养均衡很重要！"
    },
    {
        "id": "afternoon-exercise-reminder",
        "name": "Afternoon Exercise Reminder",
        "cron": "0 16 * * *",
        "text": "🏃 下午茶时间！站起来活动一下，做做伸展运动！"
    },
    {
        "id": "evening-sleep-reminder",
        "name": "Evening Sleep Reminder",
        "cron": "0 22 * * *",
        "text": "😴 该准备睡觉了！早睡早起身体好，明天又是元气满满的一天！"
    }
]

for reminder in health_reminders:
    job_data = {
        "id": reminder["id"],
        "name": reminder["name"],
        "enabled": True,
        "schedule": {
            "type": "cron",
            "cron": reminder["cron"],
            "timezone": "UTC"
        },
        "task_type": "text",
        "text": reminder["text"],
        "dispatch": {
            "type": "channel",
            "channel": "feishu",
            "target": {
                "user_id": "your_user_id",
                "session_id": "your_session_id"
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
    print(f"Created: {reminder['name']}")
```

### 场景3: 数据备份任务

创建定期数据备份提醒。

```python
backup_jobs = [
    {
        "id": "daily-backup-reminder",
        "name": "Daily Backup Reminder",
        "cron": "0 23 * * *",  # 每天23:00
        "text": "💾 每日备份提醒：请确保今天的工作已保存并备份！"
    },
    {
        "id": "weekly-full-backup",
        "name": "Weekly Full Backup",
        "cron": "0 2 * * 0",  # 每周日凌晨2:00
        "text": "💾 每周完整备份提醒：系统将在凌晨2点执行完整备份，请确保服务器正常运行。"
    },
    {
        "id": "monthly-archive",
        "name": "Monthly Archive",
        "cron": "0 3 1 * *",  # 每月1日凌晨3:00
        "text": "📦 月度归档提醒：上个月的数据将被归档，请检查归档策略。"
    }
]

for job in backup_jobs:
    job_data = {
        "id": job["id"],
        "name": job["name"],
        "enabled": True,
        "schedule": {
            "type": "cron",
            "cron": job["cron"],
            "timezone": "UTC"
        },
        "task_type": "text",
        "text": job["text"],
        "dispatch": {
            "type": "channel",
            "channel": "feishu",
            "target": {
                "user_id": "your_user_id",
                "session_id": "your_session_id"
            },
            "mode": "final",
            "meta": {}
        },
        "runtime": {
            "max_concurrency": 1,
            "timeout_seconds": 120,
            "misfire_grace_seconds": 300  # 备份任务允许更长的宽限期
        },
        "meta": {}
    }
    
    response = requests.post(f"{BASE_URL}/jobs", json=job_data, headers=headers)
    print(f"Created: {job['name']}")
```

---

## 通过AI Agent创建任务

当cron skill被加载后，可以通过自然语言与AI Agent交互来创建和管理定时任务。

### 示例对话1: 创建简单提醒

**用户**: "帮我创建一个每天早上9点的提醒，内容是'该起床了！'"

**AI Agent**: 
```
好的，我来帮你创建这个定时任务。

任务详情：
- 名称：Morning Wake Up Reminder
- 时间：每天 9:00 AM (UTC)
- 类型：文本消息
- 内容：该起床了！

任务已创建成功！任务ID: text-1234567890-abc123
下次执行时间：明天 09:00:00 UTC
```

### 示例对话2: 创建工作日提醒

**用户**: "我想在每个工作日下午6点收到下班提醒"

**AI Agent**:
```
明白了，我来创建一个工作日下班提醒。

任务详情：
- 名称：Workday End Reminder
- 时间：周一至周五 18:00 (UTC)
- 类型：文本消息
- 内容：下班时间到了！

任务已创建成功！任务ID: text-1234567891-def456
下次执行时间：[下个工作日] 18:00:00 UTC
```

### 示例对话3: 查看所有任务

**用户**: "列出我的所有定时任务"

**AI Agent**:
```
您当前有以下定时任务：

1. Morning Wake Up Reminder
   - ID: text-1234567890-abc123
   - 状态：启用
   - 时间：每天 9:00
   - 下次执行：明天 09:00:00 UTC

2. Workday End Reminder
   - ID: text-1234567891-def456
   - 状态：启用
   - 时间：工作日 18:00
   - 下次执行：今天 18:00:00 UTC

3. Weekly Meeting Reminder
   - ID: weekly-meeting-reminder
   - 状态：启用
   - 时间：每周一 10:00
   - 下次执行：下周一 10:00:00 UTC
```

### 示例对话4: 暂停任务

**用户**: "暂停早上的起床提醒"

**AI Agent**:
```
好的，我来暂停"Morning Wake Up Reminder"任务。

任务已暂停！
- 任务ID: text-1234567890-abc123
- 任务名称：Morning Wake Up Reminder

该任务将不再自动执行，直到您恢复它。
```

### 示例对话5: 修改任务时间

**用户**: "把起床提醒改到早上8点"

**AI Agent**:
```
好的，我来修改"Morning Wake Up Reminder"的执行时间。

修改内容：
- 原时间：每天 9:00
- 新时间：每天 8:00

任务已更新成功！
下次执行时间：明天 08:00:00 UTC
```

---

## 任务管理最佳实践

### 1. 任务命名规范

使用清晰、描述性的名称：
- ✅ 好的命名：`Daily Morning Reminder`, `Weekly Team Meeting`, `Monthly Report Generation`
- ❌ 不好的命名：`Task1`, `Job`, `Test`

### 2. 时区管理

明确指定时区，避免混淆：
```python
# 使用UTC时区（推荐）
"timezone": "UTC"

# 或使用本地时区
"timezone": "Asia/Shanghai"
```

### 3. 超时设置

根据任务复杂度设置合理的超时时间：
- 简单文本消息：60-120秒
- AI任务：120-300秒
- 复杂数据处理：300-600秒

### 4. 错误处理

定期检查任务状态，处理失败的任务：
```python
# 获取任务状态
response = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=headers)
job_data = response.json()['data']

if job_data['state']['last_status'] == 'error':
    print(f"任务执行失败：{job_data['state']['last_error']}")
    # 立即重试
    requests.post(f"{BASE_URL}/jobs/{job_id}/run", headers=headers)
```

### 5. 任务监控

创建一个监控脚本，定期检查所有任务的健康状态：
```python
def monitor_cron_jobs():
    response = requests.get(f"{BASE_URL}/jobs", headers=headers)
    jobs = response.json()['data']
    
    for job in jobs:
        job_id = job['id']
        detail_response = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=headers)
        job_detail = detail_response.json()['data']
        
        state = job_detail['state']
        if state['last_status'] == 'error':
            print(f"⚠️ 任务 {job['name']} 执行失败")
            print(f"   错误信息：{state['last_error']}")
        elif not job['enabled']:
            print(f"⏸️ 任务 {job['name']} 已暂停")
        else:
            print(f"✅ 任务 {job['name']} 运行正常")

# 每小时运行一次监控
monitor_cron_jobs()
```

---

## 故障排查

### 问题1: 任务没有按时执行

**可能原因**:
1. 任务被暂停
2. Cron表达式错误
3. 系统时间不正确

**解决方法**:
```python
# 检查任务状态
response = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=headers)
job = response.json()['data']

print(f"任务启用状态：{job['spec']['enabled']}")
print(f"Cron表达式：{job['spec']['schedule']['cron']}")
print(f"下次执行时间：{job['state']['next_run_at']}")
```

### 问题2: 任务执行失败

**可能原因**:
1. 超时
2. 网络问题
3. 权限不足

**解决方法**:
```python
# 查看错误信息
response = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=headers)
state = response.json()['data']['state']

if state['last_status'] == 'error':
    print(f"错误信息：{state['last_error']}")
    
    # 增加超时时间
    job = response.json()['data']['spec']
    job['runtime']['timeout_seconds'] = 300
    
    # 更新任务
    requests.put(f"{BASE_URL}/jobs/{job_id}", json=job, headers=headers)
```

### 问题3: 任务重复执行

**可能原因**:
1. 创建了重复的任务
2. 并发控制设置不当

**解决方法**:
```python
# 列出所有任务，检查重复
response = requests.get(f"{BASE_URL}/jobs", headers=headers)
jobs = response.json()['data']

# 按名称分组
from collections import defaultdict
jobs_by_name = defaultdict(list)
for job in jobs:
    jobs_by_name[job['name']].append(job['id'])

# 找出重复的任务
for name, ids in jobs_by_name.items():
    if len(ids) > 1:
        print(f"发现重复任务：{name}")
        print(f"任务IDs：{ids}")
        # 删除多余的任务
        for job_id in ids[1:]:
            requests.delete(f"{BASE_URL}/jobs/{job_id}", headers=headers)
```

---

## 总结

本文档提供了丰富的定时任务使用示例，涵盖了：
- 文本任务和AI任务的创建
- 常见应用场景的实现
- 通过AI Agent的自然语言交互
- 任务管理最佳实践
- 故障排查方法

根据这些示例，您可以快速上手并创建适合自己需求的定时任务。
