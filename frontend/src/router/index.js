import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import ConfigList from '../views/ConfigList.vue'
import ConfigDetail from '../views/ConfigDetail.vue'
import GlobalConfig from '../views/GlobalConfig.vue'
import Sessions from '../views/Sessions.vue'
import SessionDetail from '../views/SessionDetail.vue'
import Providers from '../views/Providers.vue'
import CronJobs from '../views/CronJobs.vue'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/configs',
    name: 'ConfigList',
    component: ConfigList,
    meta: { requiresAuth: true }
  },
  {
    path: '/configs/:id',
    name: 'ConfigDetail',
    component: ConfigDetail,
    meta: { requiresAuth: true }
  },
  {
    path: '/global-config',
    name: 'GlobalConfig',
    component: GlobalConfig,
    meta: { requiresAuth: true }
  },
  {
    path: '/sessions',
    name: 'Sessions',
    component: Sessions,
    meta: { requiresAuth: true }
  },
  {
    path: '/sessions/:id',
    name: 'SessionDetail',
    component: SessionDetail,
    meta: { requiresAuth: true }
  },
  {
    path: '/providers',
    name: 'Providers',
    component: Providers,
    meta: { requiresAuth: true }
  },
  {
    path: '/cron-jobs',
    name: 'CronJobs',
    component: CronJobs,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard for authentication
router.beforeEach((to, from) => {
  const token = localStorage.getItem('token')
  
  if (to.meta.requiresAuth && !token) {
    return '/login'
  } else if (to.path === '/login' && token) {
    return '/configs'
  }
  // Allow navigation by returning nothing (undefined)
})

export default router

