<template>
  <div class="dashboard">
    <aside class="sidebar">
      <div class="logo">
        <h2>🛡️ 跌倒检测</h2>
        <p>Fall Detection System</p>
      </div>

      <nav class="nav-menu">
        <router-link to="/dashboard" class="nav-item active">
          <span class="icon">📊</span>
          <span>仪表盘</span>
        </router-link>
        <router-link to="/cameras" class="nav-item">
          <span class="icon">📹</span>
          <span>摄像头管理</span>
        </router-link>
        <router-link to="/upload" class="nav-item">
          <span class="icon">📁</span>
          <span>文件上传</span>
        </router-link>
        <router-link to="/history" class="nav-item">
          <span class="icon">📋</span>
          <span>检测历史</span>
        </router-link>
        <router-link to="/statistics" class="nav-item">
          <span class="icon">📈</span>
          <span>数据统计</span>
        </router-link>
        <router-link to="/alerts" class="nav-item">
          <span class="icon">🔔</span>
          <span>告警中心</span>
        </router-link>
        <router-link to="/ai-assistant" class="nav-item">
          <span class="icon">🤖</span>
          <span>AI助手</span>
        </router-link>
        <router-link to="/settings" class="nav-item">
          <span class="icon">⚙️</span>
          <span>系统设置</span>
        </router-link>
      </nav>

      <div class="user-info">
        <div class="user-avatar">{{ user?.username?.[0]?.toUpperCase() || 'A' }}</div>
        <div class="user-details">
          <span class="user-name">{{ user?.username || 'Admin' }}</span>
          <span class="user-role">{{ user?.role === 'admin' ? '管理员' : '用户' }}</span>
        </div>
        <el-button text @click="handleLogout" title="退出登录">🚪</el-button>
      </div>
    </aside>

    <main class="main-content">
      <header class="content-header">
        <h1>实时监控</h1>
        <div class="header-actions">
          <el-tag :type="status === 'running' ? 'success' : 'danger'" size="large">
            {{ status === 'running' ? '🟢 系统运行中' : '🔴 系统离线' }}
          </el-tag>
          <el-tag type="warning" size="large" v-if="aiRisk > 0.5">
            ⚠️ 高风险告警
          </el-tag>
        </div>
      </header>

      <div class="content-body">
        <div class="main-panel">
          <div class="video-section">
            <div class="video-container">
              <video ref="videoEl" class="video-player" autoplay muted playsinline></video>
              <canvas ref="canvasEl" class="video-canvas"></canvas>
              <div v-if="!cameraActive" class="video-placeholder">
                <p>📹 点击"开启摄像头"开始实时检测</p>
                <p>或上传视频/图片文件进行分析</p>
              </div>
            </div>

            <div class="video-controls">
              <el-button type="primary" size="large" @click="toggleCamera">
                {{ cameraActive ? '🔴 关闭摄像头' : '🟢 开启摄像头' }}
              </el-button>
              <el-button size="large" @click="captureFrame">📸 截取当前帧</el-button>
              <el-button size="large" @click="saveSnapshot">💾 保存快照</el-button>
            </div>
          </div>

          <div class="detection-result" v-if="currentResult">
            <h3>检测结果</h3>
            <div class="result-grid">
              <div class="result-item">
                <span class="label">行为状态</span>
                <span class="value" :class="resultClass">{{ currentResult.detected_class }}</span>
              </div>
              <div class="result-item">
                <span class="label">置信度</span>
                <span class="value">{{ (currentResult.confidence * 100).toFixed(1) }}%</span>
              </div>
              <div class="result-item">
                <span class="label">重心下降(M1)</span>
                <span class="value">{{ currentResult.M1 ? '✓ 触发' : '✗ 未触发' }}</span>
              </div>
              <div class="result-item">
                <span class="label">身体倾斜(M2)</span>
                <span class="value">{{ currentResult.M2 ? '✓ 触发' : '✗ 未触发' }}</span>
              </div>
              <div class="result-item">
                <span class="label">轮廓变形(M3)</span>
                <span class="value">{{ currentResult.M3 ? '✓ 触发' : '✗ 未触发' }}</span>
              </div>
              <div class="result-item">
                <span class="label">跌倒判定</span>
                <span class="value" :class="currentResult.fall_detected ? 'danger' : ''">
                  {{ currentResult.fall_detected ? '⚠️ 跌倒' : '✓ 正常' }}
                </span>
              </div>
            </div>

            <div class="ai-analysis" v-if="currentResult.ai_analysis">
              <h4>🤖 AI分析</h4>
              <p>风险等级: <strong :class="currentResult.ai_analysis.risk_label === 'high' ? 'text-danger' : 'text-warning'">
                {{ currentResult.ai_analysis.risk_label === 'high' ? '高' : currentResult.ai_analysis.risk_label === 'medium' ? '中' : '低' }}
              </strong></p>
              <p>建议: {{ currentResult.ai_analysis.recommendation }}</p>
              <p v-if="currentResult.ai_analysis.pattern_detected">检测到模式: {{ currentResult.ai_analysis.pattern_detected }}</p>
            </div>
          </div>
        </div>

        <div class="side-panel">
          <div class="quick-stats">
            <h3>今日概览</h3>
            <div class="stat-cards">
              <div class="stat-card alert">
                <span class="stat-value">{{ stats.today_alerts || 0 }}</span>
                <span class="stat-label">今日告警</span>
              </div>
              <div class="stat-card warning">
                <span class="stat-value">{{ stats.warning_count || 0 }}</span>
                <span class="stat-label">疑似跌倒</span>
              </div>
              <div class="stat-card normal">
                <span class="stat-value">{{ stats.normal_count || 0 }}</span>
                <span class="stat-label">正常检测</span>
              </div>
            </div>
          </div>

          <div class="recent-alerts">
            <h3>最近告警</h3>
            <div class="alert-list">
              <div v-for="alert in recentAlerts" :key="alert.id" class="alert-item">
                <span class="alert-type">{{ alert.event_type }}</span>
                <span class="alert-time">{{ formatTime(alert.timestamp) }}</span>
              </div>
              <div v-if="recentAlerts.length === 0" class="no-alerts">暂无告警</div>
            </div>
          </div>

          <div class="model-status">
            <h3>模型状态</h3>
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="模型加载">
                <el-tag :type="hasModel ? 'success' : 'warning'">{{ hasModel ? '已加载' : '未加载' }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="AI风险等级">
                <el-tag :type="aiRisk > 0.6 ? 'danger' : aiRisk > 0.3 ? 'warning' : 'success'">
                  {{ aiRisk > 0.6 ? '高' : aiRisk > 0.3 ? '中' : '低' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="活跃摄像头">{{ activeCameras }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()
const videoEl = ref(null)
const canvasEl = ref(null)

const user = ref(null)
const cameraActive = ref(false)
const cameraStream = ref(null)
const currentResult = ref(null)
const hasModel = ref(false)
const aiRisk = ref(0)
const activeCameras = ref(0)
const status = ref('running')
const recentAlerts = ref([])

const stats = reactive({
  today_alerts: 0,
  warning_count: 0,
  normal_count: 0
})

let detectionInterval = null
let mediaRecorder = null

const resultClass = computed(() => {
  if (!currentResult.value) return ''
  if (currentResult.value.alert) return 'danger'
  if (currentResult.value.fall_detected) return 'warning'
  return 'success'
})

onMounted(async () => {
  const userData = sessionStorage.getItem('user')
  if (userData) {
    user.value = JSON.parse(userData)
  }

  await checkStatus()
  await fetchStats()
  await fetchRecentAlerts()

  setInterval(fetchStats, 10000)
  setInterval(fetchRecentAlerts, 5000)
})

onUnmounted(() => {
  stopCamera()
  if (detectionInterval) clearInterval(detectionInterval)
})

async function checkStatus() {
  try {
    const resp = await fetch('/api/status')
    const data = await resp.json()
    hasModel.value = data.has_model
    aiRisk.value = data.ai_risk_level || 0
    activeCameras.value = data.active_cameras || 0
    status.value = data.status
  } catch (e) {
    console.error('Status check error:', e)
  }
}

async function fetchStats() {
  try {
    const resp = await fetch('/api/statistics')
    const data = await resp.json()
    Object.assign(stats, data)
  } catch (e) {
    console.error('Stats error:', e)
  }
}

async function fetchRecentAlerts() {
  try {
    const resp = await fetch('/api/history?per_page=5')
    const data = await resp.json()
    recentAlerts.value = (data.items || []).filter(i => i.alert || i.fall_detected)
  } catch (e) {
    console.error('Alerts error:', e)
  }
}

async function toggleCamera() {
  if (cameraActive.value) {
    stopCamera()
  } else {
    await startCamera()
  }
}

async function startCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: 640, height: 480, facingMode: 'user' }
    })
    cameraStream.value = stream
    videoEl.value.srcObject = stream
    cameraActive.value = true

    const canvas = canvasEl.value
    const ctx = canvas.getContext('2d')

    detectionInterval = setInterval(async () => {
      if (!videoEl.value || videoEl.value.readyState < 2) return

      canvas.width = videoEl.value.videoWidth || 640
      canvas.height = videoEl.value.videoHeight || 480
      ctx.drawImage(videoEl.value, 0, 0)

      const frameData = canvas.toDataURL('image/jpeg', 0.8).split(',')[1]

      try {
        const resp = await fetch('/api/frame', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ frame: frameData })
        })
        const data = await resp.json()

        if (data.frame) {
          const img = new Image()
          img.onload = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height)
            ctx.drawImage(img, 0, 0)
          }
          img.src = 'data:image/jpeg;base64,' + data.frame
        }

        currentResult.value = data

        if (data.ai_analysis) {
          aiRisk.value = data.ai_analysis.risk_level || 0
        }
      } catch (e) {
        console.error('Detection error:', e)
      }
    }, 200)

    ElMessage.success('摄像头已开启')
  } catch (e) {
    ElMessage.error('无法访问摄像头: ' + e.message)
  }
}

