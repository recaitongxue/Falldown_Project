<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'

onMounted(() => {
  document.title = '跌倒检测系统 - Fall Detection System'
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Microsoft YaHei', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background: #0f1419;
  color: #e7e9ea;
}

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #1a1f25;
}

::-webkit-scrollbar-thumb {
  background: #38444d;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #4f606e;
}
</style>
