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
        <router-link to="/ai-assistant" class="nav-item active"><span class="icon">🤖</span><span>AI助手</span></router-link>
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
        <h1>🤖 AI 智能助手</h1>
        <el-select v-model="assistantMode" style="width: 150px;">
          <el-option value="analysis" label="智能分析" />
          <el-option value="chat" label="对话模式" />
          <el-option value="report" label="报告生成" />
        </el-select>
      </header>

      <div class="ai-container">
        <div class="quick-actions">
          <h3>快捷操作</h3>
          <div class="action-buttons">
            <el-button v-for="action in quickActions" :key="action.label" @click="sendQuickAction(action.query)">
              {{ action.icon }} {{ action.label }}
            </el-button>
          </div>
        </div>

        <div class="risk-panel">
          <h3>实时风险评估</h3>
          <div class="risk-gauge">
            <div class="risk-value" :class="riskClass">{{ (currentRisk * 100).toFixed(0) }}%</div>
            <div class="risk-label">{{ riskLabel }}</div>
          </div>
          <el-progress :percentage="currentRisk * 100" :color="riskColor" :stroke-width="20" />
          <p class="risk-desc">{{ riskDescription }}</p>
        </div>

        <div class="chat-container">
          <div class="chat-messages" ref="chatContainer">
            <div v-for="(msg, idx) in messages" :key="idx" class="message" :class="msg.role">
              <div class="message-avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
              <div class="message-content">
                <p>{{ msg.content }}</p>
                <span class="message-time">{{ msg.time }}</span>
              </div>
            </div>
          </div>

          <div class="chat-input">
            <el-input v-model="inputMessage" placeholder="输入您的问题..." @keyup.enter="sendMessage" size="large">
              <template #append>
                <el-button @click="sendMessage" :disabled="!inputMessage.trim()">发送</el-button>
              </template>
            </el-input>
          </div>
        </div>

        <div class="analysis-panel" v-if="assistantMode === 'analysis'">
          <h3>智能分析报告</h3>
          <div class="analysis-grid">
            <div class="analysis-card">
              <h4>📊 今日统计</h4>
              <p>检测总量: {{ reportData.total_events }}</p>
              <p>跌倒事件: {{ reportData.fall_events }}</p>
            </div>
            <div class="analysis-card">
              <h4>⚠️ 风险趋势</h4>
              <p>{{ reportData.risk_trend === 'increasing' ? '📈 上升中' : reportData.risk_trend === 'decreasing' ? '📉 下降中' : '➡️ 稳定' }}</p>
            </div>
            <div class="analysis-card">
              <h4>🔍 检测模式</h4>
              <p v-for="p in reportData.patterns" :key="p">{{ p || '未检测到异常模式' }}</p>
            </div>
            <div class="analysis-card">
              <h4>💡 建议</h4>
              <p v-for="r in reportData.recommendations" :key="r">{{ r }}</p>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()
const user = ref(sessionStorage.getItem('user') ? JSON.parse(sessionStorage.getItem('user')).username : 'Admin')
const assistantMode = ref('chat')
const inputMessage = ref('')
const messages = ref([{ role: 'assistant', content: '您好！我是AI智能助手，可以帮助您：\n1. 分析跌倒风险\n2. 查看检测历史\n3. 管理摄像头\n4. 生成报告\n5. 回答系统相关问题', time: new Date().toLocaleTimeString('zh-CN') }])
const chatContainer = ref(null)

const currentRisk = ref(0.3)
const reportData = reactive({ total_events: 0, fall_events: 0, risk_trend: 'stable', patterns: [], recommendations: [] })

const quickActions = [
  { icon: '📊', label: '风险分析', query: '分析当前风险' },
  { icon: '📈', label: '生成报告', query: '生成报告' },
  { icon: '🔔', label: '告警统计', query: '告警情况如何' },
  { icon: '💡', label: '优化建议', query: '有什么优化建议' }
]

