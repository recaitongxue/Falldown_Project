<template>
  <div class="camera-container">
    <div class="camera-header">
      <h2>📹 实时监控</h2>
      <div class="camera-controls">
        <el-select v-model="selectedCamera" placeholder="选择摄像头" @change="switchCamera" :disabled="isLoading">
          <el-option label="默认摄像头" value="default" />
          <el-option v-for="(cam, index) in availableCameras" :key="cam.deviceId" :label="`摄像头 ${index + 1}: ${cam.label}`" :value="cam.deviceId" />
        </el-select>
        <el-button :type="isRecording ? 'danger' : 'primary'" @click="toggleRecording" :disabled="!isCameraOn">
          {{ isRecording ? '⏹️ 停止录制' : '⏺️ 开始录制' }}
        </el-button>
        <el-button type="success" @click="captureImage" :disabled="!isCameraOn">📸 截图</el-button>
        <el-button @click="toggleDetection" :disabled="!isCameraOn">
          {{ isDetecting ? '❌ 关闭检测' : '✅ 开启检测' }}
        </el-button>
      </div>
    </div>

    <div class="video-section">
      <div class="video-wrapper">
        <video 
          ref="videoElement" 
          autoplay 
          playsinline 
          class="video-feed"
          :class="{ detecting: isDetecting }"
        ></video>
        <canvas 
          ref="canvasElement" 
          class="video-canvas"
        ></canvas>
        <div class="video-overlay" v-if="!isCameraOn && !isLoading">
          <div class="camera-off">
            <span class="icon">📷</span>
            <p>摄像头未启动</p>
            <el-button type="primary" @click="startCamera()">点击启动</el-button>
          </div>
        </div>
        <div class="video-overlay loading" v-if="isLoading">
          <div class="loading-spinner"></div>
          <p>正在启动摄像头...</p>
        </div>
        <div class="video-overlay" v-if="isDetecting">
          <div class="detection-box" v-if="detectionResult">
            <div class="detection-main">
              <span class="detection-status">STATUS: {{ detectionResult.behavior }}</span>
              <span class="detection-label">{{ detectionResult.label }}</span>
            </div>
            <div class="detection-confidence">行为: {{ detectionResult.behavior_cn }} ({{ detectionResult.confidence }}%)</div>
            <div class="detection-features">
              <span :class="detectionResult.M1 ? 'feature-active' : 'feature-inactive'">M1(重心): {{ detectionResult.M1 ? '是' : '否' }}</span>
              <span :class="detectionResult.M2 ? 'feature-active' : 'feature-inactive'">M2(倾斜): {{ detectionResult.M2 ? '是' : '否' }}</span>
              <span :class="detectionResult.M3 ? 'feature-active' : 'feature-inactive'">M3(变形): {{ detectionResult.M3 ? '是' : '否' }}</span>
            </div>
          </div>
        </div>
        <div class="video-status">
          <span :class="isRecording ? 'recording' : ''">{{ isRecording ? '● 录制中' : '' }}</span>
          <span :class="isDetecting ? 'detecting' : ''">{{ isDetecting ? '● 检测中' : '' }}</span>
        </div>
      </div>

      <div class="video-info">
        <div class="info-item">
          <span class="info-label">状态:</span>
          <span class="info-value" :class="isCameraOn ? 'online' : 'offline'">
            {{ isCameraOn ? '🟢 在线' : '🔴 离线' }}
          </span>
        </div>
        <div class="info-item">
          <span class="info-label">分辨率:</span>
          <span class="info-value">{{ videoResolution }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">帧率:</span>
          <span class="info-value">{{ frameRate }} FPS</span>
        </div>
        <div class="info-item">
          <span class="info-label">录制时长:</span>
          <span class="info-value">{{ recordingTime }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">检测结果:</span>
          <span class="info-value" :class="detectionResult?.label === '跌倒' ? 'alert' : ''">
            {{ detectionResult ? detectionResult.label : '无' }}
          </span>
        </div>
      </div>
    </div>

    <div class="history-section">
      <h3>📋 检测历史记录</h3>
      <div class="history-list">
        <div v-for="(record, index) in detectionHistory" :key="index" class="history-item">
          <div class="history-time">{{ record.time }}</div>
          <div class="history-result" :class="record.label === '跌倒' ? 'fall' : 'normal'">
            {{ record.label }}
          </div>
          <div class="history-confidence">置信度: {{ record.confidence }}%</div>
          <button v-if="record.label === '跌倒'" class="history-screenshot-btn" @click="viewScreenshot(record)">
            📷 查看截图
          </button>
        </div>
        <div v-if="detectionHistory.length === 0" class="no-history">
          暂无检测记录
        </div>
      </div>
    </div>

    <el-dialog v-model="showCaptureDialog" title="截图预览" width="600px">
      <img :src="capturedImage" class="capture-image" />
      <template #footer>
        <el-button @click="showCaptureDialog = false">关闭</el-button>
        <el-button type="primary" @click="downloadImage">下载截图</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showHistoryScreenshot" title="跌倒截图" width="800px">
      <img :src="historyScreenshotUrl" class="capture-image" />
      <template #footer>
        <el-button @click="showHistoryScreenshot = false">关闭</el-button>
        <el-button type="primary" @click="downloadHistoryScreenshot">下载截图</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'

const userInfo = ref(sessionStorage.getItem('user') ? JSON.parse(sessionStorage.getItem('user')) : null)
const userId = ref(userInfo.value?.id || 1)

const videoElement = ref(null)
const canvasElement = ref(null)
const selectedCamera = ref('default')
const availableCameras = ref([])
const isRecording = ref(false)
const isDetecting = ref(false)
const isCameraOn = ref(false)
const isLoading = ref(false)
const recordingStartTime = ref(null)
const recordingTimer = ref(null)
const detectionTimer = ref(null)
const videoResolution = ref('640x480')
const frameRate = ref(0)
const recordingTime = ref('00:00:00')
const detectionResult = ref(null)
const detectionHistory = ref([])
const showCaptureDialog = ref(false)
const capturedImage = ref('')
const showHistoryScreenshot = ref(false)
const historyScreenshotUrl = ref('')
let mediaRecorder = null
let recordedChunks = []
let frameCount = 0
let lastTime = Date.now()

// 骨骼连接关系
const skeletonConnections = [
  ['head', 'shoulder_center'],
  ['shoulder_center', 'right_shoulder'],
  ['right_shoulder', 'right_elbow'],
  ['right_elbow', 'right_hand'],
  ['shoulder_center', 'left_shoulder'],
  ['left_shoulder', 'left_elbow'],
  ['left_elbow', 'left_hand'],
  ['shoulder_center', 'right_hip'],
  ['right_hip', 'right_knee'],
  ['right_knee', 'right_ankle'],
  ['shoulder_center', 'left_hip'],
  ['left_hip', 'left_knee'],
  ['left_knee', 'left_ankle']
]

onMounted(async () => {
  await loadAvailableCameras()
  await loadDetectionHistory()
})

async function loadDetectionHistory() {
  try {
    const resp = await fetch(`/api/detection-history?user_id=${userId.value}&limit=20`)
    const data = await resp.json()
    if (data.success && data.data) {
      detectionHistory.value = data.data
    }
  } catch (err) {
    console.error('加载检测历史失败:', err)
  }
}

onUnmounted(() => {
  stopCamera()
  stopRecording()
  stopDetection()
})

async function loadAvailableCameras() {
  try {
    const devices = await navigator.mediaDevices.enumerateDevices()
    availableCameras.value = devices.filter(d => d.kind === 'videoinput')
    console.log('可用摄像头:', availableCameras.value)
  } catch (err) {
    console.error('获取摄像头列表失败:', err)
    ElMessage.warning('无法获取摄像头列表，可能是权限问题')
  }
}

async function startCamera(deviceId = 'default') {
  stopCamera()
  isLoading.value = true
  
  try {
    const constraints = {
      video: {
        deviceId: deviceId === 'default' ? undefined : deviceId,
        width: { ideal: 1280, max: 1920 },
        height: { ideal: 720, max: 1080 },
        frameRate: { ideal: 30, max: 60 },
        facingMode: 'user'
      },
      audio: false
    }
    
    const stream = await navigator.mediaDevices.getUserMedia(constraints)
    videoElement.value.srcObject = stream
    
    const track = stream.getVideoTracks()[0]
    const settings = track.getSettings()
    videoResolution.value = `${settings.width || 640}x${settings.height || 480}`
    
    isCameraOn.value = true
    startFrameRateCounter()
    ElMessage.success('摄像头启动成功')
  } catch (err) {
    console.error('启动摄像头失败:', err)
    isCameraOn.value = false
    if (err.name === 'NotAllowedError') {
      ElMessage.error('摄像头权限被拒绝，请在浏览器设置中允许摄像头访问')
    } else if (err.name === 'NotFoundError') {
      ElMessage.error('未找到可用的摄像头设备')
    } else {
      ElMessage.error('无法启动摄像头: ' + err.message)
    }
  } finally {
    isLoading.value = false
  }
}

function stopCamera() {
  if (videoElement.value?.srcObject) {
    const stream = videoElement.value.srcObject
    stream.getTracks().forEach(track => track.stop())
    videoElement.value.srcObject = null
  }
  isCameraOn.value = false
}

function switchCamera() {
  startCamera(selectedCamera.value)
}

function startFrameRateCounter() {
  function countFrame() {
    frameCount++
    const now = Date.now()
    if (now - lastTime >= 1000) {
      frameRate.value = frameCount
      frameCount = 0
      lastTime = now
    }
    if (videoElement.value?.srcObject) {
      requestAnimationFrame(countFrame)
    }
  }
  countFrame()
}

function toggleRecording() {
  if (isRecording.value) {
    stopRecording()
  } else {
    startRecording()
  }
}

function startRecording() {
  if (!videoElement.value?.srcObject) {
    ElMessage.warning('请先启动摄像头')
    return
  }
  
  mediaRecorder = new MediaRecorder(videoElement.value.srcObject, {
    mimeType: 'video/webm; codecs=vp9'
  })
  
  recordedChunks = []
  mediaRecorder.ondataavailable = (e) => {
    if (e.data.size > 0) {
      recordedChunks.push(e.data)
    }
  }
  
  mediaRecorder.onstop = () => {
    const blob = new Blob(recordedChunks, { type: 'video/webm' })
    downloadVideo(blob)
  }
  
  mediaRecorder.start(1000)
  isRecording.value = true
  recordingStartTime.value = Date.now()
  startRecordingTimer()
  ElMessage.success('开始录制')
}

function stopRecording() {
  if (mediaRecorder && isRecording.value) {
    mediaRecorder.stop()
    isRecording.value = false
    stopRecordingTimer()
    ElMessage.info('录制已停止')
  }
}

function startRecordingTimer() {
  recordingTimer.value = setInterval(() => {
    const elapsed = Date.now() - recordingStartTime.value
    const hours = Math.floor(elapsed / 3600000)
    const minutes = Math.floor((elapsed % 3600000) / 60000)
    const seconds = Math.floor((elapsed % 60000) / 1000)
    recordingTime.value = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
  }, 1000)
}

function stopRecordingTimer() {
  if (recordingTimer.value) {
    clearInterval(recordingTimer.value)
    recordingTimer.value = null
  }
}

function downloadVideo(blob) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `recording_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.webm`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function captureImage() {
  if (!videoElement.value) {
    ElMessage.warning('请先启动摄像头')
    return
  }
  
  const canvas = document.createElement('canvas')
  canvas.width = videoElement.value.videoWidth || 640
  canvas.height = videoElement.value.videoHeight || 480
  const ctx = canvas.getContext('2d')
  ctx.drawImage(videoElement.value, 0, 0, canvas.width, canvas.height)
  
  capturedImage.value = canvas.toDataURL('image/png')
  showCaptureDialog.value = true
  ElMessage.success('截图成功')
}

function downloadImage() {
  const link = document.createElement('a')
  link.href = capturedImage.value
  link.download = `capture_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.png`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

async function saveFallScreenshot(detectionResult) {
  if (!videoElement.value) {
    console.warn('无法截图：视频元素不存在')
    return
  }
  
  try {
    // 创建canvas并绘制当前帧
    const canvas = document.createElement('canvas')
    canvas.width = videoElement.value.videoWidth || 640
    canvas.height = videoElement.value.videoHeight || 480
    const ctx = canvas.getContext('2d')
    ctx.drawImage(videoElement.value, 0, 0, canvas.width, canvas.height)
    
    // 添加检测信息到截图上
    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)'
    ctx.fillRect(10, 10, 300, 80)
    
    ctx.fillStyle = '#ff0000'
    ctx.font = 'bold 16px Arial'
    ctx.fillText(`检测结果: ${detectionResult.label}`, 20, 35)
    
    ctx.fillStyle = '#ffff00'
    ctx.font = '14px Arial'
    ctx.fillText(`置信度: ${detectionResult.confidence}%`, 20, 55)
    ctx.fillText(`时间: ${new Date().toLocaleString()}`, 20, 75)
    
    // 转换为base64
    const imageData = canvas.toDataURL('image/png')
    
    // 发送到后端保存
    const response = await fetch('/api/save-fall-screenshot', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'X-User-Id': userId.value
      },
      body: JSON.stringify({
        image: imageData,
        label: detectionResult.label,
        confidence: detectionResult.confidence,
        behavior: detectionResult.behavior_cn,
        timestamp: new Date().toISOString()
      })
    })
    
    const result = await response.json()
    if (result.success) {
      console.log('跌倒截图已保存:', result.file_path)
      // 保存截图URL到历史记录 - 兼容Windows和Unix路径
      const filename = result.file_path.split(/[\\/]/).pop()
      const screenshotUrl = `/api/download/screenshot/${encodeURIComponent(filename)}`
      detectionHistory.value[0].screenshot = screenshotUrl
    } else {
      console.error('保存截图失败:', result.error)
    }
  } catch (err) {
    console.error('保存跌倒截图异常:', err)
  }
}

