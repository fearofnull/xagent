<template>
  <div class="cron-jobs-page">
    <div class="page-header">
      <div>
        <h1>定时任务</h1>
        <p class="description">管理定时任务，支持文本消息和 AI Agent 任务</p>
      </div>
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>
        创建任务
      </el-button>
    </div>

    <el-card class="table-card">
      <el-table
        :data="jobs"
        :loading="loading"
        style="width: 100%"
        stripe
      >
        <el-table-column prop="id" label="任务ID" width="200" />
        <el-table-column prop="name" label="任务名称" width="180" />
        <el-table-column prop="task_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.task_type === 'text' ? 'success' : 'primary'">
              {{ row.task_type === 'text' ? '文本' : 'Agent' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="schedule.cron" label="Cron 表达式" width="150" />
        <el-table-column prop="dispatch.channel" label="频道" width="100" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-switch
              v-model="row.enabled"
              @change="handleToggleEnabled(row)"
              active-text="启用"
              inactive-text="禁用"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button
              size="small"
              @click="handleRun(row)"
              :loading="runningJobs.has(row.id)"
            >
              立即执行
            </el-button>
            <el-button
              size="small"
              @click="handleEdit(row)"
            >
              编辑
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingJob ? '编辑任务' : '创建任务'"
      width="600px"
      @close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
      >
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入任务名称" />
        </el-form-item>

        <el-form-item label="任务类型" prop="task_type">
          <el-radio-group v-model="formData.task_type">
            <el-radio value="text">文本消息</el-radio>
            <el-radio value="agent">AI Agent</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="消息内容" prop="text">
          <el-input
            v-model="formData.text"
            type="textarea"
            :rows="3"
            placeholder="请输入消息内容或 Agent 提问"
          />
        </el-form-item>

        <el-form-item label="Cron 表达式" prop="cron">
          <el-input v-model="formData.cron" placeholder="例如: 0 9 * * *">
            <template #append>
              <el-button @click="showCronHelp">帮助</el-button>
            </template>
          </el-input>
          <div class="form-help">
            格式: 分钟 小时 日期 月份 星期 (例如: 0 9 * * * 表示每天9:00)
          </div>
        </el-form-item>

        <el-form-item label="目标频道" prop="channel">
          <el-select v-model="formData.channel" placeholder="请选择频道">
            <el-option label="飞书" value="feishu" />
            <el-option label="控制台" value="console" />
          </el-select>
        </el-form-item>

        <el-form-item label="聊天ID" prop="target_chat">
          <el-input v-model="formData.target_chat" placeholder="请输入聊天ID (chat_id)" />
          <div class="form-help">
            优先使用聊天ID,支持私聊和群聊
          </div>
        </el-form-item>

        <el-form-item label="用户ID" prop="target_user">
          <el-input v-model="formData.target_user" placeholder="请输入用户ID (open_id)" />
          <div class="form-help">
            当聊天ID为空时使用
          </div>
        </el-form-item>

        <el-form-item label="时区" prop="timezone">
          <el-select v-model="formData.timezone" placeholder="请选择时区">
            <el-option label="UTC" value="UTC" />
            <el-option label="Asia/Shanghai" value="Asia/Shanghai" />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ editingJob ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- Cron 帮助对话框 -->
    <el-dialog v-model="cronHelpVisible" title="Cron 表达式帮助" width="500px">
      <div class="cron-help">
        <h4>格式说明</h4>
        <p>Cron 表达式由 5 个字段组成：分钟 小时 日期 月份 星期</p>
        
        <h4>常用示例</h4>
        <ul>
          <li><code>0 9 * * *</code> - 每天 9:00</li>
          <li><code>0 */2 * * *</code> - 每 2 小时</li>
          <li><code>30 8 * * 1-5</code> - 工作日 8:30</li>
          <li><code>0 0 * * 0</code> - 每周日零点</li>
          <li><code>*/15 * * * *</code> - 每 15 分钟</li>
        </ul>

        <h4>特殊字符</h4>
        <ul>
          <li><code>*</code> - 匹配所有值</li>
          <li><code>,</code> - 列举多个值，如 1,3,5</li>
          <li><code>-</code> - 范围，如 1-5</li>
          <li><code>/</code> - 步长，如 */15</li>
        </ul>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { cronAPI } from '../api/client'

const jobs = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const cronHelpVisible = ref(false)
const editingJob = ref(null)
const submitting = ref(false)
const runningJobs = ref(new Set())
const formRef = ref(null)

const formData = ref({
  name: '',
  task_type: 'text',
  text: '',
  cron: '0 9 * * *',
  channel: 'feishu',
  target_chat: '',
  target_user: '',
  timezone: 'UTC'
})

const formRules = {
  name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  task_type: [{ required: true, message: '请选择任务类型', trigger: 'change' }],
  text: [{ required: true, message: '请输入消息内容', trigger: 'blur' }],
  cron: [{ required: true, message: '请输入 Cron 表达式', trigger: 'blur' }],
  channel: [{ required: true, message: '请选择频道', trigger: 'change' }]
}

// 加载任务列表
const loadJobs = async () => {
  loading.value = true
  try {
    const response = await cronAPI.getCronJobs()
    jobs.value = response.data.data || []
  } catch (error) {
    ElMessage.error(error.userMessage || '加载任务列表失败')
  } finally {
    loading.value = false
  }
}

// 创建任务
const handleCreate = () => {
  editingJob.value = null
  formData.value = {
    name: '',
    task_type: 'text',
    text: '',
    cron: '0 9 * * *',
    channel: 'feishu',
    target_chat: '',
    target_user: '',
    timezone: 'UTC'
  }
  dialogVisible.value = true
}

// 编辑任务
const handleEdit = (job) => {
  editingJob.value = job
  formData.value = {
    name: job.name,
    task_type: job.task_type,
    text: job.text || '',
    cron: job.schedule?.cron || '0 9 * * *',
    channel: job.dispatch?.channel || 'feishu',
    target_chat: job.dispatch?.target?.chat_id || '',
    target_user: job.dispatch?.target?.user_id || '',
    timezone: job.schedule?.timezone || 'UTC'
  }
  dialogVisible.value = true
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      const jobData = {
        id: editingJob.value?.id || `${formData.value.task_type}-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`,
        name: formData.value.name,
        enabled: true,
        schedule: {
          type: 'cron',
          cron: formData.value.cron,
          timezone: formData.value.timezone
        },
        task_type: formData.value.task_type,
        text: formData.value.text,
        dispatch: {
          type: 'channel',
          channel: formData.value.channel,
          target: {
            chat_id: formData.value.target_chat || null,
            user_id: formData.value.target_user || null
          },
          mode: 'final',
          meta: {}
        },
        runtime: {
          max_concurrency: 1,
          timeout_seconds: 120,
          misfire_grace_seconds: 60
        },
        meta: {}
      }

      if (editingJob.value) {
        await cronAPI.updateCronJob(editingJob.value.id, jobData)
        ElMessage.success('更新成功')
      } else {
        await cronAPI.createCronJob(jobData)
        ElMessage.success('创建成功')
      }

      dialogVisible.value = false
      await loadJobs()
    } catch (error) {
      ElMessage.error(error.userMessage || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

// 删除任务
const handleDelete = async (job) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除任务 "${job.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await cronAPI.deleteCronJob(job.id)
    ElMessage.success('删除成功')
    await loadJobs()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.userMessage || '删除失败')
    }
  }
}