function stopCamera() {
  if (cameraStream.value) {
    cameraStream.value.getTracks().forEach(track => track.stop())
    cameraStream.value = null
  }
  if (detectionInterval) {
    clearInterval(detectionInterval)
    detectionInterval = null
  }
  cameraActive.value = false
  ElMessage.info('摄像头已关闭')
}

function captureFrame() {
  if (!canvasEl.value) return
  const link = document.createElement('a')
  link.download = `capture_${Date.now()}.jpg`
  link.href = canvasEl.value.toDataURL('image/jpeg')
  link.click()
  ElMessage.success('帧已截取')
}

function saveSnapshot() {
  captureFrame()
  ElMessage.success('快照已保存')
}

function formatTime(timestamp) {
  if (!timestamp) return ''
  const d = new Date(timestamp)
  return d.toLocaleString('zh-CN')
}

function handleLogout() {
  sessionStorage.clear()
  router.push('/login')
}
</script>

<style scoped>
.dashboard {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 240px;
  background: #1a1f25;
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.logo h2 {
  color: #00d4ff;
  font-size: 18px;
  margin-bottom: 5px;
}

.logo p {
  color: #666;
  font-size: 11px;
}

.nav-menu {
  flex: 1;
  margin-top: 30px;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 12px 15px;
  color: #8899a6;
  text-decoration: none;
  border-radius: 8px;
  margin-bottom: 5px;
  transition: all 0.3s;
}

.nav-item:hover, .nav-item.router-link-active {
  background: #2f3336;
  color: #fff;
}

.nav-item.active {
  background: #00d4ff20;
  color: #00d4ff;
}

.nav-item .icon {
  margin-right: 10px;
  font-size: 18px;
}

.user-info {
  display: flex;
  align-items: center;
  padding: 15px;
  background: #2f3336;
  border-radius: 10px;
  gap: 10px;
}

.user-avatar {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
}

.user-details {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
}

.user-role {
  font-size: 11px;
  color: #888;
}

.main-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.content-header h1 {
  font-size: 24px;
  color: #fff;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.content-body {
  display: flex;
  gap: 20px;
}

.main-panel {
  flex: 2;
}

.side-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.video-section {
  background: #1a1f25;
  border-radius: 15px;
  padding: 20px;
}

.video-container {
  position: relative;
  background: #000;
  border-radius: 10px;
  overflow: hidden;
  min-height: 400px;
}

.video-player {
  width: 100%;
  display: block;
}

.video-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.video-placeholder {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #666;
}

.video-controls {
  display: flex;
  gap: 10px;
  margin-top: 15px;
  flex-wrap: wrap;
}

.detection-result {
  background: #1a1f25;
  border-radius: 15px;
  padding: 20px;
  margin-top: 20px;
}

.detection-result h3 {
  color: #fff;
  margin-bottom: 15px;
}

.result-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
}

