<template>
  <div class="admin-users-page">
    <div class="page-header">
      <h2>用户管理</h2>
      <button class="add-btn" @click="showAddModal = true">
        <span>+</span>
        <span>添加用户</span>
      </button>
    </div>
    
    <div class="filter-bar">
      <input 
        type="text" 
        class="search-input" 
        placeholder="搜索用户名..." 
        v-model="searchQuery"
      >
      <select class="filter-select" v-model="roleFilter">
        <option value="">全部角色</option>
        <option value="admin">管理员</option>
        <option value="user">普通用户</option>
      </select>
      <button class="refresh-btn" @click="loadUsers">🔄 刷新</button>
    </div>
    
    <div class="users-table">
      <table>
        <thead>
          <tr>
            <th>用户名</th>
            <th>邮箱</th>
            <th>角色</th>
            <th>状态</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in filteredUsers" :key="user.id">
            <td>{{ user.username }}</td>
            <td>{{ user.email || '-' }}</td>
            <td>
              <span class="role-badge" :class="user.role">
                {{ user.role === 'admin' ? '管理员' : '普通用户' }}
              </span>
            </td>
            <td>
              <span class="status-badge active">活跃</span>
            </td>
            <td>{{ formatDate(user.created_at) }}</td>
            <td class="actions">
              <button 
                class="action-btn edit" 
                @click="editUser(user)"
              >
                编辑
              </button>
              <button 
                class="action-btn reset" 
                @click="resetPassword(user)"
              >
                重置密码
              </button>
              <button 
                class="action-btn delete" 
                @click="deleteUser(user)"
                :disabled="user.username === currentUser?.username"
              >
                删除
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- 添加/编辑用户弹窗 -->
    <div v-if="showAddModal || editingUser" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editingUser ? '编辑用户' : '添加用户' }}</h3>
          <button class="close-btn" @click="closeModal">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>用户名</label>
            <input 
              type="text" 
              v-model="form.username" 
              placeholder="输入用户名"
              :disabled="!!editingUser"
            >
          </div>
          <div class="form-group">
            <label>邮箱</label>
            <input 
              type="email" 
              v-model="form.email" 
              placeholder="输入邮箱"
            >
          </div>
          <div class="form-group">
            <label>密码</label>
            <input 
              type="password" 
              v-model="form.password" 
              :placeholder="editingUser ? '留空则不修改密码' : '输入密码'"
            >
          </div>
          <div class="form-group">
            <label>角色</label>
            <select v-model="form.role">
              <option value="user">普通用户</option>
              <option value="admin">管理员</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="cancel-btn" @click="closeModal">取消</button>
          <button class="submit-btn" @click="saveUser">保存</button>
        </div>
      </div>
    </div>
    
    <!-- 重置密码弹窗 -->
    <div v-if="resettingUser" class="modal-overlay" @click.self="closeResetModal">
      <div class="modal small">
        <div class="modal-header">
          <h3>重置密码</h3>
          <button class="close-btn" @click="closeResetModal">×</button>
        </div>
        <div class="modal-body">
          <p>确定要重置用户 <strong>{{ resettingUser.username }}</strong> 的密码吗？</p>
          <div class="form-group">
            <label>新密码</label>
            <input type="password" v-model="newPassword" placeholder="输入新密码">
          </div>
        </div>
        <div class="modal-footer">
          <button class="cancel-btn" @click="closeResetModal">取消</button>
          <button class="submit-btn" @click="confirmReset">确认重置</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const users = ref([])
const searchQuery = ref('')
const roleFilter = ref('')
const showAddModal = ref(false)
const editingUser = ref(null)
const resettingUser = ref(null)
const newPassword = ref('')
const currentUser = ref(JSON.parse(sessionStorage.getItem('user') || 'null'))

const form = ref({
  username: '',
  email: '',
  password: '',
  role: 'user'
})

const filteredUsers = computed(() => {
  return users.value.filter(user => {
    const matchSearch = !searchQuery.value || 
      user.username.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchRole = !roleFilter.value || user.role === roleFilter.value
    return matchSearch && matchRole
  })
})

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const loadUsers = async () => {
  try {
    const resp = await fetch('/api/users', { credentials: 'include' })
    const data = await resp.json()
    users.value = data.data || []
  } catch (e) {
    console.error('获取用户列表失败', e)
  }
}

const editUser = (user) => {
  editingUser.value = user
  form.value = {
    username: user.username,
    email: user.email || '',
    password: '',
    role: user.role
  }
}

const closeModal = () => {
  showAddModal.value = false
  editingUser.value = null
  form.value = { username: '', email: '', password: '', role: 'user' }
}

