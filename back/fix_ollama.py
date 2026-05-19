import re

# 读取前端AdminSettings.vue
with open('../frontend/src/views/admin/AdminSettings.vue', 'r', encoding='utf-8') as f:
    frontend_content = f.read()

# 修改前端：添加动态获取Ollama模型列表
old_select = '''        <div class="setting-item">
          <label class="setting-label">Ollama 模型</label>
          <div class="setting-control">
            <select v-model="aiSettings.ollama_model">
              <option value="llama3">llama3</option>
              <option value="phi3">phi3</option>
              <option value="mistral">mistral</option>
            </select>
          </div>
        </div>'''

new_select = '''        <div class="setting-item">
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
        </div>'''

frontend_content = frontend_content.replace(old_select, new_select)

# 修改前端：添加ollamaModels和ollamaAvailable变量
old_import = 'import { ref, onMounted } from \'vue\'\n\nconst securitySettings = ref({'

new_import = 'import { ref, onMounted } from \'vue\'\n\nconst ollamaModels = ref([])\nconst ollamaAvailable = ref(false)\n\nconst securitySettings = ref({'

frontend_content = frontend_content.replace(old_import, new_import)

# 修改前端：添加加载Ollama模型的函数
old_load_settings = '''const loadSettings = async () => {
  try {
    const resp = await fetch('/api/settings', { credentials: 'include' })
    const data = await resp.json()
    Object.assign(securitySettings.value, data.security || {})
    Object.assign(aiSettings.value, data.ai || {})
    Object.assign(videoSettings.value, data.video || {})
    Object.assign(alertSettings.value, data.alert || {})
  } catch (e) {
    console.error('加载设置失败', e)
  }
}'''

new_load_settings = '''const loadSettings = async () => {
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
}'''

frontend_content = frontend_content.replace(old_load_settings, new_load_settings)

# 修改前端：修改saveSettings使用正确的API格式
old_save_settings = '''const saveSettings = async () => {
  try {
    const resp = await fetch('/api/settings', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        security: securitySettings.value,
        ai: aiSettings.value,
        video: videoSettings.value,
        alert: alertSettings.value
      }),
      credentials: 'include'
    })
    
    if (resp.ok) {
      alert('设置保存成功')
    } else {
      alert('保存失败')
    }
  } catch (e) {
    console.error('保存设置失败', e)
    alert('保存失败')
  }
}'''

new_save_settings = '''const saveSettings = async () => {
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
}'''

frontend_content = frontend_content.replace(old_save_settings, new_save_settings)

# 修改前端：修改onMounted调用loadOllamaModels
old_on_mounted = '''onMounted(() => {
  loadSettings()
})'''

new_on_mounted = '''onMounted(() => {
  loadSettings()
  loadOllamaModels()
})'''

frontend_content = frontend_content.replace(old_on_mounted, new_on_mounted)

# 写入前端文件
with open('../frontend/src/views/admin/AdminSettings.vue', 'w', encoding='utf-8') as f:
    f.write(frontend_content)

print('AdminSettings.vue updated successfully!')

# 现在修改后端添加管理员端智能助手API
with open('app.py', 'r', encoding='utf-8') as f:
    backend_content = f.read()

# 添加管理员端智能助手API
new_admin_ai_api = '''

@app.route('/api/admin/ai/chat', methods=['POST'])
def admin_ai_chat():
    """管理员端AI智能助手"""
    from ai_agent import get_ai_agent
    
    data = request.get_json()
    message = data.get('message', '')
    
    if not message:
        return jsonify({'success': False, 'error': '消息不能为空'}), 400
    
    try:
        agent = get_ai_agent()
        response = agent.chat(message)
        
        return jsonify({
            'success': True,
            'response': response
        }), 200
    except Exception as e:
        print(f"Admin AI chat error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/ai/analyze', methods=['POST'])
def admin_ai_analyze():
    """管理员端AI数据分析"""
    from ai_agent import get_ai_agent
    
    data = request.get_json()
    analysis_type = data.get('type', '')
    
    if not analysis_type:
        return jsonify({'success': False, 'error': '分析类型不能为空'}), 400
    
    try:
        agent = get_ai_agent()
        
        if analysis_type == 'system_summary':
            total_users = User.query.count()
            total_alerts = Alert.query.count()
            total_detections = DetectionRecord.query.count()
            fall_detections = DetectionRecord.query.filter_by(fall_detected=True).count()
            
            summary = "系统数据分析报告:\\n"
            summary += f"- 总用户数: {total_users}\\n"
            summary += f"- 总告警数: {total_alerts}\\n"
            summary += f"- 总检测次数: {total_detections}\\n"
            summary += f"- 跌倒检测次数: {fall_detections}\\n"
            summary += f"- 跌倒检测率: {fall_detections / max(total_detections, 1) * 100:.1f}%\\n"
            summary += "\\n请基于以上数据提供分析建议。"
            
            response = agent.chat(summary)
            
        elif analysis_type == 'user_risk':
            user_id = data.get('user_id')
            if user_id:
                user = User.query.get(user_id)
                if user:
                    detections = DetectionRecord.query.filter_by(user_id=user_id).count()
                    falls = DetectionRecord.query.filter_by(user_id=user_id, fall_detected=True).count()
                    
                    user_summary = "用户风险分析报告:\\n"
                    user_summary += f"用户名: {user.username}\\n"
                    user_summary += f"邮箱: {user.email}\\n"
                    user_summary += f"注册时间: {user.created_at}\\n"
                    user_summary += f"检测次数: {detections}\\n"
                    user_summary += f"跌倒事件: {falls}\\n"
                    risk_level = '高' if falls > 10 else '中' if falls > 3 else '低'
                    user_summary += f"风险等级: {risk_level}\\n"
                    user_summary += "\\n请分析该用户的健康风险并提供建议。"
                    
                    response = agent.chat(user_summary)
                else:
                    return jsonify({'success': False, 'error': '用户不存在'}), 404
            else:
                return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
        
        elif analysis_type == 'alert_trend':
            alerts = Alert.query.order_by(Alert.sent_at.desc()).limit(30).all()
            recent_alerts = [{'time': a.sent_at.strftime('%Y-%m-%d %H:%M'), 'severity': a.severity} for a in alerts]
            
            trend_summary = "最近30条告警记录趋势分析:\\n"
            trend_summary += str(recent_alerts) + "\\n"
            trend_summary += "\\n请分析告警趋势并提供优化建议。"
            
            response = agent.chat(trend_summary)
        
        else:
            return jsonify({'success': False, 'error': '未知的分析类型'}), 400
        
        return jsonify({
            'success': True,
            'response': response
        }), 200
    except Exception as e:
        print(f"Admin AI analyze error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
'''

# 添加到后端文件末尾
backend_content += new_admin_ai_api

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(backend_content)

print('app.py updated with admin AI APIs!')