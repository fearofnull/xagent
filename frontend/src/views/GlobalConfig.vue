<template>
  <div class="global-config-container">
    <!-- Page Header -->
    <div class="page-header">
      <h1 class="page-title">全局配置</h1>
      <p class="page-subtitle">查看系统的全局默认配置，这些值将作为会话配置的默认值</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading" :size="40">
        <Loading />
      </el-icon>
      <p>加载中...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <el-icon :size="40" color="#f56c6c">
        <CircleClose />
      </el-icon>
      <p class="error-message">{{ error }}</p>
      <el-button type="primary" @click="loadGlobalConfig">
        <el-icon><Refresh /></el-icon>
        重试
      </el-button>
    </div>

    <!-- Global Config Display -->
    <div v-else-if="globalConfig" class="config-content">
      <!-- Info Alert -->
      <el-alert
        title="说明"
        type="info"
        :closable="false"
        show-icon
        class="info-alert"
      >
        <p>全局配置是系统级别的默认设置，当会话配置中某个字段未设置时，将使用全局配置的对应值。</p>
        <p>修改全局配置后，将更新 .env 文件并立即生效。</p>
      </el-alert>

      <!-- Config Card -->
      <el-card shadow="hover" class="config-card">
        <template #header>
          <div class="card-header">
            <el-icon :size="20"><Setting /></el-icon>
            <span>全局默认配置</span>
            <div class="header-actions">
              <el-button 
                v-if="!isEditing" 
                type="primary" 
                size="small"
                @click="startEdit"
              >
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <template v-else>
                <el-button 
                  size="small"
                  @click="cancelEdit"
                >
                  取消
                </el-button>
                <el-button 
                  type="primary" 
                  size="small"
                  @click="saveConfig"
                  :loading="saving"
                >
                  <el-icon><Check /></el-icon>
                  保存
                </el-button>
              </template>
            </div>
          </div>
        </template>

        <!-- View Mode -->
        <el-descriptions v-if="!isEditing" :column="1" border size="large">
          <!-- Target Project Directory -->
          <el-descriptions-item>
            <template #label>
              <div class="label-content">
                <el-icon><Folder /></el-icon>
                <span>目标项目目录</span>
              </div>
            </template>
            <div class="value-content">
              <el-tag type="info" effect="plain" size="large">
                {{ globalConfig.target_project_dir || '未设置' }}
              </el-tag>
              <span class="field-description">Bot 操作的默认项目目录路径</span>
            </div>
          </el-descriptions-item>

          <!-- Response Language -->
          <el-descriptions-item>
            <template #label>
              <div class="label-content">
                <el-icon><ChatDotRound /></el-icon>
                <span>响应语言</span>
              </div>
            </template>
            <div class="value-content">
              <el-tag type="success" effect="plain" size="large">
                {{ globalConfig.response_language || '未设置' }}
              </el-tag>
              <span class="field-description">Bot 回复消息使用的默认语言</span>
            </div>
          </el-descriptions-item>

          <!-- Default CLI Provider -->
          <el-descriptions-item>
            <template #label>
              <div class="label-content">
                <el-icon><Monitor /></el-icon>
                <span>默认 CLI 提供商</span>
              </div>
            </template>
            <div class="value-content">
              <el-tag 
                v-if="globalConfig.default_cli_provider" 
                :type="getProviderTagType(globalConfig.default_cli_provider)" 
                effect="plain" 
                size="large"
              >
                {{ globalConfig.default_cli_provider }}
              </el-tag>
              <el-tag v-else type="info" effect="plain" size="large">未设置</el-tag>
              <span class="field-description">CLI 层级使用的默认提供商 (可选)</span>
            </div>
          </el-descriptions-item>

          <!-- XAgent 功能 -->
          <el-descriptions-item>
            <template #label>
              <div class="label-content">
                <el-icon><Operation /></el-icon>
                <span>XAgent 功能</span>
              </div>
            </template>
            <div class="value-content">
              <el-tag 
                :type="globalConfig.agent_enabled ? 'success' : 'danger'" 
                effect="plain" 
                size="large"
              >
                {{ globalConfig.agent_enabled ? '已启用' : '已禁用' }}
              </el-tag>
              <span class="field-description">是否启用 XAgent 智能助手功能</span>
            </div>
          </el-descriptions-item>
        </el-descriptions>

        <!-- Edit Mode -->
        <el-form v-else :model="editForm" label-width="160px" class="edit-form">
          <!-- Target Project Directory -->
          <el-form-item label="目标项目目录">
            <el-input 
              v-model="editForm.target_project_dir" 
              placeholder="例如: /path/to/project"
              clearable
            >
              <template #prepend>
                <el-icon><Folder /></el-icon>
              </template>
            </el-input>
            <div class="form-item-tip">Bot 操作的默认项目目录路径</div>
          </el-form-item>

          <!-- Response Language -->
          <el-form-item label="响应语言">
            <el-select 
              v-model="editForm.response_language" 
              placeholder="选择语言"
              clearable
              style="width: 100%"
            >
              <el-option label="简体中文" value="zh-CN" />
              <el-option label="繁体中文" value="zh-TW" />
              <el-option label="English" value="en-US" />
              <el-option label="日本語" value="ja-JP" />
              <el-option label="한국어" value="ko-KR" />
              <el-option label="Français" value="fr-FR" />
              <el-option label="Deutsch" value="de-DE" />
              <el-option label="Español" value="es-ES" />
            </el-select>
            <div class="form-item-tip">Bot 回复消息使用的默认语言</div>
          </el-form-item>

          <!-- Default CLI Provider -->
          <el-form-item label="默认 CLI 提供商">
            <el-select 
              v-model="editForm.default_cli_provider" 
              placeholder="选择 CLI 提供商（可选）"
              clearable
              style="width: 100%"
            >
              <el-option label="Claude" value="claude" />
              <el-option label="Gemini" value="gemini" />
              <el-option label="Qwen" value="qwen" />
            </el-select>
            <div class="form-item-tip">CLI 层级使用的默认提供商（可选）</div>
          </el-form-item>

          <!-- XAgent 功能 -->
          <el-form-item label="XAgent 功能">
            <el-switch 
              v-model="editForm.agent_enabled" 
              active-text="启用" 
              inactive-text="禁用"
            />
            <div class="form-item-tip">是否启用 XAgent 智能助手功能</div>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- Refresh Button (only in view mode) -->
      <div v-if="!isEditing" class="actions">
        <el-button type="primary" @click="loadGlobalConfig" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新配置
        </el-button>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="empty-container">
      <el-empty description="未找到全局配置" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useConfigStore } from '@/stores/config'
