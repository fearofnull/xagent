<template>
  <nav class="navbar">
    <div class="navbar-container">
      <!-- Logo and Title -->
      <div class="navbar-brand">
        <div class="logo-icon">
          <el-icon :size="28"><Setting /></el-icon>
        </div>
        <h1 class="app-title">飞书 AI Bot 管理</h1>
      </div>

      <!-- Navigation Links -->
      <div class="navbar-nav">
        <router-link 
          to="/providers" 
          class="nav-link"
          active-class="nav-link-active"
        >
          <el-icon><Connection /></el-icon>
          <span>提供商配置</span>
        </router-link>
        
        <router-link 
          to="/global-config" 
          class="nav-link"
          active-class="nav-link-active"
        >
          <el-icon><Tools /></el-icon>
          <span>全局配置</span>
        </router-link>
        
        <router-link 
          to="/sessions" 
          class="nav-link"
          active-class="nav-link-active"
        >
          <el-icon><ChatDotRound /></el-icon>
          <span>会话记录</span>
        </router-link>
        
        <router-link 
          to="/configs" 
          class="nav-link"
          active-class="nav-link-active"
        >
          <el-icon><List /></el-icon>
          <span>会话配置列表</span>
        </router-link>
        
        <router-link 
          to="/cron-jobs" 
          class="nav-link"
          active-class="nav-link-active"
        >
          <el-icon><Clock /></el-icon>
          <span>定时任务</span>
        </router-link>
      </div>

      <!-- Logout Button -->
      <div class="navbar-actions">
        <el-button 
          type="danger" 
          :icon="SwitchButton"
          @click="handleLogout"
          :loading="isLoggingOut"
          class="logout-btn"
        >
          登出
        </el-button>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { Setting, List, Tools, SwitchButton, ChatDotRound, Connection, Clock } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()
const isLoggingOut = ref(false)

/**
 * Handle logout action
 * Logs out user and redirects to login page
 */
const handleLogout = async () => {
  try {
    isLoggingOut.value = true
    
    // Call logout action from auth store
    await authStore.logout()
    
    // Show success message
    ElMessage.success('已成功登出')
    
    // Redirect to login page
    router.push('/login')
  } catch (error) {
    console.error('Logout failed:', error)
    ElMessage.error('登出失败，请重试')
  } finally {
    isLoggingOut.value = false
  }
}
</script>

<style scoped>
.navbar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  position: sticky;
  top: 0;
  z-index: 1000;
  backdrop-filter: blur(10px);
}

.navbar-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 32px;
}

/* Brand Section */
.navbar-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  transition: all 0.3s ease;
}

.logo-icon:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: rotate(90deg);
}

.app-title {
  font-size: 20px;
  font-weight: 600;
  color: white;
  margin: 0;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

/* Navigation Links */
.navbar-nav {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  color: rgba(255, 255, 255, 0.9);
  text-decoration: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 500;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.nav-link::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.1);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.3s ease;
  z-index: -1;
}

.nav-link:hover::before {
  transform: scaleX(1);
}

.nav-link:hover {
  color: white;
  background: rgba(255, 255, 255, 0.15);
}

.nav-link-active {
  color: white;
  background: rgba(255, 255, 255, 0.25);
  font-weight: 600;
}

.nav-link-active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 20px;
  right: 20px;
  height: 3px;
  background: white;
  border-radius: 2px 2px 0 0;
}

/* Actions Section */
.navbar-actions {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.logout-btn {
  font-weight: 500;
  border: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
}

.logout-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

/* Responsive Design */
@media (max-width: 768px) {
  .navbar-container {
    padding: 0 16px;
    height: 56px;
    gap: 16px;
  }

  .app-title {
    font-size: 16px;
  }

  .logo-icon {
    width: 36px;
    height: 36px;
  }

  .nav-link span {
    display: none;
  }

  .nav-link {
    padding: 10px 12px;
  }

  .logout-btn span {
    display: none;
  }
}

@media (max-width: 480px) {
  .navbar-container {
    gap: 8px;
  }

  .navbar-brand {
    gap: 8px;
  }

  .app-title {
    font-size: 14px;
  }

  .navbar-nav {
    gap: 4px;
  }
}
</style>
