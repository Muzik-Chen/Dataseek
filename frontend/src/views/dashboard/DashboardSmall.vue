<template>
  <div class="dashboard-page">
<<<<<<< HEAD
    <!-- 页面标题 · 不对称左对齐 -->
=======
    <BackButton />
    <!-- 页面标题 -->
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
    <div class="page-header">
      <h1 class="display-text--section">📊 数据大屏</h1>
      <p>潮汕文化平台实时数据概览</p>
      <div class="section-divider section-divider--left"></div>
    </div>

<<<<<<< HEAD
    <!-- 概览卡片 -->
    <div v-if="overviewError" class="dash-error">
      <el-alert type="error" title="概览数据加载失败" :closable="false" show-icon />
      <el-button size="small" @click="loadOverview" class="retry-btn">重新加载</el-button>
    </div>
    <div v-else class="overview-cards">
      <div class="ov-card">
        <span class="ov-icon">👥</span>
        <div class="ov-info">
          <strong>{{ overview.total_users }}</strong>
          <span>注册用户</span>
        </div>
      </div>
      <div class="ov-card">
        <span class="ov-icon">🍲</span>
        <div class="ov-info">
          <strong>{{ overview.total_foods }}</strong>
          <span>美食条目</span>
        </div>
      </div>
      <div class="ov-card">
        <span class="ov-icon">🎭</span>
        <div class="ov-info">
          <strong>{{ overview.total_heritages }}</strong>
          <span>非遗项目</span>
        </div>
      </div>
      <div class="ov-card">
        <span class="ov-icon">💬</span>
        <div class="ov-info">
          <strong>{{ overview.total_posts }}</strong>
          <span>社区动态</span>
        </div>
      </div>
      <div class="ov-card">
        <span class="ov-icon">🤖</span>
        <div class="ov-info">
          <strong>{{ overview.today_chats }}</strong>
          <span>今日咨询</span>
        </div>
      </div>
    </div>

    <div class="dashboard-grid">
      <!-- 热门区域 -->
      <section class="dash-section">
        <h3>🔥 热门区域</h3>
        <div class="region-list">
          <div
            v-for="(region, i) in overview.hot_regions"
            :key="i"
            class="region-item"
          >
            <span class="region-rank">{{ i + 1 }}</span>
            <div class="region-info">
              <strong>{{ region.region }}</strong>
              <span>{{ region.location_name }}</span>
            </div>
            <div class="region-stats">
              <span class="crowd-level">
                人流 {{ '🟢🟡🔴'[region.crowd_level - 1] || '🟢' }}
              </span>
              <span v-if="region.temperature">{{ region.temperature }}°C</span>
            </div>
          </div>
          <div v-if="!overview.hot_regions?.length" class="empty-row">
            <p>暂无数据</p>
          </div>
        </div>
      </section>

      <!-- 天气 -->
=======
    <!-- ===== 人流趋势图 · 双Y轴平滑面积折线 ===== -->
    <section class="dash-section chart-section">
      <div class="chart-header">
        <h3>👥 区域人流量趋势 & 预测</h3>
        <el-button size="small" :loading="historyLoading" @click="loadCrowdHistory">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>

      <!-- 错误状态 -->
      <div v-if="historyError" class="dash-error">
        <el-alert
          :type="historyErrorType"
          :title="historyErrorMessage"
          :closable="false"
          show-icon
        />
      </div>

      <!-- 图表 -->
      <div v-else ref="chartRef" class="trend-chart"></div>
    </section>

    <!-- ===== 天气 + 实时人流 ===== -->
    <div class="dashboard-grid">
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
      <section class="dash-section">
        <h3>🌤️ 天气数据</h3>
        <div v-if="weatherData.length" class="weather-list">
          <div v-for="w in weatherData.slice(0, 8)" :key="w.id" class="weather-item">
            <span class="weather-region">{{ w.region }}</span>
            <span class="weather-temp">{{ w.temperature }}°C</span>
            <span class="weather-desc">{{ w.weather_desc }}</span>
            <span class="weather-humidity">💧 {{ w.humidity }}%</span>
          </div>
        </div>
        <div v-else-if="weatherError" class="dash-error">
          <el-alert type="error" title="天气数据加载失败" :closable="false" show-icon />
          <el-button size="small" @click="loadWeather" class="retry-btn">重新加载</el-button>
        </div>
        <div v-else class="empty-row">
          <p>暂无天气数据</p>
        </div>
      </section>

<<<<<<< HEAD
      <!-- 人流 -->
