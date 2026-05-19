<template>
  <div class="dashboard">
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">📹</div>
        <div class="stat-info">
          <p class="stat-value">{{ stats.totalAnalyses }}</p>
          <p class="stat-label">分析次数</p>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">🔔</div>
        <div class="stat-info">
          <p class="stat-value">{{ stats.alertCount }}</p>
          <p class="stat-label">告警数量</p>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">⚠️</div>
        <div class="stat-info">
          <p class="stat-value">{{ stats.fallCount }}</p>
          <p class="stat-label">跌倒检测</p>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-info">
          <p class="stat-value">{{ stats.normalCount }}</p>
          <p class="stat-label">正常记录</p>
        </div>
      </div>
    </div>
    
    <div class="recent-section">
      <h3>最近分析记录</h3>
      <div class="record-list">
        <div 
          v-for="record in recentRecords" 
          :key="record.id" 
          class="record-item"
        >
          <div class="record-info">
            <p class="record-name">{{ record.original_filename }}</p>
            <p class="record-date">{{ formatDate(record.created_at) }}</p>
          </div>
          <div class="record-status" :class="record.status">
            {{ record.status === 'completed' ? '已完成' : record.status === 'processing' ? '处理中' : '失败' }}
          </div>
        </div>
        
        <div v-if="recentRecords.length === 0" class="empty-state">
          <p>暂无分析记录</p>
          <button class="upload-btn" @click="goToUpload">去上传视频</button>
        </div>
      </div>
    </div>
    
    <div class="quick-actions">
      <h3>快捷操作</h3>
      <div class="action-grid">
        <button class="action-btn" @click="goToUpload">
          <span class="action-icon">📹</span>
          <span class="action-text">上传视频</span>
        </button>
        <button class="action-btn" @click="goToCamera">
          <span class="action-icon">📷</span>
          <span class="action-text">摄像头检测</span>
        </button>
        <button class="action-btn" @click="goToAI">
          <span class="action-icon">🤖</span>
          <span class="action-text">AI助手</span>
        </button>
        <button class="action-btn" @click="goToHistory">
          <span class="action-icon">📋</span>
          <span class="action-text">查看记录</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const stats = ref({
  totalAnalyses: 0,
  alertCount: 0,
  fallCount: 0,
  normalCount: 0
})

const recentRecords = ref([])

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const goToUpload = () => {
  window.location.href = '/user/upload'
}

const goToCamera = () => {
  window.location.href = '/user/camera'
}

const goToAI = () => {
  window.location.href = '/user/ai-assistant'
}

const goToHistory = () => {
  window.location.href = '/user/history'
}

const fetchStats = async () => {
  try {
    const resp = await fetch('/api/statistics', { credentials: 'include' })
    const data = await resp.json()
    stats.value = {
      totalAnalyses: data.total_analyses || 0,
      alertCount: data.alert_count || 0,
      fallCount: data.fall_count || 0,
      normalCount: data.normal_count || 0
    }
  } catch (e) {
    console.error('获取统计数据失败', e)
  }
}

const fetchRecentRecords = async () => {
  try {
    const resp = await fetch('/api/analysis/records?per_page=5', { credentials: 'include' })
    const data = await resp.json()
    recentRecords.value = data.records || []
  } catch (e) {
    console.error('获取分析记录失败', e)
  }
}

onMounted(() => {
  fetchStats()
  fetchRecentRecords()
})
</script>

<style scoped>
.dashboard {
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
  color: #10b981;
  margin: 0;
}

.stat-label {
  font-size: 14px;
  color: #9ca3af;
  margin: 4px 0 0;
}

.recent-section, .quick-actions {
  background: #1a1f25;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}

.recent-section h3, .quick-actions h3 {
  color: #e7e9ea;
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 16px;
}

.record-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.record-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #2a3038;
  border-radius: 8px;
}

.record-info .record-name {
  color: #e7e9ea;
  font-size: 14px;
  margin: 0;
}

.record-info .record-date {
  color: #6b7280;
  font-size: 12px;
  margin: 4px 0 0;
}

.record-status {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.record-status.completed {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.record-status.processing {
  background: rgba(251, 191, 36, 0.1);
  color: #fbbf24;
}

.record-status.failed {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.empty-state {
  text-align: center;
  padding: 32px;
}

.empty-state p {
  color: #6b7280;
  margin: 0 0 16px;
}

.upload-btn {
  background: #10b981;
  color: white;
  padding: 10px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}

.action-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  background: #2a3038;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.2s;
}

.action-btn:hover {
  transform: translateY(-4px);
}

.action-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.action-text {
  color: #e7e9ea;
  font-size: 14px;
}

@media (max-width: 768px) {
  .stats-grid, .action-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
