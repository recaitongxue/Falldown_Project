<template>
  <div class="admin-alerts-page">
    <div class="page-header">
      <h2>告警管理</h2>
      <button 
        class="ack-all-btn" 
        @click="acknowledgeAll"
        :disabled="unacknowledgedCount === 0"
      >
        全部标为已处理
      </button>
    </div>
    
    <div class="stats-row">
      <div class="stat-item">
        <span class="stat-value">{{ totalCount }}</span>
        <span class="stat-label">总告警</span>
      </div>
      <div class="stat-item warning">
        <span class="stat-value">{{ unacknowledgedCount }}</span>
        <span class="stat-label">待处理</span>
      </div>
      <div class="stat-item success">
        <span class="stat-value">{{ acknowledgedCount }}</span>
        <span class="stat-label">已处理</span>
      </div>
    </div>
    
    <div class="filter-bar">
      <select class="filter-select" v-model="severityFilter">
        <option value="">全部级别</option>
        <option value="high">高</option>
        <option value="medium">中</option>
        <option value="low">低</option>
      </select>
      <select class="filter-select" v-model="statusFilter">
        <option value="">全部状态</option>
        <option value="unacknowledged">待处理</option>
        <option value="acknowledged">已处理</option>
      </select>
      <button class="refresh-btn" @click="loadAlerts">🔄 刷新</button>
    </div>
    
    <div class="alerts-list">
      <div 
        v-for="alert in filteredAlerts" 
        :key="alert.id" 
        class="alert-card"
        :class="{ acknowledged: alert.acknowledged, high: alert.severity === 'high' }"
      >
        <div class="alert-header">
          <div class="alert-severity">
            <span :class="alert.severity">{{ alert.severity === 'high' ? '🚨' : alert.severity === 'medium' ? '⚠️' : 'ℹ️' }}</span>
          </div>
          <div class="alert-info">
            <p class="alert-title">{{ alert.title }}</p>
            <p class="alert-meta">
              用户: {{ alert.username }} | 
              类型: {{ alert.detection_type }} | 
              置信度: {{ (alert.confidence * 100).toFixed(1) }}%
            </p>
          </div>
          <div class="alert-status">
            <span v-if="alert.acknowledged" class="status-tag acknowledged">已处理</span>
            <span v-else class="status-tag pending">待处理</span>
          </div>
        </div>
        
        <div class="alert-body">
          <p>{{ alert.description }}</p>
        </div>
        
        <div class="alert-footer">
          <span class="alert-time">{{ formatDate(alert.timestamp) }}</span>
          <div class="alert-actions">
            <button 
              v-if="!alert.acknowledged"
              class="action-btn ack" 
              @click="acknowledgeAlert(alert.id)"
            >
              标为已处理
            </button>
            <button class="action-btn view" @click="viewDetails(alert)">
              查看详情
            </button>
          </div>
        </div>
      </div>
      
      <div v-if="filteredAlerts.length === 0" class="empty-state">
        <p>暂无告警记录</p>
      </div>
    </div>
    
    <!-- 详情弹窗 -->
    <div v-if="viewingAlert" class="modal-overlay" @click.self="closeDetails">
      <div class="modal large">
        <div class="modal-header">
          <h3>告警详情</h3>
          <button class="close-btn" @click="closeDetails">×</button>
        </div>
        <div class="modal-body">
          <div class="detail-grid">
            <div class="detail-item">
              <label>告警标题</label>
              <span>{{ viewingAlert.title }}</span>
            </div>
            <div class="detail-item">
              <label>严重级别</label>
              <span :class="viewingAlert.severity">{{ viewingAlert.severity === 'high' ? '高' : viewingAlert.severity === 'medium' ? '中' : '低' }}</span>
            </div>
            <div class="detail-item">
              <label>检测类型</label>
              <span>{{ viewingAlert.detection_type }}</span>
            </div>
            <div class="detail-item">
              <label>置信度</label>
              <span>{{ (viewingAlert.confidence * 100).toFixed(1) }}%</span>
            </div>
            <div class="detail-item">
              <label>用户名</label>
              <span>{{ viewingAlert.username }}</span>
            </div>
            <div class="detail-item">
              <label>状态</label>
              <span>{{ viewingAlert.acknowledged ? '已处理' : '待处理' }}</span>
            </div>
            <div class="detail-item">
              <label>告警时间</label>
              <span>{{ formatDate(viewingAlert.timestamp) }}</span>
            </div>
            <div class="detail-item">
              <label>处理时间</label>
              <span>{{ viewingAlert.acknowledged_at ? formatDate(viewingAlert.acknowledged_at) : '-' }}</span>
            </div>
          </div>
          <div class="description-section">
            <label>描述</label>
            <p>{{ viewingAlert.description }}</p>
          </div>
        </div>
        <div class="modal-footer">
          <button class="cancel-btn" @click="closeDetails">关闭</button>
          <button 
            v-if="!viewingAlert.acknowledged"
            class="submit-btn" 
            @click="acknowledgeAlert(viewingAlert.id)"
          >
            标为已处理
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const alerts = ref([])
const severityFilter = ref('')
const statusFilter = ref('')
const viewingAlert = ref(null)

const totalCount = computed(() => alerts.value.length)
const unacknowledgedCount = computed(() => alerts.value.filter(a => !a.acknowledged).length)
const acknowledgedCount = computed(() => alerts.value.filter(a => a.acknowledged).length)