// 切换启用状态
const handleToggleEnabled = async (job) => {
  const originalState = job.enabled
  try {
    // 构建完整的任务数据
    const jobData = {
      id: job.id,
      name: job.name,
      enabled: job.enabled,  // 使用新的状态
      schedule: {
        type: job.schedule.type,
        cron: job.schedule.cron,
        timezone: job.schedule.timezone
      },
      task_type: job.task_type,
      text: job.text,
      request: job.request,
      dispatch: {
        type: job.dispatch.type,
        channel: job.dispatch.channel,
        target: {
          chat_id: job.dispatch.target.chat_id,
          user_id: job.dispatch.target.user_id
        },
        mode: job.dispatch.mode,
        meta: job.dispatch.meta
      },
      runtime: {
        max_concurrency: job.runtime.max_concurrency,
        timeout_seconds: job.runtime.timeout_seconds,
        misfire_grace_seconds: job.runtime.misfire_grace_seconds
      },
      meta: job.meta
    }
    
    await cronAPI.updateCronJob(job.id, jobData)
    ElMessage.success(job.enabled ? '已启用' : '已禁用')
  } catch (error) {
    job.enabled = originalState // 回滚状态
    ElMessage.error(error.userMessage || '操作失败')
  }
}

// 立即执行
const handleRun = async (job) => {
  runningJobs.value.add(job.id)
  try {
    await cronAPI.runCronJob(job.id)
    ElMessage.success('任务已触发执行')
  } catch (error) {
    ElMessage.error(error.userMessage || '执行失败')
  } finally {
    runningJobs.value.delete(job.id)
  }
}

// 显示 Cron 帮助
const showCronHelp = () => {
  cronHelpVisible.value = true
}

// 关闭对话框
const handleDialogClose = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
}

onMounted(() => {
  loadJobs()
})
</script>

<style scoped>
.cron-jobs-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
}

.description {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.table-card {
  margin-top: 20px;
}

.form-help {
  margin-top: 4px;
  font-size: 12px;
  color: #999;
}

.cron-help h4 {
  margin: 16px 0 8px 0;
  font-size: 14px;
  font-weight: 600;
}

.cron-help h4:first-child {
  margin-top: 0;
}

.cron-help p {
  margin: 0 0 8px 0;
  color: #666;
}

.cron-help ul {
  margin: 0;
  padding-left: 20px;
}

.cron-help li {
  margin: 4px 0;
  color: #666;
}

.cron-help code {
  padding: 2px 6px;
  background: #f5f5f5;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
}
</style>
