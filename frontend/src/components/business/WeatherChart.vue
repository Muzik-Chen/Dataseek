<template>
  <div class="weather-chart-wrapper" ref="chartRef" :style="{ height }"></div>
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

function initChart() {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
    },
    legend: {
      data: ['温度 (°C)', '湿度 (%)'],
      bottom: 0,
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
    yAxis: [
      {
        type: 'value',
        name: '°C',
        axisLabel: { formatter: '{value}°' },
      },
      {
        type: 'value',
        name: '%',
        axisLabel: { formatter: '{value}%' },
      },
    ],
    series: [
      {
        name: '温度 (°C)',
        type: 'line',
        smooth: true,
        data: [],
        itemStyle: { color: '#E67E22' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(230,126,34,0.3)' },
            { offset: 1, color: 'rgba(230,126,34,0.02)' },
          ]),
        },
      },
      {
        name: '湿度 (%)',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        data: [],
        itemStyle: { color: '#3498DB' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(52,152,219,0.3)' },
            { offset: 1, color: 'rgba(52,152,219,0.02)' },
          ]),
        },
      },
    ],
    dataZoom: [{ type: 'inside' }, { type: 'slider', bottom: 24 }],
  }

  chart.setOption(option)
}

function updateChart() {
  if (!chart) return
  const times = props.data.map((d) => {
    const t = new Date(d.record_time || d.time)
    return `${t.getHours().toString().padStart(2, '0')}:00`
  })
  const temps = props.data.map((d) => d.temperature ?? d.temp ?? 0)
  const hums = props.data.map((d) => d.humidity ?? d.hum ?? 0)

  chart.setOption({
    xAxis: { data: times },
    series: [{ data: temps }, { data: hums }],
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
.weather-chart-wrapper {
  width: 100%;
  min-height: 300px;
}
</style>
