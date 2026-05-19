<template>
  <div class="dashboard">
    <aside class="sidebar">
      <div class="logo"><h2>🛡️ 跌倒检测</h2><p>Fall Detection System</p></div>
      <nav class="nav-menu">
        <router-link to="/dashboard" class="nav-item"><span class="icon">📊</span><span>仪表盘</span></router-link>
        <router-link to="/cameras" class="nav-item"><span class="icon">📹</span><span>摄像头管理</span></router-link>
        <router-link to="/upload" class="nav-item"><span class="icon">📁</span><span>文件上传</span></router-link>
        <router-link to="/history" class="nav-item active"><span class="icon">📋</span><span>检测历史</span></router-link>
        <router-link to="/statistics" class="nav-item"><span class="icon">📈</span><span>数据统计</span></router-link>
        <router-link to="/alerts" class="nav-item"><span class="icon">🔔</span><span>告警中心</span></router-link>
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
        <h1>检测历史</h1>
        <div class="header-actions">
          <el-select v-model="filterType" placeholder="筛选类型" clearable style="width: 150px;">
            <el-option label="全部" value="" />
            <el-option label="跌倒告警" value="跌倒告警" />
            <el-option label="疑似跌倒" value="疑似跌倒" />
            <el-option label="正常" value="正常" />
          </el-select>
          <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" />
          <el-button @click="fetchHistory">🔍 搜索</el-button>
          <el-button type="danger" @click="clearHistory">🗑️ 清空</el-button>
          <el-button @click="exportData">📥 导出</el-button>
        </div>
      </header>

      <div class="history-table">
        <el-table :data="historyList" stripe v-loading="loading" @row-click="viewDetail">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="timestamp" label="时间" width="180" :formatter="r => formatTime(r.timestamp)" />
          <el-table-column prop="event_type" label="事件类型" width="120">
            <template #default="{ row }">
              <el-tag :type="row.alert ? 'danger' : row.fall_detected ? 'warning' : 'success'">
                {{ row.event_type || '正常' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="detected_class" label="检测行为" width="120" />
          <el-table-column prop="confidence" label="置信度" width="100" :formatter="r => ((r.confidence || 0) * 100).toFixed(1) + '%'" />
          <el-table-column label="检测指标" width="200">
            <template #default="{ row }">
              <span class="indicator" :class="{ active: row.M1 }">M1</span>
              <span class="indicator" :class="{ active: row.M2 }">M2</span>
              <span class="indicator" :class="{ active: row.M3 }">M3</span>
            </template>
          </el-table-column>
          <el-table-column label="跌倒判定" width="100">
            <template #default="{ row }">
              <el-tag :type="row.fall_detected ? 'danger' : 'success'" size="small">
                {{ row.fall_detected ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button size="small" @click.stop="viewDetail(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination background layout="total, prev, pager, next" :total="total" v-model:current-page="currentPage" :page-size="pageSize" @current-change="fetchHistory" style="margin-top: 20px; justify-content: center;" />
      </div>

      <el-dialog v-model="showDetail" title="检测详情" width="600px">
        <div v-if="selectedRecord" class="detail-content">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="ID">{{ selectedRecord.id }}</el-descriptions-item>
            <el-descriptions-item label="时间">{{ formatTime(selectedRecord.timestamp) }}</el-descriptions-item>
            <el-descriptions-item label="事件类型">{{ selectedRecord.event_type }}</el-descriptions-item>
            <el-descriptions-item label="检测行为">{{ selectedRecord.detected_class }}</el-descriptions-item>
            <el-descriptions-item label="置信度">{{ ((selectedRecord.confidence || 0) * 100).toFixed(1) }}%</el-descriptions-item>
            <el-descriptions-item label="摄像头ID">{{ selectedRecord.camera_id || 'N/A' }}</el-descriptions-item>
            <el-descriptions-item label="重心下降(M1)">
              <el-tag :type="selectedRecord.M1 ? 'danger' : 'info'">{{ selectedRecord.M1 ? '触发' : '未触发' }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="身体倾斜(M2)">
              <el-tag :type="selectedRecord.M2 ? 'danger' : 'info'">{{ selectedRecord.M2 ? '触发' : '未触发' }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="轮廓变形(M3)">
              <el-tag :type="selectedRecord.M3 ? 'danger' : 'info'">{{ selectedRecord.M3 ? '触发' : '未触发' }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="跌倒判定">
              <el-tag :type="selectedRecord.fall_detected ? 'danger' : 'success'" size="large">
                {{ selectedRecord.fall_detected ? '跌倒' : '正常' }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </el-dialog>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()
const user = ref(sessionStorage.getItem('user') ? JSON.parse(sessionStorage.getItem('user')).username : 'Admin')
const historyList = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filterType = ref('')
const dateRange = ref(null)
const showDetail = ref(false)
const selectedRecord = ref(null)

onMounted(fetchHistory)

async function fetchHistory() {
  loading.value = true
  try {
    const params = new URLSearchParams({ page: currentPage.value, per_page: pageSize.value })
    if (filterType.value) params.append('event_type', filterType.value)
    if (dateRange.value && dateRange.value.length === 2) {
      params.append('start_date', dateRange.value[0])
      params.append('end_date', dateRange.value[1])
    }
    const resp = await fetch(`/api/history?${params}`)
    const data = await resp.json()
    historyList.value = data.items || []
    total.value = data.total || 0
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function viewDetail(row) {
  selectedRecord.value = row
  showDetail.value = true
}

async function clearHistory() {
  try {
    await fetch('/api/history/clear', { method: 'POST' })
    ElMessage.success('已清空')
    fetchHistory()
  } catch (e) {
    ElMessage.error('清空失败')
  }
}

function exportData() {
  const csv = ['ID,时间,事件类型,检测行为,置信度,M1,M2,M3,跌倒']
  historyList.value.forEach(r => {
    csv.push(`${r.id},${r.timestamp},${r.event_type},${r.detected_class},${(r.confidence || 0).toFixed(3)},${r.M1},${r.M2},${r.M3},${r.fall_detected}`)
  })
  const blob = new Blob(['\ufeff' + csv.join('\n')], { type: 'text/csv;charset=utf-8' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `detection_history_${Date.now()}.csv`
  link.click()
  ElMessage.success('导出成功')
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
.content-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 10px; }
.content-header h1 { font-size: 24px; color: #fff; }
.header-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.history-table { background: #1a1f25; border-radius: 15px; padding: 20px; }
.indicator { display: inline-block; padding: 2px 8px; margin: 0 3px; background: #2f3336; border-radius: 4px; font-size: 12px; color: #666; }
.indicator.active { background: #ff4757; color: #fff; }
</style>
