<template>
  <div class="layout-container">
    <aside class="sidebar">
      <div class="logo">
        <h2>管理后台</h2>
        <p class="subtitle">Admin Panel</p>
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
        <div class="avatar admin">
          <span>{{ user?.username?.charAt(0)?.toUpperCase() || 'A' }}</span>
        </div>
        <div class="user-details">
          <p class="username">{{ user?.username }}</p>
          <p class="role">管理员</p>
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
          <div class="system-status" :class="{ online: systemOnline, offline: !systemOnline }">
            <span class="status-dot"></span>
            <span>{{ systemOnline ? '系统正常' : '系统离线' }}</span>
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
const systemOnline = ref(true)

const menuItems = [
  { path: '/admin', label: '概览', icon: '🏠' },
  { path: '/admin/users', label: '用户管理', icon: '👥' },
  { path: '/admin/cameras', label: '摄像头管理', icon: '📹' },
  { path: '/admin/statistics', label: '数据统计', icon: '📈' },
  { path: '/admin/alerts', label: '告警管理', icon: '🔔' },
  { path: '/admin/ai-assistant', label: 'AI助手', icon: '🤖' },
  { path: '/admin/settings', label: '系统设置', icon: '⚙️' }
]

const currentPageTitle = computed(() => {
  const item = menuItems.find(i => i.path === route.path)
  return item ? item.label : '概览'
})

const logout = () => {
  sessionStorage.removeItem('user')
  window.location.href = '/login'
}

const checkSystemStatus = async () => {
  try {
    const resp = await fetch('/api/status')
    const data = await resp.json()
    systemOnline.value = data.status === 'ok'
  } catch (e) {
    systemOnline.value = false
  }
}

onMounted(() => {
  checkSystemStatus()
})
</script>

<style scoped>
.layout-container {
  display: flex;
  min-height: 100vh;
  background: #0f1419;
  width: 100%;
  overflow: hidden;
}

.sidebar {
  width: 260px;
  background: linear-gradient(180deg, #8b5cf6, #6d28d9);
  display: flex;
  flex-direction: column;
  position: fixed;
  height: 100vh;
  left: 0;
  top: 0;
  z-index: 1000;
}

.logo {
  padding: 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo h2 {
  color: white;
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.logo .subtitle {
  color: rgba(255, 255, 255, 0.6);
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
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  transition: all 0.2s;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.nav-item.active {
  background: white;
  color: #6d28d9;
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
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.user-info .avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 12px;
}

.user-info .avatar.admin {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
}

.user-details .username {
  color: white;
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 4px;
}

.user-details .role {
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
  margin: 0;
}

.logout-btn {
  width: 100%;
  padding: 10px;
  margin-top: 12px;
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.3);
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

.system-status {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
}

.system-status.online {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.system-status.offline {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 8px;
}

.system-status.online .status-dot {
  background: #10b981;
}

.system-status.offline .status-dot {
  background: #ef4444;
}
</style>