.result-item {
  background: #2f3336;
  padding: 15px;
  border-radius: 10px;
}

.result-item .label {
  display: block;
  font-size: 12px;
  color: #888;
  margin-bottom: 5px;
}

.result-item .value {
  font-size: 16px;
  font-weight: 500;
  color: #fff;
}

.result-item .value.danger { color: #ff4757; }
.result-item .value.warning { color: #ffaa00; }
.result-item .value.success { color: #00ff88; }

.ai-analysis {
  margin-top: 20px;
  padding: 15px;
  background: #2f3336;
  border-radius: 10px;
  border-left: 4px solid #00d4ff;
}

.ai-analysis h4 {
  color: #00d4ff;
  margin-bottom: 10px;
}

.ai-analysis p {
  color: #ccc;
  margin: 5px 0;
  font-size: 14px;
}

.text-danger { color: #ff4757; }
.text-warning { color: #ffaa00; }

.side-panel > div {
  background: #1a1f25;
  border-radius: 15px;
  padding: 20px;
}

.side-panel h3 {
  color: #fff;
  font-size: 16px;
  margin-bottom: 15px;
}

.stat-cards {
  display: flex;
  gap: 10px;
}

.stat-card {
  flex: 1;
  padding: 15px;
  border-radius: 10px;
  text-align: center;
}

.stat-card.alert { background: linear-gradient(135deg, #ff4757, #ff6b81); }
.stat-card.warning { background: linear-gradient(135deg, #ffaa00, #ffbe00); }
.stat-card.normal { background: linear-gradient(135deg, #00ff88, #00cc6a); }

.stat-value {
  display: block;
  font-size: 28px;
  font-weight: bold;
  color: #fff;
}

.stat-label {
  font-size: 11px;
  color: rgba(255,255,255,0.8);
}

.alert-list {
  max-height: 200px;
  overflow-y: auto;
}

.alert-item {
  display: flex;
  justify-content: space-between;
  padding: 10px;
  background: #2f3336;
  border-radius: 8px;
  margin-bottom: 8px;
}

.alert-type {
  color: #ff4757;
  font-weight: 500;
}

.alert-time {
  color: #888;
  font-size: 12px;
}

.no-alerts {
  color: #666;
  text-align: center;
  padding: 20px;
}
</style>
