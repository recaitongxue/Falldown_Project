<template>
  <div class="admin-settings-page">
    <div class="page-header">
      <h2>系统设置</h2>
    </div>
    
    <div class="settings-grid">
      <div class="setting-card">
        <h3>🔐 安全设置</h3>
        
        <div class="setting-item">
          <label class="setting-label">密码最小长度</label>
          <div class="setting-control">
            <input type="number" v-model.number="securitySettings.min_password_length" min="6" max="32">
          </div>
        </div>
        
        <div class="setting-item">
          <label class="setting-label">会话超时时间（分钟）</label>
          <div class="setting-control">
            <input type="number" v-model.number="securitySettings.session_timeout" min="15" max="480">
          </div>
        </div>
        
        <div class="setting-item">
          <label class="setting-label">允许用户注册</label>
          <div class="setting-control">
            <label class="switch">
              <input type="checkbox" v-model="securitySettings.allow_registration">
              <span class="slider"></span>
            </label>
          </div>
        </div>
        
        <div class="setting-item">
          <label class="setting-label">禁止用户名</label>
          <div class="setting-control">
            <input type="text" v-model="securitySettings.blocked_usernames" placeholder="用逗号分隔">
          </div>
        </div>
      </div>
      
      <div class="setting-card">
        <h3>🤖 AI 设置</h3>
        
        <div class="setting-item">
          <label class="setting-label">Ollama 模型</label>
          <div class="setting-control">
            <select v-model="aiSettings.ollama_model" :disabled="!ollamaModels.length">
              <option value="" disabled>加载中...</option>
              <option v-for="model in ollamaModels" :key="model" :value="model">{{ model }}</option>
            </select>
          </div>
        </div>

        <div class="setting-item">
          <label class="setting-label">Ollama 状态</label>
          <div class="setting-control">
            <span :class="['status-badge', ollamaAvailable ? 'online' : 'offline']">
              {{ ollamaAvailable ? '✓ 在线' : '✗ 离线' }}
            </span>
          </div>
        </div>
        
        <div class="setting-item">
          <label class="setting-label">API 端点</label>
          <div class="setting-control">
            <input type="text" v-model="aiSettings.ollama_endpoint" placeholder="http://localhost:11434">
          </div>
        </div>
        
        <div class="setting-item">
          <label class="setting-label">最大响应长度</label>
          <div class="setting-control">
            <input type="number" v-model.number="aiSettings.max_response_length" min="100" max="4000">
          </div>
        </div>
        
        <div class="setting-item">
          <label class="setting-label">启用 AI 助手</label>
          <div class="setting-control">
            <label class="switch">
              <input type="checkbox" v-model="aiSettings.enable_ai_assistant">
              <span class="slider"></span>
            </label>
          </div>
        </div>
      </div>
      
      <div class="setting-card">
        <h3>📹 视频设置</h3>
        
        <div class="setting-item">
          <label class="setting-label">视频最大大小（MB）</label>
          <div class="setting-control">
            <input type="number" v-model.number="videoSettings.max_file_size" min="10" max="500">
          </div>
        </div>
        
        <div class="setting-item">
          <label class="setting-label">分析帧率</label>
          <div class="setting-control">
            <select v-model="videoSettings.analysis_fps">
              <option :value="5">5 FPS</option>
              <option :value="10">10 FPS</option>
              <option :value="15">15 FPS</option>
              <option :value="20">20 FPS</option>
            </select>
          </div>
        </div>
        
        <div class="setting-item">
          <label class="setting-label">检测阈值</label>
          <div class="setting-control">
            <input type="range" v-model.number="videoSettings.detection_threshold" min="0.1" max="0.9" step="0.1">
            <span>{{ videoSettings.detection_threshold.toFixed(1) }}</span>
          </div>
        </div>
        
        <div class="setting-item">
          <label class="setting-label">输出视频质量</label>
          <div class="setting-control">
            <select v-model="videoSettings.output_quality">
              <option value="low">低</option>
              <option value="medium">中</option>
              <option value="high">高</option>
            </select>
          </div>
        </div>
      </div>
      
      <div class="setting-card">
        <h3>📊 告警设置</h3>
        
        <div class="setting-item">
          <label class="setting-label">跌倒检测告警</label>
          <div class="setting-control">
            <label class="switch">
              <input type="checkbox" v-model="alertSettings.enable_fall_alert">
              <span class="slider"></span>
            </label>
          </div>
        </div>
        
        <div class="setting-item">
          <label class="setting-label">静默时间（分钟）</label>
          <div class="setting-control">
            <input type="number" v-model.number="alertSettings.silence_period" min="0" max="60">
          </div>
        </div>
        
        <div class="setting-item">
          <label class="setting-label">告警级别</label>
          <div class="setting-control">
            <select v-model="alertSettings.default_severity">
              <option value="high">高</option>
              <option value="medium">中</option>
              <option value="low">低</option>
            </select>
          </div>
        </div>
      </div>
    </div>
    
    <div class="actions-bar">
      <button class="save-btn" @click="saveSettings">
        💾 保存设置
      </button>
      <button class="reset-btn" @click="resetSettings">
        🔄 重置为默认值
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const ollamaModels = ref([])
const ollamaAvailable = ref(false)

