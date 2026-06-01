<template>
  <div class="admin-dashboard">
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">👥</div>
        <div class="stat-info">
          <p class="stat-value">{{ stats.total_users }}</p>
          <p class="stat-label">总用户数</p>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">📹</div>
        <div class="stat-info">
          <p class="stat-value">{{ stats.total_analyses }}</p>
          <p class="stat-label">分析次数</p>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">🔔</div>
        <div class="stat-info">
          <p class="stat-value">{{ stats.pending_alerts }}</p>
          <p class="stat-label">待处理告警</p>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">⚠️</div>
        <div class="stat-info">
          <p class="stat-value">{{ stats.fall_count }}</p>
          <p class="stat-label">跌倒检测</p>
        </div>
      </div>
    </div>
    
    <div class="charts-row">
      <div class="chart-card">
        <h3>用户增长趋势</h3>
        <div class="mini-chart">
          <div v-for="(item, index) in userGrowthData" :key="index" class="chart-bar" :style="{ height: item.percentage + '%' }">
            {{ item.month }}
          </div>
        </div>
      </div>
      
      <div class="chart-card">
        <h3>检测类型分布</h3>
        <div class="pie-chart">
          <div class="pie-slice fall" :style="{ '--percentage': fallRate + '%' }">跌倒</div>
          <div class="pie-slice normal" :style="{ '--percentage': (100 - fallRate) + '%' }">正常</div>
        </div>
        <div class="legend">
          <span class="legend-item"><span class="dot fall"></span> 跌倒 {{ fallRate }}%</span>
          <span class="legend-item"><span class="dot normal"></span> 正常 {{ 100 - fallRate }}%</span>
        </div>
      </div>
    </div>
    
    <div class="recent-section">
      <div class="section-header">
        <h3>最近告警</h3>
        <a href="/admin/alerts" class="view-all">查看全部 →</a>
      </div>
      <div class="alerts-list">
        <div 
          v-for="alert in recentAlerts" 
          :key="alert.id" 
          class="alert-item"
        >
          <div class="alert-icon">{{ alert.severity === 'high' ? '🚨' : '⚠️' }}</div>
          <div class="alert-content">
            <p class="alert-title">{{ alert.title }}</p>
            <p class="alert-user">用户: {{ alert.username }}</p>
          </div>
          <div class="alert-time">{{ formatTime(alert.timestamp) }}</div>
        </div>
        
        <div v-if="recentAlerts.length === 0" class="empty-state">
          <p>暂无告警</p>
        </div>
      </div>
    </div>
    
    <div class="system-status">
      <h3>系统状态</h3>
      <div class="status-grid">
        <div class="status-item">
          <span class="status-dot online"></span>
          <span>数据库</span>
          <span class="status-text">正常</span>
        </div>
        <div class="status-item">
          <span class="status-dot online"></span>
          <span>检测模型</span>
          <span class="status-text">已加载</span>
        </div>
        <div class="status-item">
          <span class="status-dot" :class="ollamaStatus ? 'online' : 'offline'"></span>
          <span>Ollama</span>
          <span class="status-text">{{ ollamaStatus ? '已连接' : '未连接' }}</span>
        </div>
        <div class="status-item">
          <span class="status-dot online"></span>
          <span>API服务</span>
          <span class="status-text">正常</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const userInfo = ref(sessionStorage.getItem('user') ? JSON.parse(sessionStorage.getItem('user')) : null)
const userId = ref(userInfo.value?.id || 1)

const stats = ref({
  total_users: 0,
  total_analyses: 0,
  pending_alerts: 0,
  fall_count: 0,
  normal_count: 0
})

const recentAlerts = ref([])
const ollamaStatus = ref(false)
const userGrowthData = ref([])
const fallRate = ref(0)

const formatTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const loadStats = async () => {
  try {
    const resp = await fetch('/api/statistics', { 
      credentials: 'include',
      headers: {
        'X-User-Id': userId.value
      }
    })
    const data = await resp.json()
    stats.value = {
      total_users: data.total_users || 0,
      total_analyses: data.total_analyses || 0,
      pending_alerts: data.pending_alerts || 0,
      fall_count: data.fall_count || 0,
      normal_count: data.normal_count || 0
    }
    fallRate.value = data.fall_rate || 0
    
    // 加载用户增长趋势数据
    await loadUserGrowth()
  } catch (e) {
    console.error('获取统计数据失败', e)
  }
}

