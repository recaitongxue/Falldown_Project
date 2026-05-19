<template>
  <div class="test-page">
    <h1>测试页面</h1>
    <p>这是一个测试页面，用于验证系统是否正常工作</p>
    <div class="test-info">
      <p>当前路径: {{ $route.path }}</p>
      <p>用户: {{ user ? user.username : '未登录' }}</p>
      <p>角色: {{ user ? user.role : 'N/A' }}</p>
    </div>
    <button @click="goToLogin">返回登录</button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const user = ref(null)

onMounted(() => {
  console.log('TestPage mounted')
  const storedUser = sessionStorage.getItem('user')
  if (storedUser) {
    user.value = JSON.parse(storedUser)
    console.log('用户信息:', user.value)
  } else {
    console.log('未登录')
  }
})

const goToLogin = () => {
  sessionStorage.removeItem('user')
  window.location.href = '/login'
}
</script>

<style scoped>
.test-page {
  padding: 40px;
  text-align: center;
  background: #1a1f25;
  min-height: 100vh;
}

.test-page h1 {
  color: #8b5cf6;
  font-size: 32px;
  margin-bottom: 20px;
}

.test-page p {
  color: #e7e9ea;
  font-size: 16px;
}

.test-info {
  margin: 20px 0;
  padding: 20px;
  background: #2a3038;
  border-radius: 8px;
  text-align: left;
}

.test-info p {
  margin: 8px 0;
}

button {
  padding: 12px 24px;
  background: #8b5cf6;
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 16px;
  cursor: pointer;
}
</style>
