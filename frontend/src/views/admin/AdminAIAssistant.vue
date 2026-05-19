<template>
  <div class="admin-ai-assistant">
    <div class="page-header">
      <h2>🤖 AI 智能助手</h2>
      <p>基于 Ollama 的智能分析助手</p>
    </div>

    <div class="assistant-container">
      <div class="sidebar-panel">
        <div class="sidebar-header">
          <h3>对话历史</h3>
          <button class="new-chat-btn" @click="createNewSession">
            ➕ 新对话
          </button>
        </div>

        <div class="session-list">
          <div 
            v-for="session in sessions" 
            :key="session.id"
            :class="['session-item', { active: currentSessionId === session.id }]"
            @click="selectSession(session.id)"
          >
            <div class="session-title">{{ session.title }}</div>
            <div class="session-time">{{ formatTime(session.updated_at) }}</div>
            <button class="delete-btn" @click.stop="deleteSession(session.id)">
              🗑️
            </button>
          </div>
          <div v-if="sessions.length === 0" class="empty-sessions">
            暂无对话历史
          </div>
        </div>

        <div class="quick-actions">
          <h4>快捷分析</h4>
          <button class="action-btn" @click="analyzeSystem">
            📊 系统概览分析
          </button>
          <button class="action-btn" @click="analyzeUsers">
            👥 用户风险分析
          </button>
          <button class="action-btn" @click="analyzeAlerts">
            🔔 告警趋势分析
          </button>
        </div>

        <div class="model-info">
          <h4>当前模型</h4>
          <div class="model-selector">
            <select v-model="currentModel" @change="changeModel">
              <option v-for="model in models" :key="model" :value="model">{{ model }}</option>
            </select>
          </div>
          <div :class="['status-badge', ollamaOnline ? 'online' : 'offline']">
            {{ ollamaOnline ? '✓ Ollama 在线' : '✗ Ollama 离线' }}
          </div>
        </div>
      </div>

      <div class="chat-panel">
        <div class="chat-header">
          <h3>对话</h3>
          <button class="clear-btn" @click="clearChat">清空对话</button>
        </div>

        <div class="chat-messages" ref="chatContainer">
          <div 
            v-for="(msg, index) in messages" 
            :key="index" 
            :class="['message', msg.type]"
          >
            <div class="avatar">{{ msg.type === 'user' ? '👤' : '🤖' }}</div>
            <div class="content">
              <p>{{ msg.content }}</p>
              <span class="time">{{ msg.time }}</span>
            </div>
          </div>
          <div v-if="isLoading" class="loading">
            <span class="loader"></span>
            <span>AI 正在思考...</span>
          </div>
        </div>

        <div class="chat-input">
          <input 
            type="text" 
            v-model="inputMessage" 
            @keyup.enter="sendMessage"
            placeholder="输入消息..."
            :disabled="isLoading || !ollamaOnline"
          >
          <button @click="sendMessage" :disabled="isLoading || !ollamaOnline">
            发送
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const models = ref([])
const currentModel = ref('')
const ollamaOnline = ref(false)
const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const chatContainer = ref(null)
const sessions = ref([])
const currentSessionId = ref(null)

const formatTime = (timeStr) => {
  return new Date(timeStr).toLocaleString()
}

const loadOllamaStatus = async () => {
  try {
    const resp = await fetch('/api/ai/ollama/status')
    const data = await resp.json()
    if (data.success && data.available) {
      models.value = data.models
      ollamaOnline.value = true
      const settingsResp = await fetch('/api/settings')
      const settingsData = await settingsResp.json()
      const savedModel = settingsData.data?.ollama_model
      if (savedModel && models.value.includes(savedModel)) {
        currentModel.value = savedModel
      } else if (models.value.length > 0) {
        currentModel.value = models.value[0]
      }
    } else {
      ollamaOnline.value = false
    }
  } catch (e) {
    console.error('加载Ollama状态失败', e)
    ollamaOnline.value = false
  }
}

const changeModel = async () => {
  try {
    await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ollama_model: currentModel.value })
    })
    messages.value.push({
      type: 'system',
      content: `已切换到模型: ${currentModel.value}`,
      time: new Date().toLocaleTimeString()
    })
    scrollToBottom()
  } catch (e) {
    console.error('切换模型失败', e)
  }
}

const loadSessions = async () => {
  try {
    const resp = await fetch('/api/admin/ai/sessions')
    const data = await resp.json()
    if (data.success) {
      sessions.value = data.data
      if (sessions.value.length > 0 && !currentSessionId.value) {
        selectSession(sessions.value[0].id)
      }
    }
  } catch (e) {
    console.error('加载会话列表失败', e)
  }
}

