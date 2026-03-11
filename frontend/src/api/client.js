import axios from 'axios'

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle different error scenarios
    if (error.response) {
      // Server responded with error status code
      const { status, data } = error.response
      
      switch (status) {
        case 401:
          // Unauthorized - token expired or invalid
          handleUnauthorized()
          error.userMessage = '登录已过期，请重新登录'
          error.errorType = 'auth'
          break
        case 403:
          // Forbidden - insufficient permissions
          error.userMessage = '没有权限执行此操作'
          error.errorType = 'permission'
          break
        case 404:
          // Not found
          error.userMessage = data?.message || '请求的资源不存在'
          error.errorType = 'not_found'
          break
        case 400:
          // Bad request - validation error
          error.userMessage = data?.message || '请求参数无效'
          error.validationErrors = data?.error?.details
          error.fieldErrors = data?.error?.field ? { [data.error.field]: data.error.details } : null
          error.errorType = 'validation'
          break
        case 500:
          // Internal server error
          error.userMessage = '服务器内部错误，请稍后重试'
          error.errorType = 'server'
          break
        default:
          error.userMessage = data?.message || `请求失败 (${status})`
          error.errorType = 'unknown'
      }
    } else if (error.request) {
      // Request was made but no response received (network error)
      error.userMessage = '网络连接失败，请检查网络连接'
      error.errorType = 'network'
    } else {
      // Something else happened
      error.userMessage = error.message || '请求配置错误'
      error.errorType = 'config'
    }
    
    return Promise.reject(error)
  }
)

// Handle unauthorized access
function handleUnauthorized() {
  // Clear token from localStorage
  localStorage.removeItem('token')
  
  // Redirect to login page if not already there
  if (window.location.pathname !== '/login') {
    window.location.href = '/login'
  }
}

export default apiClient


// API helper functions
export const authAPI = {
  login: (password) => apiClient.post('/auth/login', { password }),
  logout: () => apiClient.post('/auth/logout')
}

export const configAPI = {
  // Get all configs with optional filters
  getConfigs: (params = {}) => apiClient.get('/configs', { params }),
  
  // Get single config by session_id
  getConfig: (sessionId) => apiClient.get(`/configs/${sessionId}`),
  
  // Get effective config (with defaults applied)
  getEffectiveConfig: (sessionId) => apiClient.get(`/configs/${sessionId}/effective`),
  
  // Update config
  updateConfig: (sessionId, data) => apiClient.put(`/configs/${sessionId}`, data),
  
  // Delete config (reset to defaults)
  deleteConfig: (sessionId) => apiClient.delete(`/configs/${sessionId}`),
  
  // Get global config
  getGlobalConfig: () => apiClient.get('/configs/global'),
  
  // Update global config
  updateGlobalConfig: (data) => apiClient.put('/configs/global', data),
  
  // Export all configs
  exportConfigs: () => apiClient.post('/configs/export', {}, { responseType: 'blob' }),
  
  // Import configs from file
  importConfigs: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post('/configs/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
}

export const providerAPI = {
  // Get all provider configs
  getProviders: () => apiClient.get('/providers'),
  
  // Get single provider config
  getProvider: (name) => apiClient.get(`/providers/${name}`),
  
  // Create new provider config
  createProvider: (data) => apiClient.post('/providers', data),
  
  // Update provider config
  updateProvider: (name, data) => apiClient.put(`/providers/${name}`, data),
  
  // Delete provider config
  deleteProvider: (name) => apiClient.delete(`/providers/${name}`),
  
  // Set default provider
  setDefault: (name) => apiClient.post(`/providers/${name}/set-default`),
  
  // Get default provider
  getDefault: () => apiClient.get('/providers/default'),
  
  // Test provider connection
  testProvider: (name, model) => apiClient.post(`/providers/${name}/test`, { model })
}

export const sessionAPI = {
  // Get all sessions with optional filters
  getSessions: (params = {}) => apiClient.get('/sessions', { params }),
  
  // Get single session by session_id
  getSession: (sessionId) => apiClient.get(`/sessions/${sessionId}`),
  
  // Delete session
  deleteSession: (sessionId) => apiClient.delete(`/sessions/${sessionId}`)
}

export const cronAPI = {
  // Get all cron jobs
  getCronJobs: () => apiClient.get('/cron/jobs'),
  
  // Get single cron job
  getCronJob: (jobId) => apiClient.get(`/cron/jobs/${jobId}`),
  
  // Create new cron job
  createCronJob: (data) => apiClient.post('/cron/jobs', data),
  
  // Update cron job
  updateCronJob: (jobId, data) => apiClient.put(`/cron/jobs/${jobId}`, data),
  
  // Delete cron job
  deleteCronJob: (jobId) => apiClient.delete(`/cron/jobs/${jobId}`),
  
  // Pause cron job
  pauseCronJob: (jobId) => apiClient.post(`/cron/jobs/${jobId}/pause`),
  
  // Resume cron job
  resumeCronJob: (jobId) => apiClient.post(`/cron/jobs/${jobId}/resume`),
  
  // Run cron job immediately
  runCronJob: (jobId) => apiClient.post(`/cron/jobs/${jobId}/run`)
}

