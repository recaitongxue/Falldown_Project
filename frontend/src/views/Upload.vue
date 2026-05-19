<template>
  <div class="dashboard">
    <aside class="sidebar">
      <div class="logo"><h2>🛡️ 跌倒检测</h2><p>Fall Detection System</p></div>
      <nav class="nav-menu">
        <router-link to="/dashboard" class="nav-item"><span class="icon">📊</span><span>仪表盘</span></router-link>
        <router-link to="/cameras" class="nav-item"><span class="icon">📹</span><span>摄像头管理</span></router-link>
        <router-link to="/upload" class="nav-item active"><span class="icon">📁</span><span>文件上传</span></router-link>
        <router-link to="/history" class="nav-item"><span class="icon">📋</span><span>检测历史</span></router-link>
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
        <h1>文件上传分析</h1>
        <div class="header-actions">
          <el-button type="primary" @click="triggerBatchUpload">📦 批量上传</el-button>
          <el-button @click="generateReport">📝 生成报告</el-button>
        </div>
      </header>

      <div class="upload-container">
        <div class="tabs-wrapper">
          <el-tabs v-model="activeTab" type="card">
            <el-tab-pane label="视频上传" name="video">
              <div class="upload-area" @click="triggerFileInput('video')" @drop.prevent="handleDrop('video', $event)" @dragover.prevent>
                <div class="upload-icon">🎬</div>
                <p>点击或拖拽视频文件到此处</p>
                <p class="hint">支持 MP4, AVI, MOV, MKV 格式</p>
              </div>
              <input ref="videoInput" type="file" accept="video/*" class="hidden-input" @change="handleFileSelect('video', $event)" />
            </el-tab-pane>
            <el-tab-pane label="图片上传" name="image">
              <div class="upload-area" @click="triggerFileInput('image')" @drop.prevent="handleDrop('image', $event)" @dragover.prevent>
                <div class="upload-icon">🖼️</div>
                <p>点击或拖拽图片文件到此处</p>
                <p class="hint">支持 JPG, PNG, BMP 格式</p>
              </div>
              <input ref="imageInput" type="file" accept="image/*" class="hidden-input" @change="handleFileSelect('image', $event)" />
            </el-tab-pane>
          </el-tabs>
        </div>

        <div v-if="selectedFile" class="file-info">
          <el-card>
            <div class="file-header">
              <span class="file-name">{{ selectedFile.name }}</span>
              <span class="file-size">{{ formatSize(selectedFile.size) }}</span>
              <el-button text @click="clearSelection">✕</el-button>
            </div>
          </el-card>
        </div>

        <div v-if="analyzing" class="analysis-progress">
          <el-card>
            <div class="progress-header">
              <span>🔄 正在分析中...</span>
              <el-progress :percentage="analysisProgress" :stroke-width="8" />
            </div>
            <p class="progress-info">{{ analysisInfo }}</p>
          </el-card>
        </div>

        <div v-if="analysisResults.length > 0" class="analysis-results">
          <div v-if="outputVideoPath" class="video-preview">
            <el-card>
              <h3>🎬 分析结果视频</h3>
              <div class="video-container">
                <video 
                  ref="videoPlayer"
                  controls 
                  class="preview-video" 
                  :src="outputVideoPath"
                  preload="metadata"
                  playsinline
                  @error="handleVideoError"
                  @loadedmetadata="handleVideoLoaded"
                >
                  您的浏览器不支持视频播放
                </video>
                <div v-if="videoLoading" class="video-loading">
                  <el-spinner size="large" />
                  <p>正在加载视频...</p>
                </div>
              </div>
              <div class="video-actions">
                <el-button type="primary" @click="downloadVideo">📥 下载分析视频</el-button>
                <el-button @click="reloadVideo" :loading="videoLoading">🔄 重新加载</el-button>
              </div>
            </el-card>
          </div>
          
          <div class="results-summary">
            <el-card>
              <h3>📊 分析摘要</h3>
              <div class="summary-grid">
                <div class="summary-item">
                  <span class="summary-value">{{ summaryStats.total.value }}</span>
                  <span class="summary-label">{{ summaryStats.total.label }}</span>
                </div>
                <div class="summary-item highlight">
                  <span class="summary-value">{{ summaryStats.fallCount.value }}</span>
                  <span class="summary-label">{{ summaryStats.fallCount.label }}</span>
                </div>
                <div class="summary-item">
                  <span class="summary-value">{{ summaryStats.maxConfidence.value }}</span>
                  <span class="summary-label">{{ summaryStats.maxConfidence.label }}</span>
                </div>
              </div>
            </el-card>

            <el-card v-if="aiAnalysis" class="ai-analysis">
              <h3>🤖 AI 风险分析</h3>
              <div class="risk-display">
                <div class="risk-bar">
                  <div class="risk-fill" :class="aiAnalysis.risk_label" :style="{ width: (aiAnalysis.risk_level * 100) + '%' }"></div>
                </div>
                <div class="risk-info">
                  <span class="risk-label" :class="aiAnalysis.risk_label">
                    {{ aiAnalysis.risk_label === 'high' ? '高风险' : aiAnalysis.risk_label === 'medium' ? '中风险' : '低风险' }}
                  </span>
                  <span class="risk-value">{{ (aiAnalysis.risk_level * 100).toFixed(1) }}%</span>
                </div>
                <div v-if="aiAnalysis.recommendations && aiAnalysis.recommendations.length" class="recommendations">
                  <h4>💡 建议</h4>
                  <ul>
                    <li v-for="(rec, idx) in aiAnalysis.recommendations" :key="idx">{{ rec }}</li>
                  </ul>
                </div>
              </div>
            </el-card>
          </div>

          <div class="results-table">
            <el-card>
              <h3>📋 检测详情</h3>
              <el-table :data="analysisResults" stripe :max-height="400">
                <el-table-column prop="frame_idx" label="帧序号" width="100" />
                <el-table-column prop="timestamp" label="时间戳" width="120" />
                <el-table-column prop="detected_class" label="检测类别" />
                <el-table-column prop="confidence" label="置信度" width="120">
                  <template #default="{ row }">
                    <el-progress :percentage="(row.confidence * 100).toFixed(0)" :stroke-width="6" />
                  </template>
                </el-table-column>
                <el-table-column prop="fall_detected" label="跌倒检测" width="100">
                  <template #default="{ row }">
                    <el-tag :type="row.fall_detected ? 'danger' : 'success'">{{ row.fall_detected ? '是' : '否' }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="ai_risk" label="AI风险" width="120">
                  <template #default="{ row }">
                    <el-progress :percentage="(row.ai_risk * 100).toFixed(0)" :stroke-width="6" />
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </div>
        </div>

        <div v-if="batchMode" class="batch-section">
          <el-card>
            <h3>📦 批量上传</h3>
            <input ref="batchInput" type="file" accept="video/*,image/*" class="hidden-input" multiple @change="handleBatchSelect" />
            <div class="batch-upload-area" @click="triggerBatchInput" @drop.prevent="handleBatchDrop" @dragover.prevent>
              <div class="upload-icon">📁</div>
              <p>点击或拖拽多个文件到此处</p>
              <p class="hint">支持视频和图片文件</p>
            </div>
            <div v-if="batchFiles.length > 0" class="batch-files">
              <h4>待处理文件 ({{ batchFiles.length }})</h4>
              <el-list :data="batchFiles" :border="false">
                <el-list-item v-for="(file, idx) in batchFiles" :key="idx">
                  <span>{{ file.name }}</span>
                  <span class="file-size">{{ formatSize(file.size) }}</span>
                  <el-button text @click="removeBatchFile(idx)">✕</el-button>
                </el-list-item>
              </el-list>
              <el-button type="primary" @click="processBatch">开始批量分析</el-button>
            </div>
          </el-card>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()
const user = ref(sessionStorage.getItem('user') ? JSON.parse(sessionStorage.getItem('user')).username : 'Admin')
const activeTab = ref('video')
const selectedFile = ref(null)
const analyzing = ref(false)
const analysisProgress = ref(0)
const analysisInfo = ref('')
const analysisResults = ref([])
const videoInput = ref(null)
const imageInput = ref(null)
const batchInput = ref(null)
const batchMode = ref(false)
const batchFiles = ref([])
const aiAnalysis = ref(null)
const outputVideoPath = ref(null)
const videoPlayer = ref(null)
const videoLoading = ref(false)

const summaryStats = reactive({
  total: { label: '总帧数', value: 0 },
  fallCount: { label: '跌倒帧数', value: 0 },
  maxConfidence: { label: '最高置信度', value: '0%' }
})

function triggerFileInput(type) {
  if (type === 'video') videoInput.value.click()
  else imageInput.value.click()
}

function triggerBatchInput() {
  batchInput.value.click()
}

function handleFileSelect(type, event) {
  const file = event.target.files[0]
  if (!file) return
  batchMode.value = false
  selectedFile.value = file
  processFile(file, type)
}

function handleDrop(type, event) {
  const file = event.dataTransfer.files[0]
  if (!file) return
  batchMode.value = false
  selectedFile.value = file
  processFile(file, type)
}

function handleBatchSelect(event) {
  const files = Array.from(event.target.files)
  batchFiles.value = [...batchFiles.value, ...files]
}

function handleBatchDrop(event) {
  const files = Array.from(event.dataTransfer.files)
  batchFiles.value = [...batchFiles.value, ...files]
}

function removeBatchFile(idx) {
  batchFiles.value.splice(idx, 1)
}

function clearSelection() {
  selectedFile.value = null
  analysisResults.value = []
  aiAnalysis.value = null
}

async function processFile(file, type) {
  const validVideo = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-matroska', 'video/webm']
  const validImage = ['image/jpeg', 'image/png', 'image/bmp', 'image/jpg']

  const fileType = file.type.toLowerCase()
  const isValidVideo = validVideo.some(v => fileType.includes(v.split('/')[1]))
  const isValidImage = validImage.some(v => fileType.includes(v.split('/')[1]))

  if (type === 'video' && !isValidVideo) {
    ElMessage.error('请上传有效的视频文件 (MP4, AVI, MOV, MKV)')
    return
  }
  if (type === 'image' && !isValidImage) {
    ElMessage.error('请上传有效的图片文件 (JPG, PNG, BMP)')
    return
  }

  analyzing.value = true
  analysisProgress.value = 0
  analysisInfo.value = '正在上传文件...'
  analysisResults.value = []
  aiAnalysis.value = null

  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('type', type)

    const uploadResp = await fetch('/api/upload', { method: 'POST', body: formData })
    const uploadData = await uploadResp.json()

    if (uploadData.status !== 'ok') {
      throw new Error(uploadData.error || '上传失败')
    }

    analysisProgress.value = 30
    analysisInfo.value = '正在分析文件...'

    const detectResp = await fetch('/api/detect/file', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filepath: uploadData.filepath, file_type: type })
    })
    const detectData = await detectResp.json()

    if (detectData.status === 'ok') {
      analysisResults.value = detectData.results || []
      aiAnalysis.value = detectData.ai_analysis || null
      if (detectData.output_video) {
        // 提取文件名，处理 Windows 路径格式
        const path = detectData.output_video
        const filename = path.replace(/\\/g, '/').split('/').pop()
        outputVideoPath.value = `/api/video/stream/${encodeURIComponent(filename)}`
      } else {
        outputVideoPath.value = null
      }
      updateSummary()
      analysisProgress.value = 100
      analysisInfo.value = '分析完成'
      ElMessage.success(`分析完成，共处理 ${analysisResults.value.length} 帧`)
    } else {
      throw new Error(detectData.error || '分析失败')
    }
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    analyzing.value = false
  }
}

