<template>
  <div class="camera-manage-container">
    <div class="page-header">
      <h2>🏠 我的摄像头</h2>
      <el-button type="primary" @click="showAddDialog = true">➕ 添加摄像头</el-button>
    </div>

    <div class="camera-section">
      <div class="section-title">
        <h3>📹 已添加的摄像头</h3>
        <p class="subtitle">管理您家中的监控摄像头，守护老人安全</p>
      </div>

      <div class="camera-list">
        <div v-for="cam in cameras" :key="cam.id" class="camera-item">
          <div class="camera-card">
            <div class="card-header">
              <div class="camera-icon">
                <span class="icon">📷</span>
                <el-tag :type="cam.status === 'online' ? 'success' : 'danger'" class="status-tag">
                  {{ cam.status === 'online' ? '在线' : '离线' }}
                </el-tag>
              </div>
              <div class="camera-info">
                <h4>{{ cam.name }}</h4>
                <p class="location">📍 {{ cam.location || '未设置位置' }}</p>
              </div>
              <div class="camera-actions">
                <el-button size="small" @click="viewCamera(cam)">查看</el-button>
                <el-button size="small" @click="editCamera(cam)">编辑</el-button>
                <el-button size="small" type="danger" @click="deleteCamera(cam.id)">删除</el-button>
              </div>
            </div>
            
            <div class="card-body">
              <div class="camera-preview">
                <div class="preview-placeholder" v-if="cam.status === 'offline'">
                  <span>📡</span>
                  <p>摄像头离线</p>
                </div>
                <div class="preview-content" v-else>
                  <img :src="getPreview(cam)" alt="预览" class="preview-img" />
                  <div class="live-badge" v-if="cam.status === 'online'">
                    <span class="live-dot"></span>
                    <span>实时</span>
                  </div>
                </div>
              </div>
              <div class="camera-details">
                <div class="detail-row">
                  <span class="label">类型:</span>
                  <span class="value">{{ getCameraTypeName(cam.camera_type) }}</span>
                </div>
                <div class="detail-row" v-if="cam.url">
                  <span class="label">地址:</span>
                  <span class="value">{{ cam.url.substring(0, 25) }}...</span>
                </div>
                <div class="detail-row">
                  <span class="label">最后检测:</span>
                  <span class="value">{{ cam.last_detection || '从未检测' }}</span>
                </div>
              </div>
            </div>

            <div class="card-footer">
              <el-button type="success" size="small" @click="startDetection(cam)">
                {{ cam.isDetecting ? '⏹️ 停止检测' : '✅ 开启跌倒检测' }}
              </el-button>
            </div>
          </div>
        </div>

        <div v-if="cameras.length === 0" class="empty-state">
          <span class="empty-icon">🏠</span>
          <h4>还没有添加摄像头</h4>
          <p>添加摄像头来守护家人安全</p>
          <el-button type="primary" @click="showAddDialog = true">立即添加</el-button>
        </div>
      </div>
    </div>

    <div class="quick-section">
      <div class="section-title">
        <h3>⚡ 快捷操作</h3>
      </div>
      <div class="quick-actions">
        <div class="action-card" @click="goToLiveView">
          <span class="action-icon">🎥</span>
          <span class="action-label">实时监控</span>
          <p class="action-desc">查看所有摄像头实时画面</p>
        </div>
        <div class="action-card" @click="goToHistory">
          <span class="action-icon">📋</span>
          <span class="action-label">检测记录</span>
          <p class="action-desc">查看跌倒检测历史</p>
        </div>
        <div class="action-card" @click="goToAlerts">
          <span class="action-icon">🔔</span>
          <span class="action-label">告警中心</span>
          <p class="action-desc">查看所有告警通知</p>
        </div>
      </div>
    </div>

    <el-dialog v-model="showAddDialog" title="添加摄像头" width="500px">
      <el-form :model="cameraForm" label-width="100px">
        <el-form-item label="摄像头名称" required>
          <el-input v-model="cameraForm.name" placeholder="如：客厅摄像头" />
        </el-form-item>
        <el-form-item label="安装位置">
          <el-input v-model="cameraForm.location" placeholder="如：客厅、卧室、阳台" />
        </el-form-item>
        <el-form-item label="摄像头类型" required>
          <el-select v-model="cameraForm.camera_type">
            <el-option value="local" label="📱 本地摄像头（电脑/手机摄像头）" />
            <el-option value="rtsp" label="📹 RTSP摄像头（网络摄像机）" />
            <el-option value="http" label="🌐 HTTP流（网络视频流）" />
          </el-select>
        </el-form-item>
        <el-form-item label="摄像头地址" v-if="cameraForm.camera_type !== 'local'" required>
          <el-input v-model="cameraForm.url" placeholder="rtsp://用户名:密码@IP:端口/..." />
        </el-form-item>
        <el-form-item label="摄像头描述">
          <el-textarea v-model="cameraForm.description" placeholder="描述摄像头的位置或用途" rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="saveCamera">确定添加</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showViewDialog" title="摄像头监控" width="700px">
      <div v-if="selectedCamera" class="view-container">
        <div class="view-preview">
          <div class="preview-box">
            <img :src="selectedCamera.url ? `/api/stream/${selectedCamera.id}` : ''" 
                 alt="实时画面" 
                 class="stream-img" />
            <div class="preview-overlay" v-if="selectedCamera.status !== 'online'">
              <span>📡 摄像头离线</span>
            </div>
            <div class="view-controls">
              <el-button type="primary" size="small">▶️ 播放</el-button>
              <el-button size="small">⏸️ 暂停</el-button>
              <el-button size="small" type="success">📸 截图</el-button>
              <el-button size="small" type="warning">🔊 声音</el-button>
            </div>
          </div>
        </div>
        <div class="view-info">
          <h4>{{ selectedCamera.name }}</h4>
          <div class="info-list">
            <div class="info-item">位置: {{ selectedCamera.location }}</div>
            <div class="info-item">类型: {{ getCameraTypeName(selectedCamera.camera_type) }}</div>
            <div class="info-item">状态: {{ selectedCamera.status }}</div>
            <div class="info-item">描述: {{ selectedCamera.description || '无' }}</div>
          </div>
          <el-button type="success" style="width: 100%; margin-top: 15px;">
            ✅ 开启跌倒检测
          </el-button>
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