const securitySettings = ref({
  min_password_length: 6,
  session_timeout: 60,
  allow_registration: true,
  blocked_usernames: 'admin, root, administrator'
})

const aiSettings = ref({
  ollama_model: 'llama3',
  ollama_endpoint: 'http://localhost:11434',
  max_response_length: 1000,
  enable_ai_assistant: true
})

const videoSettings = ref({
  max_file_size: 100,
  analysis_fps: 10,
  detection_threshold: 0.5,
  output_quality: 'medium'
})

const alertSettings = ref({
  enable_fall_alert: true,
  silence_period: 5,
  default_severity: 'high'
})

const loadSettings = async () => {
  try {
    const resp = await fetch('/api/settings', { credentials: 'include' })
    const data = await resp.json()
    Object.assign(securitySettings.value, data.data || {})
    aiSettings.value.ollama_model = data.data?.ollama_model || 'llama3'
    aiSettings.value.ollama_endpoint = data.data?.ollama_host || 'http://localhost:11434'
  } catch (e) {
    console.error('加载设置失败', e)
  }
}

const loadOllamaModels = async () => {
  try {
    const resp = await fetch('/api/ai/ollama/status')
    const data = await resp.json()
    if (data.success && data.available) {
      ollamaModels.value = data.models || []
      ollamaAvailable.value = true
    } else {
      ollamaModels.value = []
      ollamaAvailable.value = false
    }
  } catch (e) {
    console.error('加载Ollama模型失败', e)
    ollamaModels.value = []
    ollamaAvailable.value = false
  }
}

const saveSettings = async () => {
  try {
    const resp = await fetch('/api/settings', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        ollama_model: aiSettings.value.ollama_model,
        ollama_host: aiSettings.value.ollama_endpoint
      }),
      credentials: 'include'
    })
    
    if (resp.ok) {
      alert('设置保存成功')
    } else {
      const data = await resp.json()
      alert(data.error || '保存失败')
    }
  } catch (e) {
    console.error('保存设置失败', e)
    alert('保存失败')
  }
}

const resetSettings = () => {
  securitySettings.value = {
    min_password_length: 6,
    session_timeout: 60,
    allow_registration: true,
    blocked_usernames: 'admin, root, administrator'
  }
  aiSettings.value = {
    ollama_model: 'llama3',
    ollama_endpoint: 'http://localhost:11434',
    max_response_length: 1000,
    enable_ai_assistant: true
  }
  videoSettings.value = {
    max_file_size: 100,
    analysis_fps: 10,
    detection_threshold: 0.5,
    output_quality: 'medium'
  }
  alertSettings.value = {
    enable_fall_alert: true,
    silence_period: 5,
    default_severity: 'high'
  }
}

onMounted(() => {
  loadSettings()
  loadOllamaModels()
})
</script>

<style scoped>
.admin-settings-page {
  padding: 24px;
}

.page-header h2 {
  color: #e7e9ea;
  font-size: 20px;
  margin: 0 0 24px;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.setting-card {
  background: #1a1f25;
  border-radius: 12px;
  padding: 20px;
}

.setting-card h3 {
  color: #e7e9ea;
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 20px;
}

.setting-item {
  margin-bottom: 16px;
}

.setting-item:last-child {
  margin-bottom: 0;
}

.setting-label {
  display: block;
  color: #9ca3af;
  font-size: 14px;
  margin-bottom: 8px;
}

.setting-control {
  display: flex;
  align-items: center;
  gap: 12px;
}

.setting-control input[type="number"],
.setting-control input[type="text"],
.setting-control select {
  flex: 1;
  padding: 10px;
  background: #2a3038;
  border: 1px solid #38444d;
  border-radius: 8px;
  color: #e7e9ea;
  font-size: 14px;
}

.setting-control input[type="range"] {
  flex: 1;
  height: 6px;
  background: #2a3038;
  border-radius: 3px;
  appearance: none;
}

.setting-control input[type="range"]::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 16px;
  background: #8b5cf6;
  border-radius: 50%;
  cursor: pointer;
}

.setting-control span {
  color: #e7e9ea;
  font-size: 14px;
  min-width: 40px;
}

.switch {
  position: relative;
  display: inline-block;
  width: 60px;
  height: 34px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #2a3038;
  transition: .4s;
  border-radius: 34px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 26px;
  width: 26px;
  left: 4px;
  bottom: 4px;
  background-color: #6b7280;
  transition: .4s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #10b981;
}

input:checked + .slider:before {
  transform: translateX(26px);
  background-color: white;
}

.actions-bar {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.save-btn, .reset-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}

.save-btn {
  background: #10b981;
  color: white;
}

.reset-btn {
  background: #2a3038;
  color: #e7e9ea;
}

@media (max-width: 768px) {
  .settings-grid {
    grid-template-columns: 1fr;
  }
}
</style>
