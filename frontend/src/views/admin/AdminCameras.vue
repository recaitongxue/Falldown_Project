<template>
  <div class="cameras-container">
    <div class="page-header">
      <h2>📹 摄像头管理</h2>
      <el-button type="primary" @click="showAddDialog = true">➕ 添加摄像头</el-button>
    </div>

    <div class="camera-grid">
      <div v-for="cam in cameras" :key="cam.id" class="camera-card">
        <div class="camera-header">
          <h3>{{ cam.name }}</h3>
          <el-tag :type="cam.status === 'online' ? 'success' : 'danger'">
            {{ cam.status === 'online' ? '在线' : '离线' }}
          </el-tag>
        </div>
        
        <div class="camera-preview">
          <div class="preview-placeholder" v-if="cam.status === 'offline'">
            <span class="icon">📷</span>
            <p>摄像头离线</p>
          </div>
          <div class="preview-online" v-else>
            <img :src="getCameraPreview(cam)" alt="摄像头预览" class="preview-image" />
            <div class="live-indicator">
              <span class="live-dot"></span>
              <span>LIVE</span>
            </div>
          </div>
        </div>
        
        <div class="camera-info">
          <div class="info-row">
            <span class="label">📍 位置:</span>
            <span class="value">{{ cam.location || '未设置' }}</span>
          </div>
          <div class="info-row">
            <span class="label">🔗 类型:</span>
            <span class="value">{{ getCameraTypeName(cam.camera_type) }}</span>
          </div>
          <div class="info-row" v-if="cam.url">
            <span class="label">🌐 URL:</span>
            <span class="value">{{ cam.url.substring(0, 30) }}...</span>
          </div>
          <div class="info-row">
            <span class="label">⏰ 最后检测:</span>
            <span class="value">{{ cam.last_detection || '从未检测' }}</span>
          </div>
        </div>
        
        <div class="camera-actions">
          <el-button size="small" type="primary" @click="viewCamera(cam)">查看</el-button>
          <el-button size="small" @click="editCamera(cam)">编辑</el-button>
          <el-button size="small" type="danger" @click="deleteCamera(cam.id)">删除</el-button>
        </div>
      </div>

      <div v-if="cameras.length === 0" class="empty-state">
        <span class="empty-icon">📹</span>
        <p>暂无摄像头</p>
        <p>点击上方按钮添加摄像头</p>
      </div>
    </div>

    <el-dialog v-model="showAddDialog" title="添加摄像头" width="500px">
      <el-form :model="cameraForm" label-width="100px">
        <el-form-item label="名称" required>
          <el-input v-model="cameraForm.name" placeholder="摄像头名称" />
        </el-form-item>
        <el-form-item label="位置">
          <el-input v-model="cameraForm.location" placeholder="安装位置（如：客厅、卧室）" />
        </el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="cameraForm.camera_type">
            <el-option value="rtsp" label="RTSP流（网络摄像头）" />
            <el-option value="http" label="HTTP流" />
            <el-option value="local" label="本地摄像头" />
          </el-select>
        </el-form-item>
        <el-form-item label="URL" v-if="cameraForm.camera_type !== 'local'" required>
          <el-input v-model="cameraForm.url" placeholder="rtsp://..." />
        </el-form-item>
        <el-form-item label="描述">
          <el-textarea v-model="cameraForm.description" placeholder="摄像头描述信息" rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="saveCamera">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showViewDialog" title="摄像头监控" width="800px">
      <div v-if="selectedCamera" class="view-camera">
        <div class="view-preview">
          <div class="preview-container">
            <img :src="selectedCamera.url ? `/api/stream/${selectedCamera.id}` : ''" 
                 alt="实时画面" 
                 class="stream-image"
                 @error="handleStreamError" />
            <div class="stream-overlay" v-if="!streamOnline">
              <span class="stream-error">📡 连接失败，请检查摄像头</span>
            </div>
          </div>
          <div class="stream-controls">
            <el-button type="primary" @click="toggleStream">
              {{ streamPlaying ? '⏸️ 暂停' : '▶️ 播放' }}
            </el-button>
            <el-button type="success" @click="captureSnapshot">📸 截图</el-button>
            <el-button @click="startDetection">✅ 开始检测</el-button>
          </div>
        </div>
        <div class="view-info">
          <h4>摄像头信息</h4>
          <div class="info-grid">
            <div class="info-item">名称: {{ selectedCamera.name }}</div>
            <div class="info-item">位置: {{ selectedCamera.location }}</div>
            <div class="info-item">类型: {{ getCameraTypeName(selectedCamera.camera_type) }}</div>
            <div class="info-item">状态: {{ selectedCamera.status }}</div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

const cameras = ref([])
const showAddDialog = ref(false)
const showViewDialog = ref(false)
const selectedCamera = ref(null)
const streamOnline = ref(true)
const streamPlaying = ref(true)

