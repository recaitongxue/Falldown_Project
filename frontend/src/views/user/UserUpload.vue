<template>
  <div class="upload-page">
    <div class="upload-section">
      <div class="upload-area" :class="{ dragging: isDragging }" @drop="handleDrop" @dragover="handleDragOver" @dragleave="handleDragLeave">
        <input type="file" id="fileInput" accept="video/*,.mp4,.avi,.mov" @change="handleFileSelect" hidden>
        <div class="upload-icon">📹</div>
        <p>拖拽视频文件到此处上传</p>
        <p class="hint">支持 MP4, AVI, MOV 等格式</p>
        <button class="browse-btn" @click="triggerFileSelect">选择文件</button>
      </div>
      
      <div v-if="selectedFile" class="file-info">
        <p>📁 {{ selectedFile.name }}</p>
        <p>{{ formatFileSize(selectedFile.size) }}</p>
        <button class="remove-btn" @click="removeFile">移除</button>
      </div>
    </div>
    
    <div class="analysis-section">
      <h3>分析选项</h3>
      
      <div class="option-group">
        <label class="option-label">检测模式</label>
        <div class="option-buttons">
          <button 
            class="option-btn" 
            :class="{ active: detectionMode === 'fast' }"
            @click="detectionMode = 'fast'"
          >
            快速检测
          </button>
          <button 
            class="option-btn" 
            :class="{ active: detectionMode === 'accurate' }"
            @click="detectionMode = 'accurate'"
          >
            精确检测
          </button>
        </div>
      </div>
      
      <div class="option-group">
        <label class="option-label">输出选项</label>
        <div class="checkbox-group">
          <label class="checkbox-item">
            <input type="checkbox" v-model="showLabels" checked>
            <span>显示检测标签</span>
          </label>
          <label class="checkbox-item">
            <input type="checkbox" v-model="showBboxes" checked>
            <span>显示检测框</span>
          </label>
          <label class="checkbox-item">
            <input type="checkbox" v-model="saveFrames">
            <span>保存关键帧</span>
          </label>
        </div>
      </div>
      
      <button 
        class="analyze-btn" 
        :disabled="!selectedFile || isAnalyzing"
        @click="startAnalysis"
      >
        <span v-if="isAnalyzing">分析中...</span>
        <span v-else>开始分析</span>
      </button>
    </div>
    
    <div v-if="analysisProgress > 0" class="progress-section">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: analysisProgress + '%' }"></div>
      </div>
      <p class="progress-text">{{ analysisInfo }}</p>
    </div>
    
    <div v-if="analysisResults" class="results-section">
      <h3>分析结果</h3>
      <div class="results-grid">
        <div class="result-card">
          <p class="result-label">总帧数</p>
          <p class="result-value">{{ analysisResults.totalFrames }}</p>
        </div>
        <div class="result-card">
          <p class="result-label">检测到帧数</p>
          <p class="result-value">{{ analysisResults.detectedFrames }}</p>
        </div>
        <div class="result-card" :class="{ alert: analysisResults.fallDetected }">
          <p class="result-label">是否跌倒</p>
          <p class="result-value">{{ analysisResults.fallDetected ? '是' : '否' }}</p>
        </div>
        <div class="result-card">
          <p class="result-label">告警次数</p>
          <p class="result-value">{{ analysisResults.alertCount }}</p>
        </div>
      </div>
      
      <div v-if="outputVideoPath" class="video-preview">
        <div class="video-header">
          <h4>分析结果视频</h4>
          <button class="download-btn" @click="downloadVideo">
            📥 下载视频
          </button>
        </div>
        <video 
          controls 
          class="preview-video" 
          :src="outputVideoPath"
          @error="handleVideoError"
          @loadedmetadata="handleVideoLoaded"
          @loadeddata="handleVideoLoadedData"
        >
          您的浏览器不支持视频播放
        </video>
        <div v-if="videoLoading" class="loading-overlay">
          <span>加载中...</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const userInfo = ref(sessionStorage.getItem('user') ? JSON.parse(sessionStorage.getItem('user')) : null)
const userId = ref(userInfo.value?.id || 1)
const selectedFile = ref(null)
const isDragging = ref(false)
const analysisProgress = ref(0)
const analysisInfo = ref('')
const analysisResults = ref(null)
const outputVideoPath = ref('')
const detectionMode = ref('fast')
const showLabels = ref(true)
const showBboxes = ref(true)
const saveFrames = ref(false)
const videoLoading = ref(false)

const formatFileSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

const triggerFileSelect = () => {
  document.getElementById('fileInput').click()
}

const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file) {
    selectedFile.value = file
  }
}

const handleDragOver = (event) => {
  event.preventDefault()
  isDragging.value = true
}

const handleDragLeave = () => {
  isDragging.value = false
}

const handleDrop = (event) => {
  event.preventDefault()
  isDragging.value = false
  const file = event.dataTransfer.files[0]
  if (file && file.type.startsWith('video/')) {
    selectedFile.value = file
  }
}

const removeFile = () => {
  selectedFile.value = null
  document.getElementById('fileInput').value = ''
}