const loadUserGrowth = async () => {
  try {
    const resp = await fetch('/api/statistics/daily?range=7d', { 
      credentials: 'include',
      headers: {
        'X-User-Id': userId.value
      }
    })
    const data = await resp.json()
    const dailyData = data.data || []
    
    // 转换为图表数据 - 显示日期格式 (如 "5/19")
    const maxUsers = Math.max(...dailyData.map(d => d.users), 1)
    userGrowthData.value = dailyData.map(d => {
      const date = new Date(d.date)
      return {
        month: (date.getMonth() + 1) + '/' + date.getDate(),
        percentage: Math.round((d.users / maxUsers) * 100)
      }
    })
  } catch (e) {
    console.error('获取用户增长数据失败', e)
    userGrowthData.value = []
  }
}

const loadAlerts = async () => {
  try {
    const resp = await fetch('/api/alerts?per_page=5', { credentials: 'include' })
    const data = await resp.json()
    recentAlerts.value = data.data || []
  } catch (e) {
    console.error('获取告警失败', e)
  }
}

const checkOllama = async () => {
  try {
    const resp = await fetch('/api/ai/ollama/status')
    const data = await resp.json()
    ollamaStatus.value = data.available || false
  } catch (e) {
    ollamaStatus.value = false
  }
}

onMounted(() => {
  loadStats()
  loadAlerts()
  checkOllama()
})
</script>

<style scoped>
.admin-dashboard {
  padding: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  background: #1a1f25;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
}

.stat-icon {
  font-size: 36px;
  margin-right: 16px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #8b5cf6;
  margin: 0;
}

.stat-label {
  font-size: 14px;
  color: #9ca3af;
  margin: 4px 0 0;
}

.charts-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.chart-card {
  background: #1a1f25;
  border-radius: 12px;
  padding: 20px;
}

.chart-card h3 {
  color: #e7e9ea;
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 16px;
}

.mini-chart {
  display: flex;
  justify-content: space-around;
  align-items: flex-end;
  height: 120px;
}

.chart-bar {
  width: 30px;
  background: linear-gradient(180deg, #8b5cf6, #6d28d9);
  border-radius: 4px 4px 0 0;
  transition: height 0.3s;
}

.pie-chart {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: conic-gradient(
    #ef4444 0% 35%,
    #10b981 35% 100%
  );
  margin: 0 auto 16px;
}

.legend {
  display: flex;
  justify-content: center;
  gap: 20px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #9ca3af;
  font-size: 12px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.dot.fall { background: #ef4444; }
.dot.normal { background: #10b981; }

.recent-section {
  background: #1a1f25;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  color: #e7e9ea;
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.view-all {
  color: #8b5cf6;
  font-size: 14px;
  text-decoration: none;
}

.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.alert-item {
  display: flex;
  align-items: center;
  padding: 12px;
  background: #2a3038;
  border-radius: 8px;
}

.alert-icon {
  font-size: 24px;
  margin-right: 12px;
}

.alert-content {
  flex: 1;
}

.alert-title {
  color: #e7e9ea;
  font-size: 14px;
  margin: 0 0 4px;
}

.alert-user {
  color: #6b7280;
  font-size: 12px;
  margin: 0;
}

.alert-time {
  color: #6b7280;
  font-size: 12px;
}

.empty-state {
  text-align: center;
  padding: 24px;
  color: #6b7280;
}

.system-status {
  background: #1a1f25;
  border-radius: 12px;
  padding: 20px;
}

.system-status h3 {
  color: #e7e9ea;
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 16px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #2a3038;
  border-radius: 8px;
  color: #e7e9ea;
  font-size: 14px;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.status-dot.online { background: #10b981; }
.status-dot.offline { background: #ef4444; }

.status-text {
  margin-left: auto;
  color: #6b7280;
  font-size: 12px;
}

@media (max-width: 768px) {
  .stats-grid, .charts-row, .status-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