function viewScreenshot(record) {
  if (record.screenshot) {
    historyScreenshotUrl.value = record.screenshot
    showHistoryScreenshot.value = true
  } else {
    ElMessage.warning('暂无截图可用')
  }
}

function downloadHistoryScreenshot() {
  const link = document.createElement('a')
  link.href = historyScreenshotUrl.value
  link.download = `fall_screenshot_${Date.now()}.png`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

function toggleDetection() {
  if (isDetecting.value) {
    stopDetection()
  } else {
    startDetection()
  }
}

function startDetection() {
  if (!videoElement.value?.srcObject) {
    ElMessage.warning('请先启动摄像头')
    return
  }
  
  isDetecting.value = true
  // 提高检测频率到每300ms一次，增强实时性和准确性
  detectionTimer.value = setInterval(async () => {
    await simulateDetection()
  }, 300)
  ElMessage.success('跌倒检测已开启')
}

function stopDetection() {
  isDetecting.value = false
  detectionResult.value = null
  if (detectionTimer.value) {
    clearInterval(detectionTimer.value)
    detectionTimer.value = null
  }
  ElMessage.info('跌倒检测已关闭')
}

async function simulateDetection() {
  const canvas = document.createElement('canvas')
  canvas.width = 640
  canvas.height = 480
  const ctx = canvas.getContext('2d')
  ctx.drawImage(videoElement.value, 0, 0, 640, 480)
  
  const imageData = canvas.toDataURL('image/jpeg', 0.8)
  
  try {
    const response = await fetch('/api/detect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image: imageData })
    })
    
    const result = await response.json()
    
    if (result.success) {
      detectionResult.value = {
        label: result.label,
        confidence: Math.round(result.confidence * 100),
        behavior: result.behavior || 'unknown',
        behavior_cn: result.behavior_cn || '未知',
        M1: result.M1 || false,
        M2: result.M2 || false,
        M3: result.M3 || false,
        fall_detected: result.fall_detected || false,
        alert: result.alert || false,
        joints: result.joints || {}
      }
      
      // 绘制骨骼
      drawSkeleton(result.joints || {}, result.alert || result.fall_detected)
      
      if (result.fall_detected || result.alert) {
        // 自动截图保存跌倒时刻
        await saveFallScreenshot(result)
        
        detectionHistory.value.unshift({
          time: new Date().toLocaleString(),
          label: result.label,
          confidence: Math.round(result.confidence * 100),
          behavior: result.behavior_cn || '未知',
          screenshot: null  // 将在保存后更新
        })
        
        if (detectionHistory.value.length > 10) {
          detectionHistory.value.pop()
        }
        
        ElMessage.warning('⚠️ 检测到跌倒行为！已自动保存截图')
      }
    }
  } catch (err) {
    console.error('检测失败:', err)
    detectionResult.value = {
      label: '未知',
      confidence: 0,
      behavior: 'unknown',
      behavior_cn: '未知',
      M1: false,
      M2: false,
      M3: false
    }
    // 清空骨骼绘制
    clearCanvas()
  }
}

