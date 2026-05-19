<template>
  <div class="ai-assistant-page">
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
    </div>

    <div class="chat-container">
      <div class="chat-header">
        <h2>🤖 AI健康助手</h2>
        <p class="subtitle">智能分析您的跌倒检测数据</p>
      </div>
      
      <div class="chat-messages" ref="messagesContainer">
        <div 
          v-for="(msg, index) in messages" 
          :key="index"
          class="message"
          :class="{ 'user-message': msg.type === 'user', 'bot-message': msg.type === 'bot' }"
        >
          <div class="avatar">{{ msg.type === 'user' ? '👤' : '🤖' }}</div>
          <div class="message-content">
            <p>{{ msg.content }}</p>
            <span v-if="msg.time" class="message-time">{{ msg.time }}</span>
          </div>
        </div>
        
        <div v-if="isLoading" class="message bot-message">
          <div class="avatar">🤖</div>
          <div class="message-content loading">
            <span class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </span>
          </div>
        </div>
      </div>
      
      <div class="quick-questions">
        <p class="label">快捷问题</p>
        <div class="quick-tags">
          <button 
            v-for="question in quickQuestions" 
            :key="question"
            class="quick-tag"
            @click="sendMessage(question)"
          >
            {{ question }}
          </button>
        </div>
      </div>
      
      <div class="chat-input">
        <input 
          type="text" 
          v-model="inputMessage"
          placeholder="输入您的问题..."
          @keyup.enter="sendMessage(inputMessage)"
          :disabled="isLoading"
        >
        <button class="send-btn" @click="sendMessage(inputMessage)" :disabled="isLoading">
          发送
        </button>
      </div>
    </div>
    
    <div class="analysis-panel">
      <h3>📊 健康分析报告</h3>
      
      <div class="report-card">
        <p class="report-title">近期检测概览</p>
        <div class="report-stats">
          <div class="stat-item">
            <p class="stat-value">{{ healthStats.total_analyses || 0 }}</p>
            <p class="stat-label">检测次数</p>
          </div>
          <div class="stat-item">
            <p class="stat-value">{{ healthStats.fall_count || 0 }}</p>
            <p class="stat-label">跌倒次数</p>
          </div>
          <div class="stat-item">
            <p class="stat-value">{{ healthStats.risk_level || '低' }}</p>
            <p class="stat-label">风险等级</p>
          </div>
        </div>
      </div>
      
      <div class="report-card">
        <p class="report-title">健康建议</p>
        <ul class="suggestions">
          <li v-for="(suggestion, index) in suggestions" :key="index">
            {{ suggestion }}
          </li>
        </ul>
      </div>
      
      <div class="report-card">
        <p class="report-title">安全提示</p>
        <p class="tip">⚠️ 建议定期进行身体检查，保持室内环境安全，避免湿滑地面。</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'

const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const messagesContainer = ref(null)
const sessions = ref([])
const currentSessionId = ref(null)

const healthStats = ref({
  total_analyses: 0,
  fall_count: 0,
  risk_level: '低'
})

const suggestions = ref([
  '保持规律运动，增强肌肉力量',
  '在家中安装扶手和防滑垫',
  '定期检查视力和听力',
  '避免独自长时间外出'
])

const quickQuestions = [
  '分析我的检测记录',
  '如何预防跌倒？',
  '跌倒后应该怎么做？',
  '什么是高风险行为？'
]