async function processBatch() {
  if (batchFiles.value.length === 0) {
    ElMessage.warning('请选择要处理的文件')
    return
  }

  analyzing.value = true
  analysisProgress.value = 0
  analysisInfo.value = '正在批量上传...'

  try {
    const formData = new FormData()
    batchFiles.value.forEach(file => {
      formData.append('files', file)
    })

    const uploadResp = await fetch('/api/upload/batch', { method: 'POST', body: formData })
    const uploadData = await uploadResp.json()

    if (uploadData.status !== 'ok') {
      throw new Error('批量上传失败')
    }

    analysisProgress.value = 50
    analysisInfo.value = '正在批量分析...'

    for (let i = 0; i < uploadData.results.length; i++) {
      const result = uploadData.results[i]
      if (result.status === 'uploaded') {
        const detectResp = await fetch('/api/detect/file', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ filepath: result.filepath, file_type: result.file_type })
        })
        const detectData = await detectResp.json()
        
        if (detectData.results) {
          analysisResults.value = [...analysisResults.value, ...detectData.results]
        }
        if (detectData.ai_analysis) {
          aiAnalysis.value = detectData.ai_analysis
        }
      }
      analysisProgress.value = 50 + ((i + 1) / uploadData.results.length) * 50
    }

    updateSummary()
    analysisProgress.value = 100
    analysisInfo.value = '批量分析完成'
    ElMessage.success(`批量分析完成，共处理 ${analysisResults.value.length} 帧`)
    
    batchFiles.value = []
    batchMode.value = false
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    analyzing.value = false
  }
}

