<template>
  <div class="dashboard">
    <aside class="sidebar">
      <div class="logo"><h2>🛡️ 跌倒检测</h2><p>Fall Detection System</p></div>
      <nav class="nav-menu">
        <router-link to="/dashboard" class="nav-item"><span class="icon">📊</span><span>仪表盘</span></router-link>
        <router-link to="/cameras" class="nav-item"><span class="icon">📹</span><span>摄像头管理</span></router-link>
        <router-link to="/upload" class="nav-item"><span class="icon">📁</span><span>文件上传</span></router-link>
        <router-link to="/history" class="nav-item"><span class="icon">📋</span><span>检测历史</span></router-link>
        <router-link to="/statistics" class="nav-item"><span class="icon">📈</span><span>数据统计</span></router-link>
        <router-link to="/alerts" class="nav-item"><span class="icon">🔔</span><span>告警中心</span></router-link>
        <router-link to="/ai-assistant" class="nav-item"><span class="icon">🤖</span><span>AI助手</span></router-link>
        <router-link to="/settings" class="nav-item active"><span class="icon">⚙️</span><span>系统设置</span></router-link>
      </nav>
      <div class="user-info">
        <div class="user-avatar">{{ user?.[0]?.toUpperCase() || 'A' }}</div>
        <div class="user-details"><span class="user-name">{{ user || 'Admin' }}</span></div>
        <el-button text @click="handleLogout">🚪</el-button>
      </div>
    </aside>

    <main class="main-content">
      <header class="content-header">
        <h1>系统设置</h1>
      </header>

      <div class="settings-grid">
        <div class="settings-card">
          <h3>🎯 检测参数配置</h3>
          <el-form :model="detectionConfig" label-width="140px">
            <el-form-item label="重心下降阈值">
              <el-slider v-model="detectionConfig.v_cr" :min="0.001" :max="0.05" :step="0.001" show-input />
              <span class="help-text">CGDD算法中判定跌倒的速度阈值</span>
            </el-form-item>
            <el-form-item label="倾斜角度阈值">
              <el-slider v-model="detectionConfig.theta_cr" :min="30" :max="90" :step="1" show-input />
              <span class="help-text">BTD算法中判定跌倒的角度阈值</span>
            </el-form-item>
            <el-form-item label="宽高比阈值">
              <el-slider v-model="detectionConfig.p_cr" :min="0.5" :max="2.0" :step="0.1" show-input />
              <span class="help-text">SCDD算法中判定跌倒的宽高比阈值</span>
            </el-form-item>
            <el-form-item label="告警持续时间(秒)">
              <el-slider v-model="detectionConfig.t_cr" :min="1" :max="30" :step="1" show-input />
              <span class="help-text">触发告警前需要保持跌倒状态的最小时间</span>
            </el-form-item>
            <el-form-item label="序列长度">
              <el-input-number v-model="detectionConfig.sequence_length" :min="4" :max="32" />
              <span class="help-text">模型输入的帧序列长度</span>
            </el-form-item>
          </el-form>
          <el-button type="primary" @click="saveDetectionConfig">保存设置</el-button>
        </div>

        <div class="settings-card">
          <h3>🔔 告警配置</h3>
          <el-form :model="alertConfig" label-width="120px">
            <el-form-item label="启用声音">
              <el-switch v-model="alertConfig.sound_enabled" />
            </el-form-item>
            <el-form-item label="启用弹窗">
              <el-switch v-model="alertConfig.popup_enabled" />
            </el-form-item>
            <el-form-item label="自动截图">
              <el-switch v-model="alertConfig.auto_screenshot" />
            </el-form-item>
            <el-form-item label="告警阈值">
              <el-slider v-model="alertConfig.threshold" :min="0.3" :max="1.0" :step="0.05" show-input />
            </el-form-item>
            <el-form-item label="告警接收邮箱">
              <el-input v-model="alertConfig.email" placeholder="alert@example.com" />
            </el-form-item>
            <el-form-item label="告警手机号">
              <el-input v-model="alertConfig.phone" placeholder="13800138000" />
            </el-form-item>
          </el-form>
          <el-button type="primary" @click="saveAlertConfig">保存告警设置</el-button>
        </div>

        <div class="settings-card">
          <h3>👥 用户管理</h3>
          <el-table :data="users" stripe>
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="role" label="角色">
              <template #default="{ row }">
                <el-tag :type="row.role === 'admin' ? 'danger' : 'info'">{{ row.role === 'admin' ? '管理员' : '用户' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="email" label="邮箱" />
            <el-table-column prop="is_active" label="状态">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'warning'">{{ row.is_active ? '活跃' : '停用' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作">
              <template #default="{ row }">
                <el-button size="small" @click="resetPassword(row)">重置密码</el-button>
                <el-button size="small" type="primary" @click="changeRole(row)">修改角色</el-button>
                <el-button size="small" type="danger" @click="deleteUser(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="user-actions">
            <el-button type="primary" size="small" @click="showAddUserDialog = true">添加用户</el-button>
            <el-button size="small" @click="loadUsers">刷新</el-button>
          </div>
        </div>

        <div class="settings-card">
          <h3>🤖 Ollama AI配置</h3>
          <el-form :model="ollamaConfig" label-width="120px">
            <el-form-item label="启用Ollama">
              <el-switch v-model="ollamaConfig.enabled" @change="checkOllamaStatus" />
            </el-form-item>
            <el-form-item label="Ollama服务地址">
              <el-input v-model="ollamaConfig.host" placeholder="http://localhost:11434" />
            </el-form-item>
            <el-form-item label="选择模型">
              <el-select v-model="ollamaConfig.model" :disabled="!ollamaConfig.available">
                <el-option v-for="m in ollamaModels" :key="m.name" :label="m.name" :value="m.name" />
              </el-select>
            </el-form-item>
            <el-form-item label="连接状态">
              <el-tag :type="ollamaConfig.available ? 'success' : 'danger'">
                {{ ollamaConfig.available ? '已连接' : '未连接' }}
              </el-tag>
            </el-form-item>
          </el-form>
          <div class="ollama-actions">
            <el-button type="primary" size="small" @click="saveOllamaConfig">保存配置</el-button>
            <el-button size="small" @click="refreshOllamaModels">刷新模型列表</el-button>
          </div>
        </div>

        <div class="settings-card">
          <h3>📊 系统信息</h3>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="系统版本">v2.0.0</el-descriptions-item>
            <el-descriptions-item label="数据库">SQLite 3</el-descriptions-item>
            <el-descriptions-item label="模型状态">
              <el-tag :type="hasModel ? 'success' : 'warning'">{{ hasModel ? '已加载' : '未加载' }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="GPU支持">{{ gpuAvailable ? '可用' : '不可用(CPU模式)' }}</el-descriptions-item>
            <el-descriptions-item label="MediaPipe版本">{{ mpVersion }}</el-descriptions-item>
          </el-descriptions>
          <div class="system-actions">
            <el-button type="danger" size="small" @click="clearDatabase">清空数据库</el-button>
            <el-button size="small" @click="restartSystem">重启系统</el-button>
          </div>
        </div>
      </div>
    </main>
  </div>

  <!-- 添加用户对话框 -->
  <el-dialog title="添加用户" v-model="showAddUserDialog" width="400px">
    <el-form :model="newUser" label-width="80px">
      <el-form-item label="用户名">
        <el-input v-model="newUser.username" placeholder="请输入用户名" />
      </el-form-item>
      <el-form-item label="密码">
        <el-input type="password" v-model="newUser.password" placeholder="请输入密码" />
      </el-form-item>
      <el-form-item label="角色">
        <el-select v-model="newUser.role">
          <el-option label="管理员" value="admin" />
          <el-option label="普通用户" value="user" />
        </el-select>
      </el-form-item>
      <el-form-item label="邮箱">
        <el-input v-model="newUser.email" placeholder="可选" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showAddUserDialog = false">取消</el-button>
      <el-button type="primary" @click="addUser">确定</el-button>
    </template>
  </el-dialog>

  <!-- 重置密码对话框 -->
  <el-dialog title="重置密码" v-model="showResetPasswordDialog" width="400px">
    <el-form :model="resetPasswordForm" label-width="80px">
      <el-form-item label="新密码">
        <el-input type="password" v-model="resetPasswordForm.password" placeholder="请输入新密码" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showResetPasswordDialog = false">取消</el-button>
      <el-button type="primary" @click="confirmResetPassword">确定</el-button>
    </template>
  </el-dialog>

  <!-- 修改角色对话框 -->
  <el-dialog title="修改角色" v-model="showChangeRoleDialog" width="400px">
    <el-form :model="changeRoleForm" label-width="80px">
      <el-form-item label="选择角色">
        <el-select v-model="changeRoleForm.role">
          <el-option label="管理员" value="admin" />
          <el-option label="普通用户" value="user" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showChangeRoleDialog = false">取消</el-button>
      <el-button type="primary" @click="confirmChangeRole">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()
const user = ref(sessionStorage.getItem('user') ? JSON.parse(sessionStorage.getItem('user')).username : 'Admin')
const users = ref([])
const hasModel = ref(false)
const gpuAvailable = ref(false)
const mpVersion = ref('0.4.x')

// 用户管理相关
const showAddUserDialog = ref(false)
const showResetPasswordDialog = ref(false)
const showChangeRoleDialog = ref(false)
const currentUser = ref(null)

const newUser = reactive({
  username: '',
  password: '',
  role: 'user',
  email: ''
})

const resetPasswordForm = reactive({
  password: ''
})

const changeRoleForm = reactive({
  role: 'user'
})

// Ollama配置
const ollamaConfig = reactive({
  enabled: true,
  host: 'http://localhost:11434',
  model: 'qwen3:1.7b',
  available: false
})

const ollamaModels = ref([])

const detectionConfig = reactive({
  v_cr: 0.009,
  theta_cr: 45,
  p_cr: 1.0,
  t_cr: 10,
  sequence_length: 16
})

const alertConfig = reactive({
  sound_enabled: true,
  popup_enabled: true,
  auto_screenshot: true,
  threshold: 0.7,
  email: '',
  phone: ''
})

onMounted(async () => {
  await checkStatus()
  await loadUsers()
  await loadConfig()
})

async function checkStatus() {
  try {
    const resp = await fetch('/api/status')
    const data = await resp.json()
    hasModel.value = data.has_model
  } catch (e) {
    console.error(e)
  }
}

async function loadUsers() {
  try {
    const resp = await fetch('/api/users')
    const data = await resp.json()
    users.value = data.users || []
  } catch (e) {
    console.error(e)
  }
}

async function loadConfig() {
  try {
    const resp = await fetch('/api/config/get')
    const data = await resp.json()
    if (data.detection) Object.assign(detectionConfig, data.detection)
    if (data.alert) Object.assign(alertConfig, data.alert)
  } catch (e) {
    console.error(e)
  }
}

async function saveDetectionConfig() {
  try {
    await fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ detection: { ...detectionConfig } })
    })
    ElMessage.success('检测参数已保存')
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

async function saveAlertConfig() {
  try {
    await fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ alert: { ...alertConfig } })
    })
    ElMessage.success('告警配置已保存')
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