const cameraForm = reactive({ 
  id: null,
  name: '', 
  location: '', 
  camera_type: 'local', 
  url: '',
  description: '' 
})

onMounted(fetchCameras)

async function fetchCameras() {
  try {
    const resp = await fetch('/api/cameras')
    const data = await resp.json()
    cameras.value = data.cameras || []
  } catch (e) {
    console.error(e)
  }
}

function getCameraTypeName(type) {
  const types = {
    'rtsp': 'RTSP网络摄像机',
    'http': 'HTTP视频流',
    'local': '本地摄像头'
  }
  return types[type] || type
}

function getPreview(cam) {
  return cam.url ? `/api/stream/${cam.id}` : ''
}

function editCamera(cam) {
  cameraForm.id = cam.id
  cameraForm.name = cam.name
  cameraForm.location = cam.location || ''
  cameraForm.camera_type = cam.camera_type || 'local'
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
    ElMessage.warning('请输入摄像头地址')
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
    
    ElMessage.success(cameraForm.id ? '摄像头已更新' : '摄像头添加成功')
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
    ElMessage.success('已删除')
    fetchCameras()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

function viewCamera(cam) {
  selectedCamera.value = cam
  showViewDialog.value = true
}

function startDetection(cam) {
  cam.isDetecting = !cam.isDetecting
  if (cam.isDetecting) {
    ElMessage.success(`已为 ${cam.name} 开启跌倒检测`)
  } else {
    ElMessage.info(`已为 ${cam.name} 关闭跌倒检测`)
  }
}

function goToLiveView() {
  window.location.href = '/user/camera'
}

function goToHistory() {
  window.location.href = '/user/history'
}

function goToAlerts() {
  window.location.href = '/user/alerts'
}
</script>

<style scoped>
.camera-manage-container {
  padding: 20px;
  width: 100%;
  max-width: none;
  margin: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.page-header h2 {
  font-size: 24px;
  color: #fff;
  margin: 0;
}

.section-title {
  margin-bottom: 20px;
}

.section-title h3 {
  font-size: 18px;
  color: #fff;
  margin: 0 0 5px 0;
}

.section-title .subtitle {
  color: #8899a6;
  font-size: 14px;
  margin: 0;
}

.camera-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.camera-item {
  width: 100%;
}

.camera-card {
  background: #1a1f25;
  border-radius: 15px;
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #2a3038;
}

.camera-icon {
  display: flex;
  align-items: center;
  gap: 10px;
}

.camera-icon .icon {
  font-size: 24px;
}

.status-tag {
  font-size: 12px;
}

.camera-info {
  flex: 1;
  margin-left: 15px;
}

.camera-info h4 {
  color: #fff;
  margin: 0;
  font-size: 16px;
}

.camera-info .location {
  color: #8899a6;
  font-size: 12px;
  margin: 3px 0 0 0;
}

.camera-actions {
  display: flex;
  gap: 8px;
}

.card-body {
  padding: 15px;
}

.camera-preview {
  height: 180px;
  background: #0a0a0a;
  border-radius: 10px;
  position: relative;
  overflow: hidden;
}

.preview-placeholder {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #666;
}

.preview-placeholder span {
  font-size: 32px;
  margin-bottom: 8px;
}

.preview-placeholder p {
  margin: 0;
  font-size: 14px;
}

.preview-content {
  height: 100%;
  position: relative;
}

.preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.live-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  align-items: center;
  gap: 5px;
  background: rgba(239, 68, 68, 0.9);
  padding: 4px 10px;
  border-radius: 15px;
  font-size: 12px;
  color: #fff;
}

.live-dot {
  width: 6px;
  height: 6px;
  background: #fff;
  border-radius: 50%;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.camera-details {
  margin-top: 15px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #2a3038;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-row .label {
  color: #8899a6;
  font-size: 13px;
}

.detail-row .value {
  color: #fff;
  font-size: 13px;
}

.card-footer {
  padding: 15px;
  background: #2a3038;
  display: flex;
  justify-content: center;
}

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 60px 20px;
  background: #1a1f25;
  border-radius: 15px;
}

.empty-icon {
  font-size: 64px;
  display: block;
  margin-bottom: 15px;
}

.empty-state h4 {
  color: #fff;
  margin: 0 0 8px 0;
}

.empty-state p {
  color: #8899a6;
  margin: 0 0 20px 0;
}

.quick-section {
  margin-top: 30px;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 15px;
}

.action-card {
  background: #1a1f25;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: transform 0.2s, background 0.2s;
}

.action-card:hover {
  transform: translateY(-3px);
  background: #2a3038;
}

.action-icon {
  font-size: 32px;
  display: block;
  margin-bottom: 10px;
}

.action-label {
  font-size: 16px;
  color: #fff;
  font-weight: 500;
  display: block;
  margin-bottom: 5px;
}

.action-desc {
  font-size: 13px;
  color: #8899a6;
  margin: 0;
}

.view-container {
  display: flex;
  gap: 20px;
}

.view-preview {
  flex: 1;
}

.preview-box {
  background: #0a0a0a;
  border-radius: 10px;
  overflow: hidden;
  aspect-ratio: 16 / 9;
  position: relative;
}

.stream-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.7);
  color: #ef4444;
  font-size: 18px;
}

.view-controls {
  position: absolute;
  bottom: 10px;
  left: 10px;
  display: flex;
  gap: 8px;
}

.view-info {
  width: 220px;
  background: #1a1f25;
  border-radius: 10px;
  padding: 15px;
}

.view-info h4 {
  color: #fff;
  margin: 0 0 15px 0;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-item {
  color: #8899a6;
  font-size: 13px;
}

@media (max-width: 768px) {
  .camera-list {
    grid-template-columns: 1fr;
  }
  
  .card-header {
    flex-wrap: wrap;
    gap: 10px;
  }
  
  .view-container {
    flex-direction: column;
  }
  
  .view-info {
    width: 100%;
  }
}
</style>