const filteredAlerts = computed(() => {
  let result = [...alerts.value]
  
  if (severityFilter.value) {
    result = result.filter(a => a.severity === severityFilter.value)
  }
  
  if (statusFilter.value === 'unacknowledged') {
    result = result.filter(a => !a.acknowledged)
  } else if (statusFilter.value === 'acknowledged') {
    result = result.filter(a => a.acknowledged)
  }
  
  return result.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
})

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const loadAlerts = async () => {
  try {
    const resp = await fetch('/api/alerts/all', { credentials: 'include' })
    const data = await resp.json()
    alerts.value = data.data || []
  } catch (e) {
    console.error('获取告警失败', e)
  }
}

const acknowledgeAlert = async (id) => {
  try {
    const resp = await fetch(`/api/alerts/${id}/acknowledge`, {
      method: 'POST',
      credentials: 'include'
    })
    if (resp.ok) {
      loadAlerts()
      if (viewingAlert.value && viewingAlert.value.id === id) {
        viewingAlert.value.acknowledged = true
      }
    }
  } catch (e) {
    console.error('处理告警失败', e)
  }
}

const acknowledgeAll = async () => {
  const unacknowledged = alerts.value.filter(a => !a.acknowledged)
  for (const alert of unacknowledged) {
    await acknowledgeAlert(alert.id)
  }
}

const viewDetails = (alert) => {
  viewingAlert.value = alert
}

const closeDetails = () => {
  viewingAlert.value = null
}

onMounted(() => {
  loadAlerts()
})
</script>

<style scoped>
.admin-alerts-page {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  color: #e7e9ea;
  font-size: 20px;
  margin: 0;
}

.ack-all-btn {
  padding: 10px 20px;
  background: #10b981;
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 14px;
  cursor: pointer;
}

.ack-all-btn:disabled {
  background: #374151;
  cursor: not-allowed;
}

.stats-row {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.stat-item {
  flex: 1;
  background: #1a1f25;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
}

.stat-item .stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #e7e9ea;
  display: block;
}

.stat-item .stat-label {
  font-size: 14px;
  color: #6b7280;
}

.stat-item.warning .stat-value { color: #fbbf24; }
.stat-item.success .stat-value { color: #10b981; }

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.filter-select {
  padding: 12px;
  background: #1a1f25;
  border: 1px solid #38444d;
  border-radius: 8px;
  color: #e7e9ea;
  font-size: 14px;
}

.refresh-btn {
  padding: 12px 20px;
  background: #2a3038;
  border: none;
  border-radius: 8px;
  color: #e7e9ea;
  font-size: 14px;
  cursor: pointer;
}

.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.alert-card {
  background: #1a1f25;
  border-radius: 12px;
  padding: 20px;
  border-left: 4px solid #fbbf24;
}

.alert-card.high {
  border-left-color: #ef4444;
  background: linear-gradient(90deg, rgba(239, 68, 68, 0.1), #1a1f25);
}

.alert-card.acknowledged {
  opacity: 0.6;
}

.alert-header {
  display: flex;
  align-items: center;
}

.alert-severity {
  font-size: 28px;
  margin-right: 12px;
}

.alert-info {
  flex: 1;
}

.alert-title {
  color: #e7e9ea;
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 4px;
}

.alert-meta {
  color: #6b7280;
  font-size: 12px;
  margin: 0;
}

.status-tag {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.status-tag.pending {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.status-tag.acknowledged {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.alert-body {
  margin-top: 12px;
}

.alert-body p {
  color: #9ca3af;
  margin: 0;
  line-height: 1.6;
}

.alert-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #2a3038;
}

.alert-time {
  color: #6b7280;
  font-size: 12px;
}

.alert-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}

.action-btn.ack {
  background: #10b981;
  color: white;
}

.action-btn.view {
  background: #3b82f6;
  color: white;
}

.empty-state {
  text-align: center;
  padding: 48px;
  color: #6b7280;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: #1a1f25;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
}

.modal.large {
  max-width: 800px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #2a3038;
}

.modal-header h3 {
  color: #e7e9ea;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  color: #9ca3af;
  font-size: 24px;
  cursor: pointer;
}

.modal-body {
  padding: 20px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.detail-item {
  padding: 12px;
  background: #2a3038;
  border-radius: 8px;
}

.detail-item label {
  display: block;
  color: #6b7280;
  font-size: 12px;
  margin-bottom: 4px;
}

.detail-item span {
  color: #e7e9ea;
  font-size: 14px;
}

.detail-item span.high { color: #ef4444; }
.detail-item span.medium { color: #fbbf24; }
.detail-item span.low { color: #3b82f6; }

.description-section {
  margin-top: 16px;
}

.description-section label {
  display: block;
  color: #6b7280;
  font-size: 12px;
  margin-bottom: 8px;
}

.description-section p {
  color: #e7e9ea;
  line-height: 1.6;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid #2a3038;
}

.cancel-btn {
  padding: 10px 20px;
  background: #2a3038;
  border: none;
  border-radius: 8px;
  color: #e7e9ea;
  font-size: 14px;
  cursor: pointer;
}

.submit-btn {
  padding: 10px 20px;
  background: #10b981;
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 14px;
  cursor: pointer;
}
</style>
