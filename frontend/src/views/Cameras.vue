<template>
  <div class="dashboard">
    <aside class="sidebar">
      <div class="logo">
        <h2>🛡️ 跌倒检测</h2>
        <p>Fall Detection System</p>
      </div>
      <nav class="nav-menu">
        <router-link to="/dashboard" class="nav-item"><span class="icon">📊</span><span>仪表盘</span></router-link>
        <router-link to="/cameras" class="nav-item active"><span class="icon">📹</span><span>摄像头管理</span></router-link>
        <router-link to="/upload" class="nav-item"><span class="icon">📁</span><span>文件上传</span></router-link>
        <router-link to="/history" class="nav-item"><span class="icon">📋</span><span>检测历史</span></router-link>
        <router-link to="/statistics" class="nav-item"><span class="icon">📈</span><span>数据统计</span></router-link>
        <router-link to="/alerts" class="nav-item"><span class="icon">🔔</span><span>告警中心</span></router-link>
        <router-link to="/ai-assistant" class="nav-item"><span class="icon">🤖</span><span>AI助手</span></router-link>
        <router-link to="/settings" class="nav-item"><span class="icon">⚙️</span><span>系统设置</span></router-link>
      </nav>
      <div class="user-info">
        <div class="user-avatar">{{ user?.[0]?.toUpperCase() || 'A' }}</div>
        <div class="user-details">
          <span class="user-name">{{ user || 'Admin' }}</span>
        </div>
        <el-button text @click="handleLogout">🚪</el-button>
      </div>
    </aside>

    <main class="main-content">
      <header class="content-header">
        <h1>摄像头管理</h1>
        <el-button type="primary" @click="showAddDialog = true">➕ 添加摄像头</el-button>
      </header>

      <div class="camera-grid">
        <div v-for="cam in cameras" :key="cam.id" class="camera-card">
          <div class="camera-header">
            <h3>{{ cam.name }}</h3>
            <el-tag :type="cam.status === 'online' ? 'success' : 'danger'">{{ cam.status }}</el-tag>
          </div>
          <div class="camera-info">
            <p>📍 {{ cam.location || '未设置位置' }}</p>
            <p>🔗 {{ cam.camera_type }}</p>
            <p v-if="cam.url">URL: {{ cam.url.substring(0, 40) }}...</p>
          </div>
          <div class="camera-actions">
            <el-button size="small" type="primary" @click="testCamera(cam)">测试</el-button>
            <el-button size="small" @click="editCamera(cam)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteCamera(cam.id)">删除</el-button>
          </div>
        </div>

        <div v-if="cameras.length === 0" class="no-data">
          <p>暂无摄像头</p>
          <p>点击上方按钮添加摄像头</p>
        </div>
      </div>

      <el-dialog v-model="showAddDialog" title="添加摄像头" width="500px">
        <el-form :model="cameraForm" label-width="100px">
          <el-form-item label="名称">
            <el-input v-model="cameraForm.name" placeholder="摄像头名称" />
          </el-form-item>
          <el-form-item label="位置">
            <el-input v-model="cameraForm.location" placeholder="安装位置" />
          </el-form-item>
          <el-form-item label="类型">
            <el-select v-model="cameraForm.camera_type">
              <el-option value="rtsp" label="RTSP流" />
              <el-option value="http" label="HTTP流" />
              <el-option value="local" label="本地摄像头" />
            </el-select>
          </el-form-item>
          <el-form-item label="URL" v-if="cameraForm.camera_type !== 'local'">
            <el-input v-model="cameraForm.url" placeholder="rtsp://..." />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showAddDialog = false">取消</el-button>
          <el-button type="primary" @click="addCamera">确定</el-button>
        </template>
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
const cameras = ref([])
const showAddDialog = ref(false)
const cameraForm = reactive({ name: '', location: '', camera_type: 'rtsp', url: '' })

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

async function addCamera() {
  if (!cameraForm.name) {
    ElMessage.warning('请输入摄像头名称')
    return
  }
  try {
    await fetch('/api/cameras', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cameraForm)
    })
    ElMessage.success('摄像头添加成功')
    showAddDialog.value = false
    Object.assign(cameraForm, { name: '', location: '', camera_type: 'rtsp', url: '' })
    fetchCameras()
  } catch (e) {
    ElMessage.error('添加失败')
  }
}

function editCamera(cam) {
  Object.assign(cameraForm, cam)
  showAddDialog.value = true
}

async function deleteCamera(id) {
  try {
    await fetch(`/api/cameras/${id}`, { method: 'DELETE' })
    ElMessage.success('已删除')
    fetchCameras()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

function testCamera(cam) {
  ElMessage.info(`测试摄像头: ${cam.name}`)
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
.user-details { flex: 1; display: flex; flex-direction: column; }
.user-name { font-size: 14px; font-weight: 500; }
.main-content { flex: 1; padding: 20px; overflow-y: auto; }
.content-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.content-header h1 { font-size: 24px; color: #fff; }
.camera-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
.camera-card { background: #1a1f25; border-radius: 15px; padding: 20px; }
.camera-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
.camera-header h3 { color: #fff; font-size: 18px; }
.camera-info { margin-bottom: 15px; }
.camera-info p { color: #8899a6; font-size: 14px; margin: 5px 0; }
.camera-actions { display: flex; gap: 10px; }
.no-data { grid-column: 1 / -1; text-align: center; padding: 60px; color: #666; }
</style>
