<template>
  <div class="layout-container">
    <aside class="sidebar">
      <div class="logo">
        <h2>居家老人行为监测与跌倒智能预警系统</h2>
        <p class="subtitle">Fall Detection</p>
      </div>
      
      <nav class="nav-menu">
        <router-link 
          v-for="item in menuItems" 
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: route.path === item.path }"
        >
          <span class="icon">{{ item.icon }}</span>
          <span class="text">{{ item.label }}</span>
        </router-link>
      </nav>
      
      <div class="user-info">
        <div class="avatar">
          <span>{{ user?.username?.charAt(0)?.toUpperCase() || 'U' }}</span>
        </div>
        <div class="user-details">
          <p class="username">{{ user?.username }}</p>
          <p class="role">普通用户</p>
        </div>
        <button class="logout-btn" @click="logout">
          <span>退出登录</span>
        </button>
      </div>
    </aside>
    
    <main class="main-content">
      <header class="top-header">
        <div class="header-left">
          <h1>{{ currentPageTitle }}</h1>
        </div>
        <div class="header-right">
          <div class="alert-badge" v-if="alertCount > 0">
            <span>{{ alertCount }}</span>
          </div>
        </div>
      </header>
      
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const user = ref(JSON.parse(sessionStorage.getItem('user') || 'null'))
const alertCount = ref(0)

const menuItems = [
  { path: '/user', label: '首页', icon: '📊' },
  { path: '/user/cameras', label: '摄像头管理', icon: '📹' },
  { path: '/user/camera', label: '实时监控', icon: '🎥' },
  { path: '/user/upload', label: '视频分析', icon: '📁' },
  { path: '/user/history', label: '分析记录', icon: '📋' },
  { path: '/user/alerts', label: '告警记录', icon: '🔔' },
  { path: '/user/ai-assistant', label: 'AI助手', icon: '🤖' },
  { path: '/user/profile', label: '个人中心', icon: '👤' }
]

const currentPageTitle = computed(() => {
  const item = menuItems.find(i => i.path === route.path)
  return item ? item.label : '首页'
})

const logout = () => {
  sessionStorage.removeItem('user')
  window.location.href = '/login'
}

const fetchAlertCount = async () => {
  try {
    const resp = await fetch('/api/alerts', { credentials: 'include' })
    const data = await resp.json()
    if (data.alerts) {
      alertCount.value = data.alerts.filter(a => !a.acknowledged).length
    }
  } catch (e) {
    console.error('获取告警数量失败', e)
  }
}

onMounted(() => {
  fetchAlertCount()
})
</script>

<style scoped>
.layout-container {
  display: flex;
  height: 100vh;
  background: #0f1419;
}

.sidebar {
  width: 260px;
  background: #1a1f25;
  display: flex;
  flex-direction: column;
  position: fixed;
  height: 100vh;
  left: 0;
  top: 0;
}

.logo {
  padding: 24px;
  border-bottom: 1px solid #2a3038;
}

.logo h2 {
  color: #10b981;
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.logo .subtitle {
  color: #6b7280;
  font-size: 12px;
  margin: 4px 0 0;
}

.nav-menu {
  flex: 1;
  padding: 16px;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  margin-bottom: 4px;
  border-radius: 8px;
  color: #9ca3af;
  text-decoration: none;
  transition: all 0.2s;
}

.nav-item:hover {
  background: #2a3038;
  color: #e7e9ea;
}

.nav-item.active {
  background: #10b981;
  color: white;
}

.nav-item .icon {
  font-size: 18px;
  margin-right: 12px;
}

.nav-item .text {
  font-size: 14px;
  font-weight: 500;
}

.user-info {
  padding: 16px;
  border-top: 1px solid #2a3038;
}

.user-info .avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #10b981, #059669);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 12px;
}

.user-details .username {
  color: #e7e9ea;
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 4px;
}

.user-details .role {
  color: #6b7280;
  font-size: 12px;
  margin: 0;
}

.logout-btn {
  width: 100%;
  padding: 10px;
  margin-top: 12px;
  background: #ef4444;
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}

.logout-btn:hover {
  background: #dc2626;
}

.main-content {
  flex: 1;
  margin-left: 260px;
  display: flex;
  flex-direction: column;
  overflow: auto;
}

.top-header {
  padding: 16px 24px;
  background: #1a1f25;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left h1 {
  color: #e7e9ea;
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
}

.alert-badge {
  background: #ef4444;
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
}
</style>