=======
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
      <section class="dash-section">
        <h3>👥 实时人流</h3>
        <div v-if="crowdData.length" class="crowd-list">
          <div v-for="c in crowdData.slice(0, 8)" :key="c.id" class="crowd-item">
            <div class="crowd-location">
              <strong>{{ c.location_name }}</strong>
              <span>{{ c.region }}</span>
            </div>
            <el-progress
              :percentage="c.crowd_level * 20"
              :color="crowdColor(c.crowd_level)"
              :show-text="false"
              style="flex:1"
            />
            <span class="crowd-label">{{ crowdLabel(c.crowd_level) }}</span>
          </div>
        </div>
        <div v-else-if="crowdError" class="dash-error">
          <el-alert type="error" title="人流数据加载失败" :closable="false" show-icon />
          <el-button size="small" @click="loadCrowd" class="retry-btn">重新加载</el-button>
        </div>
        <div v-else class="empty-row">
          <p>暂无人流数据</p>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
<<<<<<< HEAD
import { ref, onMounted } from 'vue'
import { getWeather, getCrowd } from '@/api'

const overview = ref({
  total_users: 0,
  total_foods: 0,
  total_heritages: 0,
  total_posts: 0,
  today_chats: 0,
  hot_regions: [],
})

const weatherData = ref([])
const crowdData = ref([])

/* Error state tracking — was silent catch{} before */
const overviewError = ref(false)
const weatherError = ref(false)
const crowdError = ref(false)

function crowdColor(level) {
  if (level <= 2) return '#52c41a'
  if (level <= 3) return '#faad14'
  return '#f5222d'
}

function crowdLabel(level) {
  if (level <= 2) return '舒适'
  if (level <= 3) return '较挤'
  return '拥挤'
}

async function loadOverview() {
  overviewError.value = false
  try {
    const resp = await fetch('/api/v1/dashboard/overview')
    const data = await resp.json()
    if (data.code === 0) overview.value = data.data
  } catch {
    overviewError.value = true
  }
}

=======
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { getWeather, getCrowd, getCrowdHistory } from '@/api'
import BackButton from '@/components/common/BackButton.vue'

// ── 状态 ──
const weatherData = ref([])
const crowdData = ref([])
const weatherError = ref(false)
const crowdError = ref(false)

const historyLoading = ref(false)
const historyError = ref(false)
const historyErrorType = ref('error')   // 'error' | 'warning'
const historyErrorMessage = ref('')

const chartRef = ref(null)
let chart = null
let resizeObserver = null

// ── 颜色 & 标签 ──
const LEVEL_COLORS = { 1: '#52c41a', 2: '#82C91E', 3: '#faad14', 4: '#E67E22', 5: '#f5222d' }

function crowdColor(level) {
  return LEVEL_COLORS[level] || '#95A5A6'
}
function crowdLabel(level) {
  const map = { 1: '空闲', 2: '较少', 3: '适中', 4: '较多', 5: '拥挤' }
  return map[level] || '未知'
}

// ── 日期工具 ──
function fmtDate(d) {
  const m = d.getMonth() + 1, day = d.getDate()
  return `${m}/${day}`
}

// ── 图表初始化 ──
function initChart() {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)

  chart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross', crossStyle: { color: '#999' } },
      formatter: (params) => {
        let html = `<strong>${params[0].axisValue}</strong><br/>`
        params.forEach(p => {
          if (p.seriesName === '预测人流') return
          html += `${p.marker} ${p.seriesName}: ${p.value}${p.seriesIndex === 0 ? ' 级' : ' 人'}<br/>`
        })
        return html
      },
    },
    legend: {
      data: ['人流等级', '预估人数', '预测人流', '预测人数'],
      bottom: 0,
      textStyle: { fontSize: 12 },
    },
    grid: { left: '3%', right: '5%', bottom: '12%', top: '8%', containLabel: true },
    xAxis: {
      type: 'category',
      data: [],
      axisLabel: { fontSize: 11 },
      boundaryGap: false,
    },
    yAxis: [
      {
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
      {
        type: 'value',
        name: '预估人数',
        axisLabel: { formatter: (v) => (v >= 1000 ? (v / 1000).toFixed(1) + 'k' : v) },
      },
    ],
    series: [
      {
        name: '人流等级',
        type: 'line',
        data: [],
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        yAxisIndex: 0,
        lineStyle: { color: '#E74C3C', width: 2 },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(231, 76, 60, 0.25)' },
          { offset: 1, color: 'rgba(231, 76, 60, 0.02)' },
        ])},
        itemStyle: { color: '#E74C3C' },
      },
      {
        name: '预估人数',
        type: 'line',
        data: [],
        smooth: true,
        symbol: 'diamond',
        symbolSize: 6,
        yAxisIndex: 1,
        lineStyle: { color: '#3498DB', width: 2 },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(52, 152, 219, 0.25)' },
          { offset: 1, color: 'rgba(52, 152, 219, 0.02)' },
        ])},
        itemStyle: { color: '#3498DB' },
      },
      {
        name: '预测人流',
        type: 'line',
        data: [],
        smooth: true,
        symbol: 'emptyCircle',
        symbolSize: 6,
        yAxisIndex: 0,
        lineStyle: { color: '#E74C3C', width: 2, type: 'dashed' },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(231, 76, 60, 0.15)' },
          { offset: 1, color: 'rgba(231, 76, 60, 0.01)' },
        ])},
        itemStyle: { color: '#E74C3C' },
      },
      {
        name: '预测人数',
        type: 'line',
        data: [],
        smooth: true,
        symbol: 'emptyDiamond',
        symbolSize: 6,
        yAxisIndex: 1,
        lineStyle: { color: '#3498DB', width: 2, type: 'dashed' },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(52, 152, 219, 0.15)' },
          { offset: 1, color: 'rgba(52, 152, 219, 0.01)' },
        ])},
        itemStyle: { color: '#3498DB' },
      },
    ],
  })

  resizeObserver = new ResizeObserver(() => chart?.resize())
  resizeObserver.observe(chartRef.value)
}