// 用户管理方法
async function addUser() {
  if (!newUser.username || !newUser.password) {
    ElMessage.error('用户名和密码不能为空')
    return
  }
  try {
    const resp = await fetch('/api/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newUser)
    })
    const data = await resp.json()
    if (resp.ok) {
      ElMessage.success('用户添加成功')
      showAddUserDialog.value = false
      newUser.username = ''
      newUser.password = ''
      newUser.role = 'user'
      newUser.email = ''
      await loadUsers()
    } else {
      ElMessage.error(data.error || '添加失败')
    }
  } catch (e) {
    ElMessage.error('添加失败')
  }
}

async function resetPassword(user) {
  currentUser.value = user
  resetPasswordForm.password = ''
  showResetPasswordDialog.value = true
}

async function confirmResetPassword() {
  if (!resetPasswordForm.password) {
    ElMessage.error('密码不能为空')
    return
  }
  try {
    const resp = await fetch(`/api/users/${currentUser.value.id}/password`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: resetPasswordForm.password })
    })
    const data = await resp.json()
    if (resp.ok) {
      ElMessage.success('密码重置成功')
      showResetPasswordDialog.value = false
    } else {
      ElMessage.error(data.error || '重置失败')
    }
  } catch (e) {
    ElMessage.error('重置失败')
  }
}

