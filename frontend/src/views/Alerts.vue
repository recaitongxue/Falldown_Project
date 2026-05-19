<template>
  <div class="dashboard">
    <aside class="sidebar">
      <div class="logo"><h2>🛡️ 跌倒检测</h2><p>Fall Detection System</p></div>
      <nav class="nav-menu">
        <router-link to="/dashboard" class="nav-item"><span class="icon">📊</span><span>仪表盘</span></router-link>
        <router-link to="/cameras" class="nav-item"><span class="icon">📹</span><span>摄像头管理</span></router-link>
        <router-link to="/upload" class="nav-item"><span class="icon">📁</span><span>文件上传</span></router-link>
        <router-link to="/history" class="nav-item"><span class="icon">📋</span><span>检测历史</span></router-link>
        <router-link to="/statistics" class="nav-item"><span class="icon">📈</span><span>数据统计</span></router-link>
        <router-link to="/alerts" class="nav-item active"><span class="icon">🔔</span><span>告警中心</span></router-link>
        <router-link to="/ai-assistant" class="nav-item"><span class="icon">🤖</span><span>AI助手</span></router-link>
        <router-link to="/settings" class="nav-item"><span class="icon">⚙️</span><span>系统设置</span></router-link>
      </nav>
      <div class="user-info">
        <div class="user-avatar">{{ user?.[0]?.toUpperCase() || 'A' }}</div>
        <div class="user-details"><span class="user-name">{{ user || 'Admin' }}</span></div>
        <el-button text @click="handleLogout">🚪</el-button>
      </div>
    </aside>

    <main class="main-content">
      <header class="content-header">
        <h1>告警中心</h1>
        <div class="header-actions">
          <el-button @click="fetchAlerts">🔄 刷新</el-button>
          <el-button type="danger" @click="clearAll">清空全部</el-button>
        </div>
      </header>

      <div class="stats-row">
        <div class="stat-card critical">
          <span class="stat-value">{{ stats.critical }}</span>
          <span class="stat-label">严重告警</span>
        </div>
        <div class="stat-card warning">
          <span class="stat-value">{{ stats.warning }}</span>
          <span class="stat-label">警告</span>
        </div>
        <div class="stat-card info">
          <span class="stat-value">{{ stats.info }}</span>
          <span class="stat-label">信息</span>
        </div>
        <div class="stat-card resolved">
          <span class="stat-value">{{ stats.resolved }}</span>
          <span class="stat-label">已处理</span>
        </div>
      </div>

      <div class="alert-list">
        <div v-for="alert in alerts" :key="alert.id" class="alert-item" :class="getSeverityClass(alert)">
          <div class="alert-icon">🔔</div>
          <div class="alert-content">
            <h4>{{ alert.behavior || '跌倒检测告警' }}</h4>
            <p>置信度: {{ ((alert.confidence || 0) * 100).toFixed(1) }}%</p>
            <p class="alert-time">{{ formatTime(alert.created_at) }}</p>
            <div class="alert-details" v-if="alert.M1 || alert.M2 || alert.M3">
              <span class="detail-tag" :class="{ active: alert.M1 }">M1(重心)</span>
              <span class="detail-tag" :class="{ active: alert.M2 }">M2(倾斜)</span>
              <span class="detail-tag" :class="{ active: alert.M3 }">M3(变形)</span>
            </div>
          </div>
          <div class="alert-actions">
            <el-tag v-if="alert.M1 && alert.M2 && alert.M3" type="danger" size="large">⚠️ 跌倒</el-tag>
            <el-tag v-else type="warning" size="large">⚡ 疑似</el-tag>
            <el-button v-if="!alert.acknowledged" type="success" size="small" @click="acknowledgeAlert(alert.id)">确认</el-button>
          </div>
        </div>

        <div v-if="alerts.length === 0" class="no-data">
          <p>🎉 暂无告警信息</p>
          <p>系统运行正常</p>
        </div>
      </div>

      <el-pagination v-if="total > 0" background layout="prev, pager, next" :total="total" v-model:current-page="currentPage" @current-change="fetchAlerts" />
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()
const user = ref(sessionStorage.getItem('user') ? JSON.parse(sessionStorage.getItem('user')).username : 'Admin')
const alerts = ref([])
const currentPage = ref(1)
const total = ref(0)

const stats = reactive({ critical: 0, warning: 0, info: 0, resolved: 0 })

onMounted(fetchAlerts)