// ── 加载人流历史数据 ──
async function loadCrowdHistory() {
  historyLoading.value = true
  historyError.value = false
  try {
    const data = await getCrowdHistory({ days: 7 })

    // data 预期格式: { current: {date, level, count}, history: [{date, level, count}, ...] }
    const current = data?.current || null
    const history = data?.history || (Array.isArray(data) ? data : (data?.items || []))

    if (!history.length && !current) {
      historyError.value = true
      historyErrorType.value = 'error'
      historyErrorMessage.value = '概览数据加载失败'
      return
    }

    // 构建 X 轴日期
    const today = new Date()

    // 历史日期（过去7天）
    const histDates = []
    for (let i = history.length - 1; i >= 0; i--) {
      const d = new Date(today)
      d.setDate(d.getDate() - (i + 1))
      histDates.push({ date: fmtDate(d), ...history[i] })
    }
    // 如果 history 为空，生成占位日期
    if (!history.length) {
      for (let i = 7; i >= 1; i--) {
        const d = new Date(today)
        d.setDate(d.getDate() - i)
        histDates.push({ date: fmtDate(d), level: null, count: null })
      }
    }

    // 今天（当前数据）
    const todayLabel = '今天'
    const todayLevel = current?.crowd_level ?? current?.level ?? null
    const todayCount = current?.estimated_count ?? current?.count ?? null

    // 计算平均值
    const validHistory = [...histDates, ...(todayLevel != null ? [{ level: todayLevel, count: todayCount }] : [])]
      .filter(d => d.level != null && d.count != null)

    const avgLevel = validHistory.length > 0
      ? +(validHistory.reduce((s, d) => s + d.level, 0) / validHistory.length).toFixed(1)
      : null
    const avgCount = validHistory.length > 0
      ? Math.round(validHistory.reduce((s, d) => s + d.count, 0) / validHistory.length)
      : null

    // 预测未来3天
    const predDates = []
    for (let i = 1; i <= 3; i++) {
      const d = new Date(today)
      d.setDate(d.getDate() + i)
      predDates.push({ date: fmtDate(d), level: avgLevel, count: avgCount })
    }

    // 组装图表数据
    const xLabels = [...histDates.map(h => h.date), todayLabel, ...predDates.map(p => p.date)]

    const levelSeries = [
      ...histDates.map(h => h.level ?? null),
      todayLevel,
      ...predDates.map(() => null),
    ]
    const countSeries = [
      ...histDates.map(h => h.count ?? null),
      todayCount,
      ...predDates.map(() => null),
    ]
    const predLevelSeries = [
      ...histDates.map(() => null),
      null,
      ...predDates.map(p => p.level),
    ]
    const predCountSeries = [
      ...histDates.map(() => null),
      null,
      ...predDates.map(p => p.count),
    ]

    await nextTick()
    if (!chart) initChart()

    chart?.setOption({
      xAxis: { data: xLabels },
      series: [
        { data: levelSeries },
        { data: countSeries },
        { data: predLevelSeries },
        { data: predCountSeries },
      ],
    })
  } catch (err) {
    historyError.value = true
    // 判断是否为网络错误
    const msg = err?.message || ''
    if (msg.includes('网络') || msg.includes('Network') || msg.includes('ECONN') || msg.includes('timeout') || msg.includes('超时')) {
      historyErrorType.value = 'warning'
      historyErrorMessage.value = '当前网络不佳，请重新加载'
    } else {
      historyErrorType.value = 'error'
      historyErrorMessage.value = '概览数据加载失败'
    }
  } finally {
    historyLoading.value = false
  }
}