function triggerBatchUpload() {
  batchMode.value = !batchMode.value
}

async function generateReport() {
  if (analysisResults.value.length === 0) {
    ElMessage.warning('请先进行文件分析')
    return
  }

  try {
    const resp = await fetch('/api/report/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: 'custom' })
    })
    const report = await resp.json()
    
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `detection_report_${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    
    ElMessage.success('报告已下载')
  } catch (e) {
    ElMessage.error('生成报告失败')
  }
}

function updateSummary() {
  summaryStats.total.value = analysisResults.value.length
  summaryStats.fallCount.value = analysisResults.value.filter(r => r.fall_detected).length
  const maxConf = Math.max(...analysisResults.value.map(r => r.confidence || 0))
  summaryStats.maxConfidence.value = (maxConf * 100).toFixed(1) + '%'
}

function downloadVideo() {
  if (!outputVideoPath.value) {
    ElMessage.warning('没有可下载的视频')
    return
  }
  
  const link = document.createElement('a')
  link.href = outputVideoPath.value
  link.download = `analysis_result_${new Date().toISOString().split('T')[0]}.mp4`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  ElMessage.success('视频下载成功')
}

function handleVideoError(event) {
  ElMessage.error('视频加载失败，请尝试重新加载或下载视频')
  console.error('Video error:', event)
  videoLoading.value = false
}

function handleVideoLoaded() {
  videoLoading.value = false
  console.log('Video metadata loaded')
}

function reloadVideo() {
  if (!outputVideoPath.value) return
  
  videoLoading.value = true
  if (videoPlayer.value) {
    videoPlayer.value.src = ''
    setTimeout(() => {
      videoPlayer.value.src = outputVideoPath.value
    }, 100)
  }
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
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
.upload-container { width: 100%; max-width: none; margin: 0; }
.tabs-wrapper { margin-bottom: 20px; }
.upload-area { border: 2px dashed #444; border-radius: 15px; padding: 50px; text-align: center; cursor: pointer; transition: all 0.3s; }
.upload-area:hover { border-color: #00d4ff; background: #00d4ff10; }
.upload-icon { font-size: 48px; margin-bottom: 15px; }
.upload-area p { color: #888; margin: 5px 0; }
.hint { font-size: 12px; color: #666; }
.hidden-input { display: none; }
.file-info { margin-bottom: 20px; }
.file-header { display: flex; justify-content: space-between; align-items: center; }
.file-name { font-weight: 500; }
.file-size { color: #888; font-size: 14px; }
.analysis-progress { margin-bottom: 20px; }
.progress-header { display: flex; flex-direction: column; gap: 10px; }
.progress-info { color: #888; font-size: 14px; }
.analysis-results { margin-top: 20px; }
.results-summary { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-bottom: 20px; }
.summary-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.summary-item { text-align: center; padding: 20px; background: #2f3336; border-radius: 10px; }
.summary-item.highlight { background: #dc354520; }
.summary-value { display: block; font-size: 32px; font-weight: bold; color: #00d4ff; }
.summary-item.highlight .summary-value { color: #dc3545; }
.summary-label { display: block; color: #888; font-size: 14px; margin-top: 5px; }
.ai-analysis { margin-top: 20px; }
.risk-display { margin-top: 15px; }
.risk-bar { height: 20px; background: #2f3336; border-radius: 10px; overflow: hidden; }
.risk-fill { height: 100%; transition: width 0.3s; }
.risk-fill.low { background: #28a745; }
.risk-fill.medium { background: #ffc107; }
.risk-fill.high { background: #dc3545; }
.risk-info { display: flex; justify-content: space-between; margin-top: 10px; }
.risk-label { padding: 5px 15px; border-radius: 20px; font-size: 14px; }
.risk-label.low { background: #28a74530; color: #28a745; }
.risk-label.medium { background: #ffc10730; color: #ffc107; }
.risk-label.high { background: #dc354530; color: #dc3545; }
.recommendations { margin-top: 15px; }
.recommendations h4 { color: #00d4ff; margin-bottom: 10px; }
.recommendations ul { list-style: none; padding: 0; }
.recommendations li { padding: 8px 15px; background: #2f3336; border-radius: 5px; margin-bottom: 5px; }
.results-table { margin-top: 20px; }
.batch-section { margin-top: 20px; }
.batch-upload-area { border: 2px dashed #444; border-radius: 15px; padding: 30px; text-align: center; cursor: pointer; transition: all 0.3s; }
.batch-upload-area:hover { border-color: #00d4ff; }
.batch-files { margin-top: 20px; }
.batch-files h4 { color: #fff; margin-bottom: 15px; }
.video-preview { margin-bottom: 20px; }
.video-container { max-width: 800px; margin: 0 auto; border-radius: 10px; overflow: hidden; position: relative; }
.preview-video { width: 100%; height: auto; max-height: 500px; background: #000; }
.video-loading { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; color: #fff; background: rgba(0,0,0,0.7); padding: 20px; border-radius: 10px; }
.video-actions { margin-top: 15px; text-align: center; }
</style>