import { ElMessage } from 'element-plus'
import { 
  Loading, 
  CircleClose, 
  Refresh, 
  Setting, 
  Folder, 
  ChatDotRound, 
  Operation, 
  Monitor,
  Edit,
  Check
} from '@element-plus/icons-vue'
import { configAPI } from '@/api/client'

const configStore = useConfigStore()

const globalConfig = ref(null)
const loading = ref(false)
const error = ref(null)
const isEditing = ref(false)
const saving = ref(false)
const editForm = ref({
  target_project_dir: '',
  response_language: '',
  default_cli_provider: '',
  agent_enabled: true
})

// Get provider tag type
const getProviderTagType = (provider) => {
  const typeMap = {
    'claude': 'primary',
    'gemini': 'success',
    'qwen': 'warning'
  }
  return typeMap[provider] || 'info'
}

// Load global configuration
const loadGlobalConfig = async () => {
  loading.value = true
  error.value = null
  
  try {
    const config = await configStore.fetchGlobalConfig()
    globalConfig.value = config
    ElMessage.success('全局配置加载成功')
  } catch (err) {
    error.value = err.userMessage || '加载全局配置失败'
    ElMessage.error(error.value)
  } finally {
    loading.value = false
  }
}

// Start editing
const startEdit = () => {
  editForm.value = {
    target_project_dir: globalConfig.value.target_project_dir || '',
    response_language: globalConfig.value.response_language || '',
    default_cli_provider: globalConfig.value.default_cli_provider || '',
    agent_enabled: globalConfig.value.agent_enabled !== undefined ? globalConfig.value.agent_enabled : true
  }
  isEditing.value = true
}

// Cancel editing
const cancelEdit = () => {
  isEditing.value = false
  editForm.value = {
    target_project_dir: '',
    response_language: '',
    default_cli_provider: '',
    agent_enabled: true
  }
}

// Save configuration
const saveConfig = async () => {
  saving.value = true
  
  try {
    // Prepare data (convert empty strings to null)
    const data = {
      target_project_dir: editForm.value.target_project_dir || null,
      response_language: editForm.value.response_language || null,
      default_cli_provider: editForm.value.default_cli_provider || null,
      agent_enabled: editForm.value.agent_enabled
    }
    
    const response = await configAPI.updateGlobalConfig(data)
    
    // Update local state
    globalConfig.value = response.data.data.global_config
    
    // Exit edit mode
    isEditing.value = false
    
    ElMessage.success('全局配置更新成功')
  } catch (err) {
    ElMessage.error(err.userMessage || '更新全局配置失败')
  } finally {
    saving.value = false
  }
}

// Load config on mount
onMounted(() => {
  loadGlobalConfig()
})
</script>

<style scoped>
.global-config-container {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

/* Page Header */
.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.page-subtitle {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

/* Loading State */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: #909399;
}

.loading-container p {
  margin-top: 16px;
  font-size: 14px;
}

/* Error State */
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
}

.error-message {
  margin: 16px 0;
  font-size: 14px;
  color: #f56c6c;
}

/* Config Content */
.config-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.info-alert {
  margin-bottom: 4px;
}

.info-alert p {
  margin: 4px 0;
  line-height: 1.6;
}

/* Config Card */
.config-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 8px;
}

/* Descriptions */
.label-content {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.value-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-description {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}

/* Edit Form */
.edit-form {
  padding: 20px 0;
}

.form-item-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.5;
}

/* Actions */
.actions {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}

/* Empty State */
.empty-container {
  padding: 80px 20px;
}

/* Responsive Design */
@media (max-width: 768px) {
  .global-config-container {
    padding: 16px;
  }

  .page-title {
    font-size: 24px;
  }

  .page-subtitle {
    font-size: 13px;
  }

  .config-card {
    margin: 0 -8px;
  }

  .value-content {
    gap: 6px;
  }

  .field-description {
    font-size: 11px;
  }

  /* Stack descriptions vertically */
  :deep(.el-descriptions__label) {
    width: 100% !important;
    text-align: left !important;
    padding-bottom: 8px !important;
  }

  :deep(.el-descriptions__content) {
    width: 100% !important;
    display: block !important;
    padding-left: 0 !important;
  }

  .label-content {
    font-size: 13px;
  }

  .info-alert {
    font-size: 13px;
  }

  .info-alert p {
    font-size: 12px;
  }
}

/* Extra small screens */
@media (max-width: 480px) {
  .global-config-container {
    padding: 12px;
  }

  .page-title {
    font-size: 20px;
  }

  .page-subtitle {
    font-size: 12px;
  }

  .card-header {
    font-size: 14px;
  }

  .label-content {
    font-size: 12px;
  }

  .value-content .el-tag {
    font-size: 11px;
  }
}
</style>
