<template>
  <div class="history-page">
    <div class="filter-bar">
      <input 
        type="text" 
        class="search-input" 
        placeholder="搜索文件名..." 
        v-model="searchQuery"
      >
      <select class="filter-select" v-model="statusFilter">
        <option value="">全部状态</option>
        <option value="completed">已完成</option>
        <option value="processing">处理中</option>
        <option value="failed">失败</option>
      </select>
      <button class="refresh-btn" @click="loadRecords">🔄 刷新</button>
    </div>
    
    <div class="records-table">
      <table>
        <thead>
          <tr>
            <th>文件名</th>
            <th>状态</th>
            <th>检测结果</th>
            <th>告警次数</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="record in filteredRecords" :key="record.id">
            <td>
              <span class="file-icon">📹</span>
              <span class="filename">{{ record.original_filename }}</span>
            </td>
            <td>
              <span class="status-badge" :class="record.status">
                {{ record.status === 'completed' ? '已完成' : record.status === 'processing' ? '处理中' : '失败' }}
              </span>
            </td>
            <td>
              <span class="result-badge" :class="{ fall: record.fall_detected }">
                {{ record.fall_detected ? '⚠️ 跌倒' : '✅ 正常' }}
              </span>
            </td>
            <td>{{ record.alert_count }}</td>
            <td>{{ formatDate(record.created_at) }}</td>
            <td class="actions">
              <button 
                class="action-btn view" 
                @click="viewRecord(record)"
                :disabled="record.status !== 'completed'"
              >
                查看
              </button>
              <button 
                class="action-btn delete" 
                @click="deleteRecord(record.id)"
              >
                删除
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      
      <div v-if="filteredRecords.length === 0" class="empty-state">
        <p>暂无分析记录</p>
      </div>
    </div>
    
    <div class="pagination" v-if="totalRecords > perPage">
      <button 
        class="page-btn" 
        :disabled="currentPage === 1"
        @click="changePage(-1)"
      >
        上一页
      </button>
      <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页</span>
      <button 
        class="page-btn" 
        :disabled="currentPage === totalPages"
        @click="changePage(1)"
      >
        下一页
      </button>
    </div>
    
    <!-- 查看详情弹窗 -->
    <div v-if="viewingRecord" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <h3>分析详情</h3>
          <button class="close-btn" @click="closeModal">×</button>
        </div>
        <div class="modal-body">
          <div class="detail-section">
            <p><strong>文件名:</strong> {{ viewingRecord.original_filename }}</p>
            <p><strong>状态:</strong> {{ viewingRecord.status === 'completed' ? '已完成' : viewingRecord.status === 'processing' ? '处理中' : '失败' }}</p>
            <p><strong>总帧数:</strong> {{ viewingRecord.total_frames }}</p>
            <p><strong>检测帧数:</strong> {{ viewingRecord.detected_frames }}</p>
            <p><strong>跌倒检测:</strong> {{ viewingRecord.fall_detected ? '是' : '否' }}</p>
            <p><strong>告警次数:</strong> {{ viewingRecord.alert_count }}</p>
          </div>
          
          <div v-if="viewingRecord.processed_filename" class="video-section">
            <h4>分析结果视频</h4>
            <video controls class="modal-video">
              <source :src="getVideoUrl(viewingRecord)" type="video/mp4">
              您的浏览器不支持视频播放
            </video>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const records = ref([])
const searchQuery = ref('')
const statusFilter = ref('')
const currentPage = ref(1)
const perPage = ref(10)
const totalRecords = ref(0)
const viewingRecord = ref(null)

const filteredRecords = computed(() => {
  return records.value.filter(record => {
    const matchSearch = !searchQuery.value || 
      record.original_filename.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchStatus = !statusFilter.value || record.status === statusFilter.value
    return matchSearch && matchStatus
  })
})

const totalPages = computed(() => Math.ceil(totalRecords.value / perPage.value))

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const userInfo = ref(sessionStorage.getItem('user') ? JSON.parse(sessionStorage.getItem('user')) : null)
const userId = ref(userInfo.value?.id || 1)

const loadRecords = async () => {
  try {
    const resp = await fetch(`/api/analysis/records?page=${currentPage.value}&per_page=${perPage.value}`, { 
      credentials: 'include',
      headers: {
        'X-User-Id': userId.value
      }
    })
    const data = await resp.json()
    records.value = data.records || []
    totalRecords.value = data.total || 0
  } catch (e) {
    console.error('获取记录失败', e)
  }
}

const changePage = (delta) => {
  const newPage = currentPage.value + delta
  if (newPage >= 1 && newPage <= totalPages.value) {
    currentPage.value = newPage
    loadRecords()
  }
}

const viewRecord = (record) => {
  viewingRecord.value = record
}

const closeModal = () => {
  viewingRecord.value = null
}

const getVideoUrl = (record) => {
  if (!record.processed_filename) return ''
  return `/api/download/video/${encodeURIComponent(record.processed_filename)}`
}

const deleteRecord = async (id) => {
  if (!confirm('确定要删除这条记录吗？')) return
  
  try {
    const resp = await fetch(`/api/analysis/record/${id}`, {
      method: 'DELETE',
      credentials: 'include'
    })
    const data = await resp.json()
    if (resp.ok) {
      alert('删除成功')
      loadRecords()
    } else {
      alert('删除失败: ' + (data.error || '未知错误'))
    }
  } catch (e) {
    console.error('删除失败', e)
    alert('删除失败')
  }
}

onMounted(() => {
  loadRecords()
})
</script>

<style scoped>
.history-page {
  padding: 24px;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.search-input {
  flex: 1;
  padding: 12px;
  background: #1a1f25;
  border: 1px solid #38444d;
  border-radius: 8px;
  color: #e7e9ea;
  font-size: 14px;
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

.records-table {
  background: #1a1f25;
  border-radius: 12px;
  overflow: hidden;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead tr {
  background: #2a3038;
}

th {
  text-align: left;
  padding: 16px;
  color: #9ca3af;
  font-size: 14px;
  font-weight: 600;
}

td {
  padding: 16px;
  border-bottom: 1px solid #2a3038;
  color: #e7e9ea;
}

.file-icon {
  margin-right: 8px;
}

.filename {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.status-badge.completed {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.status-badge.processing {
  background: rgba(251, 191, 36, 0.1);
  color: #fbbf24;
}

.status-badge.failed {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.result-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.result-badge.fall {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}

.action-btn.view {
  background: #10b981;
  color: white;
}

.action-btn.view:disabled {
  background: #374151;
  cursor: not-allowed;
}

.action-btn.delete {
  background: #ef4444;
  color: white;
}

.empty-state {
  text-align: center;
  padding: 48px;
  color: #6b7280;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
}

.page-btn {
  padding: 8px 16px;
  background: #2a3038;
  border: none;
  border-radius: 8px;
  color: #e7e9ea;
  font-size: 14px;
  cursor: pointer;
}

.page-btn:disabled {
  background: #1a1f25;
  color: #6b7280;
  cursor: not-allowed;
}

.page-info {
  color: #9ca3af;
  font-size: 14px;
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
  max-width: 800px;
  max-height: 80vh;
  overflow: auto;
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

.detail-section p {
  color: #e7e9ea;
  margin: 8px 0;
}

.video-section h4 {
  color: #e7e9ea;
  margin: 20px 0 12px;
}

.modal-video {
  width: 100%;
  max-height: 400px;
  border-radius: 8px;
}
</style>
