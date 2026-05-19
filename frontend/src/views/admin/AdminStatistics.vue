<template>
  <div class="admin-statistics-page">
    <div class="page-header">
      <h2>数据统计</h2>
      <div class="date-range">
        <select v-model="timeRange">
          <option value="7d">最近7天</option>
          <option value="30d">最近30天</option>
          <option value="90d">最近90天</option>
          <option value="all">全部</option>
        </select>
      </div>
    </div>
    
    <div class="stats-overview">
      <div class="overview-card">
        <div class="overview-header">
          <span class="overview-icon">👥</span>
          <span class="overview-title">用户统计</span>
        </div>
        <div class="overview-content">
          <div class="overview-item">
            <span class="overview-value">{{ statistics.total_users || 0 }}</span>
            <span class="overview-label">总用户数</span>
          </div>
          <div class="overview-item">
            <span class="overview-value">{{ statistics.admin_count || 0 }}</span>
            <span class="overview-label">管理员</span>
          </div>
          <div class="overview-item">
            <span class="overview-value">{{ statistics.user_count || 0 }}</span>
            <span class="overview-label">普通用户</span>
          </div>
        </div>
      </div>
      
      <div class="overview-card">
        <div class="overview-header">
          <span class="overview-icon">📊</span>
          <span class="overview-title">分析统计</span>
        </div>
        <div class="overview-content">
          <div class="overview-item">
            <span class="overview-value">{{ statistics.total_analyses || 0 }}</span>
            <span class="overview-label">总分析次数</span>
          </div>
          <div class="overview-item">
            <span class="overview-value">{{ statistics.success_rate || 0 }}%</span>
            <span class="overview-label">成功率</span>
          </div>
          <div class="overview-item">
            <span class="overview-value">{{ statistics.fall_rate || 0 }}%</span>
            <span class="overview-label">跌倒检出率</span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="charts-section">
      <div class="chart-card">
        <h3>每日分析次数趋势</h3>
        <div class="bar-chart">
          <div 
            v-for="(item, index) in dailyTrend" 
            :key="index" 
            class="bar-wrapper"
          >
            <div 
              class="bar" 
              :style="{ height: (item.count / maxDailyCount * 100) + '%' }"
            ></div>
            <span class="bar-label">{{ item.day }}</span>
          </div>
        </div>
      </div>
      
      <div class="chart-card">
        <h3>检测结果分布</h3>
        <div class="pie-section">
          <div class="pie-chart-large">
            <div class="pie-slice fall" :style="{ '--percentage': fallPercentage + '%' }"></div>
            <div class="pie-center">
              <span>{{ fallPercentage }}%</span>
              <span class="center-label">跌倒</span>
            </div>
          </div>
          <div class="pie-stats">
            <div class="pie-stat-item">
              <span class="stat-dot fall"></span>
              <span class="stat-value">{{ statistics.fall_count || 0 }}</span>
              <span class="stat-label">跌倒检测</span>
            </div>
            <div class="pie-stat-item">
              <span class="stat-dot normal"></span>
              <span class="stat-value">{{ statistics.normal_count || 0 }}</span>
              <span class="stat-label">正常行为</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="top-users-section">
      <h3>活跃用户排行</h3>
      <div class="top-users-list">
        <div 
          v-for="(user, index) in topUsers" 
          :key="user.id" 
          class="top-user-item"
        >
          <span class="rank" :class="'rank-' + (index + 1)">{{ index + 1 }}</span>
          <div class="user-info">
            <span class="user-name">{{ user.username }}</span>
            <span class="user-email">{{ user.email }}</span>
          </div>
          <div class="user-stats">
            <span class="user-analyses">{{ user.analysis_count }} 次分析</span>
          </div>
        </div>
        
        <div v-if="topUsers.length === 0" class="empty-state">
          <p>暂无数据</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const statistics = ref({
  total_users: 0,
  admin_count: 0,
  user_count: 0,
  total_analyses: 0,
  success_rate: 0,
  fall_rate: 0,
  fall_count: 0,
  normal_count: 0
})

const timeRange = ref('7d')
const dailyTrend = ref([])
const topUsers = ref([])

const maxDailyCount = computed(() => {
  const counts = dailyTrend.value.map(d => d.count)
  return Math.max(...counts, 1)
})

const fallPercentage = computed(() => {
  const total = statistics.value.fall_count + statistics.value.normal_count
  if (total === 0) return 0
  return ((statistics.value.fall_count / total) * 100).toFixed(1)
})

