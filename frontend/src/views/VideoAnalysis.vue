<template>
  <div class="video-analysis">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>视频上传与分析</span>
        </div>
      </template>

      <el-form :model="form" label-width="100px">
        <el-form-item label="视频文件">
          <el-input v-model="form.videoPath" placeholder="请输入视频文件完整路径" />
        </el-form-item>
        <el-form-item label="检测模式">
          <el-radio-group v-model="form.mode">
            <el-radio label="realtime">实时检测</el-radio>
            <el-radio label="batch">批量分析</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="灵敏度">
          <el-slider v-model="form.sensitivity" :min="0" :max="100" :step="5" show-stops />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="startAnalysis" :loading="isAnalyzing">
            <el-icon><VideoPlay /></el-icon> 开始分析
          </el-button>
          <el-button @click="clearResults">
            <el-icon><Delete /></el-icon> 清除结果
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="results-card" v-if="analysisResults.length > 0">
      <template #header>
        <div class="card-header">
          <span>分析结果</span>
          <el-button type="success" size="small" @click="exportResults">
            <el-icon><Download /></el-icon> 导出报告
          </el-button>
        </div>
      </template>

      <el-table :data="analysisResults" stripe style="width: 100%">
        <el-table-column prop="timestamp" label="时间点" width="120" />
        <el-table-column prop="event" label="事件类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getEventType(row.event)">{{ row.event }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="action" label="行为" />
        <el-table-column prop="confidence" label="置信度" width="100">
          <template #default="{ row }">
            {{ (row.confidence * 100).toFixed(1) }}%
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="jumpToFrame(row)">
              跳转
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="analysisResults.length"
        layout="total, prev, pager, next"
        style="margin-top: 20px; justify-content: center"
      />
    </el-card>

    <el-card class="preview-card" v-if="currentPreview">
      <template #header>
        <span>事件预览</span>
      </template>
      <div class="preview-container">
        <img :src="currentPreview" alt="事件预览" class="preview-image" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'

const form = reactive({
  videoPath: '',
  mode: 'realtime',
  sensitivity: 50
})

const isAnalyzing = ref(false)
const analysisResults = ref([])
const currentPage = ref(1)
const pageSize = ref(10)
const currentPreview = ref('')

function startAnalysis() {
  if (!form.videoPath) {
    ElMessage.warning('请输入视频文件路径')
    return
  }

  isAnalyzing.value = true

  setTimeout(() => {
    analysisResults.value = [
      { timestamp: '00:15', event: '疑似跌倒', action: 'lying', confidence: 0.78 },
      { timestamp: '00:45', event: '跌倒告警', action: 'lying', confidence: 0.92 },
      { timestamp: '01:30', event: '恢复站起', action: 'standing', confidence: 0.85 }
    ]
    isAnalyzing.value = false
    ElMessage.success('分析完成')
  }, 2000)
}

function clearResults() {
  analysisResults.value = []
  currentPreview.value = ''
}

function exportResults() {
  const report = analysisResults.value.map(r =>
    `时间: ${r.timestamp}, 事件: ${r.event}, 行为: ${r.action}, 置信度: ${(r.confidence * 100).toFixed(1)}%`
  ).join('\n')

  const blob = new Blob(['检测报告\n\n' + report], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'detection_report.txt'
  a.click()
  URL.revokeObjectURL(url)

  ElMessage.success('报告已导出')
}

function getEventType(event) {
  const map = {
    '跌倒告警': 'danger',
    '疑似跌倒': 'warning',
    '恢复站起': 'success',
    '正常': 'info'
  }
  return map[event] || 'info'
}

function jumpToFrame(row) {
  currentPreview.value = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='640' height='480'%3E%3Crect fill='%23333' width='640' height='480'/%3E%3Ctext x='320' y='240' fill='white' text-anchor='middle' font-size='24'%3E${row.timestamp}%3C/text%3E%3C/svg%3E`
}
</script>

<style scoped>
.video-analysis {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.results-card,
.preview-card {
  margin-top: 20px;
}

.preview-container {
  display: flex;
  justify-content: center;
}

.preview-image {
  max-width: 100%;
  border-radius: 8px;
}
</style>
