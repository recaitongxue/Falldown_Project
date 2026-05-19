<template>
  <div class="alerts-page">
    <div class="filter-bar">
      <select class="filter-select" v-model="alertFilter">
        <option value="">全部</option>
        <option value="unacknowledged">未处理</option>
        <option value="acknowledged">已处理</option>
      </select>
      <button class="refresh-btn" @click="loadAlerts">🔄 刷新</button>
      <button 
        class="ack-all-btn" 
        @click="acknowledgeAll"
        :disabled="unacknowledgedCount === 0"
      >
        全部标为已处理
      </button>
    </div>
    
    <div class="alerts-list">
      <div 
        v-for="alert in filteredAlerts" 
        :key="alert.id" 
        class="alert-card"
        :class="{ acknowledged: alert.acknowledged, alert: alert.severity === 'high' }"
      >
        <div class="alert-header">
          <div class="alert-icon">
            {{ alert.severity === 'high' ? '🚨' : '⚠️' }}
          </div>
          <div class="alert-info">
            <p class="alert-title">{{ alert.title }}</p>
            <p class="alert-time">{{ formatDate(alert.timestamp) }}</p>
          </div>
          <div class="alert-status">
            <span v-if="alert.acknowledged" class="status-tag acknowledged">已处理</span>
            <span v-else class="status-tag pending">待处理</span>
          </div>
        </div>
        
        <div class="alert-body">
          <p>{{ alert.description }}</p>
        </div>
        
        <div class="alert-meta">
          <span class="meta-item">检测类型: {{ alert.detection_type }}</span>
          <span class="meta-item">置信度: {{ (alert.confidence * 100).toFixed(1) }}%</span>
        </div>
        
        <div class="alert-actions">
          <button 
            v-if="!alert.acknowledged"
            class="action-btn ack" 
            @click="acknowledgeAlert(alert.id)"
          >
            标为已处理
          </button>
        </div>
      </div>
      
      <div v-if="filteredAlerts.length === 0" class="empty-state">
        <p>{{ alertFilter === 'unacknowledged' ? '暂无未处理告警' : '暂无告警记录' }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const alerts = ref([])
const alertFilter = ref('')

const filteredAlerts = computed(() => {
  let result = [...alerts.value]
  
  if (alertFilter.value === 'unacknowledged') {
    result = result.filter(a => !a.acknowledged)
  } else if (alertFilter.value === 'acknowledged') {
    result = result.filter(a => a.acknowledged)
  }
  
  return result.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
})

const unacknowledgedCount = computed(() => {
  return alerts.value.filter(a => !a.acknowledged).length
})

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const loadAlerts = async () => {
  try {
    const resp = await fetch('/api/alerts', { credentials: 'include' })
    const data = await resp.json()
    alerts.value = data.alerts || []
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

onMounted(() => {
  loadAlerts()
})
</script>

<style scoped>
.alerts-page {
  padding: 24px;
}

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

.refresh-btn, .ack-all-btn {
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}

.refresh-btn {
  background: #2a3038;
  color: #e7e9ea;
}

.ack-all-btn {
  background: #10b981;
  color: white;
}

.ack-all-btn:disabled {
  background: #374151;
  cursor: not-allowed;
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

.alert-card.alert {
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

.alert-icon {
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
  margin: 0;
}

.alert-time {
  color: #6b7280;
  font-size: 12px;
  margin: 4px 0 0;
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

.alert-meta {
  display: flex;
  gap: 16px;
  margin-top: 12px;
}

.meta-item {
  color: #6b7280;
  font-size: 12px;
}

.alert-actions {
  margin-top: 16px;
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

.empty-state {
  text-align: center;
  padding: 48px;
  color: #6b7280;
}
</style>