const loadStatistics = async () => {
  try {
    const resp = await fetch(`/api/statistics?range=${timeRange.value}`, { credentials: 'include' })
    const data = await resp.json()
    statistics.value = data
  } catch (e) {
    console.error('获取统计数据失败', e)
  }
}

const loadDailyTrend = async () => {
  try {
    const resp = await fetch(`/api/statistics/daily?range=${timeRange.value}`, { credentials: 'include' })
    const data = await resp.json()
    dailyTrend.value = data.data || []
  } catch (e) {
    console.error('获取每日趋势失败', e)
  }
}

const loadTopUsers = async () => {
  try {
    const resp = await fetch('/api/statistics/top-users', { credentials: 'include' })
    const data = await resp.json()
    topUsers.value = data.data || []
  } catch (e) {
    console.error('获取活跃用户失败', e)
  }
}

onMounted(() => {
  loadStatistics()
  loadDailyTrend()
  loadTopUsers()
})
</script>

<style scoped>
.admin-statistics-page {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h2 {
  color: #e7e9ea;
  font-size: 20px;
  margin: 0;
}

.date-range select {
  padding: 10px 16px;
  background: #1a1f25;
  border: 1px solid #38444d;
  border-radius: 8px;
  color: #e7e9ea;
  font-size: 14px;
}

.stats-overview {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.overview-card {
  background: #1a1f25;
  border-radius: 12px;
  padding: 20px;
}

.overview-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.overview-icon {
  font-size: 24px;
  margin-right: 12px;
}

.overview-title {
  color: #e7e9ea;
  font-size: 16px;
  font-weight: 600;
}

.overview-content {
  display: flex;
  justify-content: space-around;
}

.overview-item {
  text-align: center;
}

.overview-value {
  display: block;
  font-size: 28px;
  font-weight: 700;
  color: #8b5cf6;
}

.overview-label {
  font-size: 14px;
  color: #6b7280;
}

.charts-section {
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
  margin: 0 0 20px;
}

.bar-chart {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  height: 200px;
  padding-top: 20px;
}

.bar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.bar {
  width: 30px;
  background: linear-gradient(180deg, #8b5cf6, #6d28d9);
  border-radius: 4px 4px 0 0;
  min-height: 4px;
  transition: height 0.3s;
}

.bar-label {
  margin-top: 8px;
  color: #6b7280;
  font-size: 12px;
}

.pie-section {
  display: flex;
  align-items: center;
  justify-content: space-around;
}

.pie-chart-large {
  width: 180px;
  height: 180px;
  border-radius: 50%;
  background: conic-gradient(
    #ef4444 0% var(--percentage),
    #10b981 var(--percentage) 100%
  );
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pie-center {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: #1a1f25;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.pie-center span:first-child {
  font-size: 28px;
  font-weight: 700;
  color: #ef4444;
}

.center-label {
  font-size: 12px;
  color: #6b7280;
}

.pie-stats {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.pie-stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.stat-dot.fall { background: #ef4444; }
.stat-dot.normal { background: #10b981; }

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #e7e9ea;
}

.stat-label {
  color: #6b7280;
  font-size: 14px;
}

.top-users-section {
  background: #1a1f25;
  border-radius: 12px;
  padding: 20px;
}

.top-users-section h3 {
  color: #e7e9ea;
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 16px;
}

.top-users-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.top-user-item {
  display: flex;
  align-items: center;
  padding: 12px;
  background: #2a3038;
  border-radius: 8px;
}

.rank {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  margin-right: 12px;
}

.rank-1 { background: #fbbf24; color: #1a1f25; }
.rank-2 { background: #9ca3af; color: #1a1f25; }
.rank-3 { background: #d97706; color: #1a1f25; }

.user-info {
  flex: 1;
}

.user-name {
  display: block;
  color: #e7e9ea;
  font-size: 14px;
  font-weight: 500;
}

.user-email {
  color: #6b7280;
  font-size: 12px;
}

.user-stats {
  text-align: right;
}

.user-analyses {
  color: #8b5cf6;
  font-size: 14px;
  font-weight: 600;
}

.empty-state {
  text-align: center;
  padding: 24px;
  color: #6b7280;
}

@media (max-width: 768px) {
  .stats-overview, .charts-section {
    grid-template-columns: 1fr;
  }
}
</style>