// ── 天气 / 实时人流 ──
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
async function loadWeather() {
  weatherError.value = false
  try {
    const data = await getWeather({ limit: 24 })
    weatherData.value = Array.isArray(data) ? data : (data.items || [])
  } catch {
    weatherError.value = true
  }
}

async function loadCrowd() {
  crowdError.value = false
  try {
    const data = await getCrowd({ limit: 24 })
    crowdData.value = Array.isArray(data) ? data : (data.items || [])
  } catch {
    crowdError.value = true
  }
}

onMounted(() => {
<<<<<<< HEAD
  loadOverview()
  loadWeather()
  loadCrowd()
})
=======
  loadCrowdHistory()
  loadWeather()
  loadCrowd()
})

onUnmounted(() => {
  if (resizeObserver) { resizeObserver.disconnect(); resizeObserver = null }
  if (chart) { chart.dispose(); chart = null }
})
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
</script>

<style scoped>
.dashboard-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-2xl) var(--space-md);
}

.page-header { margin-bottom: var(--space-2xl); }
<<<<<<< HEAD

.page-header h1 { font-size: var(--fs-2xl); color: var(--ink); margin: 0 0 var(--space-xs); }
.page-header p { color: var(--muted); margin: 0 0 var(--space-md); }

/* Overview cards */
.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--space-lg);
  margin-bottom: var(--space-2xl);
}

.ov-card {
  background: var(--surface);
  border-radius: 16px;
  padding: var(--space-xl);
  display: flex;
  align-items: center;
  gap: var(--space-md);
  box-shadow: 0 2px 8px oklch(0 0 0 / 0.03);
}

.ov-icon { font-size: 32px; }

.ov-info strong { display: block; font-size: var(--fs-2xl); color: var(--ink); }
.ov-info span { font-size: var(--fs-sm); color: var(--muted); }
=======
.page-header h1 { font-size: var(--fs-2xl); color: var(--ink); margin: 0 0 var(--space-xs); }
.page-header p { color: var(--muted); margin: 0 0 var(--space-md); }

/* 图表区块 */
.chart-section { margin-bottom: var(--space-2xl); }

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-md);
}

.chart-header h3 {
  font-size: var(--fs-lg);
  color: var(--ink);
  margin: 0;
}

.trend-chart {
  width: 100%;
  height: 420px;
}
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22

/* Grid */
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: var(--space-xl);
}

.dash-section {
  background: var(--surface);
  border-radius: 16px;
  padding: var(--space-xl);
  box-shadow: 0 2px 8px oklch(0 0 0 / 0.03);
}

.dash-section h3 {
  font-size: var(--fs-lg);
  color: var(--ink);
  margin: 0 0 var(--space-lg);
}

<<<<<<< HEAD
.region-list, .weather-list, .crowd-list {
=======
.weather-list, .crowd-list {
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

<<<<<<< HEAD
.region-item {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-sm) 0;
}

.region-rank {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--brand-red);
  color: #fff;
  border-radius: 50%;
  font-size: var(--fs-xs);
  font-weight: 700;
}

.region-info { flex: 1; }
.region-info strong { display: block; color: var(--ink); font-size: var(--fs-sm); }
.region-info span { color: var(--muted); font-size: var(--fs-xs); }

.region-stats { display: flex; gap: var(--space-md); font-size: var(--fs-xs); color: var(--muted); }

=======
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
.weather-item, .crowd-item {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-sm) 0;
  font-size: var(--fs-sm);
}

.weather-region, .crowd-location strong { color: var(--ink); font-weight: 500; min-width: 60px; }
.weather-desc { flex: 1; color: var(--muted); }
.crowd-location span { font-size: var(--fs-xs); color: var(--muted); display: block; }
.crowd-label { font-size: var(--fs-xs); color: var(--muted); min-width: 32px; text-align: right; }

.dash-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-xl);
}

.retry-btn { margin-top: var(--space-sm); }
<<<<<<< HEAD

.empty-row { text-align: center; color: var(--muted); padding: var(--space-xl); font-size: var(--fs-sm); }

@media (max-width: 768px) {
  .overview-cards { grid-template-columns: repeat(2, 1fr); }
  .dashboard-grid { grid-template-columns: 1fr; }
=======
.empty-row { text-align: center; color: var(--muted); padding: var(--space-xl); font-size: var(--fs-sm); }

@media (max-width: 768px) {
  .dashboard-grid { grid-template-columns: 1fr; }
  .trend-chart { height: 300px; }
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
}
</style>