const createNewSession = async () => {
  try {
    const resp = await fetch('/api/admin/ai/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: '新对话' })
    })
    const data = await resp.json()
    if (data.success) {
      sessions.value.unshift(data.data)
      selectSession(data.data.id)
      messages.value = []
    }
  } catch (e) {
    console.error('创建新会话失败', e)
  }
}

const selectSession = async (sessionId) => {
  currentSessionId.value = sessionId
  try {
    const resp = await fetch(`/api/admin/ai/sessions/${sessionId}/history`)
    const data = await resp.json()
    if (data.success && data.data) {
      messages.value = data.data.map(msg => ({
        type: msg.role === 'user' ? 'user' : 'assistant',
        content: msg.content,
        time: new Date(msg.timestamp).toLocaleTimeString()
      }))
    }
  } catch (e) {
    console.error('加载会话历史失败', e)
  }
  scrollToBottom()
}

const deleteSession = async (sessionId) => {
  try {
    await fetch(`/api/admin/ai/sessions/${sessionId}`, {
      method: 'DELETE'
    })
    sessions.value = sessions.value.filter(s => s.id !== sessionId)
    if (currentSessionId.value === sessionId) {
      if (sessions.value.length > 0) {
        selectSession(sessions.value[0].id)
      } else {
        currentSessionId.value = null
        messages.value = []
      }
    }
  } catch (e) {
    console.error('删除会话失败', e)
  }
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return

  const message = inputMessage.value.trim()
  inputMessage.value = ''
  
  messages.value.push({
    type: 'user',
    content: message,
    time: new Date().toLocaleTimeString()
  })
  scrollToBottom()

  isLoading.value = true
  
  try {
    const resp = await fetch('/api/admin/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: currentSessionId.value })
    })
    
    const data = await resp.json()
    if (data.success) {
      if (!currentSessionId.value && data.session_id) {
        currentSessionId.value = data.session_id
        await loadSessions()
      }
      messages.value.push({
        type: 'assistant',
        content: data.response,
        time: new Date().toLocaleTimeString()
      })
    } else {
      messages.value.push({
        type: 'error',
        content: data.error || 'AI 响应失败',
        time: new Date().toLocaleTimeString()
      })
    }
  } catch (e) {
    messages.value.push({
      type: 'error',
      content: '网络错误，请稍后重试',
      time: new Date().toLocaleTimeString()
    })
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

const analyzeSystem = async () => {
  isLoading.value = true
  messages.value.push({
    type: 'user',
    content: '📊 请分析系统概览',
    time: new Date().toLocaleTimeString()
  })
  scrollToBottom()

  try {
    const resp = await fetch('/api/admin/ai/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: 'system_summary' })
    })
    
    const data = await resp.json()
    if (data.success) {
      messages.value.push({
        type: 'assistant',
        content: data.response,
        time: new Date().toLocaleTimeString()
      })
    } else {
      messages.value.push({
        type: 'error',
        content: data.error || '分析失败',
        time: new Date().toLocaleTimeString()
      })
    }
  } catch (e) {
    messages.value.push({
      type: 'error',
      content: '网络错误',
      time: new Date().toLocaleTimeString()
    })
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

const analyzeUsers = async () => {
  isLoading.value = true
  messages.value.push({
    type: 'user',
    content: '👥 请分析用户风险',
    time: new Date().toLocaleTimeString()
  })
  scrollToBottom()

  try {
    const resp = await fetch('/api/admin/ai/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: 'user_risk' })
    })
    
    const data = await resp.json()
    if (data.success) {
      messages.value.push({
        type: 'assistant',
        content: data.response,
        time: new Date().toLocaleTimeString()
      })
    } else {
      messages.value.push({
        type: 'error',
        content: data.error || '分析失败',
        time: new Date().toLocaleTimeString()
      })
    }
  } catch (e) {
    messages.value.push({
      type: 'error',
      content: '网络错误',
      time: new Date().toLocaleTimeString()
    })
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

const analyzeAlerts = async () => {
  isLoading.value = true
  messages.value.push({
    type: 'user',
    content: '🔔 请分析告警趋势',
    time: new Date().toLocaleTimeString()
  })
  scrollToBottom()

  try {
    const resp = await fetch('/api/admin/ai/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: 'alert_trend' })
    })
    
    const data = await resp.json()
    if (data.success) {
      messages.value.push({
        type: 'assistant',
        content: data.response,
        time: new Date().toLocaleTimeString()
      })
    } else {
      messages.value.push({
        type: 'error', 'content': data.error || '分析失败',
        time: new Date().toLocaleTimeString()
      })
    }
  } catch (e) {
    messages.value.push({
      type: 'error',
      content: '网络错误',
      time: new Date().toLocaleTimeString()
    })
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

const clearChat = async () => {
  try {
    await fetch('/api/admin/ai/clear', { method: 'POST' })
    await loadSessions()
  } catch (e) {
    console.error('清除对话历史失败', e)
  }
  messages.value = []
}

const scrollToBottom = () => {
  setTimeout(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  }, 100)
}

onMounted(() => {
  loadOllamaStatus()
  loadSessions()
})
</script>

<style scoped>
.admin-ai-assistant {
  padding: 24px;
  height: calc(100vh - 48px);
  display: flex;
  flex-direction: column;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
}

.page-header p {
  margin: 0;
  color: #666;
}

.assistant-container {
  display: flex;
  gap: 24px;
  flex: 1;
  min-height: 0;
}

.sidebar-panel {
  width: 320px;
  background: #1e1e2e;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
}

.new-chat-btn {
  background: #6c5ce7;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.new-chat-btn:hover {
  background: #5b4cdb;
  transform: translateY(-1px);
}

.session-list {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.session-item {
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.session-item:hover {
  background: #2d2d44;
}

.session-item.active {
  background: #6c5ce7;
}

.session-title {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-time {
  font-size: 12px;
  color: #999;
}

.session-item.active .session-time {
  color: rgba(255, 255, 255, 0.7);
}

.delete-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(231, 76, 60, 0.2);
  border: none;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  opacity: 0;
  transition: all 0.2s;
}

.session-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  background: #e74c3c;
}

.empty-sessions {
  text-align: center;
  color: #666;
  padding: 24px;
}

.quick-actions h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #999;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-btn {
  background: #2d2d44;
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  text-align: left;
  transition: all 0.2s;
}

.action-btn:hover {
  background: #3d3d5c;
  transform: translateY(-1px);
}

.model-info h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #999;
}

.model-selector {
  margin-bottom: 12px;
}

.model-selector select {
  width: 100%;
  padding: 8px;
  background: #2d2d44;
  border: 1px solid #444;
  border-radius: 8px;
  color: white;
  font-size: 14px;
}

.status-badge {
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 14px;
  text-align: center;
}

.status-badge.online {
  background: rgba(46, 204, 113, 0.2);
  color: #2ecc71;
}

.status-badge.offline {
  background: rgba(231, 76, 60, 0.2);
  color: #e74c3c;
}

.chat-panel {
  flex: 1;
  background: #1e1e2e;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chat-header {
  padding: 16px 20px;
  border-bottom: 1px solid #333;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-header h3 {
  margin: 0;
  font-size: 16px;
}

.clear-btn {
  background: rgba(231, 76, 60, 0.2);
  color: #e74c3c;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.clear-btn:hover {
  background: rgba(231, 76, 60, 0.3);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
}

.message {
  display: flex;
  gap: 12px;
  max-width: 85%;
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message.assistant {
  align-self: flex-start;
}

.avatar {
  width: 36px;
  height: 36px;
  background: #6c5ce7;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.message.user .avatar {
  background: #0984e3;
}

.content {
  background: #2d2d44;
  padding: 12px 16px;
  border-radius: 12px;
  flex: 1;
  min-width: 0;
}

.message.user .content {
  background: #0984e3;
}

.content p {
  margin: 0 0 8px 0;
  line-height: 1.6;
  white-space: pre-wrap;
}

.time {
  font-size: 12px;
  color: #999;
}

.message.user .time {
  color: rgba(255, 255, 255, 0.7);
}

.loading {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 12px 16px;
  background: rgba(108, 92, 231, 0.1);
  border-radius: 12px;
  width: fit-content;
}

.loader {
  width: 20px;
  height: 20px;
  border: 3px solid #6c5ce7;
  border-bottom-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.chat-input {
  padding: 16px 20px;
  border-top: 1px solid #333;
  display: flex;
  gap: 12px;
}

.chat-input input {
  flex: 1;
  padding: 12px 16px;
  background: #2d2d44;
  border: 1px solid #444;
  border-radius: 8px;
  color: white;
  font-size: 14px;
}

.chat-input input:focus {
  outline: none;
  border-color: #6c5ce7;
}

.chat-input button {
  background: #6c5ce7;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.chat-input button:hover:not(:disabled) {
  background: #5b4cdb;
}

.chat-input button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
