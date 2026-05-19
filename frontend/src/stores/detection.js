import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useDetectionStore = defineStore('detection', () => {
  const isDetecting = ref(false)
  const currentStatus = ref('idle')
  const lastResult = ref(null)
  const detectionHistory = ref([])
  const statistics = ref({
    totalFrames: 0,
    fallCount: 0,
    warningCount: 0,
    normalCount: 0,
    alertCount: 0
  })

  const statusText = computed(() => {
    if (currentStatus.value === 'alert') return '🚨 跌倒告警'
    if (currentStatus.value === 'warning') return '⚠️ 疑似跌倒'
    if (currentStatus.value === 'detecting') return '✓ 实时监测中'
    return '等待检测'
  })

  const statusType = computed(() => {
    if (currentStatus.value === 'alert') return 'danger'
    if (currentStatus.value === 'warning') return 'warning'
    if (currentStatus.value === 'detecting') return 'success'
    return 'info'
  })

  function updateResult(result) {
    lastResult.value = result
    currentStatus.value = result.alert ? 'alert' : result.fall_detected ? 'warning' : 'detecting'

    statistics.value.totalFrames++

    if (result.alert) {
      statistics.value.alertCount++
    }

    if (result.fall_detected) {
      statistics.value.fallCount++
    }

    detectionHistory.value.unshift({
      id: Date.now(),
      timestamp: new Date().toISOString(),
      ...result
    })

    if (detectionHistory.value.length > 100) {
      detectionHistory.value.pop()
    }
  }

  function setDetecting(value) {
    isDetecting.value = value
    if (!value) {
      currentStatus.value = 'idle'
    }
  }

  function resetStatistics() {
    statistics.value = {
      totalFrames: 0,
      fallCount: 0,
      warningCount: 0,
      normalCount: 0,
      alertCount: 0
    }
    detectionHistory.value = []
  }

  return {
    isDetecting,
    currentStatus,
    lastResult,
    detectionHistory,
    statistics,
    statusText,
    statusType,
    updateResult,
    setDetecting,
    resetStatistics
  }
})