async function changeRole(user) {
  currentUser.value = user
  changeRoleForm.role = user.role
  showChangeRoleDialog.value = true
}

async function confirmChangeRole() {
  try {
    const resp = await fetch(`/api/users/${currentUser.value.id}/role`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role: changeRoleForm.role })
    })
    const data = await resp.json()
    if (resp.ok) {
      ElMessage.success('角色修改成功')
      showChangeRoleDialog.value = false
      await loadUsers()
    } else {
      ElMessage.error(data.error || '修改失败')
    }
  } catch (e) {
    ElMessage.error('修改失败')
  }
}

async function deleteUser(targetUser) {
  const currentUserName = sessionStorage.getItem('user') ? JSON.parse(sessionStorage.getItem('user')).username : ''
  if (targetUser.username === currentUserName) {
    ElMessage.error('不能删除自己')
    return
  }
  try {
    const resp = await fetch(`/api/users/${targetUser.id}`, { method: 'DELETE' })
    const data = await resp.json()
    if (resp.ok) {
      ElMessage.success('用户删除成功')
      await loadUsers()
    } else {
      ElMessage.error(data.error || '删除失败')
    }
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

// Ollama配置方法
async function checkOllamaStatus() {
  if (!ollamaConfig.enabled) {
    ollamaConfig.available = false
    return
  }
  try {
    const resp = await fetch('/api/ai/ollama/status')
    const data = await resp.json()
    ollamaConfig.available = data.available
    ollamaConfig.host = data.host
    ollamaConfig.model = data.model
    await refreshOllamaModels()
  } catch (e) {
    ollamaConfig.available = false
    ElMessage.error('无法连接到Ollama服务')
  }
}

async function refreshOllamaModels() {
  if (!ollamaConfig.enabled) return
  try {
    const resp = await fetch('/api/ai/ollama/models')
    const data = await resp.json()
    ollamaModels.value = data.models || []
  } catch (e) {
    ElMessage.error('获取模型列表失败')
  }
}

async function saveOllamaConfig() {
  try {
    const resp = await fetch('/api/ai/ollama/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(ollamaConfig)
    })
    const data = await resp.json()
    if (resp.ok) {
      ollamaConfig.available = data.available
      ElMessage.success('Ollama配置已保存')
    } else {
      ElMessage.error(data.error || '保存失败')
    }
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

async function clearDatabase() {
  try {
    await fetch('/api/history/clear', { method: 'POST' })
    ElMessage.success('数据库已清空')
  } catch (e) {
    ElMessage.error('清空失败')
  }
}

function restartSystem() {
  ElMessage.info('系统重启功能开发中...')
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
.settings-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
.settings-card { background: #1a1f25; border-radius: 15px; padding: 25px; }
.settings-card h3 { color: #fff; margin-bottom: 20px; font-size: 18px; }
.help-text { display: block; color: #666; font-size: 12px; margin-top: 5px; }
.user-actions, .system-actions { display: flex; gap: 10px; margin-top: 15px; }
</style>