function drawSkeleton(joints, isAlert) {
  const canvas = canvasElement.value
  const video = videoElement.value
  
  if (!canvas || !video) return
  
  const ctx = canvas.getContext('2d')
  
  // 获取视频原始尺寸（实际摄像头捕获的尺寸）
  const videoWidth = video.videoWidth || 640
  const videoHeight = video.videoHeight || 480
  
  // 设置canvas尺寸与视频一致
  canvas.width = videoWidth
  canvas.height = videoHeight
  
  // 清除画布
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  
  // 检查是否有关节点数据
  const hasJoints = Object.keys(joints).length > 0 && 
    Object.values(joints).some(p => p && p[0] > 0 && p[1] > 0)
  
  if (!hasJoints) {
    return
  }
  
  // 计算缩放比例：后端返回的坐标是基于 640x480 的，需要转换到实际视频尺寸
  const inputWidth = 640
  const inputHeight = 480
  const scaleX = videoWidth / inputWidth
  const scaleY = videoHeight / inputHeight
  
  // 确定颜色和大小（加粗骨骼，与视频分析一致）
  const color = isAlert ? '#ff0000' : '#00ff00'
  const pointRadius = 12  // 增大关节点
  const lineWidth = 8     // 加粗骨骼线条
  
  // 绘制骨骼连接（带发光效果）
  ctx.strokeStyle = color
  ctx.lineWidth = lineWidth
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  ctx.shadowColor = color
  ctx.shadowBlur = 20
  
  skeletonConnections.forEach(([joint1, joint2]) => {
    const p1 = joints[joint1]
    const p2 = joints[joint2]
    
    if (p1 && p2 && p1[0] > 0 && p1[1] > 0 && p2[0] > 0 && p2[1] > 0) {
      // 将640x480坐标转换到实际视频尺寸
      const x1 = p1[0] * scaleX
      const y1 = p1[1] * scaleY
      const x2 = p2[0] * scaleX
      const y2 = p2[1] * scaleY
      
      ctx.beginPath()
      ctx.moveTo(x1, y1)
      ctx.lineTo(x2, y2)
      ctx.stroke()
    }
  })
  
  // 绘制关节点（三层效果）
  ctx.shadowBlur = 25
  
  Object.values(joints).forEach((point) => {
    if (point && point[0] > 0 && point[1] > 0) {
      // 将640x480坐标转换到实际视频尺寸
      const x = point[0] * scaleX
      const y = point[1] * scaleY
      
      // 绘制外圈光晕
      ctx.beginPath()
      ctx.arc(x, y, pointRadius + 8, 0, Math.PI * 2)
      ctx.fillStyle = color + '40'  // 半透明光晕
      ctx.fill()
      
      // 绘制关节点主体
      ctx.beginPath()
      ctx.arc(x, y, pointRadius, 0, Math.PI * 2)
      ctx.fillStyle = color
      ctx.fill()
      
      // 绘制中心点
      ctx.beginPath()
      ctx.arc(x, y, pointRadius / 2, 0, Math.PI * 2)
      ctx.fillStyle = '#ffffff'
      ctx.fill()
    }
  })
  
  // 重置阴影
  ctx.shadowBlur = 0
}

