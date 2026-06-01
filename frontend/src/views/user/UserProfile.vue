<template>
  <div class="profile-page">
    <div class="profile-header">
      <div class="avatar-section">
        <div class="avatar">
          <span>{{ user?.username?.charAt(0)?.toUpperCase() || 'U' }}</span>
        </div>
        <div class="user-info">
          <h2>{{ user?.username }}</h2>
          <p>普通用户</p>
        </div>
      </div>
    </div>
    
    <div class="profile-content">
      <div class="section">
        <h3>基本信息</h3>
        <div class="info-grid">
          <div class="info-item">
            <label>用户名</label>
            <span>{{ user?.username }}</span>
          </div>
          <div class="info-item">
            <label>邮箱</label>
            <span>{{ user?.email || '未设置' }}</span>
          </div>
          <div class="info-item">
            <label>角色</label>
            <span>普通用户</span>
          </div>
          <div class="info-item">
            <label>注册时间</label>
            <span>{{ formatDate(user?.created_at) }}</span>
          </div>
        </div>
      </div>
      
      <div class="section">
        <h3>安全设置</h3>
        
        <div class="form-group">
          <label>修改密码</label>
          <div class="password-form">
            <input type="password" v-model="oldPassword" placeholder="旧密码">
            <input type="password" v-model="newPassword" placeholder="新密码">
            <input type="password" v-model="confirmPassword" placeholder="确认新密码">
            <button class="submit-btn" @click="changePassword">修改密码</button>
          </div>
        </div>
      </div>
      
      <div class="section">
        <h3>数据管理</h3>
        <div class="data-actions">
          <button class="data-btn" @click="exportData">
            <span>📥</span>
            <span>导出个人数据</span>
          </button>
          <button class="data-btn danger" @click="deleteAccount">
            <span>🗑️</span>
            <span>删除账户</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const userInfo = ref(sessionStorage.getItem('user') ? JSON.parse(sessionStorage.getItem('user')) : null)
const userId = ref(userInfo.value?.id || 1)

const user = ref(null)
const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')

const formatDate = (dateStr) => {
  if (!dateStr) return '未知'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const loadUser = async () => {
  try {
    const resp = await fetch('/api/auth/current', { 
      credentials: 'include',
      headers: {
        'X-User-Id': userId.value
      }
    })
    const data = await resp.json()
    if (resp.ok && data.success) {
      user.value = data.user
    } else {
      // 用户未登录，跳转到登录页
      console.error('用户未登录', data.error)
      sessionStorage.removeItem('user')
      window.location.href = '/login'
    }
  } catch (e) {
    console.error('获取用户信息失败', e)
  }
}

const changePassword = async () => {
  if (!oldPassword.value || !newPassword.value || !confirmPassword.value) {
    alert('请填写所有字段')
    return
  }
  
  if (newPassword.value !== confirmPassword.value) {
    alert('新密码和确认密码不一致')
    return
  }
  
  if (newPassword.value.length < 6) {
    alert('密码长度至少6位')
    return
  }
  
  try {
    const resp = await fetch('/api/auth/change-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        old_password: oldPassword.value,
        new_password: newPassword.value
      }),
      credentials: 'include'
    })
    
    const data = await resp.json()
    
    if (resp.ok) {
      alert('密码修改成功')
      oldPassword.value = ''
      newPassword.value = ''
      confirmPassword.value = ''
    } else {
      alert(data.error || '修改失败')
    }
  } catch (e) {
    console.error('修改密码失败', e)
    alert('修改密码失败')
  }
}

const exportData = async () => {
  try {
    const resp = await fetch('/api/report/export', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ format: 'json' }),
      credentials: 'include'
    })
    
    if (resp.ok) {
      const blob = await resp.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `my_data_${Date.now()}.json`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } else {
      alert('导出失败')
    }
  } catch (e) {
    console.error('导出数据失败', e)
    alert('导出数据失败')
  }
}

const deleteAccount = async () => {
  if (!confirm('确定要删除账户吗？此操作不可撤销！')) return
  
  try {
    const resp = await fetch('/api/users/me', {
      method: 'DELETE',
      credentials: 'include'
    })
    
    if (resp.ok) {
      sessionStorage.removeItem('user')
      window.location.href = '/login'
    } else {
      const data = await resp.json()
      alert(data.error || '删除失败')
    }
  } catch (e) {
    console.error('删除账户失败', e)
    alert('删除账户失败')
  }
}

onMounted(() => {
  loadUser()
})
</script>

<style scoped>
.profile-page {
  padding: 24px;
  width: 100%;
  max-width: none;
  margin: 0;
}

.profile-header {
  background: linear-gradient(135deg, #10b981, #059669);
  border-radius: 12px;
  padding: 32px;
  margin-bottom: 24px;
}

.avatar-section {
  display: flex;
  align-items: center;
}

.avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 36px;
  font-weight: 700;
  margin-right: 20px;
}

.user-info h2 {
  color: white;
  font-size: 24px;
  margin: 0;
}

.user-info p {
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  margin: 4px 0 0;
}

.profile-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.section {
  background: #1a1f25;
  border-radius: 12px;
  padding: 20px;
}

.section h3 {
  color: #e7e9ea;
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 16px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.info-item {
  padding: 12px;
  background: #2a3038;
  border-radius: 8px;
}

.info-item label {
  display: block;
  color: #6b7280;
  font-size: 12px;
  margin-bottom: 4px;
}

.info-item span {
  color: #e7e9ea;
  font-size: 14px;
}

.password-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.password-form input {
  padding: 12px;
  background: #2a3038;
  border: 1px solid #38444d;
  border-radius: 8px;
  color: #e7e9ea;
  font-size: 14px;
}

.submit-btn {
  padding: 12px;
  background: #10b981;
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.data-actions {
  display: flex;
  gap: 16px;
}

.data-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  background: #2a3038;
  border: none;
  border-radius: 8px;
  color: #e7e9ea;
  font-size: 14px;
  cursor: pointer;
}

.data-btn.danger {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

@media (max-width: 768px) {
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .data-actions {
    flex-direction: column;
  }
}
</style>
