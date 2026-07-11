<template>
  <div class="crowd-chart-wrapper" ref="chartRef" :style="{ height }"></div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  height: { type: String, default: '400px' },
})

const chartRef = ref(null)
let chart = null

// 人流等级 → 颜色映射
const LEVEL_COLORS = {
  1: '#27AE60',
  2: '#82C91E',
  3: '#F39C12',
  4: '#E67E22',
  5: '#E74C3C',
}

function initChart() {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const p = params[0]
        const d = props.data.find((item) => item.location_name === p.name || item.location === p.name)
        const count = d?.estimated_count ?? d?.count ?? '--'
        return `${p.name}<br/>人流等级：${p.value} 级<br/>预估人数：${count}`
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '12%',
      top: '10%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: [],
      axisLabel: { rotate: 30, fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      name: '人流等级',
      min: 0,
      max: 5,
      interval: 1,
      axisLabel: {
        formatter: (v) => {
          const labels = { 0: '', 1: '空闲', 2: '较少', 3: '适中', 4: '较多', 5: '拥挤' }
          return labels[v] || ''
        },
      },
    },
    series: [
      {
        type: 'bar',
        data: [],
        itemStyle: {
          borderRadius: [6, 6, 0, 0],
          color: (params) => LEVEL_COLORS[params.value] || '#95A5A6',
        },
        barMaxWidth: 60,
      },
    ],
  }

  chart.setOption(option)
}

function updateChart() {
  if (!chart) return
  const locations = props.data.map((d) => d.location_name || d.location || '')
  const levels = props.data.map((d) => d.crowd_level ?? d.level ?? 0)

  chart.setOption({
    xAxis: { data: locations },
    series: [{ data: levels }],
  })
}

watch(() => props.data, updateChart, { deep: true })

watch(() => props.loading, (v) => {
  if (!chart) return
  if (v) chart.showLoading()
  else chart.hideLoading()
})

onMounted(() => {
  initChart()
  if (props.data.length > 0) updateChart()
})

onUnmounted(() => {
  if (chart) {
    chart.dispose()
    chart = null
  }
})
</script>

<style scoped>
.crowd-chart-wrapper {
  width: 100%;
  min-height: 300px;
}
</style>