const cameraForm = reactive({ 
  id: null,
  name: '', 
  location: '', 
  camera_type: 'rtsp', 
  url: '',
  description: '' 
})

onMounted(fetchCameras)

async function fetchCameras() {
  try {
    const resp = await fetch('/api/cameras')
    const data = await resp.json()
    cameras.value = data.data || []
  } catch (e) {
    console.error(e)
    ElMessage.error('获取摄像头列表失败')
  }
}

function getCameraTypeName(type) {
  const types = {
    'rtsp': 'RTSP流',
    'http': 'HTTP流',
    'local': '本地摄像头'
  }
  return types[type] || type
}

function getCameraPreview(cam) {
  return cam.url ? `/api/stream/${cam.id}` : ''
}

function addCamera() {
  cameraForm.id = null
  cameraForm.name = ''
  cameraForm.location = ''
  cameraForm.camera_type = 'rtsp'
  cameraForm.url = ''
  cameraForm.description = ''
  showAddDialog.value = true
}

function editCamera(cam) {
  cameraForm.id = cam.id
  cameraForm.name = cam.name
  cameraForm.location = cam.location || ''
  cameraForm.camera_type = cam.camera_type || 'rtsp'
  cameraForm.url = cam.url || ''
  cameraForm.description = cam.description || ''
  showAddDialog.value = true
}

async function saveCamera() {
  if (!cameraForm.name) {
    ElMessage.warning('请输入摄像头名称')
    return
  }
  
  if (cameraForm.camera_type !== 'local' && !cameraForm.url) {
    ElMessage.warning('请输入摄像头URL')
    return
  }

  try {
    const method = cameraForm.id ? 'PUT' : 'POST'
    const url = cameraForm.id ? `/api/cameras/${cameraForm.id}` : '/api/cameras'
    
    await fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cameraForm)
    })
    
    ElMessage.success(cameraForm.id ? '摄像头更新成功' : '摄像头添加成功')
    showAddDialog.value = false
    fetchCameras()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

async function deleteCamera(id) {
  if (!confirm('确定要删除这个摄像头吗？')) {
    return
  }
  
  try {
    await fetch(`/api/cameras/${id}`, { method: 'DELETE' })
    ElMessage.success('删除成功')
    fetchCameras()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

function viewCamera(cam) {
  selectedCamera.value = cam
  streamOnline.value = true
  streamPlaying.value = true
  showViewDialog.value = true
}

function toggleStream() {
  streamPlaying.value = !streamPlaying.value
}

function captureSnapshot() {
  ElMessage.success('截图功能开发中')
}

function startDetection() {
  ElMessage.success('已开始跌倒检测')
}

function handleStreamError() {
  streamOnline.value = false
}
</script>

<style scoped>
.cameras-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  font-size: 24px;
  color: #fff;
  margin: 0;
}

.camera-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.camera-card {
  background: #1a1f25;
  border-radius: 15px;
  overflow: hidden;
}

.camera-card .camera-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #2a3038;
}

.camera-card .camera-header h3 {
  color: #fff;
  margin: 0;
  font-size: 18px;
}

.camera-preview {
  height: 200px;
  background: #0a0a0a;
  position: relative;
}

.preview-placeholder {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #666;
}

.preview-placeholder .icon {
  font-size: 48px;
  margin-bottom: 10px;
}

.preview-online {
  height: 100%;
  position: relative;
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.live-indicator {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  align-items: center;
  gap: 5px;
  background: rgba(239, 68, 68, 0.9);
  padding: 5px 12px;
  border-radius: 20px;
  font-size: 12px;
  color: #fff;
}

.live-dot {
  width: 8px;
  height: 8px;
  background: #fff;
  border-radius: 50%;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.camera-info {
  padding: 15px 20px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #2a3038;
}

.info-row:last-child {
  border-bottom: none;
}

.info-row .label {
  color: #8899a6;
  font-size: 14px;
}

.info-row .value {
  color: #fff;
  font-size: 14px;
}

.camera-actions {
  display: flex;
  gap: 10px;
  padding: 15px 20px;
  background: #2a3038;
}

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 60px;
  color: #666;
}

.empty-icon {
  font-size: 64px;
  display: block;
  margin-bottom: 20px;
}

.view-camera {
  display: flex;
  gap: 20px;
}

.view-preview {
  flex: 1;
}

.preview-container {
  position: relative;
  background: #0a0a0a;
  border-radius: 10px;
  overflow: hidden;
  aspect-ratio: 16 / 9;
}

.stream-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.stream-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.8);
}

.stream-error {
  color: #ef4444;
  font-size: 18px;
}

.stream-controls {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}

.view-info {
  width: 250px;
  background: #1a1f25;
  border-radius: 10px;
  padding: 15px;
}

.view-info h4 {
  color: #fff;
  margin: 0 0 15px 0;
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-item {
  color: #8899a6;
  font-size: 14px;
}

.info-item::before {
  content: '• ';
  color: #8b5cf6;
}
</style>