async function fetchAlerts() {
  try {
    const resp = await fetch('/api/alerts')
    const data = await resp.json()
    alerts.value = data.data || []
    total.value = alerts.value.length

    stats.critical = alerts.value.filter(a => a.M1 && a.M2 && a.M3).length
    stats.warning = alerts.value.filter(a => !a.acknowledged).length
    stats.info = alerts.value.filter(a => !a.M1 && !a.M2 && !a.M3).length
    stats.resolved = alerts.value.filter(a => a.acknowledged).length
  } catch (e) {
    console.error(e)
  }
}

async function clearAll() {
  try {
    await fetch('/api/alerts/clear', { method: 'POST' })
    ElMessage.success('已清空')
    fetchAlerts()
  } catch (e) {
    ElMessage.error('清空失败')
  }
}

function getSeverityClass(alert) {
  if (alert.M1 && alert.M2 && alert.M3) return 'critical'
  if (!alert.acknowledged) return 'warning'
  return 'info'
}

async function acknowledgeAlert(alertId) {
  try {
    await fetch(`/api/alerts/${alertId}/acknowledge`, { method: 'POST' })
    ElMessage.success('已确认')
    fetchAlerts()
  } catch (e) {
    ElMessage.error('确认失败')
  }
}

function formatTime(ts) {
  if (!ts) return ''
  return new Date(ts).toLocaleString('zh-CN')
}

function handleLogout() {
  sessionStorage.clear()
  router.push('/login')
}
</script>

<style scoped>
.dashboard { display: flex; min-height: 100vh; }
.sidebar { width: 240px; background: #1a1f25; padding: 20px; display: flex; flex-direction: column; }
.logo h2 { color: #00d4ff; font-size: 18px; margin-bottom: 5px; }
.logo p { color: #666; font-size: 11px; }
.nav-menu { flex: 1; margin-top: 30px; }
.nav-item { display: flex; align-items: center; padding: 12px 15px; color: #8899a6; text-decoration: none; border-radius: 8px; margin-bottom: 5px; transition: all 0.3s; }
.nav-item:hover, .nav-item.router-link-active { background: #2f3336; color: #fff; }
.nav-item.active { background: #00d4ff20; color: #00d4ff; }
.nav-item .icon { margin-right: 10px; font-size: 18px; }
.user-info { display: flex; align-items: center; padding: 15px; background: #2f3336; border-radius: 10px; gap: 10px; }
.user-avatar { width: 40px; height: 40px; background: linear-gradient(135deg, #667eea, #764ba2); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold; }
.user-details { flex: 1; }
.user-name { font-size: 14px; font-weight: 500; }
.main-content { flex: 1; padding: 20px; overflow-y: auto; }
.content-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.content-header h1 { font-size: 24px; color: #fff; }
.header-actions { display: flex; gap: 10px; }
.stats-row { display: flex; gap: 20px; margin-bottom: 20px; }
.stat-card { flex: 1; padding: 20px; border-radius: 10px; text-align: center; }
.stat-card.critical { background: linear-gradient(135deg, #ff4757, #ff6b81); }
.stat-card.warning { background: linear-gradient(135deg, #ffaa00, #ffbe00); }
.stat-card.info { background: linear-gradient(135deg, #00d4ff, #0099cc); }
.stat-card.resolved { background: linear-gradient(135deg, #00ff88, #00cc6a); }
.stat-value { display: block; font-size: 32px; font-weight: bold; color: #fff; }
.stat-label { font-size: 12px; color: rgba(255,255,255,0.8); }
.alert-list { display: flex; flex-direction: column; gap: 15px; }
.alert-item { display: flex; align-items: center; background: #1a1f25; padding: 20px; border-radius: 10px; border-left: 4px solid #ff4757; }
.alert-item.warning { border-left-color: #ffaa00; }
.alert-item.resolved { border-left-color: #00ff88; }
.alert-icon { font-size: 30px; margin-right: 15px; }
.alert-content { flex: 1; }
.alert-content h4 { color: #fff; margin-bottom: 5px; }
.alert-content p { color: #8899a6; font-size: 13px; margin: 3px 0; }
.alert-time { font-size: 12px !important; color: #666 !important; }
.alert-details { display: flex; gap: 10px; margin-top: 10px; }
.detail-tag { padding: 3px 8px; background: #2f3336; border-radius: 5px; font-size: 11px; color: #666; }
.detail-tag.active { background: #ff4757; color: #fff; }
.alert-actions { display: flex; gap: 10px; }
.no-data { text-align: center; padding: 60px; color: #666; }
</style>
