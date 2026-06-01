<template>
  <div class="login-container">
    <div class="login-box">
      <h1 class="login-title">居家老人行为监测与跌倒智能预警系统</h1>
      <p class="login-subtitle">Fall Detection System</p>
      
      <!-- 切换标签 -->
      <div class="tab-switch">
        <button 
          class="tab-btn" 
          :class="{ active: isLoginMode }"
          @click="isLoginMode = true"
        >
          登录
        </button>
        <button 
          class="tab-btn" 
          :class="{ active: !isLoginMode }"
          @click="isLoginMode = false"
        >
          注册
        </button>
      </div>

      <!-- 登录表单 -->
      <el-form v-if="isLoginMode" :model="loginForm" class="login-form">
        <el-form-item>
          <el-input
            v-model="loginForm.username"
            placeholder="用户名"
            :prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="密码"
            :prefix-icon="Lock"
            size="large"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-button"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 注册表单 -->
      <el-form v-else :model="registerForm" class="login-form">
        <el-form-item>
          <el-input
            v-model="registerForm.username"
            placeholder="用户名"
            :prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="registerForm.email"
            type="email"
            placeholder="邮箱（选填）"
            :prefix-icon="Message"
            size="large"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="密码（至少6位）"
            :prefix-icon="Lock"
            size="large"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="registerForm.confirmPassword"
            type="password"
            placeholder="确认密码"
            :prefix-icon="Lock"
            size="large"
            @keyup.enter="handleRegister"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-button"
            @click="handleRegister"
          >
            注册
          </el-button>
        </el-form-item>
      </el-form>

    </div>

    <div class="system-info">
      <p>智能跌倒检测 | AI-Powered Fall Detection</p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Message } from '@element-plus/icons-vue'

const router = useRouter()
const loading = ref(false)
const isLoginMode = ref(true)

const loginForm = reactive({
  username: '',
  password: ''
})

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

async function handleLogin() {
  if (!loginForm.username) {
    ElMessage.warning('请输入用户名')
    return
  }

  loading.value = true
  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(loginForm),
      credentials: 'include'
    })

    const data = await response.json()

    if (data.status === 'ok') {
      ElMessage.success(`欢迎 ${data.user.username}!`)
      sessionStorage.setItem('user', JSON.stringify(data.user))
      const path = data.user.role === 'admin' ? '/admin' : '/user'
      router.push(path)
    } else {
      ElMessage.error(data.error || '登录失败')
    }
  } catch (e) {
    ElMessage.error('登录出错: ' + e.message)
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  if (!registerForm.username) {
    ElMessage.warning('请输入用户名')
    return
  }
  if (!registerForm.password) {
    ElMessage.warning('请输入密码')
    return
  }
  if (registerForm.password.length < 6) {
    ElMessage.warning('密码长度至少6位')
    return
  }
  if (registerForm.password !== registerForm.confirmPassword) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }

  loading.value = true
  try {
    const response = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: registerForm.username,
        password: registerForm.password,
        email: registerForm.email
      })
    })

    const data = await response.json()

    if (data.status === 'ok') {
      ElMessage.success('注册成功，请登录')
      isLoginMode.value = true
      registerForm.username = ''
      registerForm.email = ''
      registerForm.password = ''
      registerForm.confirmPassword = ''
    } else {
      ElMessage.error(data.error || '注册失败')
    }
  } catch (e) {
    ElMessage.error('注册出错: ' + e.message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-box {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 50px;
  width: 420px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.login-title {
  font-size: 32px;
  color: #1a1a2e;
  text-align: center;
  margin-bottom: 5px;
}

.login-subtitle {
  font-size: 14px;
  color: #666;
  text-align: center;
  margin-bottom: 20px;
}

.tab-switch {
  display: flex;
  margin-bottom: 20px;
  border-radius: 10px;
  background: #f5f5f5;
  padding: 4px;
}

.tab-btn {
  flex: 1;
  padding: 10px;
  border: none;
  border-radius: 8px;
  background: transparent;
  font-size: 14px;
  font-weight: 500;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn.active {
  background: #667eea;
  color: white;
}

.login-form {
  margin-top: 10px;
}

.login-button {
  width: 100%;
  height: 50px;
  font-size: 18px;
  border-radius: 10px;
}

.login-tips {
  margin-top: 20px;
  text-align: center;
  color: #888;
  font-size: 12px;
}

.system-info {
  margin-top: 30px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
}
</style>