function clearCanvas() {
  const canvas = canvasElement.value
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  ctx.clearRect(0, 0, canvas.width, canvas.height)
}

// 当检测停止时清空画布
function onDetectionStop() {
  clearCanvas()
}
</script>

<style scoped>
.camera-container {
  padding: 20px;
  width: 100%;
  max-width: none;
  margin: 0;
}

.camera-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.camera-header h2 {
  font-size: 24px;
  color: #fff;
  margin: 0;
}

.camera-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.video-section {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 20px;
  margin-bottom: 20px;
}

.video-wrapper {
  position: relative;
  background: #0a0a0a;
  border-radius: 15px;
  overflow: hidden;
  aspect-ratio: 16 / 9;
}

.video-feed {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-feed.detecting {
  border: 3px solid #8b5cf6;
}

.video-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  pointer-events: none;
}

.video-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.8);
}

.video-overlay.loading {
  background: rgba(0, 0, 0, 0.6);
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #8b5cf6;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.camera-off {
  text-align: center;
  color: #fff;
}

.camera-off .icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.camera-off p {
  margin-bottom: 20px;
  font-size: 18px;
}

.detection-box {
  position: absolute;
  top: 15px;
  left: 15px;
  background: rgba(0, 0, 0, 0.85);
  padding: 15px 20px;
  border-radius: 10px;
  border: 2px solid #00ff00;
}