const saveUser = async () => {
  if (!form.value.username) {
    alert('请输入用户名')
    return
  }
  
  try {
    const url = editingUser.value ? `/api/users/${editingUser.value.id}` : '/api/users'
    const method = editingUser.value ? 'PUT' : 'POST'
    
    const resp = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(form.value),
      credentials: 'include'
    })
    
    const data = await resp.json()
    
    if (resp.ok) {
      alert(editingUser.value ? '修改成功' : '添加成功')
      closeModal()
      loadUsers()
    } else {
      alert(data.error || '操作失败')
    }
  } catch (e) {
    console.error('保存用户失败', e)
    alert('保存失败')
  }
}

const resetPassword = (user) => {
  resettingUser.value = user
}

const closeResetModal = () => {
  resettingUser.value = null
  newPassword.value = ''
}

const confirmReset = async () => {
  if (!newPassword.value) {
    alert('请输入新密码')
    return
  }
  
  try {
    const resp = await fetch(`/api/users/${resettingUser.value.id}/password`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ password: newPassword.value }),
      credentials: 'include'
    })
    
    if (resp.ok) {
      alert('密码重置成功')
      closeResetModal()
    } else {
      const data = await resp.json()
      alert(data.error || '重置失败')
    }
  } catch (e) {
    console.error('重置密码失败', e)
    alert('重置失败')
  }
}

const deleteUser = async (user) => {
  if (user.username === currentUser.value?.username) {
    alert('不能删除自己')
    return
  }
  
  if (!confirm(`确定要删除用户 ${user.username} 吗？`)) return
  
  try {
    const resp = await fetch(`/api/users/${user.id}`, {
      method: 'DELETE',
      credentials: 'include'
    })
    
    if (resp.ok) {
      alert('删除成功')
      loadUsers()
    } else {
      const data = await resp.json()
      alert(data.error || '删除失败')
    }
  } catch (e) {
    console.error('删除用户失败', e)
    alert('删除失败')
  }
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.admin-users-page {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  color: #e7e9ea;
  font-size: 20px;
  margin: 0;
}

.add-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: #8b5cf6;
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 14px;
  cursor: pointer;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.search-input {
  flex: 1;
  padding: 12px;
  background: #1a1f25;
  border: 1px solid #38444d;
  border-radius: 8px;
  color: #e7e9ea;
  font-size: 14px;
}

.filter-select {
  padding: 12px;
  background: #1a1f25;
  border: 1px solid #38444d;
  border-radius: 8px;
  color: #e7e9ea;
  font-size: 14px;
}

.refresh-btn {
  padding: 12px 20px;
  background: #2a3038;
  border: none;
  border-radius: 8px;
  color: #e7e9ea;
  font-size: 14px;
  cursor: pointer;
}

.users-table {
  background: #1a1f25;
  border-radius: 12px;
  overflow: hidden;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead tr {
  background: #2a3038;
}

th {
  text-align: left;
  padding: 16px;
  color: #9ca3af;
  font-size: 14px;
  font-weight: 600;
}

td {
  padding: 16px;
  border-bottom: 1px solid #2a3038;
  color: #e7e9ea;
}

.role-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.role-badge.admin {
  background: rgba(139, 92, 246, 0.1);
  color: #8b5cf6;
}

.role-badge.user {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
}

.status-badge.active {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}

.action-btn.edit {
  background: #fbbf24;
  color: #1a1f25;
}

.action-btn.reset {
  background: #3b82f6;
  color: white;
}

.action-btn.delete {
  background: #ef4444;
  color: white;
}

.action-btn.delete:disabled {
  background: #374151;
  cursor: not-allowed;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: #1a1f25;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
}

.modal.small {
  max-width: 400px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #2a3038;
}

.modal-header h3 {
  color: #e7e9ea;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  color: #9ca3af;
  font-size: 24px;
  cursor: pointer;
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  color: #9ca3af;
  font-size: 14px;
  margin-bottom: 8px;
}

.form-group input, .form-group select {
  width: 100%;
  padding: 12px;
  background: #2a3038;
  border: 1px solid #38444d;
  border-radius: 8px;
  color: #e7e9ea;
  font-size: 14px;
}

.modal-body p {
  color: #e7e9ea;
  margin: 0 0 16px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid #2a3038;
}

.cancel-btn {
  padding: 10px 20px;
  background: #2a3038;
  border: none;
  border-radius: 8px;
  color: #e7e9ea;
  font-size: 14px;
  cursor: pointer;
}

.submit-btn {
  padding: 10px 20px;
  background: #8b5cf6;
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 14px;
  cursor: pointer;
}
</style>
