<template>
  <div class="statistics">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>检测事件统计</span>
          </template>
          <div ref="barChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>行为分布</span>
          </template>
          <div ref="pieChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>检测指标</span>
          </template>
          <el-table :data="metricsData" stripe>
            <el-table-column prop="name" label="指标" />
            <el-table-column prop="value" label="数值" />
            <el-table-column prop="description" label="说明" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>实时状态</span>
          </template>
          <div class="status-info">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="系统状态">
                <el-tag type="success">运行中</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="模型状态">
                <el-tag :type="modelLoaded ? 'success' : 'warning'">
                  {{ modelLoaded ? '已加载' : '未加载' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="数据库">
                <el-tag type="info">SQLite</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="最后更新">
                {{ lastUpdateTime }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const barChartRef = ref(null)
const pieChartRef = ref(null)

let barChart = null
let pieChart = null
let updateTimer = null

const modelLoaded = ref(false)
const lastUpdateTime = ref('--')

const metricsData = ref([
  { name: '总检测帧数', value: '0', description: '累计处理的视频帧数' },
  { name: '跌倒告警次数', value: '0', description: '触发跌倒告警的事件数' },
  { name: '疑似跌倒数', value: '0', description: '检测到疑似跌倒的事件数' },
  { name: '正常检测数', value: '0', description: '正常行为检测次数' }
])

async function fetchStatistics() {
  try {
    const response = await fetch('/api/statistics')
    const data = await response.json()

    metricsData.value = [
      { name: '总检测帧数', value: String(data.total || 0), description: '累计处理的视频帧数' },
      { name: '跌倒告警次数', value: String(data.alert_count || 0), description: '触发跌倒告警的事件数' },
      { name: '疑似跌倒数', value: String(data.warning_count || 0), description: '检测到疑似跌倒的事件数' },
      { name: '正常检测数', value: String(data.normal_count || 0), description: '正常行为检测次数' }
    ]

    updateCharts(data)
    lastUpdateTime.value = new Date().toLocaleTimeString('zh-CN')
  } catch (e) {
    console.error('Fetch statistics error:', e)
  }
}

async function checkStatus() {
  try {
    const response = await fetch('/api/status')
    const data = await response.json()
    modelLoaded.value = data.has_model
  } catch (e) {
    console.error('Check status error:', e)
  }
}

function initCharts() {
  if (barChartRef.value) {
    barChart = echarts.init(barChartRef.value)
  }

  if (pieChartRef.value) {
    pieChart = echarts.init(pieChartRef.value)
  }

  fetchStatistics()
}

function updateCharts(data) {
  if (barChart) {
    barChart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: ['跌倒告警', '疑似跌倒', '正常'] },
      yAxis: { type: 'value' },
      series: [{
        type: 'bar',
        data: [
          { value: data.alert_count || 0, itemStyle: { color: '#ff4757' } },
          { value: data.warning_count || 0, itemStyle: { color: '#ffaa00' } },
          { value: data.normal_count || 0, itemStyle: { color: '#00ff88' } }
        ],
        barWidth: '50%',
        itemStyle: { borderRadius: [10, 10, 0, 0] }
      }]
    })
  }

  if (pieChart) {
    const total = data.total || 0
    const other = Math.max(0, total - (data.alert_count || 0) - (data.warning_count || 0) - (data.normal_count || 0))

    pieChart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { bottom: 0 },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        data: [
          { value: data.alert_count || 0, name: '跌倒告警', itemStyle: { color: '#ff4757' } },
          { value: data.warning_count || 0, name: '疑似跌倒', itemStyle: { color: '#ffaa00' } },
          { value: data.normal_count || 0, name: '正常', itemStyle: { color: '#00ff88' } },
          { value: other, name: '未检测', itemStyle: { color: '#888' } }
        ].filter(item => item.value > 0),
        label: { show: true, formatter: '{b}: {c}' }
      }]
    })
  }
}

function handleResize() {
  barChart?.resize()
  pieChart?.resize()
}

onMounted(() => {
  initCharts()
  checkStatus()
  updateTimer = setInterval(() => {
    fetchStatistics()
    checkStatus()
  }, 5000)
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (updateTimer) clearInterval(updateTimer)
  window.removeEventListener('resize', handleResize)
  barChart?.dispose()
  pieChart?.dispose()
})
</script>

<style scoped>
.statistics {
  padding: 0;
}

.chart-container {
  height: 300px;
}

.status-info {
  padding: 10px 0;
}
</style>