const riskClass = computed(() => currentRisk.value > 0.6 ? 'high' : currentRisk.value > 0.3 ? 'medium' : 'low')
const riskLabel = computed(() => currentRisk.value > 0.6 ? '高风险' : currentRisk.value > 0.3 ? '中风险' : '低风险')
const riskColor = computed(() => currentRisk.value > 0.6 ? '#ff4757' : currentRisk.value > 0.3 ? '#ffaa00' : '#00ff88')
const riskDescription = computed(() => currentRisk.value > 0.6 ? '当前风险等级较高，建议立即检查' : currentRisk.value > 0.3 ? '风险中等，建议保持监控' : '风险较低，系统运行正常')

onMounted(async () => {
  await fetchReport()
  await fetchStatus()
  setInterval(fetchStatus, 5000)
})

async function fetchReport() {
  try {
    const resp = await fetch('/api/ai/report')
    const data = await resp.json()
    Object.assign(reportData, data)
  } catch (e) {
    console.error(e)
  }
}

async function fetchStatus() {
  try {
    const resp = await fetch('/api/status')
    const data = await resp.json()
    currentRisk.value = data.ai_risk_level || 0.3
  } catch (e) {
    console.error(e)
  }
}

async function sendMessage() {
  if (!inputMessage.value.trim()) return
  const query = inputMessage.value
  messages.value.push({ role: 'user', content: query, time: new Date().toLocaleTimeString('zh-CN') })
  inputMessage.value = ''

  await nextTick()
  chatContainer.value.scrollTop = chatContainer.value.scrollHeight

  try {
    const resp = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: query })
    })
    const data = await resp.json()
    messages.value.push({ role: 'assistant', content: data.response, time: new Date().toLocaleTimeString('zh-CN') })
  } catch (e) {
    messages.value.push({ role: 'assistant', content: '抱歉，发生了错误：' + e.message, time: new Date().toLocaleTimeString('zh-CN') })
  }

  await nextTick()
  chatContainer.value.scrollTop = chatContainer.value.scrollHeight
}

async function sendQuickAction(query) {
  inputMessage.value = query
  await sendMessage()
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
.ai-container { display: flex; flex-direction: column; gap: 20px; }
.quick-actions { background: #1a1f25; border-radius: 15px; padding: 20px; }
.quick-actions h3 { color: #fff; margin-bottom: 15px; }
.action-buttons { display: flex; gap: 10px; flex-wrap: wrap; }
.risk-panel { background: #1a1f25; border-radius: 15px; padding: 20px; }
.risk-panel h3 { color: #fff; margin-bottom: 20px; }
.risk-gauge { text-align: center; margin-bottom: 20px; }
.risk-value { font-size: 48px; font-weight: bold; }
.risk-value.high { color: #ff4757; }
.risk-value.medium { color: #ffaa00; }
.risk-value.low { color: #00ff88; }
.risk-label { font-size: 18px; color: #8899a6; margin-top: 10px; }
.risk-desc { color: #666; margin-top: 15px; text-align: center; }
.chat-container { background: #1a1f25; border-radius: 15px; padding: 20px; display: flex; flex-direction: column; height: 400px; }
.chat-messages { flex: 1; overflow-y: auto; margin-bottom: 20px; }
.message { display: flex; margin-bottom: 15px; }
.message.user { flex-direction: row-reverse; }
.message-avatar { width: 40px; height: 40px; background: #2f3336; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 10px; font-size: 20px; }
.message.user .message-avatar { margin-right: 0; margin-left: 10px; }
.message-content { max-width: 70%; background: #2f3336; padding: 15px; border-radius: 10px; }
.message.user .message-content { background: #00d4ff20; }
.message-content p { color: #fff; margin: 0; white-space: pre-wrap; }
.message-time { font-size: 11px; color: #666; margin-top: 5px; display: block; }
.chat-input { display: flex; gap: 10px; }
.analysis-panel { background: #1a1f25; border-radius: 15px; padding: 20px; }
.analysis-panel h3 { color: #fff; margin-bottom: 15px; }
.analysis-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
.analysis-card { background: #2f3336; padding: 20px; border-radius: 10px; }
.analysis-card h4 { color: #00d4ff; margin-bottom: 10px; }
.analysis-card p { color: #8899a6; margin: 5px 0; font-size: 14px; }
</style>