const formatTime = (timeStr) => {
  return new Date(timeStr).toLocaleString()
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const getUserId = () => {
  const user = JSON.parse(sessionStorage.getItem('user') || '{}')
  return user.id || 'default'
}

const loadSessions = async () => {
  try {
    const userId = getUserId()
    const resp = await fetch(`/api/ai/sessions?user_id=${userId}`, { credentials: 'include' })
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
    const userId = getUserId()
    const resp = await fetch('/api/ai/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: '新对话', user_id: userId })
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
    const resp = await fetch(`/api/ai/sessions/${sessionId}/history`, { credentials: 'include' })
    const data = await resp.json()
    if (data.success && data.data) {
      messages.value = data.data.map(msg => ({
        type: msg.role === 'user' ? 'user' : 'bot',
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
    await fetch(`/api/ai/sessions/${sessionId}`, {
      method: 'DELETE',
      credentials: 'include'
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

const sendMessage = async (message) => {
  if (!message.trim() || isLoading.value) return

  const userId = getUserId()
  
  messages.value.push({ 
    type: 'user', 
    content: message.trim(),
    time: new Date().toLocaleTimeString()
  })
  inputMessage.value = ''
  isLoading.value = true

  await scrollToBottom()

  try {
    const resp = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ 
        message: message.trim(), 
        user_id: userId,
        session_id: currentSessionId.value
      }),
      credentials: 'include'
    })

    const data = await resp.json()

    if (!currentSessionId.value && data.session_id) {
      currentSessionId.value = data.session_id
      await loadSessions()
    }

    messages.value.push({ 
      type: 'bot', 
      content: data.response,
      time: new Date().toLocaleTimeString()
    })
  } catch (error) {
    messages.value.push({ 
      type: 'bot', 
      content: '抱歉，我暂时无法回答您的问题。',
      time: new Date().toLocaleTimeString()
    })
  }

  isLoading.value = false
  await scrollToBottom()
}

const fetchHealthStats = async () => {
  try {
    const resp = await fetch('/api/ai/report', { credentials: 'include' })
    const data = await resp.json()
    healthStats.value = {
      total_analyses: data.total_analyses || 0,
      fall_count: data.fall_count || 0,
      risk_level: data.risk_level || '低'
    }
  } catch (e) {
    console.error('获取健康统计失败', e)
  }
}

onMounted(() => {
  fetchHealthStats()
  loadSessions()
})
</script>

<style scoped>
.ai-assistant-page {
  display: flex;
  gap: 24px;
  padding: 24px;
  height: calc(100vh - 80px);
}

.sidebar-panel {
  width: 280px;
  background: #1a1f25;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
  color: #e7e9ea;
}

.new-chat-btn {
  background: #10b981;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.new-chat-btn:hover {
  background: #0d9668;
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
  background: #2a3038;
}

.session-item.active {
  background: #10b981;
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
  color: #6b7280;
}

.session-item.active .session-time {
  color: rgba(255, 255, 255, 0.7);
}

.delete-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(239, 68, 68, 0.2);
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
  background: #ef4444;
}

.empty-sessions {
  text-align: center;
  color: #6b7280;
  padding: 24px;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #1a1f25;
  border-radius: 12px;
  overflow: hidden;
}

.chat-header {
  padding: 20px;
  border-bottom: 1px solid #2a3038;
}

.chat-header h2 {
  color: #e7e9ea;
  margin: 0;
  font-size: 18px;
}

.chat-header .subtitle {
  color: #6b7280;
  font-size: 12px;
  margin: 4px 0 0;
}

.chat-messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.message {
  display: flex;
  margin-bottom: 16px;
}

.message .avatar {
  font-size: 24px;
  margin-right: 12px;
}

.message-content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 16px;
}

.user-message .message-content {
  background: #10b981;
  color: white;
  border-radius: 16px 16px 4px 16px;
}

.bot-message .message-content {
  background: #2a3038;
  color: #e7e9ea;
  border-radius: 16px 16px 16px 4px;
}

.message-content p {
  margin: 0;
  line-height: 1.6;
}

.message-time {
  font-size: 11px;
  color: #6b7280;
  margin-top: 5px;
  display: block;
}

.user-message .message-time {
  color: rgba(255, 255, 255, 0.7);
}

.loading {
  min-width: 60px;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 12px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #9ca3af;
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) { animation-delay: 0s; }
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

.quick-questions {
  padding: 16px 20px;
  border-top: 1px solid #2a3038;
}

.quick-questions .label {
  color: #6b7280;
  font-size: 12px;
  margin: 0 0 12px;
}

.quick-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.quick-tag {
  padding: 6px 12px;
  background: #2a3038;
  border: none;
  border-radius: 20px;
  color: #9ca3af;
  font-size: 12px;
  cursor: pointer;
}

.quick-tag:hover {
  background: #38444d;
}

.chat-input {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #2a3038;
}

.chat-input input {
  flex: 1;
  padding: 12px;
  background: #2a3038;
  border: none;
  border-radius: 8px;
  color: #e7e9ea;
  font-size: 14px;
}

.chat-input input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-btn {
  padding: 12px 24px;
  background: #10b981;
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.send-btn:hover:not(:disabled) {
  background: #0d9668;
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.analysis-panel {
  width: 320px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.analysis-panel h3 {
  color: #e7e9ea;
  font-size: 16px;
  margin: 0;
}

.report-card {
  background: #1a1f25;
  border-radius: 12px;
  padding: 16px;
}

.report-title {
  color: #e7e9ea;
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 12px;
}

.report-stats {
  display: flex;
  justify-content: space-around;
}

.stat-item {
  text-align: center;
}

.stat-value {
  color: #10b981;
  font-size: 24px;
  font-weight: 700;
  margin: 0;
}

.stat-label {
  color: #6b7280;
  font-size: 12px;
  margin: 4px 0 0;
}

.suggestions {
  margin: 0;
  padding: 0;
  list-style: none;
}

.suggestions li {
  color: #9ca3af;
  font-size: 13px;
  padding: 6px 0;
  border-bottom: 1px solid #2a3038;
}

.suggestions li:last-child {
  border-bottom: none;
}

.tip {
  color: #fbbf24;
  font-size: 13px;
  margin: 0;
  line-height: 1.6;
}

@media (max-width: 1024px) {
  .ai-assistant-page {
    flex-direction: column;
    height: auto;
    min-height: calc(100vh - 80px);
  }
  
  .sidebar-panel {
    width: 100%;
    max-height: 300px;
  }
  
  .analysis-panel {
    width: 100%;
  }
  
  .chat-container {
    min-height: 500px;
  }
}
</style>