const startAnalysis = async () => {
  if (!selectedFile.value) return
  
  isAnalyzing.value = true
  analysisProgress.value = 0
  analysisInfo.value = '正在上传文件...'
  
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    
    const uploadResp = await fetch('/api/upload', {
      method: 'POST',
      body: formData,
      credentials: 'include'
    })
    
    const uploadData = await uploadResp.json()
    
    if (uploadData.status !== 'ok') {
      throw new Error(uploadData.error || '上传失败')
    }
    
    analysisProgress.value = 20
    analysisInfo.value = '正在分析视频...'
    
    const detectResp = await fetch('/api/detect/file', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        filepath: uploadData.filepath,
        file_type: 'video',
        user_id: userId.value,
        mode: detectionMode.value,
        show_labels: showLabels.value,
        show_bboxes: showBboxes.value,
        save_frames: saveFrames.value
      }),
      credentials: 'include'
    })
    
    const detectData = await detectResp.json()
    
    analysisProgress.value = 100
    analysisInfo.value = '分析完成'
    
    analysisResults.value = {
      totalFrames: detectData.summary?.total_frames || 0,
      detectedFrames: detectData.summary?.detected_frames || 0,
      fallDetected: detectData.summary?.fall_detected || false,
      alertCount: detectData.summary?.alert_count || 0
    }
    
    if (detectData.output_video) {
      const filename = detectData.output_video.replace(/\\/g, '/').split('/').pop()
      outputVideoPath.value = `/api/video/stream/${encodeURIComponent(filename)}`
      window.videoFilename = filename
    }
    
    isAnalyzing.value = false
    
  } catch (error) {
    console.error('分析失败', error)
    analysisInfo.value = '分析失败: ' + error.message
    isAnalyzing.value = false
  }
}

const downloadVideo = () => {
  if (window.videoFilename) {
    const downloadUrl = `/api/download/video/${encodeURIComponent(window.videoFilename)}`
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = window.videoFilename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }
}

const handleVideoError = (event) => {
  console.error('视频加载错误:', event)
  const error = event.target.error
  console.error('错误详情:', error)
  alert(`视频加载失败: ${error?.message || '未知错误'}`)
}

const handleVideoLoaded = (event) => {
  console.log('视频元数据加载完成:', event.target.duration)
  videoLoading.value = false
}

const handleVideoLoadedData = (event) => {
  console.log('视频数据加载完成')
}
</script>

<style scoped>
.upload-page {
  padding: 24px;
  width: 100%;
  max-width: none;
  margin: 0;
}

.upload-section {
  background: #1a1f25;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
}

.upload-area {
  border: 2px dashed #38444d;
  border-radius: 12px;
  padding: 48px;
  text-align: center;
  transition: all 0.2s;
}

.upload-area:hover {
  border-color: #10b981;
}

.upload-area.dragging {
  border-color: #10b981;
  background: rgba(16, 185, 129, 0.1);
}

.upload-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.upload-area p {
  color: #9ca3af;
  margin: 0 0 8px;
}

.upload-area .hint {
  font-size: 12px;
  color: #6b7280;
}

.browse-btn {
  margin-top: 16px;
  background: #10b981;
  color: white;
  padding: 12px 32px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}

.file-info {
  margin-top: 16px;
  padding: 12px;
  background: #2a3038;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.file-info p {
  color: #e7e9ea;
  margin: 0;
}

.remove-btn {
  background: #ef4444;
  color: white;
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}

.analysis-section {
  background: #1a1f25;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
}

.analysis-section h3 {
  color: #e7e9ea;
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 20px;
}

.option-group {
  margin-bottom: 20px;
}

.option-label {
  color: #9ca3af;
  font-size: 14px;
  margin-bottom: 12px;
  display: block;
}

.option-buttons {
  display: flex;
  gap: 12px;
}

.option-btn {
  flex: 1;
  padding: 12px;
  background: #2a3038;
  border: 2px solid transparent;
  border-radius: 8px;
  color: #9ca3af;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.option-btn.active {
  border-color: #10b981;
  color: #10b981;
  background: rgba(16, 185, 129, 0.1);
}

.checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.checkbox-item {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.checkbox-item input {
  margin-right: 8px;
}

.checkbox-item span {
  color: #e7e9ea;
  font-size: 14px;
}

.analyze-btn {
  width: 100%;
  padding: 16px;
  background: #10b981;
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 20px;
}

.analyze-btn:disabled {
  background: #374151;
  cursor: not-allowed;
}

.progress-section {
  background: #1a1f25;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
}

.progress-bar {
  height: 8px;
  background: #2a3038;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #059669);
  transition: width 0.3s;
}

.progress-text {
  color: #9ca3af;
  font-size: 14px;
  margin: 12px 0 0;
}

.results-section {
  background: #1a1f25;
  border-radius: 12px;
  padding: 24px;
}

.results-section h3 {
  color: #e7e9ea;
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 20px;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.result-card {
  background: #2a3038;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.result-card.alert {
  background: rgba(239, 68, 68, 0.1);
}

.result-card.alert .result-value {
  color: #ef4444;
}

.result-label {
  color: #6b7280;
  font-size: 12px;
  margin: 0 0 8px;
}

.result-value {
  color: #10b981;
  font-size: 24px;
  font-weight: 700;
  margin: 0;
}

.video-preview {
  margin-top: 20px;
}

.video-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.video-header h4 {
  color: #e7e9ea;
  font-size: 14px;
  margin: 0;
}

.download-btn {
  background: #3b82f6;
  color: white;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
}

.download-btn:hover {
  background: #2563eb;
}

.preview-video {
  width: 100%;
  max-height: 500px;
  border-radius: 8px;
  background: #000;
}

.loading-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-size: 16px;
}

.video-preview {
  position: relative;
}
</style>