.detection-main {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.detection-status {
  font-size: 16px;
  font-weight: bold;
  color: #00ff00;
}

.detection-label {
  font-size: 20px;
  font-weight: bold;
  color: #fff;
}

.detection-confidence {
  font-size: 14px;
  color: #00ffff;
  margin-top: 8px;
  margin-bottom: 10px;
}

.detection-features {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detection-features span {
  font-size: 13px;
  padding: 3px 8px;
  border-radius: 5px;
}

.feature-active {
  background: rgba(255, 0, 0, 0.3);
  color: #ff6b6b;
}

.feature-inactive {
  background: rgba(0, 128, 0, 0.2);
  color: #86efac;
}

.video-status {
  position: absolute;
  bottom: 10px;
  left: 10px;
  display: flex;
  gap: 10px;
}

.video-status span {
  padding: 5px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.video-status .recording {
  background: #ef4444;
  color: #fff;
}

.video-status .detecting {
  background: #8b5cf6;
  color: #fff;
}

.video-info {
  background: #1a1f25;
  border-radius: 15px;
  padding: 20px;
}

.video-info h3 {
  color: #fff;
  margin: 0 0 15px 0;
  font-size: 16px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid #2a3038;
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  color: #8899a6;
  font-size: 14px;
}

.info-value {
  color: #fff;
  font-size: 14px;
  font-weight: 500;
}

.info-value.online {
  color: #22c55e;
}

.info-value.offline {
  color: #ef4444;
}

.info-value.alert {
  color: #ef4444;
}

.history-section {
  background: #1a1f25;
  border-radius: 15px;
  padding: 20px;
}

.history-section h3 {
  color: #fff;
  margin: 0 0 15px 0;
  font-size: 18px;
}

.history-list {
  max-height: 200px;
  overflow-y: auto;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 15px;
  background: #2a3038;
  border-radius: 10px;
  margin-bottom: 10px;
}

.history-item:last-child {
  margin-bottom: 0;
}

.history-time {
  color: #8899a6;
  font-size: 14px;
}

.history-result {
  font-size: 14px;
  font-weight: 500;
  padding: 4px 12px;
  border-radius: 20px;
}

.history-result.normal {
  background: #22c55e;
  color: #fff;
}

.history-result.fall {
  background: #ef4444;
  color: #fff;
}

.history-confidence {
  color: #8899a6;
  font-size: 12px;
}

.no-history {
  text-align: center;
  padding: 30px;
  color: #666;
}

.capture-image {
  width: 100%;
  border-radius: 10px;
}

@media (max-width: 1000px) {
  .video-section {
    grid-template-columns: 1fr;
  }
  
  .camera-controls {
    flex-wrap: wrap;
  }
}
</style>
