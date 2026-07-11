<template>
  <div class="admin-page">
    <h1>数据大屏管理</h1>
    <div class="page-toolbar">
      <el-select v-model="region" placeholder="选择地区" style="width:140px" @change="refreshAll">
        <el-option label="汕头" value="汕头" /><el-option label="潮州" value="潮州" /><el-option label="揭阳" value="揭阳" /><el-option label="汕尾" value="汕尾" />
      </el-select>
      <el-button type="primary" @click="refreshWeather">手动拉取气象数据</el-button>
      <el-button @click="generateCrowd">生成人流模拟数据</el-button>
    </div>

    <div class="chart-grid">
      <div class="chart-card">
        <h3>📊 气象趋势 (24h)</h3>
        <WeatherChart :data="weatherData" :loading="weatherLoading" height="350px" />
      </div>
      <div class="chart-card">
        <h3>📊 人流热度 (24h)</h3>
        <CrowdChart :data="crowdData" :loading="crowdLoading" height="350px" />
      </div>
    </div>

    <h3 style="margin-top: 32px;">气象数据日志</h3>
    <el-table :data="weatherLogs" stripe size="small" max-height="300">
      <el-table-column prop="region" label="地区" width="80" />
      <el-table-column prop="temperature" label="温度(°C)" width="90" />
      <el-table-column prop="humidity" label="湿度(%)" width="80" />
      <el-table-column prop="weather_desc" label="天气" width="80" />
      <el-table-column prop="record_time" label="记录时间" width="160" />
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api/request'
import { toast } from '@/utils/toast'
import WeatherChart from '@/components/business/WeatherChart.vue'
import CrowdChart from '@/components/business/CrowdChart.vue'

const region = ref('汕头')
const weatherData = ref([]); const crowdData = ref([])
const weatherLoading = ref(false); const crowdLoading = ref(false)
const weatherLogs = ref([])

async function loadWeather() {
  weatherLoading.value = true
  try { const data = await api.get('/dashboard/weather', { params: { region: region.value } }); weatherData.value = data?.items || (Array.isArray(data) ? data : []) } catch { /* */ } finally { weatherLoading.value = false }
}
async function loadCrowd() {
  crowdLoading.value = true
  try { const data = await api.get('/dashboard/crowd', { params: { region: region.value } }); crowdData.value = data?.items || (Array.isArray(data) ? data : []) } catch { /* */ } finally { crowdLoading.value = false }
}
async function loadLogs() {
  try { const data = await api.get('/admin/weather-logs'); weatherLogs.value = data?.items?.slice(0, 20) || [] } catch { /* */ }
}

function refreshAll() { loadWeather(); loadCrowd() }

async function refreshWeather() {
  try { await api.post('/admin/refresh-weather'); toast.success('气象数据已刷新'); loadWeather(); loadLogs() } catch { toast.error('拉取失败') }
}
async function generateCrowd() {
  try { await api.post('/admin/generate-crowd'); toast.success('人流数据已生成'); loadCrowd() } catch { toast.error('生成失败') }
}

onMounted(() => { refreshAll(); loadLogs() })
</script>
<style scoped>
.admin-page h1 { font-size: 1.5rem; margin-bottom: 24px; }
.page-toolbar { display: flex; gap: 12px; margin-bottom: 24px; flex-wrap: wrap; }
.chart-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 24px; }
.chart-card { background: #fff; border-radius: var(--radius-lg); padding: 20px; box-shadow: var(--shadow-sm); }
.chart-card h3 { margin: 0 0 12px; font-size: 16px; }
</style>
